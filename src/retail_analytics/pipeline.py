"""Extract, validate, transform, and load retail orders."""

from __future__ import annotations

import csv
import hashlib
import logging
import uuid
from dataclasses import dataclass
from pathlib import Path

from .config import PipelineConfig
from .database import Warehouse
from .validation import ValidationError, parse_order, validate_headers

LOGGER = logging.getLogger(__name__)


@dataclass(frozen=True)
class PipelineResult:
    run_id: str
    status: str
    rows_read: int
    rows_loaded: int
    rows_rejected: int


def file_checksum(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(64 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def run_pipeline(
    config: PipelineConfig,
    project_root: Path,
    *,
    force: bool = False,
) -> PipelineResult:
    if not config.source_path.is_file():
        raise FileNotFoundError(f"Source file not found: {config.source_path}")

    run_id = str(uuid.uuid4())
    checksum = file_checksum(config.source_path)
    sql_dir = project_root / "sql"
    rows_read = rows_loaded = rows_rejected = 0
    rejected_rows: list[dict[str, str]] = []

    with Warehouse(config.database_path, sql_dir) as warehouse:
        warehouse.initialize()
        if not force and warehouse.checksum_loaded(checksum):
            LOGGER.info("Source checksum already loaded; skipping %s", config.source_path)
            return PipelineResult(run_id, "skipped", 0, 0, 0)

        warehouse.start_run(run_id, config.source_path.name, checksum)
        try:
            with config.source_path.open(newline="", encoding="utf-8") as source:
                reader = csv.DictReader(source)
                validate_headers(reader.fieldnames)
                for row in reader:
                    rows_read += 1
                    try:
                        order = parse_order(row)
                        warehouse.upsert_order(order, config.source_path.name)
                        rows_loaded += 1
                    except ValidationError as error:
                        rows_rejected += 1
                        rejected_rows.append({**row, "rejection_reason": str(error)})
                        LOGGER.warning("Rejected source row %s: %s", rows_read, error)

            _write_rejections(config.rejected_path, rejected_rows)
            warehouse.finish_run(
                run_id, "completed", rows_read, rows_loaded, rows_rejected
            )
        except Exception as error:
            warehouse.db.rollback()
            warehouse.finish_run(
                run_id, "failed", rows_read, rows_loaded, rows_rejected, str(error)
            )
            raise

    LOGGER.info(
        "ETL completed: read=%d loaded=%d rejected=%d",
        rows_read, rows_loaded, rows_rejected,
    )
    return PipelineResult(
        run_id, "completed", rows_read, rows_loaded, rows_rejected
    )


def _write_rejections(path: Path, rows: list[dict[str, str]]) -> None:
    if not rows:
        if path.exists():
            path.unlink()
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as target:
        writer = csv.DictWriter(target, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
