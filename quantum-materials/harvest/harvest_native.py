#!/usr/bin/env python3
"""Harvest quantum-materials records from Zenodo, HAL and OSTI native APIs.

Step 1 (harvest): for each server and query term, page through the server's
search API restricted to 2024-09-24 .. 2026-09-23 and cache each raw JSON
page under corpus/raw/<server>/<term_slug>/page_NNNN.json. Cached pages are
reused on re-run (resumable). At most 2000 records per (server, term) are
fetched; truncation is logged.

  - Zenodo: preprints only (type=publication&subtype=preprint). Unauthenticated
    page size is capped at 25 by Zenodo, and the rate limit is 30 req/min, so
    requests are spaced 2.2 s apart. The subtype filter is also re-checked
    client-side on metadata.resource_type.
  - HAL: preprints only (docType_s:UNDEFINED), cursorMark paging, sort=docid asc.
  - OSTI: all product types (product_type is kept in extra), dates in
    MM/DD/YYYY as documented at https://www.osti.gov/api/v1/docs.

Step 2 (merge): parse all cached pages, apply the phrase filter (term must
appear in title or abstract; case-insensitive, hyphen/space and diacritic
variants), dedupe within server, and write corpus/zenodo.jsonl, hal.jsonl,
osti.jsonl and corpus/native_harvest_log.json.

Usage:
    python3 harvest_native.py                 # harvest (resumable), merge, summary
    python3 harvest_native.py --merge-only    # merge + summary from cache
    python3 harvest_native.py --servers hal   # restrict to some servers
"""

import argparse
import collections
import datetime
import html
import json
import os
import re
import sys
import time
import unicodedata

import requests
import lxml.html

USER_AGENT = "qm-preprint-landscape/0.1 (non-commercial literature survey)"
HEADERS = {"User-Agent": USER_AGENT, "Accept": "application/json"}

SPAN_START = datetime.date(2024, 9, 24)
SPAN_END = datetime.date(2026, 9, 23)
WINDOWS = {
    "trailing": (datetime.date(2025, 9, 24), datetime.date(2026, 9, 23)),
    "preceding": (datetime.date(2024, 9, 24), datetime.date(2025, 9, 23)),
}
CAP_PER_TERM = 2000
RETRY_BACKOFFS = [10, 30, 60, 120]

QUERY_TERMS = [
    "superconductivity", "superconductor", "topological insulator",
    "topological semimetal", "Weyl semimetal", "quantum spin liquid",
    "altermagnet", "kagome", "moire", "twisted bilayer graphene",
    "quantum anomalous Hall", "Majorana", "heavy fermion",
    "charge density wave", "van der Waals magnet", "nickelate", "cuprate",
    "excitonic insulator", "multiferroic", "skyrmion", "quantum material",
    "strongly correlated", "flat band", "Mott insulator",
]

# Extra query strings sent to the API for a term (diacritic spelling). Results
# are credited to the base term. Only used where the API may not fold accents.
QUERY_SPELLINGS = {"moire": ["moire", "moiré"]}

SERVERS = ["zenodo", "hal", "osti"]
SLEEP_SECONDS = {"zenodo": 2.2, "hal": 1.1, "osti": 1.1}
PAGE_SIZE = {"zenodo": 25, "hal": 500, "osti": 100}

QM_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CORPUS_DIR = os.path.join(QM_DIR, "corpus")
RAW_ROOT = os.path.join(CORPUS_DIR, "raw")
OUT_LOG = os.path.join(CORPUS_DIR, "native_harvest_log.json")

ARXIV_NEW_RE = re.compile(r"(\d{4}\.\d{4,5})(v\d+)?")
ARXIV_OLD_RE = re.compile(r"([a-z\-]+(?:\.[A-Z]{2})?/\d{7})(v\d+)?")


# ---------------------------------------------------------------- utilities

def log(msg):
    print(time.strftime("%H:%M:%S"), msg, flush=True)


def slugify(text):
    return re.sub(r"[^a-z0-9]+", "_", strip_accents(text).lower()).strip("_")


def strip_accents(text):
    decomposed = unicodedata.normalize("NFKD", text)
    return "".join(ch for ch in decomposed if not unicodedata.combining(ch))


def clean_text(value):
    """Join lists, strip HTML tags/entities, normalize whitespace."""
    if value is None:
        return ""
    if isinstance(value, list):
        value = " ".join(str(v) for v in value if v)
    value = str(value)
    if "<" in value and ">" in value:
        try:
            value = lxml.html.fromstring("<div>" + value + "</div>").text_content()
        except Exception:
            value = re.sub(r"<[^>]+>", " ", value)
    value = html.unescape(value)
    return re.sub(r"\s+", " ", value).strip()


