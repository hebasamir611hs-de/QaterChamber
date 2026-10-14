import json

# All 185 = Automation per classification pass
with open('scratch_130713_allcases_merged.json', encoding='utf-8') as f:
    cases = json.load(f)

cat_priority_map = {
    'Functional-High': 1, 'Auth': 1,
    'UI': 2, 'Compatibility': 3,
    'Functional-Low': 3,
    'Edge': 4,
}

for c in cases:
    c['execution_type'] = 'Automation'
    if 'Automation' not in c['tags']:
        c['tags'].append('Automation')

with open('scratch_130713_allcases_final.json', 'w', encoding='utf-8') as f:
    json.dump(cases, f, ensure_ascii=False)

auto_count = sum(1 for c in cases if c['execution_type'] == 'Automation')
print('Automation:', auto_count, 'total:', len(cases))
