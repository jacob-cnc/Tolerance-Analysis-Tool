"""Core data models for the tolerance analysis engine.

All models are plain Python dataclasses with no framework dependencies.
These are the shared data structures used across all layers of the application.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional
from uuid import uuid4


# --- Enums ---


class ToleranceType(Enum):
    """Classification of how a tolerance is specified."""

    BILATERAL = "bilateral"
    UNILATERAL = "unilateral"
    LIMIT = "limit"


class Direction(Enum):
    """Direction of a contributor in the tolerance chain."""

    POSITIVE = 1
    NEGATIVE = -1


class DistributionType(Enum):
    """Statistical distribution type for Monte Carlo sampling."""

    NORMAL = "normal"
    UNIFORM = "uniform"
    TRIANGULAR = "triangular"


# --- Core Dataclasses ---


@dataclass
class Contributor:
    """A single dimensional element in a tolerance chain.

    Attributes:
        name: Human-readable identifier for the contributor.
        nominal: The nominal dimension value.
        direction: Whether this contributor adds (+1) or subtracts (-1) from the stack.
        tolerance_type: How the tolerance is specified (bilateral, unilateral, limit).
        upper_tolerance: Upper tolerance value.
            - Bilateral: symmetric ± value (upper == lower)
            - Unilateral: upper deviation (e.g., +0.002)
            - Limit: upper limit value
        lower_tolerance: Lower tolerance value.
            - Bilateral: symmetric ± value (upper == lower)
            - Unilateral: lower deviation (e.g., -0.005, stored as negative)
            - Limit: lower limit value
        distribution: Statistical distribution for Monte Carlo sampling.
        description: Optional description of the contributor.
        notes: Optional notes (e.g., process capability info).
        material: Optional material specification.
        id: Unique identifier (auto-generated UUID).
    """

    name: str
    nominal: float
    direction: Direction
    tolerance_type: ToleranceType
    upper_tolerance: float
    lower_tolerance: float
    distribution: DistributionType = DistributionType.NORMAL
    description: str = ""
    notes: str = ""
    material: str = ""
    id: str = field(default_factory=lambda: str(uuid4()))


@dataclass
class BilateralForm:
    """Normalized bilateral form used internally by all analyzers.

    All tolerance types are converted to this form before analysis.
    The effective range is [nominal - bilateral_tolerance, nominal + bilateral_tolerance].
    """

    nominal: float
    bilateral_tolerance: float  # Always positive, symmetric ±
    direction: Direction


@dataclass
class ToleranceChain:
    """An ordered list of dimension contributors defining a stack-up path.

    Attributes:
        name: User-specified name for the chain (1-100 characters).
        description: Optional description (0-500 characters).
        contributors: Ordered list of dimensional contributors.
        id: Unique identifier (auto-generated UUID).
    """

    name: str
    description: str = ""
    contributors: list[Contributor] = field(default_factory=list)
    id: str = field(default_factory=lambda: str(uuid4()))


# --- Result Dataclasses ---


@dataclass
class WorstCaseResult:
    """Results from worst-case (arithmetic) tolerance analysis.

    Attributes:
        nominal: Total nominal dimension (algebraic sum with directions).
        total_tolerance: Sum of all absolute tolerance magnitudes.
        maximum: nominal + total_tolerance.
        minimum: nominal - total_tolerance.
        tolerance_band: 2 × total_tolerance.
    """

    nominal: float
    total_tolerance: float
    maximum: float
    minimum: float
    tolerance_band: float


@dataclass
class RSSResult:
    """Results from RSS (Root Sum of Squares) statistical analysis.

    Attributes:
        nominal: Total nominal dimension (algebraic sum with directions).
        statistical_tolerance: sqrt(sum of squared tolerances).
        statistical_maximum: nominal + statistical_tolerance.
        statistical_minimum: nominal - statistical_tolerance.
        statistical_band: 2 × statistical_tolerance.
        worst_case: Worst-case result computed alongside for comparison.
    """

    nominal: float
    statistical_tolerance: float
    statistical_maximum: float
    statistical_minimum: float
    statistical_band: float
    worst_case: WorstCaseResult


@dataclass
class MonteCarloResult:
    """Results from Monte Carlo simulation.

    Attributes:
        mean: Mean of all assembly dimension samples.
        std_dev: Standard deviation of samples.
        minimum: Minimum sample value.
        maximum: Maximum sample value.
        percentiles: Dict with keys "0.135", "2.275", "50", "97.725", "99.865".
        histogram_data: Raw sample results for histogram rendering.
        num_iterations: Number of simulation iterations performed.
        bin_edges: Histogram bin edge values.
        bin_counts: Count of samples in each histogram bin.
    """

    mean: float
    std_dev: float
    minimum: float
    maximum: float
    percentiles: dict[str, float]
    histogram_data: list[float]
    num_iterations: int
    bin_edges: list[float]
    bin_counts: list[int]


# --- Project-Level Dataclasses ---


@dataclass
class AnalysisResults:
    """Container for all analysis results computed for a tolerance chain."""

    worst_case: Optional[WorstCaseResult] = None
    rss: Optional[RSSResult] = None
    monte_carlo: Optional[MonteCarloResult] = None


@dataclass
class Project:
    """Top-level project state containing all tolerance chains and settings.

    Attributes:
        name: Project name.
        filepath: Path to the saved project file (None if unsaved).
        unit_system: Active unit system as string ("inch" or "mm").
            The boundary layer handles enum mapping.
        standard_mode: Active GD&T standard mode as string
            ("generic", "asme_y14_5", or "iso_gps").
            The boundary layer handles enum mapping.
        tolerance_chains: All tolerance chains in this project.
        created: Timestamp when the project was created.
        modified: Timestamp when the project was last modified.
    """

    name: str
    filepath: Optional[str] = None
    unit_system: str = "inch"
    standard_mode: str = "generic"
    tolerance_chains: list[ToleranceChain] = field(default_factory=list)
    created: datetime = field(default_factory=datetime.now)
    modified: datetime = field(default_factory=datetime.now)
