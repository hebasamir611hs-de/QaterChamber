# Phase 3 engineer brief — CMS (Control_Panel), 2026-09-30

PBIs 129363 (Site Header), 129364 (Accessibility Tools), 129365 (Language Switcher).
Scope fixed by the QA Manager: Control_Panel cases, priority 1–3, `Automation`-tagged
only. Your batch file lists every case with a `disposition` — follow it exactly; do not
re-judge coverage or rewrite case content.

## Read first (only the sections you need — economy mode)
- `.claude/context/active/standards.md` — binding. Especially: Content Editorial
  Workflow; Object Authoring; Active Status; Logged-Out Context; Destructive Operations;
  Named CMS User Roles; Wait-Strategy.
- `.claude/context/active/OBJECT-AUTHORING-GUIDE.md` — tool mechanics.
- `cms/Content-Admin-Guide.docx` §3: Header = `HeaderConfiguration` (ONE entry:
  logoImage, logoAltTextEn/Ar, logoRedirectUrl, workflowStatus) + `NavItem` (labels EN/AR,
  relative URL, Parent Item relationship, displayOrder per group in multiples of 100,
  activeStatus; depth derived from parent — no Level field). Accessibility =
  `AccessibilityHeaderConfiguration` (ONE entry: `accessibilityToolsEnabled` checkbox).
  Slugs: `manage-header-configuration`, `manage-nav-item`,
  `manage-accessibility-header-configuration` (mechanical lower-kebab of the guide name;
  a 404 means signed out → `python tools/save_auth.py`, not a bad slug).
- The live HeaderConfiguration entry is titled `QCDEMO-129363-HEADER-CONFIG-DEFAULT` and
  **is the real live header** (user-confirmed). Treat it as untouchable.
- `cms/pages/components/object_authoring_page.py` — reuse it. Use `STATUS_*`,
  `SUBMIT_FOR_REVIEW_BUTTON`, `normalize_status()`. **Do not edit this shared file**; if
  you need a change in it, stop and report what and why.

## Dispositions
- `automate` → a real, runnable test.
- `conditional` → automate only if the stated non-mutating condition holds after you
  inspect the live form; otherwise treat as `skip` with the given reason.
- `skip` → still write the test function (markers, docstring with the case title and
  steps summary), decorated `@pytest.mark.skip(reason="<disposition_reason verbatim>")`.
  Body may be a minimal outline; no live calls.

## Hard rules
1. **Never click Save / Save as Draft / Submit for Review / Publish / Unpublish / Delete
   on the live `HeaderConfiguration` or `AccessibilityHeaderConfiguration` entry.** Not
   even to "restore". Non-mutating checks on them (open, inspect, change a field and
   leave without saving) are allowed.
2. **NavItem cases run on disposable records only**: title/labels `QCTEST-<tc_id>-<short>`,
   `displayOrder` a high multiple of 100 (e.g. 9900) so it sorts last, relative URL like
   `/web/qatar-chamber/qctest-<tc_id>`. Teardown every run in a `finally`/fixture, delete
   **by exact title or entry code only** — never by position. Real NavItems are never
   edited, reordered or deleted. A published + active QCTEST item appears briefly in the
   real public menu — keep that window as short as the case allows; prefer Draft /
   inactive when the case does not assert public rendering.
3. **Name the account in every lifecycle case's docstring** and log in via
   `config.settings.cms_role_credentials("<Role>")` + `CmsLoginPage.login()`:
   Editor for create/publish (Published directly), Author when the case is about
   submit → Pending Review. **Never `TEST_USER`** for lifecycle or permission cases.
   Access-denial cases (134255, 134501, 134658): prefer the site-member account
   (`cms_role_credentials` key for the no-role member) to prove denial, and assert the
   refusal positively (e.g. denial message / absent control), so a broken login cannot
   pass it. Choose a content role instead only if the case wording demands it, and say why.
4. **Public visibility** → `new_context(browser, use_auth_state=False)`; assert both gates
   (Published AND Active Status ticked). Active Status defaults UNTICKED on new entries.
5. Locate workflow row actions by `data-qc-oel-<action>="<entryId>"`; accept chained
   `confirm()`/`prompt()` dialogs.
6. Condition-based waits only. English-text locators only, no Arabic fallbacks.
7. Markers per test: `control_panel`, `global_` (service), the category marker used by
   sibling tests, `regression` only if the Azure case carries `Regression`,
   `pbi_<PBI>`, `tc_<azure id>`. **Do NOT run `tools/sync_tc_markers.py` and do NOT edit
   `pytest.ini`** — the QA Manager runs it once after both engineers finish.
8. Any test touching a shared record gets `@pytest.mark.xdist_group(...)`; group all
   NavItem-creating tests in one group `header_navitem_qctest` (they share the menu).
9. Never touch fragments, page layout, Page Editor, Documents & Media deletion.
10. **Your job stops at scripted** (engine-guide Phase 3 step 12). Do not run the pytest
    suite. You MAY run `pytest --collect-only <your file>` (offline) to prove it collects.

## Live-browser lock (two engineers, one browser at a time)
Any live qcdev action (`tools/extract_locators.py`, `tools/save_auth.py`, any Playwright
script) must hold the lock. Acquire:

```bash
python -c "import os,time,sys
p='.claude/qa-runs/qcdev-browser.lock'
for _ in range(360):
    try: os.mkdir(p); open(p+'/owner','w').write(sys.argv[1]); sys.exit(0)
    except FileExistsError: time.sleep(10)
sys.exit('lock timeout')" <your-name>
```

Release with `rm -rf .claude/qa-runs/qcdev-browser.lock` as soon as that live step
finishes. Hold it only for the live step, never while writing code. Batch your locator
needs so you acquire it as few times as possible (economy: extract once per page).

## Report back (short — under 25 lines)
Files changed; per tc_id: automated / skipped (reason code) / conditional → which way
and why; any locator you could not resolve; anything in the case that contradicts the
guide or live UI (report, don't fix); confirmation no singleton was saved and every
QCTEST record you created during extraction was deleted (list titles).