def window_for(date_str):
    if not date_str:
        return None
    try:
        day = datetime.datetime.strptime(date_str, "%Y-%m-%d").date()
    except ValueError:
        return None
    for name, (start, end) in WINDOWS.items():
        if start <= day <= end:
            return name
    return None


def normalize_arxiv_id(text):
    """Return a bare arXiv id (no version) found in text, else None."""
    if not text:
        return None
    text = str(text).strip()
    text = re.sub(r"(?i)^(arxiv:|https?://arxiv\.org/(abs|pdf)/|10\.48550/arxiv\.)", "", text)
    match = ARXIV_NEW_RE.search(text)
    if match:
        return match.group(1)
    match = ARXIV_OLD_RE.search(text)
    if match:
        return match.group(1)
    return None


# ------------------------------------------------------------ phrase filter

def normalize_for_match(text):
    """Lowercase, drop diacritics, turn hyphens/dashes into spaces."""
    text = strip_accents(text).lower()
    text = re.sub(r"[\-‐-―_/]", " ", text)
    return re.sub(r"\s+", " ", text)


def build_term_pattern(term):
    """Word-start anchored regex; words may be joined by space, hyphen or nothing."""
    words = normalize_for_match(term).split()
    body = r"\s?".join(re.escape(w) for w in words)
    return re.compile(r"(?<![a-z0-9])" + body)


TERM_PATTERNS = dict((term, build_term_pattern(term)) for term in QUERY_TERMS)


def phrase_matches(term, title, abstract):
    haystack = normalize_for_match(title + " " + abstract)
    return TERM_PATTERNS[term].search(haystack) is not None


# ------------------------------------------------------------------ HTTP

def http_get_json(server, url, params):
    """GET with retries/backoff. Returns (json_body, headers)."""
    attempts = [0] + RETRY_BACKOFFS
    last_error = None
    for wait in attempts:
        if wait:
            log("  retry in %ds (%s)" % (wait, last_error))
            time.sleep(wait)
        try:
            resp = requests.get(url, params=params, headers=HEADERS, timeout=120)
            time.sleep(SLEEP_SECONDS[server])
            if resp.status_code == 200:
                return resp.json(), dict(resp.headers)
            last_error = "HTTP %d: %s" % (resp.status_code, resp.text[:200])
            if resp.status_code in (400, 404):
                break
        except (requests.RequestException, ValueError) as exc:
            time.sleep(SLEEP_SECONDS[server])
            last_error = repr(exc)
    raise RuntimeError("%s request failed: %s" % (server, last_error))


def write_json_atomic(path, data):
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as fh:
        json.dump(data, fh, ensure_ascii=False)
    os.replace(tmp, path)


# -------------------------------------------------------- per-server fetch
# Each fetch_* function pages one (server, query string) into raw_dir and
# returns nothing; pages are cached as {"params":..., "total":..., "items":[...], ...}.

def fetch_zenodo(query, raw_dir):
    q = '"%s" AND publication_date:[%s TO %s]' % (query, SPAN_START.isoformat(), SPAN_END.isoformat())
    size = PAGE_SIZE["zenodo"]
    max_pages = (CAP_PER_TERM + size - 1) // size
    page = 1
    while page <= max_pages:
        path = os.path.join(raw_dir, "page_%04d.json" % page)
        if os.path.exists(path):
            with open(path, encoding="utf-8") as fh:
                cached = json.load(fh)
        else:
            params = {"q": q, "type": "publication", "subtype": "preprint",
                      "size": size, "page": page, "sort": "mostrecent"}
            body, _ = http_get_json("zenodo", "https://zenodo.org/api/records", params)
            cached = {"params": params, "total": body["hits"]["total"],
                      "items": body["hits"]["hits"]}
            write_json_atomic(path, cached)
        if len(cached["items"]) < size or page * size >= cached["total"]:
            break
        page += 1


