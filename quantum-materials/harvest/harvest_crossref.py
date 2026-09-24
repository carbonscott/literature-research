#!/usr/bin/env python3
"""Harvest quantum-materials preprints from Crossref DOI prefixes.

Servers: chemrxiv (10.26434), researchsquare (10.21203),
preprints_org (10.20944), techrxiv (10.36227).

Steps
  1. For each (server, query term): query Crossref /prefixes/<p>/works with
     cursor paging, capped at MAX_RESULTS_PER_TERM results.  Every page is
     cached (gzip JSON) under corpus/raw/crossref/ so re-runs are resumable:
     a (server, term) pair with a "done" marker is read from cache.
  2. Phrase filter: keep a record only if the term appears in title/abstract.
  3. Collapse versions to one record per base work.  If a base work's v1
     was not retrieved (e.g. v1 posted before the window), look v1 up by DOI
     so the "first posted" date is correct.
  4. Write corpus/<server>.jsonl and corpus/crossref_harvest_log.json.

Python 3.6, stdlib + requests only.
Usage:  python3 harvest_crossref.py [--servers chemrxiv,techrxiv]
"""
import argparse
import datetime
import gzip
import html
import json
import os
import re
import sys
import time
import unicodedata

import requests

# ---------------------------------------------------------------- config ---
QM_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CORPUS_DIR = os.path.join(QM_DIR, "corpus")
RAW_DIR = os.path.join(CORPUS_DIR, "raw", "crossref")
LOG_PATH = os.path.join(CORPUS_DIR, "crossref_harvest_log.json")

USER_AGENT = "qm-preprint-landscape/0.1 (non-commercial literature survey)"
API = "https://api.crossref.org"
MIN_SECONDS_BETWEEN_REQUESTS = 1.1   # public pool: <= 1 request / second
ROWS = 500
MAX_RESULTS_PER_TERM = 2000

FROM_DATE = "2024-09-24"
UNTIL_DATE = "2026-09-23"
WINDOWS = [
    ("trailing", "2025-09-24", "2026-09-23"),
    ("preceding", "2024-09-24", "2025-09-23"),
]

SERVERS = [
    ("chemrxiv", "10.26434"),
    ("researchsquare", "10.21203"),
    ("preprints_org", "10.20944"),
    ("techrxiv", "10.36227"),
]

QUERY_TERMS = [
    "superconductivity", "superconductor", "topological insulator",
    "topological semimetal", "Weyl semimetal", "quantum spin liquid",
    "altermagnet", "kagome", "moire", "twisted bilayer graphene",
    "quantum anomalous Hall", "Majorana", "heavy fermion",
    "charge density wave", "van der Waals magnet", "nickelate", "cuprate",
    "excitonic insulator", "multiferroic", "skyrmion", "quantum material",
    "strongly correlated", "flat band", "Mott insulator",
]


# Crossref search does not fold accents ("moire" -> 0 hits, "moiré" -> hits),
# so some terms are sent as several query strings and the results are merged.
QUERY_VARIANTS = {
    "moire": ["moire", "moiré"],
}


def log(msg):
    stamp = datetime.datetime.now().strftime("%H:%M:%S")
    print("[%s] %s" % (stamp, msg), flush=True)


