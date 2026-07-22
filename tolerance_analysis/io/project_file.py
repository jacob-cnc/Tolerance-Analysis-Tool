"""JSON project file serialization and deserialization.

Implements save/load with write-ahead pattern for crash safety,
schema validation, and detailed error reporting on parse failures.

Validates: Requirements 6.1, 6.2, 6.3, 6.5, 6.6, 13.1, 13.2, 13.3, 13.4, 13.5, 13.6
"""

import json
import os
import warnings
from datetime import datetime, timezone
from typing import Any

from tolerance_analysis.engine.models import (
    AnalysisResults,
    Contributor,
    Direction,
    DistributionType,
    MonteCarloResult,
    Project,
    RSSResult,
    ToleranceChain,
    ToleranceType,
    WorstCaseResult,
)
from tolerance_analysis.io.schema import (
    REQUIRED_CHAIN_FIELDS,
    REQUIRED_CONTRIBUTOR_FIELDS,
    REQUIRED_TOP_LEVEL_FIELDS,
    SCHEMA_VERSION,
    VALID_DIRECTIONS,
    VALID_DISTRIBUTIONS,
    VALID_STANDARD_MODES,
    VALID_TOLERANCE_TYPES,
    VALID_UNIT_SYSTEMS,
)


class ProjectFileError(Exception):
    """Raised on project file parse/validation failures.

    Attributes:
        message: Human-readable error description.
        field: The field name where the error occurred, if applicable.
        line: The line number where the error occurred, if applicable.
    """

    def __init__(self, message: str, field: str = "", line: int | None = None):
        self.field = field
        self.line = line
        detail_parts = []
        if field:
            detail_parts.append(f"field='{field}'")
        if line is not None:
            detail_parts.append(f"line={line}")
        if detail_parts:
            full_message = f"{message} ({', '.join(detail_parts)})"
        else:
            full_message = message
        super().__init__(full_message)


# Direction enum serialization mapping
_DIRECTION_TO_STR = {
    Direction.POSITIVE: "positive",
    Direction.NEGATIVE: "negative",
}
_STR_TO_DIRECTION = {v: k for k, v in _DIRECTION_TO_STR.items()}

# ToleranceType enum serialization mapping
_TOLERANCE_TYPE_TO_STR = {
    ToleranceType.BILATERAL: "bilateral",
    ToleranceType.UNILATERAL: "unilateral",
    ToleranceType.LIMIT: "limit",
}
_STR_TO_TOLERANCE_TYPE = {v: k for k, v in _TOLERANCE_TYPE_TO_STR.items()}

# DistributionType enum serialization mapping
_DISTRIBUTION_TO_STR = {
    DistributionType.NORMAL: "normal",
    DistributionType.UNIFORM: "uniform",
    DistributionType.TRIANGULAR: "triangular",
}
_STR_TO_DISTRIBUTION = {v: k for k, v in _DISTRIBUTION_TO_STR.items()}


