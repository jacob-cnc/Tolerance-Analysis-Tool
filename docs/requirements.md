# Requirements Document

## Introduction

A PyQt5 desktop application for mechanical tolerance stack-up analysis targeting mechanical engineers and machinists. The tool enables users to define tolerance chains, perform worst-case, RSS, and Monte Carlo analyses, visualize stack-ups, and generate professional reports. The application supports dual-unit systems (inch/metric) and GD&T standard awareness (ASME Y14.5 / ISO GPS / Generic). The architecture is heavily modular with a pure Python analysis engine separated from the GUI layer.

## Glossary

- **Application**: The Tolerance Analysis Tool PyQt5 desktop application
- **Analysis_Engine**: The pure Python backend module responsible for performing tolerance calculations (worst-case, RSS, Monte Carlo) with no GUI dependencies
- **Tolerance_Chain**: An ordered list of dimension contributors that defines a stack-up path from a reference to a target
- **Contributor**: A single dimensional element in a tolerance chain, defined by nominal value, tolerance specification, and direction
- **Worst_Case_Analysis**: Arithmetic summation of all tolerances assuming all contributors simultaneously at their extreme limits
- **RSS_Analysis**: Root Sum of Squares statistical analysis assuming independent, normally distributed manufacturing variation
- **Monte_Carlo_Simulation**: Statistical analysis using random sampling from specified distributions to predict assembly variation
- **Stack_Up_Visualization**: A horizontal stacking bar chart with translucent tolerance zone bands showing the cumulative dimensional path
- **Tolerance_Type**: The classification of how a tolerance is specified - bilateral (+-), unilateral (asymmetric +/-), or limit dimension
- **Standard_Mode**: The active GD&T standard context (ASME Y14.5, ISO GPS, or Generic) that controls symbol display, default assumptions, and report labeling
- **Contributor_Table**: A compact spreadsheet-style table providing an overview of all contributors in a tolerance chain with inline editing
- **Detail_Panel**: An expanded card view for a selected contributor showing distribution picker, notes, and material info
- **Project_File**: A JSON file containing the complete state of a tolerance analysis for save/load operations
- **Report**: A PDF document containing analysis inputs, results, and visualizations

## Requirements

### Requirement 1: Tolerance Chain Definition

**User Story:** As a mechanical engineer, I want to define a tolerance chain as an ordered list of contributors, so that I can model the dimensional path through my assembly.

#### Acceptance Criteria

1. THE Application SHALL allow creation of a new tolerance chain with a user-specified name (1 to 100 characters) and description (0 to 500 characters)
2. WHEN a contributor is added to a tolerance chain, THE Application SHALL store the contributor's nominal dimension (a numeric value in the range 0.0001 to 9999.9999), tolerance specification (non-negative numeric values), direction (positive or negative), and optional description (0 to 200 characters)
3. THE Application SHALL support bilateral (+-), unilateral (asymmetric +/-), and limit dimension tolerance types for each contributor
4. WHEN a contributor is selected in the Contributor_Table, THE Application SHALL display the Detail_Panel with distribution picker, notes field, and material information field
5. THE Application SHALL allow reordering of contributors within a tolerance chain via drag-and-drop or move-up/move-down controls
6. WHEN a user initiates deletion of a contributor, THE Application SHALL display a confirmation prompt before removing the contributor from the tolerance chain
7. WHEN a tolerance chain contains fewer than two contributors, THE Application SHALL disable the analysis controls and display a message indicating the minimum requirement
8. IF a user submits a contributor with a non-numeric nominal dimension or a negative tolerance value, THEN THE Application SHALL reject the entry, retain the input values in the form, and display an error message indicating the invalid field
9. IF a user attempts to create a tolerance chain with an empty name or a name that already exists in the current session, THEN THE Application SHALL prevent creation and display an error message indicating the naming constraint

### Requirement 2: Worst-Case Analysis

**User Story:** As a mechanical engineer, I want to perform worst-case (arithmetic) tolerance analysis, so that I can determine the absolute maximum and minimum assembly dimensions.

#### Acceptance Criteria

1. WHEN the user initiates a worst-case analysis, THE Analysis_Engine SHALL compute the total nominal dimension as the algebraic sum of all contributor nominals multiplied by their direction signs (+1 or -1)
2. WHEN the user initiates a worst-case analysis, THE Analysis_Engine SHALL compute the total worst-case tolerance as the arithmetic sum of all individual contributor absolute tolerance magnitudes
3. WHEN the worst-case analysis completes, THE Application SHALL display the nominal result, maximum limit (nominal plus total tolerance), minimum limit (nominal minus total tolerance), and total tolerance band (2 times total tolerance)
4. WHEN a contributor uses a unilateral tolerance (e.g., +0.000/-0.005), THE Analysis_Engine SHALL convert it to equivalent bilateral form by shifting the nominal by half the sum of the upper and lower deviations and setting the bilateral tolerance to half the difference between the upper and lower deviations, before including it in summation
5. WHEN a contributor uses limit dimensions, THE Analysis_Engine SHALL derive the nominal as the midpoint of the upper and lower limits and the bilateral tolerance as half the difference between the upper and lower limits, before including it in summation
6. IF the user initiates a worst-case analysis and the tolerance stack contains fewer than 2 contributors, THEN THE Application SHALL display an error message indicating that at least 2 contributors are required and SHALL NOT perform the calculation

