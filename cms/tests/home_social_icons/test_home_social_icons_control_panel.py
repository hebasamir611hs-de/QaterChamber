"""
cms/tests/home_social_icons/test_home_social_icons_control_panel.py

Intentionally still a stub — DO NOT build out this module before reading this.

2026-09-16 (Phase 3, PBI 129373 "QC-HOME-004B — Social Media Icons" hand-off,
batch "CMS Form Validation", ADO cases 131168-131196): a prior session had
ALREADY scripted all 29 of these exact cases in
`cms/tests/components/test_footer_control_panel.py`, driving
`SocialMediaIconAdminPage` (`cms/pages/components/footer_admin_component.py`),
each carrying `@pytest.mark.pbi_129373` + its own `@pytest.mark.tc_1311xx`.
Re-verified this session via `pytest --collect-only -q -m pbi_129373`: exactly
29/1034 tests collected, all from that one file; spot-checked
`tc_131168`/`tc_131180`/`tc_131188`/`tc_131196` each resolve to exactly one
test. See `test_footer_control_panel.py`'s own module docstring for the full
per-case trail (skips, live-confirmed findings, production-content caution).

Building a second module here for the same 29 cases would be a straight
duplicate — the redundancy scan forbids two tests covering the same
traceability ID, and Axis C's contract ("one test, one `tc_*` marker per
case") means a second `@pytest.mark.tc_131168` etc. here would break the
single-case retest selector `verify-ready-bugs` depends on. Nothing was
duplicated here on that basis.

WHY THE FILE LIVES UNDER `footer`, NOT `home_social_icons`, PER THE PROJECT'S
OWN MAPPING TABLE (`.claude/context/active/standards.md`'s "Automation
Structure" section) — flagged, not resolved, in this pass:
  - The table maps QC-GBL-004 (Site Footer & Social Media Icons) -> file base
    `footer`, and QC-HOME-004B (Social Media Icons, homepage widget) -> file
    base `home_social_icons` (this folder) — as two distinct rows.
  - But `footer_admin_component.py`'s "LOAD-BEARING FINDING #1" documents,
    live-confirmed, that the underlying CMS surface (`manage-social-media-
    icon`) is ONE SHARED Object Authoring object serving both the footer and
    the Home-page "Find us on social media" widget — not two separate
    objects. The 29 ADO cases in this PBI's own batch resolved (via Azure's
    own PBI-link resolution, not a guess) to PBI 129373 = HOME-004B, yet
    were scripted under the GBL-004 `footer` file base because that is where
    a previous PBI's automation for this same shared surface already lived.
  - Net effect: by the table's own mapping, an argument exists that these 29
    tests belong under `home_social_icons/` instead. Moving them is a
    decision for the QA Manager (it also means correcting the table's
    HOME-004B row, which currently reads "distinct from GBL-004's footer
    icons unless confirmed otherwise" — that conditional has now been
    confirmed otherwise). NOT done as a side effect of this batch: both
    `footer_admin_component.py` and `test_footer_control_panel.py` were
    touched by another session's heal pass on this same date, and moving
    files out from under a same-day heal is out of this task's scope.

OPEN QUESTION, ALSO FLAGGED FOR THE QA MANAGER: three of the 29 cases assert
on the live PUBLIC frontend — 131188 ("...reflects the icon's frontend
position"), 131194 ("...excludes it once published"), 131196 ("...has no
frontend effect [on Home]"). The existing tests assert against the FOOTER's
"Find us on social media" container (`web/pages/components/footer_component.py`).
But Finding #1 also documents three fields this shared surface carries that
are specific to the Home-page delivery surface — "Show on Home", "Home Icon
Image", "Home Display Order" — left untouched (default/blank) by every
existing test. If the Home-page widget only renders an entry that has "Show
on Home" set, these three tests may be asserting the wrong delivery surface
for a PBI-129373 (HOME-004B) batch specifically. Not re-authored here per
this task's own instruction not to reinterpret case intent, and per
automation-standards.md's rule against loosening/rewording an expected result
mid-pass — surfaced as a named risk instead.

No test functions, no markers, in this file — nothing here can collide with
the existing `tc_*` registrations in `pytest.ini`.
"""
