"""Build quantum-materials/findings.html from findings.md and the analysis JSON files.

The page text (headlines, tables) comes from findings.md, so the HTML always
matches the audited report. Chart series come from analysis/*.json.

Usage:  python3 quantum-materials/report/build_report.py
"""
import json
import os
import re
import subprocess
import sys

REPORT_DIR = os.path.dirname(os.path.abspath(__file__))
QM_DIR = os.path.dirname(REPORT_DIR)
TEMPLATE_PATH = os.path.join(REPORT_DIR, "template.html")
OUTPUT_PATH = os.path.join(QM_DIR, "findings.html")

# Short cluster names for chart row labels (full names stay in the tables).
SHORT_CLUSTER_NAMES = {
    "nickelate_sc": "Nickelate superconductivity",
    "cuprate_sc": "Cuprate superconductivity",
    "iron_based_sc": "Iron-based superconductivity",
    "hydride_high_pressure_sc": "Hydride / high-pressure SC",
    "kagome": "Kagome materials",
    "altermagnetism": "Altermagnetism",
    "fractional_qah_chern": "Fractional QAH / Chern insulators",
    "rhombohedral_multilayer_graphene": "Rhombohedral graphene",
    "moire_twisted_2d": "Moiré / twisted 2D",
    "unconventional_topological_sc": "Unconventional / topological SC",
    "spin_liquid_frustrated": "Spin liquids / frustrated magnets",
    "heavy_fermion_kondo_qcp": "Heavy fermions / Kondo",
    "vdw_magnets_topological_magnetism": "2D magnets & spintronics",
    "cdw_nematic_excitonic": "CDW / nematicity / excitons",
    "topological_insulators_semimetals": "Topological insulators / semimetals",
    "flat_band_quantum_geometry": "Flat bands / quantum geometry",
    "mott_hubbard_strange_metal": "Mott physics / strange metals",
    "ultrafast_floquet_noneq": "Ultrafast / Floquet",
    "ml_ai": "Machine learning / AI",
    "quantum_magnetism_ferroic_order": "Quantum magnetism (residual)",
    "quantum_many_body_theory": "Many-body theory (residual)",
    "other_superconductivity": "Other superconductivity (residual)",
}
RESIDUAL_CLUSTERS = {"quantum_magnetism_ferroic_order", "quantum_many_body_theory", "other_superconductivity"}

# Clusters shown as monthly small multiples: the one rising and the two declining.
MONTHLY_CLUSTERS = ["altermagnetism", "topological_insulators_semimetals", "spin_liquid_frustrated"]

# Material families and formulas shown in the Q3 chart (key -> display name).
MATERIAL_FAMILIES = {
    "altermagnet_candidates": "Altermagnet candidates",
    "tmds": "TMDs",
    "graphene_multilayers": "Graphene",
    "cuprates": "Cuprates",
    "vdw_magnets": "vdW magnets",
    "nickelates_bilayer_trilayer_rp": "RP bilayer/trilayer nickelates",
    "weyl_dirac_semimetals": "Weyl/Dirac semimetals",
    "mnbi2te4_bi2se3_tetradymites": "Tetradymites incl. MnBi2Te4",
    "other_kagome_metals": "Other kagome metals",
    "av3sb5_kagome": "AV3Sb5 kagome metals",
    "ext_kagome_more": "Further kagome compounds",
    "kitaev_materials": "Kitaev materials",
}
MATERIAL_FORMULAS = ["CrSb", "YBa2Cu3O7", "MnTe", "WSe2", "RuO2", "CrSBr", "UTe2", "CsV3Sb5", "La3Ni2O7"]

# The formula extractor in analysis/materials.py skips a formula written directly
# before "(", so it misses two trailing records that name the MnBi2Te4(Bi2Te3)n
# series (37 vs 52). Counting them gives 39 vs 52, whose CI includes 1, so the
# chart shows that count and findings.md calls MnBi2Te4 borderline.
MNBI2TE4_RECOUNT = {"label": "MnBi2Te4", "kind": "formula", "T": 39, "P": 52,
                    "R": 0.67, "lo": 0.44, "hi": 1.02,
                    "note": "Counts the two MnBi2Te4(Bi2Te3)n records that the formula extractor skips; without them it is "
                            "37 vs 52, CI 0.42-0.97. Borderline either way."}