### Requirement 3: RSS Analysis

**User Story:** As a mechanical engineer, I want to perform RSS (Root Sum of Squares) statistical analysis, so that I can determine the statistically probable assembly variation assuming normal distributions.

#### Acceptance Criteria

1. WHEN the user initiates an RSS analysis on a tolerance chain containing 2 or more contributors, THE Analysis_Engine SHALL compute the statistical tolerance as the square root of the sum of squares of all individual contributor tolerances
2. WHEN the RSS analysis completes, THE Application SHALL display the nominal result, statistical maximum limit, statistical minimum limit, and the statistical tolerance band, each rounded to 4 decimal places
3. WHEN the RSS analysis completes, THE Application SHALL display the RSS statistical result and the worst-case result together in a comparative format showing both tolerance bands and both sets of limits
4. WHEN a tolerance chain has mixed tolerance types, THE Analysis_Engine SHALL convert each contributor to equivalent bilateral form by halving the total tolerance range and shifting the nominal by the mean of the deviation limits, before performing the RSS calculation
5. IF the user initiates an RSS analysis on a tolerance chain containing fewer than 2 contributors, THEN THE Application SHALL display an error message indicating that RSS analysis requires at least 2 tolerance contributors

### Requirement 4: Monte Carlo Simulation

**User Story:** As a mechanical engineer, I want to run Monte Carlo simulations on my tolerance stack, so that I can understand the full statistical distribution of assembly outcomes under realistic manufacturing conditions.

#### Acceptance Criteria

1. WHEN the user initiates a Monte Carlo simulation, THE Analysis_Engine SHALL generate random samples for each contributor based on the contributor's specified distribution, producing one assembly result per iteration
2. THE Application SHALL allow the user to specify the number of simulation iterations between 1,000 and 1,000,000 inclusive, with a default of 10,000
3. WHEN the Monte Carlo simulation completes, THE Application SHALL display a histogram of the assembly dimension distribution with a minimum of 20 bins
4. WHEN the Monte Carlo simulation completes, THE Analysis_Engine SHALL report the mean, standard deviation, minimum, maximum, and percentile values at the 0.135%, 2.275%, 50%, 97.725%, and 99.865% levels (corresponding to +-2sigma and +-3sigma coverage)
5. THE Analysis_Engine SHALL support normal, uniform, and triangular distributions for contributor sampling, with normal as the default distribution when no distribution type has been explicitly assigned to a contributor
6. WHEN the user changes a contributor's distribution type in the Detail_Panel, THE Application SHALL use the selected distribution for that contributor in subsequent Monte Carlo simulations
7. IF the user initiates a Monte Carlo simulation when the tolerance stack contains no contributors, THEN THE Application SHALL display an error message indicating that at least one contributor is required and SHALL NOT execute the simulation

### Requirement 5: Stack-Up Visualization

**User Story:** As a mechanical engineer, I want to see a visual representation of my tolerance stack-up, so that I can quickly understand contributor magnitudes, directions, and tolerance zones.

#### Acceptance Criteria

1. THE Application SHALL render the stack-up as a horizontal stacking bar chart where each bar segment represents a contributor's nominal dimension, scaled proportionally to its magnitude relative to other contributors
2. THE Application SHALL display tolerance zones as translucent bands (20%-50% opacity) overlaid on each contributor segment, with band width representing the contributor's tolerance range
3. THE Application SHALL use blue/cyan color for positive-direction contributors and orange/amber color for negative-direction contributors
4. WHEN analysis results are available, THE Application SHALL display the overall stack-up result bar in green color when the total assembly dimension falls within the specified tolerance limits, and in red color when it falls outside the specified tolerance limits
5. WHEN a Monte Carlo simulation has been run, THE Application SHALL overlay the Monte Carlo result distribution as a histogram or density curve on the visualization in purple color, aligned to the total stack-up axis
6. THE Application SHALL render the visualization on a dark workspace canvas surrounded by the light UI shell
7. WHEN a contributor is added, removed, or modified, THE Application SHALL update the visualization within 500 milliseconds
8. IF the stack-up contains zero contributors, THEN THE Application SHALL display an empty chart area with a placeholder message indicating that no contributors have been added

