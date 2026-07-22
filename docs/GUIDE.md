# Getting Started with the Tolerance Analysis Tool

A practical guide for mechanical engineers who know tolerances but are new to this tool.

---

## 1. Quick Start

Launch the application and you'll see four panels:

- **Contributor Table** (top-left) — Lists all dimensional contributors in the active tolerance chain. Each row shows name, nominal, tolerance, direction, and distribution.
- **Detail Panel** (bottom-left) — Displays and edits the full properties of the selected contributor: tolerance type, distribution, material, description, and notes.
- **Visualization Canvas** (center) — A proportional bar chart showing each contributor's relative size and tolerance band in the stack. Positive contributors extend right; negative extend left.
- **Results Panel** (right) — Displays analysis output: worst-case, RSS, and Monte Carlo results with numeric summaries and histograms.

## 2. Loading the Sample Project

1. Go to **File → Open**
2. Navigate to the `examples/` folder in the application directory
3. Select `bearing_housing_stack.json`
4. The contributor table populates with 5 rows, the visualization draws the stack, and the project name shows "Bearing Housing Axial Stack-Up" in the title bar

This sample file is a realistic lathe spindle bearing housing stack-up you can use to explore every feature before building your own.

## 3. Understanding the Sample

The bearing housing stack represents the axial distance from the housing face through the bearing pocket to the snap ring that retains the assembly. The **gap** — the result of this stack-up — is the space left over for a preload shim.

Physical layout (left to right along the spindle axis):

```
Housing Face → [Bore Depth] → [Bearing] → [Spacer] → ... → [Snap Ring Groove] ← Housing Face
```

**Direction convention:**

