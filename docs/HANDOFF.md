# Agent Handoff Document

Standardized session notes for continuity between AI coding agents working on this project.

---

## How to Use This Document

Each session adds an entry at the top of the Session Log (newest first). An incoming agent should read the **Current State** and the most recent session entry to understand where things left off.

---

## Current State

| Field | Value |
|-------|-------|
| **Phase** | Feature development — NX-style tolerance input, warnings engine complete |
| **Spec Location** | `docs/requirements.md`, `docs/design.md` |
| **Kiro Spec Mirror** | `~/.kiro/specs/tolerance-analysis-tool/` |
| **Workflow** | Requirements-first feature spec |
| **Blocked On** | Nothing — ready for help guide drafting |
| **Open Questions** | None |

---

## Project Quick Reference

| Item | Detail |
|------|--------|
| Repo | `https://github.com/jacob-cnc/Tolerance-Analysis-Tool` |
| Language | Python 3.10+ |
| GUI Framework | PyQt5 |
| Test Framework | pytest + Hypothesis (property-based) |
| Key Dependencies | numpy, reportlab, PyQt5, pytest-qt |
| Architecture | 4-layer: Engine -> Boundary -> GUI, I/O |
| Unit Default | Inches (4 decimal places) |
| Entry Point | `python -m tolerance_analysis.main` |
| Sample Project | `examples/bearing_housing_stack.json` |

---

## Conventions

