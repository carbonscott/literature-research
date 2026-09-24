import sys, pickle, re
from collections import Counter, defaultdict
sys.path.insert(0, '.')
import materials as m
recs = pickle.load(open(sys.argv[1],'rb'))
tr = [r for r in recs if r['window']=='trailing']
texts = m.load_texts(set(r['id'] for r in tr))
checks = {
 'ext_ferroelectrics_multiferroics': re.compile(r'(?i:\bmultiferroics?\b)'),
 'semiconductor_2deg_and_qw': re.compile(r'(?i:\bquantum wells?\b|\bnanowires?\b)'),
 'frustrated_rare_earth_and_triangular': re.compile(r'(?i:\bherbertsmithite|\bpyrochlore)'),
 'kitaev_materials': re.compile(r'(?i:\bkitaev materials?|\bhoneycomb cobaltate|\bhoneycomb iridate)'),
 'iridates_mott_oxides': re.compile(r'1T-TaS2|(?i:\biridates?\b|\bmanganites?\b|\brare[- ]earth nickelate)'),
 'cuprates': re.compile(r'(?i:\bcuprates?\b)'),
 'srtio3_ktao3_oxide_interfaces': re.compile(r'(?i:\boxide interface|\boxide heterostructure)'),
 'tmds': re.compile(r'(?i:\btransition[- ]metal dichalcogenide)|\bTMDs?\b|\bTMDCs?\b'),
}
by = defaultdict(list)
for r in tr: by[r['primary_cluster'] or '_unclassified'].append(r)
for c, rs in sorted(by.items()):
    for fam, generic in checks.items():
        rx = m.ALL_FAMILY_REGEXES[fam]
        n = 0; wo = 0
        for r in rs:
            if fam not in r['all_families']: continue
            n += 1
            hits = [mm.group(0) for mm in rx.finditer(texts[r['id']]['text'])]
            if all(generic.fullmatch(h) for h in hits): wo += 1
        if n >= 5: print(c, fam, n, 'word-only', wo)
