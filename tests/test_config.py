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
