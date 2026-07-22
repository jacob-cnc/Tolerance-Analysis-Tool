"""
Help panel providing built-in reference content for the Tolerance Analysis Tool.

Displays GD&T basics, tolerance strategies, common standards, and usage guides
in a non-modal dialog with table-of-contents navigation.
"""

from PyQt5.QtWidgets import (
    QDialog, QSplitter, QListWidget, QTextBrowser,
    QVBoxLayout, QListWidgetItem
)
from PyQt5.QtCore import Qt


# ---------------------------------------------------------------------------
# Help content sections (embedded HTML)
# ---------------------------------------------------------------------------

_APPLICATION_OVERVIEW = """\
<h2>Application Overview</h2>
<p>The Tolerance Analysis Tool is a desktop application for mechanical tolerance
stack-up analysis. It helps engineers and machinists predict how individual part
dimensions combine in an assembly.</p>

<h3>Core Workflow</h3>
<ol>
  <li><b>Create a Tolerance Chain</b> &mdash; Define the dimensional path through
      your assembly from a reference datum to a target feature.</li>
  <li><b>Add Contributors</b> &mdash; Enter each dimension along the path with
      its nominal value, tolerance, direction, and distribution type.</li>
  <li><b>Run Analysis</b> &mdash; Choose worst-case, RSS, or Monte Carlo to
      compute the expected assembly variation.</li>
  <li><b>Review Results</b> &mdash; View numeric results alongside the stack-up
      visualization showing contributor magnitudes and tolerance zones.</li>
  <li><b>Export</b> &mdash; Save the project for later or generate a PDF report
      for documentation and review.</li>
</ol>

<h3>Key Features</h3>
<ul>
  <li>Three analysis methods: Worst-Case, RSS, and Monte Carlo</li>
  <li>Horizontal stacking bar-chart visualization with tolerance bands</li>
  <li>Dual-unit support (inch / millimeter)</li>
  <li>GD&amp;T standard awareness (ASME Y14.5, ISO GPS, Generic)</li>
  <li>JSON project files for save/load</li>
  <li>Professional PDF report generation</li>
</ul>
"""

_GDT_BASICS = """\
<h2>GD&amp;T Basics</h2>

<h3>Datum References</h3>
<p>A <b>datum</b> is a theoretically exact geometric reference derived from a
datum feature on the part. Datums establish the coordinate system used to locate
and orient tolerance zones. They are identified by letters (A, B, C&hellip;) and
referenced in feature control frames.</p>

<h3>Feature Control Frames</h3>
<p>A feature control frame communicates geometric tolerance requirements. It
contains (left to right):</p>
<ol>
  <li>Geometric characteristic symbol</li>
  <li>Tolerance zone shape and value</li>
  <li>Material condition modifier (if applicable)</li>
  <li>Datum references (primary, secondary, tertiary)</li>
</ol>

<h3>The 14 Geometric Tolerance Types</h3>
<table border="1" cellpadding="4" cellspacing="0">
<tr><th>#</th><th>Type</th><th>Category</th><th>Description</th></tr>
<tr><td>1</td><td>Straightness</td><td>Form</td>
    <td>Controls how straight a line element or axis is</td></tr>
<tr><td>2</td><td>Flatness</td><td>Form</td>
    <td>Controls how flat a surface is</td></tr>
<tr><td>3</td><td>Circularity</td><td>Form</td>
    <td>Controls how round a cross-section is</td></tr>
<tr><td>4</td><td>Cylindricity</td><td>Form</td>
    <td>Controls combined roundness and straightness of a cylinder</td></tr>
<tr><td>5</td><td>Profile of a Line</td><td>Profile</td>
    <td>Controls the shape of a 2D cross-section</td></tr>
<tr><td>6</td><td>Profile of a Surface</td><td>Profile</td>
    <td>Controls the shape of a 3D surface</td></tr>
<tr><td>7</td><td>Angularity</td><td>Orientation</td>
    <td>Controls a surface or axis at a specified angle to a datum</td></tr>
<tr><td>8</td><td>Perpendicularity</td><td>Orientation</td>
    <td>Controls a surface or axis at 90&deg; to a datum</td></tr>
<tr><td>9</td><td>Parallelism</td><td>Orientation</td>
    <td>Controls a surface or axis parallel to a datum</td></tr>
<tr><td>10</td><td>Position</td><td>Location</td>
    <td>Controls the location of a feature relative to datums</td></tr>
<tr><td>11</td><td>Concentricity</td><td>Location</td>
    <td>Controls the center points of a feature relative to a datum axis</td></tr>
<tr><td>12</td><td>Symmetry</td><td>Location</td>
    <td>Controls the median points of a feature relative to a datum</td></tr>
<tr><td>13</td><td>Circular Runout</td><td>Runout</td>
    <td>Controls surface variation at any single cross-section during rotation</td></tr>
<tr><td>14</td><td>Total Runout</td><td>Runout</td>
    <td>Controls entire surface variation during full rotation</td></tr>
</table>
"""

