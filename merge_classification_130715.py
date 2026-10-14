import json

with open('scratch_130715_allcases.json', encoding='utf-8') as f:
    cases = json.load(f)

manual_ids = {'050'}

pmap_priority = {
    'Auth': 1, 'Functional-High': 2, 'Functional-Low': 3, 'UI': 2,
    'Compatibility': 3, 'Edge': 3
}

def priority(c):
    cat = c['category']
    tags = c['tags']
    if cat in ('Functional-High', 'Auth'):
        return 1
    if 'Regression' in tags or 'UAT' in tags:
        return 2
    if cat == 'Edge':
        return 4
    return 3

for c in cases:
    exec_tag = 'Manual' if c['id'] in manual_ids else 'Automation'
    c['tags'] = [t for t in c['tags'] if t not in ('Automation', 'Manual')]
    c['tags'].append(exec_tag)
    c['execution_type'] = 'Manual' if exec_tag == 'Manual' else 'Automated'
    c['priority'] = priority(c)

with open('scratch_130715_allcases.json', 'w', encoding='utf-8') as f:
    json.dump(cases, f, ensure_ascii=False)

from collections import Counter
print('exec:', Counter(c['execution_type'] for c in cases))
print('priority:', Counter(c['priority'] for c in cases))
