from src.eval.case_loader import load_gold_snapshot, GoldEntry


def test_load_gold_snapshot_returns_entries(eval_cases_dir):
    entries = load_gold_snapshot(eval_cases_dir / "gold_result_snapshot_template.jsonl")
    assert len(entries) == 163
    assert all(isinstance(e, GoldEntry) for e in entries)


def test_gold_entry_fields(eval_cases_dir):
    entries = load_gold_snapshot(eval_cases_dir / "gold_result_snapshot_template.jsonl")
    e = entries[0]
    assert e.case_id is not None
    assert e.query is not None
    assert e.gold_sql == ""
    assert hasattr(e, "result_sort_key")
    assert hasattr(e, "reviewed_by")


def test_gold_snapshot_as_dict(eval_cases_dir):
    entries = load_gold_snapshot(eval_cases_dir / "gold_result_snapshot_template.jsonl")
    by_id = {e.case_id: e for e in entries}
    assert "MET-002" in by_id
    assert "EASY-001" in by_id
