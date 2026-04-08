#!/usr/bin/env python3
"""Rebuild eval cases: dedup, add eval_tier, add diverse patterns, add easy baselines."""

from __future__ import annotations

import json
from pathlib import Path

EVAL_DIR = Path(__file__).resolve().parent.parent / "eval" / "cases"

CORE_AGENCIES = {
    "Department of Defense",
    "Department of Health and Human Services",
    "NASA",
    "Department of Homeland Security",
    "General Services Administration",
}
EXTENDED_AGENCIES = {
    "Department of Veterans Affairs",
    "Department of Energy",
    "Department of Transportation",
}
ALL_AGENCIES = CORE_AGENCIES | EXTENDED_AGENCIES


def detect_agency(case: dict) -> str | None:
    """Extract primary agency from expected_semantics or query text."""
    sem = case.get("expected_semantics", {})
    scope = sem.get("scope", {})
    for key in ("agency", "awarding_agency"):
        if key in scope:
            return scope[key]
    query = case.get("query", "")
    for ag in sorted(ALL_AGENCIES, key=len, reverse=True):
        if ag.lower() in query.lower():
            return ag
    return None


def assign_tier(case: dict) -> str:
    ag = detect_agency(case)
    if ag in CORE_AGENCIES:
        return "core"
    if ag in EXTENDED_AGENCIES:
        return "extended"
    # Entity resolution cases without clear agency -> check entity inputs
    er = case.get("expected_semantics", {}).get("entity_resolution", {})
    canonical = er.get("canonical", "")
    for a in CORE_AGENCIES:
        if a.lower() in canonical.lower():
            return "core"
    return "core"  # default to core for recipient-focused cases


def dedup_cases(cases: list[dict]) -> list[dict]:
    """Keep first occurrence of each unique query text."""
    seen = set()
    result = []
    for c in cases:
        q = c["query"].strip()
        if q not in seen:
            seen.add(q)
            result.append(c)
    return result


def renumber(cases: list[dict], prefix: str) -> list[dict]:
    """Re-assign sequential case_ids."""
    for i, c in enumerate(cases, 1):
        c["case_id"] = f"{prefix}-{i:03d}"
    return cases


# ---------------------------------------------------------------------------
# New diverse cases per category
# ---------------------------------------------------------------------------

