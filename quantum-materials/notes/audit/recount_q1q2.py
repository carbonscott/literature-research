"""
Independent audit recount of the Q1 and Q2 tables in findings.md.

Usage:  /usr/bin/python3 notes/audit/recount_q1q2.py

Reads analysis/classified.jsonl, corpus/arxiv.jsonl, corpus/arxiv_harvest_log.json
and findings.md. Does NOT import momentum.py or count_clusters.py.
Writes notes/audit/recount_q1q2.json and prints a plain-text report.

Parts:
  1. Recount (arXiv, in scope): scope_T, scope_P, per-cluster trailing primary,
     trailing multi-label, preceding primary, R, 95% CI, label; compare to the
     Q1 and Q2 markdown tables cell by cell (R and CI tolerance 0.01).
  2. Monthly diagnostics for the 2025-10 dip.
  3. Sensitivity: labels excluding 2026-09 and excluding 2024-09-24..30.
"""

import json
import math
import os
from collections import Counter, defaultdict

AUDIT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT = os.path.dirname(os.path.dirname(AUDIT_DIR))
CLASSIFIED = os.path.join(PROJECT, "analysis", "classified.jsonl")
ARXIV_CORPUS = os.path.join(PROJECT, "corpus", "arxiv.jsonl")
HARVEST_LOG = os.path.join(PROJECT, "corpus", "arxiv_harvest_log.json")
FINDINGS = os.path.join(PROJECT, "findings.md")
OUTPUT = os.path.join(AUDIT_DIR, "recount_q1q2.json")

UNCLASSIFIED = "unclassified"
TOLERANCE = 0.01
TOP_CLUSTERS_FOR_DIP = 5


# ---------------------------------------------------------------- loading

def load_in_scope_arxiv():
    rows = []
    with open(CLASSIFIED) as handle:
        for line in handle:
            row = json.loads(line)
            if row["server"] == "arxiv" and row["in_scope"] and row["window"] in ("trailing", "preceding"):
                rows.append(row)
    return rows


def load_all_arxiv_classified():
    rows = []
    with open(CLASSIFIED) as handle:
        for line in handle:
            row = json.loads(line)
            if row["server"] == "arxiv" and row["window"] in ("trailing", "preceding"):
                rows.append(row)
    return rows


def load_corpus_matched_terms():
    """id -> (date, matched_terms, categories) for corpus/arxiv.jsonl."""
    info = {}
    with open(ARXIV_CORPUS) as handle:
        for line in handle:
            rec = json.loads(line)
            info[rec["id"]] = (rec["date"], rec["matched_terms"], rec["categories"])
    return info


# ---------------------------------------------------------------- statistics

def primary_label(row):
    return row["primary_cluster"] or UNCLASSIFIED


def momentum_row(t, p, scope_t, scope_p):
    if t == 0 or p == 0:
        return {"T": t, "P": p, "R": None, "lo": None, "hi": None, "label": "n/a"}
    ratio = (t / scope_t) / (p / scope_p)
    se = math.sqrt(1.0 / t + 1.0 / p + 1.0 / scope_t + 1.0 / scope_p)
    lo = math.exp(math.log(ratio) - 1.96 * se)
    hi = math.exp(math.log(ratio) + 1.96 * se)
    if ratio >= 1.10 and lo > 1.0:
        label = "rising"
    elif ratio <= 0.90 and hi < 1.0:
        label = "declining"
    else:
        label = "flat"
    return {"T": t, "P": p, "R": ratio, "lo": lo, "hi": hi, "label": label}


def compute_table(rows):
    scope_t = sum(1 for r in rows if r["window"] == "trailing")
    scope_p = sum(1 for r in rows if r["window"] == "preceding")
    trailing_primary = Counter()
    preceding_primary = Counter()
    trailing_multi = Counter()
    for r in rows:
        label = primary_label(r)
        if r["window"] == "trailing":
            trailing_primary[label] += 1
            for cluster in r["clusters"]:
                trailing_multi[cluster] += 1
        else:
            preceding_primary[label] += 1
    clusters = sorted(set(trailing_primary) | set(preceding_primary))
    table = {}
    for cluster in clusters:
        stats = momentum_row(trailing_primary[cluster], preceding_primary[cluster], scope_t, scope_p)
        stats["T_multi"] = trailing_multi[cluster] if cluster != UNCLASSIFIED else None
        table[cluster] = stats
    return scope_t, scope_p, table