_STRATEGY_GUIDE = """\
<h2>Tolerance Strategy Guide</h2>

<h3>Worst-Case Analysis</h3>
<p>Assumes every contributor simultaneously at its worst limit. This is the most
conservative method.</p>
<ul>
  <li><b>Formula:</b> Total tolerance = &Sigma;|t<sub>i</sub>|</li>
  <li><b>When to use:</b> Safety-critical assemblies, small contributor counts
      (&lt;5), or when 100% interchangeability is required.</li>
  <li><b>Pros:</b> Guarantees assembly &mdash; no rejects possible.</li>
  <li><b>Cons:</b> Over-constrains manufacturing; tight tolerances increase cost.</li>
</ul>

<h3>RSS (Root Sum of Squares) Analysis</h3>
<p>Assumes contributors are statistically independent and normally distributed.
Predicts the statistically likely variation rather than the absolute extreme.</p>
<ul>
  <li><b>Formula:</b> Statistical tolerance = &radic;(&Sigma;t<sub>i</sub>&sup2;)</li>
  <li><b>When to use:</b> High-volume production (&gt;50 parts), contributors are
      independent, processes are in statistical control (Cpk &ge; 1.33).</li>
  <li><b>Pros:</b> Allows looser individual tolerances, reducing manufacturing cost.</li>
  <li><b>Cons:</b> Predicts ~99.73% yield (3&sigma;), not 100%. Assumptions must hold.</li>
</ul>

<h3>Monte Carlo Simulation</h3>
<p>Generates random samples for each contributor from its specified distribution
and computes the assembly result for thousands of virtual assemblies.</p>
<ul>
  <li><b>Formula:</b> Numeric sampling &mdash; no closed-form expression.</li>
  <li><b>When to use:</b> Mixed distributions, non-normal processes, complex
      interactions, or when you need the full probability distribution of
      assembly outcomes.</li>
  <li><b>Pros:</b> Handles any distribution shape; shows the complete output
      distribution including tails.</li>
  <li><b>Cons:</b> Results vary between runs (seed-dependent); requires more
      computation time.</li>
</ul>

<h3>Comparison Summary</h3>
<table border="1" cellpadding="4" cellspacing="0">
<tr><th>Method</th><th>Conservatism</th><th>Speed</th><th>Best For</th></tr>
<tr><td>Worst-Case</td><td>Highest</td><td>Instant</td>
    <td>Safety-critical, low volume</td></tr>
<tr><td>RSS</td><td>Moderate</td><td>Instant</td>
    <td>High-volume, normal processes</td></tr>
<tr><td>Monte Carlo</td><td>Realistic</td><td>Seconds</td>
    <td>Complex/mixed distributions</td></tr>
</table>
"""

