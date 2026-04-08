# M0 + M1: Foundation & Evaluation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the runnable foundation (DuckDB + data loader + executor) and a working evaluation harness so that `./score.sh --quick` returns real numbers, enabling the score-gated development loop for M2+.

**Architecture:** USAspending contract data is downloaded as CSV/Parquet via the public bulk download API, loaded into DuckDB in-memory at startup. A thin query executor runs SQL against DuckDB. The evaluation harness reads the 228 existing JSONL cases, runs each through the executor (or a stub NL2SQL pipeline), compares results against gold snapshots, and computes per-axis scores. `score.sh` delegates to `python -m src.eval.score_runner`.

**Tech Stack:** Python 3.12, DuckDB, pytest, JSONL for eval cases, YAML for config

**Decision log from planning conversation:**
- Multi-candidate generation is OUT (cost concern) — Phase 2 will rely on verification + abstain policy instead
- Gold results must be backfilled after data slice is locked
- After M1 completes, the agent autonomous loop (implement → score → accept/revert) becomes viable

**Scorer weight note:** The M1 scorer uses simplified weights (positive_result_accuracy=0.50, negative_abstain_f1=0.30, execution_success=0.10, risky_answer_penalty=0.10) because per-axis metrics (metric_definition, time_axis, etc.) are not computable until M2+. These will converge to the full weights defined in `docs/evaluation_framework.md` section 5.2 as per-axis metrics become available.

---

## Scope Check

This plan covers two WBS milestones that must be sequential:
- **M0 (Foundation):** directory skeleton, DuckDB, config, loader, executor, harness skeleton, score CLI
- **M1 (Evaluation — partial):** eval case normalization, result-set comparison, score computation, gold backfill, score report

