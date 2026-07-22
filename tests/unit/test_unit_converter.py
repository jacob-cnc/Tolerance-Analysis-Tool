"""Unit tests for boundary.unit_converter module.

Validates: Requirements 8.1, 8.2, 8.3, 8.4
"""

import pytest

from tolerance_analysis.boundary.unit_converter import UnitConverter, UnitSystem
from tolerance_analysis.engine.models import (
    Contributor,
    Direction,
    DistributionType,
    ToleranceChain,
    ToleranceType,
)


@pytest.fixture
def uc():
    """Provide a UnitConverter instance."""
    return UnitConverter()


class TestConvertSingleValue:
    """Tests for UnitConverter.convert()."""

    def test_inch_to_mm(self, uc):
        assert abs(uc.convert(1.0, UnitSystem.INCH, UnitSystem.MILLIMETER) - 25.4) < 1e-10

    def test_mm_to_inch(self, uc):
        assert abs(uc.convert(25.4, UnitSystem.MILLIMETER, UnitSystem.INCH) - 1.0) < 1e-10

    def test_same_unit_noop_inch(self, uc):
        assert uc.convert(3.1415, UnitSystem.INCH, UnitSystem.INCH) == 3.1415

    def test_same_unit_noop_mm(self, uc):
        assert uc.convert(80.0, UnitSystem.MILLIMETER, UnitSystem.MILLIMETER) == 80.0

    def test_zero_value(self, uc):
        assert uc.convert(0.0, UnitSystem.INCH, UnitSystem.MILLIMETER) == 0.0

    def test_negative_value(self, uc):
        result = uc.convert(-2.0, UnitSystem.INCH, UnitSystem.MILLIMETER)
        assert abs(result - (-50.8)) < 1e-10

    def test_round_trip_precision(self, uc):
        """Converting inch->mm->inch should return within floating point tolerance."""
        original = 1.2345
        mm = uc.convert(original, UnitSystem.INCH, UnitSystem.MILLIMETER)
        back = uc.convert(mm, UnitSystem.MILLIMETER, UnitSystem.INCH)
        assert abs(back - original) < 1e-10


class TestDisplayPrecision:
    """Tests for UnitConverter.display_precision()."""

    def test_inch_precision(self, uc):
        assert uc.display_precision(UnitSystem.INCH) == 4

    def test_mm_precision(self, uc):
        assert uc.display_precision(UnitSystem.MILLIMETER) == 3


class TestFormatValue:
    """Tests for UnitConverter.format_value()."""

    def test_inch_format_4_decimals(self, uc):
        assert uc.format_value(1.5, UnitSystem.INCH) == "1.5000"

    def test_mm_format_3_decimals(self, uc):
        assert uc.format_value(38.1, UnitSystem.MILLIMETER) == "38.100"

    def test_inch_format_rounding(self, uc):
        # 1.00005 should round to 1.0001
        assert uc.format_value(1.00005, UnitSystem.INCH) == "1.0001"

    def test_mm_format_rounding(self, uc):
        # 25.4005 should round to 25.401
        assert uc.format_value(25.4005, UnitSystem.MILLIMETER) == "25.401"

    def test_zero_formatting_inch(self, uc):
        assert uc.format_value(0.0, UnitSystem.INCH) == "0.0000"

    def test_zero_formatting_mm(self, uc):
        assert uc.format_value(0.0, UnitSystem.MILLIMETER) == "0.000"

    def test_large_value_inch(self, uc):
        assert uc.format_value(999.9999, UnitSystem.INCH) == "999.9999"

    def test_negative_value_formatting(self, uc):
        assert uc.format_value(-0.005, UnitSystem.INCH) == "-0.0050"


