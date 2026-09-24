#!/usr/bin/env python3
"""Find arXiv-DOI (10.48550) versions of papers by title via OpenAlex (use sparingly).
Usage: python3 openalex_title.py "title one" "title two" ...
"""
import sys
import time
import requests

HEADERS = {"User-Agent": "qm-preprint-landscape/0.1 (non-commercial literature survey)"}
for title in sys.argv[1:]:
    clean = title.replace(",", " ").replace(":", " ")
    response = requests.get("https://api.openalex.org/works", headers=HEADERS, timeout=30,
                            params={"filter": "title.search:" + clean, "per-page": 8,
                                    "select": "doi,title,publication_date,cited_by_count"})
    print("==", title, response.status_code)
    for work in response.json().get("results", []):
        print("   ", work.get("doi"), work.get("publication_date"), work.get("cited_by_count"), work.get("title")[:100])
    time.sleep(2)
