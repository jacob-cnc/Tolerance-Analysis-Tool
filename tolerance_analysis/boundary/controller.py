"""Analysis orchestration controller for the tolerance analysis tool.

Central orchestrator between the GUI and engine layers. Manages application
state including the current project, active tolerance chains, analysis results,
and unit/standard mode settings. Handles unit conversion at the boundary.

Validates: Requirements 1.5, 1.6, 1.7, 2.6, 3.5, 4.7, 8.3
"""

from datetime import datetime
from typing import Optional

from tolerance_analysis.boundary.standards import StandardMode, StandardsManager
from tolerance_analysis.boundary.unit_converter import UnitConverter, UnitSystem
from tolerance_analysis.engine.models import (
    AnalysisResults,
    Contributor,
    MonteCarloResult,
    Project,
    RSSResult,
    ToleranceChain,
    WorstCaseResult,
)
from tolerance_analysis.engine.monte_carlo import MonteCarloSimulator
from tolerance_analysis.engine.rss import RSSAnalyzer
from tolerance_analysis.engine.validator import Validator
from tolerance_analysis.engine.worst_case import WorstCaseAnalyzer


class AnalysisController:
    """Central orchestrator between GUI and engine.

    Manages application state: current project, active chains, results.
    Handles unit conversion at the boundary.
    """

    def __init__(self) -> None:
        """Initialize the controller with default project and analyzers."""
        self.project = Project(name="Untitled Project")
        self.unit_system = UnitSystem.INCH
        self.standard_mode = StandardMode.GENERIC
        self.worst_case_analyzer = WorstCaseAnalyzer()
        self.rss_analyzer = RSSAnalyzer()
        self.monte_carlo = MonteCarloSimulator()
        self.validator = Validator()
        self.unit_converter = UnitConverter()
        self.standards_manager = StandardsManager()

        # Analysis results keyed by chain ID
        self._results: dict[str, AnalysisResults] = {}

    # --- Chain Management ---

    def create_chain(self, name: str, description: str = "") -> Optional[str]:
        """Create a new tolerance chain and add it to the project.

        Args:
            name: Name for the chain (1-100 characters).
            description: Optional description (0-500 characters).

        Returns:
            The chain ID if created successfully, or None if validation fails.
        """
        existing_names = [c.name for c in self.project.tolerance_chains]
        errors = self.validator.validate_chain_name(name, existing_names)
        if errors:
            return None

        chain = ToleranceChain(name=name, description=description)
        self.project.tolerance_chains.append(chain)
        self._results[chain.id] = AnalysisResults()
        self.project.modified = datetime.now()
        return chain.id

    def delete_chain(self, chain_id: str) -> bool:
        """Delete a tolerance chain from the project.

        Args:
            chain_id: The ID of the chain to delete.

        Returns:
            True if the chain was found and deleted, False otherwise.
        """
        for i, chain in enumerate(self.project.tolerance_chains):
            if chain.id == chain_id:
                self.project.tolerance_chains.pop(i)
                self._results.pop(chain_id, None)
                self.project.modified = datetime.now()
                return True
        return False

    def get_chain(self, chain_id: str) -> Optional[ToleranceChain]:
        """Retrieve a tolerance chain by its ID.

        Args:
            chain_id: The ID of the chain to retrieve.

        Returns:
            The ToleranceChain if found, or None.
        """
        for chain in self.project.tolerance_chains:
            if chain.id == chain_id:
                return chain
        return None

    # --- Contributor Management ---

    def add_contributor(self, chain_id: str, contributor: Contributor) -> bool:
        """Validate and add a contributor to a chain.

        Args:
            chain_id: The ID of the chain to add the contributor to.
            contributor: The Contributor instance to add.

        Returns:
            True if the contributor was validated and added, False otherwise.
        """
        chain = self.get_chain(chain_id)
        if chain is None:
            return False

        errors = self.validator.validate_contributor(contributor)
        if errors:
            return False

        chain.contributors.append(contributor)
        self.project.modified = datetime.now()
        return True

    def remove_contributor(self, chain_id: str, contributor_id: str) -> bool:
        """Remove a contributor from a chain by its ID.

        Args:
            chain_id: The ID of the chain.
            contributor_id: The ID of the contributor to remove.

        Returns:
            True if the contributor was found and removed, False otherwise.
        """
        chain = self.get_chain(chain_id)
        if chain is None:
            return False

        for i, contrib in enumerate(chain.contributors):
            if contrib.id == contributor_id:
                chain.contributors.pop(i)
                self.project.modified = datetime.now()
                return True
        return False

    def reorder_contributors(self, chain_id: str, new_order: list[str]) -> None:
        """Reorder contributors in a chain by a list of IDs.

        Contributors are reordered to match the given ID sequence. Any IDs
        not found are silently ignored; contributors not in new_order are
        appended at the end in their original relative order.

        Args:
            chain_id: The ID of the chain.
            new_order: List of contributor IDs defining the new order.
        """
        chain = self.get_chain(chain_id)
        if chain is None:
            return

        # Build lookup of contributors by ID
        contrib_map = {c.id: c for c in chain.contributors}

        reordered: list[Contributor] = []
        seen: set[str] = set()

        # Place contributors in the requested order
        for cid in new_order:
            if cid in contrib_map and cid not in seen:
                reordered.append(contrib_map[cid])
                seen.add(cid)

        # Append any remaining contributors not in new_order
        for contrib in chain.contributors:
            if contrib.id not in seen:
                reordered.append(contrib)

        chain.contributors = reordered
        self.project.modified = datetime.now()

    # --- Analysis Methods ---

    def run_worst_case(self, chain_id: str) -> WorstCaseResult | str:
        """Validate then run worst-case analysis on a chain.

        Args:
            chain_id: The ID of the chain to analyze.

        Returns:
            WorstCaseResult on success, or an error message string.
        """
        chain = self.get_chain(chain_id)
        if chain is None:
            return f"Chain '{chain_id}' not found."

        if len(chain.contributors) < 2:
            return "Worst-case analysis requires at least 2 contributors."

        try:
            result = self.worst_case_analyzer.analyze(chain)
        except (ValueError, Exception) as e:
            return str(e)

        # Store result
        if chain_id not in self._results:
            self._results[chain_id] = AnalysisResults()
        self._results[chain_id].worst_case = result
        self.project.modified = datetime.now()
        return result

    def run_rss(self, chain_id: str) -> RSSResult | str:
        """Validate then run RSS analysis on a chain.

        Args:
            chain_id: The ID of the chain to analyze.

        Returns:
            RSSResult on success, or an error message string.
        """
        chain = self.get_chain(chain_id)
        if chain is None:
            return f"Chain '{chain_id}' not found."

        if len(chain.contributors) < 2:
            return "RSS analysis requires at least 2 contributors."

        try:
            result = self.rss_analyzer.analyze(chain)
        except (ValueError, Exception) as e:
            return str(e)

        # Store result
        if chain_id not in self._results:
            self._results[chain_id] = AnalysisResults()
        self._results[chain_id].rss = result
        self.project.modified = datetime.now()
        return result

    def run_monte_carlo(self, chain_id: str, iterations: int) -> MonteCarloResult | str:
        """Validate then run Monte Carlo simulation on a chain.

        Args:
            chain_id: The ID of the chain to simulate.
            iterations: Number of iterations (1,000 to 1,000,000).

        Returns:
            MonteCarloResult on success, or an error message string.
        """
        chain = self.get_chain(chain_id)
        if chain is None:
            return f"Chain '{chain_id}' not found."

        if len(chain.contributors) < 1:
            return "Monte Carlo simulation requires at least 1 contributor."

        try:
            result = self.monte_carlo.simulate(chain, iterations=iterations)
        except (ValueError, Exception) as e:
            return str(e)

        # Store result
        if chain_id not in self._results:
            self._results[chain_id] = AnalysisResults()
        self._results[chain_id].monte_carlo = result
        self.project.modified = datetime.now()
        return result

    def get_results(self, chain_id: str) -> Optional[AnalysisResults]:
        """Get the stored analysis results for a chain.

        Args:
            chain_id: The chain ID.

        Returns:
            AnalysisResults for the chain, or None if not found.
        """
        return self._results.get(chain_id)

    # --- Unit System ---

    def change_unit_system(self, new_unit: UnitSystem) -> None:
        """Convert all dimensional data in the project to a new unit system.

        Converts every contributor in every chain using UnitConverter.
        Updates the stored unit system.

        Args:
            new_unit: The target unit system.
        """
        if new_unit == self.unit_system:
            return

        old_unit = self.unit_system

        # Convert all chains in-place
        for i, chain in enumerate(self.project.tolerance_chains):
            converted_chain = self.unit_converter.convert_chain(
                chain, from_unit=old_unit, to_unit=new_unit
            )
            self.project.tolerance_chains[i] = converted_chain

        self.unit_system = new_unit
        self.project.unit_system = new_unit.value
        self.project.modified = datetime.now()

    # --- Standard Mode ---

    def change_standard_mode(self, new_mode: StandardMode) -> None:
        """Change the active GD&T standard mode.

        This changes only the standard mode and report labels — all numeric
        data remains unchanged.

        Args:
            new_mode: The target standard mode.
        """
        self.standard_mode = new_mode
        self.project.standard_mode = new_mode.value
        self.project.modified = datetime.now()

    # --- I/O Operations (stubs — delegates to I/O layer) ---

    def save_project(self, filepath: str) -> Optional[str]:
        """Save the current project to a file.

        Delegates to io.project_file.ProjectFileManager.

        Args:
            filepath: Path where the project file should be saved.

        Returns:
            Error message string on failure, or None on success.
        """
        from tolerance_analysis.io.project_file import ProjectFileManager
        manager = ProjectFileManager()
        try:
            manager.save(self.project, filepath)
            self.project.filepath = filepath
            return None
        except Exception as e:
            return str(e)

    def load_project(self, filepath: str) -> Optional[str]:
        """Load a project from a file.

        Delegates to io.project_file.ProjectFileManager.

        Args:
            filepath: Path to the project file to load.

        Returns:
            Error message string on failure, or None on success.
        """
        from tolerance_analysis.io.project_file import ProjectFileManager
        manager = ProjectFileManager()
        try:
            self.project = manager.load(filepath)
            self.unit_system = UnitSystem(self.project.unit_system)
            self.standard_mode = StandardMode(self.project.standard_mode)
            self._results = {}
            return None
        except Exception as e:
            return str(e)

    def export_pdf(self, filepath: str) -> Optional[str]:
        """Export a PDF report of the current project/chain.

        Delegates to io.pdf_report.PDFReportGenerator.

        Args:
            filepath: Path where the PDF should be written.

        Returns:
            Error message string on failure, or None on success.
        """
        from tolerance_analysis.io.pdf_report import PDFReportGenerator
        generator = PDFReportGenerator()
        try:
            # Find the active chain (first one) and its results
            if not self.project.tolerance_chains:
                return "No tolerance chains to export."
            chain = self.project.tolerance_chains[0]
            results = self._results.get(chain.id)
            if results is None or (results.worst_case is None and results.rss is None and results.monte_carlo is None):
                return "No analysis results to export. Run an analysis first."
            generator.generate(
                project=self.project,
                chain=chain,
                results=results,
                filepath=filepath,
                standard_mode=self.standard_mode,
                unit_system=self.unit_system,
            )
            return None
        except Exception as e:
            return str(e)