def new_metric_ambiguity_cases() -> list[dict]:
    """Add diverse metric ambiguity patterns not in the originals."""
    cases = []

    def _case(cid, pol, beh, diff, query, sem, notes):
        return {
            "case_id": cid, "category": "metric_ambiguity",
            "polarity": pol, "expected_behavior": beh, "difficulty": diff,
            "query": query, "tags": ["metric", "usaspending", "contracts"],
            "expected_semantics": sem, "notes": notes,
        }

    # --- Diverse hard/ambiguous ---
    cases.append(_case("", "ambiguous", "clarify", "hard",
        "What is the total spending by NASA on contracts in fiscal year 2024?",
        {"scope": {"agency": "NASA", "award_type": "contract_only"},
         "time_axis": {"type": "fiscal_year", "value": 2024},
         "clarification_targets": ["metric_definition"]},
        "Spending is ambiguous: obligation, outlay, or award amount?"))

    cases.append(_case("", "ambiguous", "clarify", "hard",
        "How much funding did Department of Defense allocate to contracts last year?",
        {"scope": {"agency": "Department of Defense", "award_type": "contract_only"},
         "time_axis": {"type": "fiscal_year_relative", "value": "previous_fy"},
         "clarification_targets": ["metric_definition"]},
        "Funding/allocate is ambiguous: obligation vs appropriation vs outlay."))

    cases.append(_case("", "ambiguous", "clarify", "hard",
        "Compare the total value of DHS contracts between fiscal year 2024 and 2025.",
        {"scope": {"agency": "Department of Homeland Security", "award_type": "contract_only"},
         "comparison": {"left": {"type": "fiscal_year", "value": 2024},
                        "right": {"type": "fiscal_year", "value": 2025}},
         "clarification_targets": ["metric_definition"]},
        "Total value is ambiguous between obligation, outlay, and award amount."))

    cases.append(_case("", "ambiguous", "clarify", "hard",
        "What percentage of GSA contracts exceeded $1 million in value?",
        {"scope": {"agency": "General Services Administration", "award_type": "contract_only"},
         "clarification_targets": ["metric_definition", "threshold_metric"]},
        "Value could be obligation, outlay, or total award amount. Threshold metric unclear."))

    cases.append(_case("", "ambiguous", "clarify", "hard",
        "Show the average contract size for HHS in fiscal year 2025.",
        {"scope": {"agency": "Department of Health and Human Services", "award_type": "contract_only"},
         "time_axis": {"type": "fiscal_year", "value": 2025},
         "clarification_targets": ["metric_definition"]},
        "Average contract size: by obligation? outlay? award amount? Per award or per transaction?"))

    # --- Diverse hard/positive ---
    cases.append(_case("", "positive", "answer", "hard",
        "Sum total obligations, not outlays, for all NASA contracts in fiscal year 2025.",
        {"metric": "total_obligation", "scope": {"agency": "NASA", "award_type": "contract_only"},
         "time_axis": {"type": "fiscal_year", "value": 2025},
         "must_not_use": ["total_outlay", "total_award_amount"]},
        "Explicit obligation; must not substitute outlay."))

    cases.append(_case("", "positive", "answer", "hard",
        "What is the total outlay for Department of Defense contracts in fiscal year 2024?",
        {"metric": "total_outlay", "scope": {"agency": "Department of Defense", "award_type": "contract_only"},
         "time_axis": {"type": "fiscal_year", "value": 2024},
         "must_not_use": ["total_obligation", "total_award_amount"]},
        "Explicit outlay metric."))

    cases.append(_case("", "positive", "answer", "hard",
        "Count distinct contract awards, not transaction modifications, for DHS in fiscal year 2025.",
        {"metric": "distinct_award_count", "scope": {"agency": "Department of Homeland Security", "award_type": "contract_only"},
         "time_axis": {"type": "fiscal_year", "value": 2025},
         "must_not_use": ["transaction_count"]},
        "Must count distinct awards, not transaction rows."))

    cases.append(_case("", "positive", "answer", "medium",
        "What is the median obligation per contract for GSA in fiscal year 2024?",
        {"metric": "median_obligation", "scope": {"agency": "General Services Administration", "award_type": "contract_only"},
         "time_axis": {"type": "fiscal_year", "value": 2024}},
        "Statistical aggregate: median, not sum or average."))

    cases.append(_case("", "positive", "answer", "medium",
        "Show the ratio of obligations to outlays for HHS contracts in fiscal year 2025.",
        {"metric": "obligation_outlay_ratio",
         "scope": {"agency": "Department of Health and Human Services", "award_type": "contract_only"},
         "time_axis": {"type": "fiscal_year", "value": 2025}},
        "Ratio metric: tests multi-metric computation."))

    return cases


def new_time_interpretation_cases() -> list[dict]:
    cases = []

    def _case(pol, beh, diff, query, sem, notes):
        return {
            "case_id": "", "category": "time_interpretation",
            "polarity": pol, "expected_behavior": beh, "difficulty": diff,
            "query": query, "tags": ["time", "period", "fiscal_vs_calendar"],
            "expected_semantics": sem, "notes": notes,
        }

    # --- Ambiguous ---
    cases.append(_case("ambiguous", "clarify", "hard",
        "Show NASA contract obligations for last year.",
        {"scope": {"agency": "NASA", "award_type": "contract_only"},
         "clarification_targets": ["time_axis"]},
        "Last year: fiscal or calendar?"))

    cases.append(_case("ambiguous", "clarify", "hard",
        "How much did DoD spend on contracts recently?",
        {"scope": {"agency": "Department of Defense", "award_type": "contract_only"},
         "clarification_targets": ["time_axis", "metric_definition"]},
        "Recently is undefined. Metric also ambiguous."))

    cases.append(_case("ambiguous", "clarify", "hard",
        "Show year-over-year growth in GSA contract awards.",
        {"scope": {"agency": "General Services Administration", "award_type": "contract_only"},
         "clarification_targets": ["time_axis", "metric_definition"]},
        "Which years? Fiscal or calendar? Growth in count or dollar amount?"))

    # --- Positive ---
    cases.append(_case("positive", "answer", "hard",
        "Show NASA contract obligations between October 2023 and March 2024.",
        {"metric": "total_obligation",
         "time_axis": {"type": "date_range", "start": "2023-10-01", "end": "2024-03-31"},
         "scope": {"agency": "NASA", "award_type": "contract_only"}},
        "Explicit date range; happens to be FY2024 H1."))

    cases.append(_case("positive", "answer", "hard",
        "How many DHS contracts were awarded in fiscal year 2025 Q1?",
        {"metric": "award_count",
         "time_axis": {"type": "fiscal_quarter", "value": "FY2025-Q1"},
         "scope": {"agency": "Department of Homeland Security", "award_type": "contract_only"}},
        "Explicit fiscal quarter."))

    cases.append(_case("positive", "answer", "hard",
        "Show month-by-month obligations for HHS contracts in fiscal year 2024.",
        {"metric": "total_obligation", "group_by": "month",
         "time_axis": {"type": "fiscal_year", "value": 2024},
         "scope": {"agency": "Department of Health and Human Services", "award_type": "contract_only"}},
        "Monthly breakdown within a fiscal year."))

    cases.append(_case("positive", "answer", "hard",
        "Compare DoD contract obligations in calendar year 2024 versus calendar year 2023.",
        {"metric": "total_obligation",
         "comparison": {"left": {"type": "calendar_year", "value": 2024},
                        "right": {"type": "calendar_year", "value": 2023}},
         "scope": {"agency": "Department of Defense", "award_type": "contract_only"}},
        "Explicit calendar year comparison."))

    cases.append(_case("positive", "answer", "medium",
        "List GSA contracts with action date in January 2025.",
        {"metric": "row_list",
         "time_axis": {"type": "month", "value": "2025-01", "date_field": "action_date"},
         "scope": {"agency": "General Services Administration", "award_type": "contract_only"}},
        "Specific month + explicit date field."))

    cases.append(_case("positive", "answer", "hard",
        "What were total NASA contract obligations year-to-date in fiscal year 2025?",
        {"metric": "total_obligation",
         "time_axis": {"type": "fiscal_ytd", "value": "FY2025"},
         "scope": {"agency": "NASA", "award_type": "contract_only"}},
        "Year-to-date within fiscal year."))

    cases.append(_case("positive", "answer", "hard",
        "Show the trailing 12-month obligation total for DHS contracts as of March 2025.",
        {"metric": "total_obligation",
         "time_axis": {"type": "trailing_months", "months": 12, "anchor": "2025-03"},
         "scope": {"agency": "Department of Homeland Security", "award_type": "contract_only"}},
        "Rolling window time interpretation."))

    return cases


