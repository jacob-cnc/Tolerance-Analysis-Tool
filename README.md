# Tolerance Analysis Tool

A PyQt5 desktop application for mechanical tolerance stack-up analysis targeting mechanical engineers and machinists.

## Features

- **Tolerance Chain Definition** — Define ordered lists of dimensional contributors with bilateral, unilateral, or limit tolerances
- **Worst-Case Analysis** — Arithmetic summation assuming all contributors at extreme limits
- **RSS Analysis** — Root Sum of Squares statistical analysis assuming normal distributions
- **Monte Carlo Simulation** — Random sampling (1K–1M iterations) with normal, uniform, or triangular distributions
- **Stack-Up Visualization** — Horizontal bar chart with tolerance zone overlays on a dark canvas
- **Dual-Unit Support** — Inch (4 dp) / Millimeter (3 dp) with live conversion
- **GD&T Standard Awareness** — ASME Y14.5, ISO GPS, and Generic modes
- **PDF Report Export** — Professional reports via ReportLab
- **Project Save/Load** — Versioned JSON serialization with round-trip fidelity

## Architecture

```
tolerance_analysis/
├── engine/       # Pure Python analysis (no GUI deps, only numpy for MC)
├── boundary/     # Unit conversion, standards, orchestration
├── gui/          # PyQt5 widgets and visualization
├── io/           # JSON project files, PDF report generation
└── resources/    # Help content, icons
```

See [`docs/design.md`](docs/design.md) for the full technical design.

## Tech Stack

- Python 3.10+
- PyQt5
- numpy (Monte Carlo only)
- ReportLab (PDF generation)
- Hypothesis + pytest (testing)

## Development

```bash
# Install dependencies
pip install -r requirements.txt

# Run the application
python -m tolerance_analysis.main

# Run tests
pytest tests/
```

## Documentation

| Document | Description |
|----------|-------------|
| [`docs/requirements.md`](docs/requirements.md) | Formal requirements (EARS format) |
| [`docs/design.md`](docs/design.md) | Technical design, algorithms, correctness properties |
| [`docs/HANDOFF.md`](docs/HANDOFF.md) | Session continuity notes for AI-assisted development |

## License

MIT