# ---------------------------------------------------------------- findings.md parsing

def section_text(markdown, heading):
    start = markdown.index(heading)
    end = markdown.find("\n## ", start + len(heading))
    return markdown[start:end if end >= 0 else len(markdown)]


def parse_first_table(section):
    lines = [ln for ln in section.splitlines() if ln.startswith("|")]
    header = [c.strip() for c in lines[0].strip("|").split("|")]
    body = []
    for ln in lines[2:]:
        cells = [c.strip() for c in ln.strip("|").split("|")]
        if len(cells) == len(header):
            body.append(dict(zip(header, cells)))
    return header, body


def to_int(text):
    text = text.replace(",", "").strip()
    return None if text in ("-", "") else int(text)


def compare_q1(body, table, mismatches):
    for row in body:
        name = row["Cluster"].replace(" (in scope)", "").strip()
        stats = table.get(name)
        if stats is None:
            mismatches.append(("Q1", name, "row", "cluster not found in recount", ""))
            continue
        checks = [("Trailing 12 mo (primary)", stats["T"]),
                  ("Preceding 12 mo (primary)", stats["P"]),
                  ("Trailing (multi-label)", stats["T_multi"])]
        for column, expected in checks:
            reported = to_int(row[column])
            if reported != expected:
                mismatches.append(("Q1", name, column, row[column], expected))
        trend = row["Q2 trend"]
        reported_label = trend.split(" ")[0]
        reported_r = float(trend.split("R ")[1].rstrip(")"))
        if reported_label != stats["label"]:
            mismatches.append(("Q1", name, "Q2 trend label", reported_label, stats["label"]))
        if abs(reported_r - stats["R"]) > TOLERANCE:
            mismatches.append(("Q1", name, "Q2 trend R", reported_r, round(stats["R"], 3)))
    missing = set(table) - {r["Cluster"].replace(" (in scope)", "").strip() for r in body}
    for name in missing:
        mismatches.append(("Q1", name, "row", "missing from findings table", ""))


def compare_q2(body, table, mismatches):
    for row in body:
        name = row["Cluster"]
        stats = table.get(name)
        if stats is None:
            mismatches.append(("Q2", name, "row", "cluster not found in recount", ""))
            continue
        for column, expected in (("T", stats["T"]), ("P", stats["P"])):
            if to_int(row[column]) != expected:
                mismatches.append(("Q2", name, column, row[column], expected))
        if abs(float(row["Share ratio R"]) - stats["R"]) > TOLERANCE:
            mismatches.append(("Q2", name, "R", row["Share ratio R"], round(stats["R"], 3)))
        lo_text, hi_text = row["95% CI"].split("-")
        if abs(float(lo_text) - stats["lo"]) > TOLERANCE:
            mismatches.append(("Q2", name, "CI low", lo_text, round(stats["lo"], 3)))
        if abs(float(hi_text) - stats["hi"]) > TOLERANCE:
            mismatches.append(("Q2", name, "CI high", hi_text, round(stats["hi"], 3)))
        if row["Label"] != stats["label"]:
            mismatches.append(("Q2", name, "Label", row["Label"], stats["label"]))
    missing = set(table) - {r["Cluster"] for r in body}
    for name in missing:
        mismatches.append(("Q2", name, "row", "missing from findings table", ""))


def compute_variant(rows, multi, category_only):
    """R/CI/label for the robustness variants quoted in the Q2 'Robustness note' column."""
    if category_only:
        rows = [r for r in rows if r["scope_reason"] == "category"]
    scope_t = sum(1 for r in rows if r["window"] == "trailing")
    scope_p = sum(1 for r in rows if r["window"] == "preceding")
    trailing, preceding = Counter(), Counter()
    for r in rows:
        labels = (r["clusters"] or [UNCLASSIFIED]) if multi else [primary_label(r)]
        target = trailing if r["window"] == "trailing" else preceding
        for label in labels:
            target[label] += 1
    return {c: momentum_row(trailing[c], preceding[c], scope_t, scope_p)
            for c in set(trailing) | set(preceding)}