class TestConvertContributor:
    """Tests for UnitConverter.convert_contributor()."""

    def test_bilateral_conversion(self, uc):
        c = Contributor(
            name="Housing Bore",
            nominal=1.5,
            direction=Direction.POSITIVE,
            tolerance_type=ToleranceType.BILATERAL,
            upper_tolerance=0.002,
            lower_tolerance=0.002,
        )
        c_mm = uc.convert_contributor(c, UnitSystem.INCH, UnitSystem.MILLIMETER)
        assert abs(c_mm.nominal - 38.1) < 1e-10
        assert abs(c_mm.upper_tolerance - 0.0508) < 1e-10
        assert abs(c_mm.lower_tolerance - 0.0508) < 1e-10

    def test_limit_type_conversion(self, uc):
        """LIMIT type: upper/lower are the limits themselves, must be converted."""
        c = Contributor(
            name="Shaft",
            nominal=1.0,
            direction=Direction.POSITIVE,
            tolerance_type=ToleranceType.LIMIT,
            upper_tolerance=1.005,
            lower_tolerance=0.995,
        )
        c_mm = uc.convert_contributor(c, UnitSystem.INCH, UnitSystem.MILLIMETER)
        assert abs(c_mm.nominal - 25.4) < 1e-10
        assert abs(c_mm.upper_tolerance - 1.005 * 25.4) < 1e-10
        assert abs(c_mm.lower_tolerance - 0.995 * 25.4) < 1e-10

    def test_unilateral_conversion(self, uc):
        c = Contributor(
            name="Spacer",
            nominal=0.5,
            direction=Direction.NEGATIVE,
            tolerance_type=ToleranceType.UNILATERAL,
            upper_tolerance=0.0,
            lower_tolerance=-0.005,
        )
        c_mm = uc.convert_contributor(c, UnitSystem.INCH, UnitSystem.MILLIMETER)
        assert abs(c_mm.nominal - 12.7) < 1e-10
        assert abs(c_mm.upper_tolerance - 0.0) < 1e-10
        assert abs(c_mm.lower_tolerance - (-0.127)) < 1e-10

    def test_immutability(self, uc):
        """Original contributor must not be mutated."""
        c = Contributor(
            name="Original",
            nominal=2.0,
            direction=Direction.POSITIVE,
            tolerance_type=ToleranceType.BILATERAL,
            upper_tolerance=0.01,
            lower_tolerance=0.01,
        )
        uc.convert_contributor(c, UnitSystem.INCH, UnitSystem.MILLIMETER)
        assert c.nominal == 2.0
        assert c.upper_tolerance == 0.01

    def test_non_dimensional_fields_preserved(self, uc):
        c = Contributor(
            name="Bearing",
            nominal=1.0,
            direction=Direction.NEGATIVE,
            tolerance_type=ToleranceType.BILATERAL,
            upper_tolerance=0.001,
            lower_tolerance=0.001,
            distribution=DistributionType.UNIFORM,
            description="Main bearing",
            notes="CNC turned",
            material="Steel",
        )
        c_mm = uc.convert_contributor(c, UnitSystem.INCH, UnitSystem.MILLIMETER)
        assert c_mm.name == "Bearing"
        assert c_mm.direction == Direction.NEGATIVE
        assert c_mm.tolerance_type == ToleranceType.BILATERAL
        assert c_mm.distribution == DistributionType.UNIFORM
        assert c_mm.description == "Main bearing"
        assert c_mm.notes == "CNC turned"
        assert c_mm.material == "Steel"
        assert c_mm.id == c.id

    def test_same_unit_returns_new_instance(self, uc):
        c = Contributor(
            name="Part",
            nominal=1.0,
            direction=Direction.POSITIVE,
            tolerance_type=ToleranceType.BILATERAL,
            upper_tolerance=0.001,
            lower_tolerance=0.001,
        )
        c_same = uc.convert_contributor(c, UnitSystem.INCH, UnitSystem.INCH)
        assert c_same is not c
        assert c_same.nominal == c.nominal


class TestConvertChain:
    """Tests for UnitConverter.convert_chain()."""

    def test_chain_conversion(self, uc):
        chain = ToleranceChain(
            name="Stack-Up",
            description="Test chain",
            contributors=[
                Contributor(
                    name="Part A",
                    nominal=2.0,
                    direction=Direction.POSITIVE,
                    tolerance_type=ToleranceType.BILATERAL,
                    upper_tolerance=0.003,
                    lower_tolerance=0.003,
                ),
                Contributor(
                    name="Part B",
                    nominal=1.0,
                    direction=Direction.NEGATIVE,
                    tolerance_type=ToleranceType.BILATERAL,
                    upper_tolerance=0.005,
                    lower_tolerance=0.005,
                ),
            ],
        )
        chain_mm = uc.convert_chain(chain, UnitSystem.INCH, UnitSystem.MILLIMETER)
        assert abs(chain_mm.contributors[0].nominal - 50.8) < 1e-10
        assert abs(chain_mm.contributors[1].nominal - 25.4) < 1e-10

    def test_chain_immutability(self, uc):
        chain = ToleranceChain(
            name="Original Chain",
            contributors=[
                Contributor(
                    name="Part",
                    nominal=3.0,
                    direction=Direction.POSITIVE,
                    tolerance_type=ToleranceType.BILATERAL,
                    upper_tolerance=0.01,
                    lower_tolerance=0.01,
                ),
            ],
        )
        uc.convert_chain(chain, UnitSystem.INCH, UnitSystem.MILLIMETER)
        assert chain.contributors[0].nominal == 3.0

    def test_chain_metadata_preserved(self, uc):
        chain = ToleranceChain(
            name="My Chain",
            description="Important stack-up",
            contributors=[],
        )
        chain_mm = uc.convert_chain(chain, UnitSystem.INCH, UnitSystem.MILLIMETER)
        assert chain_mm.name == "My Chain"
        assert chain_mm.description == "Important stack-up"
        assert chain_mm.id == chain.id
        assert chain_mm is not chain

    def test_same_unit_returns_new_chain(self, uc):
        chain = ToleranceChain(
            name="Same",
            contributors=[
                Contributor(
                    name="P",
                    nominal=1.0,
                    direction=Direction.POSITIVE,
                    tolerance_type=ToleranceType.BILATERAL,
                    upper_tolerance=0.001,
                    lower_tolerance=0.001,
                ),
            ],
        )
        chain_same = uc.convert_chain(chain, UnitSystem.INCH, UnitSystem.INCH)
        assert chain_same is not chain
        assert chain_same.contributors[0].nominal == chain.contributors[0].nominal
