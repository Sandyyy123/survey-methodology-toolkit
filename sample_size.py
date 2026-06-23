"""
Sample-size determination for survey research.

Implements Cochran's formula for estimating a population proportion, the
finite-population correction, a design-effect adjustment for weighted/clustered
designs, and a subgroup-aware sizer.

References:
    Cochran, W. G. (1977). Sampling Techniques, 3rd ed.
"""
from __future__ import annotations

from dataclasses import dataclass

# Two-sided z critical values for common confidence levels.
Z = {0.90: 1.645, 0.95: 1.960, 0.99: 2.576}


@dataclass
class SampleSizeResult:
    confidence: float
    margin_of_error: float
    p: float
    n_infinite: int
    n_corrected: int
    population: int | None
    design_effect: float
    n_final: int

    def summary(self) -> str:
        pop = "infinite" if self.population is None else f"{self.population:,}"
        return (
            f"Confidence {self.confidence:.0%}, MoE +/-{self.margin_of_error:.1%}, "
            f"p={self.p}\n"
            f"  Population:        {pop}\n"
            f"  n (uncorrected):  {self.n_infinite:,}\n"
            f"  n (finite-corr):  {self.n_corrected:,}\n"
            f"  Design effect:    {self.design_effect}\n"
            f"  REQUIRED COMPLETES: {self.n_final:,}"
        )


def cochran_n(p: float = 0.5, margin_of_error: float = 0.03,
              confidence: float = 0.95) -> float:
    """Base sample size for estimating a proportion (infinite population)."""
    if confidence not in Z:
        raise ValueError(f"confidence must be one of {sorted(Z)}")
    if not 0 < p < 1:
        raise ValueError("p must be between 0 and 1")
    if not 0 < margin_of_error < 1:
        raise ValueError("margin_of_error must be between 0 and 1")
    z = Z[confidence]
    return (z ** 2 * p * (1 - p)) / (margin_of_error ** 2)


def finite_population_correction(n0: float, population: int) -> float:
    """Adjust an infinite-population n down for a known finite population."""
    return n0 / (1 + (n0 - 1) / population)


def required_sample(p: float = 0.5, margin_of_error: float = 0.03,
                    confidence: float = 0.95, population: int | None = None,
                    design_effect: float = 1.0) -> SampleSizeResult:
    """Full pipeline: Cochran -> finite correction -> design effect -> ceil."""
    import math
    n0 = cochran_n(p, margin_of_error, confidence)
    n_corr = finite_population_correction(n0, population) if population else n0
    n_final = math.ceil(n_corr * design_effect)
    return SampleSizeResult(
        confidence=confidence,
        margin_of_error=margin_of_error,
        p=p,
        n_infinite=math.ceil(n0),
        n_corrected=math.ceil(n_corr),
        population=population,
        design_effect=design_effect,
        n_final=n_final,
    )


def subgroup_total(n_subgroups: int, per_cell_min: int = 100,
                   headline: int | None = None) -> int:
    """If results must be read within subgroups, each cell needs a floor."""
    needed = n_subgroups * per_cell_min
    return max(needed, headline or 0)


if __name__ == "__main__":
    print("=== Sample-size scenarios (US adult frame) ===\n")
    for moe in (0.05, 0.04, 0.03):
        print(required_sample(margin_of_error=moe).summary(), "\n")

    print("=== With cluster/weighting design effect 1.5 ===\n")
    print(required_sample(margin_of_error=0.03, design_effect=1.5).summary(), "\n")

    print("=== Subgroup-aware (4 age x 4 region = 16 cells) ===")
    print(f"  Minimum total for stable subgroups: "
          f"{subgroup_total(16, 100, headline=1068):,} completes")
