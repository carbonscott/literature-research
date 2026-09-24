#!/usr/bin/env python3
"""Print a short summary of findings.md (stdlib only).

(a) The Q1 cluster table: cluster, trailing primary count, Q2 trend, Q3 families.
(b) For each of Q1..Q6: its Headline, Counts and Key IDs lines, plus the
    extra labelled lines in EXTRA_LABELS (Q1 Scope, Q6 Noise filter).

A "line" for any label is the bold label line plus any bullet lines
directly under it (some sections list the values as bullets).

Usage: python3 print_findings_summary.py [path/to/findings.md]
"""

import os
import re
import sys

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DEFAULT_FINDINGS = os.path.join(SCRIPT_DIR, "findings.md")

QUESTION_HEADING = re.compile(r"^##\s+(Q[1-6])\b.*$")
LEVEL2_HEADING = re.compile(r"^##\s")
FIELD_LABELS = ["Headline", "Counts", "Key IDs"]
# Extra labelled lines printed for some questions, placed after the Headline.
EXTRA_LABELS = {"Q1": ["Scope"], "Q6": ["Noise filter"]}


def split_sections(lines):
    """Return {"Q1": [lines...], ...} for each '## Qn' section."""
    sections = {}
    current = None
    for line in lines:
        match = QUESTION_HEADING.match(line)
        if match:
            current = match.group(1)
            sections[current] = []
        elif LEVEL2_HEADING.match(line):
            current = None
        elif current is not None:
            sections[current].append(line)
    return sections


def table_cells(line):
    """Split a markdown table row into stripped cell strings."""
    return [cell.strip() for cell in line.strip().strip("|").split("|")]


def q1_cluster_rows(q1_lines):
    """Return dict rows from the first Q1 table whose header starts with 'Cluster'."""
    rows = []
    header = None
    for line in q1_lines:
        if not line.startswith("|"):
            if header is not None:
                break  # the table has ended
            continue
        cells = table_cells(line)
        if header is None:
            if cells and cells[0] == "Cluster":
                header = cells
            continue
        if set(line.replace("|", "").strip()) <= set("-: "):
            continue  # separator row
        rows.append(dict(zip(header, cells)))
    return rows


def field_block(section_lines, label):
    """Return the '**label:**' line plus the bullet lines that follow it."""
    prefix = "**" + label + ":**"
    for index, line in enumerate(section_lines):
        if line.startswith(prefix):
            block = [line.rstrip()]
            for follow in section_lines[index + 1:]:
                if follow.lstrip().startswith("- "):
                    block.append(follow.rstrip())
                else:
                    break
            return block
    return ["(" + label + " not found)"]


def main():
    path = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_FINDINGS
    with open(path, encoding="utf-8") as handle:
        lines = handle.read().splitlines()
    sections = split_sections(lines)

    print("== (a) Q1 cluster table ==")
    print("cluster | trailing count | Q2 trend | Q3 families")
    for row in q1_cluster_rows(sections.get("Q1", [])):
        print("{} | {} | {} | {}".format(
            row.get("Cluster", ""),
            row.get("Trailing 12 mo (primary)", ""),
            row.get("Q2 trend", ""),
            row.get("Q3 leading material families", ""),
        ))

    print()
    print("== (b) Headline / Counts / Key IDs per question (+ Q1 Scope, Q6 Noise filter) ==")
    for question in ["Q1", "Q2", "Q3", "Q4", "Q5", "Q6"]:
        print("--- " + question + " ---")
        section_lines = sections.get(question)
        if section_lines is None:
            print("(section missing)")
            continue
        labels = FIELD_LABELS[:1] + EXTRA_LABELS.get(question, []) + FIELD_LABELS[1:]
        for label in labels:
            for line in field_block(section_lines, label):
                print(line)


if __name__ == "__main__":
    main()