# ------------------------------------------------------------------ HTTP ---
class CrossrefClient(object):
    """Sequential, rate-limited Crossref client with simple retries."""

    def __init__(self):
        self.session = requests.Session()
        self.session.headers["User-Agent"] = USER_AGENT
        self.last_request_time = 0.0
        self.request_count = 0

    def get_json(self, url, params=None, max_tries=6):
        for attempt in range(1, max_tries + 1):
            wait = MIN_SECONDS_BETWEEN_REQUESTS - (time.time() - self.last_request_time)
            if wait > 0:
                time.sleep(wait)
            self.last_request_time = time.time()
            self.request_count += 1
            try:
                resp = self.session.get(url, params=params, timeout=180)
            except requests.RequestException as exc:
                log("  request error (%s), attempt %d" % (exc, attempt))
                time.sleep(10 * attempt)
                continue
            if resp.status_code == 200:
                return resp.json()
            if resp.status_code == 404:
                return None
            if resp.status_code in (429, 500, 502, 503, 504):
                retry_after = resp.headers.get("Retry-After")
                pause = int(retry_after) if (retry_after or "").isdigit() else 15 * attempt
                log("  HTTP %d, sleeping %ds (attempt %d)" % (resp.status_code, pause, attempt))
                time.sleep(pause)
                continue
            raise RuntimeError("HTTP %d for %s: %s" % (resp.status_code, resp.url, resp.text[:300]))
        raise RuntimeError("giving up on %s after %d tries" % (url, max_tries))


# ----------------------------------------------------------------- cache ---
def slugify(text):
    text = unicodedata.normalize("NFKD", text)
    text = "".join(ch for ch in text if not unicodedata.combining(ch))
    return re.sub(r"[^a-z0-9]+", "_", text.lower()).strip("_")


def write_gz_json(path, obj):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    tmp = path + ".tmp"
    with gzip.open(tmp, "wt", encoding="utf-8") as fh:
        json.dump(obj, fh)
    os.replace(tmp, path)


def read_gz_json(path):
    with gzip.open(path, "rt", encoding="utf-8") as fh:
        return json.load(fh)


def fetch_term(client, server_id, prefix, term):
    """Return (items, stats) for one (server, term), using the cache if complete."""
    # Keep accented variants in their own cache dir ("moiré" -> "moire_accented").
    slug = slugify(term)
    if any(ord(ch) > 127 for ch in term):
        slug += "_accented"
    term_dir = os.path.join(RAW_DIR, server_id, slug)
    done_path = os.path.join(term_dir, "done.json")
    if os.path.exists(done_path):
        stats = json.load(open(done_path))
        items = []
        for page_index in range(stats["pages"]):
            page = read_gz_json(os.path.join(term_dir, "page_%03d.json.gz" % page_index))
            items.extend(page["message"]["items"])
        return items, stats

    url = "%s/prefixes/%s/works" % (API, prefix)
    params = {
        "filter": "type:posted-content,from-posted-date:%s,until-posted-date:%s" % (FROM_DATE, UNTIL_DATE),
        "query.bibliographic": term,
        "rows": ROWS,
        "cursor": "*",
    }
    items = []
    total_results = None
    page_index = 0
    while True:
        data = client.get_json(url, params=params)
        message = data["message"]
        if total_results is None:
            total_results = message["total-results"]
        page_items = message["items"]
        # Trim the last page so we never exceed the cap.
        room = MAX_RESULTS_PER_TERM - len(items)
        if len(page_items) > room:
            message["items"] = page_items = page_items[:room]
        write_gz_json(os.path.join(term_dir, "page_%03d.json.gz" % page_index), data)
        page_index += 1
        items.extend(page_items)
        next_cursor = message.get("next-cursor")
        if not page_items or len(items) >= MAX_RESULTS_PER_TERM or len(items) >= total_results or not next_cursor:
            break
        params["cursor"] = next_cursor

    truncated = total_results > len(items) and len(items) >= MAX_RESULTS_PER_TERM
    stats = {
        "server": server_id,
        "term": term,
        "total_results": total_results,
        "fetched": len(items),
        "pages": page_index,
        "truncated_by_cap": truncated,
        "fetched_at": datetime.datetime.utcnow().isoformat() + "Z",
    }
    with open(done_path, "w") as fh:
        json.dump(stats, fh)
    return items, stats


