#!/usr/bin/env python3
"""Harvest arXiv metadata for the quantum-materials corpus.

Step 1 (harvest): for each category and calendar-month slice of
2024-09-24 .. 2026-09-23, query the arXiv API
(cat:<CAT> AND submittedDate:[...]) and cache each page of raw Atom XML
under corpus/raw/arxiv/. Cached pages are skipped on re-run (resumable).
Each page is validated against opensearch:totalResults; short/empty pages
are retried with backoff.

Step 2 (merge): parse all cached pages, dedupe by arXiv ID (version
stripped), and write corpus/arxiv.jsonl plus corpus/arxiv_harvest_log.json.

Usage:
    python3 harvest_arxiv.py            # harvest (resumable) then merge
    python3 harvest_arxiv.py --merge-only

Single-threaded, >= 3.1 s sleep between every request (arXiv API terms).
"""

import datetime
import json
import os
import re
import sys
import time

import requests
from lxml import etree

API_URL = "https://export.arxiv.org/api/query"
USER_AGENT = "qm-preprint-landscape/0.1 (non-commercial literature survey)"
CATEGORIES = [
    "cond-mat.str-el",
    "cond-mat.supr-con",
    "cond-mat.mes-hall",
    "cond-mat.mtrl-sci",
]
SPAN_START = datetime.date(2024, 9, 24)
SPAN_END = datetime.date(2026, 9, 23)
WINDOWS = {
    "trailing": (datetime.date(2025, 9, 24), datetime.date(2026, 9, 23)),
    "preceding": (datetime.date(2024, 9, 24), datetime.date(2025, 9, 23)),
}
PAGE_SIZE = 1000
SLEEP_BETWEEN_REQUESTS = 3.1
RETRY_BACKOFFS = [10, 30, 60, 120]  # up to 4 retries after the first try

NS = {
    "atom": "http://www.w3.org/2005/Atom",
    "opensearch": "http://a9.com/-/spec/opensearch/1.1/",
    "arxiv": "http://arxiv.org/schemas/atom",
}

QM_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CORPUS_DIR = os.path.join(QM_DIR, "corpus")
RAW_DIR = os.path.join(CORPUS_DIR, "raw", "arxiv")
OUT_JSONL = os.path.join(CORPUS_DIR, "arxiv.jsonl")
OUT_LOG = os.path.join(CORPUS_DIR, "arxiv_harvest_log.json")
STATUS_FILE = os.path.join(RAW_DIR, "_slice_status.json")

_last_request_time = [0.0]


def log(msg):
    stamp = datetime.datetime.now().strftime("%H:%M:%S")
    print("[%s] %s" % (stamp, msg), flush=True)


# ---------------------------------------------------------------- slices

def month_slices(start, end):
    """Return list of (slice_start, slice_end) calendar-month slices."""
    slices = []
    current = start
    while current <= end:
        if current.month == 12:
            next_month = datetime.date(current.year + 1, 1, 1)
        else:
            next_month = datetime.date(current.year, current.month + 1, 1)
        slice_end = min(next_month - datetime.timedelta(days=1), end)
        slices.append((current, slice_end))
        current = next_month
    return slices


def slice_label(slice_start, slice_end):
    return "%s_%s" % (slice_start.strftime("%Y%m%d"), slice_end.strftime("%Y%m%d"))


def cache_path(category, label, start_index):
    name = "%s__%s__start%05d.xml" % (category, label, start_index)
    return os.path.join(RAW_DIR, name)


# ---------------------------------------------------------------- HTTP

def polite_get(params):
    """GET the arXiv API, sleeping so requests are >= 3.1 s apart."""
    wait = SLEEP_BETWEEN_REQUESTS - (time.time() - _last_request_time[0])
    if wait > 0:
        time.sleep(wait)
    try:
        response = requests.get(
            API_URL, params=params, headers={"User-Agent": USER_AGENT}, timeout=120
        )
        return response
    finally:
        _last_request_time[0] = time.time()


def parse_feed(xml_bytes):
    """Return (totalResults, list of entry elements) from Atom XML bytes."""
    root = etree.fromstring(xml_bytes)
    total_text = root.findtext("opensearch:totalResults", namespaces=NS)
    total = int(total_text) if total_text is not None else None
    entries = root.findall("atom:entry", NS)
    # arXiv returns an <entry> with id .../api/errors on query errors
    real_entries = []
    for entry in entries:
        entry_id = entry.findtext("atom:id", default="", namespaces=NS)
        if "/api/errors" in entry_id:
            raise ValueError("arXiv API error entry: %s" %
                             entry.findtext("atom:summary", namespaces=NS))
        real_entries.append(entry)
    return total, real_entries