def new_scope_state_cases() -> list[dict]:
    cases = []

    def _case(pol, beh, diff, query, sem, notes):
        return {
            "case_id": "", "category": "scope_state",
            "polarity": pol, "expected_behavior": beh, "difficulty": diff,
            "query": query, "tags": ["scope", "status", "contracts"],
            "expected_semantics": sem, "notes": notes,
        }

    cases.append(_case("ambiguous", "clarify", "hard",
        "Show all DoD awards including grants and contracts.",
        {"scope": {"agency": "Department of Defense"},
         "clarification_targets": ["scope_state"]},
        "Dataset only has contracts. System should clarify that grants are out of scope."))

    cases.append(_case("positive", "answer", "hard",
        "List competitive contracts only for NASA in fiscal year 2025.",
        {"metric": "award_count",
         "time_axis": {"type": "fiscal_year", "value": 2025},
         "scope": {"agency": "NASA", "award_type": "contract_only", "competition_type": "competitive_only"}},
        "Tests competition type filter."))

    cases.append(_case("positive", "answer", "hard",
        "Show HHS contracts where the funding agency differs from the awarding agency.",
        {"metric": "row_list",
         "scope": {"agency": "Department of Health and Human Services", "award_type": "contract_only",
                   "filter": "funding_agency != awarding_agency"}},
        "Tests awarding vs funding agency distinction."))

    cases.append(_case("positive", "answer", "hard",
        "How many GSA contracts have a place of performance outside the United States?",
        {"metric": "award_count",
         "scope": {"agency": "General Services Administration", "award_type": "contract_only",
                   "pop_filter": "foreign_only"}},
        "Tests place of performance filter."))

    cases.append(_case("ambiguous", "clarify", "hard",
        "Show DHS contract obligations including modifications and base awards.",
        {"scope": {"agency": "Department of Homeland Security", "award_type": "contract_only"},
         "clarification_targets": ["scope_state"]},
        "Are modifications separate rows? Should they be summed into base awards?"))

    cases.append(_case("positive", "answer", "hard",
        "List only small business set-aside contracts for DoD in fiscal year 2024.",
        {"metric": "award_count",
         "time_axis": {"type": "fiscal_year", "value": 2024},
         "scope": {"agency": "Department of Defense", "award_type": "contract_only",
                   "set_aside": "small_business"}},
        "Tests set-aside type filter."))

    cases.append(_case("positive", "answer", "hard",
        "Show NASA contracts where the NAICS code is 541715.",
        {"metric": "row_list",
         "scope": {"agency": "NASA", "award_type": "contract_only",
                   "naics_code": "541715"}},
        "Tests NAICS code filter on contracts."))

    cases.append(_case("ambiguous", "clarify", "hard",
        "What is the total value of all HHS procurement actions?",
        {"scope": {"agency": "Department of Health and Human Services"},
         "clarification_targets": ["metric_definition", "scope_state"]},
        "Procurement actions vs awards vs transactions: which grain?"))

    return cases


