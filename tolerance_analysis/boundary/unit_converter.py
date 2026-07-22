"""Unit system conversion for the tolerance analysis boundary layer.

Handles conversion between inch and millimeter unit systems.
All conversions are stateless — the caller provides from_unit and to_unit.

Validates: Requirements 8.1, 8.2, 8.3, 8.4
"""

from dataclasses import replace
from enum import Enum

from tolerance_analysis.engine.models import Contributor, ToleranceChain


class UnitSystem(Enum):
    """Supported unit systems for dimensional values."""

    INCH = "inch"
    MILLIMETER = "mm"


class UnitConverter:
    """Stateless converter between inch and millimeter unit systems.

    Uses the exact conversion factor: 1 inch = 25.4 mm.
    Display precision: 4 decimal places for inch, 3 for millimeter.
    """

    INCH_TO_MM: float = 25.4

    def convert(self, value: float, from_unit: UnitSystem, to_unit: UnitSystem) -> float:
        """Convert a single dimensional value between unit systems.

        Args:
            value: The numeric value to convert.
            from_unit: The current unit system of the value.
            to_unit: The target unit system.

        Returns:
            The converted value. If from_unit == to_unit, returns the value unchanged.
        """
        if from_unit == to_unit:
            return value

        if from_unit == UnitSystem.INCH and to_unit == UnitSystem.MILLIMETER:
            return value * self.INCH_TO_MM
        else:
            # MILLIMETER -> INCH
            return value / self.INCH_TO_MM

    def convert_contributor(
        self, contributor: Contributor, from_unit: UnitSystem, to_unit: UnitSystem
    ) -> Contributor:
        """Convert all dimensional values in a contributor to a new unit system.

        Creates and returns a NEW Contributor instance — the original is not mutated.
        Converts nominal, upper_tolerance, and lower_tolerance values.
        For LIMIT type, upper/lower tolerances are the limits themselves, so they
        are also converted.

        Args:
            contributor: The contributor to convert.
            from_unit: The current unit system of the contributor's values.
            to_unit: The target unit system.

        Returns:
            A new Contributor with converted dimensional values.
        """
        if from_unit == to_unit:
            return replace(contributor)

        return replace(
            contributor,
            nominal=self.convert(contributor.nominal, from_unit, to_unit),
            upper_tolerance=self.convert(contributor.upper_tolerance, from_unit, to_unit),
            lower_tolerance=self.convert(contributor.lower_tolerance, from_unit, to_unit),
        )

    def convert_chain(
        self, chain: ToleranceChain, from_unit: UnitSystem, to_unit: UnitSystem
    ) -> ToleranceChain:
        """Convert all contributors in a tolerance chain to a new unit system.

        Creates and returns a NEW ToleranceChain — the original is not mutated.

        Args:
            chain: The tolerance chain to convert.
            from_unit: The current unit system of the chain's values.
            to_unit: The target unit system.

        Returns:
            A new ToleranceChain with all contributors converted.
        """
        if from_unit == to_unit:
            return replace(chain, contributors=list(chain.contributors))

        converted_contributors = [
            self.convert_contributor(c, from_unit, to_unit)
            for c in chain.contributors
        ]
        return replace(chain, contributors=converted_contributors)

    def display_precision(self, unit: UnitSystem) -> int:
        """Return the number of decimal places for display in the given unit system.

        Args:
            unit: The unit system.

        Returns:
            4 for inch, 3 for millimeter.
        """
        if unit == UnitSystem.INCH:
            return 4
        return 3

    def format_value(self, value: float, unit: UnitSystem) -> str:
        """Format a dimensional value with the correct decimal places for display.

        Args:
            value: The numeric value to format.
            unit: The unit system determining precision.

        Returns:
            A string representation with exactly 4 decimal places (inch)
            or 3 decimal places (millimeter).
        """
        precision = self.display_precision(unit)
        return f"{value:.{precision}f}"
