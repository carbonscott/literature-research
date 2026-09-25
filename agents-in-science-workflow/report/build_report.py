"""Build agents-in-science-workflow/findings.html from the report sources.

Inputs (defaults are the files next to this script):
  source.html   HTML body fragment. Citations are written [@key] or
                [@key1; @key2]. It must contain the placeholders
                <!--CATALOG--> (replaced by the catalog table) and
                <!--REFERENCES--> (replaced by the numbered reference list),
                each exactly once.
  refs.json     JSON array of references:
                {"key", "kind" ("doi" | "arxiv" | "url"), "id", "title",
                 "authors", "venue", "year", "evidence", "supports"}.
                "id" is a bare DOI (10.xxxx/...), a bare arXiv ID
                (2304.05332) or a full URL (https://...).
  catalog.json  JSON array of catalog rows:
                {"name", "organization", "year", "stage", "spans", "autonomy",
                 "evidence_type", "ref_key", "one_line"}.
  template.html Full HTML page with {{BODY}} and {{BUILD_DATE}} placeholders.

What it does:
  1. Inserts the Q1 taxonomy table at <!--TAXONOMY--> (optional placeholder)
     and the catalog table (sorted by stage, then year, then name).
  2. Numbers references by order of first citation and turns each citation
     group into linked numbers, e.g. [3, 7].
  3. Inserts the reference list, one <li id="ref-N"> per cited reference.
  4. Fails (exit code 1) on an unknown citation key, a duplicate key in
     refs.json, a catalog ref_key missing from refs.json, or malformed input.
     Warns about references that are never cited and leaves them out.

The HTML contract the finished page must satisfy is documented in
../check_report.py, which checks the page independently. The orchestrator
writes everything in source.html except the catalog table and the reference
list, which this script fills in. Skeleton:

  <section class="question" id="q1"><h2>...</h2><p class="answer">... [@key]</p>
    ... <table id="taxonomy"> ... <span class="sys" data-stage="experiment"
    data-autonomy="L3">Coscientist</span> ... </table></section>
  <section class="question" id="q2"> ... <div id="q2-established">...</div>
    <div id="q2-claims">...</div> <div id="q2-benchmarks">...</div></section>
  ... q3, q4, q5 ...
  <section class="question" id="q6"> ... <ol id="discussion-prompts">
    <li class="prompt">... <a href="#q4">Q4</a> [@key]</li> ... </ol></section>
  <section id="appendix"><h2>Appendix</h2>
    <section id="catalog"><h3>System catalog</h3><!--CATALOG--></section>
    <section id="glossary"><h3>Glossary</h3><dl><dt>..</dt><dd>..</dd></dl></section>
    <section id="method-notes"><h3>Method notes</h3>...</section></section>
  <section id="references"><h2>References</h2><!--REFERENCES--></section>

Usage (from the repository root):
  python agents-in-science-workflow/report/build_report.py
  python agents-in-science-workflow/report/build_report.py \
      --source S.html --refs R.json --catalog C.json --out OUT.html
"""
import argparse
import datetime
import html
import json
import os
import re
import sys
import urllib.parse

REPORT_DIR = os.path.dirname(os.path.abspath(__file__))
CAMPAIGN_DIR = os.path.dirname(REPORT_DIR)
TEMPLATE_PATH = os.path.join(REPORT_DIR, "template.html")
DEFAULT_SOURCE_PATH = os.path.join(REPORT_DIR, "source.html")
DEFAULT_REFS_PATH = os.path.join(REPORT_DIR, "refs.json")
DEFAULT_CATALOG_PATH = os.path.join(REPORT_DIR, "catalog.json")
DEFAULT_OUTPUT_PATH = os.path.join(CAMPAIGN_DIR, "findings.html")

CATALOG_PLACEHOLDER = "<!--CATALOG-->"
TAXONOMY_PLACEHOLDER = "<!--TAXONOMY-->"
REFERENCES_PLACEHOLDER = "<!--REFERENCES-->"

