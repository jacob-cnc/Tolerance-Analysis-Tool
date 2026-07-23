"""Debug dock for live-tuning visualization layout constants.

Temporary development tool. Run the app, load a project, and use the
sliders to adjust label positioning, font sizes, bar height, etc.
Once values look right, note them down or click "Print Values" to dump
to console, then we'll bake them into visualization.py.

Remove this file before release.
"""

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QDockWidget,
    QFormLayout,
    QGroupBox,
    QLabel,
    QPushButton,
    QSlider,
    QSpinBox,
    QVBoxLayout,
    QWidget,
    QComboBox,
    QCheckBox,
)


class VizDebugDock(QDockWidget):
    """Dockable panel with sliders to live-tune VisualizationCanvas constants."""

    def __init__(self, canvas, parent=None):
        super().__init__("Viz Debug Controls", parent)
        self.setAllowedAreas(Qt.LeftDockWidgetArea | Qt.RightDockWidgetArea)
        self._canvas = canvas

        container = QWidget()
        layout = QVBoxLayout(container)

        # --- Bar Geometry ---
        bar_group = QGroupBox("Bar Geometry")
        bar_layout = QFormLayout(bar_group)

        self._bar_height = self._make_spin(20, 150, canvas._BAR_HEIGHT)
        bar_layout.addRow("Bar Height:", self._bar_height)

        self._margin_top = self._make_spin(10, 200, canvas._MARGIN_TOP)
        bar_layout.addRow("Margin Top:", self._margin_top)

        self._margin_bottom = self._make_spin(10, 200, canvas._MARGIN_BOTTOM)
        bar_layout.addRow("Margin Bottom:", self._margin_bottom)

        self._margin_left = self._make_spin(5, 100, canvas._MARGIN_LEFT)
        bar_layout.addRow("Margin Left:", self._margin_left)

        self._margin_right = self._make_spin(5, 100, canvas._MARGIN_RIGHT)
        bar_layout.addRow("Margin Right:", self._margin_right)

        self._min_bar_width = self._make_spin(2, 80, 2)
        bar_layout.addRow("Min Bar Width:", self._min_bar_width)

        layout.addWidget(bar_group)

        # --- Label Layout ---
        label_group = QGroupBox("Label Layout")
        label_layout = QFormLayout(label_group)

        self._label_font_size = self._make_spin(6, 24, 10)
        label_layout.addRow("Name Font Size:", self._label_font_size)

        self._value_font_size = self._make_spin(6, 24, 9)
        label_layout.addRow("Value Font Size:", self._value_font_size)

        self._label_y_offset = self._make_spin(0, 60, 4)
        label_layout.addRow("Label Y Offset:", self._label_y_offset)

        self._value_y_offset = self._make_spin(0, 60, 16)
        label_layout.addRow("Value Y Above Bar:", self._value_y_offset)

        self._label_max_width = self._make_spin(50, 400, 150)
        label_layout.addRow("Label Max Width:", self._label_max_width)

        self._label_mode = QComboBox()
        self._label_mode.addItems(["overflow", "clip_to_bar", "stagger", "rotate_45", "rotate_90", "hide_if_narrow"])
        label_layout.addRow("Label Mode:", self._label_mode)

        self._stagger_threshold = self._make_spin(20, 200, 80)
        label_layout.addRow("Stagger Threshold:", self._stagger_threshold)

        self._show_values = QCheckBox()
        self._show_values.setChecked(True)
        label_layout.addRow("Show Values:", self._show_values)

        layout.addWidget(label_group)

        # --- Tolerance Band ---
        tol_group = QGroupBox("Tolerance Band")
        tol_layout = QFormLayout(tol_group)

        self._tol_opacity = self._make_spin(0, 255, 77)
        tol_layout.addRow("Band Opacity (0-255):", self._tol_opacity)

        layout.addWidget(tol_group)

        # --- Result Bar ---
        result_group = QGroupBox("Result Bar")
        result_layout = QFormLayout(result_group)

        self._result_bar_height = self._make_spin(10, 60, 24)
        result_layout.addRow("Result Bar Height:", self._result_bar_height)

        self._result_font_size = self._make_spin(6, 20, 10)
        result_layout.addRow("Result Font Size:", self._result_font_size)

        self._gap = self._make_spin(2, 40, 12)
        result_layout.addRow("Gap Between Sections:", self._gap)

        layout.addWidget(result_group)

        # --- Actions ---
        btn_apply = QPushButton("Apply && Repaint")
        btn_apply.clicked.connect(self._apply)
        layout.addWidget(btn_apply)

        btn_print = QPushButton("Print Current Values to Console")
        btn_print.clicked.connect(self._print_values)
        layout.addWidget(btn_print)

        layout.addStretch()
        self.setWidget(container)

    def _make_spin(self, min_val, max_val, default):
        spin = QSpinBox()
        spin.setRange(min_val, max_val)
        spin.setValue(default)
        return spin

    def _apply(self):
        """Push all current slider values into the canvas and repaint."""
        c = self._canvas

        # Bar geometry
        c._BAR_HEIGHT = self._bar_height.value()
        c._MARGIN_TOP = self._margin_top.value()
        c._MARGIN_BOTTOM = self._margin_bottom.value()
        c._MARGIN_LEFT = self._margin_left.value()
        c._MARGIN_RIGHT = self._margin_right.value()
        c._RESULT_BAR_HEIGHT = self._result_bar_height.value()
        c._GAP = self._gap

        # Store debug overrides for paintEvent to use
        c._debug_label_font_size = self._label_font_size.value()
        c._debug_value_font_size = self._value_font_size.value()
        c._debug_label_y_offset = self._label_y_offset.value()
        c._debug_value_y_offset = self._value_y_offset.value()
        c._debug_label_max_width = self._label_max_width.value()
        c._debug_label_mode = self._label_mode.currentText()
        c._debug_stagger_threshold = self._stagger_threshold.value()
        c._debug_show_values = self._show_values.isChecked()
        c._debug_tol_opacity = self._tol_opacity.value()
        c._debug_min_bar_width = self._min_bar_width.value()
        c._debug_result_font_size = self._result_font_size.value()
        c._debug_gap = self._gap.value()

        c.update()

    def _print_values(self):
        """Print current values to console for baking into code."""
        print("\n" + "=" * 60)
        print("VISUALIZATION DEBUG VALUES - Copy these into visualization.py")
        print("=" * 60)
        print(f"    _MARGIN_TOP = {self._margin_top.value()}")
        print(f"    _MARGIN_BOTTOM = {self._margin_bottom.value()}")
        print(f"    _MARGIN_LEFT = {self._margin_left.value()}")
        print(f"    _MARGIN_RIGHT = {self._margin_right.value()}")
        print(f"    _BAR_HEIGHT = {self._bar_height.value()}")
        print(f"    _RESULT_BAR_HEIGHT = {self._result_bar_height.value()}")
        print(f"    _GAP = {self._gap.value()}")
        print(f"    _MIN_BAR_WIDTH = {self._min_bar_width.value()}")
        print(f"    # Label settings")
        print(f"    _LABEL_FONT_SIZE = {self._label_font_size.value()}")
        print(f"    _VALUE_FONT_SIZE = {self._value_font_size.value()}")
        print(f"    _LABEL_Y_OFFSET = {self._label_y_offset.value()}")
        print(f"    _VALUE_Y_OFFSET = {self._value_y_offset.value()}")
        print(f"    _LABEL_MAX_WIDTH = {self._label_max_width.value()}")
        print(f"    _LABEL_MODE = \"{self._label_mode.currentText()}\"")
        print(f"    _STAGGER_THRESHOLD = {self._stagger_threshold.value()}")
        print(f"    _SHOW_VALUES = {self._show_values.isChecked()}")
        print(f"    # Tolerance band")
        print(f"    _TOL_OPACITY = {self._tol_opacity.value()}")
        print(f"    # Result bar")
        print(f"    _RESULT_FONT_SIZE = {self._result_font_size.value()}")
        print("=" * 60 + "\n")
