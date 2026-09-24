"""
Q3 Materials: which material families and compounds each topic cluster studies,
and which materials are growing fastest.

Usage:  /usr/bin/python3 materials.py

Inputs (read-only):
  analysis/classified.jsonl   taxonomy-v2 labels per record (families, primary_cluster, ...)
  corpus/arxiv.jsonl          titles + abstracts (for formula extraction and exemplars)

Population: arXiv records that are in scope (taxonomy v2 scope rule).
Per-cluster tables use the trailing window and the record's PRIMARY cluster.

Steps
  1. Per cluster: records per material family (taxonomy.MATERIAL_FAMILIES, taken
     from the `families` field), share of the cluster's records naming any
     family, top 3 families.
  2. Data-driven gap check: chemical-formula-like tokens are extracted from the
     normalized title+abstract (taxonomy.normalize_text) and the top 10 formulas
     per cluster are listed. Families that the formulas show to be missing from
     MATERIAL_FAMILIES are defined in EXTENDED_FAMILIES below (taxonomy.py is
     not edited) and the per-cluster tables are recounted with base+extended.
  3. Trends: for the 20 most frequent families (base+extended) and the 20 most
     frequent formulas, trailing vs preceding counts and the share ratio against
     the in-scope baseline, R = (T/scope_T) / (P/scope_P), with a Poisson CI
     var(log R) ~= 1/T + 1/P + 1/scope_T + 1/scope_P (same as the momentum lane).
  4. Exemplars: one trailing-window arXiv ID per cluster whose TITLE names the
     cluster's leading family, and one per fastest-growing material.

Writes analysis/materials.json.
"""

import json
import math
import os
import re
import sys
from collections import Counter, defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import taxonomy as tx  # noqa: E402

PROJECT_DIR = os.path.dirname(HERE)
CLASSIFIED_PATH = os.path.join(HERE, "classified.jsonl")
ARXIV_CORPUS_PATH = os.path.join(PROJECT_DIR, "corpus", "arxiv.jsonl")
OUTPUT_PATH = os.path.join(HERE, "materials.json")

Z_95 = 1.96
TOP_FAMILIES_PER_CLUSTER = 3
TOP_FORMULAS_PER_CLUSTER = 10
N_TREND_ITEMS = 20
N_FASTEST_GROWING = 5
MIN_SUPPORT_FOR_GROWTH = 30   # T + P records needed before a material can rank as "fast-growing"


# ---------------------------------------------------------------------------
# Extended family lexicon (Q3 gap check)
#
# Built from the formulas that the extraction below found frequently in in-scope
# arXiv records but that no taxonomy.MATERIAL_FAMILIES pattern matches.
# Same conventions as taxonomy.py: case-sensitive formulas guarded by tx.L / tx.R,
# tx.ci() for case-insensitive words. Each entry lists the evidence that motivated it.
# ---------------------------------------------------------------------------

L, R = tx.L, tx.R


def formula_group(formulas):
    """Case-sensitive alternation of formulas with the taxonomy guards."""
    return L + "(?:" + "|".join(formulas) + ")" + R