### Requirement 6: Save and Load Projects

**User Story:** As a mechanical engineer, I want to save and load my tolerance analyses, so that I can resume work across sessions and share analyses with colleagues.

#### Acceptance Criteria

1. WHEN the user saves a project, THE Application SHALL serialize the complete analysis state to a JSON Project_File including a schema version identifier, all tolerance chains, contributor data, analysis settings, and results, preserving numeric values to at least 6 significant decimal digits
2. WHEN the user loads a Project_File, THE Application SHALL restore the complete analysis state including tolerance chains, contributor data, analysis settings, and previously computed results within 5 seconds for files up to 50 MB in size
3. IF a Project_File fails to parse, THEN THE Application SHALL display an error message indicating the field name or line number where parsing failed and SHALL NOT modify the current application state
4. WHEN the user opens the application without a project loaded, THE Application SHALL present an option to create a new project or open an existing Project_File
5. THE Application SHALL maintain round-trip fidelity such that saving and then loading a Project_File produces an analysis state where all string and boolean values are identical and all numeric values match within +-1e-10
6. IF a save operation fails due to a file system error, THEN THE Application SHALL display an error message indicating the cause of the failure and SHALL preserve the previously saved Project_File without corruption

### Requirement 7: PDF Report Export

**User Story:** As a mechanical engineer, I want to export my analysis results to a professional PDF report, so that I can share findings with colleagues and include them in design documentation.

#### Acceptance Criteria

1. WHEN the user exports a report, THE Application SHALL generate a PDF document containing the tolerance chain definition, analysis inputs, computed results, and stack-up visualization, and SHALL display a confirmation indicating the file name and save location within 30 seconds of the export request
2. THE Report SHALL include a header with project name, date, active Standard_Mode, and unit system
3. THE Report SHALL present contributor data in a table with columns for name, nominal, tolerance, direction, and tolerance type, supporting up to 50 contributors
4. THE Report SHALL include the worst-case and RSS results, each preceded by its analysis method name as a label
5. IF Monte Carlo results are available, THEN THE Report SHALL include the Monte Carlo results preceded by the label identifying the analysis method, sample size, and statistical values
6. IF the active Standard_Mode is ASME, THEN THE Report SHALL use ASME Y14.5 symbols and terminology in labeling
7. IF the active Standard_Mode is ISO, THEN THE Report SHALL use ISO GPS symbols and terminology in labeling
8. IF the user attempts to export a report before any analysis has been computed, THEN THE Application SHALL display an error message indicating that analysis results are required and SHALL not generate a PDF file

### Requirement 8: Dual-Unit Support

**User Story:** As a mechanical engineer, I want to work in either inch or metric units, so that I can use the measurement system appropriate for my project and industry.

#### Acceptance Criteria

1. THE Application SHALL provide a unit system selector with options for inch and millimeter, with inch selected as the default on first launch
2. WHEN the user selects a unit system, THE Application SHALL display all dimensional values in the selected unit using 4 decimal places for inch values and 3 decimal places for millimeter values
3. WHEN the user changes the unit system, THE Application SHALL convert all existing dimensional values to the newly selected unit using the conversion factor 1 inch = 25.4 mm, rounding results to the display precision defined in criterion 2
4. THE Application SHALL display the active unit system label adjacent to all dimensional input fields and result displays
5. WHEN a Project_File is saved, THE Application SHALL store the active unit system in the file
6. WHEN a Project_File is loaded, THE Application SHALL restore the unit system that was active when the file was saved
7. IF a Project_File is loaded and contains no stored unit system, THEN THE Application SHALL default to inch and display a notification indicating that the default unit system was applied

### Requirement 9: GD&T Standard Awareness

**User Story:** As a mechanical engineer, I want to select between ASME Y14.5, ISO GPS, and Generic standard modes, so that symbol display, default assumptions, and report labeling match my project's applicable standard.

#### Acceptance Criteria

1. THE Application SHALL provide a standard mode selector with options for ASME Y14.5, ISO GPS, and Generic
2. WHILE ASME Y14.5 mode is active, THE Application SHALL display tolerance symbols using ASME Y14.5 conventions, apply the Rule #1 envelope principle as the default assumption, and label reports with the ASME Y14.5 standard identifier
3. WHILE ISO GPS mode is active, THE Application SHALL display tolerance symbols using ISO GPS conventions, apply the independency principle as the default assumption, and label reports with the ISO GPS standard identifier
4. WHILE Generic mode is active, THE Application SHALL display tolerance values without standard-specific symbols, apply no default geometric assumptions, and label reports without a standard identifier
5. WHEN the user changes the Standard_Mode, THE Application SHALL update all symbol displays and report labels within 2 seconds without modifying the underlying numerical tolerance data
6. WHEN a Project_File is saved, THE Application SHALL store the active Standard_Mode in the file
7. WHEN a Project_File is opened that contains a stored Standard_Mode, THE Application SHALL apply the stored Standard_Mode and update all displays accordingly
8. IF no Standard_Mode has been previously selected or stored, THEN THE Application SHALL default to Generic mode

