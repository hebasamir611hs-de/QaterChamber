import re
from collections import Counter

with open(r".claude/qa-baselines/114_rerun_output.txt", encoding="utf-8", errors="replace") as f:
    content = f.read()

blocks = re.split(r"(?=^_{5,} test_)", content, flags=re.MULTILINE)
locs = Counter()
pattern = re.compile(r"^((?:cms|web)\\(?:pages|tests)\\[^\n]+): in ", re.MULTILINE)

for b in blocks:
    if "TimeoutError" not in b:
        continue
    our_frames = pattern.findall(b)
    if our_frames:
        locs[our_frames[-1]] += 1
    else:
        locs["NO-OWN-FRAME-FOUND"] += 1

for loc, cnt in locs.most_common(25):
    print(cnt, loc)
