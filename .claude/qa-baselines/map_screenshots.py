import json
import glob
import os

results_dir = "reports/allure-results-rerun114"
wanted_tc_ids = [
    143571, 143573, 143574, 143576,  # Annual Reports Figma tokens group
    143580, 143605, 143831,          # Annual Reports wording group
    143586,                          # Annual Reports tap target
    143842, 143959, 143967, 143845, 143846,  # Export Reports copy group
    143852,                          # Export Reports tablet overflow
    144250, 144259, 144260,          # Made in China Expo redirect group
    144092, 143983,                  # Breadcrumb group (2 PBIs)
    143981,                          # Publications missing filter
]

mapping = {}
for path in glob.glob(os.path.join(results_dir, "*-result.json")):
    with open(path, encoding="utf-8", errors="replace") as f:
        try:
            data = json.load(f)
        except Exception:
            continue
    name = data.get("name", "")
    full_name = data.get("fullName", "")
    labels = {l["name"]: l["value"] for l in data.get("labels", [])}
    tc_label = None
    for l in data.get("labels", []):
        if l["name"] == "tag" and l["value"].startswith("tc_"):
            tc_label = l["value"]
    # find tc_id also from parameters or testCaseId label
    attachments = data.get("attachments", [])
    png = None
    for a in attachments:
        if a.get("type") == "image/png":
            png = a.get("source")
            break
    mapping[full_name or name] = {"status": data.get("status"), "png": png, "tags": [l["value"] for l in data.get("labels", []) if l["name"]=="tag"]}

# match by tc_ tag
out = {}
for full_name, info in mapping.items():
    for tag in info["tags"]:
        if tag.startswith("tc_"):
            tcid = int(tag.replace("tc_", ""))
            if tcid in wanted_tc_ids:
                out[tcid] = {"full_name": full_name, "png": info["png"], "status": info["status"]}

with open(".claude/qa-baselines/screenshot_map.json", "w", encoding="utf-8") as f:
    json.dump(out, f, ensure_ascii=False, indent=2)

print("mapped:", len(out), "of", len(wanted_tc_ids))
missing = set(wanted_tc_ids) - set(out.keys())
print("missing:", missing)