### Requirement 10: Help and Reference Content

**User Story:** As a mechanical engineer or machinist, I want access to built-in help content covering GD&T basics, tolerance strategies, and common standards, so that I can make informed decisions while performing analysis.

#### Acceptance Criteria

1. THE Application SHALL provide a help section accessible from the main menu or toolbar
2. THE Application SHALL include a GD&T basics guide explaining geometric dimensioning and tolerancing concepts including datum references, feature control frames, and the 14 geometric tolerance types
3. THE Application SHALL include a tolerance strategy guide covering worst-case, RSS, and Monte Carlo approaches for allocating tolerances in assemblies
4. THE Application SHALL include a common tolerance standards reference with tables for press fits, clearance fits, transition fits, and standard tolerance grades based on ISO 286 and ANSI B4.1 standards
5. THE Application SHALL include an application usage overview explaining the tool's workflow and features
6. WHEN the user accesses a help topic, THE Application SHALL display the content in a dedicated panel or dialog within 2 seconds without closing the active analysis or discarding unsaved data in the active session
7. THE Application SHALL provide a table of contents or topic list enabling the user to navigate between help topics without returning to the main menu

### Requirement 11: Data Entry Interface

**User Story:** As a mechanical engineer, I want a hybrid table and detail panel interface for entering contributor data, so that I can efficiently manage many contributors while having access to detailed settings when needed.

#### Acceptance Criteria

1. THE Application SHALL display all contributors (up to 100) in a spreadsheet-style Contributor_Table with columns for name, nominal, tolerance, direction, and tolerance type
2. THE Contributor_Table SHALL support inline editing of the nominal, tolerance, direction, and tolerance type columns directly within table cells
3. WHEN the user clicks a row in the Contributor_Table, THE Application SHALL display the Detail_Panel showing the settings for that contributor, replacing any previously displayed Detail_Panel content
4. THE Detail_Panel SHALL provide controls for selecting distribution type, entering notes (up to 500 characters), and specifying material name
5. IF the user enters a non-numeric value into a numeric input field (nominal or tolerance), THEN THE Application SHALL reject the entry, preserve the previous valid value, and display a visual indicator on the field border
6. WHEN the user enters a numeric value into the nominal or tolerance field, THE Application SHALL accept values in the range -999999.9999 to 999999.9999 with up to 4 decimal places

### Requirement 12: Application Theme and Layout

**User Story:** As a user, I want a clean, information-dense interface with a dark visualization canvas and light UI shell, so that I can work efficiently with complex data in a professional environment.

#### Acceptance Criteria

1. THE Application SHALL render the Stack_Up_Visualization on a canvas area with a background lightness value no greater than 20% (HSL L <= 20%)
2. THE Application SHALL render UI controls (menus, tables, panels, toolbars) using a theme with background lightness value of at least 55% (HSL L >= 55%), visually distinguishable from the dark canvas area
3. THE Application SHALL use consistent color semantics: blue/cyan for positive contributors, orange/amber for negative contributors, green for in-spec results, red for out-of-spec results, and purple for Monte Carlo overlays
4. THE Application SHALL enforce a minimum window size of no less than 1024x768 pixels, below which the window cannot be resized
5. IF the user attempts to resize the Application window below the minimum window size, THEN THE Application SHALL prevent the resize and maintain the window at the minimum enforced dimensions

### Requirement 13: Project File Serialization Format

**User Story:** As a developer, I want a well-defined JSON serialization format for project files, so that the data is human-readable, versionable, and interoperable.

#### Acceptance Criteria

1. THE Application SHALL serialize Project_Files using JSON format with a top-level schema version field containing a semantic version string (MAJOR.MINOR.PATCH)
2. THE Application SHALL include in the Project_File: schema version, unit system, standard mode, and an array of tolerance chains with their contributors and analysis settings
3. WHEN a Project_File with an unrecognized schema version is loaded, THE Application SHALL display a non-blocking warning message indicating the file's schema version and the application's supported schema version, and then attempt to load the file
4. THE Application SHALL write Project_Files with indented JSON formatting using a consistent indentation of 2 spaces per nesting level
5. WHEN a valid Project_File JSON document is parsed and then serialized, THE Application SHALL produce a JSON document containing identical keys, values, array ordering, and nesting structure as the original, regardless of key ordering or whitespace differences
6. IF a Project_File contains syntactically invalid JSON, THEN THE Application SHALL reject the file, display an error message indicating the file could not be parsed, and preserve any currently open project data unchanged
