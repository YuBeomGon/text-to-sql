from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

import yaml

_CONFIG_PATH = Path(__file__).resolve().parent.parent / "config" / "slice.yaml"


@dataclass(frozen=True)
class SliceConfig:
    source: str
    domain: str
    fiscal_years: list[int]
    core_agencies: list[str]
    pending_agencies: list[str]
    extended_agencies: list[str]
    db_engine: str
    datasets_dir: str
    eval_cases_dir: str
    gold_snapshot: str


def load_config(path: Path | None = None) -> SliceConfig:
    path = path or _CONFIG_PATH
    with open(path) as f:
        raw = yaml.safe_load(f)

    ds = raw["data_slice"]
    paths = raw["paths"]
    return SliceConfig(
        source=ds["source"],
        domain=ds["domain"],
        fiscal_years=ds["fiscal_years"],
        core_agencies=ds["core_agencies"],
        pending_agencies=ds.get("pending_agencies", []),
        extended_agencies=ds["extended_agencies"],
        db_engine=ds["db_engine"],
        datasets_dir=paths["datasets_dir"],
        eval_cases_dir=paths["eval_cases_dir"],
        gold_snapshot=paths["gold_snapshot"],
    )