SHORT_METHOD_NAMES = {
    "Magnetotransport / Hall / resistivity": "Magnetotransport / Hall",
    "Tight-binding / Wannier / continuum & effective models": "Tight-binding / continuum models",
    "Hartree-Fock / mean field / RPA / BdG": "Hartree-Fock / mean field",
    "Thin-film growth (MBE, PLD, CVD, sputtering)": "Thin-film growth",
    "Optical / infrared / THz / Raman / magneto-optics": "Optical / IR / THz / Raman",
    "Specific heat / magnetization / thermodynamics": "Specific heat / magnetization",
    "X-ray / electron diffraction & electron microscopy": "Diffraction / electron microscopy",
    "Phonons / electron-phonon / Eliashberg": "Phonons / electron-phonon",
    "Machine learning / neural networks": "Machine learning",
    "Ultrafast pump-probe / time-resolved": "Ultrafast pump-probe",
    "High pressure / diamond anvil cell": "High pressure / DAC",
    "DMFT / DFT+DMFT / cluster DMFT": "DMFT / DFT+DMFT",
    "RIXS / resonant & soft x-ray spectroscopy": "RIXS / resonant x-ray",
    "GW / BSE / hybrid functionals / quantum chemistry (beyond DFT)": "Beyond-DFT (GW, BSE, hybrids)",
    "muSR": "μSR",
    "NV-center / quantum sensing / scanning SQUID magnetometry": "NV / scanning-probe magnetometry",
}

SERVER_NAMES = {
    "osti": "OSTI.GOV", "researchsquare": "Research Square", "chemrxiv": "ChemRxiv",
    "preprints_org": "Preprints.org", "hal": "HAL", "zenodo": "Zenodo", "techrxiv": "TechRxiv",
}


def read_json(relative_path):
    with open(os.path.join(QM_DIR, relative_path), encoding="utf-8") as handle:
        return json.load(handle)


def strip_markdown(text):
    """Remove bold/italic markers and backticks; keep the words."""
    text = text.replace("**", "").replace("`", "")
    return text.strip()


def get_section(markdown, heading_prefix):
    """Return the text of the '## <heading_prefix>...' section, up to the next '## ' heading."""
    pattern = r"^## " + re.escape(heading_prefix) + r".*?$(.*?)(?=^## |\Z)"
    match = re.search(pattern, markdown, flags=re.MULTILINE | re.DOTALL)
    if not match:
        raise ValueError("section not found: " + heading_prefix)
    return match.group(1)


def get_labelled_line(section_text, label):
    """Return the text after '**<label>:**' on its line."""
    match = re.search(r"^\*\*" + re.escape(label) + r":\*\*\s*(.+)$", section_text, flags=re.MULTILINE)
    return strip_markdown(match.group(1)) if match else ""


def get_table(section_text, first_header):
    """Parse the markdown table whose header row starts with '| <first_header> |'."""
    lines = section_text.splitlines()
    for start, line in enumerate(lines):
        if line.startswith("| " + first_header + " |"):
            break
    else:
        raise ValueError("table not found: " + first_header)
    header = split_row(lines[start])
    rows = []
    for line in lines[start + 2:]:  # skip the |---| separator
        if not line.startswith("|"):
            break
        cells = split_row(line)
        rows.append(dict(zip(header, cells)))
    return rows


def split_row(line):
    return [strip_markdown(cell) for cell in line.strip().strip("|").split("|")]


def parse_cluster_cell(cell):
    """'Altermagnetism (altermagnetism)' -> ('Altermagnetism', 'altermagnetism')."""
    match = re.match(r"^(.*) \(([a-z0-9_]+)\)$", cell)
    return (match.group(1), match.group(2)) if match else (cell, cell)


def parse_ci(cell):
    low, high = cell.split("-")
    return float(low), float(high)


def to_int(cell):
    return int(cell.replace(",", ""))


