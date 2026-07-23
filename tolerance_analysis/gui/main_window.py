"""Main application window shell for the Tolerance Analysis Tool.

Provides the top-level QMainWindow with menu bar, toolbar, and central
layout using splitters. Integrates unit system selector, standard mode
selector, and connects to AnalysisController for all operations.

Validates: Requirements 6.4, 8.1, 9.1, 12.4, 12.5
"""

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QAction,
    QComboBox,
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QMenuBar,
    QMessageBox,
    QSplitter,
    QToolBar,
    QVBoxLayout,
    QWidget,
)

from tolerance_analysis.boundary.controller import AnalysisController
from tolerance_analysis.boundary.standards import StandardMode
from tolerance_analysis.boundary.unit_converter import UnitConverter, UnitSystem
from tolerance_analysis.gui.chain_tab import ChainTab
from tolerance_analysis.gui.detail_panel import DetailPanel
from tolerance_analysis.gui.dialogs import NewChainDialog, ResultsSummaryDialog
from tolerance_analysis.gui.help_panel import HelpPanel
from tolerance_analysis.gui.results_panel import ResultsPanel
from tolerance_analysis.gui.theme import STYLESHEET
from tolerance_analysis.gui.visualization import VisualizationCanvas
from tolerance_analysis.gui.viz_debug_dock import VizDebugDock


