# Phase 3 engineer brief v2 — 2026-10-01 (supersedes v1's skip rules only)

Everything in `.claude/qa-runs/phase3_2026-09-30_engineer_brief.md` still applies
(reading list, roles, markers, lock protocol, report format) **except** where this file
overrides it. The user has ordered: **no test stays `@pytest.mark.skip`** — every
`skip` / `conditional` case from the v1 batch files becomes a real, live test.

## User approval recorded 2026-10-01 (ID-named, standards "Destructive-Precondition" rule 5)

Approved, **for these two records only**, edits with snapshot-and-restore:
- HeaderConfiguration entry `QCDEMO-129363-HEADER-CONFIG-DEFAULT` (logo, alt text EN/AR,
  logo redirect URL, save as draft, submit for review, update, **unpublish**).
- AccessibilityHeaderConfiguration entry id **45370**
  (code `8f47e8e3-fcc8-a55f-845a-87b59c92c88f`) — `accessibilityToolsEnabled` on/off.

Mandatory mechanics for every test that writes to either record:
1. **Snapshot** every field the test will touch, the workflow status, and Active Status
   BEFORE the first write (read from the reopened edit form, not from memory).
2. **Restore in a fixture finalizer** that runs even when the test fails: write the
   snapshot back as **Site Content Editor** and bring it back to `Published` + its
   original Active Status. Then **re-read and verify** the restored values.
3. If the restore cannot be verified → `pytest.exit("RESTORE FAILED on <record>: <diff>")`
   so the whole run stops immediately. Never continue past an unrestored record.
4. Keep the window short: for 134305 (unpublish) re-publish immediately after the
   public-hidden assertion.
5. Group every test touching a record in one `xdist_group` per record
   (`header_config_singleton`, `accessibility_header_config_singleton`).
6. Anything **not** on this list (any other record, Documents & Media deletion, site
   search config, re-index, fragments, page layout) is **not approved** — see below.

Remove the read-only guards you added (`ReadOnlyViolation` / `_refuse`) only as far as
these approved tests need; keep the restore discipline in their place.

## Per-PBI instructions

**129363 Site Header (eng-header)**
- Former SKIP-SINGLETON + conditional cases (134254, 134266, 134267, 134268, 134270,
  134272, 134273, 134277, 134281, 134282, 134304, 134305): implement for real under the
  approval above.
- Logo upload (134270, 134272): use a small disposable image named `QCTEST-<tc_id>-logo.png`
  from `tools/fixture_factory.py` output (or generate one there — never hand-add binaries).
  Restore the original logo reference afterwards. **Do not delete the uploaded file from
  Documents & Media** (not approved; the Site Header PBI note says linked images must not
  be deletable). List every uploaded file name in your report.
- 134297 / 134299: your 2026-09-30 report says the live NavItem form DOES have
  "Nav Item Level" (1/2/3) and "Parent Menu". Implement them for real against the live
  form on disposable QCTEST NavItems; the old spec-gap reason no longer holds.
- **Heal 134303 / 134308** (one shot): triage says `submit()` on the `?editEntry=` path of
  a PUBLISHED QCTEST row never posts — either the edit form posts to a different action
  than `FORM_ACTION_FRAGMENT`, or a published entry must go "Unpublish to edit as draft"
  first. Fix the mechanism; QCTEST rows only.
- 134300 is not skipped in code — leave as is.

**129364 Accessibility + 129365 Language Switcher (eng-a11y)**
- SKIP-SINGLETON cases (134511, 134512, 134513, 134640, 134641, 134643, 134644): real,
  under the approval above, on entry 45370. Public checks in an anonymous context.
- Alt-text cases (134492, 134515–134523, 134642, 134645–134652): the PBI's rule is
  site-wide ("an image cannot be published without EN + AR alt text"). Implement them on a
  **disposable QCTEST record** of an object that the Content Admin Guide lists with an
  image field plus a bilingual alt-text field (name the object and guide § in the
  docstring). Never on HeaderConfiguration's logo, never on a real record. Teardown by
  exact title. If the CMS shows no alt-text field on the image dialog the case describes,
  the test fails with that evidence — do not retarget the assertion.
- 134429: open the live HeaderConfiguration edit form and look for a Language Switcher
  enable/disable control. If absent → fail with evidence (requirement not implemented). If
  present → disable/verify public/restore under the approval above.

**131055 Global Advanced Search CMS (eng-a11y, after the above)** — batch
`.claude/qa-runs/phase3_131055_cp_batch.json` (21 automate + 1 manual, not scripted).
- New files: `cms/pages/global_search/global_search_admin_page.py`,
  `cms/tests/global_search/test_global_search_control_panel.py` (+ `__init__.py`).
- No document names this configuration screen; the user believes it may not exist.
  Write ONE locator helper that tries, as TEST_USER (the cases say "Administrator"):
  (a) an Object Authoring entry whose guide name mentions search — **only if the Content
  Admin Guide names one** (it does not today), then (b) Liferay Control Panel →
  Configuration → Instance Settings / System Settings → Search. If none shows Results
  Per Page / Indexed Content Types / Available Filters / Re-index Schedule fields, every
  test fails at step 1 with `"Global Search configuration screen not found: checked <list>"`
  plus a screenshot. Auth cases (141846, 141890, 141892, 141894) use Author / Editor via
  `cms_role_credentials` and assert denial positively.
- **If the screen IS found: stop before any Save or Trigger Re-index**, record the URL and
  fields in your report and return. Site search config and re-index are NOT approved.

## Do not touch
`core/` (incl. `core/web/base_page.py` — a framework repair there is pending the user's
decision), `pytest.ini`, `tools/sync_tc_markers.py` runs, `object_authoring_page.py`.
If you need any of these, stop and report.

## Report back (under 30 lines)
Per tc_id: implemented / how restore works / anything that cannot be built. Uploaded
files. Any QCTEST record you could not delete. Confirmation both approved records were
restored after every live probe (paste the verified values).
