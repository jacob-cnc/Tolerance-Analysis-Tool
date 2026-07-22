"""GD&T standards manager for tolerance analysis.

Provides standard-specific symbols, report labels, and default geometric
assumptions for ASME Y14.5, ISO GPS, and generic (no standard) modes.
"""

from enum import Enum


class StandardMode(Enum):
    """GD&T standard mode selection."""

    ASME = "asme_y14_5"
    ISO = "iso_gps"
    GENERIC = "generic"


# Symbol sets per standard

ASME_SYMBOLS: dict[str, str] = {
    "bilateral": "±",
    "diameter": "⌀",
    "datum": "DATUM",
    "tolerance_label": "Tolerance",
    "envelope_note": "Rule #1 (Envelope Principle) applies unless otherwise specified",
}

ISO_SYMBOLS: dict[str, str] = {
    "bilateral": "±",
    "diameter": "⌀",
    "datum": "DATUM",
    "tolerance_label": "Tolerance",
    "independency_note": "Independency principle (ISO 8015) applies unless otherwise specified",
}

GENERIC_SYMBOLS: dict[str, str] = {
    "bilateral": "±",
    "diameter": "DIA",
    "datum": "",
    "tolerance_label": "Tolerance",
}


class StandardsManager:
    """Manages GD&T standard-specific symbols, labels, and assumptions.

    Provides accessors that return the correct symbol set, report label,
    and default geometric assumption text based on the active standard mode.
    """

    def get_symbols(self, mode: StandardMode) -> dict[str, str]:
        """Return tolerance symbol set for the active standard.

        Args:
            mode: The active GD&T standard mode.

        Returns:
            Dictionary mapping symbol names to their string representations.
        """
        if mode == StandardMode.ASME:
            return dict(ASME_SYMBOLS)
        elif mode == StandardMode.ISO:
            return dict(ISO_SYMBOLS)
        else:
            return dict(GENERIC_SYMBOLS)

    def get_report_label(self, mode: StandardMode) -> str:
        """Return standard identifier string for report headers.

        Args:
            mode: The active GD&T standard mode.

        Returns:
            Standard identifier (e.g. "ASME Y14.5-2018") or empty string
            for generic mode.
        """
        if mode == StandardMode.ASME:
            return "ASME Y14.5-2018"
        elif mode == StandardMode.ISO:
            return "ISO GPS (ISO 8015)"
        else:
            return ""

    def get_default_assumption(self, mode: StandardMode) -> str:
        """Return default geometric assumption text.

        Args:
            mode: The active GD&T standard mode.

        Returns:
            Default assumption text for the standard, or empty string
            for generic mode (no assumptions).
        """
        if mode == StandardMode.ASME:
            return "Rule #1 (Envelope Principle) applies unless otherwise specified"
        elif mode == StandardMode.ISO:
            return "Independency principle (ISO 8015) applies unless otherwise specified"
        else:
            return ""