def fetch_hal(query, raw_dir):
    fl = ("halId_s,title_s,abstract_s,submittedDate_s,producedDate_s,"
          "authFullName_s,domain_s,arxivId_s,doiId_s,uri_s")
    rows = PAGE_SIZE["hal"]
    max_pages = (CAP_PER_TERM + rows - 1) // rows
    cursor = "*"
    for page in range(1, max_pages + 1):
        path = os.path.join(raw_dir, "page_%04d.json" % page)
        if os.path.exists(path):
            with open(path, encoding="utf-8") as fh:
                cached = json.load(fh)
        else:
            params = [
                ("q", '"%s"' % query),
                ("fq", "docType_s:UNDEFINED"),
                ("fq", "submittedDate_tdate:[%sT00:00:00Z TO %sT23:59:59Z]"
                 % (SPAN_START.isoformat(), SPAN_END.isoformat())),
                ("fl", fl), ("rows", rows), ("wt", "json"),
                ("sort", "docid asc"), ("cursorMark", cursor),
            ]
            body, _ = http_get_json("hal", "https://api.archives-ouvertes.fr/search/", params)
            cached = {"params": params, "total": body["response"]["numFound"],
                      "items": body["response"]["docs"],
                      "cursor": cursor, "next_cursor": body.get("nextCursorMark")}
            write_json_atomic(path, cached)
        next_cursor = cached.get("next_cursor")
        if not cached["items"] or not next_cursor or next_cursor == cursor:
            break
        if page * rows >= cached["total"]:
            break
        cursor = next_cursor


def fetch_osti(query, raw_dir):
    rows = PAGE_SIZE["osti"]
    max_pages = (CAP_PER_TERM + rows - 1) // rows
    for page in range(1, max_pages + 1):
        path = os.path.join(raw_dir, "page_%04d.json" % page)
        if os.path.exists(path):
            with open(path, encoding="utf-8") as fh:
                cached = json.load(fh)
        else:
            params = {"q": '"%s"' % query,
                      "publication_date_start": SPAN_START.strftime("%m/%d/%Y"),
                      "publication_date_end": SPAN_END.strftime("%m/%d/%Y"),
                      "rows": rows, "page": page}
            body, headers = http_get_json("osti", "https://www.osti.gov/api/v1/records", params)
            total = int(headers.get("X-Total-Count", headers.get("x-total-count", "0")) or 0)
            cached = {"params": params, "total": total, "items": body}
            write_json_atomic(path, cached)
        if len(cached["items"]) < rows or page * rows >= cached["total"]:
            break


FETCHERS = {"zenodo": fetch_zenodo, "hal": fetch_hal, "osti": fetch_osti}


def query_strings(term):
    return QUERY_SPELLINGS.get(term, [term])


def raw_dir_for(server, query):
    return os.path.join(RAW_ROOT, server, slugify(query) + ("_accent" if query != strip_accents(query) else ""))


def harvest(servers):
    for server in servers:
        for term in QUERY_TERMS:
            for query in query_strings(term):
                raw_dir = raw_dir_for(server, query)
                done_flag = os.path.join(raw_dir, "_done")
                if os.path.exists(done_flag):
                    continue
                os.makedirs(raw_dir, exist_ok=True)
                log("%s | %s" % (server, query))
                FETCHERS[server](query, raw_dir)
                open(done_flag, "w").close()


def load_pages(server, query):
    raw_dir = raw_dir_for(server, query)
    if not os.path.isdir(raw_dir):
        return None, []
    total = None
    items = []
    for name in sorted(os.listdir(raw_dir)):
        if not name.startswith("page_"):
            continue
        with open(os.path.join(raw_dir, name), encoding="utf-8") as fh:
            page = json.load(fh)
        if total is None:
            total = page["total"]
        items.extend(page["items"])
    return total, items


# ------------------------------------------------------ record conversion

def zenodo_arxiv_id(meta):
    for ident in meta.get("alternate_identifiers") or []:
        scheme = (ident.get("scheme") or "").lower()
        value = ident.get("identifier") or ""
        if scheme == "arxiv" or value.lower().startswith("arxiv:") or "arxiv.org" in value.lower():
            found = normalize_arxiv_id(value)
            if found:
                return found
    for ident in meta.get("related_identifiers") or []:
        scheme = (ident.get("scheme") or "").lower()
        value = ident.get("identifier") or ""
        relation = (ident.get("relation") or "").lower()
        # Only identity-type relations say "this record IS the arXiv paper".
        if relation not in ("isidenticalto", "isversionof", "isalternateidentifier",
                            "ispreviousversionof", "isnewversionof", "haspart", "ispartof",
                            "isvariantformof", "isoriginalformof"):
            continue
        if scheme == "arxiv" or "arxiv" in value.lower():
            found = normalize_arxiv_id(value)
            if found:
                return found
    return None


