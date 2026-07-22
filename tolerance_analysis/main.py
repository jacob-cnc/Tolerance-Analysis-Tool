"""Application entry point for the Tolerance Analysis Tool.

Creates the QApplication, applies the global stylesheet, initializes the
controller, creates the main window, and enters the event loop.

Validates: Requirements 6.4, 8.1, 8.5, 8.6, 8.7, 9.6, 9.7, 9.8
"""

import sys

from PyQt5.QtWidgets import QApplication, QMessageBox

from tolerance_analysis.boundary.controller import AnalysisController
from tolerance_analysis.boundary.standards import StandardMode
from tolerance_analysis.boundary.unit_converter import UnitSystem
from tolerance_analysis.gui.main_window import MainWindow
from tolerance_analysis.gui.theme import STYLESHEET


def main() -> int:
    """Launch the Tolerance Analysis Tool application.

    Accepts an optional command-line argument specifying a project file to
    load on startup. If provided, the file is loaded and the unit system and
    standard mode are restored from it (defaulting to INCH and GENERIC if
    missing).

    Returns:
        Exit code from the Qt event loop.
    """
    app = QApplication(sys.argv)
    app.setApplicationName("Tolerance Analysis Tool")
    app.setApplicationVersion("0.1.0")
    app.setStyleSheet(STYLESHEET)

    controller = AnalysisController()
    window = MainWindow(controller)

    # Handle optional project file argument
    if len(sys.argv) > 1:
        filepath = sys.argv[1]
        error = controller.load_project(filepath)
        if error:
            QMessageBox.critical(
                window, "Load Error", f"Failed to load project:\n{error}"
            )
        else:
            # Restore unit system from loaded project (default to INCH if missing)
            _restore_unit_system(controller, window)
            # Restore standard mode from loaded project (default to GENERIC if missing)
            _restore_standard_mode(controller, window)
            # Update window title with project name
            window.setWindowTitle(
                f"Tolerance Analysis Tool \u2014 {controller.project.name}"
            )

    window.show()
    return app.exec_()


def _restore_unit_system(controller: AnalysisController, window: MainWindow) -> None:
    """Restore unit system from loaded project state.

    If the project has no stored unit system or it is unrecognized, defaults
    to INCH and shows a notification to the user.
    """
    project_unit = getattr(controller.project, "unit_system", None)

    resolved_unit: UnitSystem | None = None

    if project_unit is None or project_unit == "":
        resolved_unit = None
    elif isinstance(project_unit, UnitSystem):
        resolved_unit = project_unit
    elif isinstance(project_unit, str):
        # Try to match the string value to a UnitSystem enum
        try:
            resolved_unit = UnitSystem(project_unit)
        except ValueError:
            resolved_unit = None

    if resolved_unit is None:
        # Default to INCH and notify user
        controller.unit_system = UnitSystem.INCH
        controller.project.unit_system = UnitSystem.INCH.value
        QMessageBox.information(
            window,
            "Unit System",
            "No unit system found in project file. Defaulting to Inch.",
        )
    else:
        controller.unit_system = resolved_unit

    # Sync the toolbar combo box to match the restored unit
    _sync_unit_combo(window, controller.unit_system)


def _restore_standard_mode(
    controller: AnalysisController, window: MainWindow
) -> None:
    """Restore standard mode from loaded project state.

    If the project has no stored standard mode or it is unrecognized, defaults
    to GENERIC.
    """
    project_mode = getattr(controller.project, "standard_mode", None)

    resolved_mode: StandardMode | None = None

    if project_mode is None or project_mode == "":
        resolved_mode = None
    elif isinstance(project_mode, StandardMode):
        resolved_mode = project_mode
    elif isinstance(project_mode, str):
        # Try to match the string value to a StandardMode enum
        try:
            resolved_mode = StandardMode(project_mode)
        except ValueError:
            resolved_mode = None

    if resolved_mode is None:
        # Default to GENERIC
        controller.standard_mode = StandardMode.GENERIC
        controller.project.standard_mode = StandardMode.GENERIC.value
    else:
        controller.standard_mode = resolved_mode

    # Sync the toolbar combo box to match the restored mode
    _sync_standard_combo(window, controller.standard_mode)


def _sync_unit_combo(window: MainWindow, unit: UnitSystem) -> None:
    """Sync the unit system combo box in the toolbar without triggering signals."""
    combo = window.unit_combo
    combo.blockSignals(True)
    for i in range(combo.count()):
        if combo.itemData(i) == unit:
            combo.setCurrentIndex(i)
            break
    combo.blockSignals(False)


def _sync_standard_combo(window: MainWindow, mode: StandardMode) -> None:
    """Sync the standard mode combo box in the toolbar without triggering signals."""
    combo = window.standard_combo
    combo.blockSignals(True)
    for i in range(combo.count()):
        if combo.itemData(i) == mode:
            combo.setCurrentIndex(i)
            break
    combo.blockSignals(False)


if __name__ == "__main__":
    sys.exit(main())
