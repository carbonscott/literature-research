import sys, json, re, pickle
from collections import Counter, defaultdict
sys.path.insert(0, '.')
import materials as m
recs = m.build_records()
tr = [r for r in recs if r['window'] == 'trailing']
pickle.dump(recs, open(sys.argv[1], 'wb'))
by = defaultdict(list)
for r in tr: by[r['primary_cluster'] or '_unclassified'].append(r)
# need texts
texts = m.load_texts(set(r['id'] for r in tr))
for c, rs in sorted(by.items()):
    fc = Counter(f for r in rs for f in r['all_families'])
    print('==', c, len(rs))
    for fam, n in fc.most_common(4):
        rx = m.ALL_FAMILY_REGEXES[fam]
        terms = Counter()
        for r in rs:
            if fam in r['all_families']:
                hits = set(mm.group(0) for mm in rx.finditer(texts[r['id']]['text']))
                terms.update(hits)
        print('  ', fam, n, terms.most_common(8))