EXTENDED_FAMILIES = {
    # NbN (55), MgB2 (40), NbTiN (23), TiN (20), Nb3Sn (13), NbTi (9), TaN (7):
    # conventional / device superconductors (v1 noted "conventional SC" in unclassified bigrams).
    "ext_conventional_sc_compounds": formula_group([
        "NbN", "NbTiN", "TiN", "TaN", "MgB2", "Nb3Sn", "Nb3Ge", "NbTi", "V3Si",
        "MoGe", "MoSi", "MoRe", "WSi", "K3C60", "CaC6", "Mo3Al2C"]),
    # BiFeO3 (43), BaTiO3 (28), PbTiO3 (16), Cr2O3 (14), In2Se3 (14), LiNbO3 (11),
    # HfO2 (10), Fe2Mo3O8 (9), CuCrP2S6 (8): ferroelectrics and multiferroics.
    "ext_ferroelectrics_multiferroics": formula_group([
        "BiFeO3", "BaTiO3", "PbTiO3", "PbZrO3", "Cr2O3", "In2Se3",
        "LiNbO3", "LiTaO3", "HfO2", "Hf0.5Zr0.5O2", "Fe2Mo3O8", "Co2Mo3O8", "Ni3TeO6",
        "CuCrP2S6", "CuInP2S6", "NbOI2", "TbMnO3", "YMnO3", "BiMnO3", "GeTe"])
        + "|" + tx.ci(r"\bmultiferroics?\b"),
    # Nb3Cl8 (22), LaRu3Si2 (9), HoAgGe (9), FeSn (14), LuNb6Sn6 (7), GdTi3Bi4 (6),
    # Nb3Br8 / Nb3I8, HfFe6Ge6: kagome materials beyond AV3Sb5 and the v2 "other kagome" list.
    "ext_kagome_more": formula_group([
        "Nb3Cl8", "Nb3Br8", "Nb3I8", "LaRu3Si2", "CeRu3Si2", "HoAgGe", "FeSn",
        "[A-Z][a-z]?Nb6Sn6", "[A-Z][a-z]?Ti3Bi4", "[A-Z][a-z]?Fe6Ge6", "Pd3Pb2S2"]),
    # SrIrO3 (17), SrVO3 (16), La0.7Sr0.3MnO3 (12), LaCoO3, LaFeO3, SrFeO3, CaMnO3,
    # SrMnO3, La2NiO4 (15): transition-metal perovskite / RP oxides not in the v2 lists.
    "ext_tm_perovskite_oxides": formula_group([
        "SrIrO3", "CaIrO3", "BaIrO3", "SrVO3", "CaVO3", "LaCoO3", "LaFeO3", "SrFeO3",
        "CaMnO3", "SrMnO3", "BaMnO3", "La2NiO4", "La2-xSrxNiO4", "SrCoO3", "SrCoO2.5",
        r"La0\.\d+Sr0\.\d+MnO3", r"La0\.\d+Ca0\.\d+MnO3", r"Pr0\.\d+Ca0\.\d+MnO3"]),
    # Sr2CuO3 (8), SrCuO2 (6), BaCo2V2O8 (8), CoNb2O6 (8), CuGeO3, Sr14Cu24O41,
    # KCuF3, Na2Cu3Ge4O12: quasi-1D spin chains / ladders (v1 unclassified bigram "spin chains").
    "ext_spin_chain_ladder_compounds": formula_group([
        "Sr2CuO3", "SrCuO2", "Ca2CuO3", "BaCo2V2O8", "SrCo2V2O8", "CoNb2O6", "CuGeO3",
        "Sr14Cu24O41", "KCuF3", "Na2Cu3Ge4O12", "LiCuVO4", "CsCoCl3", "YbAlO3",
        "Cs2CoCl4", "BaCu2Si2O7"]),
    # CoFeB (15), Ni80Fe20 (8), NiFe, CuMnAs (8), Mn3NiN, Mn3Ga, Co2FeAl, Fe3O4, YIG:
    # spintronic ferro/antiferromagnets (films, electrodes, magnon hosts).
    "ext_spintronic_magnets": formula_group([
        "CoFeB", "Co20Fe60B20", "Ni80Fe20", "Ni81Fe19", "NiFe", "CuMnAs", "Mn2Au",
        "Mn3NiN", "Mn3GaN", "Mn3Ga", "Mn3Pt", "Mn3Ir", "IrMn", "Co2FeAl", "Co2MnSi",
        "Fe3O4", "Y3Fe5O12", "Tm3Fe5O12"])
        + "|" + r"\bYIG\b|\bTmIG\b|" + tx.ci(r"\bpermalloy\b|\byttrium iron garnet"),
    # NiTe2 (10), SnSe2 (8), ZrTe2 (7), VTe2 (6), VS2 (6), NbTe2 (5), PdSe2, ZrS2:
    # further layered dichalcogenides not in taxonomy "tmds".
    "ext_layered_dichalcogenides_more": formula_group([
        "NiTe2", "SnSe2", "SnS2", "ZrTe2", "ZrS2", "VTe2", "VS2", "NbTe2", "TaTe2",
        "PdSe2", "PtS2", "HfTe2", "TiTe2", "TiS2"]),
    # CrOCl (8), NiBr2 (5), FePSe3, Cr3Te4 (6), Cr1+δTe2 (5), Mn3Si2Te6 (9), MnTe2 (9):
    # vdW / layered magnets beyond taxonomy "vdw_magnets".
    "ext_layered_magnets_more": formula_group([
        "CrOCl", "CrOBr", "NiBr2", "NiCl2", "CoCl2", "FePSe3", "Cr3Te4", "Cr5Te8",
        r"Cr1\+δTe2", r"Cr1\+xTe2", "Mn3Si2Te6", "MnTe2", "CrSe2", "VBr3", "VCl3",
        "MnBi6Te10", "MnBi8Te13", "AgCrP2S6", "AgCrSe2"]),
    # CeNiAsO (8), CeCoSi, CeCoGe3, CeRh6Ge4, YbCuS2, URhSn, LiV2O4 (8): more f-electron /
    # heavy-fermion compounds.
    "ext_heavy_fermion_more": formula_group([
        "CeNiAsO", "CeCoSi", "CeCoGe3", "CeRh6Ge4", "CeRhSi3", "CeIrSi3", "CePt3Si",
        "YbCuS2", "URhSn", "UCoAl", "UTe3", "USb2", "LiV2O4"]),
    # SiGe (23), InP (13), PbTe (9), GaSb (6), AlN (6), SiC (35), PbSe, Pb1-xSnxSe:
    # conventional semiconductors (hosts for qubits, 2DEGs, color centres, TCIs).
    "ext_semiconductors_more": formula_group([
        "SiGe", r"Si1-xGex", "InP", "GaSb", "AlSb", "AlAs", "AlN", "SiC", "PbTe", "PbSe",
        "PbS", r"Pb1-xSnxSe", "InGaAs", "GaInSb", "InAsSb", "CdSe", "ZnSe"]),
    # PdCoO2, PdCrO2, PtCoO2: metallic delafossites (hydrodynamic transport).
    "ext_delafossites": formula_group(["PdCoO2", "PdCrO2", "PtCoO2"])
        + "|" + tx.ci(r"\bdelafossites?\b"),
}
# Formulas already covered by a taxonomy family (e.g. SrTiO3, SnTe, NiO, PtTe2, MoTe2)
# are deliberately not repeated here, so base and extended families do not overlap.