# Workflow stages, in the order the catalog is sorted.
STAGE_ORDER = [
    "Literature & ideation",
    "Hypothesis generation",
    "Experiment design & self-driving labs",
    "Data analysis & simulation",
    "Writing & review",
]
# Short stage names used in the taxonomy table's data-stage attributes.
STAGE_SLUGS = {
    "Literature & ideation": "literature",
    "Hypothesis generation": "hypothesis",
    "Experiment design & self-driving labs": "experiment",
    "Data analysis & simulation": "analysis",
    "Writing & review": "writing",
}
AUTONOMY_ORDER = ["L1 Assistant", "L2 Tool-using agent", "L3 Closed-loop", "L4 End-to-end"]
CATALOG_COLUMNS = ["System", "Organization", "Year", "Stage", "Autonomy", "Evidence type", "Reference"]
REFERENCE_KINDS = ("doi", "arxiv", "url")

# A citation group: [@key] or [@key1; @key2; ...].
CITATION_KEY_CHARS = r"[\w:./-]+"
CITATION_GROUP = re.compile(r"\[\s*@" + CITATION_KEY_CHARS + r"(?:\s*;\s*@" + CITATION_KEY_CHARS + r")*\s*\]")
CITATION_KEY = re.compile(r"@(" + CITATION_KEY_CHARS + r")")

MAX_AUTHORS_SHOWN = 3


class BuildError(Exception):
    """A problem in the inputs that must stop the build."""


def escape(text):
    """HTML-escape text for use in element content or attribute values."""
    return html.escape(text, quote=True)


def as_text(value):
    """Turn a JSON field (string, number, list or null) into display text."""
    if value is None:
        return ""
    if isinstance(value, list):
        return "; ".join(as_text(item) for item in value if as_text(item))
    return str(value).strip()


def format_authors(authors):
    """Authors as one string; long lists are cut to the first few plus 'et al.'."""
    if isinstance(authors, list):
        names = [as_text(name) for name in authors if as_text(name)]
        if len(names) > MAX_AUTHORS_SHOWN:
            return ", ".join(names[:MAX_AUTHORS_SHOWN]) + " et al."
        return ", ".join(names)
    return as_text(authors)


def display_title(title):
    """Title as plain text: Crossref titles can carry markup such as <i>...</i> or entities."""
    return " ".join(html.unescape(re.sub(r"<[^>]+>", "", title)).split())


def closing_period(text):
    """Return "." unless the text already ends with punctuation."""
    return "" if text.endswith((".", "?", "!")) else "."


def load_json_list(path, description):
    """Read a JSON file that must hold an array."""
    if not os.path.isfile(path):
        raise BuildError("%s not found: %s" % (description, path))
    with open(path, encoding="utf-8") as handle:
        try:
            data = json.load(handle)
        except ValueError as error:
            raise BuildError("%s is not valid JSON (%s): %s" % (description, error, path))
    if not isinstance(data, list):
        raise BuildError("%s must be a JSON array: %s" % (description, path))
    return data


def validate_reference(ref, position):
    """Return a list of problems with one refs.json entry (empty if fine)."""
    label = "refs.json entry %d (key %r)" % (position, ref.get("key"))
    kind = as_text(ref.get("kind"))
    ref_id = as_text(ref.get("id"))
    problems = []
    if not re.match(r"^" + CITATION_KEY_CHARS + r"$", as_text(ref.get("key"))):
        problems.append("%s: 'key' must be non-empty and use only letters, digits and _ : . / -" % label)
    if kind not in REFERENCE_KINDS:
        problems.append("%s: 'kind' must be one of %s, got %r" % (label, ", ".join(REFERENCE_KINDS), kind))
    if not ref_id:
        problems.append("%s: missing 'id'" % label)
    elif kind == "doi" and not ref_id.startswith("10."):
        problems.append("%s: a doi id must be a bare DOI such as 10.1038/..., got %r" % (label, ref_id))
    elif kind == "arxiv" and (ref_id.lower().startswith("arxiv:") or "/abs/" in ref_id):
        problems.append("%s: an arxiv id must be a bare ID such as 2304.05332, got %r" % (label, ref_id))
    elif kind == "url" and not ref_id.startswith(("http://", "https://")):
        problems.append("%s: a url id must start with http:// or https://, got %r" % (label, ref_id))
    if not as_text(ref.get("title")):
        problems.append("%s: missing 'title'" % label)
    return problems