def fetch_page(category, slice_start, slice_end, start_index):
    """Fetch one page with retries. Returns (xml_bytes, total, n_entries, ok)."""
    query = "cat:%s AND submittedDate:[%s0000 TO %s2359]" % (
        category, slice_start.strftime("%Y%m%d"), slice_end.strftime("%Y%m%d"))
    params = {
        "search_query": query,
        "sortBy": "submittedDate",
        "sortOrder": "ascending",
        "start": start_index,
        "max_results": PAGE_SIZE,
    }
    last = (None, None, 0, False)
    for attempt in range(len(RETRY_BACKOFFS) + 1):
        if attempt > 0:
            backoff = RETRY_BACKOFFS[attempt - 1]
            log("  retry %d for %s %s start=%d after %d s" % (
                attempt, category, slice_label(slice_start, slice_end), start_index, backoff))
            time.sleep(backoff)
        try:
            response = polite_get(params)
            if response.status_code != 200:
                log("  HTTP %d" % response.status_code)
                continue
            total, entries = parse_feed(response.content)
        except Exception as exc:  # network or XML problem -> retry
            log("  error: %r" % (exc,))
            continue
        if total is None:
            log("  missing totalResults")
            continue
        expected = max(0, min(PAGE_SIZE, total - start_index))
        last = (response.content, total, len(entries), False)
        # A total of 0 for a full month of these categories is almost surely
        # a transient glitch, so treat it as a failure worth retrying.
        if total == 0:
            log("  totalResults=0 (suspicious)")
            continue
        if len(entries) == expected:
            return response.content, total, len(entries), True
        log("  short page: got %d entries, expected %d (total %d)" % (
            len(entries), expected, total))
    return last


# ---------------------------------------------------------------- harvest

def load_status():
    if os.path.exists(STATUS_FILE):
        with open(STATUS_FILE) as handle:
            return json.load(handle)
    return {}


def save_status(status):
    tmp = STATUS_FILE + ".tmp"
    with open(tmp, "w") as handle:
        json.dump(status, handle, indent=1, sort_keys=True)
    os.replace(tmp, STATUS_FILE)


def write_bytes(path, data):
    tmp = path + ".tmp"
    with open(tmp, "wb") as handle:
        handle.write(data)
    os.replace(tmp, path)


def harvest_slice(category, slice_start, slice_end):
    """Harvest all pages of one (category, slice). Returns status dict."""
    label = slice_label(slice_start, slice_end)
    start_index = 0
    total = None
    pages_ok = True
    while True:
        path = cache_path(category, label, start_index)
        if os.path.exists(path):
            with open(path, "rb") as handle:
                page_total, entries = parse_feed(handle.read())
            n_entries = len(entries)
        else:
            data, page_total, n_entries, ok = fetch_page(
                category, slice_start, slice_end, start_index)
            if data is None:
                log("  FAILED %s %s start=%d (no usable response)" % (category, label, start_index))
                return {"totalResults": total, "complete": False}
            if ok:
                write_bytes(path, data)
            else:
                # keep the best attempt for inspection, but under a name that
                # is not treated as a valid cache on re-run
                write_bytes(path.replace(".xml", ".unreconciled.xml"), data)
                pages_ok = False
            log("  %s %s start=%d total=%d entries=%d ok=%s" % (
                category, label, start_index, page_total, n_entries, ok))
        if total is None:
            total = page_total
        elif page_total != total:
            log("  totalResults changed across pages (%d -> %d)" % (total, page_total))
            total = max(total, page_total)
        start_index += PAGE_SIZE
        if start_index >= total or not pages_ok:
            break
    return {"totalResults": total, "complete": pages_ok}


def run_harvest():
    os.makedirs(RAW_DIR, exist_ok=True)
    status = load_status()
    for slice_start, slice_end in month_slices(SPAN_START, SPAN_END):
        label = slice_label(slice_start, slice_end)
        for category in CATEGORIES:
            key = "%s|%s" % (category, label)
            if status.get(key, {}).get("complete"):
                continue
            log("harvesting %s" % key)
            status[key] = harvest_slice(category, slice_start, slice_end)
            save_status(status)


# ---------------------------------------------------------------- merge