_BASE_FAMILY_REGEXES = [(key, re.compile(pattern)) for key, pattern in tx.MATERIAL_FAMILIES.items()]
_EXTENDED_FAMILY_REGEXES = [(key, re.compile(pattern)) for key, pattern in EXTENDED_FAMILIES.items()]
ALL_FAMILY_REGEXES = dict(_BASE_FAMILY_REGEXES + _EXTENDED_FAMILY_REGEXES)


def find_extended_families(text):
    """Extended-family keys whose pattern matches normalized `text`."""
    return [key for key, regex in _EXTENDED_FAMILY_REGEXES if regex.search(text)]


# ---------------------------------------------------------------------------
# Chemical-formula extraction
# ---------------------------------------------------------------------------

ELEMENTS = set("""
H He Li Be B C N O F Ne Na Mg Al Si P S Cl Ar K Ca Sc Ti V Cr Mn Fe Co Ni Cu Zn
Ga Ge As Se Br Kr Rb Sr Y Zr Nb Mo Tc Ru Rh Pd Ag Cd In Sn Sb Te I Xe Cs Ba La Ce
Pr Nd Pm Sm Eu Gd Tb Dy Ho Er Tm Yb Lu Hf Ta W Re Os Ir Pt Au Hg Tl Pb Bi Po At Rn
Fr Ra Ac Th Pa U Np Pu Am Cm Bk Cf Es Fm Md No Lr
""".split())

# One element symbol followed by an optional count: "3", "0.7", "-x", "x", "+δ".
_ELEMENT_WITH_COUNT = r"[A-Z][a-z]?(?:\d+(?:\.\d+)?|[-+]?[xyδ])*"
# A candidate formula: 2+ such groups, optional polytype/phase prefix (1T-, 2H-, α-, Td-).
FORMULA_CANDIDATE = re.compile(
    r"(?<![A-Za-z0-9])"
    r"(?P<prefix>(?:[1-6][TRH]'?|Td|[αβγδεκλ])-)?"
    r"(?P<body>(?:" + _ELEMENT_WITH_COUNT + r"){2,})"
    r"(?![A-Za-z0-9])"
)
_SYMBOL_AND_COUNT = re.compile(r"([A-Z][a-z]?)((?:\d+(?:\.\d+)?|[-+]?[xyδ])*)")

# Common chemicals, substrates, dielectrics: not informative about the material studied.
GENERIC_FORMULAS = {
    "H2O", "D2O", "CO2", "CO", "NH3", "CH4", "HCl", "NaCl", "LiF", "CaF2", "N2O",
    "SiO2", "Al2O3", "MgO", "Si3N4", "SiN", "TiO2", "Ta2O5", "CaH2",
}
# Acronyms that happen to parse as element symbols.
ACRONYM_FALSE_POSITIVES = {"SU2", "SU3", "SO3", "SO5", "CP1", "CP2", "SYK2", "HC2", "SC1", "SC2", "SC3"}
# Structural units: coordination polyhedra and layers, not compounds.
STRUCTURAL_UNIT = re.compile(r"^(?:[A-Z][a-z]?O[3-6]|CuO2|NiO2)$")
# Structure-type labels ("NiAs-type", "ThCr2Si2 structure") are not the material studied.
STRUCTURE_TYPE_AFTER = re.compile(r"^[- ](?:type|structure|structured)\b")