def build_clusters(markdown):
    q1_rows = get_table(get_section(markdown, "Q1"), "Cluster")
    q2_rows = get_table(get_section(markdown, "Q2"), "Cluster")
    q2_by_key = {parse_cluster_cell(row["Cluster"])[1]: row for row in q2_rows}

    clusters = []
    for row in q1_rows:
        full_name, key = parse_cluster_cell(row["Cluster"])
        if key == "unclassified":
            continue
        q2 = q2_by_key[key]
        ci_low, ci_high = parse_ci(q2["95% CI"])
        clusters.append({
            "key": key,
            "name": full_name,
            "short_name": SHORT_CLUSTER_NAMES.get(key, full_name),
            "residual": key in RESIDUAL_CLUSTERS,
            "trailing": to_int(row["Trailing 12 mo (primary)"]),
            "trailing_multi": to_int(row["Trailing (multi-label)"]),
            "preceding": to_int(row["Preceding 12 mo (primary)"]),
            "trend": q2["Label"],
            "R": float(q2["Share ratio R"]),
            "ci_low": ci_low,
            "ci_high": ci_high,
            "robustness": q2["Robustness note"],
            "families": row["Q3 leading material families"],
            "examples": row["Example IDs"],
        })
    return clusters


def build_monthly():
    momentum = read_json("analysis/momentum.json")
    monthly = momentum["monthly"]
    base = momentum["variants"]["primary_full_scope"]
    series = []
    for key in MONTHLY_CLUSTERS:
        shares = monthly["clusters"][key]["monthly_share"]
        counts = [round(share * total) for share, total in zip(shares, monthly["in_scope_per_month"])]
        cluster = base["clusters"][key]
        series.append({
            "key": key,
            "name": SHORT_CLUSTER_NAMES[key],
            "trend": cluster["label"],
            "share": shares,
            "count": counts,
            "share_trailing": cluster["share_T"],
            "share_preceding": cluster["share_P"],
            "R": cluster["R"],
        })
    return {
        "months": monthly["months"],
        "in_scope": monthly["in_scope_per_month"],
        "full_months": monthly["full_months"],
        "series": series,
    }


def build_materials():
    materials = read_json("analysis/materials.json")
    rows = []
    families = {row["label"]: row for row in materials["growth_ranking_families_min_support"]}
    for key, name in MATERIAL_FAMILIES.items():
        row = families[key]
        rows.append({"label": name, "kind": "family", "T": row["trailing"], "P": row["preceding"],
                     "R": row["share_ratio"], "lo": row["ci95_low"], "hi": row["ci95_high"], "note": ""})
    formulas = {row["label"]: row for row in materials["growth_ranking_formulas_min_support"]}
    for label in MATERIAL_FORMULAS:
        row = formulas[label]
        rows.append({"label": label, "kind": "formula", "T": row["trailing"], "P": row["preceding"],
                     "R": row["share_ratio"], "lo": row["ci95_low"], "hi": row["ci95_high"], "note": ""})
    rows.append(dict(MNBI2TE4_RECOUNT))
    rows.sort(key=lambda row: row["R"], reverse=True)
    return rows


def build_methods():
    methods = read_json("analysis/methods.json")
    rows = []
    for row in methods["methods"]:
        rows.append({"label": row["label"], "short_label": SHORT_METHOD_NAMES.get(row["label"], row["label"]),
                     "kind": row["kind"], "T": row["trailing"], "P": row["preceding"],
                     "R": row["share_ratio"], "lo": row["ci95_low"], "hi": row["ci95_high"]})
    rows.sort(key=lambda row: row["T"], reverse=True)
    return rows


def build_servers(markdown):
    rows = get_table(get_section(markdown, "Q5"), "Server")
    servers = []
    for row in rows:
        servers.append({
            "server": SERVER_NAMES.get(row["Server"], row["Server"]),
            "records": row["Records T / P"],
            "duplicate_share": row["arXiv-duplicate share"],
            "on_topic": row["On-topic (all audited)"],
            "fringe": row["Fringe"],
            "unique_on_topic": row["Unique on-topic T+P [95%] (T only)"],
            "noise": row["Noise rating"],
            "contribution": row["Unique contribution"],
        })
    return servers