def clean_text(text):
    if not text:
        return ""
    text = re.sub(r"<[^>]+>", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def strip_version(arxiv_id):
    return re.sub(r"v\d+$", "", arxiv_id)


def window_for(date_str):
    date = datetime.datetime.strptime(date_str, "%Y-%m-%d").date()
    for name, (lo, hi) in WINDOWS.items():
        if lo <= date <= hi:
            return name
    return None


def entry_to_record(entry, category):
    raw_id = entry.findtext("atom:id", default="", namespaces=NS)
    bare_id = strip_version(raw_id.split("/abs/")[-1])
    published = entry.findtext("atom:published", default="", namespaces=NS)
    date = published[:10]
    primary = entry.find("arxiv:primary_category", NS)
    categories = []
    for cat in entry.findall("atom:category", NS):
        term = cat.get("term")
        if term and term not in categories:
            categories.append(term)
    doi = entry.findtext("arxiv:doi", namespaces=NS)
    return {
        "id": "arXiv:" + bare_id,
        "server": "arxiv",
        "title": clean_text(entry.findtext("atom:title", namespaces=NS)),
        "abstract": clean_text(entry.findtext("atom:summary", namespaces=NS)),
        "date": date,
        "window": window_for(date),
        "authors": [clean_text(a.findtext("atom:name", namespaces=NS))
                    for a in entry.findall("atom:author", NS)],
        "categories": categories,
        "primary_category": primary.get("term") if primary is not None else None,
        "doi": doi.strip() if doi else None,
        "url": "https://arxiv.org/abs/" + bare_id,
        "matched_terms": [category],
        "arxiv_id": bare_id,
        "extra": {
            "comment": clean_text(entry.findtext("arxiv:comment", namespaces=NS)) or None,
            "journal_ref": clean_text(entry.findtext("arxiv:journal_ref", namespaces=NS)) or None,
            "updated": entry.findtext("atom:updated", namespaces=NS),
            "version_seen": raw_id.split("/abs/")[-1],
        },
    }


def run_merge():
    records = {}
    slice_log = []
    status = load_status()
    raw_per_category_window = {}
    for slice_start, slice_end in month_slices(SPAN_START, SPAN_END):
        label = slice_label(slice_start, slice_end)
        for category in CATEGORIES:
            key = "%s|%s" % (category, label)
            total = status.get(key, {}).get("totalResults")
            parsed = 0
            ids_in_slice = set()
            start_index = 0
            while True:
                path = cache_path(category, label, start_index)
                if not os.path.exists(path):
                    break
                with open(path, "rb") as handle:
                    page_total, entries = parse_feed(handle.read())
                if total is None:
                    total = page_total
                for entry in entries:
                    record = entry_to_record(entry, category)
                    parsed += 1
                    ids_in_slice.add(record["id"])
                    bucket = raw_per_category_window.setdefault(category, {})
                    w = str(record["window"])
                    bucket[w] = bucket.get(w, 0) + 1
                    existing = records.get(record["id"])
                    if existing is None:
                        records[record["id"]] = record
                    elif category not in existing["matched_terms"]:
                        existing["matched_terms"].append(category)
                start_index += PAGE_SIZE
                if total is None or start_index >= total:
                    break
            reconciled = total is not None and total > 0 and parsed == total
            slice_log.append({
                "category": category,
                "slice": label,
                "totalResults": total,
                "parsed": parsed,
                "unique_ids": len(ids_in_slice),
                "reconciled": reconciled,
            })
            if not reconciled:
                log("UNRECONCILED %s: total=%s parsed=%d" % (key, total, parsed))

    ordered = sorted(records.values(), key=lambda r: (r["date"], r["id"]))
    tmp = OUT_JSONL + ".tmp"
    with open(tmp, "w", encoding="utf-8") as handle:
        for record in ordered:
            handle.write(json.dumps(record, ensure_ascii=False) + "\n")
    os.replace(tmp, OUT_JSONL)

    unique_per_window = {}
    unique_per_primary = {}
    for record in ordered:
        w = str(record["window"])
        unique_per_window[w] = unique_per_window.get(w, 0) + 1
        p = str(record["primary_category"])
        unique_per_primary[p] = unique_per_primary.get(p, 0) + 1
    raw_per_window = {}
    for per_window in raw_per_category_window.values():
        for w, n in per_window.items():
            raw_per_window[w] = raw_per_window.get(w, 0) + n
    summary = {
        "generated": datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
        "api": API_URL,
        "categories": CATEGORIES,
        "span": [SPAN_START.isoformat(), SPAN_END.isoformat()],
        "windows": {k: [v[0].isoformat(), v[1].isoformat()] for k, v in WINDOWS.items()},
        "slices": slice_log,
        "unreconciled_slices": [s["category"] + "|" + s["slice"]
                                for s in slice_log if not s["reconciled"]],
        "raw_entries_per_window": raw_per_window,
        "raw_entries_per_category_per_window": raw_per_category_window,
        "unique_ids_total": len(ordered),
        "unique_ids_per_window": unique_per_window,
        "unique_ids_per_primary_category": unique_per_primary,
    }
    with open(OUT_LOG, "w") as handle:
        json.dump(summary, handle, indent=1)
    log("merge done: %d unique records; per window %s; unreconciled %d" % (
        len(ordered), unique_per_window, len(summary["unreconciled_slices"])))


def main():
    if "--merge-only" not in sys.argv:
        run_harvest()
    run_merge()


if __name__ == "__main__":
    main()