def fetch_single_work(client, doi):
    """Look up one DOI (cached). Returns the Crossref work dict or None."""
    path = os.path.join(RAW_DIR, "works", slugify(doi) + ".json.gz")
    if os.path.exists(path):
        cached = read_gz_json(path)
        return cached.get("message")
    data = client.get_json("%s/works/%s" % (API, doi))
    write_gz_json(path, data if data else {"message": None})
    return data["message"] if data else None


# -------------------------------------------------------------- parsing ---
def strip_tags(text):
    """Remove JATS/HTML tags, unescape entities, normalize whitespace."""
    if not text:
        return ""
    # Drop the leading "<jats:title>Abstract</jats:title>" style headings.
    text = re.sub(r"<(jats:)?title[^>]*>.*?</(jats:)?title>", " ", text, flags=re.S)
    # Sub/superscripts join their neighbours without a space (TaSe<sub>2</sub> -> TaSe2).
    text = re.sub(r"</?(jats:)?(sub|sup)\b[^>]*>", "", text, flags=re.I)
    text = re.sub(r"&lt;/?(sub|sup)&gt;", "", text, flags=re.I)
    text = re.sub(r"<[^>]+>", " ", text)
    # Some deposits entity-escape their markup (&lt;sub&gt;), so unescape and strip again.
    text = html.unescape(text)
    text = re.sub(r"</?(sub|sup|i|b|em|strong|italic|bold|scp|p|br|span)\b[^>]*>", " ", text, flags=re.I)
    text = html.unescape(text)
    return re.sub(r"\s+", " ", text).strip()


def normalize_for_matching(text):
    """Lowercase, strip accents (moiré -> moire), hyphens -> spaces."""
    text = unicodedata.normalize("NFKD", text)
    text = "".join(ch for ch in text if not unicodedata.combining(ch))
    text = text.lower()
    text = re.sub(r"[\-‐-―_]", " ", text)
    return re.sub(r"\s+", " ", text)


def build_term_pattern(term):
    """Phrase regex: words may be joined by a space, hyphen, or nothing.

    Leading word boundary only, so plurals / suffixes still match
    (cuprate -> cuprates, altermagnet -> altermagnetism).
    """
    words = normalize_for_matching(term).split()
    return re.compile(r"\b" + r" ?".join(re.escape(w) for w in words))


TERM_PATTERNS = dict((term, build_term_pattern(term)) for term in QUERY_TERMS)


def date_from_parts(date_obj):
    if not date_obj or not date_obj.get("date-parts") or not date_obj["date-parts"][0]:
        return None
    parts = date_obj["date-parts"][0]
    if parts[0] is None:
        return None
    year = parts[0]
    month = parts[1] if len(parts) > 1 else 1
    day = parts[2] if len(parts) > 2 else 1
    return "%04d-%02d-%02d" % (year, month, day)


def window_for(date):
    if not date:
        return None
    for name, start, end in WINDOWS:
        if start <= date <= end:
            return name
    return None


# Version suffixes seen on each server's DOIs.
#   researchsquare: 10.21203/rs.3.rs-1234567/v2
#   preprints_org : 10.20944/preprints202410.1234.v2
#   chemrxiv      : 10.26434/chemrxiv-2024-abc12-v2  or  10.26434/chemrxiv.15000484/v2
#   techrxiv      : 10.36227/techrxiv.176472696.64455714/v1
VERSION_SUFFIX = re.compile(r"(?P<sep>[/.\-])v(?P<num>\d+)$")


def split_version(doi):
    """Return (base_doi, version_number or None, separator)."""
    match = VERSION_SUFFIX.search(doi)
    if not match:
        return doi, None, None
    return doi[:match.start()], int(match.group("num")), match.group("sep")


ARXIV_IN_TEXT = re.compile(r"arxiv[:\s]*(\d{4}\.\d{4,5})", re.I)
ARXIV_DOI = re.compile(r"10\.48550/arxiv\.(\d{4}\.\d{4,5})", re.I)