def convert_zenodo(item):
    meta = item.get("metadata", {})
    resource = meta.get("resource_type") or {}
    if resource.get("subtype") != "preprint":
        return None  # client-side check of the subtype filter
    doi = ("10.5281/zenodo.%s" % item["id"]).lower()
    record_doi = (item.get("doi") or meta.get("doi") or "").lower() or None
    publication_date = meta.get("publication_date") or ""
    date = publication_date[:10]
    if not re.match(r"^\d{4}-\d{2}-\d{2}$", date):
        # Partial dates ("2025", "2025-11") fall back to the upload date.
        date = (item.get("created") or "")[:10]
    return {
        "id": "doi:" + doi,
        "server": "zenodo",
        "title": clean_text(meta.get("title")),
        "abstract": clean_text(meta.get("description")),
        "date": date,
        "window": window_for(date),
        "authors": [c.get("name", "") for c in meta.get("creators") or []],
        "categories": [],
        "primary_category": None,
        "doi": record_doi or doi,
        "url": (item.get("links") or {}).get("self_html") or "https://zenodo.org/records/%s" % item["id"],
        "matched_terms": [],
        "arxiv_id": zenodo_arxiv_id(meta),
        "extra": {
            "zenodo_recid": item["id"],
            "conceptrecid": item.get("conceptrecid"),
            "created": (item.get("created") or "")[:10],
            "keywords": meta.get("keywords") or [],
            "communities": [c.get("id") for c in meta.get("communities") or []],
            "publication_date": publication_date,
            "date_note": "date = metadata.publication_date (user-declared) if a full YYYY-MM-DD, else upload date",
        },
    }


def convert_hal(item):
    hal_id = item.get("halId_s")
    if not hal_id:
        return None
    date = (item.get("submittedDate_s") or "")[:10]
    domains = item.get("domain_s") or []
    arxiv_id = normalize_arxiv_id(item.get("arxivId_s"))
    doi = (item.get("doiId_s") or "").lower() or None
    if not arxiv_id and doi and doi.startswith("10.48550/arxiv."):
        arxiv_id = normalize_arxiv_id(doi)
    return {
        "id": "hal:" + hal_id,
        "server": "hal",
        "title": clean_text(item.get("title_s")),
        "abstract": clean_text(item.get("abstract_s")),
        "date": date,
        "window": window_for(date),
        "authors": item.get("authFullName_s") or [],
        "categories": domains,
        "primary_category": domains[-1] if domains else None,
        "doi": doi,
        "url": item.get("uri_s") or "https://hal.science/" + hal_id,
        "matched_terms": [],
        "arxiv_id": arxiv_id,
        "extra": {"producedDate": item.get("producedDate_s")},
    }


def osti_arxiv_id(item):
    candidates = [item.get("doi") or ""]
    for key in ("other_identifiers", "report_number"):
        value = item.get(key)
        if isinstance(value, list):
            candidates.extend(value)
        elif value:
            candidates.append(value)
    for value in candidates:
        if "arxiv" in str(value).lower():
            found = normalize_arxiv_id(value)
            if found:
                return found
    return None


def convert_osti(item):
    osti_id = item.get("osti_id")
    if not osti_id:
        return None
    date = (item.get("publication_date") or "")[:10]
    subjects = item.get("subjects") or []
    categories = [s for s in subjects if re.match(r"^\d{2} ", s)]
    keywords = [s for s in subjects if s not in categories]
    url = "https://www.osti.gov/biblio/%s" % osti_id
    for link in item.get("links") or []:
        if link.get("rel") == "citation":
            url = link.get("href")
    return {
        "id": "osti:%s" % osti_id,
        "server": "osti",
        "title": clean_text(item.get("title")),
        "abstract": clean_text(item.get("description")),
        "date": date,
        "window": window_for(date),
        "authors": [re.sub(r"\s*\[.*$", "", a).strip() for a in item.get("authors") or []],
        "categories": categories,
        "primary_category": categories[0] if categories else None,
        "doi": (item.get("doi") or "").lower() or None,
        "url": url,
        "matched_terms": [],
        "arxiv_id": osti_arxiv_id(item),
        "extra": {
            "product_type": item.get("product_type"),
            "article_type": item.get("article_type"),
            "journal_name": item.get("journal_name"),
            "entry_date": (item.get("entry_date") or "")[:10],
            "keywords": keywords,
            "research_orgs": item.get("research_orgs") or [],
            "sponsor_orgs": item.get("sponsor_orgs") or [],
        },
    }


CONVERTERS = {"zenodo": convert_zenodo, "hal": convert_hal, "osti": convert_osti}


# ------------------------------------------------------------------ merge

