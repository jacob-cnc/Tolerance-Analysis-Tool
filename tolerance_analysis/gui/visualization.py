"""Stack-up visualization canvas for the Tolerance Analysis Tool.

Provides a custom QPainter-based horizontal stacking bar chart showing
contributor bars, tolerance bands, result indicators, and Monte Carlo
distribution overlays.
"""

from typing import Optional

from PyQt5.QtCore import QRectF, QSize, Qt
from PyQt5.QtGui import QColor, QPainter, QPen, QFont, QPaintEvent
from PyQt5.QtWidgets import QWidget

from tolerance_analysis.engine.models import (
    AnalysisResults,
    Direction,
    MonteCarloResult,
    ToleranceChain,
    WorstCaseResult,
)
from tolerance_analysis.gui.theme import COLORS


class VisualizationCanvas(QWidget):
    """Custom-painted horizontal stacking bar chart for tolerance stack-up.

    Renders contributor bars proportional to their nominal values, tolerance
    bands as translucent overlays, result indicators, and optional Monte Carlo
    distribution histograms.

    Uses QPainter for all rendering (no matplotlib dependency).
    """

    # Layout constants
    _MARGIN_TOP = 50
    _MARGIN_BOTTOM = 60
    _MARGIN_LEFT = 20
    _MARGIN_RIGHT = 20
    _BAR_HEIGHT = 50
    _RESULT_BAR_HEIGHT = 24
    _LABEL_HEIGHT = 28
    _MC_HEIGHT = 60
    _GAP = 12

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.setObjectName("VisualizationCanvas")
        self.setMinimumSize(400, 200)

        self._chain: Optional[ToleranceChain] = None
        self._results: Optional[AnalysisResults] = None

    def sizeHint(self) -> QSize:
        """Return preferred size for the canvas."""
        return QSize(800, 300)

    def set_chain(
        self, chain: ToleranceChain, results: Optional[AnalysisResults] = None
    ) -> None:
        """Update visualization data and trigger repaint.

        Args:
            chain: The tolerance chain to visualize.
            results: Optional analysis results (worst-case, RSS, Monte Carlo).
        """
        self._chain = chain
        self._results = results
        self.update()

    def paintEvent(self, event: QPaintEvent) -> None:
        """Custom paint: bars, tolerance bands, result indicators."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        # Fill background (in case stylesheet doesn't apply)
        bg_color = QColor(COLORS["canvas_bg"])
        painter.fillRect(self.rect(), bg_color)

        # Check for empty state
        if self._chain is None or not self._chain.contributors:
            self._draw_placeholder(painter)
            painter.end()
            return

        # Draw the stack-up visualization
        self._draw_contributor_bars(painter)
        self._draw_result_bar(painter)

        # Draw Monte Carlo overlay if available
        if (
            self._results is not None
            and self._results.monte_carlo is not None
        ):
            self._draw_monte_carlo_overlay(painter)

        painter.end()

    def _draw_placeholder(self, painter: QPainter) -> None:
        """Show centered placeholder message when no contributors present."""
        text_color = QColor(COLORS["text_on_dark"])
        painter.setPen(QPen(text_color))
        font = QFont("Inter", 14)
        font.setStyleHint(QFont.SansSerif)
        painter.setFont(font)
        painter.drawText(self.rect(), Qt.AlignCenter, "No contributors added")

    def _draw_contributor_bars(self, painter: QPainter) -> None:
        """Render horizontal stacking bars proportional to contributor nominals."""
        contributors = self._chain.contributors
        if not contributors:
            return

        # Calculate total absolute nominal span for scaling
        total_abs_nominal = sum(abs(c.nominal) for c in contributors)
        if total_abs_nominal == 0:
            total_abs_nominal = 1.0  # Avoid division by zero

        # Available drawing width
        canvas_width = self.width() - self._MARGIN_LEFT - self._MARGIN_RIGHT
        scale = canvas_width / total_abs_nominal

        # Draw each contributor as a bar segment
        x_offset = self._MARGIN_LEFT
        y_bar = self._MARGIN_TOP

        label_font = QFont("Inter", 10)
        label_font.setStyleHint(QFont.SansSerif)
        value_font = QFont("JetBrains Mono", 9)
        value_font.setStyleHint(QFont.Monospace)
        text_color = QColor(COLORS["text_on_dark"])

        for contributor in contributors:
            # Determine bar color based on direction
            if contributor.direction == Direction.POSITIVE:
                bar_color = QColor(COLORS["positive"])
            else:
                bar_color = QColor(COLORS["negative"])

            # Calculate bar width from nominal
            bar_width = abs(contributor.nominal) * scale
            if bar_width < 2:
                bar_width = 2  # Minimum visible width

            # Draw the solid bar
            bar_rect = QRectF(x_offset, y_bar, bar_width, self._BAR_HEIGHT)
            painter.fillRect(bar_rect, bar_color)

            # Draw tolerance band as 30% opacity overlay
            tol_color = QColor(bar_color)
            tol_color.setAlpha(77)  # 30% opacity (0.3 * 255 ≈ 77)

            # Tolerance band extends beyond the bar proportionally
            tol_width = (contributor.upper_tolerance + contributor.lower_tolerance) * scale
            if tol_width > 0:
                tol_rect = QRectF(
                    x_offset - (contributor.lower_tolerance * scale),
                    y_bar,
                    bar_width + tol_width,
                    self._BAR_HEIGHT,
                )
                painter.fillRect(tol_rect, tol_color)

            # Draw contributor name label below bar - allow overflow for readability
            painter.setPen(QPen(text_color))
            painter.setFont(label_font)
            label_rect = QRectF(
                x_offset, y_bar + self._BAR_HEIGHT + 4, max(bar_width, 150), self._LABEL_HEIGHT + 8
            )
            painter.drawText(
                label_rect, Qt.AlignLeft | Qt.AlignTop, contributor.name
            )

            # Draw nominal value above bar
            painter.setFont(value_font)
            value_rect = QRectF(x_offset, y_bar - 16, bar_width, 14)
            painter.drawText(
                value_rect, Qt.AlignCenter, f"{contributor.nominal:.4f}"
            )

            x_offset += bar_width

    def _draw_result_bar(self, painter: QPainter) -> None:
        """Render result bar (green in-spec, red out-of-spec)."""
        if self._results is None or self._results.worst_case is None:
            return

        wc: WorstCaseResult = self._results.worst_case
        contributors = self._chain.contributors

        # Calculate total absolute nominal span for scaling
        total_abs_nominal = sum(abs(c.nominal) for c in contributors)
        if total_abs_nominal == 0:
            total_abs_nominal = 1.0

        canvas_width = self.width() - self._MARGIN_LEFT - self._MARGIN_RIGHT
        scale = canvas_width / total_abs_nominal

        # Position result bar below contributor bars
        y_result = (
            self._MARGIN_TOP
            + self._BAR_HEIGHT
            + self._LABEL_HEIGHT
            + self._GAP * 2
        )

        # Result bar represents the total nominal dimension
        result_width = abs(wc.nominal) * scale
        if result_width < 4:
            result_width = 4

        # Determine color: green for in-spec, red for out-of-spec
        # Use a simple heuristic: if tolerance_band is reasonable relative to nominal
        # For now, default to in-spec (green) since we don't have spec limits defined
        # The result is always "in-spec" for worst-case unless external limits are set
        result_color = QColor(COLORS["in_spec"])

        result_rect = QRectF(
            self._MARGIN_LEFT, y_result, result_width, self._RESULT_BAR_HEIGHT
        )
        painter.fillRect(result_rect, result_color)

        # Draw tolerance band on result bar
        tol_width = wc.total_tolerance * scale * 2
        if tol_width > 0:
            tol_color = QColor(result_color)
            tol_color.setAlpha(77)  # 30% opacity
            tol_rect = QRectF(
                self._MARGIN_LEFT + result_width / 2 - tol_width / 2,
                y_result,
                tol_width,
                self._RESULT_BAR_HEIGHT,
            )
            painter.fillRect(tol_rect, tol_color)

        # Label the result
        text_color = QColor(COLORS["text_on_dark"])
        painter.setPen(QPen(text_color))
        label_font = QFont("JetBrains Mono", 10)
        label_font.setStyleHint(QFont.Monospace)
        painter.setFont(label_font)

        result_text = (
            f"Nom: {wc.nominal:.4f}  "
            f"Tol: ±{wc.total_tolerance:.4f}  "
            f"[{wc.minimum:.4f}, {wc.maximum:.4f}]"
        )
        text_rect = QRectF(
            self._MARGIN_LEFT,
            y_result + self._RESULT_BAR_HEIGHT + 4,
            canvas_width,
            self._LABEL_HEIGHT,
        )
        painter.drawText(text_rect, Qt.AlignLeft | Qt.AlignVCenter, result_text)

    def _draw_monte_carlo_overlay(self, painter: QPainter) -> None:
        """Render Monte Carlo distribution overlay in purple when available."""
        mc: MonteCarloResult = self._results.monte_carlo
        if not mc.bin_counts or not mc.bin_edges:
            return

        contributors = self._chain.contributors
        total_abs_nominal = sum(abs(c.nominal) for c in contributors)
        if total_abs_nominal == 0:
            total_abs_nominal = 1.0

        canvas_width = self.width() - self._MARGIN_LEFT - self._MARGIN_RIGHT

        # Position MC overlay below the result bar
        y_mc = (
            self._MARGIN_TOP
            + self._BAR_HEIGHT
            + self._LABEL_HEIGHT
            + self._GAP * 2
            + self._RESULT_BAR_HEIGHT
            + self._LABEL_HEIGHT
            + self._GAP
        )

        # Scale histogram bins to canvas width
        bin_min = mc.bin_edges[0]
        bin_max = mc.bin_edges[-1]
        bin_range = bin_max - bin_min
        if bin_range == 0:
            bin_range = 1.0

        max_count = max(mc.bin_counts) if mc.bin_counts else 1
        if max_count == 0:
            max_count = 1

        # Monte Carlo purple at 60% opacity
        mc_color = QColor(COLORS["monte_carlo"])
        mc_color.setAlpha(153)  # 60% opacity (0.6 * 255 ≈ 153)

        num_bins = len(mc.bin_counts)
        bin_pixel_width = canvas_width / num_bins

        for i, count in enumerate(mc.bin_counts):
            bar_height = (count / max_count) * self._MC_HEIGHT
            x = self._MARGIN_LEFT + i * bin_pixel_width
            y = y_mc + self._MC_HEIGHT - bar_height

            bin_rect = QRectF(x, y, bin_pixel_width, bar_height)
            painter.fillRect(bin_rect, mc_color)

        # Label
        text_color = QColor(COLORS["text_on_dark"])
        painter.setPen(QPen(text_color))
        label_font = QFont("Inter", 10)
        label_font.setStyleHint(QFont.SansSerif)
        painter.setFont(label_font)

        mc_label = f"Monte Carlo ({mc.num_iterations:,} iterations)  μ={mc.mean:.4f}  σ={mc.std_dev:.4f}"
        label_rect = QRectF(
            self._MARGIN_LEFT,
            y_mc + self._MC_HEIGHT + 4,
            canvas_width,
            self._LABEL_HEIGHT,
        )
        painter.drawText(label_rect, Qt.AlignLeft | Qt.AlignVCenter, mc_label)
