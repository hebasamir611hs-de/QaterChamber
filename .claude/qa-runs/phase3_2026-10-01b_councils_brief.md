# Phase 3 brief — CMS (Control_Panel), batch 2026-10-01b — ECONOMY MODE

Scope is fixed by the QA Manager. Don't re-judge coverage and don't rewrite case content.
**Control_Panel cases with Azure Priority 1, 2 or 3 that are tagged `Automation`.** Count
Manual-tagged and P4 cases and list them in your report, but don't script them.
Test Plan **137724**.

| PBI | Suite | Feature | Agent |
|---|---|---|---|
| 130716 | 140375 | Sectoral Committees & Business Councils (`sectoral_committees`) | A |
| 130717 | 140376 | Request to Join a Committee (`join_committee`) | A |
| 130718 | 140377 | QAFL Membership Registration (no web folder yet: `qafl_membership`) | A |
| 130719 | 140378 | Business Council Membership Request (`business_council_membership`) | A |
| 130720 | 140379 | Partners & Offers (`partners_offers`) | B |
| 130947 | 140380 | Certificate of Origin Online (`certificate_of_origin`) | B |
| 130949 | 140381 | Proposal for Research (`proposal_for_research`) | B |

None of these PBIs has CMS scripts yet. Write them from scratch:
`cms/pages/<f>/<f>_admin_page.py` and `cms/tests/<f>/test_<f>_control_panel.py`.
Don't modify the web tests.

## Binding rules
Everything in `.claude/qa-runs/phase3_2026-10-01_engineer_brief.md` applies: Steps 1–4,
the new 7-state flow, role logins, both visibility gates, logged-out context, disposable
`QCTEST-<tc_id>-*` records with teardown, markers, offline gate, triage-then-STOP, the
report format, and the **Object-name source** paragraph. That paragraph means the live
Object Authoring sidebar is the authority where the guide falls short, using its exact
labels. Also apply `standards.md` § "Webform / Approval-Workflow Rules". These are mostly
webform → Submissions → Approve/Reject features. Use the **Form Manager** role for
Submissions view/update. A rejected record must stay stored. Never approve or reject a
real visitor submission: act only on a submission you created yourself as `QCTEST-<tc_id>`.
If a case needs a real submission that you can't create, the case is BLOCKED and you
STOP and ask.

## Parallel offline, serial live
A and B write code at the same time, but **only one of you drives a qcdev browser at any
moment**. Every live step must hold this session's lock: extract_locators, save_auth, any
Playwright script, and every pytest run. The lock directory is
`.claude/qa-runs/qcdev-browser-b2.lock`. The old `qcdev-browser.lock` belongs to another
session: don't touch it.

```bash
python -c "import os,time,sys
p='.claude/qa-runs/qcdev-browser-b2.lock'
for _ in range(720):
    try: os.mkdir(p); open(p+'/owner','w').write(sys.argv[1]); sys.exit(0)
    except FileExistsError: time.sleep(10)
sys.exit('lock timeout')" <A|B>
```

Release it with `rm -rf .claude/qa-runs/qcdev-browser-b2.lock` as soon as the live step
ends. Batch your locator extraction so you take the lock as few times as possible.
`tools/sync_tc_markers.py` rewrites `pytest.ini`, so hold the lock while you run it too.

## Allure — this session's own report
Pass these flags on every pytest run:
`--alluredir=reports/allure-results-phase3-b2-<A|B>-20261001 --no-clean-evidence`.
Never use the default `reports/allure-results`, because other sessions share it. Put your
run's report path in your report.

## Stop conditions
- The instance shows "This instance is expired" (Liferay license).
- A login fails.
- An object is missing from the sidebar.
- You'd need to act on a real submission.

In any of these cases, STOP and report. Don't retry or loop.

## Character-limit rules (team decision, relayed by the user 2026-10-01): binding
1. **Rich-text fields:** every char-limit case on a rich-text field gets the disposition
   `skip` with the reason `"N/A: no character limit is applied to rich-text fields (team decision 2026-10-01)"`.
   Record it as `NA` in the report. It will be set to Not Applicable later, not Failed.
2. **Plain fields where the implemented max is GREATER than the US limit:** don't fail on
   the length itself. Read the implemented max from the field (`maxlength` attribute or
   validation), fill it to that implemented max, save, and check the admin form and list
   UI, plus the public render where the case covers it. If the layout is broken (overflow,
   truncation that hides content, wrapping that breaks the layout), that is a
   `PRODUCT_BUG` with owner **FE (UI fix)**. If FE can't fix it, the fallback owner is
   **Alaa**, to apply the original US limit. If the UI is fine, the case passes. Note both
   numbers: US = X, implemented = Y.
3. **Plain fields where the implemented max is SHORTER than the US limit:** that's a
   `PRODUCT_BUG` with owner **Alaa**. State the US limit and the implemented limit.
Bugs are still NOT filed by you. Put the verdict and owner in the triage table only.
