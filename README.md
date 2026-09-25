# Literature research

Evidence-backed surveys of research fronts, built from preprint servers.
Each topic lives in its own folder.

Site: https://carbonscott.github.io/literature-research/

## Topics

| Folder | Report | Summary page |
|---|---|---|
| `quantum-materials/` | [findings.md](quantum-materials/findings.md) | [findings.html](https://carbonscott.github.io/literature-research/quantum-materials/findings.html) |
| `agents-in-science-workflow/` | The summary page is the report; see [README.md](agents-in-science-workflow/README.md) | [findings.html](https://carbonscott.github.io/literature-research/agents-in-science-workflow/findings.html) |

## Layout of a topic folder (`quantum-materials/`)

| Path | What it holds |
|---|---|
| `findings.md` | The written report: answers to the six questions, with every cited preprint ID |
| `findings.html` | Interactive summary page (generated; do not edit by hand) |
| `report/` | `build_report.py` and `template.html`, which generate `findings.html` from `findings.md` and `analysis/*.json` |
| `harvest/` | Harvest scripts for arXiv, Crossref-prefix servers (ChemRxiv, Research Square, Preprints.org, TechRxiv) and native APIs (Zenodo, HAL, OSTI) |
| `analysis/` | Taxonomy, classification cache, and the momentum, materials, methods, beyond-arXiv and noise analyses |
| `notes/` | Per-question notes and the independent audit reports (`notes/audit/`) |
| `corpus/` | Only `SCHEMA.md` and the harvest logs are published (see below) |
| `verify_citations.py` | Checks every ID cited in `findings.md` against the harvested corpus |
| `.goal/` | The goal contract, iteration ledger and claims file that drove the campaign |

The shared server manifest is `.externals/preprint_servers.json`.

## The corpus is not in the repository

The harvested corpus (about 290 MB) is not published. It is large, and many
abstracts carry the licenses of their source servers. To rebuild it, run the
harvest scripts. They respect each server's rate limits, and the arXiv harvest
takes about 10 minutes:

```bash
python3 quantum-materials/harvest/harvest_arxiv.py
python3 quantum-materials/harvest/harvest_crossref.py
python3 quantum-materials/harvest/harvest_native.py
python3 quantum-materials/verify_citations.py
```

A rebuilt corpus can differ slightly from the original run of 2026-09-23,
because servers update their records.

## Rebuilding the summary page

```bash
python3 quantum-materials/report/build_report.py
```

The builder runs `verify_citations.py` to fill in the citation-check section,
so it needs the corpus.