def find_arxiv_id(relation, abstract):
    for rel_list in (relation or {}).values():
        for rel in rel_list:
            rel_id = str(rel.get("id", ""))
            match = ARXIV_DOI.search(rel_id)
            if match:
                return "arXiv:" + match.group(1)
            if rel.get("id-type", "").lower() == "arxiv":
                match = re.search(r"(\d{4}\.\d{4,5})", rel_id)
                if match:
                    return "arXiv:" + match.group(1)
    match = ARXIV_IN_TEXT.search(abstract or "")
    if match:
        return "arXiv:" + match.group(1)
    return None


def format_authors(item):
    names = []
    for author in item.get("author", []) or []:
        if author.get("given") or author.get("family"):
            names.append(" ".join(p for p in (author.get("given"), author.get("family")) if p))
        elif author.get("name"):
            names.append(author["name"])
    return names


def parse_item(item):
    """Crossref work -> flat version-level record."""
    doi = item["DOI"].lower()
    title = strip_tags(" ".join(item.get("title") or []))
    abstract = strip_tags(item.get("abstract"))
    posted = date_from_parts(item.get("posted"))
    created = date_from_parts(item.get("created"))
    url = (((item.get("resource") or {}).get("primary") or {}).get("URL")) or item.get("URL")
    return {
        "doi": doi,
        "title": title,
        "abstract": abstract,
        "date": posted or created,
        "date_source": "posted" if posted else "created",
        "authors": format_authors(item),
        "subjects": item.get("subject") or [],
        "url": url,
        "relation": item.get("relation") or {},
        "institution": [inst.get("name") for inst in (item.get("institution") or []) if inst.get("name")],
        "group_title": item.get("group-title"),
        "publisher": item.get("publisher"),
        "subtype": item.get("subtype"),
    }


def phrase_match(term, record):
    text = normalize_for_matching(record["title"] + " " + record["abstract"])
    return TERM_PATTERNS[term].search(text) is not None


# -------------------------------------------------------------- merging ---
def merge_versions(client, server_id, versions_by_base, matched_terms_by_base):
    """Collapse version-level records into one corpus record per base work."""
    records = []
    v1_lookups = 0
    for base, versions in sorted(versions_by_base.items()):
        # versions: dict doi -> (version_number, sep, parsed_record)
        # An unsuffixed DOI in a versioned group (old ChemRxiv style
        # "chemrxiv-2022-abcde" + "chemrxiv-2022-abcde-v2") is the first version.
        for doi, (num, sep_, rec) in list(versions.items()):
            if num is None and len(versions) > 1:
                versions[doi] = (1, sep_, rec)
        version_numbers = [v[0] for v in versions.values() if v[0] is not None]
        sep = next((v[1] for v in versions.values() if v[1]), None)

        # If versioned but v1 was not retrieved, fetch v1 by DOI to get the
        # true first-posted date (v1 may predate the query window).
        if version_numbers and 1 not in version_numbers:
            candidates = [base + sep + "v1"]
            if sep == "-":
                candidates.append(base)   # old ChemRxiv: v1 has no suffix
            for v1_doi in candidates:
                work = fetch_single_work(client, v1_doi)
                v1_lookups += 1
                if work:
                    versions[v1_doi.lower()] = (1, sep, parse_item(work))
                    break

        ordered = sorted(versions.items(), key=lambda kv: ((kv[1][2]["date"] or "9999"), kv[1][0] or 0))
        earliest_date = ordered[0][1][2]["date"]
        v1_entry = [kv for kv in ordered if kv[1][0] == 1]
        chosen_doi, (chosen_num, _, chosen) = v1_entry[0] if v1_entry else ordered[0]
        # Use the most recent version's text if it is richer (e.g. v1 lacks abstract).
        latest = sorted(versions.values(), key=lambda v: v[0] or 0)[-1][2]
        title = chosen["title"] or latest["title"]
        abstract = chosen["abstract"] or latest["abstract"]

        relation = {}
        for _, (_, _, rec) in ordered:
            for key, rel_list in rec["relation"].items():
                existing = relation.setdefault(key, [])
                for rel in rel_list:
                    if rel not in existing:
                        existing.append(rel)
        institutions = []
        for _, (_, _, rec) in ordered:
            for name in rec["institution"]:
                if name not in institutions:
                    institutions.append(name)
        subjects = []
        for _, (_, _, rec) in ordered:
            for s in rec["subjects"]:
                if s not in subjects:
                    subjects.append(s)

        version_list = [
            {"doi": doi, "version": num, "date": rec["date"], "date_source": rec["date_source"]}
            for doi, (num, _, rec) in sorted(versions.items(), key=lambda kv: kv[1][0] or 0)
        ]
        records.append({
            "id": "doi:" + chosen_doi,
            "server": server_id,
            "title": title,
            "abstract": abstract,
            "date": earliest_date,
            "window": window_for(earliest_date),
            "authors": chosen["authors"] or latest["authors"],
            "categories": subjects,
            "primary_category": None,
            "doi": chosen_doi,
            "url": chosen["url"],
            "matched_terms": [t for t in QUERY_TERMS if t in matched_terms_by_base[base]],
            "arxiv_id": find_arxiv_id(relation, abstract),
            "extra": {
                "base_doi": base,
                "versions": version_list,
                "relation": relation,
                "is_preprint_of": [r.get("id") for r in relation.get("is-preprint-of", [])],
                "institution": institutions,
                "group_title": latest["group_title"] or chosen["group_title"],
                "publisher": chosen["publisher"],
                "date_source": ordered[0][1][2]["date_source"],
            },
        })
    return records, v1_lookups