def parse_formula(body):
    """Element symbols in `body` if it is a plausible formula, else None.

    Plausible = only real element symbols, at least 2 distinct elements, no count
    above 99 (rejects "SC2024"), and either a numeric/variable count or at least one
    two-letter symbol (rejects all-caps acronyms such as "BCS", "NV").
    """
    symbols = []
    position = 0
    has_count = False
    has_two_letter_symbol = False
    for match in _SYMBOL_AND_COUNT.finditer(body):
        if match.start() != position:
            return None
        symbol, count = match.group(1), match.group(2)
        if symbol not in ELEMENTS:
            return None
        if any(len(number) > 2 for number in re.findall(r"\d+", count)):
            return None
        symbols.append(symbol)
        has_count = has_count or bool(count)
        has_two_letter_symbol = has_two_letter_symbol or len(symbol) == 2
        position = match.end()
    if position != len(body) or len(set(symbols)) < 2:
        return None
    if not (has_count or has_two_letter_symbol):
        return None
    return symbols


def is_plural_acronym(body):
    """'SCs', 'BICs', 'SOCs': all-caps acronym + plural s (parses as ...Cs / ...Os)."""
    return re.match(r"^[A-Z]+s$", body) is not None


def canonical_formula(body):
    """Drop a trailing off-stoichiometry variable: 'La3Ni2O7-δ', 'YBa2Cu3O7-x',
    'Bi2Sr2CaCu2O8+x' -> 'La3Ni2O7', 'YBa2Cu3O7', 'Bi2Sr2CaCu2O8'."""
    return re.sub(r"[-+][xyδ]$|δ$", "", body)


def extract_formulas(text):
    """Set of canonical formula tokens found in normalized `text`."""
    formulas = set()
    for match in FORMULA_CANDIDATE.finditer(text):
        body = canonical_formula(match.group("body"))
        before = text[match.start() - 1] if match.start() > 0 else ""
        after = text[match.end():match.end() + 12]
        if before == "(" or after.startswith(")") or after.startswith("("):
            continue  # fragment of a parenthesized formula, e.g. Co2(PO4)2, SrCu2(BO3)2
        if STRUCTURE_TYPE_AFTER.match(after):
            continue
        if body in GENERIC_FORMULAS or body in ACRONYM_FALSE_POSITIVES:
            continue
        if STRUCTURAL_UNIT.match(body) or is_plural_acronym(body):
            continue
        if parse_formula(body) is None:
            continue
        formulas.add(body)
    return formulas


# ---------------------------------------------------------------------------
# Loading
# ---------------------------------------------------------------------------

def load_in_scope_arxiv_labels():
    """id -> classified row, for in-scope arXiv records (both windows)."""
    labels = {}
    with open(CLASSIFIED_PATH, encoding="utf-8") as handle:
        for line in handle:
            row = json.loads(line)
            if row["server"] == "arxiv" and row["in_scope"]:
                labels[row["id"]] = row
    return labels


