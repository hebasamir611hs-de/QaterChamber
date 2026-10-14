import re, json

def split_numbered(steps_raw):
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
    return chunks

def build_steps_expected(chunks):
    arrow = '\u2192'
    has_any_arrow = any(arrow in c for c in chunks)
    all_have_arrow = all(arrow in c for c in chunks)
    if all_have_arrow:
        steps_list, expected_list = [], []
        for c in chunks:
            step_part, exp_part = c.split(arrow, 1)
            steps_list.append(step_part.strip().rstrip('.').strip() + '.')
            expected_list.append(exp_part.strip().rstrip('.').strip() + '.')
        return steps_list, expected_list
    else:
        # mixed or no-arrow: combine into one step / one expected
        if len(chunks) == 1:
            c = chunks[0]
            if arrow in c:
                step_part, exp_part = c.split(arrow, 1)
                return [step_part.strip().rstrip('.').strip() + '.'], [exp_part.strip().rstrip('.').strip() + '.']
            else:
                return [c.strip().rstrip('.').strip() + '.'], [c.strip().rstrip('.').strip() + '.']
        else:
            step_chunks = chunks[:-1]
            last = chunks[-1]
            if arrow in last:
                last_step, last_exp = last.split(arrow, 1)
                combined_step = '; '.join(x.strip().rstrip('.') for x in step_chunks) + '; ' + last_step.strip().rstrip('.')
                expected = last_exp.strip().rstrip('.')
            else:
                combined_step = '; '.join(x.strip().rstrip('.') for x in step_chunks)
                expected = last.strip().rstrip('.')
            return [combined_step.strip() + '.'], [expected.strip() + '.']

# --- Parse main doc cases 001-090 ---
path = r'C:\Users\Heba.Samir\.claude\projects\d--MCP-servers-QaterChamper\12c5af37-ddf6-450c-ac4b-a278dc26a313\tool-results\toolu_01W2U6Rc3p6zWEReLPHPVsca.txt'
with open(path, encoding='utf-8') as f:
    content = f.read()
start = content.index('## §3. Test Cases')
end = content.index('## Assumptions')
section = content[start:end]
# Cut off before Functional-Low block (091+) since that has its own raw file
fl_start = section.index('### Category: Functional-Low')
section_main = section[:fl_start]

blocks = re.split(r'\n(?=\*\*MEDIA-PODCAST-TC-\d+)', section_main)
fixed = {}
for b in blocks:
    m = re.search(r'\*\*MEDIA-PODCAST-TC-(\d+)\*\*', b)
    if not m:
        continue
    num = m.group(1).zfill(3)
    m5 = re.search(r'Steps.?Expected:\s*(.+?)(?:\ntest_type=)', b, re.S)
    steps_raw = m5.group(1).strip() if m5 else ''
    chunks = split_numbered(steps_raw)
    steps_list, expected_list = build_steps_expected(chunks)
    fixed[num] = (steps_list, expected_list)

print('main parsed:', len(fixed))

# --- Parse funclow raw cases 091-185 ---
with open('scratch_130713_funclow_raw.txt', encoding='utf-8') as f:
    fl_content = f.read()
fl_blocks = re.split(r'\n(?=\*\*MEDIA-PODCAST-TC-\d+)', fl_content)
for b in fl_blocks:
    m = re.search(r'\*\*MEDIA-PODCAST-TC-(\d+)\*\*', b)
    if not m:
        continue
    num = m.group(1).zfill(3)
    m5 = re.search(r'Steps.?Expected:\s*(.+?)(?:\ntest_type=)', b, re.S)
    steps_raw = m5.group(1).strip() if m5 else ''
    chunks = split_numbered(steps_raw)
    steps_list, expected_list = build_steps_expected(chunks)
    fixed[num] = (steps_list, expected_list)

print('total parsed (incl funclow):', len(fixed))

# --- Apply to merged cases ---
with open('scratch_130713_allcases_merged.json', encoding='utf-8') as f:
    cases = json.load(f)

mismatch_count = 0
dup_count = 0
for c in cases:
    cid = c['id']
    if cid not in fixed:
        print('MISSING fix for', cid)
        continue
    steps_list, expected_list = fixed[cid]
    if len(steps_list) != len(expected_list):
        mismatch_count += 1
        print('mismatch', cid, len(steps_list), len(expected_list))
    if steps_list == expected_list:
        dup_count += 1
    c['steps_list'] = steps_list
    c['expected_list'] = expected_list
    c['expected'] = ' '.join(expected_list)

print('mismatches:', mismatch_count, 'still-duplicate cases:', dup_count)

with open('scratch_130713_allcases_merged.json', 'w', encoding='utf-8') as f:
    json.dump(cases, f, ensure_ascii=False)
