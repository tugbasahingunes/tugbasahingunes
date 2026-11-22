# Project Operations Toolkit: Virtual Assistant & Project Management

**Service:** virtual assistance · project coordination · Excel / Google Sheets trackers · reporting automation · SOPs

**Client problem:** "Our projects live in e-mail threads. Nobody knows what's late until it's too late, and writing the weekly update takes an hour."

| File | What it does |
|---|---|
| [`project_tracker.xlsx`](project_tracker.xlsx) | **Tracker** with a live **Gantt chart** (pure conditional formatting: planned, completed and today markers), automatic health flags (✔ done / ⚠ late / ● behind / ○ on track), overall progress and overdue counter · **RACI** matrix · **Risk register** with likelihood × impact scoring · **Actions** log |
| [`status_report.py`](status_report.py) | Reads the tracker and writes the weekly status e-mail: health (🟢/🟡/🔴 vs plan), late and behind tasks, what starts next week, top risks. Example: [`status_20261215.md`](status_20261215.md) |
| [`SOP_client_onboarding.md`](SOP_client_onboarding.md) | Standard operating procedure: 7 steps, tools, "done when" criteria, quality checks |
| [`build_tracker.py`](build_tracker.py) | Regenerates the workbook |

No macros, so the tracker works in Excel and Google Sheets. Also available as a Notion or Trello set-up.

```bash
python build_tracker.py
python status_report.py 2026-12-15
```