def merge(servers):
    if os.path.exists(OUT_LOG):
        with open(OUT_LOG, encoding="utf-8") as fh:
            full_log = json.load(fh)
    else:
        full_log = {}
    full_log["generated"] = datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
    full_log["span"] = [SPAN_START.isoformat(), SPAN_END.isoformat()]
    full_log["cap_per_term"] = CAP_PER_TERM
    full_log.setdefault("servers", {})

    for server in servers:
        records = collections.OrderedDict()
        term_log = []
        for term in QUERY_TERMS:
            entry = {"term": term, "queries": [], "api_total": 0, "fetched": 0,
                     "kept": 0, "truncated": False, "dropped_not_preprint": 0}
            kept_ids = set()
            for query in query_strings(term):
                total, items = load_pages(server, query)
                if total is None:
                    entry["queries"].append({"query": query, "status": "not harvested"})
                    continue
                truncated = total > len(items) and len(items) >= CAP_PER_TERM
                entry["queries"].append({"query": query, "api_total": total,
                                         "fetched": len(items), "truncated": truncated})
                entry["api_total"] += total
                entry["fetched"] += len(items)
                entry["truncated"] = entry["truncated"] or truncated
                for item in items:
                    record = CONVERTERS[server](item)
                    if record is None:
                        entry["dropped_not_preprint"] += 1
                        continue
                    if not phrase_matches(term, record["title"], record["abstract"]):
                        continue
                    kept_ids.add(record["id"])
                    if record["id"] not in records:
                        records[record["id"]] = record
                    if term not in records[record["id"]]["matched_terms"]:
                        records[record["id"]]["matched_terms"].append(term)
            entry["kept"] = len(kept_ids)
            if entry["truncated"]:
                log("TRUNCATED %s | %s: api_total=%d fetched=%d"
                    % (server, term, entry["api_total"], entry["fetched"]))
            term_log.append(entry)

        unique = list(records.values())
        if server == "zenodo":
            unique = collapse_zenodo_versions(unique)
        unique.sort(key=lambda r: (r["date"], r["id"]))

        out_path = os.path.join(CORPUS_DIR, "%s.jsonl" % server)
        with open(out_path + ".tmp", "w", encoding="utf-8") as fh:
            for record in unique:
                fh.write(json.dumps(record, ensure_ascii=False) + "\n")
        os.replace(out_path + ".tmp", out_path)

        full_log["servers"][server] = {
            "unique_kept": len(unique),
            "per_window": dict(collections.Counter(str(r["window"]) for r in unique)),
            "with_arxiv_id": sum(1 for r in unique if r["arxiv_id"]),
            "terms": term_log,
        }
        log("wrote %s (%d records)" % (out_path, len(unique)))

    write_json_atomic(OUT_LOG, full_log)
    return full_log


def collapse_zenodo_versions(records):
    """Keep one record per Zenodo concept (highest record id); merge matched_terms."""
    by_concept = collections.OrderedDict()
    for record in records:
        key = record["extra"].get("conceptrecid") or record["id"]
        current = by_concept.get(key)
        if current is None:
            by_concept[key] = record
            continue
        terms = current["matched_terms"] + [t for t in record["matched_terms"]
                                            if t not in current["matched_terms"]]
        if record["extra"]["zenodo_recid"] > current["extra"]["zenodo_recid"]:
            by_concept[key] = record
        by_concept[key]["matched_terms"] = terms
    return list(by_concept.values())


# ---------------------------------------------------------------- summary

def summarize(servers):
    for server in servers:
        path = os.path.join(CORPUS_DIR, "%s.jsonl" % server)
        if not os.path.exists(path):
            continue
        with open(path, encoding="utf-8") as fh:
            records = [json.loads(line) for line in fh]
        print("\n=== %s: %d unique kept ===" % (server, len(records)))
        for window in ("trailing", "preceding", None):
            subset = [r for r in records if r["window"] == window]
            if not subset:
                continue
            with_arxiv = sum(1 for r in subset if r["arxiv_id"])
            print("  window=%-9s n=%5d  with arxiv_id=%4d (%.1f%%)"
                  % (window, len(subset), with_arxiv, 100.0 * with_arxiv / len(subset)))
        term_counts = collections.Counter(t for r in records for t in r["matched_terms"])
        print("  top terms:", ", ".join("%s=%d" % kv for kv in term_counts.most_common(8)))
        if server == "osti":
            types = collections.Counter(r["extra"].get("product_type") for r in records)
            print("  product_type:", dict(types.most_common()))
        for record in [r for r in records if r["window"] == "trailing"][-3:]:
            print("  e.g. [%s] %s  (%s)" % (record["date"], record["title"][:110], record["id"]))


def main():
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--merge-only", action="store_true")
    parser.add_argument("--servers", nargs="+", default=SERVERS, choices=SERVERS)
    args = parser.parse_args()
    if not args.merge_only:
        harvest(args.servers)
    merge(args.servers)
    summarize(args.servers)


if __name__ == "__main__":
    sys.exit(main())