def new_entity_resolution_cases() -> list[dict]:
    cases = []

    def _case(pol, beh, diff, query, sem, notes):
        return {
            "case_id": "", "category": "entity_resolution",
            "polarity": pol, "expected_behavior": beh, "difficulty": diff,
            "query": query, "tags": ["entity", "alias", "normalization"],
            "expected_semantics": sem, "notes": notes,
        }

    cases.append(_case("positive", "answer", "hard",
        "Show contracts for Raytheon Technologies and RTX Corp as the same entity.",
        {"metric": "award_count", "scope": {"award_type": "contract_only"},
         "entity_resolution": {"type": "recipient", "inputs": ["Raytheon Technologies", "RTX Corp"],
                               "canonical": "RTX Corporation", "deduplicate": True}},
        "Parent company rename: Raytheon -> RTX."))

    cases.append(_case("positive", "answer", "hard",
        "How many contracts went to LM from NASA in fiscal year 2025?",
        {"metric": "award_count",
         "time_axis": {"type": "fiscal_year", "value": 2025},
         "scope": {"agency": "NASA", "award_type": "contract_only"},
         "entity_resolution": {"type": "recipient", "input": "LM", "canonical": "Lockheed Martin"}},
        "Two-letter abbreviation for a major contractor."))

    cases.append(_case("ambiguous", "clarify", "hard",
        "Show contracts for BAH in fiscal year 2024.",
        {"time_axis": {"type": "fiscal_year", "value": 2024},
         "scope": {"award_type": "contract_only"},
         "entity_resolution": {"type": "recipient_or_agency", "input": "BAH"},
         "clarification_targets": ["entity_identity"]},
        "BAH could be Booz Allen Hamilton or an unknown abbreviation."))

    cases.append(_case("positive", "answer", "medium",
        "Count awards for 'Northrop Grumman' and 'NORTHROP GRUMMAN CORP' as the same recipient.",
        {"metric": "award_count", "scope": {"award_type": "contract_only"},
         "entity_resolution": {"type": "recipient",
                               "inputs": ["Northrop Grumman", "NORTHROP GRUMMAN CORP"],
                               "canonical": "Northrop Grumman", "deduplicate": True}},
        "Casing + legal suffix normalization."))

    cases.append(_case("positive", "answer", "hard",
        "What are the top 5 recipients for the National Aeronautics and Space Administration in fiscal year 2024?",
        {"metric": "total_obligation", "group_by": "recipient",
         "ranking": {"metric": "total_obligation", "order": "desc", "limit": 5},
         "time_axis": {"type": "fiscal_year", "value": 2024},
         "scope": {"agency": "NASA", "award_type": "contract_only"},
         "entity_resolution": {"type": "agency", "input": "National Aeronautics and Space Administration",
                               "canonical": "NASA"}},
        "Full agency name must resolve to the canonical short form."))

    cases.append(_case("ambiguous", "clarify", "hard",
        "Show contracts for General Dynamics in fiscal year 2025. Do you mean the parent company or a specific subsidiary?",
        {"time_axis": {"type": "fiscal_year", "value": 2025},
         "scope": {"award_type": "contract_only"},
         "entity_resolution": {"type": "recipient", "input": "General Dynamics"},
         "clarification_targets": ["entity_identity"]},
        "Parent vs subsidiary ambiguity."))

    cases.append(_case("positive", "answer", "medium",
        "Show obligations for DEPT OF DEFENSE in fiscal year 2024.",
        {"metric": "total_obligation",
         "time_axis": {"type": "fiscal_year", "value": 2024},
         "scope": {"agency": "Department of Defense", "award_type": "contract_only"},
         "entity_resolution": {"type": "agency", "input": "DEPT OF DEFENSE",
                               "canonical": "Department of Defense"}},
        "ALL CAPS abbreviation for agency."))

    cases.append(_case("positive", "answer", "hard",
        "List contracts where the recipient name contains 'Boeing' regardless of subsidiary.",
        {"metric": "row_list", "scope": {"award_type": "contract_only"},
         "entity_resolution": {"type": "recipient", "input": "Boeing",
                               "match_mode": "contains"}},
        "Fuzzy/contains match across subsidiaries."))

    return cases