def compare_q2_robustness(body, rows, mismatches):
    import re
    multi = compute_variant(rows, multi=True, category_only=False)
    cat_only = compute_variant(rows, multi=False, category_only=True)
    for row in body:
        name = row["Cluster"]
        note = row["Robustness note"]
        for key, variant in (("multi-label R", multi), ("category-only R", cat_only)):
            match = re.search(key + r" ([0-9.]+) \((\w+)", note)
            if not match:
                mismatches.append(("Q2 robustness", name, key, "not found in note", ""))
                continue
            stats = variant[name]
            if abs(float(match.group(1)) - stats["R"]) > TOLERANCE:
                mismatches.append(("Q2 robustness", name, key, match.group(1), round(stats["R"], 3)))
            if match.group(2) != stats["label"]:
                mismatches.append(("Q2 robustness", name, key + " label", match.group(2), stats["label"]))


# ---------------------------------------------------------------- part 2: monthly diagnostics

def monthly_diagnostics(in_scope_rows, all_rows, corpus_info, top_clusters):
    months = sorted({r["month"] for r in all_rows})
    all_by_month = Counter(r["month"] for r in all_rows)
    queried_by_month = defaultdict(Counter)       # month -> category -> records (from matched_terms)
    mtrl_only_by_month = Counter()                 # records whose only queried category is mtrl-sci
    for r in all_rows:
        date, matched, _cats = corpus_info.get(r["id"], (None, [], []))
        for term in matched:
            queried_by_month[r["month"]][term] += 1
        if matched == ["cond-mat.mtrl-sci"]:
            mtrl_only_by_month[r["month"]] += 1

    scope_by_month = Counter()
    scope_reason_by_month = defaultdict(Counter)
    keyword_mtrl_only_by_month = Counter()
    cluster_by_month = defaultdict(Counter)
    for r in in_scope_rows:
        month = r["month"]
        scope_by_month[month] += 1
        scope_reason_by_month[month][r["scope_reason"]] += 1
        matched = corpus_info.get(r["id"], (None, [], []))[1]
        if r["scope_reason"] == "keyword" and matched == ["cond-mat.mtrl-sci"]:
            keyword_mtrl_only_by_month[month] += 1
        cluster_by_month[month][primary_label(r)] += 1

    table = []
    for month in months:
        scope = scope_by_month[month]
        cat_scope = scope_reason_by_month[month]["category"]
        row = {
            "month": month,
            "arxiv_all": all_by_month[month],
            "queried": dict(queried_by_month[month]),
            "mtrl_only_all": mtrl_only_by_month[month],
            "in_scope": scope,
            "in_scope_category": cat_scope,
            "in_scope_keyword": scope_reason_by_month[month]["keyword"],
            "keyword_mtrl_only": keyword_mtrl_only_by_month[month],
            "keyword_share": scope_reason_by_month[month]["keyword"] / scope if scope else None,
            "shares_full": {c: cluster_by_month[month][c] / scope for c in top_clusters},
            "counts": {c: cluster_by_month[month][c] for c in top_clusters},
        }
        # share within category-scoped records only (removes baseline-composition effect)
        cat_counts = Counter(primary_label(r) for r in in_scope_rows
                             if r["month"] == month and r["scope_reason"] == "category")
        row["shares_category_only"] = {c: cat_counts[c] / cat_scope for c in top_clusters} if cat_scope else {}
        row["counts_category_only"] = {c: cat_counts[c] for c in top_clusters}
        table.append(row)
    return table


def harvest_slices_by_month():
    log = json.load(open(HARVEST_LOG))
    by_slice = defaultdict(dict)
    for s in log["slices"]:
        by_slice[s["slice"]][s["category"]] = (s["totalResults"], s["parsed"], s["unique_ids"], s["reconciled"])
    return by_slice


def month_zscores(monthly, cluster, key, exclude=("2024-09", "2026-09")):
    """z-score of each month's share vs a Poisson/binomial expectation from the pooled share."""
    count_key = "counts" if key == "shares_full" else "counts_category_only"
    denom_key = "in_scope" if key == "shares_full" else "in_scope_category"
    rows = [m for m in monthly if m["month"] not in exclude]
    total_c = sum(m[count_key][cluster] for m in rows)
    total_n = sum(m[denom_key] for m in rows)
    pooled = total_c / total_n
    out = {}
    for m in monthly:
        n = m[denom_key]
        expected = pooled * n
        sd = math.sqrt(n * pooled * (1 - pooled))
        out[m["month"]] = (m[count_key][cluster] - expected) / sd if sd else None
    return pooled, out