class MainWindow(QMainWindow):
    """Application main window shell.

    Hosts menu bar, toolbar, and central layout with real interactive panels
    for contributor table, detail panel, visualization canvas, and results.
    """

    def __init__(self, controller: AnalysisController | None = None) -> None:
        """Initialize the main window.

        Args:
            controller: Optional AnalysisController instance. If None,
                a new default controller is created.
        """
        super().__init__()

        self.controller = controller if controller is not None else AnalysisController()

        self.setWindowTitle("Tolerance Analysis Tool")
        self.setMinimumSize(1024, 768)
        self.setStyleSheet(STYLESHEET)

        # --- Real widget panels ---
        self._chain_tab = ChainTab(self.controller)
        self._detail_panel = DetailPanel()
        self._visualization = VisualizationCanvas()
        self._results_panel = ResultsPanel()
        self._debug_dock: VizDebugDock | None = None

        # --- Build UI ---
        self._setup_menu_bar()
        self._setup_toolbar()
        self._setup_central_layout()
        self._connect_signals()

    # ------------------------------------------------------------------
    # UI Construction
    # ------------------------------------------------------------------

    def _setup_menu_bar(self) -> None:
        """Create the application menu bar with File, Edit, Analysis, Help."""
        menu_bar: QMenuBar = self.menuBar()

        # --- File menu ---
        file_menu = menu_bar.addMenu("&File")

        self.action_new = QAction("&New Project", self)
        self.action_new.setShortcut("Ctrl+N")
        self.action_new.triggered.connect(self._on_new_project)
        file_menu.addAction(self.action_new)

        self.action_open = QAction("&Open...", self)
        self.action_open.setShortcut("Ctrl+O")
        self.action_open.triggered.connect(self._on_open_project)
        file_menu.addAction(self.action_open)

        file_menu.addSeparator()

        self.action_save = QAction("&Save", self)
        self.action_save.setShortcut("Ctrl+S")
        self.action_save.triggered.connect(self._on_save_project)
        file_menu.addAction(self.action_save)

        self.action_save_as = QAction("Save &As...", self)
        self.action_save_as.setShortcut("Ctrl+Shift+S")
        self.action_save_as.triggered.connect(self._on_save_as)
        file_menu.addAction(self.action_save_as)

        file_menu.addSeparator()

        self.action_export_pdf = QAction("&Export PDF...", self)
        self.action_export_pdf.triggered.connect(self._on_export_pdf)
        file_menu.addAction(self.action_export_pdf)

        file_menu.addSeparator()

        self.action_exit = QAction("E&xit", self)
        self.action_exit.setShortcut("Alt+F4")
        self.action_exit.triggered.connect(self.close)
        file_menu.addAction(self.action_exit)

        # --- Edit menu ---
        edit_menu = menu_bar.addMenu("&Edit")

        self.action_add_chain = QAction("Add &Chain", self)
        self.action_add_chain.triggered.connect(self._on_add_chain)
        edit_menu.addAction(self.action_add_chain)

        self.action_add_contributor = QAction("Add C&ontributor", self)
        self.action_add_contributor.triggered.connect(self._on_add_contributor)
        edit_menu.addAction(self.action_add_contributor)

        # --- Analysis menu ---
        analysis_menu = menu_bar.addMenu("&Analysis")

        self.action_run_worst_case = QAction("Run &Worst-Case", self)
        self.action_run_worst_case.triggered.connect(self._on_run_worst_case)
        analysis_menu.addAction(self.action_run_worst_case)

        self.action_run_rss = QAction("Run &RSS", self)
        self.action_run_rss.triggered.connect(self._on_run_rss)
        analysis_menu.addAction(self.action_run_rss)

        self.action_run_monte_carlo = QAction("Run &Monte Carlo", self)
        self.action_run_monte_carlo.triggered.connect(self._on_run_monte_carlo)
        analysis_menu.addAction(self.action_run_monte_carlo)

        # --- Help menu ---
        help_menu = menu_bar.addMenu("&Help")

        self.action_help_topics = QAction("Help &Topics", self)
        self.action_help_topics.triggered.connect(self._on_help_topics)
        help_menu.addAction(self.action_help_topics)

        help_menu.addSeparator()

        self.action_debug_viz = QAction("Toggle &Viz Debug Dock", self)
        self.action_debug_viz.triggered.connect(self._on_toggle_debug_dock)
        help_menu.addAction(self.action_debug_viz)

        help_menu.addSeparator()

        self.action_about = QAction("&About", self)
        self.action_about.triggered.connect(self._on_about)
        help_menu.addAction(self.action_about)

    def _setup_toolbar(self) -> None:
        """Create the toolbar with unit system and standard mode selectors."""
        toolbar: QToolBar = self.addToolBar("Main")
        toolbar.setMovable(False)
        toolbar.setObjectName("MainToolbar")

        # --- Unit system selector ---
        toolbar.addWidget(QLabel(" Units: "))
        self.unit_combo = QComboBox()
        self.unit_combo.addItem("Inch", UnitSystem.INCH)
        self.unit_combo.addItem("mm", UnitSystem.MILLIMETER)
        self.unit_combo.setToolTip("Select unit system (inch or millimeter)")
        self.unit_combo.currentIndexChanged.connect(self._on_unit_changed)
        toolbar.addWidget(self.unit_combo)

        toolbar.addSeparator()

        # --- Standard mode selector ---
        toolbar.addWidget(QLabel(" Standard: "))
        self.standard_combo = QComboBox()
        self.standard_combo.addItem("Generic", StandardMode.GENERIC)
        self.standard_combo.addItem("ASME Y14.5", StandardMode.ASME)
        self.standard_combo.addItem("ISO GPS", StandardMode.ISO)
        self.standard_combo.setToolTip("Select GD&T standard mode")
        self.standard_combo.currentIndexChanged.connect(self._on_standard_changed)
        toolbar.addWidget(self.standard_combo)

        toolbar.addSeparator()

        # --- Analysis buttons ---
        self.action_toolbar_worst_case = toolbar.addAction("Worst-Case")
        self.action_toolbar_worst_case.setToolTip("Run worst-case analysis")
        self.action_toolbar_worst_case.triggered.connect(self._on_run_worst_case)

        self.action_toolbar_rss = toolbar.addAction("RSS")
        self.action_toolbar_rss.setToolTip("Run RSS analysis")
        self.action_toolbar_rss.triggered.connect(self._on_run_rss)

        self.action_toolbar_monte_carlo = toolbar.addAction("Monte Carlo")
        self.action_toolbar_monte_carlo.setToolTip("Run Monte Carlo simulation")
        self.action_toolbar_monte_carlo.triggered.connect(self._on_run_monte_carlo)

    def _setup_central_layout(self) -> None:
        """Set up the central widget with QSplitter-based layout.

        Layout:
            Left side: chain_tab (top) + detail_panel (bottom)
            Right side: visualization (top) + results_panel (bottom)
        """
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(4, 4, 4, 4)

        # Horizontal splitter: left | right
        self.main_splitter = QSplitter(Qt.Horizontal)

        # Left vertical splitter: chain_tab / detail_panel
        self.left_splitter = QSplitter(Qt.Vertical)
        self.left_splitter.addWidget(self._chain_tab)
        self.left_splitter.addWidget(self._detail_panel)
        self.left_splitter.setStretchFactor(0, 3)
        self.left_splitter.setStretchFactor(1, 1)

        # Right vertical splitter: visualization / results_panel
        self.right_splitter = QSplitter(Qt.Vertical)
        self.right_splitter.addWidget(self._visualization)
        self.right_splitter.addWidget(self._results_panel)
        self.right_splitter.setStretchFactor(0, 2)
        self.right_splitter.setStretchFactor(1, 1)

        self.main_splitter.addWidget(self.left_splitter)
        self.main_splitter.addWidget(self.right_splitter)
        self.main_splitter.setStretchFactor(0, 3)
        self.main_splitter.setStretchFactor(1, 2)

        main_layout.addWidget(self.main_splitter)

    def _connect_signals(self) -> None:
        """Wire cross-widget signals for interactivity."""
        # ChainTab → DetailPanel: show selected contributor details
        self._chain_tab.contributor_selected.connect(self._on_contributor_selected)

        # ChainTab → auto-rerun analyses and refresh display when chain data changes
        self._chain_tab.chain_changed.connect(self._on_chain_data_changed)

        # DetailPanel → Controller: update contributor properties
        self._detail_panel.distribution_changed.connect(self._on_distribution_changed)
        self._detail_panel.notes_changed.connect(self._on_notes_changed)
        self._detail_panel.material_changed.connect(self._on_material_changed)

    # ------------------------------------------------------------------
    # Signal Handlers — Cross-widget wiring
    # ------------------------------------------------------------------

    def _on_chain_data_changed(self) -> None:
        """Auto-rerun any previously-computed analyses when chain data changes.

        This fires when the user edits a cell in the contributor table,
        adds/removes a contributor, or reorders the chain. It silently
        reruns whichever analyses were already computed so the visualization
        and results stay in sync without requiring the user to re-click
        analysis buttons.
        """
        chain_id = self._get_active_chain_id()
        if chain_id is None:
            self._refresh_visualization()
            return

        results = self.controller.get_results(chain_id)
        if results is not None:
            # Re-run whichever analyses were previously computed
            if results.worst_case is not None:
                self.controller.run_worst_case(chain_id)
            if results.rss is not None:
                self.controller.run_rss(chain_id)
            if results.monte_carlo is not None:
                iterations = results.monte_carlo.num_iterations
                self.controller.run_monte_carlo(chain_id, iterations=iterations)

        self._refresh_visualization()
        self._refresh_results()

    def _on_contributor_selected(self, contributor_id: str) -> None:
        """Look up the contributor and display in the detail panel."""
        chain_id = self._get_active_chain_id()
        if chain_id is None:
            return
        chain = self.controller.get_chain(chain_id)
        if chain is None:
            return
        for contrib in chain.contributors:
            if contrib.id == contributor_id:
                self._detail_panel.set_contributor(contrib)
                return
        self._detail_panel.clear()

    def _on_distribution_changed(self, contributor_id: str, dist_value: str) -> None:
        """Update a contributor's distribution type and auto-rerun analyses."""
        chain_id = self._get_active_chain_id()
        if chain_id is None:
            return
        chain = self.controller.get_chain(chain_id)
        if chain is None:
            return
        from tolerance_analysis.engine.models import DistributionType

        for contrib in chain.contributors:
            if contrib.id == contributor_id:
                try:
                    contrib.distribution = DistributionType(dist_value)
                except ValueError:
                    pass
                break
        self._on_chain_data_changed()

    def _on_notes_changed(self, contributor_id: str, notes: str) -> None:
        """Update a contributor's notes field."""
        chain_id = self._get_active_chain_id()
        if chain_id is None:
            return
        chain = self.controller.get_chain(chain_id)
        if chain is None:
            return
        for contrib in chain.contributors:
            if contrib.id == contributor_id:
                contrib.notes = notes
                break

    def _on_material_changed(self, contributor_id: str, material: str) -> None:
        """Update a contributor's material field."""
        chain_id = self._get_active_chain_id()
        if chain_id is None:
            return
        chain = self.controller.get_chain(chain_id)
        if chain is None:
            return
        for contrib in chain.contributors:
            if contrib.id == contributor_id:
                contrib.material = material
                break

    # ------------------------------------------------------------------
    # Refresh Helpers
    # ------------------------------------------------------------------

    def _refresh_visualization(self) -> None:
        """Refresh the visualization canvas with the active chain and results."""
        chain_id = self._get_active_chain_id()
        if chain_id is None:
            return
        chain = self.controller.get_chain(chain_id)
        if chain is None:
            return
        results = self.controller.get_results(chain_id)
        self._visualization.set_chain(chain, results)

    def _refresh_results(self) -> None:
        """Refresh the results panel with current analysis results."""
        chain_id = self._get_active_chain_id()
        if chain_id is None:
            return
        results = self.controller.get_results(chain_id)
        if results is not None:
            self._results_panel.set_results(results, self.controller.unit_system)

    # ------------------------------------------------------------------
    # Slots — File Operations
    # ------------------------------------------------------------------

    def _on_new_project(self) -> None:
        """Create a new empty project, resetting the controller state."""
        self.controller.project.tolerance_chains.clear()
        self.controller.project.name = "Untitled Project"
        self.controller.project.filepath = None
        self.setWindowTitle("Tolerance Analysis Tool — Untitled Project")
        self._detail_panel.clear()
        self._refresh_visualization()
        self._refresh_results()

    def _on_open_project(self) -> None:
        """Open a project file via file dialog."""
        filepath, _ = QFileDialog.getOpenFileName(
            self, "Open Project", "", "Tolerance Project (*.json);;All Files (*)"
        )
        if filepath:
            error = self.controller.load_project(filepath)
            if error:
                QMessageBox.critical(self, "Open Error", error)
            else:
                self.setWindowTitle(
                    f"Tolerance Analysis Tool — {self.controller.project.name}"
                )
                self._chain_tab._refresh_chain_selector()
                self._refresh_visualization()
                self._refresh_results()

    def _on_save_project(self) -> None:
        """Save the current project. Prompts for path if none set."""
        filepath = self.controller.project.filepath
        if not filepath:
            self._on_save_as()
            return
        error = self.controller.save_project(filepath)
        if error:
            QMessageBox.critical(self, "Save Error", error)

    def _on_save_as(self) -> None:
        """Save the project to a new file path."""
        filepath, _ = QFileDialog.getSaveFileName(
            self, "Save Project As", "", "Tolerance Project (*.json);;All Files (*)"
        )
        if filepath:
            error = self.controller.save_project(filepath)
            if error:
                QMessageBox.critical(self, "Save Error", error)
            else:
                self.setWindowTitle(
                    f"Tolerance Analysis Tool — {self.controller.project.name}"
                )

    def _on_export_pdf(self) -> None:
        """Export the current analysis results as a PDF report."""
        filepath, _ = QFileDialog.getSaveFileName(
            self, "Export PDF Report", "", "PDF Files (*.pdf);;All Files (*)"
        )
        if filepath:
            error = self.controller.export_pdf(filepath)
            if error:
                QMessageBox.critical(self, "Export Error", error)

    # ------------------------------------------------------------------
    # Slots — Edit Operations
    # ------------------------------------------------------------------

    def _on_add_chain(self) -> None:
        """Add a new tolerance chain via the NewChainDialog."""
        result = NewChainDialog.get_new_chain(self)
        if result is not None:
            name, description = result
            chain_id = self.controller.create_chain(name, description)
            if chain_id is None:
                QMessageBox.warning(
                    self,
                    "Add Chain",
                    "Could not create chain (name may be duplicate).",
                )
            else:
                # Refresh the chain tab to show the new chain
                self._chain_tab._refresh_chain_selector()

    def _on_add_contributor(self) -> None:
        """Add a contributor to the active chain via the chain tab."""
        self._chain_tab._on_add_contributor()

    # ------------------------------------------------------------------
    # Slots — Analysis Operations
    # ------------------------------------------------------------------

    def _on_run_worst_case(self) -> None:
        """Run worst-case analysis on the active chain."""
        chain_id = self._get_active_chain_id()
        if chain_id is None:
            QMessageBox.information(
                self, "Analysis", "No active tolerance chain selected."
            )
            return
        result = self.controller.run_worst_case(chain_id)
        if isinstance(result, str):
            QMessageBox.warning(self, "Worst-Case Analysis", result)
        else:
            self._refresh_visualization()
            self._refresh_results()
            chain = self.controller.get_chain(chain_id)
            chain_name = chain.name if chain else "Unknown"
            results = self.controller.get_results(chain_id)
            self._show_results_summary(chain_name, results, self.controller.unit_system)

    def _on_run_rss(self) -> None:
        """Run RSS analysis on the active chain."""
        chain_id = self._get_active_chain_id()
        if chain_id is None:
            QMessageBox.information(
                self, "Analysis", "No active tolerance chain selected."
            )
            return
        result = self.controller.run_rss(chain_id)
        if isinstance(result, str):
            QMessageBox.warning(self, "RSS Analysis", result)
        else:
            self._refresh_visualization()
            self._refresh_results()
            chain = self.controller.get_chain(chain_id)
            chain_name = chain.name if chain else "Unknown"
            results = self.controller.get_results(chain_id)
            self._show_results_summary(chain_name, results, self.controller.unit_system)

    def _on_run_monte_carlo(self) -> None:
        """Run Monte Carlo simulation on the active chain."""
        chain_id = self._get_active_chain_id()
        if chain_id is None:
            QMessageBox.information(
                self, "Analysis", "No active tolerance chain selected."
            )
            return
        result = self.controller.run_monte_carlo(chain_id, iterations=10_000)
        if isinstance(result, str):
            QMessageBox.warning(self, "Monte Carlo Simulation", result)
        else:
            self._refresh_visualization()
            self._refresh_results()
            chain = self.controller.get_chain(chain_id)
            chain_name = chain.name if chain else "Unknown"
            results = self.controller.get_results(chain_id)
            self._show_results_summary(chain_name, results, self.controller.unit_system)

    # ------------------------------------------------------------------
    # Slots — Toolbar Selectors
    # ------------------------------------------------------------------

    def _on_unit_changed(self, index: int) -> None:
        """Handle unit system combo box change."""
        new_unit = self.unit_combo.itemData(index)
        if new_unit is not None:
            self.controller.change_unit_system(new_unit)
            self._refresh_visualization()
            self._refresh_results()

    def _on_standard_changed(self, index: int) -> None:
        """Handle standard mode combo box change."""
        new_mode = self.standard_combo.itemData(index)
        if new_mode is not None:
            self.controller.change_standard_mode(new_mode)

    # ------------------------------------------------------------------
    # Slots — Help
    # ------------------------------------------------------------------

    def _on_help_topics(self) -> None:
        """Show the HelpPanel dialog."""
        help_dialog = HelpPanel(self)
        help_dialog.show()

    def _on_toggle_debug_dock(self) -> None:
        """Toggle the visualization debug dock panel."""
        if self._debug_dock is None:
            self._debug_dock = VizDebugDock(self._visualization, self)
            self.addDockWidget(Qt.RightDockWidgetArea, self._debug_dock)
        else:
            if self._debug_dock.isVisible():
                self._debug_dock.hide()
            else:
                self._debug_dock.show()

    def _on_about(self) -> None:
        """Show about dialog."""
        QMessageBox.about(
            self,
            "About Tolerance Analysis Tool",
            "Tolerance Analysis Tool v1.0\n\n"
            "Worst-case, RSS, and Monte Carlo tolerance stack-up analysis\n"
            "for mechanical engineering applications.\n\n"
            "Built with PyQt5.",
        )

    # ------------------------------------------------------------------
    # Results Summary Dialog
    # ------------------------------------------------------------------

    def _show_results_summary(self, chain_name: str, results, unit_system) -> None:
        """Show a plain-language results summary dialog after analysis.

        Includes engineering warnings when potential issues are detected.

        Args:
            chain_name: Name of the analyzed tolerance chain.
            results: AnalysisResults object with the computed results.
            unit_system: The active UnitSystem for formatting values.
        """
        if results is None:
            return

        from tolerance_analysis.engine.warnings import evaluate_warnings, WarningSeverity

        converter = UnitConverter()
        unit = '"' if unit_system == UnitSystem.INCH else "mm"

        def fmt(value: float) -> str:
            return converter.format_value(value, unit_system)

        message = f"Stack-Up Results: {chain_name}\n\n"

        # RSS result (includes worst-case comparison)
        if results.rss is not None:
            rss = results.rss
            wc = rss.worst_case
            message += f"Nominal gap: {fmt(rss.nominal)} {unit}\n\n"
            message += f"Worst-Case (100% coverage):\n"
            message += f"  Range: {fmt(wc.minimum)} {unit} to {fmt(wc.maximum)} {unit} (band: {fmt(wc.tolerance_band)} {unit})\n\n"
            message += f"RSS Statistical (\u224899.73% coverage):\n"
            message += f"  Range: {fmt(rss.statistical_minimum)} {unit} to {fmt(rss.statistical_maximum)} {unit} (band: {fmt(rss.statistical_band)} {unit})\n\n"
            message += (
                "The RSS range is tighter because it's statistically unlikely that all\n"
                "dimensions will be at their extremes simultaneously. Approximately\n"
                "99.73% of assemblies will fall within the RSS range assuming normal\n"
                "manufacturing processes."
            )

        # Worst-case only (no RSS)
        elif results.worst_case is not None:
            wc = results.worst_case
            message += f"Nominal gap: {fmt(wc.nominal)} {unit}\n"
            message += f"Worst-case range: {fmt(wc.minimum)} {unit} to {fmt(wc.maximum)} {unit}\n"
            message += f"Total tolerance band: {fmt(wc.tolerance_band)} {unit}\n\n"
            message += (
                f"This means the gap could be as small as {fmt(wc.minimum)} {unit} or as large as\n"
                f"{fmt(wc.maximum)} {unit} if all contributors simultaneously hit their worst limits.\n"
                "This is the most conservative estimate."
            )

        # Monte Carlo result
        if results.monte_carlo is not None:
            mc = results.monte_carlo
            if results.rss is not None or results.worst_case is not None:
                message += "\n\n" + "\u2500" * 40 + "\n\n"
            message += f"Monte Carlo Simulation ({mc.num_iterations:,} iterations):\n"
            message += f"  Mean gap: {fmt(mc.mean)} {unit}\n"
            message += f"  Std deviation: {fmt(mc.std_dev)} {unit}\n"
            message += f"  Observed range: {fmt(mc.minimum)} {unit} to {fmt(mc.maximum)} {unit}\n\n"

            plus_3sigma = mc.mean + 3 * mc.std_dev
            minus_3sigma = mc.mean - 3 * mc.std_dev
            plus_2sigma = mc.mean + 2 * mc.std_dev
            minus_2sigma = mc.mean - 2 * mc.std_dev

            message += f"  99.73% of assemblies (\u00b13\u03c3): {fmt(minus_3sigma)} {unit} to {fmt(plus_3sigma)} {unit}\n"
            message += f"  95.45% of assemblies (\u00b12\u03c3): {fmt(minus_2sigma)} {unit} to {fmt(plus_2sigma)} {unit}\n\n"
            message += (
                "This simulation randomly sampled each contributor from its specified\n"
                "distribution (normal, uniform, or triangular) to predict the actual\n"
                "assembly variation."
            )

        # --- Engineering Warnings ---
        chain_id = self._get_active_chain_id()
        chain = self.controller.get_chain(chain_id) if chain_id else None
        warnings = evaluate_warnings(chain, results) if chain else []

        if warnings:
            message += "\n\n" + "=" * 40 + "\n"
            message += "\u26a0  ENGINEERING WARNINGS\n"
            message += "=" * 40 + "\n\n"

            for w in warnings:
                severity_icon = {
                    WarningSeverity.CRITICAL: "\u274c CRITICAL",
                    WarningSeverity.CAUTION: "\u26a0\ufe0f  CAUTION",
                    WarningSeverity.INFO: "\u2139\ufe0f  INFO",
                }
                message += f"{severity_icon[w.severity]}: {w.title}\n"
                message += f"  {w.message}\n"
                if w.detail:
                    message += f"  \u2192 {w.detail}\n"
                message += "\n"

        # Choose dialog type based on warning severity
        has_critical = any(w.severity == WarningSeverity.CRITICAL for w in warnings)

        ResultsSummaryDialog.show_results(
            self,
            f"Analysis Results \u2014 {chain_name}",
            message,
            has_critical=has_critical,
        )

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _get_active_chain_id(self) -> str | None:
        """Return the ID of the currently active chain, or None.

        Uses the ChainTab's current chain selection if available,
        otherwise falls back to the first chain.
        """
        # Prefer the chain tab's current selection
        if hasattr(self._chain_tab, '_current_chain_id') and self._chain_tab._current_chain_id:
            return self._chain_tab._current_chain_id
        # Fallback: first chain in the project
        if self.controller.project.tolerance_chains:
            return self.controller.project.tolerance_chains[0].id
        return None
