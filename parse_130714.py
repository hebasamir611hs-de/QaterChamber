import re, json

path = r'C:\Users\Heba.Samir\.claude\projects\d--MCP-servers-QaterChamper\12c5af37-ddf6-450c-ac4b-a278dc26a313\tool-results\toolu_01MZ4mpWNwiUgBhaGYxrPfTh.txt'
with open(path, encoding='utf-8') as f:
    content = f.read()

# isolate the test cases section
start = content.index('## §3. Test Cases')
end = content.index('## §4. Assumptions')
section = content[start:end]

# split into case blocks
blocks = re.split(r'\n(?=\*\*MEDIA-PHOTOGALLERY-TC-\d+)', section)

cases = []
category_map = {
    'UI': 'UI', 'Compatibility': 'Compatibility', 'Auth': 'Auth',
    'Functional-High': 'Functional-High', 'Functional-Low': 'Functional-Low', 'Edge': 'Edge'
}

for b in blocks:
    m = re.search(r'\*\*MEDIA-PHOTOGALLERY-TC-(\d+)\s*—\s*(.+?)\*\*', b)
    if not m:
        continue
    num = m.group(1)
    title = m.group(2).strip()

    m2 = re.search(r'\n([A-Za-z\-]+) \| ([A-Za-z]+) \| (positive|negative) \| (\w+) \| (\d) \| (\w+)', b)
    if not m2:
        print('WARN no meta line for', num)
        continue
    category, test_type, scenario, impact_area, priority, language = m2.groups()

    m3 = re.search(r'Tags:\s*(\[.*?\])', b)
    tags = json.loads(m3.group(1)) if m3 else []

    m4 = re.search(r'Traceability:\s*\[(.*?)\]', b)
    trace_raw = m4.group(1) if m4 else ''
    traceability = [t.strip() for t in trace_raw.split(',') if t.strip()]

    m5 = re.search(r'Steps:\s*(.+?)\nExpected:', b, re.S)
    steps_raw = m5.group(1).strip() if m5 else ''
    m6 = re.search(r'Expected:\s*(.+?)(?:\n\n|\Z)', b, re.S)
    expected_raw = m6.group(1).strip() if m6 else ''

    SPLIT_RE = re.compile(r'(?:(?<=^)|(?<=\. ))\d+\)\s+(?=["“\'A-Z0-9])')

    def split_numbered(s):
        s = re.sub(r'\*\(.*?\)\*\s*$', '', s.strip())
        matches = list(SPLIT_RE.finditer(s))
        if not matches:
            return [s.strip().rstrip('.') + '.'] if s.strip() else []
        bounds = [m.end() for m in matches]
        starts = [m.start() for m in matches]
        text_chunks = []
        for i in range(len(starts)):
            s0 = bounds[i]
            s1 = starts[i+1] if i+1 < len(starts) else len(s)
            text_chunks.append(s[s0:s1].strip())
        return [c.rstrip('.').strip() + '.' for c in text_chunks if c]

    steps_list = split_numbered(steps_raw)
    expected_list = split_numbered(expected_raw)

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
        'language': language,
        'priority': int(priority),
    }
    cases.append(case)

print('parsed', len(cases), 'cases')
# sanity: mismatched steps/expected counts
mismatches = [c['id'] for c in cases if len(c['steps_list']) != len(c['expected_list'])]
print('mismatched steps/expected count:', mismatches)

with open('scratch_130714_allcases.json', 'w', encoding='utf-8') as f:
    json.dump(cases, f, ensure_ascii=False)