def build_claims(markdown):
    rows = get_table(get_section(markdown, "Q6"), "Claim")
    claims = []
    for row in rows:
        score_cell = row["Noise score"]
        score = int(re.match(r"-?\d+", score_cell).group(0))
        claims.append({
            "claim": row["Claim"],
            "status": row["Status"],
            "supportive": row["Supportive (groups)"],
            "critical": row["Critical (groups)"],
            "score": score,
            "score_note": score_cell,
            "noisy": "noisy" in score_cell,
            "watch": "WATCH" in score_cell,
            "ids": row["IDs"],
        })
    return claims


def build_noise_filter(markdown):
    section = get_section(markdown, "Q6")
    block = section.split("**Noise filter:**", 1)[1]
    bullets = []
    for line in block.splitlines()[1:]:
        if line.startswith("- "):
            bullets.append(strip_markdown(line[2:]))
        elif bullets and not line.strip():
            break
    return bullets


def build_caveats(markdown):
    section = get_section(markdown, "Caveats and next steps")
    caveat_block = section.split("Possible next steps", 1)[0]
    return [strip_markdown(line[2:]) for line in caveat_block.splitlines() if line.startswith("- ")]


def run_citation_check():
    """Run verify_citations.py and pull out the corpus size and the final tally line."""
    result = subprocess.run([sys.executable, os.path.join(QM_DIR, "verify_citations.py")],
                            stdout=subprocess.PIPE, universal_newlines=True)
    output = result.stdout
    corpus_total = int(re.search(r"harvested corpus: (\d+) records", output).group(1))
    per_server = [{"server": name, "records": int(count)}
                  for name, count in re.findall(r"^  ([a-z_]+): (\d+)$", output, flags=re.MULTILINE)]
    tally = re.search(r"cited IDs: (\d+) \| found in corpus: (\d+) \| missing: (\d+)", output)
    return {
        "corpus_total": corpus_total,
        "per_server": per_server,
        "cited": int(tally.group(1)),
        "found": int(tally.group(2)),
        "missing": int(tally.group(3)),
        "tally_line": tally.group(0),
    }


def build_report_data():
    with open(os.path.join(QM_DIR, "findings.md"), encoding="utf-8") as handle:
        markdown = handle.read()
    momentum = read_json("analysis/momentum.json")
    base = momentum["variants"]["primary_full_scope"]
    clusters = build_clusters(markdown)

    headlines = {}
    for question in ["Q1", "Q2", "Q3", "Q4", "Q5", "Q6"]:
        headlines[question] = get_labelled_line(get_section(markdown, question), "Headline")

    return {
        "run_date": "2026-09-23",
        "windows": momentum["windows"],
        "scope_trailing": base["scope_T"],
        "scope_preceding": base["scope_P"],
        "label_rule": momentum["label_rule"],
        "scope_line": get_labelled_line(get_section(markdown, "Q1"), "Scope").replace(
            "The verbatim rule is under Scope and method.", "The verbatim rule is in findings.md (Scope and method)."),
        "headlines": headlines,
        "clusters": clusters,
        "monthly": build_monthly(),
        "materials": build_materials(),
        "methods": build_methods(),
        "servers": build_servers(markdown),
        "claims": build_claims(markdown),
        "noise_filter": build_noise_filter(markdown),
        "caveats": build_caveats(markdown),
        "verification": run_citation_check(),
    }


def main():
    data = build_report_data()
    with open(TEMPLATE_PATH, encoding="utf-8") as handle:
        template = handle.read()
    # Escape "</" so no string in the data can close the <script> tag early.
    data_json = json.dumps(data, ensure_ascii=False).replace("</", "<\\/")
    html = template.replace("__REPORT_DATA__", data_json)
    with open(OUTPUT_PATH, "w", encoding="utf-8") as handle:
        handle.write(html)
    print("wrote", OUTPUT_PATH, "({} clusters, {} claims, {} bytes)".format(
        len(data["clusters"]), len(data["claims"]), len(html)))


if __name__ == "__main__":
    main()