def load_references(path):
    """Read refs.json; return ({key: ref}, warnings). Fails on duplicate keys."""
    refs = load_json_list(path, "refs.json")
    problems = []
    refs_by_key = {}
    duplicate_keys = []
    for position, ref in enumerate(refs, start=1):
        if not isinstance(ref, dict):
            problems.append("refs.json entry %d is not an object" % position)
            continue
        problems.extend(validate_reference(ref, position))
        key = as_text(ref.get("key"))
        if key in refs_by_key:
            duplicate_keys.append(key)
        refs_by_key[key] = ref
    if duplicate_keys:
        problems.append("duplicate keys in refs.json: " + ", ".join(sorted(set(duplicate_keys))))
    if problems:
        raise BuildError("\n".join(problems))

    warnings = []
    keys_by_id = {}
    for key, ref in refs_by_key.items():
        identity = (as_text(ref["kind"]), as_text(ref["id"]).lower())
        keys_by_id.setdefault(identity, []).append(key)
    for (kind, ref_id), keys in keys_by_id.items():
        if len(keys) > 1:
            warnings.append("same %s %s under several keys: %s" % (kind, ref_id, ", ".join(keys)))
    return refs_by_key, warnings


def load_catalog(path, refs_by_key):
    """Read catalog.json; return (rows, warnings). Fails on unknown ref_key."""
    rows = load_json_list(path, "catalog.json")
    missing = []
    warnings = []
    stage_names = [stage.lower() for stage in STAGE_ORDER]
    for position, row in enumerate(rows, start=1):
        if not isinstance(row, dict):
            raise BuildError("catalog.json row %d is not an object" % position)
        name = as_text(row.get("name")) or "(row %d)" % position
        ref_key = as_text(row.get("ref_key"))
        if ref_key not in refs_by_key:
            missing.append("%s -> %r" % (name, ref_key))
        if as_text(row.get("stage")).lower() not in stage_names:
            warnings.append("catalog row %r has unknown stage %r (sorted last); expected one of: %s"
                            % (name, as_text(row.get("stage")), "; ".join(STAGE_ORDER)))
    if missing:
        raise BuildError("catalog ref_key not found in refs.json: " + ", ".join(missing))
    return rows, warnings


def catalog_sort_key(row):
    """Sort by stage order, then year, then name."""
    stage = as_text(row.get("stage")).lower()
    stage_names = [name.lower() for name in STAGE_ORDER]
    stage_index = stage_names.index(stage) if stage in stage_names else len(stage_names)
    try:
        year = int(as_text(row.get("year")))
    except ValueError:
        year = 9999
    return (stage_index, year, as_text(row.get("name")).lower())


def catalog_table_html(rows):
    """The catalog <table>; reference cells hold [@key] so they get numbered later."""
    lines = ['<div class="table-scroll">', '<table id="catalog-table">', "<thead><tr>"]
    lines.append("".join("<th>%s</th>" % escape(column) for column in CATALOG_COLUMNS))
    lines.append("</tr></thead>")
    lines.append("<tbody>")
    for row in sorted(rows, key=catalog_sort_key):
        name_cell = '<span class="system-name">%s</span>' % escape(as_text(row.get("name")))
        if as_text(row.get("one_line")):
            name_cell += '<span class="one-line">%s</span>' % escape(as_text(row.get("one_line")))
        stage_cell = escape(as_text(row.get("stage")))
        if as_text(row.get("spans")):
            stage_cell += '<span class="spans">spans: %s</span>' % escape(as_text(row.get("spans")))
        cells = [
            "<td>%s</td>" % name_cell,
            "<td>%s</td>" % escape(as_text(row.get("organization"))),
            '<td class="num">%s</td>' % escape(as_text(row.get("year"))),
            "<td>%s</td>" % stage_cell,
            "<td>%s</td>" % escape(as_text(row.get("autonomy"))),
            "<td>%s</td>" % escape(as_text(row.get("evidence_type"))),
            "<td>[@%s]</td>" % as_text(row.get("ref_key")),
        ]
        lines.append("<tr>" + "".join(cells) + "</tr>")
    lines.append("</tbody>")
    lines.append("</table>")
    lines.append("</div>")
    return "\n".join(lines)


