import re

with open(r".claude/qa-baselines/114_rerun_output.txt", encoding="utf-8", errors="replace") as f:
    content = f.read()

with open(r".claude/qa-baselines/114_failed_nodeids.txt", encoding="utf-8") as f:
    web_failed = set()
    for line in f:
        line = line.strip()
        if line.startswith("web/"):
            name = line.split("::")[-1]
            web_failed.add(name)

blocks = re.split(r"(?=^_{5,} test_)", content, flags=re.MULTILINE)
upload_timeout = []
other_timeout = []
real_mismatch = []

header_re = re.compile(r"^_+ (test_\S+?) _+")

for b in blocks:
    m = header_re.match(b.strip())
    if not m:
        continue
    name_raw = m.group(1)
    name = re.sub(r"\[.*\]$", "", name_raw)
    if name_raw not in web_failed and name not in web_failed:
        continue
    if "TimeoutError" in b:
        if "object_authoring_page.py:5" in b or "object_authoring_page.py:6" in b:
            upload_timeout.append(name_raw)
        else:
            other_timeout.append(name_raw)
    else:
        real_mismatch.append(name_raw)

print("upload-picker timeout (web/ scope):", len(upload_timeout))
print()
print("other timeout (web/ scope):", len(other_timeout))
for n in other_timeout:
    print("  -", n)
print()
print("real mismatch / non-timeout (web/ scope):", len(real_mismatch))
for n in real_mismatch:
    print("  -", n)
print()
print("TOTAL categorized:", len(upload_timeout) + len(other_timeout) + len(real_mismatch))
print("TOTAL expected (web/ failed):", len(web_failed))