class ProjectFileManager:
    """Manages project file serialization and deserialization.

    Uses a write-ahead pattern for safe file writes:
    1. Serialize to memory
    2. Write to {filepath}.tmp
    3. Verify temp file is valid JSON
    4. Atomic rename: {filepath}.tmp -> {filepath}
    5. On failure at any step, original file is untouched
    """

    SCHEMA_VERSION = SCHEMA_VERSION

    def save(self, project: Project, filepath: str) -> None:
        """Serialize project to JSON with 2-space indent, 6+ significant digits.

        Uses write-ahead pattern: writes to .tmp file first, verifies,
        then renames to final path.

        Args:
            project: The project to serialize.
            filepath: Destination file path.

        Raises:
            ProjectFileError: If serialization or file write fails.
        """
        try:
            data = self._serialize_project(project)
            json_str = json.dumps(data, indent=2, ensure_ascii=False)
        except (TypeError, ValueError) as e:
            raise ProjectFileError(f"Serialization failed: {e}") from e

        tmp_path = filepath + ".tmp"

        try:
            # Step 2: Write to temp file
            dir_path = os.path.dirname(filepath)
            if dir_path:
                os.makedirs(dir_path, exist_ok=True)
            with open(tmp_path, "w", encoding="utf-8") as f:
                f.write(json_str)

            # Step 3: Verify temp file is valid JSON
            with open(tmp_path, "r", encoding="utf-8") as f:
                json.load(f)

            # Step 4: Atomic rename (on Windows, need to remove target first)
            if os.path.exists(filepath):
                os.replace(tmp_path, filepath)
            else:
                os.rename(tmp_path, filepath)

        except OSError as e:
            # Clean up temp file on failure
            if os.path.exists(tmp_path):
                try:
                    os.remove(tmp_path)
                except OSError:
                    pass
            raise ProjectFileError(
                f"File system write failed: {e}"
            ) from e
        except json.JSONDecodeError as e:
            # Verification of temp file failed — should not happen
            if os.path.exists(tmp_path):
                try:
                    os.remove(tmp_path)
                except OSError:
                    pass
            raise ProjectFileError(
                f"Verification of written file failed: {e}"
            ) from e

    def load(self, filepath: str) -> Project:
        """Deserialize project from JSON file.

        Raises ProjectFileError with field/line info on parse failure.
        Issues a warning for unrecognized schema versions but attempts
        to load anyway.

        Args:
            filepath: Path to the project file.

        Returns:
            The deserialized Project instance.

        Raises:
            ProjectFileError: On JSON parse failure or validation errors.
        """
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                raw_content = f.read()
        except OSError as e:
            raise ProjectFileError(f"Cannot read file: {e}") from e

        # Parse JSON with line-level error reporting
        try:
            data = json.loads(raw_content)
        except json.JSONDecodeError as e:
            raise ProjectFileError(
                f"Invalid JSON: {e.msg}",
                field="",
                line=e.lineno,
            ) from e

        if not isinstance(data, dict):
            raise ProjectFileError(
                "Project file root must be a JSON object",
                field="(root)",
            )

        # Schema version check — non-blocking warning for unrecognized versions
        file_version = data.get("schema_version", "")
        if file_version and file_version != self.SCHEMA_VERSION:
            warnings.warn(
                f"Unrecognized schema version '{file_version}' "
                f"(supported: '{self.SCHEMA_VERSION}'). "
                f"Attempting to load anyway.",
                UserWarning,
                stacklevel=2,
            )

        # Validate schema
        errors = self.validate_schema(data)
        if errors:
            raise ProjectFileError(
                f"Schema validation failed: {errors[0]}",
                field=errors[0].split("'")[1] if "'" in errors[0] else "",
            )

        # Deserialize
        try:
            return self._deserialize_project(data, filepath)
        except (KeyError, TypeError, ValueError) as e:
            raise ProjectFileError(
                f"Deserialization failed: {e}"
            ) from e

    def validate_schema(self, data: dict) -> list[str]:
        """Check required fields and types in project data.

        Args:
            data: The parsed JSON dictionary.

        Returns:
            List of error messages. Empty list means valid.
        """
        errors: list[str] = []

        # Check required top-level fields
        for field_name, expected_type in REQUIRED_TOP_LEVEL_FIELDS.items():
            if field_name not in data:
                errors.append(f"Missing required field '{field_name}'")
            elif not isinstance(data[field_name], expected_type):
                errors.append(
                    f"Field '{field_name}' must be of type "
                    f"{expected_type.__name__ if isinstance(expected_type, type) else str(expected_type)}, "
                    f"got {type(data[field_name]).__name__}"
                )

        # Validate enum-like field values
        if "unit_system" in data and isinstance(data["unit_system"], str):
            if data["unit_system"] not in VALID_UNIT_SYSTEMS:
                errors.append(
                    f"Invalid unit_system '{data['unit_system']}'. "
                    f"Must be one of: {sorted(VALID_UNIT_SYSTEMS)}"
                )

        if "standard_mode" in data and isinstance(data["standard_mode"], str):
            if data["standard_mode"] not in VALID_STANDARD_MODES:
                errors.append(
                    f"Invalid standard_mode '{data['standard_mode']}'. "
                    f"Must be one of: {sorted(VALID_STANDARD_MODES)}"
                )

        # Validate tolerance chains array
        chains = data.get("tolerance_chains")
        if isinstance(chains, list):
            for i, chain in enumerate(chains):
                if not isinstance(chain, dict):
                    errors.append(
                        f"tolerance_chains[{i}] must be an object"
                    )
                    continue
                chain_errors = self._validate_chain(chain, i)
                errors.extend(chain_errors)

        return errors

    def _validate_chain(self, chain: dict, index: int) -> list[str]:
        """Validate a single tolerance chain entry."""
        errors: list[str] = []
        prefix = f"tolerance_chains[{index}]"

        for field_name, expected_type in REQUIRED_CHAIN_FIELDS.items():
            if field_name not in chain:
                errors.append(f"Missing required field '{prefix}.{field_name}'")
            elif not isinstance(chain[field_name], expected_type):
                type_name = (
                    expected_type.__name__
                    if isinstance(expected_type, type)
                    else str(expected_type)
                )
                errors.append(
                    f"Field '{prefix}.{field_name}' must be of type {type_name}"
                )

        # Validate contributors
        contributors = chain.get("contributors")
        if isinstance(contributors, list):
            for j, contrib in enumerate(contributors):
                if not isinstance(contrib, dict):
                    errors.append(
                        f"{prefix}.contributors[{j}] must be an object"
                    )
                    continue
                contrib_errors = self._validate_contributor(
                    contrib, f"{prefix}.contributors[{j}]"
                )
                errors.extend(contrib_errors)

        return errors

    def _validate_contributor(self, contrib: dict, prefix: str) -> list[str]:
        """Validate a single contributor entry."""
        errors: list[str] = []

        for field_name, expected_type in REQUIRED_CONTRIBUTOR_FIELDS.items():
            if field_name not in contrib:
                errors.append(f"Missing required field '{prefix}.{field_name}'")
            elif not isinstance(contrib[field_name], expected_type):
                type_name = (
                    expected_type.__name__
                    if isinstance(expected_type, type)
                    else str(expected_type)
                )
                errors.append(
                    f"Field '{prefix}.{field_name}' must be of type {type_name}"
                )

        # Validate enum values
        if "tolerance_type" in contrib and isinstance(contrib["tolerance_type"], str):
            if contrib["tolerance_type"] not in VALID_TOLERANCE_TYPES:
                errors.append(
                    f"{prefix}.tolerance_type '{contrib['tolerance_type']}' "
                    f"is invalid. Must be one of: {sorted(VALID_TOLERANCE_TYPES)}"
                )

        if "direction" in contrib and isinstance(contrib["direction"], str):
            if contrib["direction"] not in VALID_DIRECTIONS:
                errors.append(
                    f"{prefix}.direction '{contrib['direction']}' "
                    f"is invalid. Must be one of: {sorted(VALID_DIRECTIONS)}"
                )

        if "distribution" in contrib and isinstance(contrib["distribution"], str):
            if contrib["distribution"] not in VALID_DISTRIBUTIONS:
                errors.append(
                    f"{prefix}.distribution '{contrib['distribution']}' "
                    f"is invalid. Must be one of: {sorted(VALID_DISTRIBUTIONS)}"
                )

        return errors

    # --- Serialization helpers ---

    def _serialize_project(self, project: Project) -> dict[str, Any]:
        """Convert a Project instance to a serializable dictionary."""
        now = datetime.now(timezone.utc)
        return {
            "schema_version": self.SCHEMA_VERSION,
            "unit_system": project.unit_system,
            "standard_mode": project.standard_mode,
            "project_name": project.name,
            "created": project.created.isoformat(),
            "modified": now.isoformat(),
            "tolerance_chains": [
                self._serialize_chain(chain)
                for chain in project.tolerance_chains
            ],
        }

    def _serialize_chain(self, chain: ToleranceChain) -> dict[str, Any]:
        """Convert a ToleranceChain to a serializable dictionary."""
        return {
            "id": chain.id,
            "name": chain.name,
            "description": chain.description,
            "contributors": [
                self._serialize_contributor(c) for c in chain.contributors
            ],
            "analysis_settings": {
                "monte_carlo_iterations": 10000,
            },
        }

    def _serialize_contributor(self, contributor: Contributor) -> dict[str, Any]:
        """Convert a Contributor to a serializable dictionary."""
        return {
            "id": contributor.id,
            "name": contributor.name,
            "nominal": contributor.nominal,
            "tolerance_type": _TOLERANCE_TYPE_TO_STR[contributor.tolerance_type],
            "upper_tolerance": contributor.upper_tolerance,
            "lower_tolerance": contributor.lower_tolerance,
            "direction": _DIRECTION_TO_STR[contributor.direction],
            "distribution": _DISTRIBUTION_TO_STR[contributor.distribution],
            "description": contributor.description,
            "notes": contributor.notes,
            "material": contributor.material,
        }

    # --- Deserialization helpers ---

    def _deserialize_project(self, data: dict, filepath: str) -> Project:
        """Convert a parsed dictionary back to a Project instance."""
        created = self._parse_datetime(data.get("created", ""))
        modified = self._parse_datetime(data.get("modified", ""))

        chains = [
            self._deserialize_chain(chain_data)
            for chain_data in data.get("tolerance_chains", [])
        ]

        return Project(
            name=data["project_name"],
            filepath=filepath,
            unit_system=data["unit_system"],
            standard_mode=data["standard_mode"],
            tolerance_chains=chains,
            created=created,
            modified=modified,
        )

    def _deserialize_chain(self, data: dict) -> ToleranceChain:
        """Convert a dictionary to a ToleranceChain instance."""
        contributors = [
            self._deserialize_contributor(c)
            for c in data.get("contributors", [])
        ]

        return ToleranceChain(
            name=data["name"],
            description=data.get("description", ""),
            contributors=contributors,
            id=data["id"],
        )

    def _deserialize_contributor(self, data: dict) -> Contributor:
        """Convert a dictionary to a Contributor instance."""
        return Contributor(
            name=data["name"],
            nominal=data["nominal"],
            direction=_STR_TO_DIRECTION[data["direction"]],
            tolerance_type=_STR_TO_TOLERANCE_TYPE[data["tolerance_type"]],
            upper_tolerance=data["upper_tolerance"],
            lower_tolerance=data["lower_tolerance"],
            distribution=_STR_TO_DISTRIBUTION[data["distribution"]],
            description=data.get("description", ""),
            notes=data.get("notes", ""),
            material=data.get("material", ""),
            id=data["id"],
        )

    def _parse_datetime(self, value: str) -> datetime:
        """Parse an ISO 8601 datetime string.

        Falls back to current time if parsing fails.
        """
        if not value:
            return datetime.now(timezone.utc)
        try:
            # Handle timezone-aware ISO format
            return datetime.fromisoformat(value)
        except (ValueError, TypeError):
            return datetime.now(timezone.utc)
