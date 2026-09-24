# Corpus record schema

Each harvested server writes `corpus/<server_id>.jsonl`: UTF-8, one JSON object per line.
Only raw API caches may go under `corpus/raw/`; `verify_citations.py` ignores that folder.

## Time windows (inclusive, by submission / first-posted date; run date 2026-09-23)

| window      | from       | to         |
|-------------|------------|------------|
| `trailing`  | 2025-09-24 | 2026-09-23 |
| `preceding` | 2024-09-24 | 2025-09-23 |

## Fields

| field              | type            | notes |
|--------------------|-----------------|-------|
| `id`               | string          | Canonical prefixed ID (see below) |
| `server`           | string          | Manifest server id: `arxiv`, `chemrxiv`, `researchsquare`, `preprints_org`, `techrxiv`, `zenodo`, `hal`, `osti` |
| `title`            | string          | Plain text, whitespace-normalized, tags stripped |
| `abstract`         | string          | Plain text, whitespace-normalized, tags stripped |
| `date`             | string          | `YYYY-MM-DD`, first-posted / submitted date |
| `window`           | string or null  | `trailing`, `preceding`, or `null` if outside both |
| `authors`          | list of strings | |
| `categories`       | list of strings | May be empty |
| `primary_category` | string or null  | |
| `doi`              | string or null  | |
| `url`              | string          | Landing page |
| `matched_terms`    | list of strings | Query terms / categories that retrieved the record |
| `arxiv_id`         | string or null  | Non-arXiv records: the arXiv ID the record declares, else null |
| `extra`            | object          | Optional, free-form |

## Canonical `id` forms

| source            | form                   | example |
|-------------------|------------------------|---------|
| arXiv             | `arXiv:YYMM.NNNNN`     | `arXiv:2510.00575` (no version suffix) |
| DOI-based servers | `doi:<lowercased DOI>` | `doi:10.26434/chemrxiv-2025-abc12` |
| HAL               | `hal:hal-XXXXXXXX`     | `hal:hal-04567890` |
| OSTI              | `osti:<number>`        | `osti:2345678` |

## Citation forms in findings.md

`verify_citations.py` recognizes only these forms:

- `arXiv:YYMM.NNNNN`, optionally with a version (`arXiv:2510.00575v2`); the version is dropped
  and the prefix is matched case-insensitively.
- `doi:10.NNNN/...`; compared lowercased.
- `hal:hal-NNNNNNNN`
- `osti:NNNNNN`

Trailing `) . , ; ] |` and backticks are stripped. Bare IDs without a prefix are not counted.
Each cited ID must equal the canonical `id` of some record in `corpus/*.jsonl`
(a record's `doi` or `arxiv_id` field does not count as a match).
