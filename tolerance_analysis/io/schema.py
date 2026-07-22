"""Project file JSON schema definition and validation.

Defines the schema version, required fields, and type constraints
for the tolerance analysis project file format.

Validates: Requirements 13.1, 13.2, 13.4
"""

SCHEMA_VERSION = "1.0.0"

# Required top-level fields and their expected types
REQUIRED_TOP_LEVEL_FIELDS: dict[str, type | tuple[type, ...]] = {
    "schema_version": str,
    "unit_system": str,
    "standard_mode": str,
    "project_name": str,
    "tolerance_chains": list,
}

# Valid values for enum-like fields
VALID_UNIT_SYSTEMS = {"inch", "mm"}
VALID_STANDARD_MODES = {"generic", "asme_y14_5", "iso_gps"}
VALID_TOLERANCE_TYPES = {"bilateral", "unilateral", "limit"}
VALID_DIRECTIONS = {"positive", "negative"}
VALID_DISTRIBUTIONS = {"normal", "uniform", "triangular"}

# Required fields for a tolerance chain entry
REQUIRED_CHAIN_FIELDS: dict[str, type | tuple[type, ...]] = {
    "id": str,
    "name": str,
    "contributors": list,
}

# Required fields for a contributor entry
REQUIRED_CONTRIBUTOR_FIELDS: dict[str, type | tuple[type, ...]] = {
    "id": str,
    "name": str,
    "nominal": (int, float),
    "tolerance_type": str,
    "upper_tolerance": (int, float),
    "lower_tolerance": (int, float),
    "direction": str,
    "distribution": str,
}
