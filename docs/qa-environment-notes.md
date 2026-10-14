# qcdev Environment Notes — Qatar Chamber

> Split out of `.claude/context/active/standards.md` on 2026-09-30.
> **This file is reference, not rules.** The binding rules live in
> `standards.md`; this file holds the environment facts those rules rest on.
> Read it when a run misbehaves, not before every run.

Environment: `https://qcdev.ihorizons.com` — a shared Liferay dev instance.
It is **shared, live, server-scoped state**. Nothing here is a private sandbox.

---

## 1. Navigation quirks — handle on every page load (Web + Control_Panel)

Confirmed live 2026-08-12. Both must be handled before a test interacts with
the page.

**Announcement popup dialog** (e.g. "إشعار عطلة عيد الأضحى") — appears on fresh
page loads on both surfaces. Click its `×` (`إغلاق`) close button first; it
intercepts pointer events and blocks clicks underneath if left open.

**Liferay "developer mode connection limit" license page**
(`/c/portal/license_activation`) — a dev-instance-only quirk (too many
concurrent dev connections), **not** a real license or product blocker. When
Control_Panel navigation lands here, click the **"here"** link
(`/c/portal/license?cmd=resetState&resetToken=...`) to reset connections; it
redirects through to the intended page. Dismiss the announcement popup first if
it is also present.

> **The reset is scoped to the browser session/cookies that clicked it, not the
> whole server.** A fresh, cookie-less request (a `curl`, a new automated
> session) hits the same block again even right after a successful reset
> elsewhere — confirmed 2026-08-18, and it cost real time to re-diagnose.
> Automated runs must perform the reset-then-navigate sequence themselves, in
> the same browser context. Handled in `core/web/license_gate.py`.

**Session drop under sustained traffic** — `core/web/session_guard.py`
documents a ~30 s session-drop behaviour under sustained automated traffic.
This is the mechanism behind most "worked once, timed out the second time"
reports.

---

## 2. CMS admin UI locale drift

The shared `TEST_USER` account's Liferay UI language preference is **persisted
server-side** (account profile, not just a session cookie) and can end up set
to Arabic — e.g. from a prior manual QA session that clicked the site's "AR"
switcher while signed in as this shared account.

When that happens, every English-text locator (`role=link[name="Edit"]`,
"Preview", "Unpublish", "Delete", the whole Object Authoring action bar) stops
matching. The symptom looks like *"no live row found for category X"* or
timeouts on buttons that are actually rendered under Arabic accessible names.
**It is not a locator bug and not missing data.**

`CmsLoginPage.login()` forces English on login
(`/c/portal/update_language?languageId=en_US`) as a first line of defence, but
this has been observed **not to hold for a whole run** — the account can flip
back mid-run through a path not yet root-caused (open since 2026-09-15;
suspects: a re-auth path bypassing the fixed `login()`, or portlet-level
language negotiation independent of the account preference).

**Diagnostic:** if early tests pass with real assertions and later tests in the
*same* run fail with "no live row found" / element-not-found on
previously-fine locators, suspect locale drift before assuming a data or
selector problem. Live-check the admin page's action text (`Edit` vs `تحرير`)
to confirm before reporting a product bug.

---

## 3. CMS UI vocabulary drift (2026-09-28)

The Liferay CMS renamed workflow actions and statuses under the team. Stale
locators from before the rename fail **suite-wide**; these are *not* product
bugs:

| Old label (stale locators) | Current label |
|---|---|
| `Submit for Publishing` | `Submit for Review` |
| `Approved` (status) | `PUBLISHED` |

Treat a mass failure on these strings as migration debt, not a regression.

---

## 4. Active Status gates public visibility