_STANDARDS_REFERENCE = """\
<h2>Common Standards Reference</h2>

<h3>Fit Types</h3>
<table border="1" cellpadding="4" cellspacing="0">
<tr><th>Fit Type</th><th>Characteristic</th><th>Example Use</th></tr>
<tr><td>Clearance Fit</td>
    <td>Shaft is always smaller than hole; free movement</td>
    <td>Sliding bearings, running fits</td></tr>
<tr><td>Transition Fit</td>
    <td>May result in clearance or interference</td>
    <td>Locating pins, spigot fits</td></tr>
<tr><td>Press Fit (Interference)</td>
    <td>Shaft is always larger than hole; requires force to assemble</td>
    <td>Bearing races, dowel pins, bushings</td></tr>
</table>

<h3>ISO 286 Tolerance Grades (IT Grades)</h3>
<p>ISO 286 defines standard tolerance grades IT01 through IT18. Lower grades
are tighter (more precise). Common applications:</p>
<table border="1" cellpadding="4" cellspacing="0">
<tr><th>Grade</th><th>Typical Application</th></tr>
<tr><td>IT01&ndash;IT1</td><td>Gauge blocks, master gauges</td></tr>
<tr><td>IT2&ndash;IT4</td><td>Precision grinding, honing</td></tr>
<tr><td>IT5&ndash;IT7</td><td>Fits for bearings, precision machining</td></tr>
<tr><td>IT8&ndash;IT11</td><td>General machining (turning, milling)</td></tr>
<tr><td>IT12&ndash;IT14</td><td>Sheet metal, stamping, forging</td></tr>
<tr><td>IT15&ndash;IT18</td><td>Casting, flame cutting</td></tr>
</table>

<h3>ISO 286 Hole/Shaft Basis</h3>
<ul>
  <li><b>Hole-basis system (H):</b> Hole has zero fundamental deviation;
      shaft letter determines fit class (e.g., H7/g6 clearance, H7/p6 press).</li>
  <li><b>Shaft-basis system (h):</b> Shaft has zero fundamental deviation;
      hole letter determines fit class (e.g., G7/h6 clearance, P7/h6 press).</li>
</ul>

<h3>ANSI B4.1 &mdash; Preferred Limits and Fits</h3>
<p>ANSI B4.1 defines preferred fit classes for the inch system:</p>
<table border="1" cellpadding="4" cellspacing="0">
<tr><th>Class</th><th>Name</th><th>Type</th></tr>
<tr><td>RC1&ndash;RC9</td><td>Running &amp; Sliding Clearance</td><td>Clearance</td></tr>
<tr><td>LC1&ndash;LC11</td><td>Locational Clearance</td><td>Clearance</td></tr>
<tr><td>LT1&ndash;LT6</td><td>Locational Transition</td><td>Transition</td></tr>
<tr><td>LN1&ndash;LN3</td><td>Locational Interference</td><td>Interference</td></tr>
<tr><td>FN1&ndash;FN5</td><td>Force &amp; Shrink Fits</td><td>Interference</td></tr>
</table>
<p><b>Tip:</b> For press-fit bearing installations, FN2 (light drive) or
FN3 (medium drive) are common starting points.</p>
"""

_USING_THE_TOOL = """\
<h2>Using the Tool</h2>

<h3>Creating a Tolerance Chain</h3>
<ol>
  <li>Click <b>New Chain</b> in the toolbar or use File &rarr; New Chain.</li>
  <li>Enter a descriptive name (e.g., &ldquo;Bearing Housing Axial Stack&rdquo;).</li>
  <li>Optionally add a description for documentation purposes.</li>
</ol>

<h3>Adding Contributors</h3>
<ol>
  <li>With a chain selected, click <b>Add Contributor</b>.</li>
  <li>Enter the nominal dimension and tolerance values.</li>
  <li>Select the tolerance type: bilateral (&plusmn;), unilateral, or limit.</li>
  <li>Set the direction: positive (adds to stack) or negative (subtracts).</li>
  <li>Click the row to open the Detail Panel for distribution type, notes, and
      material info.</li>
</ol>

<h3>Running Analyses</h3>
<ul>
  <li><b>Worst-Case:</b> Click the Worst-Case button. Requires &ge;2 contributors.</li>
  <li><b>RSS:</b> Click the RSS button. Requires &ge;2 contributors.</li>
  <li><b>Monte Carlo:</b> Click Monte Carlo, choose iteration count (1,000&ndash;1,000,000),
      and run. Each contributor uses its assigned distribution.</li>
</ul>

<h3>Changing Units</h3>
<p>Use the unit selector (inch / mm) in the toolbar. All values convert
automatically using 1 in = 25.4 mm. Display precision adjusts to
4 decimals (inch) or 3 decimals (mm).</p>

<h3>Changing Standards</h3>
<p>Select ASME Y14.5, ISO GPS, or Generic from the standards selector. This
changes symbol display and report labeling but does <em>not</em> modify your
numeric data.</p>

<h3>Saving and Loading</h3>
<ul>
  <li><b>Save:</b> File &rarr; Save (Ctrl+S). Stores as a versioned JSON file.</li>
  <li><b>Open:</b> File &rarr; Open (Ctrl+O). Restores all chains, contributors,
      and results.</li>
</ul>

<h3>Exporting PDF Reports</h3>
<p>File &rarr; Export PDF generates a professional report including the tolerance
chain table, analysis results, and visualization. The report header shows
project name, date, standard mode, and unit system.</p>
"""