- **Engine layer** is pure Python with zero GUI dependencies (only numpy for Monte Carlo)
- **Boundary layer** handles unit conversion and standards -- no Qt types cross this boundary
- **All analysis** operates on bilateral-normalized tolerance forms internally
- **Project files** are versioned JSON (schema_version: semver)
- **Property-based tests** use Hypothesis; each maps to a numbered design property (P1-P11)
- **Color palette**: dark canvas (#1a1a2e), light UI shell (#f0f0f5), semantic colors per design
- **Fonts**: Inter (UI) + JetBrains Mono (numeric/code), system fallbacks
- **Unit symbol**: Use `"` (double-quote) for inches, `mm` for millimeters in UI displays
- **Render harness**: `python tests/render_harness.py` outputs PNGs to `tests/renders/` for visual review

---

## Session Log

### Session 3 -- 2026-07-23 (Thursday)

**Objective:** Fix visualization legibility, redesign chart layout, add engineering warnings, NX-style tolerance input.

**Completed:**
1. **Opposed-bar visualization redesign** — replaced sequential bar chart with a two-row layout:
   - Positive contributors stacked on top row (blue)
   - Negative contributors stacked on bottom row (orange)
   - Both rows left-aligned; gap between endpoints is visually obvious
   - Green gap indicator for clearance, red for interference
   - Dashed vertical alignment lines connecting endpoints
2. **Label collision avoidance** — labels placed in dedicated zone below each bar row with automatic row staggering and leader lines; no overlap regardless of bar width
3. **Value collision avoidance** — values inside bars when they fit, above with multi-row staggering when they don't; clamped to canvas bounds
4. **Engineering warnings engine** (`engine/warnings.py`):
   - Detects: zero nominal clearance, worst-case interference, statistical interference probability, Monte Carlo reject rate, low Cpk, missing directions
   - Corrected RSS interference probability calculation using actual normal CDF (was incorrectly reporting 0.27% for scenarios that are actually 50%)
   - Warnings display on canvas as colored banners and in results dialog
5. **Analysis auto-rerun** — editing any contributor field automatically reruns previously computed analyses and refreshes visualization + results
6. **Scrollable results dialog** — replaced QMessageBox with `ResultsSummaryDialog` (scrollable QTextEdit) so warnings aren't cut off
7. **NX-style tolerance input widget** (`gui/tolerance_input.py`):
   - Four format buttons: ±X, +X/−Y, Limits, Fit Class
   - Fields morph based on selected format
   - ISO 286 fit class auto-lookup with deviation display
8. **ISO 286 lookup engine** (`engine/iso286.py`):
   - IT1–IT18 grades for 13 size ranges (0–500mm)
   - Hole deviations: H, G, F, E, D
   - Shaft deviations: h, g, f, e, d, c, k, m, n, p, r, s, js
   - Fit descriptions for common pairs (H7/g6, H7/h6, etc.)
9. **Simplified contributor table** — replaced Upper Tol + Lower Tol + Type columns with single formatted "Tolerance" column (e.g., "±0.0010", "+0.002/−0.001", "Lim [1.000, 1.002]")
10. **Debug dock** (`gui/viz_debug_dock.py`) — dockable panel with live sliders for tuning visualization parameters
11. **Fixed C++ object deletion crash** — guarded table refresh from occurring mid-cell-edit callback

**Known Issues:**
- Property-based tests still not written (optional tasks)
- Help guide content is placeholder — needs full rewrite with practical examples
- The VizDebugDock is a dev tool that should be removed before release (or hidden behind a flag)

**Decisions Made:**
- Opposed-bar layout is fundamentally more useful than sequential bars — makes gap/interference visually obvious
- RSS interference warning now uses actual P(gap < 0) via normal CDF rather than the misleading "0.27% outside ±3σ" approximation
- Tolerance "Type" column removed from table — type is now implicit from how the user enters values (format picker in detail panel)
- ISO 286 data stored internally in micrometers/mm, converted to inches on output
- Table tolerance column is read-only; tolerance editing happens exclusively in detail panel via the format picker

**Next Session Should:**
1. Draft a comprehensive help guide with:
   - How to set up a stack-up (choosing directions, the bore/shaft example)
   - Explanation of each analysis method (worst-case, RSS, Monte Carlo) with when to use each
   - How to interpret the visualization
   - How to use the ISO 286 fit class lookup
   - Common pitfalls (direction confusion, zero-gap scenarios)
2. Consider adding iteration count input dialog for Monte Carlo
3. Optional: write property-based tests (P1–P11)
4. Consider adding a "Fit Analysis" mode where user specifies hole + shaft fit codes and gets a full fit characterization

**File Map (updated):**
```
Tolerance-Analysis-Tool/
+-- README.md
+-- pyproject.toml
+-- docs/
|   +-- HANDOFF.md               # <- You are here
|   +-- GUIDE.md                 # User guide (needs rewrite)
|   +-- requirements.md          # Formal requirements (EARS format)
|   +-- design.md                # Technical design document
+-- examples/
|   +-- bearing_housing_stack.json
+-- tests/
|   +-- conftest.py              # Hypothesis strategies
|   +-- render_harness.py        # Offscreen PNG render utility
|   +-- renders/                 # Output PNGs
|   +-- properties/              # Property-based tests (not yet written)
|   +-- unit/
+-- tolerance_analysis/
    +-- __init__.py
    +-- main.py
    +-- engine/
    |   +-- models.py
    |   +-- converter.py
    |   +-- validator.py
    |   +-- worst_case.py
    |   +-- rss.py
    |   +-- monte_carlo.py
    |   +-- warnings.py          # NEW: Engineering warnings engine
    |   +-- iso286.py            # NEW: ISO 286 fit class lookup
    +-- boundary/
    |   +-- controller.py
    |   +-- unit_converter.py
    |   +-- standards.py
    +-- gui/
    |   +-- main_window.py
    |   +-- chain_tab.py         # Simplified: 5 columns now
    |   +-- detail_panel.py      # Now includes tolerance input widget
    |   +-- tolerance_input.py   # NEW: NX-style format picker
    |   +-- visualization.py     # Rewritten: opposed-bar layout
    |   +-- results_panel.py
    |   +-- help_panel.py
    |   +-- dialogs.py           # Added ResultsSummaryDialog
    |   +-- viz_debug_dock.py    # NEW: Dev tool for live tuning
    |   +-- theme.py
    +-- io/
    |   +-- project_file.py
    |   +-- schema.py
    |   +-- pdf_report.py
    +-- resources/
        +-- help/
        +-- icons/
```

---

### Session 2 -- 2026-07-22 (Wednesday)

**Objective:** Generate task list, implement full application, and begin UI polish.

**Completed:**
1. Generated `tasks.md` with 12 top-level tasks, 26 leaf sub-tasks, and dependency graph
2. Implemented ALL required tasks (25 non-optional):
   - Engine layer: models, converter, validator, worst-case/RSS/Monte Carlo analyzers
   - Boundary layer: unit converter, standards manager, analysis controller
   - I/O layer: JSON project file (save/load with write-ahead safety), PDF report generator
   - GUI layer: theme, main window, chain tab (contributor table), detail panel, visualization canvas, results panel, help panel, dialogs
3. Wired main window to use real widgets (initially had placeholders)
4. Connected controller I/O methods (save/load/export_pdf) to ProjectFileManager and PDFReportGenerator
5. Added offscreen render harness (`tests/render_harness.py`) for visual feedback loop
6. Created sample project: `examples/bearing_housing_stack.json` (bearing housing axial stack-up, 5 contributors)
7. Created user guide: `docs/GUIDE.md`
8. Added plain-language results summary dialog after each analysis run
9. Multiple rounds of UI legibility fixes (font sizes, column widths, splitter ratios)

**Known Issues (in progress):**
- **Visualization canvas text overlap**: When bar segments are narrow (small nominal values like 0.125"), the value text above bars and name labels below bars overlap with adjacent bars. Need a smarter label layout strategy (staggered rows, eliding, or drawing labels in a separate legend area).
- The render harness produces PNGs but Qt font fallback in offscreen mode doesn't match live rendering exactly.

**Not Started:**
- Optional property-based test tasks (2.2, 2.4, 3.2, 3.4, 3.6, 5.2, 5.4, 6.2) -- all 11 correctness properties defined but tests not written yet
- Wiring controller I/O to chain_tab refresh after save (minor)

**Decisions Made:**
- Used `"` (double-quote) as the inch unit symbol instead of "in" for professional display
- Main window uses QSplitter with 3:2 stretch ratio (left panel gets 60%)
- Results summary dialog shows plain-language explanation of what analysis numbers mean
- Sample file uses ASME Y14.5 mode with mixed distributions (normal, uniform, triangular)
- Snap Ring Groove Position nominal set to 2.2860 to produce a positive 0.047" gap

**Next Session Should:**
1. Fix visualization label overlap/cutoff -- consider:
   - Drawing labels in a separate row below all bars (fixed Y position per contributor index)
   - Using vertical/angled text for narrow bars
   - Adding a legend panel separate from the bar chart
   - Clipping labels to canvas bounds
2. Run the render harness, have user annotate the PNG, iterate on layout
3. Write the optional property-based tests (P1-P11) for formal correctness validation
4. Consider adding iteration count input dialog for Monte Carlo
5. Wire the real widgets into the main window's save workflow (refresh table after save/load)

**File Map:**
```
Tolerance-Analysis-Tool/
+-- README.md
+-- pyproject.toml                # Build config, dependencies
+-- docs/
|   +-- HANDOFF.md               # <- You are here
|   +-- GUIDE.md                 # User guide
|   +-- requirements.md          # Formal requirements (EARS format)
|   +-- design.md                # Technical design document
+-- examples/
|   +-- bearing_housing_stack.json  # Sample project file
+-- tests/
|   +-- conftest.py              # Hypothesis strategies
|   +-- render_harness.py        # Offscreen PNG render utility
|   +-- renders/                 # Output PNGs (gitignored)
|   +-- properties/              # Property-based tests (not yet written)
|   +-- unit/                    # Unit tests
|   +-- integration/             # Integration tests
+-- tolerance_analysis/
    +-- __init__.py
    +-- main.py                  # Application entry point
    +-- engine/
    |   +-- models.py            # Core dataclasses and enums
    |   +-- converter.py         # Tolerance type normalization
    |   +-- validator.py         # Input validation
    |   +-- worst_case.py        # Worst-case analyzer
    |   +-- rss.py               # RSS analyzer
    |   +-- monte_carlo.py       # Monte Carlo simulator
    +-- boundary/
    |   +-- controller.py        # Analysis orchestration
    |   +-- unit_converter.py    # Inch/mm conversion
    |   +-- standards.py         # GD&T standards manager
    +-- gui/
    |   +-- main_window.py       # MainWindow shell
    |   +-- chain_tab.py         # Contributor table widget
    |   +-- detail_panel.py      # Contributor detail card
    |   +-- visualization.py     # QPainter stack-up chart
    |   +-- results_panel.py     # Analysis results display
    |   +-- help_panel.py        # Built-in help viewer
    |   +-- dialogs.py           # Confirmation/error/new-chain dialogs
    |   +-- theme.py             # Colors, fonts, stylesheet
    +-- io/
    |   +-- project_file.py      # JSON save/load
    |   +-- schema.py            # Schema definition
    |   +-- pdf_report.py        # PDF generation
    +-- resources/
        +-- help/                # (placeholder for future markdown help files)
        +-- icons/               # (placeholder for future icons)
```
