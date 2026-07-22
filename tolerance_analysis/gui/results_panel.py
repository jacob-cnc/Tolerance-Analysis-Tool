"""Results panel for displaying tolerance analysis output.

Displays worst-case, RSS, and Monte Carlo results in a formatted layout
with proper unit labels and precision per unit system.

Validates: Requirements 2.3, 3.2, 3.3, 4.3, 4.4, 8.4
"""

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont
from PyQt5.QtWidgets import (
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from tolerance_analysis.boundary.unit_converter import UnitConverter, UnitSystem
from tolerance_analysis.engine.models import (
    AnalysisResults,
    MonteCarloResult,
    RSSResult,
    WorstCaseResult,
)
from tolerance_analysis.gui.theme import FONTS


def _mono_font() -> QFont:
    """Return a monospace font for numeric values."""
    font = QFont(FONTS["mono"])
    font.setStyleHint(QFont.Monospace)
    font.setPointSize(10)
    return font


def _unit_label(unit_system: UnitSystem) -> str:
    """Return the display unit abbreviation."""
    if unit_system == UnitSystem.INCH:
        return '"'
    return "mm"


class ResultsPanel(QWidget):
    """Panel displaying analysis results in formatted, readable sections.

    Shows worst-case, RSS (comparative), and Monte Carlo results with
    appropriate precision and unit labels.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self._converter = UnitConverter()
        self._setup_ui()

    def _setup_ui(self) -> None:
        """Initialize the panel layout with a scrollable content area."""
        outer_layout = QVBoxLayout(self)
        outer_layout.setContentsMargins(0, 0, 0, 0)

        # Scroll area for results content
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QScrollArea.NoFrame)
        outer_layout.addWidget(scroll)

        # Content widget inside scroll area
        self._content = QWidget()
        self._content_layout = QVBoxLayout(self._content)
        self._content_layout.setContentsMargins(8, 8, 8, 8)
        self._content_layout.setSpacing(12)
        scroll.setWidget(self._content)

        # Placeholder label
        self._placeholder = QLabel("Run an analysis to see results here")
        self._placeholder.setAlignment(Qt.AlignCenter)
        self._placeholder.setStyleSheet("color: #616161; font-style: italic;")
        self._content_layout.addWidget(self._placeholder)
        self._content_layout.addStretch()

    def set_results(self, results: AnalysisResults, unit_system: UnitSystem) -> None:
        """Update the panel with new analysis results.

        Args:
            results: The analysis results to display.
            unit_system: The active unit system for formatting and labels.
        """
        self.clear()

        has_content = False

        # Worst-case section (standalone, only if no RSS)
        if results.worst_case and not results.rss:
            self._add_worst_case_section(results.worst_case, unit_system)
            has_content = True

        # RSS section (comparative with worst-case)
        if results.rss:
            self._add_rss_section(results.rss, unit_system)
            has_content = True

        # Monte Carlo section
        if results.monte_carlo:
            self._add_monte_carlo_section(results.monte_carlo, unit_system)
            has_content = True

        if not has_content:
            self._placeholder = QLabel("Run an analysis to see results here")
            self._placeholder.setAlignment(Qt.AlignCenter)
            self._placeholder.setStyleSheet("color: #616161; font-style: italic;")
            self._content_layout.addWidget(self._placeholder)

        self._content_layout.addStretch()

    def clear(self) -> None:
        """Clear all displayed results."""
        # Remove all widgets from content layout
        while self._content_layout.count():
            item = self._content_layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()

    def _format(self, value: float, unit_system: UnitSystem) -> str:
        """Format a value with the correct precision for the unit system."""
        return self._converter.format_value(value, unit_system)

    def _make_value_label(self, text: str) -> QLabel:
        """Create a QLabel with monospace font for numeric display."""
        label = QLabel(text)
        label.setFont(_mono_font())
        return label

    def _add_worst_case_section(
        self, wc: WorstCaseResult, unit_system: UnitSystem
    ) -> None:
        """Add a worst-case results group box."""
        group = QGroupBox("Worst-Case Results")
        layout = QVBoxLayout(group)
        layout.setSpacing(6)

        unit = _unit_label(unit_system)

        rows = [
            ("Nominal:", self._format(wc.nominal, unit_system)),
            ("Maximum:", self._format(wc.maximum, unit_system)),
            ("Minimum:", self._format(wc.minimum, unit_system)),
            ("Tolerance Band:", self._format(wc.tolerance_band, unit_system)),
        ]

        for label_text, value_text in rows:
            row = QHBoxLayout()
            lbl = QLabel(label_text)
            lbl.setMinimumWidth(120)
            row.addWidget(lbl)

            val = self._make_value_label(f"{value_text} {unit}")
            row.addWidget(val)
            row.addStretch()
            layout.addLayout(row)

        self._content_layout.addWidget(group)

    def _add_rss_section(self, rss: RSSResult, unit_system: UnitSystem) -> None:
        """Add RSS results in comparative format alongside worst-case."""
        group = QGroupBox("RSS vs Worst-Case Comparison")
        layout = QVBoxLayout(group)
        layout.setSpacing(6)

        unit = _unit_label(unit_system)
        wc = rss.worst_case

        # Header row
        header = QHBoxLayout()
        header_label = QLabel("")
        header_label.setMinimumWidth(120)
        header.addWidget(header_label)

        rss_header = QLabel("RSS")
        rss_header.setFont(_mono_font())
        rss_header.setMinimumWidth(140)
        header.addWidget(rss_header)

        wc_header = QLabel("Worst-Case")
        wc_header.setFont(_mono_font())
        wc_header.setMinimumWidth(140)
        header.addWidget(wc_header)

        header.addStretch()
        layout.addLayout(header)

        # Data rows: (label, rss_value, wc_value)
        rows = [
            (
                "Nominal:",
                self._format(rss.nominal, unit_system),
                self._format(wc.nominal, unit_system),
            ),
            (
                "Maximum:",
                self._format(rss.statistical_maximum, unit_system),
                self._format(wc.maximum, unit_system),
            ),
            (
                "Minimum:",
                self._format(rss.statistical_minimum, unit_system),
                self._format(wc.minimum, unit_system),
            ),
            (
                "Band:",
                self._format(rss.statistical_band, unit_system),
                self._format(wc.tolerance_band, unit_system),
            ),
        ]

        for label_text, rss_val, wc_val in rows:
            row = QHBoxLayout()
            lbl = QLabel(label_text)
            lbl.setMinimumWidth(120)
            row.addWidget(lbl)

            rss_lbl = self._make_value_label(f"{rss_val} {unit}")
            rss_lbl.setMinimumWidth(140)
            row.addWidget(rss_lbl)

            wc_lbl = self._make_value_label(f"{wc_val} {unit}")
            wc_lbl.setMinimumWidth(140)
            row.addWidget(wc_lbl)

            row.addStretch()
            layout.addLayout(row)

        self._content_layout.addWidget(group)

    def _add_monte_carlo_section(
        self, mc: MonteCarloResult, unit_system: UnitSystem
    ) -> None:
        """Add Monte Carlo results section with statistics and percentiles."""
        group = QGroupBox("Monte Carlo Results")
        layout = QVBoxLayout(group)
        layout.setSpacing(6)

        unit = _unit_label(unit_system)

        # Iteration count
        iter_row = QHBoxLayout()
        iter_lbl = QLabel("Iterations:")
        iter_lbl.setMinimumWidth(120)
        iter_row.addWidget(iter_lbl)
        iter_val = self._make_value_label(f"{mc.num_iterations:,}")
        iter_row.addWidget(iter_val)
        iter_row.addStretch()
        layout.addLayout(iter_row)

        # Statistics
        stats_rows = [
            ("Mean:", self._format(mc.mean, unit_system)),
            ("Std Dev:", self._format(mc.std_dev, unit_system)),
            ("Minimum:", self._format(mc.minimum, unit_system)),
            ("Maximum:", self._format(mc.maximum, unit_system)),
        ]

        for label_text, value_text in stats_rows:
            row = QHBoxLayout()
            lbl = QLabel(label_text)
            lbl.setMinimumWidth(120)
            row.addWidget(lbl)

            val = self._make_value_label(f"{value_text} {unit}")
            row.addWidget(val)
            row.addStretch()
            layout.addLayout(row)

        # Percentiles sub-section
        if mc.percentiles:
            sep = QLabel("─── Percentiles ───")
            sep.setStyleSheet("color: #616161; margin-top: 4px;")
            layout.addWidget(sep)

            # Map percentile keys to readable labels
            percentile_labels = {
                "0.135": "-3\u03c3 (0.135%)",
                "2.275": "-2\u03c3 (2.275%)",
                "50": "Median (50%)",
                "97.725": "+2\u03c3 (97.725%)",
                "99.865": "+3\u03c3 (99.865%)",
            }

            for key, display_name in percentile_labels.items():
                if key in mc.percentiles:
                    row = QHBoxLayout()
                    lbl = QLabel(f"{display_name}:")
                    lbl.setMinimumWidth(160)
                    row.addWidget(lbl)

                    val = self._make_value_label(
                        f"{self._format(mc.percentiles[key], unit_system)} {unit}"
                    )
                    row.addWidget(val)
                    row.addStretch()
                    layout.addLayout(row)

        self._content_layout.addWidget(group)
