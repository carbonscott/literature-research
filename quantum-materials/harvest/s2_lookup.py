#!/usr/bin/env python3
"""Slow Semantic Scholar title-search helper for the contested-claims scout.

Usage:  python3 s2_lookup.py queries.txt  (one search query per line)
Raw responses are cached under corpus/raw/s2_contested/<slug>.json.
Prints one line per hit: query | arXiv id | year | venue | citations | title
"""
import json
import os
import re
import sys
import time

import requests

HERE = os.path.dirname(os.path.abspath(__file__))
CACHE_DIR = os.path.join(HERE, "..", "corpus", "raw", "s2_contested")
URL = "https://api.semanticscholar.org/graph/v1/paper/search"
FIELDS = "title,externalIds,year,venue,citationCount,publicationDate"
HEADERS = {"User-Agent": "qm-preprint-landscape/0.1 (non-commercial literature survey)"}
PAUSE_SECONDS = 4
MAX_TRIES = 7


def slugify(text):
    return re.sub(r"[^a-z0-9]+", "_", text.lower()).strip("_")[:120]


def search(query, limit=6):
    cache_path = os.path.join(CACHE_DIR, slugify(query) + ".json")
    if os.path.exists(cache_path):
        with open(cache_path) as handle:
            return json.load(handle)
    wait = 8
    for _ in range(MAX_TRIES):
        response = requests.get(URL, headers=HEADERS, timeout=30,
                                params={"query": query, "fields": FIELDS, "limit": limit})
        if response.status_code == 200:
            data = response.json()
            with open(cache_path, "w") as handle:
                json.dump(data, handle)
            time.sleep(PAUSE_SECONDS)
            return data
        time.sleep(wait)
        wait = min(wait * 2, 90)
    return {"data": [], "error": "gave up after retries"}


def main():
    os.makedirs(CACHE_DIR, exist_ok=True)
    with open(sys.argv[1]) as handle:
        queries = [line.strip() for line in handle if line.strip()]
    for query in queries:
        result = search(query)
        if result.get("error"):
            print("%s | ERROR %s" % (query, result["error"]), flush=True)
        for paper in result.get("data", []) or []:
            ids = paper.get("externalIds") or {}
            print("%s | %s | %s | %s | %s | %s | %s" % (
                query[:40], ids.get("ArXiv"), paper.get("publicationDate") or paper.get("year"),
                (paper.get("venue") or "")[:30], paper.get("citationCount"),
                ids.get("DOI"), paper.get("title")), flush=True)


if __name__ == "__main__":
    main()
