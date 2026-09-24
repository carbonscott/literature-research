"""
Draw the deterministic precision-audit sample for taxonomy v2.

Usage:  /usr/bin/python3 sample_precision_audit.py [--cluster KEY] [--abstract]

For every cluster: sorted ids of trailing-window arXiv records whose
primary_cluster is that cluster (from analysis/classified.jsonl), then
random.Random(42).sample(ids, 15). Prints id, title and all cluster labels
so a human can judge each item. Verdicts are recorded by hand in
analysis/precision_audit_v2.json.
"""

import argparse
import json
import os
import random
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import taxonomy as tx  # noqa: E402

CLASSIFIED_PATH = os.path.join(HERE, "classified.jsonl")
ARXIV_PATH = os.path.join(os.path.dirname(HERE), "corpus", "arxiv.jsonl")
SAMPLE_SIZE = 15
SEED = 42


def audit_sample(rows, cluster_key):
    """Deterministic sample of trailing arXiv ids whose primary is cluster_key."""
    ids = sorted(row["id"] for row in rows
                 if row["server"] == "arxiv" and row["window"] == "trailing"
                 and row["primary_cluster"] == cluster_key)
    rng = random.Random(SEED)
    if len(ids) <= SAMPLE_SIZE:
        return ids
    return rng.sample(ids, SAMPLE_SIZE)


def load_rows():
    with open(CLASSIFIED_PATH, encoding="utf-8") as handle:
        return [json.loads(line) for line in handle]


def load_arxiv_text():
    texts = {}
    with open(ARXIV_PATH, encoding="utf-8") as handle:
        for line in handle:
            record = json.loads(line)
            texts[record["id"]] = (tx.record_title(record), tx.normalize_text(record.get("abstract")))
    return texts


def main():
    parser = argparse.ArgumentParser(description="Print the precision-audit sample")
    parser.add_argument("--cluster", default=None)
    parser.add_argument("--abstract", action="store_true")
    args = parser.parse_args()

    rows = load_rows()
    rows_by_id = dict((row["id"], row) for row in rows if row["server"] == "arxiv")
    texts = load_arxiv_text()
    keys = [args.cluster] if args.cluster else tx.CLUSTER_KEYS
    for key in keys:
        print("=" * 30, key, "|", tx.CLUSTER_LABELS[key])
        for record_id in audit_sample(rows, key):
            title, abstract = texts[record_id]
            print("%s | %s | %s" % (record_id, title, ",".join(rows_by_id[record_id]["clusters"])))
            if args.abstract:
                print("      " + abstract[:400])


if __name__ == "__main__":
    main()
