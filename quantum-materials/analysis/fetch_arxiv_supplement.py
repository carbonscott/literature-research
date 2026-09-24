#!/usr/bin/env python3
"""Fetch specific arXiv papers (by ID) that the category harvest missed.

Used for Q6 (noise / contested claims): some papers in a contested-claim thread
are older than the survey span, or are cross-listed outside the four harvested
categories. They are looked up with the arXiv API `id_list` parameter only.

Rules (from the task brief):
  * id_list lookups only, single-threaded, >= 3.1 s between requests,
    at most MAX_REQUESTS requests per run;
  * records are appended to corpus/arxiv_supplement.jsonl with the normal
    corpus schema, server "arxiv", window from the date (or null),
    extra.supplement = true;
  * IDs already present in corpus/arxiv.jsonl or arxiv_supplement.jsonl are skipped.

Raw API responses are cached under corpus/raw/arxiv_supplement/.

Usage:  python3 analysis/fetch_arxiv_supplement.py 2409.13504 2510.03256 ...
"""

import datetime
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
QM_DIR = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(QM_DIR, "harvest"))

import harvest_arxiv  # noqa: E402  (reuses polite_get, parse_feed, entry_to_record)

CORPUS_DIR = os.path.join(QM_DIR, "corpus")
MAIN_JSONL = os.path.join(CORPUS_DIR, "arxiv.jsonl")
SUPPLEMENT_JSONL = os.path.join(CORPUS_DIR, "arxiv_supplement.jsonl")
RAW_DIR = os.path.join(CORPUS_DIR, "raw", "arxiv_supplement")

IDS_PER_REQUEST = 20
MAX_REQUESTS = 10


def known_ids():
    """Canonical ids already in the main arXiv file or the supplement."""
    ids = set()
    for path in (MAIN_JSONL, SUPPLEMENT_JSONL):
        if not os.path.exists(path):
            continue
        with open(path) as handle:
            for line in handle:
                ids.add(json.loads(line)["id"])
    return ids


def fetch_batch(batch, request_number):
    """One id_list request; returns list of corpus records."""
    params = {"id_list": ",".join(batch), "max_results": len(batch)}
    response = harvest_arxiv.polite_get(params)
    response.raise_for_status()
    stamp = datetime.datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
    raw_path = os.path.join(RAW_DIR, "id_list_%s_%02d.xml" % (stamp, request_number))
    with open(raw_path, "wb") as handle:
        handle.write(response.content)
    _, entries = harvest_arxiv.parse_feed(response.content)
    records = []
    for entry in entries:
        record = harvest_arxiv.entry_to_record(entry, "supplement:id_list")
        record["matched_terms"] = ["supplement:id_list"]
        record["extra"]["supplement"] = True
        records.append(record)
    return records


def main(requested):
    os.makedirs(RAW_DIR, exist_ok=True)
    existing = known_ids()
    todo = [i for i in requested if "arXiv:" + i not in existing]
    skipped = [i for i in requested if "arXiv:" + i in existing]
    if skipped:
        print("already in corpus, skipped: %s" % ", ".join(skipped))
    batches = [todo[k:k + IDS_PER_REQUEST] for k in range(0, len(todo), IDS_PER_REQUEST)]
    if len(batches) > MAX_REQUESTS:
        sys.exit("refusing: %d requests needed, limit is %d" % (len(batches), MAX_REQUESTS))
    added = 0
    with open(SUPPLEMENT_JSONL, "a") as out:
        for number, batch in enumerate(batches, 1):
            for record in fetch_batch(batch, number):
                if record["id"] in existing:
                    continue
                existing.add(record["id"])
                out.write(json.dumps(record, ensure_ascii=False) + "\n")
                added += 1
                print("added %s %s %s | %s" % (
                    record["id"], record["date"], record["window"], record["title"][:80]))
    print("requests: %d | added: %d" % (len(batches), added))


if __name__ == "__main__":
    main(sys.argv[1:])
