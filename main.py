"""
Survey Methodology Toolkit -- runnable demo entry point.

Ties the three modules together into the workflow a methodologist follows:
  1. size the study   (sample_size)
  2. plan the audience (quota_weighting)
  3. clean the questions (bias_audit)

Run:  python main.py
"""
from __future__ import annotations

from sample_size import required_sample, subgroup_total
from quota_weighting import (build_quota_plan, rake_weights, design_effect,
                             effective_sample_size)
from bias_audit import audit_survey

US_CENSUS_MARGINS = {
    "age": {"18-24": 0.12, "25-44": 0.35, "45-64": 0.33, "65+": 0.20},
    "gender": {"female": 0.51, "male": 0.49},
    "region": {"NE": 0.17, "MW": 0.21, "S": 0.38, "W": 0.24},
}


def section(title: str) -> None:
    print("\n" + "=" * 64)
    print(title)
    print("=" * 64)


def step_1_size() -> int:
    section("STEP 1  -  Sample size")
    for moe in (0.05, 0.04, 0.03):
        r = required_sample(margin_of_error=moe)
        print(f"  +/-{moe:.0%} MoE @95% -> {r.n_final:,} completes")
    target = required_sample(margin_of_error=0.03).n_final
    print(f"\n  Subgroup-stable total (16 cells): "
          f"{subgroup_total(16, 100, headline=target):,}")
    return target


def step_2_audience(total: int) -> None:
    section("STEP 2  -  Audience (quotas + weighting)")
    plan = build_quota_plan(total, US_CENSUS_MARGINS)
    for dim, cells in plan.items():
        print(f"  {dim:8s}: {cells}")
    # show weighting recovering a skewed sample
    sample = ([{"age": "18-24"}] * 400 + [{"age": "25-44"}] * 300
              + [{"age": "45-64"}] * 200 + [{"age": "65+"}] * 100)
    w = rake_weights(sample, {"age": US_CENSUS_MARGINS["age"]})
    print(f"\n  Skewed n={len(sample)} -> design effect {design_effect(w):.2f}, "
          f"effective n {effective_sample_size(w):.0f}")


def step_3_questions() -> None:
    section("STEP 3  -  Question bias audit")
    survey = [
        {"text": "How much did you enjoy our easy-to-use product?"},
        {"text": "Was the service fast and friendly?"},
        {"text": "How would you rate your overall experience?",
         "scale": ["Strongly agree", "Agree", "Somewhat agree", "Disagree"]},
        {"text": "How would you rate the speed of service?",
         "scale": ["Very poor", "Poor", "Neutral", "Good", "Very good", "N/A"]},
    ]
    results = audit_survey(survey)
    clean = sum(r.is_clean for r in results)
    print(f"  {len(results)} questions -> {clean} clean, "
          f"{len(results) - clean} flagged\n")
    for r in results:
        print("  " + r.report().replace("\n", "\n  "))


if __name__ == "__main__":
    print("SURVEY METHODOLOGY TOOLKIT  -  demo run")
    total = step_1_size()
    step_2_audience(total)
    step_3_questions()
    print("\nDone. See README.md for how each step maps to a deliverable.")
