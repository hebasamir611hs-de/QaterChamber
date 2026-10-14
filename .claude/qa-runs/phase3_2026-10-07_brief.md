# Phase 3 brief — 2026-10-07 — ECONOMY MODE — one PBI per engineer run

## ⚠ USER ORDER, 2026-10-07 22:45. It overrides anything below that conflicts with it.
1. **Every case in the suite gets executed.** That covers P1–P4 and Manual-tagged cases alike. No case is left
   skipped, blocked, not-scripted or not-executed while there is ANY way to execute it.
   - Script every Automation case, including all of P3/P4. The Rule-4 Run/Skip list is replaced by "run all".
   - Execute Manual cases by hand, live, under the lock: Playwright MCP or a short script, with screenshots
     `reports/manual-exec-<PBI>-<tc>.png`. Record the result the same way you record an automated one.
   - Char-limit cases are still executed per bug-rules Rule 5: test at the implemented max and check the UI.
     A rich-text field gets result N/A, and you write down that you checked it.
   - Figma: try the azure-devops MCP tool `extract_figma_design` (Figma link from `get_story_for_analysis`).
     The Figma MCP connector is down; don't use it.
1b. **USER, 2026-10-08 11:20: P4 is deferred.** Don't script or run P4 cases now. List them as
   `DEFERRED (P4, user 2026-10-08)`. P1–P3 and Manual still all run.
2. **Real shared data is still untouched.** Unblock with TEST DATA instead:
   - QCTEST records;
   - a NEW QCTEST record of the same object instead of editing the live one, if the page picks it up;
   - a QCTEST event or article, etc.
   Look for the test-data path first. Only if NO test-data path exists AND executing needs a real record,
   leave it as `NEEDS USER — real record <ID>`, with the evidence that you looked.
3. **Bugs: confirm, don't file.**
   - Every PRODUCT_BUG candidate gets the live manual repro (Step 5) AND a check against the PBI
     Description/AC: quote the clause.
   - The QA Manager has a Fable reviewer verify each one afterwards.
   - Nobody files anything. The user approves the full confirmed-bug list at the very end.
4. **Deletion:**
   - Tear down your own `QCTEST-` records by exact title, as the policy says.
   - Never delete anything without the `QCTEST-` prefix, even when you created it, for example draft
     `7ac9f8fb-…`. List those in the report.
   - When a test needs a public QCTEST record, unpublish it or untick Active as soon as the assertion is done,
     so visitors on qcdev don't keep seeing it.

You are a senior automation engineer (Playwright + pytest, this repo). The QA Manager gives you
**exactly one PBI** in your prompt. Finish it end to end, write the report file, and return.
Scope is fixed: don't re-judge coverage and don't rewrite case content. Test Plan **133534**.

| PBI | Suite | Feature folder(s) |
|---|---|---|
| 129368 | 134448 | `home_promo_banners` |
| 129372 | 134450 | `home_latest_news` |
| 129381 | 134452 | `home_strategic_direction` |
| 129382 | 134453 | `home_featured_event` |
| 129384 | 134455 | `home_dynamic_widgets` |
| 129389 | 134460 | `home_about_summary` (prior runs: `reports/pbi_129389_*.log`, last = v9_clean) |
| 129390 | 134461 | `home_quick_contact`, `home_contact_us` (CMS tests for this PBI live in both) |
| 129392 | 134463 | `about_qatar_chamber` |

Tests already exist for every PBI, both trees (`web/tests/<f>/`, `cms/tests/<f>/`), most written
**before** the 7-state workflow / role / vocabulary rules (2026-09-28). Treat them as suspect.

## Read first (only what you need)
- `.claude/context/active/standards.md` — binding. Sections: Content Editorial Workflow; Object
  Authoring; Object Names; Active Status; Logged-Out Context; Destructive Operations; Fragments;
  Destructive-Precondition; Named CMS User Roles; Execution Process Conventions; Wait-Strategy.
- `.claude/context/active/bug-rules.md` — binding (Figma tolerance, one bug per root cause,
  Rule 3 confirm-before-bug, Rule 4 run order, Rule 5 char limits).
- `.claude/context/active/OBJECT-AUTHORING-GUIDE.md` — tool mechanics.
- `docs/qa-environment-notes.md` — shared-record table, login gate, locale drift.
- Object names: `cms/Content-Admin-Guide.docx`; where it falls short, the live Object Authoring
  sidebar's exact labels.

## Step 1 — Inventory (offline + Azure read)
`get_test_cases_from_suite(133534, <suite>)`. Build `.claude/qa-runs/phase3_<PBI>_2026-10-07.json`:
per case `tc_id, title, priority, platform, execution (Automation/Manual), test function nodeid or
"MISSING", currently_skipped (y/n + reason), stale_flags`. Stale flags to grep for in the test and
its Page Object: `"Submit for Publishing"`, `"Approved"`, `"(draft)"` lowercase, `TEST_USER` on a
lifecycle/permission case, public-visibility check on the authenticated `page`, missing Active
Status tick on a create→public case, Unpublish polled as "Draft", delete by position/"newest"/
"first match", `Content & Data` navigation, fixed `wait_for_timeout` with no measured comment.