# ----------------------------------------------------------------- main ---
def harvest_server(client, server_id, prefix, term_stats):
    versions_by_base = {}        # base -> {doi: (num, sep, record)}
    matched_terms_by_base = {}   # base -> set(terms)
    for term in QUERY_TERMS:
        items = []
        variant_stats = []
        for query_string in QUERY_VARIANTS.get(term, [term]):
            variant_items, one_stats = fetch_term(client, server_id, prefix, query_string)
            items.extend(variant_items)
            variant_stats.append(one_stats)
        stats = {
            "server": server_id,
            "term": term,
            "total_results": sum(v["total_results"] for v in variant_stats),
            "fetched": sum(v["fetched"] for v in variant_stats),
            "truncated_by_cap": any(v["truncated_by_cap"] for v in variant_stats),
        }
        if len(variant_stats) > 1:
            stats["query_variants"] = variant_stats
        kept_dois = set()
        kept_bases = set()
        for item in items:
            record = parse_item(item)
            if not phrase_match(term, record):
                continue
            base, num, sep = split_version(record["doi"])
            versions_by_base.setdefault(base, {})[record["doi"]] = (num, sep, record)
            matched_terms_by_base.setdefault(base, set()).add(term)
            kept_dois.add(record["doi"])
            kept_bases.add(base)
        stats["kept_after_phrase_filter"] = len(kept_dois)
        stats["kept_unique_works"] = len(kept_bases)
        stats["kept_ratio"] = round(len(kept_dois) / stats["fetched"], 4) if stats["fetched"] else None
        term_stats.append(stats)
        flag = "  [TRUNCATED at cap %d]" % MAX_RESULTS_PER_TERM if stats["truncated_by_cap"] else ""
        log("%-15s %-26s total=%-6d fetched=%-5d kept=%-4d%s" % (
            server_id, term, stats["total_results"], stats["fetched"], len(kept_dois), flag))
    records, v1_lookups = merge_versions(client, server_id, versions_by_base, matched_terms_by_base)
    records.sort(key=lambda r: (r["date"] or "", r["id"]))
    return records, v1_lookups