# ---------------------------------------------------------------- part 3: sensitivity

def in_first_week(row):
    return row["month"] == "2024-09"   # 2024-09 bucket holds only 09-24..30


def in_partial_last_month(row):
    return row["month"] == "2026-09"


def main():
    in_scope = load_in_scope_arxiv()
    all_arxiv = load_all_arxiv_classified()
    corpus_info = load_corpus_matched_terms()
    scope_t, scope_p, table = compute_table(in_scope)

    markdown = open(FINDINGS).read()
    _h1, q1_body = parse_first_table(section_text(markdown, "## Q1 Landscape"))
    _h2, q2_body = parse_first_table(section_text(markdown, "## Q2 Momentum"))
    mismatches = []
    compare_q1(q1_body, table, mismatches)
    compare_q2(q2_body, table, mismatches)
    compare_q2_robustness(q2_body, in_scope, mismatches)

    print("PART 1: scope_T = %d, scope_P = %d, growth = %+.2f%%" % (scope_t, scope_p, 100.0 * (scope_t / scope_p - 1)))
    print("%-36s %5s %6s %5s %6s %6s %6s %s" % ("cluster", "T", "Tmulti", "P", "R", "lo", "hi", "label"))
    for name, s in sorted(table.items(), key=lambda kv: -kv[1]["R"]):
        print("%-36s %5d %6s %5d %6.3f %6.3f %6.3f %s" % (name, s["T"], s["T_multi"], s["P"], s["R"], s["lo"], s["hi"], s["label"]))
    print("Q1 rows parsed: %d; Q2 rows parsed: %d" % (len(q1_body), len(q2_body)))
    print("MISMATCHES: %d" % len(mismatches))
    for m in mismatches:
        print("  ", m)

    # residual-cluster total and unclassified shares used in Q1 text
    residual = ["quantum_magnetism_ferroic_order", "quantum_many_body_theory", "other_superconductivity"]
    residual_t = sum(table[c]["T"] for c in residual)
    print("residual trailing = %d (%.1f%%); unclassified T share %.2f%%, P share %.2f%%; n clusters (excl. unclassified) = %d" % (
        residual_t, 100.0 * residual_t / scope_t, 100.0 * table[UNCLASSIFIED]["T"] / scope_t,
        100.0 * table[UNCLASSIFIED]["P"] / scope_p, len(table) - 1))

    # ---- part 2
    top = [c for c, _ in sorted(((c, s["T"] + s["P"]) for c, s in table.items() if c != UNCLASSIFIED),
                                key=lambda kv: -kv[1])[:TOP_CLUSTERS_FOR_DIP]]
    dip_named = ["topological_insulators_semimetals", "spin_liquid_frustrated"]
    watch = top + [c for c in dip_named if c not in top]
    monthly = monthly_diagnostics(in_scope, all_arxiv, corpus_info, watch)
    slices = harvest_slices_by_month()
    print("\nPART 2: harvest log totalResults per slice (str-el, supr-con, mes-hall, mtrl-sci)")
    cats = ["cond-mat.str-el", "cond-mat.supr-con", "cond-mat.mes-hall", "cond-mat.mtrl-sci"]
    for slice_name in sorted(slices):
        vals = [slices[slice_name].get(c, (None,) * 4) for c in cats]
        print("  %s %s reconciled=%s" % (slice_name, [v[0] for v in vals], all(v[3] for v in vals)))
    print("\nmonthly (records by corpus 'date' month): all arXiv, queried-by-category, in-scope, cat, kw, kw&mtrl-only, kw share")
    for m in monthly:
        q = m["queried"]
        print("  %s all=%5d  str=%4d sup=%4d mes=%4d mtrl=%4d | scope=%4d cat=%4d kw=%4d kw_mtrl_only=%4d kw_share=%.3f" % (
            m["month"], m["arxiv_all"], q.get(cats[0], 0), q.get(cats[1], 0), q.get(cats[2], 0), q.get(cats[3], 0),
            m["in_scope"], m["in_scope_category"], m["in_scope_keyword"], m["keyword_mtrl_only"], m["keyword_share"]))
    print("\nmonthly shares, full scope (top %d + dip-named)" % TOP_CLUSTERS_FOR_DIP)
    print("  month   " + " ".join("%10s" % c[:10] for c in watch) + "  top5sum")
    for m in monthly:
        top_sum = sum(m["shares_full"][c] for c in top)
        print("  %s " % m["month"] + " ".join("%10.3f" % m["shares_full"][c] for c in watch) + "  %.3f" % top_sum)
    print("\nmonthly shares, category-only scope")
    for m in monthly:
        top_sum = sum(m["shares_category_only"][c] for c in top)
        print("  %s " % m["month"] + " ".join("%10.3f" % m["shares_category_only"][c] for c in watch) + "  %.3f" % top_sum)
    print("\nz-scores of monthly count vs pooled share (full scope / category-only)")
    zs = {}
    for c in watch:
        pooled_f, z_full = month_zscores(monthly, c, "shares_full")
        pooled_c, z_cat = month_zscores(monthly, c, "shares_category_only")
        zs[c] = {"pooled_full": pooled_f, "pooled_cat": pooled_c, "z_full": z_full, "z_cat": z_cat}
        print("  %-36s pooled %.3f  2025-10 z_full %+.2f z_cat %+.2f | 2025-09 z_full %+.2f | min z_full month %s %+.2f" % (
            c, pooled_f, z_full["2025-10"], z_cat["2025-10"], z_full["2025-09"],
            min(z_full, key=lambda k: z_full[k]), min(z_full.values())))

    # 2025-09 boundary split
    split = Counter((r["window"], r["scope_reason"]) for r in in_scope if r["month"] == "2025-09")
    print("\n2025-09 in-scope split by window/scope_reason:", dict(split))

    # ---- part 3
    variants = {
        "exclude_2026-09": [r for r in in_scope if not in_partial_last_month(r)],
        "exclude_2024-09-24..30": [r for r in in_scope if not in_first_week(r)],
        "exclude_both": [r for r in in_scope if not in_partial_last_month(r) and not in_first_week(r)],
    }
    sensitivity = {}
    print("\nPART 3: sensitivity")
    for name, rows in variants.items():
        st, sp, vt = compute_table(rows)
        changes = []
        for c, s in vt.items():
            if s["label"] != table[c]["label"]:
                changes.append((c, table[c]["label"], s["label"], round(s["R"], 3), round(s["lo"], 3), round(s["hi"], 3)))
        sensitivity[name] = {"scope_T": st, "scope_P": sp, "table": vt, "label_changes": changes}
        print("  %s: scope_T=%d scope_P=%d label changes=%s" % (name, st, sp, changes))
        for c in ("spin_liquid_frustrated", "topological_insulators_semimetals", "altermagnetism", "kagome",
                  "fractional_qah_chern", "unconventional_topological_sc", "iron_based_sc"):
            s = vt[c]
            print("     %-36s R %.3f CI %.3f-%.3f %s" % (c, s["R"], s["lo"], s["hi"], s["label"]))

    # leave-one-month-out: which labels depend on a single calendar month?
    print("\nPART 3b: leave-one-month-out label changes")
    loo = {}
    for month in sorted({r["month"] for r in in_scope}):
        _st, _sp, vt = compute_table([r for r in in_scope if r["month"] != month])
        changes = [(c, table[c]["label"], s["label"], round(s["R"], 3), round(s["lo"], 3), round(s["hi"], 3))
                   for c, s in vt.items() if s["label"] != table[c]["label"]]
        if changes:
            loo[month] = changes
            print("  drop %s: %s" % (month, changes))
    sensitivity["leave_one_month_out"] = loo

    json.dump({"scope_T": scope_t, "scope_P": scope_p, "table": table, "mismatches": mismatches,
               "monthly": monthly, "zscores": zs, "sensitivity": sensitivity,
               "boundary_2025_09": {"%s/%s" % k: v for k, v in split.items()}},
              open(OUTPUT, "w"), indent=1, sort_keys=True, default=str)
    print("\nwrote", OUTPUT)


if __name__ == "__main__":
    main()
