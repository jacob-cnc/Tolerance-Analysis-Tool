"""RSS (Root Sum of Squares) statistical tolerance stack-up analyzer.

Computes the statistical assembly dimensions by taking the square root
of the sum of squared tolerance contributions. This represents a more
realistic estimate than worst-case, assuming tolerances follow
independent statistical distributions.
"""

import math

from tolerance_analysis.engine.converter import to_bilateral
from tolerance_analysis.engine.models import RSSResult, ToleranceChain
from tolerance_analysis.engine.worst_case import WorstCaseAnalyzer


class RSSAnalyzer:
    """Performs RSS statistical tolerance stack-up analysis.

    The RSS method assumes tolerance contributions are statistically
    independent and combines them as root-sum-of-squares. This produces
    a tighter range than worst-case, representing approximately 99.73%
    (3-sigma) coverage for normally distributed processes.
    """

    def analyze(self, chain: ToleranceChain) -> RSSResult:
        """Compute RSS statistical stack-up for a tolerance chain.

        Algorithm:
            1. Convert each contributor to bilateral form.
            2. total_nominal = sum(bilateral.nominal * direction.value)
            3. rss_tolerance = sqrt(sum(bilateral.bilateral_tolerance^2))
            4. statistical_maximum = total_nominal + rss_tolerance
            5. statistical_minimum = total_nominal - rss_tolerance
            6. statistical_band = 2 * rss_tolerance
            7. Compute worst-case result for comparative display.

        Args:
            chain: A ToleranceChain with at least 2 contributors.

        Returns:
            RSSResult with computed nominal, statistical tolerance,
            max, min, band, and worst-case comparison.

        Raises:
            ValueError: If the chain has fewer than 2 contributors.
        """
        if len(chain.contributors) < 2:
            raise ValueError(
                f"RSS analysis requires at least 2 contributors, "
                f"got {len(chain.contributors)}."
            )

        total_nominal = 0.0
        sum_of_squares = 0.0

        for contributor in chain.contributors:
            bilateral = to_bilateral(contributor)
            total_nominal += bilateral.nominal * bilateral.direction.value
            sum_of_squares += bilateral.bilateral_tolerance ** 2

        rss_tolerance = math.sqrt(sum_of_squares)

        statistical_maximum = total_nominal + rss_tolerance
        statistical_minimum = total_nominal - rss_tolerance
        statistical_band = 2.0 * rss_tolerance

        # Compute worst-case for comparative display
        worst_case_analyzer = WorstCaseAnalyzer()
        worst_case = worst_case_analyzer.analyze(chain)

        return RSSResult(
            nominal=total_nominal,
            statistical_tolerance=rss_tolerance,
            statistical_maximum=statistical_maximum,
            statistical_minimum=statistical_minimum,
            statistical_band=statistical_band,
            worst_case=worst_case,
        )
