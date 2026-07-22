"""Worst-case (arithmetic) tolerance stack-up analyzer.

Computes the absolute worst-case assembly dimensions by summing all
tolerance contributions arithmetically. This represents the most
conservative analysis method — guaranteeing 100% of assemblies will
fall within the computed range.
"""

from tolerance_analysis.engine.converter import to_bilateral
from tolerance_analysis.engine.models import ToleranceChain, WorstCaseResult


class WorstCaseAnalyzer:
    """Performs worst-case tolerance stack-up analysis.

    The worst-case method sums all tolerances arithmetically, producing
    the widest possible range. Every contributor's full tolerance is
    assumed to occur simultaneously at its worst extreme.
    """

    def analyze(self, chain: ToleranceChain) -> WorstCaseResult:
        """Compute worst-case stack-up for a tolerance chain.

        Algorithm:
            1. Convert each contributor to bilateral form.
            2. total_nominal = sum(bilateral.nominal * direction.value)
            3. total_tolerance = sum(|bilateral.bilateral_tolerance|)
            4. maximum = total_nominal + total_tolerance
            5. minimum = total_nominal - total_tolerance
            6. tolerance_band = 2 * total_tolerance

        Args:
            chain: A ToleranceChain with at least 2 contributors.

        Returns:
            WorstCaseResult with computed nominal, tolerance, max, min, band.

        Raises:
            ValueError: If the chain has fewer than 2 contributors.
        """
        if len(chain.contributors) < 2:
            raise ValueError(
                f"Worst-case analysis requires at least 2 contributors, "
                f"got {len(chain.contributors)}."
            )

        total_nominal = 0.0
        total_tolerance = 0.0

        for contributor in chain.contributors:
            bilateral = to_bilateral(contributor)
            total_nominal += bilateral.nominal * bilateral.direction.value
            total_tolerance += abs(bilateral.bilateral_tolerance)

        maximum = total_nominal + total_tolerance
        minimum = total_nominal - total_tolerance
        tolerance_band = 2.0 * total_tolerance

        return WorstCaseResult(
            nominal=total_nominal,
            total_tolerance=total_tolerance,
            maximum=maximum,
            minimum=minimum,
            tolerance_band=tolerance_band,
        )