These are tightly coupled (M1 needs M0's executor), so one plan is appropriate.

**M1 remaining after this plan (requires real data or real pipeline):**
- Paraphrase expansion runner (templates exist in `eval/expansions/` but no runner)
- Temporal fuzz expansion runner (templates exist but no runner)
- Lock an initial hard regression set (needs gold backfill after USAspending data is loaded)

**Prerequisite for M2:** USAspending data must be downloaded and loaded before the semantic interpretation layer can produce meaningful SQL. The data download mechanism is out of scope for this plan but must be done before M2 begins.

## Parallelization Note

Tasks 4-6 (DuckDB modules: loader, schema inspector, executor) and Tasks 7-9 (eval modules: case loader, result comparator, scorer) have no dependencies on each other. If using subagent-driven development, these two groups can run in parallel after Tasks 1-3 complete.

---

## File Structure

```
text-to-sql-v2/
├── pyproject.toml                     # project metadata, dependencies, pytest config
├── src/
│   ├── __init__.py
│   ├── config.py                      # data slice config (agencies, FY, paths)
│   ├── db.py                          # DuckDB bootstrap and connection management
│   ├── loader.py                      # USAspending CSV/Parquet → DuckDB loader
│   ├── schema_inspector.py            # introspect loaded tables/columns
│   ├── executor.py                    # run SQL against DuckDB, return results
│   └── eval/
│       ├── __init__.py
│       ├── case_loader.py             # read JSONL eval cases, filter by tier
│       ├── result_compare.py          # compare query result-set vs gold
│       ├── scorer.py                  # compute per-axis and aggregate scores
│       └── score_runner.py            # CLI entrypoint for score.sh
├── tests/
│   ├── __init__.py
│   ├── conftest.py                    # shared fixtures (in-memory DuckDB with sample data)
│   ├── test_config.py
│   ├── test_db.py
│   ├── test_loader.py
│   ├── test_schema_inspector.py
│   ├── test_executor.py
│   ├── test_case_loader.py
│   ├── test_result_compare.py
│   └── test_scorer.py
├── datasets/
│   └── README.md                      # instructions for acquiring USAspending data
├── config/
│   └── slice.yaml                     # locked data slice definition
├── score.sh                           # (modify existing) delegate to Python scorer
└── eval/
    └── cases/                         # (existing) 228 JSONL cases
```

---

## Task 1: Project Skeleton and Dependencies

**Files:**
- Create: `pyproject.toml`
- Create: `src/__init__.py`
- Create: `src/eval/__init__.py`
- Create: `tests/__init__.py`
- Create: `datasets/README.md`

- [ ] **Step 1: Create pyproject.toml**

```toml
[project]
name = "public-nl2sql"
version = "0.1.0"
requires-python = ">=3.12"
dependencies = [
    "duckdb>=1.1.0",
    "pyyaml>=6.0",
    "httpx>=0.27.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=8.0",
    "pytest-cov>=5.0",
]

[tool.setuptools.packages.find]
where = ["."]
include = ["src*"]

[tool.pytest.ini_options]
testpaths = ["tests"]
pythonpath = ["."]
```

- [ ] **Step 2: Create package init files**

`src/__init__.py` — empty file:
```python
```

`src/eval/__init__.py` — empty file:
```python
```

`tests/__init__.py` — empty file:
```python
```

- [ ] **Step 3: Create datasets README**

`datasets/README.md`:
```markdown
# Datasets

This directory holds the local USAspending data files used by the project.

## How to acquire data

1. Run `python -m src.loader --download` (after Task 4 is implemented)
2. Or manually download from https://api.usaspending.gov/api/v2/bulk_download/

## What should be here after download

- `contracts_FY2024.csv` or `.parquet`
- `contracts_FY2025.csv` or `.parquet`

Do not commit large data files. Add them to `.gitignore`.
```

- [ ] **Step 4: Install dependencies**

Run: `cd /data/MyProject/side/text-to-sql-v2 && pip install -e ".[dev]"`
Expected: successful install including duckdb

- [ ] **Step 5: Verify import works**

Run: `python -c "import duckdb; print(duckdb.__version__)"`
Expected: prints duckdb version (1.x.x)

- [ ] **Step 6: Commit**

```bash
git init
git add pyproject.toml src/__init__.py src/eval/__init__.py tests/__init__.py datasets/README.md .gitignore
git commit -m "chore(m0): add project skeleton and dependencies"
```

---

## Task 2: Data Slice Config

**Files:**
- Create: `config/slice.yaml`
- Create: `src/config.py`
- Create: `tests/test_config.py`

- [ ] **Step 1: Create slice.yaml**

`config/slice.yaml`:
```yaml
data_slice:
  source: usaspending
  domain: contracts
  fiscal_years: [2024, 2025]
  core_agencies:
    - "Department of Defense"
    - "Department of Health and Human Services"
    - "NASA"
    - "Department of Homeland Security"
    - "General Services Administration"
  extended_agencies:
    - "Department of Veterans Affairs"
    - "Department of Energy"
    - "Department of Transportation"
  db_engine: duckdb_memory

paths:
  datasets_dir: "datasets"
  eval_cases_dir: "eval/cases"
  gold_snapshot: "eval/cases/gold_result_snapshot_template.jsonl"
```

- [ ] **Step 2: Write the failing test**

`tests/test_config.py`:
```python
from src.config import load_config


def test_load_config_returns_core_agencies():
    cfg = load_config()
    assert "Department of Defense" in cfg.core_agencies
    assert "NASA" in cfg.core_agencies
    assert len(cfg.core_agencies) == 5


def test_load_config_returns_fiscal_years():
    cfg = load_config()
    assert cfg.fiscal_years == [2024, 2025]


def test_load_config_returns_paths():
    cfg = load_config()
    assert cfg.datasets_dir == "datasets"
    assert cfg.eval_cases_dir == "eval/cases"
```

- [ ] **Step 3: Run test to verify it fails**

Run: `cd /data/MyProject/side/text-to-sql-v2 && python -m pytest tests/test_config.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'src.config'`

- [ ] **Step 4: Write minimal implementation**

`src/config.py`:
```python
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
        extended_agencies=ds["extended_agencies"],
        db_engine=ds["db_engine"],
        datasets_dir=paths["datasets_dir"],
        eval_cases_dir=paths["eval_cases_dir"],
        gold_snapshot=paths["gold_snapshot"],
    )
```

- [ ] **Step 5: Run test to verify it passes**

Run: `python -m pytest tests/test_config.py -v`
Expected: 3 passed

- [ ] **Step 6: Commit**

```bash
git add config/slice.yaml src/config.py tests/test_config.py
git commit -m "feat(m0): add data slice config loader"
```

---

## Task 3: DuckDB Bootstrap

**Files:**
- Create: `src/db.py`
- Create: `tests/test_db.py`
- Create: `tests/conftest.py`

- [ ] **Step 1: Write the failing test**

`tests/test_db.py`:
```python
from src.db import create_connection


def test_create_connection_returns_working_duckdb():
    conn = create_connection()
    result = conn.execute("SELECT 1 AS val").fetchone()
    assert result == (1,)
    conn.close()


def test_create_connection_is_in_memory():
    conn = create_connection()
    # DuckDB in-memory has no persistent file
    result = conn.execute("SELECT current_database()").fetchone()
    assert result is not None
    conn.close()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_db.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'src.db'`

- [ ] **Step 3: Write minimal implementation**

`src/db.py`:
```python
from __future__ import annotations

import duckdb


def create_connection() -> duckdb.DuckDBPyConnection:
    """Create an in-memory DuckDB connection."""
    return duckdb.connect(database=":memory:")
```

- [ ] **Step 4: Create shared test fixtures**

`tests/conftest.py`:
```python
import pytest
import duckdb
from pathlib import Path

from src.db import create_connection

_PROJECT_ROOT = Path(__file__).resolve().parent.parent


@pytest.fixture
def project_root() -> Path:
    return _PROJECT_ROOT


@pytest.fixture
def eval_cases_dir(project_root) -> Path:
    return project_root / "eval" / "cases"


@pytest.fixture
def db_conn():
    """Provide a fresh in-memory DuckDB connection per test."""
    conn = create_connection()
    yield conn
    conn.close()


@pytest.fixture
def sample_db(db_conn):
    """DuckDB with a small sample contracts table for testing."""
    db_conn.execute("""
        CREATE TABLE contracts (
            award_id VARCHAR,
            awarding_agency_name VARCHAR,
            awarding_sub_agency_name VARCHAR,
            recipient_name VARCHAR,
            award_type VARCHAR,
            fiscal_year INTEGER,
            total_obligation DOUBLE,
            total_outlay DOUBLE,
            total_award_amount DOUBLE,
            action_date DATE,
            award_start_date DATE,
            naics_code VARCHAR,
            award_status VARCHAR
        )
    """)
    db_conn.execute("""
        INSERT INTO contracts VALUES
        ('AWD-001', 'Department of Defense', 'Army', 'Lockheed Martin Corp', 'contract', 2024, 5000000.0, 3000000.0, 6000000.0, '2024-01-15', '2024-01-01', '336411', 'active'),
        ('AWD-002', 'Department of Defense', 'Navy', 'Boeing Co', 'contract', 2024, 3000000.0, 2000000.0, 4000000.0, '2024-03-20', '2024-03-01', '336411', 'active'),
        ('AWD-003', 'NASA', 'Goddard', 'Northrop Grumman Corp', 'contract', 2024, 2000000.0, 1500000.0, 2500000.0, '2024-06-10', '2024-06-01', '541715', 'active'),
        ('AWD-004', 'NASA', 'JPL', 'Lockheed Martin Corp', 'contract', 2025, 4000000.0, 2500000.0, 5000000.0, '2024-11-05', '2024-10-01', '541715', 'active'),
        ('AWD-005', 'Department of Health and Human Services', 'CDC', 'Deloitte LLP', 'contract', 2025, 1000000.0, 800000.0, 1200000.0, '2025-01-10', '2025-01-01', '541611', 'active'),
        ('AWD-006', 'Department of Homeland Security', 'FEMA', 'Booz Allen Hamilton', 'contract', 2024, 1500000.0, 1000000.0, 2000000.0, '2024-04-15', '2024-04-01', '541611', 'closed'),
        ('AWD-007', 'General Services Administration', 'FAS', 'SAIC Inc', 'contract', 2025, 800000.0, 600000.0, 1000000.0, '2025-02-20', '2025-02-01', '541512', 'active')
    """)
    return db_conn
```

- [ ] **Step 5: Run tests to verify they pass**

Run: `python -m pytest tests/test_db.py -v`
Expected: 2 passed

- [ ] **Step 6: Commit**

```bash
git add src/db.py tests/test_db.py tests/conftest.py
git commit -m "feat(m0): add DuckDB in-memory bootstrap"
```

---

## Task 4: USAspending Data Loader

**Files:**
- Create: `src/loader.py`
- Create: `tests/test_loader.py`

- [ ] **Step 1: Write the failing test**

`tests/test_loader.py`:
```python
import tempfile
import csv
from pathlib import Path

from src.db import create_connection
from src.loader import load_contracts_csv


def _write_sample_csv(directory: Path) -> Path:
    """Write a tiny CSV that mimics USAspending contract columns."""
    filepath = directory / "contracts_sample.csv"
    rows = [
        {
            "award_id_piid": "AWD-T01",
            "awarding_agency_name": "NASA",
            "awarding_sub_agency_name": "JPL",
            "recipient_name": "SpaceX",
            "award_type": "contract",
            "fiscal_year": "2024",
            "total_obligation": "1000000.00",
            "total_outlay": "500000.00",
            "total_award_amount": "1200000.00",
            "action_date": "2024-02-15",
            "period_of_performance_start_date": "2024-02-01",
            "naics_code": "336414",
            "award_status": "active",
        },
    ]
    with open(filepath, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)
    return filepath


def test_load_contracts_csv_creates_table(tmp_path):
    csv_path = _write_sample_csv(tmp_path)
    conn = create_connection()
    load_contracts_csv(conn, csv_path)

    tables = conn.execute("SHOW TABLES").fetchall()
    table_names = [t[0] for t in tables]
    assert "contracts" in table_names
    conn.close()


def test_load_contracts_csv_row_count(tmp_path):
    csv_path = _write_sample_csv(tmp_path)
    conn = create_connection()
    load_contracts_csv(conn, csv_path)

    count = conn.execute("SELECT COUNT(*) FROM contracts").fetchone()[0]
    assert count == 1
    conn.close()


def test_load_contracts_csv_column_mapping(tmp_path):
    csv_path = _write_sample_csv(tmp_path)
    conn = create_connection()
    load_contracts_csv(conn, csv_path)

    row = conn.execute("SELECT award_id, awarding_agency_name, fiscal_year, total_obligation FROM contracts").fetchone()
    assert row[0] == "AWD-T01"
    assert row[1] == "NASA"
    assert row[2] == 2024
    assert row[3] == 1000000.00
    conn.close()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_loader.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'src.loader'`

- [ ] **Step 3: Write minimal implementation**

`src/loader.py`:
```python
from __future__ import annotations

from pathlib import Path

import duckdb

# Maps USAspending CSV column names to our internal column names.
_COLUMN_MAP = {
    "award_id_piid": "award_id",
    "awarding_agency_name": "awarding_agency_name",
    "awarding_sub_agency_name": "awarding_sub_agency_name",
    "recipient_name": "recipient_name",
    "award_type": "award_type",
    "fiscal_year": "fiscal_year",
    "total_obligation": "total_obligation",
    "total_outlay": "total_outlay",
    "total_award_amount": "total_award_amount",
    "action_date": "action_date",
    "period_of_performance_start_date": "award_start_date",
    "naics_code": "naics_code",
    "award_status": "award_status",
}


def load_contracts_csv(
    conn: duckdb.DuckDBPyConnection,
    csv_path: Path,
) -> None:
    """Load a USAspending contracts CSV into the 'contracts' table.

    Reads the CSV, selects and renames known columns, and casts types.
    Can be called multiple times to append data from different files.
    """
    source_cols = ", ".join(
        f'"{src}" AS {dst}' for src, dst in _COLUMN_MAP.items()
    )

    table_exists = conn.execute(
        "SELECT COUNT(*) FROM information_schema.tables WHERE table_name = 'contracts'"
    ).fetchone()[0]

    if table_exists:
        conn.execute(f"""
            INSERT INTO contracts
            SELECT {source_cols}
            FROM read_csv_auto('{csv_path}', header=true, all_varchar=true)
        """)
    else:
        conn.execute(f"""
            CREATE TABLE contracts AS
            SELECT {source_cols}
            FROM read_csv_auto('{csv_path}', header=true, all_varchar=true)
        """)

    # Cast numeric and date columns after loading
    conn.execute("""
        CREATE OR REPLACE TABLE contracts AS
        SELECT
            award_id,
            awarding_agency_name,
            awarding_sub_agency_name,
            recipient_name,
            award_type,
            CAST(fiscal_year AS INTEGER) AS fiscal_year,
            CAST(total_obligation AS DOUBLE) AS total_obligation,
            CAST(total_outlay AS DOUBLE) AS total_outlay,
            CAST(total_award_amount AS DOUBLE) AS total_award_amount,
            TRY_CAST(action_date AS DATE) AS action_date,
            TRY_CAST(award_start_date AS DATE) AS award_start_date,
            naics_code,
            award_status
        FROM contracts
    """)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_loader.py -v`
Expected: 3 passed

- [ ] **Step 5: Commit**

```bash
git add src/loader.py tests/test_loader.py
git commit -m "feat(m0): add USAspending CSV loader with column mapping"
```

---

## Task 5: Schema Inspector

**Files:**
- Create: `src/schema_inspector.py`
- Create: `tests/test_schema_inspector.py`

- [ ] **Step 1: Write the failing test**

`tests/test_schema_inspector.py`:
```python
from src.schema_inspector import get_tables, get_columns


def test_get_tables_returns_contracts(sample_db):
    tables = get_tables(sample_db)
    assert "contracts" in tables


def test_get_columns_returns_expected_columns(sample_db):
    columns = get_columns(sample_db, "contracts")
    expected = {
        "award_id", "awarding_agency_name", "awarding_sub_agency_name",
        "recipient_name", "award_type", "fiscal_year",
        "total_obligation", "total_outlay", "total_award_amount",
        "action_date", "award_start_date", "naics_code", "award_status",
    }
    assert expected.issubset(set(columns.keys()))


def test_get_columns_includes_types(sample_db):
    columns = get_columns(sample_db, "contracts")
    assert columns["fiscal_year"] == "INTEGER"
    assert columns["total_obligation"] == "DOUBLE"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_schema_inspector.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'src.schema_inspector'`

- [ ] **Step 3: Write minimal implementation**

`src/schema_inspector.py`:
```python
from __future__ import annotations

import duckdb


def get_tables(conn: duckdb.DuckDBPyConnection) -> list[str]:
    """Return list of table names in the current database."""
    rows = conn.execute("SHOW TABLES").fetchall()
    return [row[0] for row in rows]


def get_columns(conn: duckdb.DuckDBPyConnection, table: str) -> dict[str, str]:
    """Return {column_name: column_type} for the given table."""
    rows = conn.execute(f'DESCRIBE "{table}"').fetchall()
    return {row[0]: row[1] for row in rows}
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_schema_inspector.py -v`
Expected: 3 passed

- [ ] **Step 5: Commit**

```bash
git add src/schema_inspector.py tests/test_schema_inspector.py
git commit -m "feat(m0): add schema inspector for table/column introspection"
```

---

## Task 6: Query Executor

**Files:**
- Create: `src/executor.py`
- Create: `tests/test_executor.py`

- [ ] **Step 1: Write the failing test**

`tests/test_executor.py`:
```python
from src.executor import execute_query, QueryResult


def test_execute_query_returns_rows(sample_db):
    result = execute_query(sample_db, "SELECT award_id FROM contracts WHERE awarding_agency_name = 'NASA'")
    assert isinstance(result, QueryResult)
    assert result.success is True
    assert len(result.rows) == 2
    assert result.columns == ["award_id"]


def test_execute_query_returns_error_on_bad_sql(sample_db):
    result = execute_query(sample_db, "SELECT nonexistent FROM contracts")
    assert result.success is False
    assert result.error is not None
    assert result.rows == []


def test_execute_query_aggregate(sample_db):
    result = execute_query(
        sample_db,
        "SELECT SUM(total_obligation) AS total FROM contracts WHERE awarding_agency_name = 'Department of Defense'"
    )
    assert result.success is True
    assert len(result.rows) == 1
    assert result.rows[0][0] == 8000000.0
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_executor.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'src.executor'`

- [ ] **Step 3: Write minimal implementation**

`src/executor.py`:
```python
from __future__ import annotations

from dataclasses import dataclass, field

import duckdb


@dataclass
class QueryResult:
    success: bool
    columns: list[str] = field(default_factory=list)
    rows: list[tuple] = field(default_factory=list)
    error: str | None = None


def execute_query(conn: duckdb.DuckDBPyConnection, sql: str) -> QueryResult:
    """Execute SQL against DuckDB and return a structured result."""
    try:
        rel = conn.execute(sql)
        columns = [desc[0] for desc in rel.description]
        rows = rel.fetchall()
        return QueryResult(success=True, columns=columns, rows=rows)
    except duckdb.Error as e:
        return QueryResult(success=False, error=str(e))
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_executor.py -v`
Expected: 3 passed

- [ ] **Step 5: Commit**

```bash
git add src/executor.py tests/test_executor.py
git commit -m "feat(m0): add query executor with structured result"
```

---

## Task 7: Eval Case Loader

**Files:**
- Create: `src/eval/case_loader.py`
- Create: `tests/test_case_loader.py`

- [ ] **Step 1: Write the failing test**

`tests/test_case_loader.py`:
```python
from src.eval.case_loader import load_cases, EvalCase


def test_load_all_cases(eval_cases_dir):
    cases = load_cases(eval_cases_dir / "combined_hard_cases.jsonl")
    assert len(cases) == 228
    assert all(isinstance(c, EvalCase) for c in cases)


def test_load_cases_filter_core_tier(eval_cases_dir):
    cases = load_cases(eval_cases_dir / "combined_hard_cases.jsonl", tier="core")
    assert all(c.eval_tier == "core" for c in cases)
    assert len(cases) == 190


def test_load_cases_filter_by_category(eval_cases_dir):
    cases = load_cases(eval_cases_dir / "combined_hard_cases.jsonl", category="metric_ambiguity")
    assert all(c.category == "metric_ambiguity" for c in cases)
    assert len(cases) >= 26  # at least the initial 26; may grow as cases are added


def test_eval_case_has_expected_fields(eval_cases_dir):
    cases = load_cases(eval_cases_dir / "combined_hard_cases.jsonl")
    c = cases[0]
    assert c.case_id is not None
    assert c.query is not None
    assert c.expected_behavior in ("answer", "clarify", "abstain")
    assert c.polarity in ("positive", "ambiguous", "negative")
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_case_loader.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'src.eval.case_loader'`

- [ ] **Step 3: Write minimal implementation**

`src/eval/case_loader.py`:
```python
from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class EvalCase:
    case_id: str
    category: str
    polarity: str
    expected_behavior: str
    difficulty: str
    query: str
    tags: list[str]
    expected_semantics: dict
    notes: str
    eval_tier: str


def load_cases(
    path: Path,
    tier: str | None = None,
    category: str | None = None,
) -> list[EvalCase]:
    """Load eval cases from a JSONL file, optionally filtering by tier or category."""
    cases: list[EvalCase] = []
    with open(path) as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            raw = json.loads(line)
            case = EvalCase(
                case_id=raw["case_id"],
                category=raw["category"],
                polarity=raw["polarity"],
                expected_behavior=raw["expected_behavior"],
                difficulty=raw["difficulty"],
                query=raw["query"],
                tags=raw.get("tags", []),
                expected_semantics=raw.get("expected_semantics", {}),
                notes=raw.get("notes", ""),
                eval_tier=raw.get("eval_tier", "core"),
            )
            if tier and case.eval_tier != tier:
                continue
            if category and case.category != category:
                continue
            cases.append(case)
    return cases
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_case_loader.py -v`
Expected: 4 passed

- [ ] **Step 5: Commit**

```bash
git add src/eval/case_loader.py tests/test_case_loader.py
git commit -m "feat(m1): add eval case loader with tier/category filtering"
```

---

## Task 8: Result-Set Comparison

**Files:**
- Create: `src/eval/result_compare.py`
- Create: `tests/test_result_compare.py`

- [ ] **Step 1: Write the failing test**

`tests/test_result_compare.py`:
```python
from src.eval.result_compare import compare_results, CompareVerdict


def test_exact_match():
    gold_rows = [(1, "NASA", 5000000.0)]
    actual_rows = [(1, "NASA", 5000000.0)]
    verdict = compare_results(gold_rows, actual_rows, order_sensitive=False)
    assert verdict.match is True
    assert verdict.score == 1.0


def test_order_insensitive_match():
    gold = [(1, "A"), (2, "B")]
    actual = [(2, "B"), (1, "A")]
    verdict = compare_results(gold, actual, order_sensitive=False)
    assert verdict.match is True


def test_order_sensitive_mismatch():
    gold = [(1, "A"), (2, "B")]
    actual = [(2, "B"), (1, "A")]
    verdict = compare_results(gold, actual, order_sensitive=True)
    assert verdict.match is False


def test_row_count_mismatch():
    gold = [(1,), (2,)]
    actual = [(1,), (2,), (3,)]
    verdict = compare_results(gold, actual, order_sensitive=False)
    assert verdict.match is False


def test_empty_both():
    verdict = compare_results([], [], order_sensitive=False)
    assert verdict.match is True
    assert verdict.score == 1.0


def test_numeric_tolerance():
    gold = [(1000000.001,)]
    actual = [(1000000.002,)]
    verdict = compare_results(gold, actual, order_sensitive=False, numeric_tolerance=0.01)
    assert verdict.match is True


def test_partial_overlap_score():
    gold = [(1,), (2,), (3,)]
    actual = [(1,), (2,), (4,)]
    verdict = compare_results(gold, actual, order_sensitive=False)
    assert verdict.match is False
    assert 0.0 < verdict.score < 1.0


def test_clarify_behavior_match():
    verdict = compare_results(
        gold_rows=None,
        actual_rows=None,
        expected_behavior="clarify",
        actual_behavior="clarify",
    )
    assert verdict.match is True


def test_clarify_expected_but_answered():
    verdict = compare_results(
        gold_rows=None,
        actual_rows=[(1,)],
        expected_behavior="clarify",
        actual_behavior="answer",
    )
    assert verdict.match is False
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_result_compare.py -v`
Expected: FAIL — `ModuleNotFoundError`

- [ ] **Step 3: Write minimal implementation**

`src/eval/result_compare.py`:
```python
from __future__ import annotations

from dataclasses import dataclass


@dataclass
class CompareVerdict:
    match: bool
    score: float
    reason: str = ""


def _rows_as_sets(rows: list[tuple]) -> set[tuple]:
    """Normalize rows into a frozenset for order-insensitive comparison."""
    normalized = []
    for row in rows:
        normalized.append(tuple(row))
    return set(normalized)


def _numeric_close(a, b, tol: float) -> bool:
    if isinstance(a, (int, float)) and isinstance(b, (int, float)):
        return abs(a - b) <= tol
    return a == b


def _stable_sort_key(row: tuple) -> tuple:
    """Sort key that handles mixed types deterministically."""
    return tuple((type(v).__name__, str(v)) for v in row)


def _rows_match_with_tolerance(
    gold: list[tuple], actual: list[tuple], tol: float, order_sensitive: bool
) -> tuple[bool, float]:
    if len(gold) != len(actual):
        # Partial overlap score: count matching rows.
        # Note: partial overlap ignores numeric_tolerance (known limitation).
        gold_set = _rows_as_sets(gold)
        actual_set = _rows_as_sets(actual)
        overlap = len(gold_set & actual_set)
        total = max(len(gold_set), len(actual_set))
        return False, overlap / total if total > 0 else 0.0

    if not order_sensitive:
        gold = sorted(gold, key=_stable_sort_key)
        actual = sorted(actual, key=_stable_sort_key)

    matched = 0
    for g, a in zip(gold, actual):
        if len(g) != len(a):
            continue
        if all(_numeric_close(gv, av, tol) for gv, av in zip(g, a)):
            matched += 1

    score = matched / len(gold) if gold else 1.0
    return score == 1.0, score


def compare_results(
    gold_rows: list[tuple] | None = None,
    actual_rows: list[tuple] | None = None,
    order_sensitive: bool = False,
    numeric_tolerance: float = 0.0,
    expected_behavior: str = "answer",
    actual_behavior: str = "answer",
) -> CompareVerdict:
    """Compare actual query results against gold, handling behavior routing."""

    # Behavior-level comparison (clarify/abstain cases)
    if expected_behavior in ("clarify", "abstain"):
        if actual_behavior == expected_behavior:
            return CompareVerdict(match=True, score=1.0, reason="behavior_match")
        return CompareVerdict(
            match=False, score=0.0,
            reason=f"expected {expected_behavior}, got {actual_behavior}",
        )

    # Result-set comparison (answer cases)
    if gold_rows is None or actual_rows is None:
        return CompareVerdict(match=False, score=0.0, reason="missing_data")

    if len(gold_rows) == 0 and len(actual_rows) == 0:
        return CompareVerdict(match=True, score=1.0, reason="both_empty")

    is_match, score = _rows_match_with_tolerance(
        gold_rows, actual_rows, numeric_tolerance, order_sensitive
    )
    reason = "exact_match" if is_match else "partial_or_mismatch"
    return CompareVerdict(match=is_match, score=score, reason=reason)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_result_compare.py -v`
Expected: 9 passed

- [ ] **Step 5: Commit**

```bash
git add src/eval/result_compare.py tests/test_result_compare.py
git commit -m "feat(m1): add result-set comparison with tolerance and behavior routing"
```

---

## Task 9: Scorer

**Files:**
- Create: `src/eval/scorer.py`
- Create: `tests/test_scorer.py`

- [ ] **Step 1: Write the failing test**

`tests/test_scorer.py`:
```python
from src.eval.scorer import compute_scores, ScoreReport, CaseOutcome


def _make_outcomes() -> list[CaseOutcome]:
    return [
        # 3 positive answer cases: 2 correct, 1 wrong
        CaseOutcome(case_id="EASY-001", category="easy_baseline", expected_behavior="answer", actual_behavior="answer", result_score=1.0, execution_success=True),
        CaseOutcome(case_id="EASY-002", category="easy_baseline", expected_behavior="answer", actual_behavior="answer", result_score=1.0, execution_success=True),
        CaseOutcome(case_id="MET-002", category="metric_ambiguity", expected_behavior="answer", actual_behavior="answer", result_score=0.0, execution_success=True),
        # 2 clarify cases: 1 correctly clarified, 1 incorrectly answered
        CaseOutcome(case_id="MET-001", category="metric_ambiguity", expected_behavior="clarify", actual_behavior="clarify", result_score=1.0, execution_success=True),
        CaseOutcome(case_id="SCOPE-001", category="scope_state", expected_behavior="clarify", actual_behavior="answer", result_score=0.0, execution_success=True),
    ]


def test_compute_scores_returns_report():
    outcomes = _make_outcomes()
    report = compute_scores(outcomes)
    assert isinstance(report, ScoreReport)


def test_positive_result_accuracy():
    outcomes = _make_outcomes()
    report = compute_scores(outcomes)
    # 2 correct out of 3 answer cases
    assert abs(report.positive_result_accuracy - 2 / 3) < 0.01


def test_negative_abstain_f1():
    outcomes = _make_outcomes()
    report = compute_scores(outcomes)
    # 1 correct clarify out of 2 clarify cases
    assert report.negative_abstain_precision == 1.0  # 1 clarify predicted, 1 correct
    assert report.negative_abstain_recall == 0.5  # 1 correct out of 2 expected


def test_execution_success():
    outcomes = _make_outcomes()
    report = compute_scores(outcomes)
    assert report.execution_success == 1.0


def test_risky_answer_rate():
    outcomes = _make_outcomes()
    report = compute_scores(outcomes)
    # 1 case where expected=clarify but actual=answer (risky)
    # total cases = 5
    assert abs(report.risky_answer_rate - 1 / 5) < 0.01


def test_total_weighted_score():
    outcomes = _make_outcomes()
    report = compute_scores(outcomes)
    assert 0.0 <= report.total <= 1.0
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_scorer.py -v`
Expected: FAIL — `ModuleNotFoundError`

- [ ] **Step 3: Write minimal implementation**

`src/eval/scorer.py`:
```python
from __future__ import annotations

from dataclasses import dataclass


@dataclass
class CaseOutcome:
    case_id: str
    category: str
    expected_behavior: str
    actual_behavior: str
    result_score: float
    execution_success: bool


@dataclass
class ScoreReport:
    execution_success: float
    positive_result_accuracy: float
    negative_abstain_precision: float
    negative_abstain_recall: float
    negative_abstain_f1: float
    risky_answer_rate: float
    total: float
    case_count: int
    category_scores: dict[str, float]

    def format_text(self) -> str:
        lines = [
            "Score breakdown:",
            f"  case_count:                {self.case_count}",
            f"  execution_success:         {self.execution_success:.3f}",
            f"  positive_result_accuracy:  {self.positive_result_accuracy:.3f}",
            f"  negative_abstain_f1:       {self.negative_abstain_f1:.3f}",
            f"  risky_answer_rate:         {self.risky_answer_rate:.3f}",
            "",
            f"Total: {self.total:.3f}",
            "",
            "Gates:",
            f"  execution_success: {'PASS' if self.execution_success >= 0.995 else 'FAIL'}",
            f"  risky_answer_rate: {'PASS' if self.risky_answer_rate <= 0.02 else 'FAIL'}",
        ]
        if self.category_scores:
            lines.append("")
            lines.append("Per-category accuracy:")
            for cat, score in sorted(self.category_scores.items()):
                lines.append(f"  {cat:30s} {score:.3f}")
        return "\n".join(lines)


# M1 baseline weights — simplified because per-axis metrics (metric_definition,
# time_axis, etc.) are not computable until M2+.
# Target weights are in docs/evaluation_framework.md section 5.2.
_WEIGHTS = {
    "positive_result_accuracy": 0.50,
    "negative_abstain_f1": 0.30,
    "execution_success": 0.10,
    "risky_answer_penalty": 0.10,
}


def compute_scores(outcomes: list[CaseOutcome]) -> ScoreReport:
    """Compute aggregate scores from a list of case outcomes."""
    if not outcomes:
        return ScoreReport(
            execution_success=0.0, positive_result_accuracy=0.0,
            negative_abstain_precision=0.0, negative_abstain_recall=0.0,
            negative_abstain_f1=0.0, risky_answer_rate=0.0,
            total=0.0, case_count=0, category_scores={},
        )

    # Execution success
    exec_ok = sum(1 for o in outcomes if o.execution_success)
    exec_rate = exec_ok / len(outcomes)

    # Positive result accuracy (only answer-expected cases)
    answer_cases = [o for o in outcomes if o.expected_behavior == "answer"]
    if answer_cases:
        pos_acc = sum(o.result_score for o in answer_cases) / len(answer_cases)
    else:
        pos_acc = 0.0

    # Negative abstain precision / recall / F1
    neg_expected = [o for o in outcomes if o.expected_behavior in ("clarify", "abstain")]
    neg_predicted = [o for o in outcomes if o.actual_behavior in ("clarify", "abstain")]
    neg_correct = [
        o for o in outcomes
        if o.expected_behavior in ("clarify", "abstain")
        and o.actual_behavior in ("clarify", "abstain")
    ]

    neg_precision = len(neg_correct) / len(neg_predicted) if neg_predicted else 0.0
    neg_recall = len(neg_correct) / len(neg_expected) if neg_expected else 0.0
    neg_f1 = (
        2 * neg_precision * neg_recall / (neg_precision + neg_recall)
        if (neg_precision + neg_recall) > 0
        else 0.0
    )

    # Risky answer rate: expected clarify/abstain but got answer
    risky = sum(
        1 for o in outcomes
        if o.expected_behavior in ("clarify", "abstain")
        and o.actual_behavior == "answer"
    )
    risky_rate = risky / len(outcomes)

    # Per-category accuracy (answer cases only)
    cat_scores: dict[str, float] = {}
    cat_counts: dict[str, list[float]] = {}
    for o in answer_cases:
        cat_counts.setdefault(o.category, []).append(o.result_score)
    for cat, scores in cat_counts.items():
        cat_scores[cat] = sum(scores) / len(scores)

    # Weighted total
    total = (
        _WEIGHTS["positive_result_accuracy"] * pos_acc
        + _WEIGHTS["negative_abstain_f1"] * neg_f1
        + _WEIGHTS["execution_success"] * exec_rate
        + _WEIGHTS["risky_answer_penalty"] * (1.0 - risky_rate)
    )

    return ScoreReport(
        execution_success=exec_rate,
        positive_result_accuracy=pos_acc,
        negative_abstain_precision=neg_precision,
        negative_abstain_recall=neg_recall,
        negative_abstain_f1=neg_f1,
        risky_answer_rate=risky_rate,
        total=total,
        case_count=len(outcomes),
        category_scores=cat_scores,
    )
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_scorer.py -v`
Expected: 6 passed

- [ ] **Step 5: Commit**

```bash
git add src/eval/scorer.py tests/test_scorer.py
git commit -m "feat(m1): add scorer with positive accuracy, abstain F1, and risky rate"
```

---

## Task 10: Score Runner CLI (makes `score.sh` real)

**Files:**
- Create: `src/eval/score_runner.py`
- Modify: `score.sh`

- [ ] **Step 1: Write score_runner.py**

`src/eval/score_runner.py`:
```python
"""CLI entrypoint for ./score.sh.

Usage:
    python -m src.eval.score_runner --quick
    python -m src.eval.score_runner --full

At this stage (pre-M2), there is no NL2SQL pipeline yet.
The runner loads eval cases, produces a "stub" outcome for each
(execution_success=False, result_score=0.0, actual_behavior="none"),
and computes the baseline score.

As modules are added in M2+, the runner will call the real pipeline
and compare against gold results.
"""
from __future__ import annotations

import sys
from pathlib import Path

from src.eval.case_loader import load_cases
from src.eval.scorer import CaseOutcome, compute_scores

_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
_CASES_PATH = _PROJECT_ROOT / "eval" / "cases" / "combined_hard_cases.jsonl"


def _run_stub_pipeline(tier: str) -> list[CaseOutcome]:
    """Stub: no NL2SQL pipeline yet. Every case gets score 0."""
    cases = load_cases(_CASES_PATH, tier=tier)
    outcomes = []
    for c in cases:
        outcomes.append(
            CaseOutcome(
                case_id=c.case_id,
                category=c.category,
                expected_behavior=c.expected_behavior,
                actual_behavior="none",
                result_score=0.0,
                execution_success=False,
            )
        )
    return outcomes


def main() -> None:
    mode = sys.argv[1] if len(sys.argv) > 1 else "--quick"
    if mode not in ("--quick", "--full"):
        print("Usage: python -m src.eval.score_runner [--quick | --full]", file=sys.stderr)
        sys.exit(2)

    tier = "core" if mode == "--quick" else None
    outcomes = _run_stub_pipeline(tier)
    report = compute_scores(outcomes)
    print(report.format_text())


if __name__ == "__main__":
    main()
```

- [ ] **Step 2: Update score.sh to delegate to Python**

Replace `score.sh` content with:
```bash
#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")"

MODE="${1:---quick}"

case "$MODE" in
  --quick|--full)
    python -m src.eval.score_runner "$MODE"
    ;;
  *)
    echo "Usage: ./score.sh --quick | --full" >&2
    exit 2
    ;;
esac
```

- [ ] **Step 3: Verify score.sh runs and returns numbers**

Run: `cd /data/MyProject/side/text-to-sql-v2 && ./score.sh --quick`
Expected: score output with real zeroes (baseline), not TODO:
```
Score breakdown:
  case_count:                190
  execution_success:         0.000
  positive_result_accuracy:  0.000
  negative_abstain_f1:       0.000
  risky_answer_rate:         0.000
  ...
Total: 0.100
Gates:
  execution_success: FAIL
  risky_answer_rate: PASS
```

- [ ] **Step 4: Verify --full mode**

Run: `./score.sh --full`
Expected: same format but case_count = 228

- [ ] **Step 5: Commit**

```bash
git add src/eval/score_runner.py score.sh
git commit -m "feat(m1): wire score.sh to real Python scorer — baseline zeroes"
```

---

## Task 11: Gold Result Snapshot Loader

**Files:**
- Modify: `src/eval/case_loader.py`
- Create: `tests/test_gold_loader.py`

This task adds the ability to load gold SQL and result hashes from the snapshot template,
so the scorer can compare against them once they are backfilled.

- [ ] **Step 1: Write the failing test**

`tests/test_gold_loader.py`:
```python
from src.eval.case_loader import load_gold_snapshot, GoldEntry


def test_load_gold_snapshot_returns_entries(eval_cases_dir):
    entries = load_gold_snapshot(eval_cases_dir / "gold_result_snapshot_template.jsonl")
    assert len(entries) == 163  # answer cases only
    assert all(isinstance(e, GoldEntry) for e in entries)


def test_gold_entry_fields(eval_cases_dir):
    entries = load_gold_snapshot(eval_cases_dir / "gold_result_snapshot_template.jsonl")
    e = entries[0]
    assert e.case_id is not None
    assert e.query is not None
    # gold_sql is empty at this stage — that is expected
    assert e.gold_sql == ""
    # Fields from actual JSONL schema must be present
    assert hasattr(e, "result_sort_key")
    assert hasattr(e, "reviewed_by")


def test_gold_snapshot_as_dict(eval_cases_dir):
    entries = load_gold_snapshot(eval_cases_dir / "gold_result_snapshot_template.jsonl")
    by_id = {e.case_id: e for e in entries}
    assert "MET-002" in by_id
    assert "EASY-001" in by_id
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_gold_loader.py -v`
Expected: FAIL — `cannot import name 'load_gold_snapshot'`

- [ ] **Step 3: Add GoldEntry and load_gold_snapshot to case_loader.py**

Append to `src/eval/case_loader.py`:
```python

@dataclass
class GoldEntry:
    case_id: str
    query: str
    expected_behavior: str
    eval_tier: str
    gold_sql: str
    canonical_result_hash: str
    canonical_result_format: str
    result_sort_key: str
    reviewed_by: str
    notes: str


def load_gold_snapshot(path: Path) -> list[GoldEntry]:
    """Load gold result snapshot entries from JSONL."""
    entries: list[GoldEntry] = []
    with open(path) as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            raw = json.loads(line)
            entries.append(
                GoldEntry(
                    case_id=raw["case_id"],
                    query=raw["query"],
                    expected_behavior=raw["expected_behavior"],
                    eval_tier=raw["eval_tier"],
                    gold_sql=raw.get("gold_sql", ""),
                    canonical_result_hash=raw.get("canonical_result_hash", ""),
                    canonical_result_format=raw.get("canonical_result_format", ""),
                    result_sort_key=raw.get("result_sort_key", ""),
                    reviewed_by=raw.get("reviewed_by", ""),
                    notes=raw.get("notes", ""),
                )
            )
    return entries
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_gold_loader.py -v`
Expected: 3 passed

- [ ] **Step 5: Commit**

```bash
git add src/eval/case_loader.py tests/test_gold_loader.py
git commit -m "feat(m1): add gold result snapshot loader"
```

---

## Task 12: Integration Test — Full Score Pipeline

**Files:**
- Create: `tests/test_score_integration.py`

- [ ] **Step 1: Write integration test**

`tests/test_score_integration.py`:
```python
"""Integration test: load cases → stub outcomes → compute score → format report."""
from src.eval.case_loader import load_cases
from src.eval.scorer import CaseOutcome, compute_scores


def test_full_quick_pipeline(eval_cases_dir):
    cases_path = eval_cases_dir / "combined_hard_cases.jsonl"
    cases = load_cases(cases_path, tier="core")
    assert len(cases) == 190

    outcomes = []
    for c in cases:
        outcomes.append(
            CaseOutcome(
                case_id=c.case_id,
                category=c.category,
                expected_behavior=c.expected_behavior,
                actual_behavior="none",
                result_score=0.0,
                execution_success=False,
            )
        )

    report = compute_scores(outcomes)
    assert report.case_count == 190
    assert report.execution_success == 0.0
    assert report.positive_result_accuracy == 0.0
    # Baseline: everything fails, but the pipeline runs end-to-end
    text = report.format_text()
    assert "execution_success" in text
    assert "FAIL" in text


def test_perfect_score_pipeline(eval_cases_dir):
    """Simulate all-correct outcomes to verify scoring math."""
    cases_path = eval_cases_dir / "combined_hard_cases.jsonl"
    cases = load_cases(cases_path, tier="core")
    outcomes = []
    for c in cases:
        outcomes.append(
            CaseOutcome(
                case_id=c.case_id,
                category=c.category,
                expected_behavior=c.expected_behavior,
                actual_behavior=c.expected_behavior,
                result_score=1.0,
                execution_success=True,
            )
        )

    report = compute_scores(outcomes)
    assert report.execution_success == 1.0
    assert report.positive_result_accuracy == 1.0
    assert report.negative_abstain_f1 == 1.0
    assert report.risky_answer_rate == 0.0
    assert report.total == 1.0
```

- [ ] **Step 2: Run test to verify it passes**

Run: `python -m pytest tests/test_score_integration.py -v`
Expected: 2 passed

- [ ] **Step 3: Run full test suite**

Run: `python -m pytest tests/ -v`
Expected: all tests pass (approximately 25 tests)

- [ ] **Step 4: Run score.sh to confirm end-to-end**

Run: `./score.sh --quick`
Expected: real numeric output, not TODO

- [ ] **Step 5: Commit**

```bash
git add tests/test_score_integration.py
git commit -m "test(m1): add integration tests for full score pipeline"
```

---

## Task 13: .gitignore and Cleanup

**Files:**
- Create or update: `.gitignore`
- Create: `config/__init__.py` (not needed — config is YAML, not a package)

- [ ] **Step 1: Create .gitignore**

```gitignore
# Data files (large, not committed)
datasets/*.csv
datasets/*.parquet
datasets/*.zip

# Python
__pycache__/
*.pyc
*.egg-info/
dist/
build/

# DuckDB
*.duckdb

# IDE
.vscode/
.idea/

# OS
.DS_Store
```

- [ ] **Step 2: Verify no unwanted files are tracked**

Run: `git status`
Expected: clean or only expected files

- [ ] **Step 3: Commit**

```bash
git add .gitignore
git commit -m "chore(m0): add .gitignore for data files and Python artifacts"
```

---

## Task 14: Update WBS and Documentation

**Files:**
- Modify: `docs/wbs_v0.1.md`
- Modify: `docs/evaluation_framework.md`

- [ ] **Step 1: Mark completed M0 items in WBS**

Update `docs/wbs_v0.1.md` M0 section — change `[ ]` to `[x]` for all 8 M0 items.

- [ ] **Step 2: Mark completed M1 items in WBS**

Update `docs/wbs_v0.1.md` M1 section — change `[ ]` to `[x]` for:
- Normalize 300 hard cases (already done in eval/cases/)
- Tag each case with polarity, failure axis, expected behavior, difficulty (already done)
- Result-set comparison logic (Task 8)
- Negative/ambiguous expected behavior schema (Task 8)
- Score report output format (Task 9)

Leave unchecked:
- Paraphrase expansion framework (deferred — templates exist but no runner)
- Temporal fuzz expansion framework (deferred — templates exist but no runner)
- Lock an initial hard regression set (needs gold backfill after data load)

- [ ] **Step 3: Add note to evaluation_framework.md about multi-candidate removal**

Append to `docs/evaluation_framework.md` section 5.2:
```markdown

### 5.3 Cost policy

Multi-candidate SQL generation is excluded from this project due to cost.
Phase 2 accuracy improvement relies on:
- verification and repair loop strength
- abstain/clarify policy precision
- hard-case regression locking
```

- [ ] **Step 4: Commit**

```bash
git add docs/wbs_v0.1.md docs/evaluation_framework.md
git commit -m "docs: update WBS completion status and add cost policy note"
```

---

## Self-Review

**1. Spec coverage:**
- M0 items: all 8 covered (skeleton=T1, DuckDB=T3, config=T2, loader=T4, schema inspector=T5, executor=T6, harness skeleton=T7-T10, score CLI=T10)
- M1 items: 5 of 8 covered; paraphrase/temporal expansion runners and locked regression set are deferred until gold data exists — this is noted in T14 and in the Scope Check section
- Multi-candidate removal: documented in T14 and in plan header decision log
- Data download as M2 prerequisite: documented in Scope Check

**2. Placeholder scan:** No TBD/TODO in any code block. All steps have concrete code.

**3. Type consistency:** `EvalCase`, `GoldEntry` (with `result_sort_key` and `reviewed_by`), `CaseOutcome`, `CompareVerdict`, `ScoreReport`, `QueryResult`, `SliceConfig` — verified consistent across all tasks.

**4. Review fixes applied (from code-reviewer subagent):**
- [Critical] Fixed argparse bug in score_runner.py — uses sys.argv instead (Task 10)
- [Critical] Added `[tool.setuptools.packages.find]` to pyproject.toml (Task 1)
- [Important] Added `result_sort_key` and `reviewed_by` to GoldEntry (Task 11)
- [Important] Replaced `key=str` sort with `_stable_sort_key` in result_compare (Task 8)
- [Important] Added identifier quoting in schema_inspector (Task 5)
- [Important] Added `cd "$(dirname "$0")"` to score.sh (Task 10)
- [Important] Added weight deviation note referencing evaluation_framework.md (Task 9)
- [Important] Documented partial overlap tolerance limitation (Task 8)
- [Important] Changed hardcoded `len(cases) == 26` to `>= 26` (Task 7)
- [Important] Fixed double "Score breakdown" header (Task 10)
- [Suggestion] Centralized eval paths into conftest.py fixture (Task 3)
- [Suggestion] Added parallelization note for Tasks 4-6 vs 7-9
- [Suggestion] Added explicit post-M1 remaining work section
- [Suggestion] Documented data download as M2 prerequisite

---

Plan complete and saved to `docs/superpowers/plans/2026-04-08-m0-m1-foundation-and-evaluation.md`. Two execution options:

**1. Subagent-Driven (recommended)** - I dispatch a fresh subagent per task, review between tasks, fast iteration

**2. Inline Execution** - Execute tasks in this session using executing-plans, batch execution with checkpoints

Which approach?
