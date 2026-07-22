"""Monte Carlo simulation for tolerance analysis.

Uses numpy for vectorized sampling across normal, uniform, and triangular
distributions. Produces statistical results including percentiles and
histogram data for visualization.
"""

import math
from typing import Optional

import numpy as np

from tolerance_analysis.engine.converter import to_bilateral
from tolerance_analysis.engine.models import (
    DistributionType,
    MonteCarloResult,
    ToleranceChain,
)


class MonteCarloSimulator:
    """Monte Carlo tolerance stack-up simulator.

    Generates random samples for each contributor based on its distribution
    type, sums them respecting direction signs, and computes assembly-level
    statistics from the resulting distribution.
    """

    def simulate(
        self,
        chain: ToleranceChain,
        iterations: int = 10_000,
        seed: Optional[int] = None,
    ) -> MonteCarloResult:
        """Run Monte Carlo simulation on a tolerance chain.

        Args:
            chain: Tolerance chain with at least 1 contributor.
            iterations: Number of simulation iterations (1,000 to 1,000,000).
            seed: Optional RNG seed for reproducibility.

        Returns:
            MonteCarloResult with statistics, percentiles, and histogram data.

        Raises:
            ValueError: If chain has 0 contributors or iterations is out of range.
        """
        if not chain.contributors:
            raise ValueError("Chain must have at least 1 contributor.")

        if iterations < 1_000 or iterations > 1_000_000:
            raise ValueError(
                "Iterations must be between 1,000 and 1,000,000."
            )

        rng = np.random.default_rng(seed)

        results = np.zeros(iterations)

        for contributor in chain.contributors:
            bilateral = to_bilateral(contributor)
            nominal = bilateral.nominal
            tol = bilateral.bilateral_tolerance
            direction = bilateral.direction.value

            if contributor.distribution == DistributionType.NORMAL:
                samples = rng.normal(
                    loc=nominal,
                    scale=tol / 3,
                    size=iterations,
                )
            elif contributor.distribution == DistributionType.UNIFORM:
                samples = rng.uniform(
                    low=nominal - tol,
                    high=nominal + tol,
                    size=iterations,
                )
            elif contributor.distribution == DistributionType.TRIANGULAR:
                samples = rng.triangular(
                    left=nominal - tol,
                    mode=nominal,
                    right=nominal + tol,
                    size=iterations,
                )
            else:
                raise ValueError(
                    f"Unknown distribution type: {contributor.distribution}"
                )

            results += samples * direction

        # Compute statistics
        mean = float(np.mean(results))
        std_dev = float(np.std(results))
        minimum = float(np.min(results))
        maximum = float(np.max(results))

        percentile_values = np.percentile(
            results, [0.135, 2.275, 50, 97.725, 99.865]
        )
        percentiles = {
            "0.135": float(percentile_values[0]),
            "2.275": float(percentile_values[1]),
            "50": float(percentile_values[2]),
            "97.725": float(percentile_values[3]),
            "99.865": float(percentile_values[4]),
        }

        # Build histogram
        num_bins = max(20, int(math.sqrt(iterations)))
        bin_counts_arr, bin_edges_arr = np.histogram(results, bins=num_bins)

        return MonteCarloResult(
            mean=mean,
            std_dev=std_dev,
            minimum=minimum,
            maximum=maximum,
            percentiles=percentiles,
            histogram_data=results.tolist(),
            num_iterations=iterations,
            bin_edges=bin_edges_arr.tolist(),
            bin_counts=bin_counts_arr.tolist(),
        )
