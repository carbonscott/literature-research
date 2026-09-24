#!/usr/bin/env python3
"""Verify that every preprint ID cited in findings.md exists in the harvested corpus.

No network calls are made; this only reads local files.

Corpus
------
Every ``corpus/*.jsonl`` file (the ``corpus/raw/`` subfolder is ignored) is read.
Each line is one JSON record; its ``id`` field is normalized to a canonical key:

    arXiv:2510.00575v2   -> arxiv:2510.00575   (prefix lowercased, version dropped)
    doi:10.1234/ABC.def  -> doi:10.1234/abc.def (whole DOI lowercased)
    hal:hal-01234567     -> hal:hal-01234567
    osti:1234567         -> osti:1234567

Citation forms recognized in findings.md (ONLY these):

    arXiv:YYMM.NNNNN     optional version suffix vN (e.g. arXiv:2510.00575v2);
                         the "arXiv:" prefix is matched case-insensitively
    doi:10.NNNN/...      DOI suffix runs until whitespace, backtick, quote, "]" or "|"; compared lowercased
    hal:hal-NNNNNNNN     HAL identifier
    osti:NNNNNN          OSTI numeric identifier

Trailing punctuation ``) . , ; ] |`` and backticks are stripped from each match,
so "(arXiv:2510.00575)." and "`doi:10.1234/x`," are both handled. Bare IDs without
a prefix (e.g. "2510.00575" or "10.1234/x") are NOT counted as citations.

Output
------
1. Corpus summary: total records, per-server counts, per-window counts for arxiv.
2. Per-question tally of unique cited IDs under headings "## Q1" .. "## Q6".
3. Missing IDs (one per line), if any.
4. Final line: "cited IDs: N | found in corpus: M | missing: K"

Exit status is 0 if K == 0 and N > 0, otherwise 1.
"""

import argparse
import glob
import json
import os
import re
import sys
from collections import Counter

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DEFAULT_FINDINGS = os.path.join(SCRIPT_DIR, "findings.md")
DEFAULT_CORPUS_DIR = os.path.join(SCRIPT_DIR, "corpus")

TRAILING_PUNCTUATION = ").,;]|`"

# Each pattern captures the whole citation token (prefix included).
CITATION_PATTERNS = [
    re.compile(r"\barXiv:\d{4}\.\d{4,5}(?:v\d+)?", re.IGNORECASE),
    re.compile(r"\bdoi:10\.\d{4,9}/[^\s`<>\"'\]|]+", re.IGNORECASE),
    re.compile(r"\bhal:hal-\d+", re.IGNORECASE),
    re.compile(r"\bosti:\d+", re.IGNORECASE),
]

ARXIV_VERSION = re.compile(r"v\d+$", re.IGNORECASE)
QUESTION_HEADING = re.compile(r"^##\s+(Q[1-6])\b")
ANY_LEVEL2_HEADING = re.compile(r"^##\s")


def normalize_id(raw_id):
    """Return the canonical, comparison-ready form of an ID, or None if unrecognized."""
    text = raw_id.strip().rstrip(TRAILING_PUNCTUATION).lstrip("`")
    if ":" not in text:
        return None
    prefix, value = text.split(":", 1)
    prefix = prefix.lower()
    if prefix == "arxiv":
        return "arxiv:" + ARXIV_VERSION.sub("", value)
    if prefix in ("doi", "hal", "osti"):
        return prefix + ":" + value.lower()
    return None


def load_corpus(corpus_dir):
    """Read corpus/*.jsonl and return (set of canonical ids, list of records)."""
    records = []
    for path in sorted(glob.glob(os.path.join(corpus_dir, "*.jsonl"))):
        with open(path, encoding="utf-8") as handle:
            for line_number, line in enumerate(handle, start=1):
                line = line.strip()
                if not line:
                    continue
                try:
                    records.append(json.loads(line))
                except ValueError:
                    print("warning: bad JSON in %s line %d" % (path, line_number),
                          file=sys.stderr)
    corpus_ids = set()
    for record in records:
        canonical = normalize_id(str(record.get("id", "")))
        if canonical:
            corpus_ids.add(canonical)
    return corpus_ids, records


def print_corpus_summary(records):
    print("harvested corpus: %d records" % len(records))
    server_counts = Counter(record.get("server") or "unknown" for record in records)
    # Sort by count descending, then by name for a stable order.
    for server, count in sorted(server_counts.items(), key=lambda item: (-item[1], item[0])):
        print("  %s: %d" % (server, count))
    arxiv_windows = Counter(
        record.get("window") or "none" for record in records if record.get("server") == "arxiv"
    )
    print("arxiv by window: trailing=%d | preceding=%d | outside=%d" % (
        arxiv_windows["trailing"], arxiv_windows["preceding"], arxiv_windows["none"]))


def extract_citations(text):
    """Return a list of unique canonical cited IDs, in order of first appearance."""
    found = []
    seen = set()
    for pattern in CITATION_PATTERNS:
        for match in pattern.finditer(text):
            canonical = normalize_id(match.group(0))
            if canonical and canonical not in seen:
                seen.add(canonical)
                found.append((match.start(), canonical))
    found.sort()
    return [canonical for _, canonical in found]


def split_by_question(text):
    """Map "Q1".."Q6" to the text under that heading (up to the next '## ' heading)."""
    sections = {}
    current = None
    for line in text.splitlines():
        heading = QUESTION_HEADING.match(line)
        if heading:
            current = heading.group(1)
            sections.setdefault(current, [])
            continue
        if ANY_LEVEL2_HEADING.match(line):
            current = None
            continue
        if current:
            sections[current].append(line)
    return {question: "\n".join(lines) for question, lines in sections.items()}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--findings", default=DEFAULT_FINDINGS, help="path to findings.md")
    parser.add_argument("--corpus-dir", default=DEFAULT_CORPUS_DIR, help="directory of *.jsonl")
    args = parser.parse_args(argv)

    corpus_ids, records = load_corpus(args.corpus_dir)
    print_corpus_summary(records)

    if os.path.exists(args.findings):
        with open(args.findings, encoding="utf-8") as handle:
            findings_text = handle.read()
    else:
        print("warning: findings file not found: %s" % args.findings, file=sys.stderr)
        findings_text = ""

    sections = split_by_question(findings_text)
    if sections:
        print("per-question unique cited IDs:")
        for question in sorted(sections):
            print("  %s: %d" % (question, len(extract_citations(sections[question]))))

    cited = extract_citations(findings_text)
    missing = [cited_id for cited_id in cited if cited_id not in corpus_ids]
    if missing:
        print("missing from corpus:")
        for cited_id in missing:
            print("  " + cited_id)

    found_count = len(cited) - len(missing)
    print("cited IDs: %d | found in corpus: %d | missing: %d" % (
        len(cited), found_count, len(missing)))
    return 0 if (not missing and cited) else 1


if __name__ == "__main__":
    sys.exit(main())