Content will not appear on the public site unless its **Active Status** is
enabled, regardless of Published/Approved state. A failing propagation
assertion ("edited value did not appear on the public listing within N
seconds") is **not** automatically a caching bug or a product defect — check
Active Status on the target record first. It is the most common root cause.

---

## 5. Shared / singleton records and their `xdist_group` tags

Under `pytest.ini`'s `-n 3 --dist loadgroup`, a test that mutates a shared
record carries `@pytest.mark.xdist_group(...)` so xdist never schedules two of
them concurrently. Everything else parallelises freely.

### 5a. Groups actually applied in the code — audited live 2026-09-30

| Group tag | Tests carrying it | Shared thing it protects |
|---|---|---|
| `board_directory_page_main` | 21 | the single Board of Directors page draft |
| `smi_production_rows` | 5 | the 9 real production Social Media Icon rows |
| `gm_message_79878` | 5 | GM Message singleton, record 79878 |
| `pin_event_49205` | 4 | Upcoming Event Pins singleton, record 49205 |
| `hero_banner_slide_45560` | 4 | Hero banner slide 45560 |
| `achievement_counter_45659` | 4 | About-Us achievement counter 45659 |
| `member_services_sector_80734` | 3 | Member Services sector 80734 |
| `qatar_airways_45776` | 2 | Qatar Airways partner, record 45776 |
| `mission_49082` | 2 | Mission pillar card, record 49082 (`tc_135557`, `tc_135562`) |
| `contact_us_public_webform` | 2 | the public Contact Us webform |

### 5b. Drift found against the old standards.md table — OPEN

The table that used to live in `standards.md` had drifted **in both
directions**. Recorded here as measured; **no grouping has been changed**,
because altering xdist scheduling against a shared live environment is a
decision for the QA Manager, not a documentation fix.

**Listed in the old table, never applied in code:**
`objectives_49108` · `about_us_section_52157` ·
`home_contact_us_section_article_53012` · `home_contact_us_inquiry_category_52706`

**Applied in code, absent from the old table:**
`board_directory_page_main` · `smi_production_rows` · `hero_banner_slide_45560` ·
`achievement_counter_45659` · `member_services_sector_80734` ·
`contact_us_public_webform`

**Rows that "matched" but under-counted:** the table attributed
`gm_message_79878` to `tc_135453` only (code: 5 tests) and `pin_event_49205` to
`tc_135670` only (code: 4 tests).

### 5c. What the audit did NOT find — the Strategic Pillar Card module is clean

The old table implied `objectives_49108` should be on "any Strategic Pillar Card
test (`tc_135558` etc.)". It is on none of them. **That is not, however, an
unprotected-real-record risk**, which was verified rather than assumed:
`tc_135556`, `tc_135558`, `tc_135559`, `tc_135560`, `tc_135561` in
`cms/tests/home_strategic_direction/` each **create their own disposable
`QCTEST-<tc_id>-*` card**, act on it, and delete it by entry code in teardown.
None touches the real Vision/Mission/Objectives records. That is exactly what
`standards.md`'s disposable-test-data and never-delete-by-position rules
require — the module complies.

**The residual, lower-severity question (open):** those disposable cards are
created in the *same* pillar-card carousel that `tc_135557`/`tc_135562` mutate
under `xdist_group("mission_49082")`, and some assert on public carousel
contents/ordering. A module-level group would remove that interference.
`standards.md`'s own merge rule ("if a test straddles two, merge the groups")
points that way. **Decision required before changing anything.**

### 5c-bis. ✅ 39 tests sharing ONE real Board Member record — FIXED 2026-10-01

**The most serious gap found in the 2026-09-30 audit. Resolved 2026-10-01.**

In `cms/tests/board_of_directors/test_board_of_directors_control_panel.py`, the
fixtures `board_member_field_edit`, `short_bio_edit`, `role_badge_label_edit`,
`display_order_edit` and `board_member_rich_text_edit` each:

1. open the **first** row matching category "Board Member" —
   `member_row_by_category` → `find_row_index_by_category`, which is
   **deterministic**, so every test gets the *same* row;
2. capture that field's original value;
3. edit it;
4. revert it in teardown.

**39 tests do this, and none carries an `xdist_group`.** The module's 21
page-draft tests are correctly grouped under `board_directory_page_main`; these
39 are not.

Under `pytest.ini`'s `-n 3 --dist loadgroup`, three of them can run
concurrently against that one real record. Interleaved capture/edit/revert is a
**lost update**: a revert can write back a value another test had just set,
**permanently corrupting real CMS content** — not merely producing a flaky
failure. This is the same failure class that destroyed record 49108 on
2026-09-03.

**Fix applied 2026-10-01 (QA Manager approved):** all 39 now carry
`@pytest.mark.xdist_group("board_member_shared_row")`. Verified: 0 tests using
those five fixtures remain ungrouped. The module's two groups are now
`board_directory_page_main` (19, the shared page draft) and
`board_member_shared_row` (39, the shared member row).

**Standing rule:** a new test using any of those five fixtures MUST carry the
same group. The fixtures resolve to one shared row whatever the test is named —
a fixture that selects by "first match" is a shared-record fixture even when
nothing in its name says so.

Tests using the `disposable_member` fixture create and delete their own record
and are unaffected.

### 5d. The `Vision` record — the old table's note was probably wrong

The old table carried: *"Vision (real record, ID pending confirmation) is the
third member of the same Strategic Pillar Card carousel as Mission (49082) and
Objectives (49108)."*

That appears to **conflate two different CMS surfaces**:

- **Strategic Pillar Cards** (`cms/tests/home_strategic_direction/`) — numeric
  record IDs, including Mission `49082` and Objectives `49108`.
- **VMO Section** (`cms/pages/vision_mission_objectives/vmo_admin_page.py`) — a
  **separate 3-entry object**, slug `vmo-section`, keyed by external reference
  code, confirmed live 2026-09-07:
  `QCDEMO-129395-VMO-VISION`, `QCDEMO-129395-VMO-MISSION`,
  `QCDEMO-129395-VMO-OBJECTIVES` (all APPROVED at baseline).

So "the missing Vision ID" may be chasing a number that does not exist on that
carousel. Confirm which surface is meant before adding any row.

### 5e. Baselines — last verified live 2026-09-01

| Record | Baseline |
|---|---|
| Mission (49082) | Pillar Title = "Mission" |
| Qatar Airways (45776) | Active = True |
| GM Message (79878) | Status = Published |
| Upcoming Event Pin (49205) | pinnedEvent = `/web/qatar-chamber/events/novgorod-delegation`, active = True |
| VMO Vision | Section Label "Vision", Headline "INTERNATIONAL LEADERSHIP", Active=True |
| VMO Mission | Section Label "Mission", Headline "REPRESENT. SUPPORT. ELEVATE.", Active=True |
| VMO Objectives | Section Label "Objectives", Headline "FIVE PILLARS OF GROWTH", Active=True |

All four numeric records confirmed at baseline on 2026-09-01 — no restore was
needed. VMO baselines confirmed 2026-09-07.

---

## 6. Named CMS role accounts

Eight named accounts are provisioned on qcdev (2026-09-27; the retired
`*@xyz.com` logins are gone). Credentials live in `.env` — one shared password —
and are resolved through `config.settings.cms_role_credentials(role)`.

| Role (`cms_role_credentials`) | Site role | Email | User id |
|---|---|---|---|
| `Site Content Editor` | QC Site Content Editor | `qc.editor.test@qatarchamber.local` | 156488 |
| `Site Content Author` | QC Site Content Author | `qc.author.test@qatarchamber.local` | 156492 |
| `Content Contributor` | QC Site Content Contributor | `qc.contributor.test@qatarchamber.local` | 156496 |
| `Form Manager` | QC Form Manager | `qc.forms.test@qatarchamber.local` | 156500 |
| `Event Organizer` | QC Event Organizer | `qc.events.test@qatarchamber.local` | 156504 |
| `SEO Manager` | QC SEO Manager | `qc.seomanager.test@qatarchamber.local` | 156508 |
| `SEO Editor` | QC SEO Editor | `qc.seoeditor.test@qatarchamber.local` | 156512 |
| `Site Member` | *none — site member only* | `qc.member.test@qatarchamber.local` | 156516 |

`TEST_USER` / `TEST_PASSWORD` is a **super-admin-equivalent** login for setup and
general CMS access — never for role-scoped permission testing. Passwords are not
reproduced here; read them via `cms_role_credentials()`.

> Superseded gap: the old `Test2@xyz.com` Author login did **not authenticate**
> (see `cms/tests/export_reports/...`'s `tc_143858`/`tc_143859`). The
> replacement `qc.author.test` account signed in live 2026-09-28, so any skip
> still citing that reason is stale and should be re-checked.
