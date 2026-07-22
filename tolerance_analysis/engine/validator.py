"""Input validation for the tolerance analysis engine.

Provides validation for numeric inputs, contributor data, chain constraints,
and chain naming rules. All validation methods return error messages rather
than raising exceptions, allowing the UI layer to display appropriate feedback.
"""

from tolerance_analysis.engine.models import Contributor, ToleranceChain, ToleranceType


# Numeric range bounds per requirement 11.6
MIN_NUMERIC_VALUE = -999999.9999
MAX_NUMERIC_VALUE = 999999.9999
MAX_DECIMAL_PLACES = 4

# Chain name constraints per requirement 1.9
MIN_CHAIN_NAME_LENGTH = 1
MAX_CHAIN_NAME_LENGTH = 100

# Chain description constraint
MAX_DESCRIPTION_LENGTH = 500

# Minimum contributors for analysis
MIN_CONTRIBUTORS_FOR_ANALYSIS = 2


class Validator:
    """Validates user inputs for tolerance analysis.

    All validation methods return lists of error messages (empty = valid)
    or tuples with parse results for numeric input.
    """

    def validate_contributor(self, contributor: Contributor) -> list[str]:
        """Validate a contributor's data fields.

        Checks:
        - Nominal is within the accepted numeric range
        - Tolerances are non-negative for bilateral type
        - For unilateral: upper_tolerance >= 0; lower_tolerance can be negative
        - Tolerance values are within numeric range

        Args:
            contributor: The Contributor dataclass to validate.

        Returns:
            List of error messages. Empty list means valid.
        """
        errors: list[str] = []

        # Validate nominal is within range
        if not (MIN_NUMERIC_VALUE <= contributor.nominal <= MAX_NUMERIC_VALUE):
            errors.append(
                f"Nominal value {contributor.nominal} is outside the accepted range "
                f"[{MIN_NUMERIC_VALUE}, {MAX_NUMERIC_VALUE}]."
            )

        # Validate upper_tolerance within range
        if not (MIN_NUMERIC_VALUE <= contributor.upper_tolerance <= MAX_NUMERIC_VALUE):
            errors.append(
                f"Upper tolerance {contributor.upper_tolerance} is outside the accepted range "
                f"[{MIN_NUMERIC_VALUE}, {MAX_NUMERIC_VALUE}]."
            )

        # Validate lower_tolerance within range
        if not (MIN_NUMERIC_VALUE <= contributor.lower_tolerance <= MAX_NUMERIC_VALUE):
            errors.append(
                f"Lower tolerance {contributor.lower_tolerance} is outside the accepted range "
                f"[{MIN_NUMERIC_VALUE}, {MAX_NUMERIC_VALUE}]."
            )

        # Tolerance sign constraints depend on tolerance type
        if contributor.tolerance_type == ToleranceType.BILATERAL:
            # Bilateral tolerances must be non-negative (symmetric ±)
            if contributor.upper_tolerance < 0:
                errors.append(
                    "Bilateral upper tolerance must be non-negative."
                )
            if contributor.lower_tolerance < 0:
                errors.append(
                    "Bilateral lower tolerance must be non-negative."
                )
        elif contributor.tolerance_type == ToleranceType.UNILATERAL:
            # Unilateral: upper_tolerance must be >= 0
            # lower_tolerance can be negative (e.g., +0.000 / -0.005)
            if contributor.upper_tolerance < 0:
                errors.append(
                    "Unilateral upper tolerance must be non-negative."
                )
        elif contributor.tolerance_type == ToleranceType.LIMIT:
            # Limit: upper must be >= lower
            if contributor.upper_tolerance < contributor.lower_tolerance:
                errors.append(
                    "Upper limit must be greater than or equal to lower limit."
                )

        return errors

    def validate_chain(self, chain: ToleranceChain) -> list[str]:
        """Validate chain-level constraints.

        Checks:
        - Chain name is valid (1-100 characters)
        - Description length is within bounds (0-500)
        - Chain has minimum number of contributors for analysis

        Args:
            chain: The ToleranceChain dataclass to validate.

        Returns:
            List of error messages. Empty list means valid.
        """
        errors: list[str] = []

        # Validate name
        if not chain.name or not chain.name.strip():
            errors.append("Chain name cannot be empty.")
        elif len(chain.name) > MAX_CHAIN_NAME_LENGTH:
            errors.append(
                f"Chain name must be {MAX_CHAIN_NAME_LENGTH} characters or fewer "
                f"(currently {len(chain.name)})."
            )

        # Validate description length
        if len(chain.description) > MAX_DESCRIPTION_LENGTH:
            errors.append(
                f"Chain description must be {MAX_DESCRIPTION_LENGTH} characters or fewer "
                f"(currently {len(chain.description)})."
            )

        # Validate minimum contributors
        if len(chain.contributors) < MIN_CONTRIBUTORS_FOR_ANALYSIS:
            errors.append(
                f"Chain must have at least {MIN_CONTRIBUTORS_FOR_ANALYSIS} contributors "
                f"for analysis (currently {len(chain.contributors)})."
            )

        return errors

    def validate_chain_name(self, name: str, existing_names: list[str]) -> list[str]:
        """Validate chain name for length and uniqueness.

        Args:
            name: The proposed chain name.
            existing_names: List of names already in use.

        Returns:
            List of error messages. Empty list means valid.
        """
        errors: list[str] = []

        # Check empty / whitespace-only
        if not name or not name.strip():
            errors.append("Chain name cannot be empty.")
            return errors

        # Check length bounds
        if len(name) > MAX_CHAIN_NAME_LENGTH:
            errors.append(
                f"Chain name must be {MAX_CHAIN_NAME_LENGTH} characters or fewer "
                f"(currently {len(name)})."
            )

        # Check uniqueness (case-sensitive comparison)
        if name in existing_names:
            errors.append(
                f"A chain named '{name}' already exists. Chain names must be unique."
            )

        return errors

    def validate_numeric_input(
        self, value: str, field_name: str
    ) -> tuple[bool, float | None, str]:
        """Parse and validate a numeric input string.

        Attempts to parse the string as a float, then checks it falls within
        the acceptable range [-999999.9999, 999999.9999] with up to 4 decimal
        places.

        Args:
            value: The raw string from user input.
            field_name: Name of the field (used in error messages).

        Returns:
            Tuple of (is_valid, parsed_value_or_None, error_message).
            If valid: (True, float_value, "")
            If invalid: (False, None, "descriptive error message")
        """
        # Reject empty or whitespace-only input
        stripped = value.strip()
        if not stripped:
            return (False, None, f"{field_name} cannot be empty.")

        # Attempt to parse as float
        try:
            parsed = float(stripped)
        except ValueError:
            return (
                False,
                None,
                f"{field_name} must be a valid number. '{value}' is not numeric.",
            )

        # Reject special float values (inf, nan)
        if not _is_finite(parsed):
            return (
                False,
                None,
                f"{field_name} must be a finite number.",
            )

        # Check range
        if parsed < MIN_NUMERIC_VALUE or parsed > MAX_NUMERIC_VALUE:
            return (
                False,
                None,
                f"{field_name} must be between {MIN_NUMERIC_VALUE} and "
                f"{MAX_NUMERIC_VALUE}. Got {parsed}.",
            )

        # Check decimal places (up to 4 allowed)
        if not _check_decimal_places(stripped, MAX_DECIMAL_PLACES):
            return (
                False,
                None,
                f"{field_name} allows at most {MAX_DECIMAL_PLACES} decimal places.",
            )

        return (True, parsed, "")


def _is_finite(value: float) -> bool:
    """Check if a float value is finite (not inf or nan)."""
    import math

    return math.isfinite(value)


def _check_decimal_places(value_str: str, max_places: int) -> bool:
    """Check that the string representation has at most max_places decimals.

    Args:
        value_str: The stripped numeric string.
        max_places: Maximum allowed decimal digits.

    Returns:
        True if within limit, False otherwise.
    """
    # Handle scientific notation — allow it but check effective precision
    if "e" in value_str.lower():
        # For scientific notation, just accept if it parses to a valid float
        # The range check already bounds the effective value
        return True

    if "." in value_str:
        decimal_part = value_str.split(".")[-1]
        return len(decimal_part) <= max_places

    # No decimal point — integer representation, always valid
    return True