## Step 2 — Fix the scripts to the new flow (offline)
- Correct every stale flag. Use `object_authoring_page.py`'s `STATUS_*`, `SUBMIT_FOR_REVIEW_BUTTON`,
  `normalize_status()`. Name the account in each lifecycle docstring; log in via
  `config.settings.cms_role_credentials("<Role>")` (Editor → Published directly; Author → Pending Review;
  site member → denial, asserted positively). Never `TEST_USER` for lifecycle/permission.
- **No `@pytest.mark.skip` stays.** Every existing skip becomes a real test. If a case truly can't be
  run (no CMS path, needs a real visitor submission, needs mutating a real shared record not
  approved by ID, needs Figma you can't open…), do NOT skip it and do NOT invent a workaround:
  list it under **NEEDS USER** in your report with the exact blocker. The user will tell us how.
- Missing P1/P2 cases: script them. Missing P3/P4 cases: don't script — put them in the Rule-4
  Run/Skip table (customer-visible ⇒ lean Run).
- Destructive preconditions → disposable `QCTEST-<tc_id>-*` records, teardown every run, delete by
  exact title/ID only, after confirming the `QCTEST-` prefix. Real records: snapshot + verified
  restore only where `docs/qa-environment-notes.md`'s shared-record table allows it; otherwise NEEDS USER.
- **129381 only:** a real record (49108) was destroyed by a positional delete on this PBI's batch
  (`docs/qa-decisions-log.md` 2026-09-03). Before ANY live step, prove from the code that every
  delete path in this feature resolves by ID/exact title + QCTEST guard; quote it in the report.
- Shared record mutation needs `@pytest.mark.xdist_group(...)`. Don't edit `core/`,
  `object_authoring_page.py`, or by hand `pytest.ini` — if you need them, NEEDS USER.
- `pytest --collect-only <files>` must pass (offline).

## Step 3 — Run (live, under the lock)
Order (Rule 4): all P1/P2 first, then the already-scripted P3/P4.
```
pytest <nodeids or -m "pbi_<PBI>"> --alluredir=reports/allure-results-phase3-<PBI>-20261007-<HHMM> --no-clean-evidence
```
Default `-n 3 --dist loadgroup`; use `-n 0` if the module mutates a shared record without a group.
Never the default `reports/allure-results`.

## Step 4 — Triage, one heal, one targeted rerun
Classify every failure: PRODUCT_BUG / AUTOMATION_BUG / ENVIRONMENT_ERROR / NEEDS_INVESTIGATION,
with quoted evidence. For AUTOMATION_BUG: fix **once**, rerun **only those nodeids once** (new
alluredir suffix `-rerun`). Then stop healing. Still failing ⇒ report it, don't loop.

## Step 5 — Confirm every PRODUCT_BUG manually (bug-rules Rule 3) — mandatory
For each PRODUCT_BUG candidate, outside pytest: re-read the PBI (`get_story_for_analysis`) AC +
the TC expected result; reproduce it **by hand live** (Playwright MCP or a short standalone script,
under the lock), with the right account, both visibility gates checked, logged-out context for public
checks; screenshot to `reports/manual-repro-<PBI>-<tc>.png`; check persisted data for data-changing
cases. Outcome per candidate: **CONFIRMED** (repro'd, contradicts PBI/TC) / **NOT REPRODUCED** (→
it's ours, fix or report) / **INCONCLUSIVE** (→ NEEDS USER). Apply Rule 2: group by root cause.
Char-limit, missing toast, different wording, file ≤3 MB accepted → not bugs (Rule 5 / memory).
**You never file bugs or write test results to Azure.** Azure is read-only for you.

## Live-browser lock (two engineers in parallel offline, ONE browser on qcdev at a time)
Every live step — pytest run, manual repro, `tools/save_auth.py`, `tools/extract_locators.py`,
`tools/sync_tc_markers.py` — holds this session's lock. Never touch other `*.lock` dirs.
```bash
python -c "import os,time,sys
p='.claude/qa-runs/qcdev-browser-c7.lock'
for _ in range(1080):
    try: os.mkdir(p); open(p+'/owner','w').write(sys.argv[1]); sys.exit(0)
    except FileExistsError: time.sleep(10)
sys.exit('lock timeout')" <PBI>
```
Release with `rm -rf .claude/qa-runs/qcdev-browser-c7.lock` the moment the live step ends (use a
`trap`/finally). Batch live work to take the lock as few times as possible.
A 404 on an authoring URL = signed out → `python tools/save_auth.py`, then retry once.

## Stop immediately and report (no retry loops)
"This instance is expired"; a role login fails; an object missing from the sidebar; any delete whose
target isn't positively a QCTEST record; a needed write to a real shared record not approved by ID;
a page section missing (finding — never touch fragments/layout).

## Report — write `.claude/qa-runs/phase3_<PBI>_2026-10-07_report.md`, return its path + ≤15-line summary
1. Totals: cases in suite / scripted / run / passed / failed / NEEDS USER / not scripted (P3/P4).
2. Files changed + the stale flags fixed (one line each kind).
3. Results table: tc_id | title | P | result | verdict | note.
4. Findings: CONFIRMED (with screenshot path, PBI/TC clause contradicted, root-cause group, affected
   TCs) / NOT REPRODUCED / INCONCLUSIVE.
5. NEEDS USER list (tc_id, exact blocker, what you'd need).
6. Rule-4 P3/P4 Run/Skip table for unscripted cases.
7. QCTEST records created/deleted (titles); any real record touched + verified restore values.
8. Allure dirs used.
