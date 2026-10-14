import re, json

path = r'C:\Users\Heba.Samir\.claude\projects\d--MCP-servers-QaterChamper\12c5af37-ddf6-450c-ac4b-a278dc26a313\tool-results\toolu_01W2U6Rc3p6zWEReLPHPVsca.txt'
with open(path, encoding='utf-8') as f:
    content = f.read()

start = content.index('## §3. Test Cases')
end = content.index('## Assumptions')
section = content[start:end]

# tokenize: find all category headings and case markers in order
token_re = re.compile(r'### Category: ([\w-]+).*?\((\d+) cases?\)|\*\*MEDIA-PODCAST-TC-(\d+)\*\*\s*—\s*(.+)')
positions = [(m.start(), m) for m in token_re.finditer(section)]

current_cat = None
case_starts = []  # (start_pos, id, title, category)
for pos, m in positions:
    if m.group(1):
        current_cat = m.group(1)
    else:
        case_starts.append((pos, m.group(3), m.group(4).strip(), current_cat))

cases = []
for i, (pos, num, title, category) in enumerate(case_starts):
    end_pos = case_starts[i+1][0] if i+1 < len(case_starts) else len(section)
    b = section[pos:end_pos]

    m2 = re.search(r'test_type=(\w+),\s*scenario=(\w+),\s*impact_area=(\w+),\s*priority=(\d),\s*execution_type=(\w+)', b)
    test_type, scenario, impact_area, priority, execution_type = m2.groups()

    m3 = re.search(r'Tags:\s*(\[.*?\])', b)
    tags = json.loads(m3.group(1)) if m3 else []

    m4 = re.search(r'Traceability:\s*(.+)', b)
    trace_raw = m4.group(1).strip() if m4 else ''
    traceability = [t.strip() for t in trace_raw.split(',') if t.strip()]

    m5 = re.search(r'Steps.?Expected:\s*(.+?)(?:\ntest_type=)', b, re.S)
    steps_raw = m5.group(1).strip() if m5 else ''

    SPLIT_RE = re.compile(r'(?:(?<=^)|(?<=\. ))\d+\)\s+')
    parts = list(SPLIT_RE.finditer(steps_raw))
    chunks = []
    if parts:
        bounds = [p.end() for p in parts]
        starts_ = [p.start() for p in parts]
        for j in range(len(starts_)):
            s0 = bounds[j]
            s1 = starts_[j+1] if j+1 < len(starts_) else len(steps_raw)
            chunks.append(steps_raw[s0:s1].strip())
    else:
        chunks = [steps_raw.strip()]

    steps_list = []
    expected_list = []
    for c in chunks:
        if '\u2192' in c:
            step_part, exp_part = c.split('\u2192', 1)
        elif '->' in c:
            step_part, exp_part = c.split('->', 1)
        else:
            step_part, exp_part = c, c
        step_part = step_part.strip().rstrip('.').strip()
        exp_part = exp_part.strip().rstrip('.').strip()
        steps_list.append(step_part + '.')
        expected_list.append(exp_part + '.')

    case = {
        'id': num.zfill(3),
        'title': title,
        'category': category,
        'tags': tags,
        'traceability': traceability,
        'steps_list': steps_list,
        'expected_list': expected_list,
        'expected': ' '.join(expected_list),
        'test_type': test_type,
        'scenario': scenario,
        'execution_type': None,
        'impact_area': impact_area,
        'language': 'en',
        'priority': int(priority),
    }
    cases.append(case)

print('parsed', len(cases), 'cases')
mismatches = [c['id'] for c in cases if len(c['steps_list']) != len(c['expected_list'])]
print('mismatched steps/expected count:', mismatches)
cats = {}
for c in cases:
    cats[c['category']] = cats.get(c['category'], 0) + 1
print('by category:', cats)
none_cat = [c['id'] for c in cases if c['category'] is None]
print('no category:', none_cat)

with open('scratch_130713_allcases.json', 'w', encoding='utf-8') as f:
    json.dump(cases, f, ensure_ascii=False)
