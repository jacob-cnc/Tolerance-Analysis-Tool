"""Offscreen render harness for visual inspection of GUI widgets.

Renders any QWidget to PNG using QImage in offscreen mode.
Used for the visual feedback loop: agent generates PNGs, user drops
them into chat for review.

Usage:
    python tests/render_harness.py

Outputs test PNGs to tests/renders/
"""

import sys
import os

# Must be set before any Qt imports
os.environ["QT_QPA_PLATFORM"] = "offscreen"

from pathlib import Path

from PyQt5.QtCore import QSize, Qt
from PyQt5.QtGui import QColor, QFont, QImage, QPainter, QPen
from PyQt5.QtWidgets import (
    QApplication,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QSplitter,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

# Project imports
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from tolerance_analysis.gui.theme import COLORS, STYLESHEET


# ---------------------------------------------------------------------------
# Core render utility
# ---------------------------------------------------------------------------


def render_widget_to_png(
    widget: QWidget, filepath: str, size: tuple[int, int] | None = None
) -> None:
    """Render a QWidget to a PNG file using offscreen mode.

    Args:
        widget: The widget to render.
        filepath: Output PNG file path.
        size: Optional (width, height) tuple. Uses widget's sizeHint if not
              specified, falling back to 800x600.
    """
    if size:
        widget.resize(*size)
    elif widget.sizeHint().isValid():
        widget.resize(widget.sizeHint())
    else:
        widget.resize(800, 600)

    widget.show()

    # Process pending layout events so child widgets get positioned
    QApplication.processEvents()

    image = QImage(widget.size(), QImage.Format_ARGB32)
    image.fill(QColor(COLORS["ui_bg"]))
    widget.render(image)

    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    image.save(filepath)
    print(f"Rendered: {filepath} ({widget.width()}x{widget.height()})")


# ---------------------------------------------------------------------------
# Placeholder visualization canvas (until task 10.1 builds the real one)
# ---------------------------------------------------------------------------


class PlaceholderVisualizationCanvas(QWidget):
    """Placeholder dark-background widget mimicking the visualization canvas.

    Draws sample contributor bars to demonstrate the stack-up visualization
    area. Will be replaced by the real VisualizationCanvas in task 10.1.
    """

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("VisualizationCanvas")
        self.setMinimumSize(700, 300)

    def sizeHint(self) -> QSize:
        return QSize(700, 300)

    def paintEvent(self, event) -> None:  # noqa: N802
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        # Dark canvas background
        painter.fillRect(self.rect(), QColor(COLORS["canvas_bg"]))

        # Draw sample contributor bars
        margin = 40
        bar_height = 36
        y_start = 60
        total_width = self.width() - 2 * margin

        # Sample data: name, proportion, color_key
        contributors = [
            ("Housing Bore", 0.35, "positive"),
            ("Bearing Width", 0.25, "positive"),
            ("Shim", 0.10, "negative"),
            ("Snap Ring", 0.15, "positive"),
            ("Cover Depth", 0.15, "negative"),
        ]

        # Title
        painter.setPen(QPen(QColor(COLORS["text_on_dark"])))
        title_font = QFont("Inter", 11, QFont.Bold)
        painter.setFont(title_font)
        painter.drawText(margin, 30, "Stack-Up Visualization (Placeholder)")

        # Draw bars
        x = margin
        label_font = QFont("JetBrains Mono", 8)
        painter.setFont(label_font)

        for name, proportion, color_key in contributors:
            bar_width = int(total_width * proportion)
            color = QColor(COLORS[color_key])

            # Main bar
            painter.fillRect(x, y_start, bar_width, bar_height, color)

            # Tolerance band overlay (30% opacity)
            tol_color = QColor(color)
            tol_color.setAlpha(77)  # ~30%
            painter.fillRect(
                x + 2, y_start + bar_height, bar_width - 4, 8, tol_color
            )

            # Label
            painter.setPen(QPen(QColor(COLORS["text_on_dark"])))
            painter.drawText(
                x + 4, y_start + bar_height + 24, name
            )

            x += bar_width + 2

        # Result bar
        result_y = y_start + bar_height + 50
        result_width = total_width - 40
        painter.fillRect(
            margin + 20, result_y, result_width, 20, QColor(COLORS["in_spec"])
        )
        painter.setPen(QPen(QColor(COLORS["text_on_dark"])))
        painter.setFont(QFont("Inter", 9))
        painter.drawText(margin + 20, result_y + 36, "Result: 1.5000 ± 0.0045 (IN SPEC)")

        # Monte Carlo overlay hint
        mc_y = result_y + 60
        mc_color = QColor(COLORS["monte_carlo"])
        mc_color.setAlpha(153)  # ~60%
        for i in range(50):
            h = int(30 * (1 - abs(i - 25) / 25) ** 2) + 2
            painter.fillRect(margin + 20 + i * 6, mc_y + 30 - h, 5, h, mc_color)

        painter.setPen(QPen(QColor(COLORS["text_on_dark"])))
        painter.drawText(margin + 20, mc_y + 46, "Monte Carlo Distribution (10,000 iterations)")

        painter.end()


# ---------------------------------------------------------------------------
# Placeholder MainWindow layout
# ---------------------------------------------------------------------------


class PlaceholderMainWindow(QMainWindow):
    """Placeholder MainWindow demonstrating the application layout.

    Includes: toolbar area, contributor table, detail panel,
    visualization canvas, and results panel.
    """

    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("Tolerance Analysis Tool")
        self.setStyleSheet(STYLESHEET)
        self._build_ui()

    def _build_ui(self) -> None:
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QVBoxLayout(central)
        main_layout.setContentsMargins(8, 8, 8, 8)

        # --- Toolbar placeholder ---
        toolbar_group = QGroupBox("Toolbar")
        toolbar_layout = QHBoxLayout(toolbar_group)
        for label in ["New Chain", "Add Contributor", "Run Analysis", "Save", "Export PDF"]:
            btn_label = QLabel(f"[ {label} ]")
            btn_label.setStyleSheet(
                f"background: {COLORS['ui_surface']}; "
                f"border: 1px solid {COLORS['ui_border']}; "
                "padding: 6px 12px; border-radius: 4px;"
            )
            toolbar_layout.addWidget(btn_label)
        toolbar_layout.addStretch()
        main_layout.addWidget(toolbar_group)

        # --- Main content splitter ---
        splitter = QSplitter(Qt.Horizontal)

        # Left: Contributor table
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(0, 0, 0, 0)

        table_label = QLabel("Tolerance Chain: Main Bearing Stack")
        table_label.setStyleSheet("font-weight: bold; font-size: 11pt;")
        left_layout.addWidget(table_label)

        table = QTableWidget(5, 5)
        table.setHorizontalHeaderLabels(
            ["Name", "Nominal", "Tol+", "Tol-", "Direction"]
        )
        sample_data = [
            ("Housing Bore", "1.5000", "+0.0020", "-0.0020", "+"),
            ("Bearing Width", "0.7500", "+0.0015", "-0.0015", "+"),
            ("Shim", "0.0300", "+0.0005", "-0.0005", "-"),
            ("Snap Ring", "0.0625", "+0.0010", "-0.0010", "+"),
            ("Cover Depth", "0.5000", "+0.0020", "-0.0020", "-"),
        ]
        for row, (name, nom, tol_p, tol_n, d) in enumerate(sample_data):
            table.setItem(row, 0, QTableWidgetItem(name))
            table.setItem(row, 1, QTableWidgetItem(nom))
            table.setItem(row, 2, QTableWidgetItem(tol_p))
            table.setItem(row, 3, QTableWidgetItem(tol_n))
            table.setItem(row, 4, QTableWidgetItem(d))
        table.resizeColumnsToContents()
        left_layout.addWidget(table)

        splitter.addWidget(left_panel)

        # Right: Detail + Results
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(0, 0, 0, 0)

        detail_group = QGroupBox("Contributor Detail")
        detail_layout = QVBoxLayout(detail_group)
        for field, value in [
            ("Name:", "Housing Bore"),
            ("Nominal:", "1.5000 in"),
            ("Tolerance Type:", "Bilateral ±0.0020"),
            ("Distribution:", "Normal"),
            ("Material:", "6061-T6 Aluminum"),
        ]:
            row_widget = QWidget()
            row_layout = QHBoxLayout(row_widget)
            row_layout.setContentsMargins(0, 2, 0, 2)
            lbl = QLabel(field)
            lbl.setStyleSheet("font-weight: bold;")
            val = QLabel(value)
            row_layout.addWidget(lbl)
            row_layout.addWidget(val)
            row_layout.addStretch()
            detail_layout.addWidget(row_widget)
        right_layout.addWidget(detail_group)

        results_group = QGroupBox("Analysis Results")
        results_layout = QVBoxLayout(results_group)
        for line in [
            "Worst Case: 1.5000 ± 0.0070  [1.4930 – 1.5070]",
            "RSS:        1.5000 ± 0.0035  [1.4965 – 1.5035]",
            "Monte Carlo: μ=1.5001, σ=0.0012 (10,000 iter)",
        ]:
            lbl = QLabel(line)
            lbl.setStyleSheet(
                f"font-family: 'JetBrains Mono', Consolas, monospace; font-size: 9pt;"
            )
            results_layout.addWidget(lbl)
        right_layout.addWidget(results_group)
        right_layout.addStretch()

        splitter.addWidget(right_panel)
        splitter.setSizes([500, 300])
        main_layout.addWidget(splitter)

        # --- Visualization canvas ---
        canvas = PlaceholderVisualizationCanvas()
        main_layout.addWidget(canvas)

    def sizeHint(self) -> QSize:
        return QSize(1024, 768)


# ---------------------------------------------------------------------------
# Helper functions for external callers
# ---------------------------------------------------------------------------


def render_visualization_canvas(
    output_dir: str = "tests/renders",
    size: tuple[int, int] = (700, 300),
) -> str:
    """Render the placeholder VisualizationCanvas to PNG.

    Args:
        output_dir: Directory for output PNG.
        size: Widget size as (width, height).

    Returns:
        Path to the rendered PNG file.
    """
    filepath = os.path.join(output_dir, "visualization_canvas.png")
    canvas = PlaceholderVisualizationCanvas()
    render_widget_to_png(canvas, filepath, size=size)
    return filepath


def render_main_window(
    output_dir: str = "tests/renders",
    size: tuple[int, int] = (1024, 768),
) -> str:
    """Render the full MainWindow layout to PNG for layout review.

    Args:
        output_dir: Directory for output PNG.
        size: Widget size as (width, height).

    Returns:
        Path to the rendered PNG file.
    """
    filepath = os.path.join(output_dir, "main_window.png")
    window = PlaceholderMainWindow()
    render_widget_to_png(window, filepath, size=size)
    return filepath


# ---------------------------------------------------------------------------
# Main script — runnable via `python tests/render_harness.py`
# ---------------------------------------------------------------------------


def main() -> None:
    """Generate all test renders and print output paths."""
    app = QApplication.instance() or QApplication(sys.argv)

    # Determine output directory (relative to project root)
    script_dir = Path(__file__).resolve().parent
    output_dir = str(script_dir / "renders")
    os.makedirs(output_dir, exist_ok=True)

    print("=" * 60)
    print("Tolerance Analysis Tool — Offscreen Render Harness")
    print("=" * 60)
    print()

    rendered_files: list[str] = []

    # 1. Render the visualization canvas
    path = render_visualization_canvas(output_dir)
    rendered_files.append(path)

    # 2. Render the full main window layout
    path = render_main_window(output_dir)
    rendered_files.append(path)

    print()
    print("All renders complete. Output files:")
    for f in rendered_files:
        print(f"  {f}")
    print()


if __name__ == "__main__":
    main()
