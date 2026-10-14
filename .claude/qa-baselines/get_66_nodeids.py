import re

with open(r".claude/qa-baselines/114_rerun_output.txt", encoding="utf-8", errors="replace") as f:
    content = f.read()

with open(r".claude/qa-baselines/114_failed_nodeids.txt", encoding="utf-8") as f:
    web_failed_nodeids = [l.strip() for l in f if l.strip().startswith("web/")]

# map short test name -> full node id(s)
name_to_nodeid = {}
for nid in web_failed_nodeids:
    short = nid.split("::")[-1]
    name_to_nodeid.setdefault(short, []).append(nid)

blocks = re.split(r"(?=^_{5,} test_)", content, flags=re.MULTILINE)
header_re = re.compile(r"^_+ (test_\S+?) _+")

upload_timeout_names = []
other_timeout_names = []

seen_web_shortnames = set(name_to_nodeid.keys())

for b in blocks:
    m = header_re.match(b.strip())
    if not m:
        continue
    name_raw = m.group(1)
    base = re.sub(r"\[.*\]$", "", name_raw)
    if name_raw not in seen_web_shortnames and base not in seen_web_shortnames:
        continue
    if "TimeoutError" not in b:
        continue
    if "object_authoring_page.py:5" in b or "object_authoring_page.py:6" in b:
        upload_timeout_names.append(name_raw)
    else:
        other_timeout_names.append(name_raw)

def resolve(names):
    out = []
    for n in names:
        base = re.sub(r"\[.*\]$", "", n)
        cands = name_to_nodeid.get(n) or name_to_nodeid.get(base) or []
        out.extend(cands)
    return out

upload_nodeids = resolve(upload_timeout_names)
other_nodeids = resolve(other_timeout_names)

all_66 = sorted(set(upload_nodeids + other_nodeids))
with open(r".claude/qa-baselines/66_timeout_nodeids.txt", "w", encoding="utf-8") as out:
    out.write("\n".join(all_66) + "\n")

print("upload timeout nodeids:", len(upload_nodeids))
print("other timeout nodeids:", len(other_nodeids))
print("total unique:", len(all_66))
