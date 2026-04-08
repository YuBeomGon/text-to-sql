from src.config import load_config


def test_load_config_returns_core_agencies():
    cfg = load_config()
    assert "NASA" in cfg.core_agencies
    assert len(cfg.core_agencies) == 3


def test_load_config_returns_pending_agencies():
    cfg = load_config()
    assert "Department of Defense" in cfg.pending_agencies
    assert "General Services Administration" in cfg.pending_agencies


def test_load_config_returns_fiscal_years():
    cfg = load_config()
    assert cfg.fiscal_years == [2025]


def test_load_config_returns_paths():
    cfg = load_config()
    assert cfg.datasets_dir == "datasets"
    assert cfg.eval_cases_dir == "eval/cases"