def taxonomy_table_html(rows):
    """The Q1 stage x autonomy table: one pill per cataloged system.

    Facility and national-lab systems (catalog lane "facility") get an extra
    class so they stand out; the checker reads data-stage and data-autonomy.
    """
    lines = ['<div class="table-scroll">', '<table id="taxonomy">', "<thead><tr><th>Stage</th>"]
    lines.append("".join("<th>%s</th>" % escape(level) for level in AUTONOMY_ORDER))
    lines.append("<th class=\"num\">Total</th></tr></thead>")
    lines.append("<tbody>")
    for stage in STAGE_ORDER:
        stage_rows = [row for row in rows if as_text(row.get("stage")) == stage]
        cells = ["<th>%s</th>" % escape(stage)]
        for level in AUTONOMY_ORDER:
            level_rows = sorted((row for row in stage_rows if as_text(row.get("autonomy")) == level),
                                key=lambda row: (as_text(row.get("lane")) == "facility", as_text(row.get("name")).lower()))
            pills = []
            for row in level_rows:
                css_class = "sys facility" if as_text(row.get("lane")) == "facility" else "sys"
                pills.append('<span class="%s" data-stage="%s" data-autonomy="%s">%s</span>' % (
                    css_class, STAGE_SLUGS[stage], escape(level.split()[0]), escape(as_text(row.get("name")))))
            cells.append("<td>%s</td>" % " ".join(pills))
        cells.append('<td class="num">%d</td>' % len(stage_rows))
        lines.append("<tr>" + "".join(cells) + "</tr>")
    totals = ['<td class="num">%d</td>' % sum(1 for row in rows if as_text(row.get("autonomy")) == level)
              for level in AUTONOMY_ORDER]
    lines.append("<tr><th>Total</th>" + "".join(totals) + '<td class="num">%d</td></tr>' % len(rows))
    lines.append("</tbody>")
    lines.append("</table>")
    lines.append("</div>")
    return "\n".join(lines)


def number_citations(body, refs_by_key):
    """Replace citation groups with linked numbers.

    Numbers follow the order of first citation in the body. Returns
    (new_body, cited_keys) where cited_keys[i] has number i + 1.
    """
    number_by_key = {}
    cited_keys = []
    unknown_keys = []

    def replace_group(match):
        numbers = []
        for key in CITATION_KEY.findall(match.group(0)):
            if key not in refs_by_key:
                unknown_keys.append(key)
                continue
            if key not in number_by_key:
                cited_keys.append(key)
                number_by_key[key] = len(cited_keys)
            numbers.append(number_by_key[key])
        links = ['<a class="cite" href="#ref-%d">%d</a>' % (number, number) for number in sorted(set(numbers))]
        return '<span class="cites">[' + ", ".join(links) + "]</span>"

    new_body = CITATION_GROUP.sub(replace_group, body)
    if unknown_keys:
        raise BuildError("unknown citation keys (not in refs.json): " + ", ".join(sorted(set(unknown_keys))))
    leftover = new_body.find("[@")
    if leftover != -1:
        context = new_body[leftover:leftover + 60].replace("\n", " ")
        raise BuildError("malformed citation (use [@key] or [@key1; @key2]) near: %s" % context)
    return new_body, cited_keys


def reference_link(ref):
    """Return (href, link_text) for a reference."""
    kind = as_text(ref["kind"])
    ref_id = as_text(ref["id"])
    if kind == "doi":
        return "https://doi.org/" + urllib.parse.quote(ref_id, safe="/:;()._-"), "doi:" + ref_id
    if kind == "arxiv":
        return "https://arxiv.org/abs/" + ref_id, "arXiv:" + ref_id
    return ref_id, "link"


