"""Stack-up warning engine for the Tolerance Analysis Tool.

Evaluates analysis results against common engineering failure modes and
generates actionable, plain-language warnings. This is pure logic with
no GUI dependencies.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional

from tolerance_analysis.engine.models import (
    AnalysisResults,
    MonteCarloResult,
    RSSResult,
    ToleranceChain,
    WorstCaseResult,
)


class WarningSeverity(Enum):
    """Severity levels for stack-up warnings."""
    INFO = "info"           # Informational, no action needed
    CAUTION = "caution"     # Potential issue, review recommended
    CRITICAL = "critical"   # Likely failure, action required


@dataclass
class StackUpWarning:
    """A single warning generated from analysis evaluation."""
    severity: WarningSeverity
    title: str
    message: str
    detail: str = ""


def evaluate_warnings(
    chain: ToleranceChain,
    results: Optional[AnalysisResults],
) -> list[StackUpWarning]:
    """Evaluate a tolerance chain and its results for engineering concerns.

    Args:
        chain: The tolerance chain being analyzed.
        results: Analysis results (worst-case, RSS, Monte Carlo). Can be None.

    Returns:
        List of StackUpWarning objects, sorted by severity (critical first).
    """
    warnings: list[StackUpWarning] = []

    if results is None:
        return warnings

    # --- Worst-Case Warnings ---
    if results.worst_case is not None:
        warnings.extend(_evaluate_worst_case(results.worst_case))

    # --- RSS Warnings ---
    if results.rss is not None:
        warnings.extend(_evaluate_rss(results.rss))

    # --- Monte Carlo Warnings ---
    if results.monte_carlo is not None:
        warnings.extend(_evaluate_monte_carlo(results.monte_carlo))

    # --- Chain structure warnings ---
    warnings.extend(_evaluate_chain_structure(chain))

    # Sort: critical first, then caution, then info
    severity_order = {WarningSeverity.CRITICAL: 0, WarningSeverity.CAUTION: 1, WarningSeverity.INFO: 2}
    warnings.sort(key=lambda w: severity_order[w.severity])

    return warnings


def _evaluate_worst_case(wc: WorstCaseResult) -> list[StackUpWarning]:
    """Evaluate worst-case results for failure conditions."""
    warnings = []

    # Nominal gap is negative — interference by design
    if wc.nominal < -1e-8:
        warnings.append(StackUpWarning(
            severity=WarningSeverity.CRITICAL,
            title="Interference by Design",
            message=(
                f"The nominal gap is {wc.nominal:.4f}\" — the assembly has built-in "
                f"interference before tolerances are even considered."
            ),
            detail="Check contributor directions. If this is intentional (press fit), this may be acceptable.",
        ))

    # Nominal gap is exactly zero
    elif abs(wc.nominal) < 1e-8:
        warnings.append(StackUpWarning(
            severity=WarningSeverity.CRITICAL,
            title="Zero Nominal Clearance",
            message=(
                "The nominal gap is 0.0000\" — any manufacturing variation in "
                "either direction will cause either interference or excessive clearance."
            ),
            detail=(
                "With bilateral tolerances, approximately 50% of assemblies will "
                "have interference. Consider adding designed-in clearance."
            ),
        ))

    # Worst-case minimum is negative (interference possible)
    if wc.minimum < -1e-8:
        warnings.append(StackUpWarning(
            severity=WarningSeverity.CRITICAL,
            title="Assembly Interference Possible",
            message=(
                f"Worst-case minimum is {wc.minimum:.4f}\" — if all contributors "
                f"hit their extreme limits simultaneously, the assembly WILL NOT FIT."
            ),
            detail=(
                f"The assembly gap ranges from {wc.minimum:.4f}\" to {wc.maximum:.4f}\". "
                f"Any combination producing a negative gap means physical interference. "
                f"Consider tightening tolerances or adding clearance."
            ),
        ))
    # Worst-case minimum is positive but very small relative to tolerance band
    elif wc.minimum > 0 and wc.tolerance_band > 0:
        clearance_ratio = wc.minimum / wc.tolerance_band
        if clearance_ratio < 0.1:
            warnings.append(StackUpWarning(
                severity=WarningSeverity.CAUTION,
                title="Near-Zero Worst-Case Clearance",
                message=(
                    f"Worst-case minimum clearance is only {wc.minimum:.4f}\" — "
                    f"this is less than 10% of the total tolerance band ({wc.tolerance_band:.4f}\")."
                ),
                detail=(
                    "While technically no interference occurs at worst-case, the margin "
                    "is extremely thin. Assembly difficulty, thermal expansion, or wear "
                    "could push this into interference."
                ),
            ))

    return warnings


def _evaluate_rss(rss: RSSResult) -> list[StackUpWarning]:
    """Evaluate RSS results for statistical failure risk."""
    warnings = []

    # Compute actual interference probability from RSS statistics.
    # RSS assumes a normal distribution centered on the nominal gap
    # with std_dev = rss_tolerance / 3 (since tolerance = 3σ coverage).
    # P(gap < 0) = Φ(-nominal / σ) where σ = rss_tolerance / 3
    if rss.statistical_tolerance > 1e-10:
        sigma = rss.statistical_tolerance / 3.0
        # z-score for gap = 0: z = (0 - nominal) / sigma = -nominal / sigma
        z_zero = -rss.nominal / sigma if sigma > 1e-10 else 0.0

        # Approximate Φ(z) using the standard normal CDF
        # Using a good rational approximation
        interference_pct = _normal_cdf(z_zero) * 100.0

        if interference_pct > 10.0:
            warnings.append(StackUpWarning(
                severity=WarningSeverity.CRITICAL,
                title=f"High Statistical Interference: ~{interference_pct:.0f}%",
                message=(
                    f"Based on the RSS analysis (normal distribution assumption), approximately "
                    f"{interference_pct:.1f}% of assemblies are expected to have interference (gap < 0)."
                ),
                detail=(
                    f"Nominal gap: {rss.nominal:.4f}\", RSS σ: {sigma:.4f}\". "
                    f"The process is not capable of producing this assembly reliably. "
                    f"Add clearance or tighten tolerances."
                ),
            ))
        elif interference_pct > 1.0:
            warnings.append(StackUpWarning(
                severity=WarningSeverity.CRITICAL,
                title=f"Significant Interference Risk: ~{interference_pct:.1f}%",
                message=(
                    f"Based on RSS analysis, approximately {interference_pct:.1f}% of assemblies "
                    f"({interference_pct * 10:.0f} per 1000) are expected to have interference."
                ),
                detail=(
                    f"Nominal gap: {rss.nominal:.4f}\", RSS σ: {sigma:.4f}\". "
                    f"Consider whether this reject rate is acceptable for your production volume."
                ),
            ))
        elif interference_pct > 0.1:
            warnings.append(StackUpWarning(
                severity=WarningSeverity.CAUTION,
                title=f"Statistical Interference Risk: ~{interference_pct:.2f}%",
                message=(
                    f"Based on RSS analysis, approximately {interference_pct:.2f}% of assemblies "
                    f"are expected to have interference (gap < 0)."
                ),
                detail=(
                    f"Nominal gap: {rss.nominal:.4f}\", RSS σ: {sigma:.4f}\". "
                    f"This is a low but non-zero reject rate."
                ),
            ))
        elif rss.statistical_minimum < -1e-8:
            warnings.append(StackUpWarning(
                severity=WarningSeverity.INFO,
                title="RSS Range Crosses Zero",
                message=(
                    f"The RSS ±3σ range [{rss.statistical_minimum:.4f}\", "
                    f"{rss.statistical_maximum:.4f}\"] extends below zero, "
                    f"but interference probability is very low (~{interference_pct:.3f}%)."
                ),
                detail="Likely acceptable for most applications.",
            ))

    return warnings


def _normal_cdf(z: float) -> float:
    """Approximate the standard normal CDF using Abramowitz & Stegun formula.

    Accurate to about 1e-5 for all z values.
    Returns P(Z <= z) where Z is standard normal.
    """
    import math

    if z > 8.0:
        return 1.0
    if z < -8.0:
        return 0.0

    # Use symmetry for negative values
    if z < 0:
        return 1.0 - _normal_cdf(-z)

    # Constants for the approximation (Abramowitz & Stegun 26.2.17)
    p = 0.2316419
    b1 = 0.319381530
    b2 = -0.356563782
    b3 = 1.781477937
    b4 = -1.821255978
    b5 = 1.330274429

    t = 1.0 / (1.0 + p * z)
    t2 = t * t
    t3 = t2 * t
    t4 = t3 * t
    t5 = t4 * t

    pdf = math.exp(-0.5 * z * z) / math.sqrt(2.0 * math.pi)
    cdf = 1.0 - pdf * (b1 * t + b2 * t2 + b3 * t3 + b4 * t4 + b5 * t5)

    return cdf


def _evaluate_monte_carlo(mc: MonteCarloResult) -> list[StackUpWarning]:
    """Evaluate Monte Carlo results for simulated failure rate."""
    warnings = []

    # Count samples below zero (interference)
    if mc.histogram_data:
        interference_count = sum(1 for x in mc.histogram_data if x < 0)
        interference_pct = (interference_count / mc.num_iterations) * 100

        if interference_pct > 5.0:
            warnings.append(StackUpWarning(
                severity=WarningSeverity.CRITICAL,
                title=f"High Interference Rate: {interference_pct:.1f}%",
                message=(
                    f"{interference_count:,} of {mc.num_iterations:,} simulated assemblies "
                    f"({interference_pct:.1f}%) had interference (gap < 0)."
                ),
                detail=(
                    "More than 5% of assemblies will not fit. This is a serious "
                    "manufacturing problem. Increase clearance or tighten tolerances."
                ),
            ))
        elif interference_pct > 0.1:
            warnings.append(StackUpWarning(
                severity=WarningSeverity.CAUTION,
                title=f"Moderate Interference Rate: {interference_pct:.2f}%",
                message=(
                    f"{interference_count:,} of {mc.num_iterations:,} simulated assemblies "
                    f"({interference_pct:.2f}%) had interference (gap < 0)."
                ),
                detail=(
                    "Some assemblies will not fit. Depending on production volume and "
                    "reject cost, this may or may not be acceptable."
                ),
            ))
        elif interference_pct > 0:
            warnings.append(StackUpWarning(
                severity=WarningSeverity.INFO,
                title=f"Rare Interference: {interference_pct:.3f}%",
                message=(
                    f"{interference_count:,} of {mc.num_iterations:,} simulated assemblies "
                    f"({interference_pct:.3f}%) had interference."
                ),
                detail="Very low rate — likely acceptable for most applications.",
            ))

    # Check if distribution is heavily skewed toward zero
    if mc.minimum < 0 and mc.mean > 0:
        margin_ratio = mc.mean / mc.std_dev if mc.std_dev > 1e-10 else float('inf')
        if margin_ratio < 2.0:
            warnings.append(StackUpWarning(
                severity=WarningSeverity.CAUTION,
                title="Low Statistical Margin",
                message=(
                    f"The mean gap ({mc.mean:.4f}\") is less than 2× the standard "
                    f"deviation ({mc.std_dev:.4f}\")."
                ),
                detail=(
                    "The process capability (Cpk) is below 0.67. Most quality standards "
                    "require Cpk ≥ 1.33. Consider tightening tolerances or increasing clearance."
                ),
            ))

    return warnings


def _evaluate_chain_structure(chain: ToleranceChain) -> list[StackUpWarning]:
    """Evaluate the chain structure for potential setup issues."""
    warnings = []
    from tolerance_analysis.engine.models import Direction

    directions = [c.direction for c in chain.contributors]
    has_positive = Direction.POSITIVE in directions
    has_negative = Direction.NEGATIVE in directions

    if chain.contributors and not has_negative:
        warnings.append(StackUpWarning(
            severity=WarningSeverity.INFO,
            title="No Negative Contributors",
            message=(
                "All contributors are positive (same direction). There is nothing "
                "opposing the stack — the result is just a sum, not a gap analysis."
            ),
            detail=(
                "Typically a stack-up has dimensions going in both directions to "
                "find a gap or closure. Verify contributor directions are correct."
            ),
        ))
    elif chain.contributors and not has_positive:
        warnings.append(StackUpWarning(
            severity=WarningSeverity.INFO,
            title="No Positive Contributors",
            message=(
                "All contributors are negative. There is nothing opposing the "
                "stack — verify contributor directions are correct."
            ),
            detail="A meaningful stack-up usually has both positive and negative contributors.",
        ))

    return warnings