- **Positive** = adds to the gap (builds material toward the far end)
- **Negative** = subtracts from the gap (defines the boundary we're measuring against)

The three positive contributors (Housing Bore Depth, Bearing Width, Spacer Ring) represent material stacking up from the housing face inward. The two negative contributors (Snap Ring Groove Position, Snap Ring Thickness) define where the snap ring sits — the far boundary. The difference is the shim gap.

Why are the snap ring groove and snap ring negative? Because they establish the reference datum on the opposite side. The groove position is measured from the same housing face, so it *limits* how much space is available. The snap ring thickness further reduces the available gap.

## 4. Running Analysis

### Worst-Case Analysis

Click **"Worst-Case"** in the toolbar.

Worst-case (also called arithmetic or limit stacking) assumes every contributor simultaneously hits its worst extreme. All positive contributors go to their maximum, and all negative contributors go to their minimum — or vice versa — whichever makes the gap largest or smallest.

The results panel shows:
- **Nominal** — The gap when everything is at nominal (≈0.0470")
- **Maximum** — The largest possible gap (all tolerances conspire to open it)
- **Minimum** — The smallest possible gap (all tolerances conspire to close it)
- **Tolerance Band** — Maximum minus minimum; the total range of possible outcomes

This is the most conservative method. In reality, it's statistically improbable that all dimensions hit their extremes simultaneously.

### RSS (Root Sum of Squares)

Click **"RSS"** in the toolbar.

RSS assumes each contributor's actual value is statistically independent and normally distributed within its tolerance. Instead of adding tolerances arithmetically, it takes the square root of the sum of their squares.

The result is always tighter than worst-case. The statistical band represents approximately 99.73% coverage (±3σ) assuming normal manufacturing processes.

The results panel shows both the RSS result and the worst-case result side by side for comparison. If they're close together, your stack has very few contributors and worst-case may be the safer design target.

### Monte Carlo Simulation

Click **"Monte Carlo"** in the toolbar.

Monte Carlo generates thousands of virtual assemblies. For each iteration, it randomly samples each contributor from its specified distribution (normal, uniform, or triangular), applies the direction, and computes the resulting gap.

The results panel shows:
- **Histogram** — The shape of the predicted gap distribution. This accounts for mixed distribution types (the spacer is uniform, the snap ring is triangular, the rest are normal).
- **Mean and Std Dev** — Center and spread of the simulated distribution
- **Percentiles** — Key boundaries:
  - 0.135% (≈ -3σ lower bound)
  - 2.275% (≈ -2σ)
  - 50% (median)
  - 97.725% (≈ +2σ)
  - 99.865% (≈ +3σ upper bound)

Monte Carlo is the most realistic method when your contributors have different distribution shapes.

## 5. Interpreting Results

For the bearing housing sample:

- The **nominal gap** of ~0.0470" is the preload shim space when every dimension is perfect.
- The **worst-case band** tells you the absolute range this gap could ever be. If the minimum gap goes negative, you have an interference condition — parts won't assemble.
- The **RSS band** tells you the statistically likely range assuming normal processes. This covers ~99.73% of assemblies. Use this when your manufacturing is well-controlled.
- The **Monte Carlo distribution** gives you the actual predicted shape. Because the spacer uses a uniform distribution (ground parts tend toward uniform rather than normal) and the snap ring uses triangular (stamped parts), the overall assembly distribution won't be perfectly normal. Monte Carlo captures this.

**What the percentiles mean:**

- The 0.135% to 99.865% range corresponds to ±3σ coverage — 99.73% of assemblies will fall within this range.
- If your design requirement is that the shim gap must be between 0.030" and 0.065", check whether the Monte Carlo percentile range fits within those limits.
- If the distribution tails exceed your limits, you need to tighten tolerances on the dominant contributors (the visualization shows which ones are largest).

## 6. Creating Your Own Stack-Up

### Starting a new project

Go to **File → New Project** to start fresh, or **Edit → Add Chain** to add a second chain to an existing project.

### Adding contributors

Add contributors one at a time. For each one, specify:

- **Name** — Something descriptive ("Shoulder Length", "Bearing Width", etc.)
- **Nominal** — The dimension from your drawing
- **Tolerance type:**
  - *Bilateral* — Symmetric ±, e.g., 1.500 ± 0.002
  - *Unilateral* — Asymmetric, e.g., 1.500 +0.002/-0.000
  - *Limit* — Explicit upper and lower limits, e.g., 1.498 to 1.502
- **Direction:**
  - *Positive* = this dimension adds to the gap/result
  - *Negative* = this dimension subtracts from the gap/result

Think of it like walking along the stack path. Dimensions going "with" the direction of measurement are positive. Dimensions going "against" (or defining the far boundary) are negative.

### Setting distributions

In the detail panel, set the distribution type for each contributor. This only affects Monte Carlo results:

- **Normal** — Default. Good for most machined dimensions where process capability is known.
- **Uniform** — Every value within the tolerance band is equally likely. Use for ground or lapped parts, purchased shims, or when you have no process data.
- **Triangular** — Values near nominal are more likely than extremes, but with a definite cutoff. Use for stamped parts, castings, or purchased components with limited data.

## 7. Saving and Exporting

- **File → Save** — Saves in JSON format. The file is human-readable and version-control friendly. You can open it in any text editor to inspect or hand-edit values.
- **File → Export PDF** — Generates a professional tolerance analysis report suitable for design reviews, including the stack-up table, analysis results, and distribution plots.

## 8. Tips

- **Unit switching** — Use the unit selector in the toolbar to toggle between inch and mm. All values convert automatically; your underlying data stays precise.
- **Standard mode** — Switching between ASME Y14.5, ISO GPS, and Generic affects symbols and terminology in reports and labels, but not the math.
- **Monte Carlo iterations** — 10,000 is a good default. More iterations (50,000–100,000) give smoother histograms but take longer. Fewer (1,000) are fine for quick checks during design iteration.
- **RSS ≈ Worst-Case?** — If your RSS result is nearly identical to worst-case, your stack has very few contributors. With 2–3 contributors, the RSS assumption provides little benefit — use worst-case as your design target.
- **Visualization proportions** — The bar chart shows contributor proportions at a glance. Look for which contributor dominates the total tolerance — that's where tightening tolerances gives the most return.
- **Iterate on the dominant contributor** — If your stack doesn't meet requirements, tighten the tolerance on the largest contributor first. Going from ±0.003 to ±0.002 on a dominant feature is more effective than tightening three small ones.