def load_texts(wanted_ids):
    """id -> {"title": normalized title, "text": normalized title+abstract, "raw_title"}."""
    texts = {}
    with open(ARXIV_CORPUS_PATH, encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue
            record = json.loads(line)
            record_id = record.get("id")
            if record_id not in wanted_ids or record_id in texts:
                continue
            texts[record_id] = {
                "title": tx.record_title(record),
                "text": tx.record_text(record),
                "raw_title": record.get("title") or "",
            }
    return texts


def build_records():
    """List of dicts: id, window, date, primary_cluster, base_families, all_families, formulas, title."""
    labels = load_in_scope_arxiv_labels()
    texts = load_texts(set(labels))
    records = []
    for record_id, row in labels.items():
        text_info = texts.get(record_id)
        if text_info is None:
            continue
        base_families = list(row["families"])
        extended = find_extended_families(text_info["text"])
        records.append({
            "id": record_id,
            "window": row["window"],
            "date": row["date"],
            "primary_cluster": row["primary_cluster"],
            "base_families": base_families,
            "all_families": base_families + extended,
            "formulas": extract_formulas(text_info["text"]),
            "title": text_info["title"],
            "raw_title": text_info["raw_title"],
        })
    records.sort(key=lambda record: record["id"])
    return records


# ---------------------------------------------------------------------------
# Step 1-2: per-cluster tables
# ---------------------------------------------------------------------------

def family_table(cluster_records, family_field):
    """Counts per family, share naming any family, top families."""
    counts = Counter()
    n_with_family = 0
    for record in cluster_records:
        families = record[family_field]
        counts.update(families)
        if families:
            n_with_family += 1
    n_records = len(cluster_records)
    return {
        "n_with_any_family": n_with_family,
        "share_with_any_family": round(n_with_family / n_records, 3) if n_records else None,
        "family_counts": dict(counts.most_common()),
        "top_families": counts.most_common(TOP_FAMILIES_PER_CLUSTER),
    }


def formulas_not_covered(formula_counts):
    """Formulas (from a Counter) that no base or extended family pattern matches."""
    uncovered = []
    for formula, count in formula_counts:
        if not any(regex.search(formula) for regex in ALL_FAMILY_REGEXES.values()):
            uncovered.append((formula, count))
    return uncovered


def title_exemplar(cluster_records, family_key):
    """First (by id) record whose normalized title matches the family pattern."""
    regex = ALL_FAMILY_REGEXES[family_key]
    for record in cluster_records:
        if family_key in record["all_families"] and regex.search(record["title"]):
            return {"id": record["id"], "family": family_key, "title": record["raw_title"]}
    return None


def leading_family_exemplar(cluster_records, top_families):
    """Exemplar for the leading family; falls back to the next top family if no title names it."""
    for family_key, _count in top_families:
        exemplar = title_exemplar(cluster_records, family_key)
        if exemplar:
            exemplar["is_leading_family"] = family_key == top_families[0][0]
            return exemplar
    return None


def per_cluster_tables(records):
    trailing = [record for record in records if record["window"] == "trailing"]
    by_cluster = defaultdict(list)
    for record in trailing:
        by_cluster[record["primary_cluster"] or "_unclassified"].append(record)

    tables = {}
    for cluster_key in tx.CLUSTER_KEYS + ["_unclassified"]:
        cluster_records = by_cluster.get(cluster_key, [])
        formula_counts = Counter()
        for record in cluster_records:
            formula_counts.update(record["formulas"])
        top_formulas = formula_counts.most_common(TOP_FORMULAS_PER_CLUSTER)
        extended_table = family_table(cluster_records, "all_families")
        leading = extended_table["top_families"][0][0] if extended_table["top_families"] else None
        tables[cluster_key] = {
            "label": tx.CLUSTER_LABELS.get(cluster_key, "in scope, no cluster"),
            "n_records_trailing_primary": len(cluster_records),
            "base_families_v2": family_table(cluster_records, "base_families"),
            "base_plus_extended": extended_table,
            "top_formulas": top_formulas,
            "top_formulas_not_covered_by_any_family": formulas_not_covered(top_formulas),
            "leading_family": leading,
            "leading_family_exemplar": leading_family_exemplar(cluster_records, extended_table["top_families"]),
        }
    return tables


# ---------------------------------------------------------------------------
# Step 3: trends vs the in-scope baseline
# ---------------------------------------------------------------------------

def share_ratio(trailing_count, preceding_count, scope_trailing, scope_preceding):
    """Share ratio R and its 95% Poisson CI; None if either count is 0."""
    if trailing_count == 0 or preceding_count == 0:
        return None, None, None
    ratio = (trailing_count / scope_trailing) / (preceding_count / scope_preceding)
    variance = 1 / trailing_count + 1 / preceding_count + 1 / scope_trailing + 1 / scope_preceding
    half_width = Z_95 * math.sqrt(variance)
    log_ratio = math.log(ratio)
    return ratio, math.exp(log_ratio - half_width), math.exp(log_ratio + half_width)


def window_counts(records, field):
    """{label: {"trailing": n, "preceding": n}} over a list-valued record field."""
    counts = defaultdict(lambda: {"trailing": 0, "preceding": 0})
    for record in records:
        for label in record[field]:
            counts[label][record["window"]] += 1
    return counts


def trend_rows(counts, scope_trailing, scope_preceding, labels):
    rows = []
    for label in labels:
        trailing_count = counts[label]["trailing"]
        preceding_count = counts[label]["preceding"]
        ratio, low, high = share_ratio(trailing_count, preceding_count, scope_trailing, scope_preceding)
        rows.append({
            "label": label,
            "trailing": trailing_count,
            "preceding": preceding_count,
            "share_ratio": round(ratio, 3) if ratio else None,
            "ci95_low": round(low, 3) if low else None,
            "ci95_high": round(high, 3) if high else None,
        })
    return rows


def most_frequent(counts, n):
    """Top-n labels by trailing+preceding count (ties broken alphabetically)."""
    ordered = sorted(counts, key=lambda label: (-(counts[label]["trailing"] + counts[label]["preceding"]), label))
    return ordered[:n]


def fastest_growing(counts, scope_trailing, scope_preceding):
    """Formulas with >= MIN_SUPPORT_FOR_GROWTH records, ranked by the CI lower bound of R."""
    supported = [label for label in counts
                 if counts[label]["trailing"] + counts[label]["preceding"] >= MIN_SUPPORT_FOR_GROWTH]
    rows = trend_rows(counts, scope_trailing, scope_preceding, supported)
    rows = [row for row in rows if row["ci95_low"] is not None]
    rows.sort(key=lambda row: (-row["ci95_low"], row["label"]))
    return rows


def formula_title_exemplar(records, formula):
    """First (by id) trailing record whose title contains the formula token."""
    for record in records:
        if record["window"] == "trailing" and formula in extract_formulas(record["title"]):
            return {"id": record["id"], "title": record["raw_title"]}
    return None


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    records = build_records()
    scope_trailing = sum(1 for record in records if record["window"] == "trailing")
    scope_preceding = sum(1 for record in records if record["window"] == "preceding")

    clusters = per_cluster_tables(records)

    family_counts = window_counts(records, "all_families")
    formula_counts = window_counts(records, "formulas")
    family_trends = trend_rows(family_counts, scope_trailing, scope_preceding,
                               most_frequent(family_counts, N_TREND_ITEMS))
    formula_trends = trend_rows(formula_counts, scope_trailing, scope_preceding,
                                most_frequent(formula_counts, N_TREND_ITEMS))

    growth_ranking = fastest_growing(formula_counts, scope_trailing, scope_preceding)
    fastest = []
    for row in growth_ranking[:N_FASTEST_GROWING]:
        entry = dict(row)
        entry["exemplar"] = formula_title_exemplar(records, row["label"])
        fastest.append(entry)
    family_growth_ranking = fastest_growing(family_counts, scope_trailing, scope_preceding)

    output = {
        "taxonomy_version": tx.TAXONOMY_VERSION,
        "population": "arXiv records, in scope (taxonomy v2); per-cluster tables: trailing window, primary cluster",
        "windows": {"trailing": ["2025-09-24", "2026-09-23"], "preceding": ["2024-09-24", "2025-09-23"]},
        "scope_baseline": {"trailing": scope_trailing, "preceding": scope_preceding,
                           "baseline_share_ratio_note": "R=1 means the item kept pace with in-scope arXiv growth"},
        "ci_method": "var(log R) ~= 1/T + 1/P + 1/scope_T + 1/scope_P; 95% CI = exp(log R +- 1.96 sd)",
        "extended_families": EXTENDED_FAMILIES,
        "formula_rules": {
            "generic_excluded": sorted(GENERIC_FORMULAS),
            "acronyms_excluded": sorted(ACRONYM_FALSE_POSITIVES),
            "structural_units_excluded": STRUCTURAL_UNIT.pattern,
            "also_excluded": "parenthesis fragments, '-type'/'structure' labels, plural all-caps acronyms, counts > 99",
            "canonicalization": "polytype/phase prefix (1T-, 2H-, alpha-) and a trailing -x/+x/-y/-delta variable dropped",
        },
        "clusters": clusters,
        "family_trends_top20": family_trends,
        "formula_trends_top20": formula_trends,
        "fastest_growing_formulas": fastest,
        "growth_ranking_formulas_min_support": growth_ranking[:25],
        "growth_ranking_families_min_support": family_growth_ranking,
        "min_support_for_growth": MIN_SUPPORT_FOR_GROWTH,
    }
    with open(OUTPUT_PATH, "w", encoding="utf-8") as handle:
        json.dump(output, handle, indent=1, ensure_ascii=False)
    print("in-scope arXiv: trailing %d, preceding %d" % (scope_trailing, scope_preceding))
    print("wrote", OUTPUT_PATH)


if __name__ == "__main__":
    main()
