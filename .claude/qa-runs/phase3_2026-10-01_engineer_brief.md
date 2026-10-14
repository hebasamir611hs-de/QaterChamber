# Phase 3 engineer brief — CMS (Control_Panel), 2026-10-01 — ECONOMY MODE

QA Manager scope (fixed — do not re-judge coverage, do not rewrite case content):
**Control_Panel cases, Azure Priority 1, 2 or 3, `Automation`-tagged**, for your PBIs only.
Test Plan **137724** (Sprint 2 — NOT 133534). Suites: 130708→140367, 130713→140372, 130714→140373, 130715→140374, 131061→140395, 131062→140396, 130712→140371, 130711→140370, 130710→140369, 131313→140399, 130953→140384. Cases tagged Manual, or Priority 4, are out of scope: count them and
list them in your report, but don't script them.

Two engineers work **sequentially**, never at the same time. You are the only agent
driving a qcdev browser while you run. Don't spawn sub-agents.

**Object-name source, user-authorized 2026-10-01:** the Content-Admin-Guide.docx is
behind. Every object exists on the live Object Authoring sidebar (Objects Home →
`/web/qatar-chamber/manage-<slug>`), built by Engy and already on the new 7-state flow.
If the guide is missing an object or field, take its name and slug from that sidebar list
and from the form's actual fields. That is the authoritative source for this batch,
e.g. `Made in Qatar Expo Hero` → `manage-made-in-qatar-expo-hero`, and `Podcast Episode` /
`Podcast Platform Link` / `Podcast Show Configuration` / `Podcast Subscriber`,
`Photo Album`, `Photo Gallery Page Hero`. Copy the exact sidebar label. Never invent a slug.
Pre-existing `QCDEMO-*` entries are real shared content: open and read them only.

## Read first (only the sections you need)
- `.claude/context/active/standards.md` — binding. Sections: Content Editorial Workflow
  (7 states, account decides path); Object Authoring; Active Status; Logged-Out Context;
  Destructive-Precondition / Disposable Test Data; Named CMS User Roles; Wait-Strategy;
  Execution Process Conventions; Safe Parallelism.
- `CLAUDE.md` CMS non-negotiables 1–9 (enforced by `cms/tests/test_cms_conventions.py`).
- `.claude/context/active/OBJECT-AUTHORING-GUIDE.md` — tool mechanics.
- `cms/Content-Admin-Guide.docx` — the ONLY source of object names and slugs. Never guess a
  slug, and never copy one from a sibling. A 404 means you're signed out: run
  `python tools/save_auth.py`.
- `cms/pages/components/object_authoring_page.py` — reuse it (`STATUS_*`,
  `SUBMIT_FOR_REVIEW_BUTTON`, `normalize_status()`, `data-qc-oel-<action>` row actions).
  **Do not edit this shared file**; if you need a change, stop and report it.
- Precedent to mirror: `.claude/qa-runs/phase3_2026-09-30_engineer_brief.md` and the
  migrated modules `cms/tests/{components,gm_message,home_featured_event}/`.

## Step 1 — Batch file (route-automation scope)
Pull your PBIs' cases from Azure (azure-devops MCP: suite IDs above →
`get_test_cases_from_suite`). Write `.claude/qa-runs/phase3_<PBI>_cp_batch.json` in the
same shape as `phase3_129363_cp_batch.json`: tc_id, priority, tags, title, steps, and a
`disposition` of `automate`, `conditional` or `skip`, plus `disposition_reason`. Mark a case `skip` only if one of
these applies: the CMS provides no path to build the state, it needs a real shared
record mutated, or it is layout/fragment work. Quote the exact reason.

## Step 2 — Script (automate-test-case contract)
- The new flow everywhere: 7 states, `STATUS_*` constants, "Submit for Review",
  `PUBLISHED` badge. Never write the `"Approved"` / `"Submit for Publishing"` literals.
- **Name the account in every lifecycle docstring.** Log in via
  `config.settings.cms_role_credentials("<Role>")` + `CmsLoginPage.login()`. Use Editor for
  create→Published and Author for submit→Pending Review. Permission denial uses the
  site-member account, and the refusal must be asserted positively. **Never `TEST_USER`**
  for lifecycle or permission cases.
- Public visibility: `new_context(browser, use_auth_state=False)`. Assert both gates
  (Published AND Active Status ticked). Active Status defaults to UNTICKED.
- Prefer the History trail (`ul.qc-oel__history-list`) over a badge read alone.
  Accept chained `confirm()` and `prompt()` dialogs.
- Mutations happen on disposable `QCTEST-<tc_id>-<short>` records only, with teardown every
  run in a `finally` block or fixture. Delete by exact title or entry ID, never by position.
  Real shared records are never saved or deleted. Shared-record tests get an
  `@pytest.mark.xdist_group(...)`.
- `skip` dispositions still get a test function (markers, a docstring with the title and
  a steps summary) decorated `@pytest.mark.skip(reason="<reason verbatim>")`.
- Markers: `control_panel`, the service marker siblings use, the category marker,
  `regression` only if the case carries `Regression`, `pbi_<PBI>`, `tc_<id>`. Then run
  `python tools/sync_tc_markers.py` (never hand-edit pytest.ini).
- Condition-based waits only. English locators only, no Arabic fallback. Extract
  locators once per page (`tools/extract_locators.py`), batched.
- Never touch fragments, page layout, Page Editor, or Documents & Media deletion.
- Offline gate before any live run: `pytest --collect-only <files>` and
  `pytest cms/tests/test_cms_conventions.py -p no:xdist` must both be green.

## Step 3 — Run (run-automation contract)
Run only your in-scope P1–3 tests: `pytest -m "control_panel and (pbi_A or pbi_B ...)"`
with the default `-n 3 --dist loadgroup` (use `-n 0` for any module with an unresolved
shared-row race). Run once, with Allure results archived per run-automation.
**No fix→rerun loops.**

## Step 4 — Triage (triage-failures contract), then STOP
Classify every failure as PRODUCT_BUG, AUTOMATION_BUG, ENVIRONMENT_ERROR or
NEEDS_INVESTIGATION, with quoted evidence. Before you call anything PRODUCT_BUG, check
both visibility gates and the account used. **File no bugs. Write no Azure results.
Don't heal.** Healing is a separate, user-gated, one-shot step.

## Report back (under 30 lines)
Per PBI: in-scope count, then automated / skipped (reason) / conditional, then
passed / failed / skipped. Then the failures table: tc_id | verdict | one-line evidence.
Then: files changed, Allure report path, every QCTEST record created and confirmation it
was deleted, any singleton touched (it must be none), and open questions. If you are
blocked on something you can't find, STOP and report it. Don't loop.
