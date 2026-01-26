# BioBucks - Biotech DCF Valuation Tool

A Claude Code skill that generates comprehensive, research-backed DCF (Discounted Cash Flow) inputs for biotech asset valuation using AI-powered web research, with a simple web viewer.

## What is This?

This tool combines:
1. **Claude Code Skill** (`/biobucks`): AI-powered research and parameter generation
2. **Simple Web Viewer**: Self-contained HTML interface with Python server (no build step!)

When activated, Claude will:
1. Gather details about your biotech asset (drug name, indication, development phase, etc.)
2. Research 13 categories of parameters using live web search:
   - Market size, pricing, and adoption curves
   - Clinical trial costs and timelines
   - Probability of success by phase
   - Financial parameters (COGS, OpEx, WACC, tax rates)
3. Output a comprehensive **JSON file** with all DCF inputs, including:
   - Every parameter value with units
   - Source citations with URLs
   - Explanations justifying each assumption
   - Confidence levels (High/Medium/Low)
4. Save the JSON to `valuations/` directory for viewing in the web interface

## Quick Start

### 1. Generate a Valuation

Use the `/biobucks` skill in Claude Code:

```bash
/biobucks
```

Then provide details about the biotech asset. The skill will research parameters and save a JSON file to `valuations/`.

### 2. View Valuations

Start the web viewer:

```bash
python3 server.py
```

Open your browser to: **http://localhost:8000**

## Installation

### For This Project Only (Project Skill)

The skill is already included in this repository at `.claude/skills/biobucks/SKILL.md`.

If you're using Claude Code in this directory, the skill will be automatically available.

### For All Your Projects (Personal Skill)

To use this skill across all projects:

1. Copy the skill directory to your personal Claude skills folder:
   ```bash
   mkdir -p ~/.claude/skills
   cp -r .claude/skills/biobucks ~/.claude/skills/
   ```

2. The skill will now be available in any directory when using Claude Code.
