import json

classification = """001: Automation
002: Automation
003: Automation
004: Automation
005: Automation
006: Automation
007: Automation
008: Automation
009: Automation
010: Automation
011: Automation
012: Automation
013: Automation
014: Automation
015: Automation
016: Automation
017: Automation
018: Automation
019: Automation
020: Automation
021: Automation
022: Automation
023: Automation
024: Automation
025: Automation
026: Automation
027: Automation
028: Automation
029: Automation
030: Automation
031: Automation
032: Automation
033: Automation
034: Automation
035: Automation
036: Automation
037: Automation
038: Automation
039: Automation
040: Automation
041: Automation
042: Automation
043: Automation
044: Automation
045: Manual
046: Automation
047: Automation
048: Automation
049: Automation
050: Automation
051: Automation
052: Automation
053: Automation
054: Automation
055: Automation
056: Automation
057: Automation
058: Automation
059: Automation
060: Automation
061: Automation
062: Automation
063: Automation
064: Automation
065: Automation
066: Automation
067: Automation
068: Automation
069: Automation
070: Automation
071: Automation
072: Automation
073: Automation
074: Automation
075: Automation
076: Manual
077: Automation
078: Automation
079: Automation
080: Automation
081: Automation
082: Automation
083: Automation
084: Automation
085: Manual
086: Automation"""

exec_map = {}
for line in classification.strip().split("\n"):
    cid, val = line.split(":")
    exec_map[cid.strip()] = val.strip()

with open('scratch_130714_allcases.json', encoding='utf-8') as f:
    cases = json.load(f)

cat_priority = {
    'Auth': 1, 'Functional-High': 1,
    'Regression': 2, 'UAT': 2,
    'Compatibility': 3, 'UI': 3,
    'Functional-Low': 3,
    'Edge': 4,
}

for c in cases:
    ex = exec_map[c['id']]
    c['execution_type'] = ex
    c['tags'].append(ex)
    # priority heuristic (category-based), consistent with 130715 approach
    cat = c['category']
    if cat in ('Functional-High', 'Auth'):
        c['priority'] = 1
    elif 'Regression' in c['tags'] or 'UAT' in c['tags']:
        c['priority'] = 2
    elif cat == 'Edge':
        c['priority'] = 4
    else:
        c['priority'] = 3

with open('scratch_130714_allcases_final.json', 'w', encoding='utf-8') as f:
    json.dump(cases, f, ensure_ascii=False)

manual_count = sum(1 for c in cases if c['execution_type'] == 'Manual')
auto_count = sum(1 for c in cases if c['execution_type'] == 'Automation')
print('Automation:', auto_count, 'Manual:', manual_count, 'total:', len(cases))
