# Secure Charts Directory

This directory stores sensitive chart data in isolated chart folders.

## Naming Rules

### Client charts
Use:
CLIENT-<identifier>

Examples:
- CLIENT-C001
- CLIENT-CHRISTINA01

### Non-person, anonymous, or event charts
Use:
CHART-YYYY-MM-DD_HHMM

Examples:
- CHART-1975-04-04_0225
- CHART-2026-03-26_1315

## Standard Files Per Chart Folder
- raw_export.txt
- normalized_chart.json
- chapter8.md
- full_analysis.md
- notes.md

## Security
All chart folders should remain permission-restricted to the owner only.
