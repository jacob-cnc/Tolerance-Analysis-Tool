"""Tolerance type normalization.

Converts all tolerance types (bilateral, unilateral, limit) to a unified
bilateral form for uniform treatment by all analysis methods.
"""

from tolerance_analysis.engine.models import BilateralForm, Contributor, ToleranceType


def to_bilateral(contributor: Contributor) -> BilateralForm:
    """Convert any tolerance type to equivalent bilateral form.

    Bilateral (±T):
        bilateral_nominal = nominal
        bilateral_tolerance = upper_tolerance

    Unilateral (+U / -L):
        shift = (upper_tolerance + lower_tolerance) / 2
        bilateral_nominal = nominal + shift
        bilateral_tolerance = (upper_tolerance - lower_tolerance) / 2

    Limit (Upper_Limit / Lower_Limit):
        bilateral_nominal = (upper_tolerance + lower_tolerance) / 2
        bilateral_tolerance = (upper_tolerance - lower_tolerance) / 2

    Args:
        contributor: A Contributor with any tolerance_type.

    Returns:
        BilateralForm with shifted nominal and symmetric ± tolerance.
    """
    if contributor.tolerance_type == ToleranceType.BILATERAL:
        return BilateralForm(
            nominal=contributor.nominal,
            bilateral_tolerance=contributor.upper_tolerance,
            direction=contributor.direction,
        )

    elif contributor.tolerance_type == ToleranceType.UNILATERAL:
        shift = (contributor.upper_tolerance + contributor.lower_tolerance) / 2
        bilateral_nominal = contributor.nominal + shift
        bilateral_tolerance = (contributor.upper_tolerance - contributor.lower_tolerance) / 2
        return BilateralForm(
            nominal=bilateral_nominal,
            bilateral_tolerance=bilateral_tolerance,
            direction=contributor.direction,
        )

    elif contributor.tolerance_type == ToleranceType.LIMIT:
        bilateral_nominal = (contributor.upper_tolerance + contributor.lower_tolerance) / 2
        bilateral_tolerance = (contributor.upper_tolerance - contributor.lower_tolerance) / 2
        return BilateralForm(
            nominal=bilateral_nominal,
            bilateral_tolerance=bilateral_tolerance,
            direction=contributor.direction,
        )

    else:
        raise ValueError(f"Unknown tolerance type: {contributor.tolerance_type}")
