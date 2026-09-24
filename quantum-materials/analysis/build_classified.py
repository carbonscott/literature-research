"""
Build the per-record classification cache used by every analysis lane.

Usage:  /usr/bin/python3 build_classified.py [--workers N]

Reads quantum-materials/corpus/*.jsonl (not corpus/raw/), keeps records whose
window is "trailing" or "preceding" (all servers), classifies each one with
taxonomy.classify_record, and writes quantum-materials/analysis/classified.jsonl
with one JSON object per record:

  {id, server, window, date, month ("YYYY-MM"), primary_category,
   in_scope, scope_reason ("category" | "keyword" | null),
   clusters, primary_cluster, methods, families, taxonomy_version}

Duplicate (server, id) pairs are written once (first occurrence wins).
Re-runnable: the output file is rewritten from scratch each time.
Classification runs in a multiprocessing pool (regex matching is CPU-bound).
"""

import argparse
import glob
import json
import os
import sys
import time
from multiprocessing import Pool

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import taxonomy as tx  # noqa: E402

CORPUS_DIR = os.path.join(os.path.dirname(HERE), "corpus")
OUTPUT_PATH = os.path.join(HERE, "classified.jsonl")
KEPT_WINDOWS = ("trailing", "preceding")


def load_windowed_records():
    """Records with window trailing/preceding from corpus/*.jsonl, deduplicated."""
    records = []
    seen = set()
    for path in sorted(glob.glob(os.path.join(CORPUS_DIR, "*.jsonl"))):
        file_server = os.path.splitext(os.path.basename(path))[0]
        with open(path, encoding="utf-8") as handle:
            for line in handle:
                line = line.strip()
                if not line:
                    continue
                try:
                    record = json.loads(line)
                except ValueError:
                    continue
                if record.get("window") not in KEPT_WINDOWS:
                    continue
                record.setdefault("server", file_server)
                key = (record["server"], record.get("id"))
                if key in seen:
                    continue
                seen.add(key)
                records.append(record)
    return records


def classified_row(record):
    """One output row (dict) for a corpus record."""
    date = record.get("date") or ""
    row = {
        "id": record.get("id"),
        "server": record.get("server"),
        "window": record.get("window"),
        "date": date,
        "month": date[:7] if len(date) >= 7 else None,
        "primary_category": record.get("primary_category"),
    }
    row.update(tx.classify_record(record))
    return row


def main():
    parser = argparse.ArgumentParser(description="Build analysis/classified.jsonl")
    parser.add_argument("--workers", type=int, default=min(16, os.cpu_count() or 1))
    args = parser.parse_args()

    start = time.time()
    records = load_windowed_records()
    print("records with window trailing/preceding: %d" % len(records))

    if args.workers > 1:
        with Pool(args.workers) as pool:
            rows = pool.map(classified_row, records, chunksize=200)
    else:
        rows = [classified_row(record) for record in records]

    with open(OUTPUT_PATH, "w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")

    n_in_scope = sum(1 for row in rows if row["in_scope"])
    print("in scope: %d | taxonomy %s | %.1f s with %d workers"
          % (n_in_scope, tx.TAXONOMY_VERSION, time.time() - start, args.workers))
    print("wrote " + OUTPUT_PATH)


if __name__ == "__main__":
    main()