def reference_item_html(number, ref):
    """One <li> of the reference list."""
    href, link_text = reference_link(ref)
    parts = []
    authors = format_authors(ref.get("authors"))
    if authors:
        parts.append('<span class="ref-authors">%s</span>%s' % (escape(authors), closing_period(authors)))
    title = display_title(as_text(ref["title"]))
    parts.append('<span class="ref-title">%s</span>%s' % (escape(title), closing_period(title)))
    venue = as_text(ref.get("venue"))
    year = as_text(ref.get("year"))
    if venue and year:
        parts.append('<span class="ref-venue">%s</span> (<span class="ref-year">%s</span>).' % (escape(venue), escape(year)))
    elif venue:
        parts.append('<span class="ref-venue">%s</span>%s' % (escape(venue), closing_period(venue)))
    elif year:
        parts.append('(<span class="ref-year">%s</span>).' % escape(year))
    parts.append('<a href="%s">%s</a>' % (escape(href), escape(link_text)))
    evidence = as_text(ref.get("evidence"))
    if evidence:
        parts.append('<span class="ref-evidence">[%s]</span>' % escape(evidence))
    return '<li id="ref-%d" data-kind="%s" data-id="%s">%s</li>' % (
        number, escape(as_text(ref["kind"])), escape(as_text(ref["id"])), " ".join(parts))


def reference_list_html(cited_keys, refs_by_key):
    """The numbered <ol class="references">."""
    items = [reference_item_html(number, refs_by_key[key]) for number, key in enumerate(cited_keys, start=1)]
    return '<ol class="references">\n' + "\n".join(items) + "\n</ol>"


def replace_placeholder(text, placeholder, replacement):
    """Replace a placeholder that must occur exactly once."""
    count = text.count(placeholder)
    if count != 1:
        raise BuildError("source.html must contain %s exactly once (found %d)" % (placeholder, count))
    return text.replace(placeholder, replacement)


def build(source_path, refs_path, catalog_path, out_path):
    """Build the page; return a summary dict. Raises BuildError on bad input."""
    if not os.path.isfile(source_path):
        raise BuildError("source.html not found: %s" % source_path)
    with open(source_path, encoding="utf-8") as handle:
        body = handle.read()
    with open(TEMPLATE_PATH, encoding="utf-8") as handle:
        template = handle.read()

    refs_by_key, warnings = load_references(refs_path)
    catalog_rows, catalog_warnings = load_catalog(catalog_path, refs_by_key)
    warnings.extend(catalog_warnings)

    if TAXONOMY_PLACEHOLDER in body:
        body = replace_placeholder(body, TAXONOMY_PLACEHOLDER, taxonomy_table_html(catalog_rows))
    body = replace_placeholder(body, CATALOG_PLACEHOLDER, catalog_table_html(catalog_rows))
    body, cited_keys = number_citations(body, refs_by_key)
    body = replace_placeholder(body, REFERENCES_PLACEHOLDER, reference_list_html(cited_keys, refs_by_key))

    uncited_keys = [key for key in refs_by_key if key not in cited_keys]
    for key in uncited_keys:
        warnings.append("reference %r is never cited; left out of the list" % key)

    page = template.replace("{{BUILD_DATE}}", datetime.date.today().isoformat())
    page = page.replace("{{BODY}}", body)
    with open(out_path, "w", encoding="utf-8") as handle:
        handle.write(page)
    return {
        "out_path": out_path,
        "bytes": os.path.getsize(out_path),
        "references": len(cited_keys),
        "catalog_rows": len(catalog_rows),
        "warnings": warnings,
    }


def main():
    parser = argparse.ArgumentParser(description="Build findings.html from source.html, refs.json and catalog.json.")
    parser.add_argument("--source", default=DEFAULT_SOURCE_PATH, help="HTML body fragment (default: report/source.html)")
    parser.add_argument("--refs", default=DEFAULT_REFS_PATH, help="references JSON (default: report/refs.json)")
    parser.add_argument("--catalog", default=DEFAULT_CATALOG_PATH, help="catalog JSON (default: report/catalog.json)")
    parser.add_argument("--out", default=DEFAULT_OUTPUT_PATH, help="output page (default: findings.html in the campaign folder)")
    args = parser.parse_args()
    sys.stdout.reconfigure(errors="replace")

    try:
        summary = build(args.source, args.refs, args.catalog, args.out)
    except BuildError as error:
        print("build_report: ERROR\n" + str(error), file=sys.stderr)
        sys.exit(1)

    print("wrote %s (%d bytes)" % (summary["out_path"], summary["bytes"]))
    print("references numbered: %d" % summary["references"])
    print("catalog rows: %d" % summary["catalog_rows"])
    print("warnings: %d" % len(summary["warnings"]))
    for warning in summary["warnings"]:
        print("  WARNING: " + warning)


if __name__ == "__main__":
    main()
