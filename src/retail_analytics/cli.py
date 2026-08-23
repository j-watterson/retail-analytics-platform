"""Command-line entry point."""

from __future__ import annotations

import argparse
import logging
from pathlib import Path

from .config import PipelineConfig
from .pipeline import run_pipeline
from .reporting import build_summary


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Northwind retail analytics ETL")
    parser.add_argument(
        "--config", type=Path, default=Path("configs/pipeline.json"),
        help="Path to pipeline configuration",
    )
    parser.add_argument(
        "--force", action="store_true",
        help="Process the source even if its checksum was previously loaded",
    )
    parser.add_argument(
        "--report", action="store_true",
        help="Print the sales report after the load",
    )
    return parser


def main() -> int:
    args = build_parser().parse_args()
    config_path = args.config.resolve()
    config = PipelineConfig.from_file(config_path)
    project_root = config_path.parent.parent
    logging.basicConfig(
        level=getattr(logging, config.log_level.upper(), logging.INFO),
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )
    result = run_pipeline(config, project_root, force=args.force)
    print(
        f"status={result.status} read={result.rows_read} "
        f"loaded={result.rows_loaded} rejected={result.rows_rejected}"
    )
    if args.report:
        print()
        print(build_summary(config.database_path))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