def summarize(server_id, records, stats_for_server):
    by_window = {"trailing": 0, "preceding": 0, None: 0}
    for rec in records:
        by_window[rec["window"]] += 1
    term_counts = {}
    for rec in records:
        for term in rec["matched_terms"]:
            term_counts[term] = term_counts.get(term, 0) + 1
    fetched = sum(s["fetched"] for s in stats_for_server)
    kept = sum(s["kept_after_phrase_filter"] for s in stats_for_server)
    total = sum(s["total_results"] for s in stats_for_server)
    top_terms = sorted(term_counts.items(), key=lambda kv: -kv[1])[:10]
    return {
        "unique_records": len(records),
        "by_window": {"trailing": by_window["trailing"], "preceding": by_window["preceding"],
                      "outside": by_window[None]},
        "top_terms_by_unique_kept": top_terms,
        "crossref_total_results_sum": total,
        "fetched_sum": fetched,
        "kept_sum": kept,
        "raw_to_kept_ratio": round(kept / fetched, 4) if fetched else None,
        "with_is_preprint_of": sum(1 for r in records if r["extra"]["is_preprint_of"]),
        "with_arxiv_id": sum(1 for r in records if r["arxiv_id"]),
        "truncated_terms": [s["term"] for s in stats_for_server if s["truncated_by_cap"]],
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--servers", default=",".join(s for s, _ in SERVERS))
    args = parser.parse_args()
    wanted = set(args.servers.split(","))

    client = CrossrefClient()
    log_data = {}
    if os.path.exists(LOG_PATH):
        log_data = json.load(open(LOG_PATH))
    log_data.setdefault("servers", {})
    log_data.update({
        "generated": datetime.datetime.utcnow().isoformat() + "Z",
        "api": API,
        "query_template": "/prefixes/<prefix>/works?filter=type:posted-content,from-posted-date:%s,"
                          "until-posted-date:%s&query.bibliographic=<term>&rows=%d&cursor=*" % (FROM_DATE, UNTIL_DATE, ROWS),
        "cap_per_server_term": MAX_RESULTS_PER_TERM,
        "windows": dict((n, [a, b]) for n, a, b in WINDOWS),
        "phrase_filter": "term (case/accent-insensitive; hyphen/space/no-space variants; leading word boundary) in title or abstract",
    })

    for server_id, prefix in SERVERS:
        if server_id not in wanted:
            continue
        log("=== %s (prefix %s) ===" % (server_id, prefix))
        term_stats = []
        records, v1_lookups = harvest_server(client, server_id, prefix, term_stats)
        out_path = os.path.join(CORPUS_DIR, server_id + ".jsonl")
        with open(out_path, "w", encoding="utf-8") as fh:
            for rec in records:
                fh.write(json.dumps(rec, ensure_ascii=False) + "\n")
        summary = summarize(server_id, records, term_stats)
        summary["v1_lookups"] = v1_lookups
        log_data["servers"][server_id] = {"prefix": prefix, "summary": summary, "terms": term_stats}
        with open(LOG_PATH, "w") as fh:
            json.dump(log_data, fh, indent=1)

        print("\n--- %s: %d unique records -> %s" % (server_id, len(records), out_path))
        print("  by window: %s" % summary["by_window"])
        print("  raw->kept: fetched %d, kept %d (ratio %s); crossref total-results sum %d" % (
            summary["fetched_sum"], summary["kept_sum"], summary["raw_to_kept_ratio"],
            summary["crossref_total_results_sum"]))
        print("  top terms: %s" % ", ".join("%s=%d" % kv for kv in summary["top_terms_by_unique_kept"]))
        if summary["truncated_terms"]:
            print("  TRUNCATED by cap: %s" % summary["truncated_terms"])
        for rec in records[-3:]:
            print("  e.g. [%s] %s" % (rec["date"], rec["title"][:120]))
        print(flush=True)
    log("done; %d HTTP requests this run" % client.request_count)


if __name__ == "__main__":
    sys.exit(main())
