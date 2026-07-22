"""Shared Hypothesis strategies for property-based testing.

Provides reusable strategies for generating valid Contributor and ToleranceChain
instances based on the data models defined in tolerance_analysis.engine.models.
"""

import hypothesis.strategies as st
from hypothesis import settings

from tolerance_analysis.engine.models import (
    Contributor,
    Direction,
    DistributionType,
    ToleranceChain,
    ToleranceType,
)

# Configure Hypothesis defaults for the project
settings.register_profile("default", max_examples=100, deadline=None)
settings.register_profile("ci", max_examples=500, deadline=None)
settings.load_profile("default")


# --- Enum strategies ---

tolerance_types = st.sampled_from(ToleranceType)
directions = st.sampled_from(Direction)
distribution_types = st.sampled_from(DistributionType)


# --- Numeric strategies ---

# Reasonable nominal values for mechanical dimensions (avoid extremes that cause overflow)
nominals = st.floats(
    min_value=-9999.0,
    max_value=9999.0,
    allow_nan=False,
    allow_infinity=False,
)

# Non-negative tolerance values (tolerances represent dimensional ranges)
tolerances = st.floats(
    min_value=0.0,
    max_value=999.0,
    allow_nan=False,
    allow_infinity=False,
)

# Positive tolerance values (for cases where zero tolerance is invalid)
positive_tolerances = st.floats(
    min_value=0.0001,
    max_value=999.0,
    allow_nan=False,
    allow_infinity=False,
)


# --- Contributor strategy ---


@st.composite
def contributors(draw, tolerance_type=None, direction=None, distribution=None):
    """Generate a valid Contributor instance.

    Parameters:
        tolerance_type: Fix the tolerance type (or draw randomly if None)
        direction: Fix the direction (or draw randomly if None)
        distribution: Fix the distribution type (or draw randomly if None)
    """
    tt = draw(tolerance_types) if tolerance_type is None else tolerance_type
    d = draw(directions) if direction is None else direction
    dist = draw(distribution_types) if distribution is None else distribution

    nominal = draw(nominals)
    upper_tol = draw(tolerances)

    # Generate lower_tolerance based on tolerance type
    if tt == ToleranceType.BILATERAL:
        # Bilateral: upper == lower (symmetric)
        lower_tol = upper_tol
    elif tt == ToleranceType.UNILATERAL:
        # Unilateral: lower_tolerance may be negative (e.g., +0.000/-0.005)
        # upper >= lower, stored as upper=positive, lower=negative or zero
        lower_tol = draw(
            st.floats(
                min_value=-999.0,
                max_value=upper_tol,
                allow_nan=False,
                allow_infinity=False,
            )
        )
    else:
        # Limit dimensions: upper_tol = upper limit, lower_tol = lower limit
        # Upper limit must be >= lower limit
        lower_tol = draw(
            st.floats(
                min_value=nominal - 999.0,
                max_value=nominal + upper_tol,
                allow_nan=False,
                allow_infinity=False,
            )
        )
        # For limit type, upper_tolerance is the upper limit
        upper_tol = draw(
            st.floats(
                min_value=lower_tol,
                max_value=lower_tol + 999.0,
                allow_nan=False,
                allow_infinity=False,
            )
        )

    name = draw(st.text(min_size=1, max_size=50, alphabet=st.characters(
        whitelist_categories=("L", "N", "Z"),
        whitelist_characters=" -_"
    )))

    return Contributor(
        name=name,
        nominal=nominal,
        direction=d,
        tolerance_type=tt,
        upper_tolerance=upper_tol,
        lower_tolerance=lower_tol,
        distribution=dist,
    )


@st.composite
def bilateral_contributors(draw, direction=None, distribution=None):
    """Generate a Contributor with bilateral tolerance type."""
    return draw(contributors(
        tolerance_type=ToleranceType.BILATERAL,
        direction=direction,
        distribution=distribution,
    ))


@st.composite
def unilateral_contributors(draw, direction=None, distribution=None):
    """Generate a Contributor with unilateral tolerance type."""
    return draw(contributors(
        tolerance_type=ToleranceType.UNILATERAL,
        direction=direction,
        distribution=distribution,
    ))


@st.composite
def limit_contributors(draw, direction=None, distribution=None):
    """Generate a Contributor with limit tolerance type."""
    return draw(contributors(
        tolerance_type=ToleranceType.LIMIT,
        direction=direction,
        distribution=distribution,
    ))


# --- ToleranceChain strategy ---


@st.composite
def tolerance_chains(draw, min_contributors=2, max_contributors=10):
    """Generate a valid ToleranceChain with the specified number of contributors.

    Parameters:
        min_contributors: Minimum number of contributors (default 2 for analysis)
        max_contributors: Maximum number of contributors (default 10)
    """
    name = draw(st.text(min_size=1, max_size=100, alphabet=st.characters(
        whitelist_categories=("L", "N", "Z"),
        whitelist_characters=" -_"
    )))
    description = draw(st.text(min_size=0, max_size=200, alphabet=st.characters(
        whitelist_categories=("L", "N", "Z"),
        whitelist_characters=" -_.,;:!?"
    )))

    num_contributors = draw(st.integers(
        min_value=min_contributors,
        max_value=max_contributors,
    ))

    chain_contributors = draw(
        st.lists(contributors(), min_size=num_contributors, max_size=num_contributors)
    )

    return ToleranceChain(
        name=name,
        description=description,
        contributors=chain_contributors,
    )


@st.composite
def small_tolerance_chains(draw):
    """Generate a ToleranceChain with 2-4 contributors (fast for property tests)."""
    return draw(tolerance_chains(min_contributors=2, max_contributors=4))


@st.composite
def analysis_ready_chains(draw):
    """Generate a ToleranceChain that meets minimum requirements for analysis (>=2 contributors)."""
    return draw(tolerance_chains(min_contributors=2, max_contributors=8))