def new_missingness_linked_cases() -> list[dict]:
    cases = []

    def _case(pol, beh, diff, query, sem, notes):
        return {
            "case_id": "", "category": "missingness_linked",
            "polarity": pol, "expected_behavior": beh, "difficulty": diff,
            "query": query, "tags": ["missingness", "linked_data", "null_vs_zero"],
            "expected_semantics": sem, "notes": notes,
        }

    cases.append(_case("positive", "answer", "hard",
        "What fraction of NASA contracts are missing a NAICS code?",
        {"metric": "missing_ratio", "field": "naics_code",
         "scope": {"agency": "NASA", "award_type": "contract_only"}},
        "Data completeness check on classification field."))

    cases.append(_case("positive", "answer", "hard",
        "Exclude contracts with no recipient name from DoD totals in fiscal year 2025.",
        {"metric": "total_obligation",
         "time_axis": {"type": "fiscal_year", "value": 2025},
         "scope": {"agency": "Department of Defense", "award_type": "contract_only"},
         "missingness_rule": {"field": "recipient_name", "action": "exclude_missing"}},
        "Explicit exclusion of incomplete records."))

    cases.append(_case("ambiguous", "clarify", "hard",
        "Show the total obligation for GSA contracts, treating missing outlays as zero.",
        {"scope": {"agency": "General Services Administration", "award_type": "contract_only"},
         "clarification_targets": ["missingness_policy"]},
        "User wants to impute missing as zero; system should confirm this is intentional."))

    cases.append(_case("positive", "answer", "hard",
        "How many HHS contracts have a recipient state but no recipient ZIP code?",
        {"metric": "row_count",
         "scope": {"agency": "Department of Health and Human Services", "award_type": "contract_only"},
         "missingness_rule": {"has_field": "recipient_state", "missing_field": "recipient_zip"}},
        "Cross-field completeness check."))

    cases.append(_case("positive", "answer", "hard",
        "Count DHS contracts where the PSC code is populated versus where it is null.",
        {"metric": "bucketed_count",
         "scope": {"agency": "Department of Homeland Security", "award_type": "contract_only"},
         "missingness_rule": {"field": "psc_code", "buckets": ["populated", "missing"]}},
        "Binary completeness bucket for a classification field."))

    return cases


def new_join_aggregation_cases() -> list[dict]:
    cases = []

    def _case(pol, beh, diff, query, sem, notes):
        return {
            "case_id": "", "category": "join_aggregation",
            "polarity": pol, "expected_behavior": beh, "difficulty": diff,
            "query": query, "tags": ["join", "aggregation", "dedup"],
            "expected_semantics": sem, "notes": notes,
        }

    cases.append(_case("positive", "answer", "hard",
        "For each awarding agency, show the number of unique recipients in fiscal year 2024.",
        {"metric": "unique_recipient_count", "group_by": "awarding_agency",
         "time_axis": {"type": "fiscal_year", "value": 2024},
         "scope": {"award_type": "contract_only"},
         "aggregation_rules": {"count_distinct": "recipient"}},
        "COUNT DISTINCT on grouped aggregation."))

    cases.append(_case("positive", "answer", "hard",
        "Show the running total of obligations for NASA contracts in fiscal year 2025, ordered by action date.",
        {"metric": "running_total_obligation",
         "time_axis": {"type": "fiscal_year", "value": 2025},
         "scope": {"agency": "NASA", "award_type": "contract_only"},
         "aggregation_rules": {"window": "running_sum", "order_by": "action_date"}},
        "Window function: running sum."))

    cases.append(_case("ambiguous", "clarify", "hard",
        "Show the average obligation per recipient per agency for fiscal year 2024.",
        {"time_axis": {"type": "fiscal_year", "value": 2024},
         "scope": {"award_type": "contract_only"},
         "clarification_targets": ["aggregation_definition"]},
        "Average of what? Per award then averaged by recipient? Or total per recipient?"))

    cases.append(_case("positive", "answer", "hard",
        "Rank agencies by the total number of contract awards in fiscal year 2025, showing only agencies with more than 100 awards.",
        {"metric": "award_count", "group_by": "awarding_agency",
         "time_axis": {"type": "fiscal_year", "value": 2025},
         "scope": {"award_type": "contract_only"},
         "aggregation_rules": {"having": "award_count > 100", "order_by": "award_count DESC"}},
        "HAVING clause filter on grouped result."))

    cases.append(_case("positive", "answer", "hard",
        "For DoD, show the top 5 recipients whose fiscal year 2025 obligations exceeded their fiscal year 2024 obligations.",
        {"metric": "total_obligation",
         "comparison": {"left": {"type": "fiscal_year", "value": 2025},
                        "right": {"type": "fiscal_year", "value": 2024}},
         "scope": {"agency": "Department of Defense", "award_type": "contract_only"},
         "aggregation_rules": {"self_join": True, "filter": "fy2025 > fy2024",
                               "ranking": {"limit": 5}}},
        "Self-join year-over-year comparison with ranking."))

    return cases


