"""Pipeline configuration loading."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class PipelineConfig:
    source_path: Path
    database_path: Path
    rejected_path: Path
    log_level: str = "INFO"

    @classmethod
    def from_file(cls, config_path: Path) -> "PipelineConfig":
        config_path = config_path.resolve()
        project_root = config_path.parent.parent
        with config_path.open(encoding="utf-8") as handle:
            values = json.load(handle)

        def project_path(value: str) -> Path:
            path = Path(value)
            return path if path.is_absolute() else project_root / path

        return cls(
            source_path=project_path(values["source_path"]),
            database_path=project_path(values["database_path"]),
            rejected_path=project_path(values["rejected_path"]),
            log_level=values.get("log_level", "INFO"),
        )

