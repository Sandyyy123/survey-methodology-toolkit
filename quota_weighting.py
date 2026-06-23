"""
Quota planning and rake (iterative proportional fitting) weighting.

- build_quota_plan: turn benchmark population margins into per-cell completion
  targets for a given total sample.
- rake_weights: post-stratification weighting to correct residual skew on
  one or more marginal dimensions; reports the design effect and the
  effective sample size (Kish's formula).
"""
from __future__ import annotations

from collections import defaultdict


def build_quota_plan(total: int, margins: dict[str, dict[str, float]]
                     ) -> dict[str, dict[str, int]]:
    """margins: {dimension: {level: target_proportion}} -> per-cell counts."""
    plan: dict[str, dict[str, int]] = {}
    for dim, levels in margins.items():
        if abs(sum(levels.values()) - 1.0) > 0.01:
            raise ValueError(f"{dim} proportions must sum to 1.0")
        plan[dim] = {lvl: round(total * prop) for lvl, prop in levels.items()}
    return plan


def rake_weights(respondents: list[dict], targets: dict[str, dict[str, float]],
                 max_iter: int = 50, tol: float = 1e-6) -> list[float]:
    """Iterative proportional fitting on marginal targets (proportions)."""
    n = len(respondents)
    weights = [1.0] * n
    for _ in range(max_iter):
        max_change = 0.0
        for dim, levels in targets.items():
            sums: dict[str, float] = defaultdict(float)
            for w, r in zip(weights, respondents):
                sums[r[dim]] += w
            for i, r in enumerate(respondents):
                lvl = r[dim]
                target_count = levels[lvl] * n
                if sums[lvl] > 0:
                    factor = target_count / sums[lvl]
                    max_change = max(max_change, abs(factor - 1))
                    weights[i] *= factor
        if max_change < tol:
            break
    # normalize so weights average to 1
    mean_w = sum(weights) / n
    return [w / mean_w for w in weights]


def design_effect(weights: list[float]) -> float:
    """Kish design effect from unequal weighting."""
    n = len(weights)
    mean_w = sum(weights) / n
    var = sum((w - mean_w) ** 2 for w in weights) / n
    cv2 = var / (mean_w ** 2)
    return 1 + cv2


def effective_sample_size(weights: list[float]) -> float:
    return len(weights) / design_effect(weights)


if __name__ == "__main__":
    print("=== Quota plan for 1,068 completes ===")
    margins = {
        "age": {"18-24": 0.12, "25-44": 0.35, "45-64": 0.33, "65+": 0.20},
        "region": {"NE": 0.17, "MW": 0.21, "S": 0.38, "W": 0.24},
    }
    plan = build_quota_plan(1068, margins)
    for dim, cells in plan.items():
        print(f"  {dim}: {cells}")

    print("\n=== Rake weighting demo (skewed sample) ===")
    # Simulate a sample over-weighted to young respondents.
    sample = ([{"age": "18-24"}] * 400 + [{"age": "25-44"}] * 300
              + [{"age": "45-64"}] * 200 + [{"age": "65+"}] * 100)
    targets = {"age": margins["age"]}
    w = rake_weights(sample, targets)
    print(f"  n = {len(sample)}")
    print(f"  design effect      = {design_effect(w):.3f}")
    print(f"  effective sample n = {effective_sample_size(w):.0f}")