def easy_baseline_cases() -> list[dict]:
    """Simple, unambiguous queries that any correct system should handle."""
    cases = []

    def _case(query, sem, notes):
        return {
            "case_id": "", "category": "easy_baseline",
            "polarity": "positive", "expected_behavior": "answer", "difficulty": "easy",
            "query": query, "tags": ["baseline", "usaspending", "contracts"],
            "expected_semantics": sem, "notes": notes,
        }

    cases.append(_case(
        "How many contracts did NASA award in fiscal year 2024?",
        {"metric": "award_count",
         "time_axis": {"type": "fiscal_year", "value": 2024},
         "scope": {"agency": "NASA", "award_type": "contract_only"}},
        "Simple count with clear scope."))

    cases.append(_case(
        "What is the total obligation for Department of Defense contracts in fiscal year 2025?",
        {"metric": "total_obligation",
         "time_axis": {"type": "fiscal_year", "value": 2025},
         "scope": {"agency": "Department of Defense", "award_type": "contract_only"}},
        "Simple sum with clear metric."))

    cases.append(_case(
        "List the top 10 recipients by obligation for HHS contracts in fiscal year 2024.",
        {"metric": "total_obligation", "group_by": "recipient",
         "ranking": {"metric": "total_obligation", "order": "desc", "limit": 10},
         "time_axis": {"type": "fiscal_year", "value": 2024},
         "scope": {"agency": "Department of Health and Human Services", "award_type": "contract_only"}},
        "Top-N with explicit metric and scope."))

    cases.append(_case(
        "Show the total obligation for DHS contracts in fiscal year 2025.",
        {"metric": "total_obligation",
         "time_axis": {"type": "fiscal_year", "value": 2025},
         "scope": {"agency": "Department of Homeland Security", "award_type": "contract_only"}},
        "Simple sum."))

    cases.append(_case(
        "How many contract awards did GSA make in fiscal year 2024?",
        {"metric": "award_count",
         "time_axis": {"type": "fiscal_year", "value": 2024},
         "scope": {"agency": "General Services Administration", "award_type": "contract_only"}},
        "Simple count."))

    cases.append(_case(
        "What is the total outlay for NASA contracts in fiscal year 2025?",
        {"metric": "total_outlay",
         "time_axis": {"type": "fiscal_year", "value": 2025},
         "scope": {"agency": "NASA", "award_type": "contract_only"}},
        "Simple outlay sum; metric is explicit."))

    cases.append(_case(
        "Show all contract awards for Department of Defense with Lockheed Martin in fiscal year 2024.",
        {"metric": "row_list",
         "time_axis": {"type": "fiscal_year", "value": 2024},
         "scope": {"agency": "Department of Defense", "award_type": "contract_only"},
         "entity_resolution": {"type": "recipient", "input": "Lockheed Martin", "canonical": "Lockheed Martin"}},
        "Simple filter by agency + recipient + year."))

    cases.append(_case(
        "Count the number of contracts for HHS in fiscal year 2025.",
        {"metric": "award_count",
         "time_axis": {"type": "fiscal_year", "value": 2025},
         "scope": {"agency": "Department of Health and Human Services", "award_type": "contract_only"}},
        "Simple count."))

    cases.append(_case(
        "What is the largest single contract obligation for DHS in fiscal year 2024?",
        {"metric": "max_obligation",
         "time_axis": {"type": "fiscal_year", "value": 2024},
         "scope": {"agency": "Department of Homeland Security", "award_type": "contract_only"}},
        "MAX aggregate, simple."))

    cases.append(_case(
        "Show the number of unique recipients for GSA contracts in fiscal year 2025.",
        {"metric": "unique_recipient_count",
         "time_axis": {"type": "fiscal_year", "value": 2025},
         "scope": {"agency": "General Services Administration", "award_type": "contract_only"}},
        "COUNT DISTINCT recipients, simple."))

    cases.append(_case(
        "List Department of Defense contracts with obligations over $10 million in fiscal year 2024.",
        {"metric": "row_list",
         "time_axis": {"type": "fiscal_year", "value": 2024},
         "scope": {"agency": "Department of Defense", "award_type": "contract_only",
                   "filter": "obligation > 10000000"}},
        "Simple threshold filter."))

    cases.append(_case(
        "What is the average obligation per contract for NASA in fiscal year 2025?",
        {"metric": "avg_obligation",
         "time_axis": {"type": "fiscal_year", "value": 2025},
         "scope": {"agency": "NASA", "award_type": "contract_only"}},
        "AVG aggregate, simple."))

    cases.append(_case(
        "Show the bottom 5 agencies by total contract obligations in fiscal year 2024.",
        {"metric": "total_obligation", "group_by": "awarding_agency",
         "ranking": {"metric": "total_obligation", "order": "asc", "limit": 5},
         "time_axis": {"type": "fiscal_year", "value": 2024},
         "scope": {"award_type": "contract_only"}},
        "Bottom-N ranking, ascending order."))

    cases.append(_case(
        "How many HHS contracts were awarded in fiscal year 2024 Q2?",
        {"metric": "award_count",
         "time_axis": {"type": "fiscal_quarter", "value": "FY2024-Q2"},
         "scope": {"agency": "Department of Health and Human Services", "award_type": "contract_only"}},
        "Simple count by fiscal quarter."))

    cases.append(_case(
        "Show the total obligation for Department of Defense contracts with Boeing in fiscal year 2025.",
        {"metric": "total_obligation",
         "time_axis": {"type": "fiscal_year", "value": 2025},
         "scope": {"agency": "Department of Defense", "award_type": "contract_only"},
         "entity_resolution": {"type": "recipient", "input": "Boeing", "canonical": "Boeing"}},
        "Simple sum filtered by recipient."))

    cases.append(_case(
        "List all awarding agencies that had contract obligations in fiscal year 2024.",
        {"metric": "agency_list",
         "time_axis": {"type": "fiscal_year", "value": 2024},
         "scope": {"award_type": "contract_only"}},
        "Simple distinct agency list."))

    cases.append(_case(
        "What is the total number of contract transactions for DHS in fiscal year 2025?",
        {"metric": "transaction_count",
         "time_axis": {"type": "fiscal_year", "value": 2025},
         "scope": {"agency": "Department of Homeland Security", "award_type": "contract_only"}},
        "Transaction count, not award count. Simple."))

    cases.append(_case(
        "Show obligations by awarding agency for fiscal year 2024, sorted descending.",
        {"metric": "total_obligation", "group_by": "awarding_agency",
         "ranking": {"metric": "total_obligation", "order": "desc"},
         "time_axis": {"type": "fiscal_year", "value": 2024},
         "scope": {"award_type": "contract_only"}},
        "Group by + sort, straightforward."))

    cases.append(_case(
        "How many GSA contracts have a NAICS code starting with 54?",
        {"metric": "award_count",
         "scope": {"agency": "General Services Administration", "award_type": "contract_only",
                   "filter": "naics_code LIKE '54%'"}},
        "Simple prefix filter on classification."))

    cases.append(_case(
        "What is the minimum obligation among NASA contracts in fiscal year 2024?",
        {"metric": "min_obligation",
         "time_axis": {"type": "fiscal_year", "value": 2024},
         "scope": {"agency": "NASA", "award_type": "contract_only"}},
        "MIN aggregate, simple."))

    return cases


