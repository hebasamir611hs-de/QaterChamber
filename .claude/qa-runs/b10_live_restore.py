"""B10 live-record snapshot / restore harness (2026-10-04). Scratch tool, not a test.

python .claude/qa-runs/b10_live_restore.py discover
python .claude/qa-runs/b10_live_restore.py snap    <pbi> <tc> <plural>:<id> [...]
python .claude/qa-runs/b10_live_restore.py restore <pbi> <tc> <plural>:<id> [...]
python .claude/qa-runs/b10_live_restore.py patch   <plural>:<id> <json-file>   (one-off edit as Editor)

Every call signs in as the Site Content Editor (cms_role_credentials) and talks to
/o/c/ from the Object Authoring page context, the same calls the manage page makes.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from config.settings import cms_role_credentials, control_panel_url  # noqa: E402
from cms.pages.control_panel.login_page import CmsLoginPage  # noqa: E402

API_JS = """async ([m, u, b]) => {
  const t = (window.Liferay && Liferay.authToken) || '';
  const r = await fetch(u, {method: m, credentials: 'same-origin',
    headers: {'accept': 'application/json', 'content-type': 'application/json', 'x-csrf-token': t}, body: b});
  let txt = ''; try { txt = await r.text(); } catch (e) {}
  return [r.status, txt];
}"""

SYSTEM = {"actions", "creator", "dateCreated", "dateModified", "externalReferenceCode", "id", "keywords",
          "taxonomyCategoryBriefs", "taxonomyCategoryIds", "scopeKey", "status", "auditEvents",
          "friendlyUrlPath", "friendlyUrlPath_i18n", "systemProperties"}
COMPARE_SKIP = {"actions", "dateModified", "creator", "auditEvents"}

PUBLIC = {
    "coo": "/our-services/certificate-of-origin-online",
}


def out_dir(pbi):
    d = ROOT / "reports" / "live-restore" / str(pbi)
    d.mkdir(parents=True, exist_ok=True)
    return d


class S:
    def __init__(self, pw):
        self.browser = pw.chromium.launch()
        self.ctx = self.browser.new_context(viewport={"width": 1440, "height": 900}, ignore_https_errors=True)
        self.page = self.ctx.new_page()
        email, pwd = cms_role_credentials("Site Content Editor")
        CmsLoginPage(self.page).open_login().login(email, pwd)
        self.home()

    def home(self):
        self.page.goto(control_panel_url("/en/web/qatar-chamber/manage-coo-page-content"), wait_until="domcontentloaded")
        self.page.wait_for_function("() => !!(window.Liferay && Liferay.authToken)", timeout=60000)

    def api(self, m, path, body=None):
        url = control_panel_url(path)
        for _ in (0, 1):
            try:
                return self.page.evaluate(API_JS, [m, url, body])
            except Exception:  # noqa: BLE001
                self.home()
        return self.page.evaluate(API_JS, [m, url, body])

    def get(self, plural, eid):
        st, txt = self.api("GET", f"/o/c/{plural}/{eid}?nestedFields=")
        assert st == 200, f"GET {plural}/{eid} -> {st} {txt[:200]}"
        return json.loads(txt)

    def close(self):
        self.browser.close()


def comparable(d):
    out = {}
    for k, v in d.items():
        if k in COMPARE_SKIP:
            continue
        if k == "status":
            out[k] = (v or {}).get("label")
        elif isinstance(v, dict) and {"id", "link"} & set(v):
            out[k] = {"file_id": v.get("id")}
        else:
            out[k] = v
    return out


def norm(v):
    if isinstance(v, str):
        return " ".join(v.split())
    if isinstance(v, dict):
        return {k: norm(x) for k, x in v.items()}
    if isinstance(v, list):
        return [norm(x) for x in v]
    return v


def diff(a, b):
    a, b = comparable(a), comparable(b)
    d = {}
    for k in sorted(set(a) | set(b)):
        if a.get(k) != b.get(k):
            kind = "whitespace-only" if norm(a.get(k)) == norm(b.get(k)) else "REAL"
            d[k] = {"before": a.get(k), "after": b.get(k), "kind": kind}
    return d


def patch_body(before):
    body = {}
    for k, v in before.items():
        if k in SYSTEM or k.startswith("r_") or k.endswith("ERC"):
            continue
        if isinstance(v, dict) and "link" in v and "id" in v:
            body[k] = v["id"]
        else:
            body[k] = v
    return body


def shots(pw_unused, s, pbi, tc, tag, public_path):
    if not public_path:
        return []
    from config.settings import web_url
    paths = []
    ctx = s.browser.new_context(viewport={"width": 1440, "height": 900}, ignore_https_errors=True)
    try:
        p = ctx.new_page()
        for loc in ("en", "ar"):
            p.goto(web_url(public_path, locale=loc), wait_until="domcontentloaded")
            try:
                p.wait_for_load_state("networkidle", timeout=20000)
            except Exception:  # noqa: BLE001
                pass
            f = out_dir(pbi) / f"tc_{tc}_{tag}_{loc}.png"
            p.screenshot(path=str(f), full_page=True)
            txt = " ".join(p.locator("body").inner_text().split())
            (out_dir(pbi) / f"tc_{tc}_{tag}_{loc}.txt").write_text(txt, encoding="utf-8")
            paths.append(str(f))
    finally:
        ctx.close()
    return paths


def main():
    cmd = sys.argv[1]
    with sync_playwright() as pw:
        s = S(pw)
        try:
            if cmd == "discover":
                for plural in sys.argv[2:]:
                    st, txt = s.api("GET", f"/o/c/{plural}/scopes/37246?pageSize=50")
                    print("==", plural, st)
                    if st != 200:
                        print(txt[:300]); continue
                    for it in json.loads(txt).get("items", []):
                        brief = {k: v for k, v in it.items() if isinstance(v, (str, int, bool)) and k not in
                                 ("dateCreated", "dateModified", "externalReferenceCode", "scopeKey")}
                        brief["status"] = (it.get("status") or {}).get("label")
                        print(json.dumps(brief, ensure_ascii=False)[:400])
            elif cmd in ("snap", "restore"):
                pbi, tc, public_path = sys.argv[2], sys.argv[3], sys.argv[4] if sys.argv[4] != "-" else ""
                recs = [a.split(":") for a in sys.argv[5:]]
                if cmd == "snap":
                    for plural, eid in recs:
                        d = s.get(plural, eid)
                        (out_dir(pbi) / f"tc_{tc}_{eid}_before.json").write_text(
                            json.dumps({"plural": plural, "record": d}, ensure_ascii=False, indent=1), encoding="utf-8")
                        print("snap", plural, eid, "status", d.get("status", {}).get("label"),
                              "active", d.get("activeStatus"))
                    print("shots", shots(pw, s, pbi, tc, "before", public_path))
                else:
                    report = {"tc": tc, "records": {}}
                    clean = True
                    for plural, eid in recs:
                        before = json.loads((out_dir(pbi) / f"tc_{tc}_{eid}_before.json").read_text(encoding="utf-8"))["record"]
                        now = s.get(plural, eid)
                        d0 = diff(before, now)
                        real0 = {k: v for k, v in d0.items() if v["kind"] == "REAL"}
                        patched = None
                        if real0:
                            st, txt = s.api("PATCH", f"/o/c/{plural}/{eid}", json.dumps(patch_body(before), ensure_ascii=False))
                            patched = [st, txt[:300]]
                            now = s.get(plural, eid)
                        d1 = diff(before, now)
                        real1 = {k: v for k, v in d1.items() if v["kind"] == "REAL"}
                        clean &= not real1
                        report["records"][f"{plural}:{eid}"] = {"diff_before_restore": d0, "patch": patched,
                                                                "diff_after_restore": d1, "clean": not real1}
                        print(plural, eid, "pre-diff", list(real0), "patched", patched and patched[0],
                              "post-diff", list(real1) or "CLEAN")
                    report["shots_after"] = shots(pw, s, pbi, tc, "after", public_path)
                    for loc in ("en", "ar"):
                        a = out_dir(pbi) / f"tc_{tc}_before_{loc}.txt"
                        b = out_dir(pbi) / f"tc_{tc}_after_{loc}.txt"
                        if a.exists() and b.exists():
                            same = a.read_text(encoding="utf-8") == b.read_text(encoding="utf-8")
                            report[f"public_text_same_{loc}"] = same
                            print("public text", loc, "same" if same else "DIFFERS")
                    report["clean"] = clean
                    (out_dir(pbi) / f"tc_{tc}_restore.json").write_text(
                        json.dumps(report, ensure_ascii=False, indent=1), encoding="utf-8")
                    print("RESTORE", "CLEAN" if clean else "NOT CLEAN")
            elif cmd == "raw":
                st, txt = s.api(sys.argv[2], sys.argv[3], sys.argv[4] if len(sys.argv) > 4 else None)
                import os
                f = os.environ.get("B10_OUT")
                if f:
                    open(f, "w", encoding="utf-8").write(txt)
                print(st, txt[:4000] if not f else f)
        finally:
            s.close()


if __name__ == "__main__":
    main()