# ---------------------------------------------------------------------------
# Assemble topics list with actual content
# ---------------------------------------------------------------------------

HELP_TOPICS = [
    ("Application Overview", _APPLICATION_OVERVIEW),
    ("GD&T Basics", _GDT_BASICS),
    ("Tolerance Strategy Guide", _STRATEGY_GUIDE),
    ("Common Standards Reference", _STANDARDS_REFERENCE),
    ("Using the Tool", _USING_THE_TOOL),
]


# ---------------------------------------------------------------------------
# HelpPanel widget
# ---------------------------------------------------------------------------

class HelpPanel(QDialog):
    """
    Non-modal help dialog with a table of contents and content browser.

    Opens alongside the main window so the user can reference help content
    without closing or losing their active analysis.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Help — Tolerance Analysis Tool")
        self.setMinimumSize(800, 550)
        self.resize(1000, 620)
        # Non-modal: user can interact with the main window
        self.setModal(False)

        self._setup_ui()
        self._populate_topics()

        # Select the first topic by default
        if self._toc_list.count() > 0:
            self._toc_list.setCurrentRow(0)

    def _setup_ui(self):
        """Build the splitter layout: TOC list on the left, content on the right."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(6, 6, 6, 6)

        splitter = QSplitter(Qt.Horizontal, self)

        # Table of contents (left pane)
        self._toc_list = QListWidget()
        self._toc_list.setMaximumWidth(260)
        self._toc_list.setMinimumWidth(180)
        self._toc_list.currentRowChanged.connect(self._on_topic_selected)
        splitter.addWidget(self._toc_list)

        # Content browser (right pane)
        self._content_browser = QTextBrowser()
        self._content_browser.setOpenExternalLinks(True)
        splitter.addWidget(self._content_browser)

        # Set initial splitter sizes (TOC ~25%, content ~75%)
        splitter.setSizes([240, 760])

        layout.addWidget(splitter)

    def _populate_topics(self):
        """Load topic titles into the TOC list."""
        for title, _content in HELP_TOPICS:
            item = QListWidgetItem(title)
            self._toc_list.addItem(item)

    def _on_topic_selected(self, row: int):
        """Display the HTML content for the selected topic."""
        if 0 <= row < len(HELP_TOPICS):
            _title, content = HELP_TOPICS[row]
            self._content_browser.setHtml(self._wrap_html(content))

    @staticmethod
    def _wrap_html(body: str) -> str:
        """Wrap body content in a styled HTML document."""
        return f"""\
<!DOCTYPE html>
<html>
<head>
<style>
body {{
    font-family: 'Segoe UI', Arial, sans-serif;
    font-size: 13px;
    line-height: 1.5;
    padding: 8px;
    color: #212121;
}}
h2 {{
    color: #1565c0;
    border-bottom: 1px solid #ccc;
    padding-bottom: 4px;
}}
h3 {{
    color: #37474f;
    margin-top: 16px;
}}
table {{
    border-collapse: collapse;
    margin: 8px 0;
    font-size: 12px;
}}
th {{
    background-color: #e3f2fd;
    text-align: left;
    padding: 5px 8px;
}}
td {{
    padding: 4px 8px;
}}
ul, ol {{
    margin: 4px 0 8px 20px;
}}
</style>
</head>
<body>
{body}
</body>
</html>"""