def main():
    # --- Step 1: Load and dedup existing cases by category ---
    categories = [
        "metric_ambiguity", "time_interpretation", "scope_state",
        "entity_resolution", "missingness_linked", "join_aggregation",
    ]
    prefix_map = {
        "metric_ambiguity": "MET",
        "time_interpretation": "TIME",
        "scope_state": "SCOPE",
        "entity_resolution": "ENTITY",
        "missingness_linked": "MISS",
        "join_aggregation": "JOIN",
        "easy_baseline": "EASY",
    }

    all_cases = {}
    for cat in categories:
        fpath = EVAL_DIR / f"{cat}.jsonl"
        with open(fpath) as f:
            cases = [json.loads(line) for line in f if line.strip()]
        deduped = dedup_cases(cases)
        print(f"{cat}: {len(cases)} -> {len(deduped)} (deduped)")
        all_cases[cat] = deduped

    # --- Step 2: Add new diverse cases ---
    new_cases = {
        "metric_ambiguity": new_metric_ambiguity_cases(),
        "time_interpretation": new_time_interpretation_cases(),
        "scope_state": new_scope_state_cases(),
        "entity_resolution": new_entity_resolution_cases(),
        "missingness_linked": new_missingness_linked_cases(),
        "join_aggregation": new_join_aggregation_cases(),
    }

    for cat, nc in new_cases.items():
        existing_queries = {c["query"].strip() for c in all_cases[cat]}
        added = [c for c in nc if c["query"].strip() not in existing_queries]
        all_cases[cat].extend(added)
        print(f"{cat}: +{len(added)} new diverse cases = {len(all_cases[cat])} total")

    # --- Step 3: Add easy baseline ---
    easy = easy_baseline_cases()
    all_cases["easy_baseline"] = easy
    print(f"easy_baseline: {len(easy)} new cases")

    # --- Step 4: Assign eval_tier and renumber ---
    for cat, cases in all_cases.items():
        prefix = prefix_map[cat]
        for c in cases:
            c["eval_tier"] = assign_tier(c)
        renumber(cases, prefix)

    # --- Step 5: Write per-category files ---
    combined = []
    for cat in list(categories) + ["easy_baseline"]:
        cases = all_cases[cat]
        fpath = EVAL_DIR / f"{cat}.jsonl"
        with open(fpath, "w") as f:
            for c in cases:
                f.write(json.dumps(c, ensure_ascii=False) + "\n")
        combined.extend(cases)
        print(f"Wrote {len(cases)} cases to {fpath.name}")

    # --- Step 6: Write combined file ---
    combined_path = EVAL_DIR / "combined_hard_cases.jsonl"
    with open(combined_path, "w") as f:
        for c in combined:
            f.write(json.dumps(c, ensure_ascii=False) + "\n")
    print(f"Wrote {len(combined)} total cases to combined_hard_cases.jsonl")

    # --- Step 7: Rebuild gold template for answer cases ---
    gold_cases = []
    for c in combined:
        if c["expected_behavior"] == "answer":
            gold_cases.append({
                "case_id": c["case_id"],
                "query": c["query"],
                "expected_behavior": "answer",
                "eval_tier": c["eval_tier"],
                "canonical_result_hash": "",
                "canonical_result_format": "json_rows",
                "result_sort_key": "",
                "gold_sql": "",
                "reviewed_by": "",
                "notes": "Backfill after locking the USAspending slice and reviewing the reference query.",
            })
    gold_path = EVAL_DIR / "gold_result_snapshot_template.jsonl"
    with open(gold_path, "w") as f:
        for g in gold_cases:
            f.write(json.dumps(g, ensure_ascii=False) + "\n")
    print(f"Wrote {len(gold_cases)} gold template entries")

    # --- Step 8: Write MANIFEST ---
    manifest_path = EVAL_DIR / "MANIFEST.md"
    lines = ["# Hard-case manifest\n\n"]
    lines.append("Counts by category, tier, and expected behavior:\n\n")

    for cat in list(categories) + ["easy_baseline"]:
        cases = all_cases[cat]
        answer_ct = sum(1 for c in cases if c["expected_behavior"] == "answer")
        clarify_ct = sum(1 for c in cases if c["expected_behavior"] == "clarify")
        core_ct = sum(1 for c in cases if c["eval_tier"] == "core")
        ext_ct = sum(1 for c in cases if c["eval_tier"] == "extended")
        parts = []
        if answer_ct:
            parts.append(f"answer={answer_ct}")
        if clarify_ct:
            parts.append(f"clarify={clarify_ct}")
        parts.append(f"core={core_ct}")
        parts.append(f"extended={ext_ct}")
        lines.append(f"- {cat}: {len(cases)} cases | {', '.join(parts)}\n")

    lines.append(f"\nTotal cases: {len(combined)}\n")
    core_total = sum(1 for c in combined if c["eval_tier"] == "core")
    ext_total = sum(1 for c in combined if c["eval_tier"] == "extended")
    lines.append(f"Core tier: {core_total} | Extended tier: {ext_total}\n")
    lines.append(f"\nGold template entries (answer cases): {len(gold_cases)}\n")
    lines.append("\nUse `combined_hard_cases.jsonl` for scoring pipelines.\n")
    lines.append("`--quick` uses core tier only. `--full` uses core + extended.\n")

    with open(manifest_path, "w") as f:
        f.writelines(lines)
    print(f"Wrote MANIFEST.md")

    # --- Summary ---
    print("\n=== Summary ===")
    for cat in list(categories) + ["easy_baseline"]:
        print(f"  {cat}: {len(all_cases[cat])}")
    print(f"  TOTAL: {len(combined)}")
    print(f"  Unique queries: {len(set(c['query'] for c in combined))}")


if __name__ == "__main__":
    main()
