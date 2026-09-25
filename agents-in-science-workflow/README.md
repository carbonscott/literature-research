# AI agents in scientific workflows

A landscape survey for a discussion with DOE x-ray and neutron facility
scientists (SLAC, ORNL, BNL) and university collaborators. Run date: 2026-09-25.

The deliverable is `findings.html`: a self-contained page that answers six
questions (landscape, what works, infrastructure, facilities, risks, discussion
prompts), with a system catalog, a glossary, method notes and a numbered,
machine-checked reference list.

## Layout

| Path | What it holds |
|---|---|
| `findings.html` | The report (generated; do not edit by hand) |
| `check_report.py` | Independent checker: structure, self-containment, and live resolution of every reference (Crossref / doi.org, arXiv API, URL fetch) with title matching |
| `report/parts/*.html` | Report text, one fragment per section; citations are written `[@key]` |
| `report/merge_notes.py` | Merges the research lanes' references and catalog rows into `report/refs.json` and `report/catalog.json` |
| `report/assemble_source.py` | Joins the parts into `report/source.html` |
| `report/build_report.py`, `report/template.html` | Build `findings.html` (numbered citations, taxonomy table, catalog, reference list) |
| `report/apply_edits.py` | Applies audited text edits and catalog changes from `notes/*.json` |
| `notes/` | Research-lane notes (`q1`–`q5`), lane references and catalog rows, and the audit and review files |
| `.goal/` | The goal contract, iteration ledger and claims file that drove the campaign |

## Rebuild and check

From the repository root. The scripts use only the Python standard library but
need Python 3.7 or newer (`build_report.py` and `check_report.py` fail on 3.6).
If `python` is missing or older on your system, call a specific interpreter,
such as `python3.12`:

```bash
python agents-in-science-workflow/report/merge_notes.py
python agents-in-science-workflow/report/assemble_source.py
python agents-in-science-workflow/report/build_report.py
python agents-in-science-workflow/check_report.py            # add --offline to skip network checks
```

`check_report.py` makes about 170 network requests (arXiv IDs are batched) and
respects each server's rate limits; a full run takes about two minutes.
