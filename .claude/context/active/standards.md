# QATAR CHAMBER — QA Standards & Conventions

> Process-level rules for the Qatar Chamber QA system. Keep test cases and
> deliverables consistent with these. Domain/service/role details come from
> `@.claude/context/active/background.md`.

## Service / Module Codes
Use in test case IDs and grouping — mapped to the BRD's website structure:

| Code | Service |
|---|---|
| `ABOUT` | About Us (Qatar Chamber, Chairman's Message, Laws, Vision/Mission, GM's Message, Board, Org Structure) |
| `SVC` | Our Services (Membership, Legal Consulting, Mediation, Information/Circulars, Training, Halls Reservation) |
| `ESERV` | E-Services (Certificate of Origin, ATA Carnet, TIR Carnet) — redirect-only gateways |
| `COMM` | Committees (Committee/Business Councils, QAFL, Joining Requests, Suggestions & Complaints) |
| `EVENT` | Events (Chamber Events, Global Events, Partners) |
| `EXPO` | Exhibitions (Made in Qatar/China Expo) — redirect-only |
| `MEDIA` | Media Center (News, Photo Archive, Video, Podcasts, Al-Moltaqa, Advertisements, Annual Reports, Publications, Commercial Directory, For Media Professionals, Event Media internal service) |
| `INVEST` | Invest in Qatar (Qatar at a Glance, Economic Laws, Visas, Investment, Business Opportunities, Business Owners Platform, Tenders) |
| `B2B` | B2B (Platform, Registration) |
| `CONTACT` | Contact Us |
| `CHATBOT` | AI-Powered Chatbot |
| `GLOBAL` | Cross-cutting site features (navigation, header/footer/widgets, bilingual engine, SEO/friendly URLs, announcement popup, TTS, newsletter, sitemap, keyboard nav, global search) |
| `CMS` | CMS/Admin backend (user management, workflow, audit logging, lookup master data, permissions) |
| `LINKS` | Useful Links, FAQ Knowledge Base |

## Platform / Surface Codes
The Platform tag is **exactly one (or more) of these two values** for this project —
there is no mobile app in scope:

| Code | Surface |
|---|---|
| `Web` | The public Qatar Chamber website (desktop/tablet/mobile responsive) |
| `Control_Panel` | Liferay CMS / admin backend |

If a future phase introduces `IOS`/`Android`, extend this table then — do not invent
mobile Platform tags against this BRD.

## Test Case ID Convention
`<SERVICE>-<FEATURE>-TC-<NNN>` — numbers zero-padded and sequential within a feature.

Examples:
- `SVC-MEMBERSHIP-TC-001`
- `SVC-MEDIATION-TC-014`
- `EVENT-CHAMBER-TC-007`
- `MEDIA-PHOTOARCHIVE-TC-022`
- `INVEST-TENDER-TC-003`
- `CMS-LOOKUP-TC-005`

## Priority Rubric
This project has **no real payment processing** (see background.md — E-Services,
Tenders, Advertisements, Halls Reservation are all gateway/lead-capture only).
Priority is therefore driven by **access control, data integrity of business-critical
submissions, and public-facing content correctness** rather than money handling:

- **P1 — Critical:** RBAC/permission bypass, AD SSO auth failures, any webform that
  silently fails to store a submission or fails to send the acknowledgement email,
  bilingual content completely missing (EN or AR blank on a published page),
  Commercial Directory / B2B Registration approval flow writing incorrect/duplicate
  data, chatbot returning ungrounded/hallucinated answers, CAPTCHA bypass.
- **P2 — High:** Core webform validation gaps (missing mandatory field enforcement:
  e.g., Tender EOI's Commercial Registration Number, QAFL's authorization letter),
  Approve/Reject workflow not updating status or not sending the correct email,
  Photo Archive Flickr import mismatches, event registration limit not enforced when
  configured, Global Events accidentally showing an internal registration form.
  Money is not on this list — page-load and content-lifecycle correctness are the
  closest P2/P3 analogue here.
- **P3 — Medium:** Search/filter/sort inaccuracies, secondary field validation,
  pagination edge cases, lookup master-data dropdown not reflecting a newly added
  value, Add-to-Calendar export field mismatches.
- **P4 — Low:** Cosmetic/RTL layout nuances, tooltip/label wording, non-blocking
  accessibility polish beyond the explicit keyboard-nav/contrast requirements.

## Tag Taxonomy
Every test case carries a **`Tags`** attribute — one or more keywords that describe
it at a glance. Tags are **queryable in Azure DevOps** (they land in `System.Tags`
via the MCP), so they are how we slice the suite later: build the automation set
(`Tag = Automation`), pick the regression re-run subset (`Tag = Regression`), export
the client doc (`Tag = UAT`), etc.

**The agent decides every tag.** Tag selection is pure QA judgement and lives here in
the standards — the agent applies it when it writes each case. The MCP does **no**
tag thinking: it injects the tags the agent decided, verbatim, and adds exactly one
provenance tag of its own (Axis 0).

Tags are organized in axes. A typical case carries **one tag from several axes**
(at minimum a Service, a Platform, a Category, and any applicable Lifecycle tag).

### Axis 0 — Provenance *(MCP-applied — the ONLY automatic tag)*
| Tag | Applied by | Meaning |
|---|---|---|
| `Ai_MCP_Injected` | The MCP, automatically, on every injected case | Marks the case as created through the AI/MCP pipeline. The **agent never adds this**; the **MCP always does**. |

### Axis 1 — Lifecycle / Suite *(the important ones)*
| Tag | Meaning | Used for |
|---|---|---|
| `Regression` | A **MAIN / basic functional scenario** — the feature's headline happy + critical-negative paths that must be **re-run after every change**. A focused subset, not most of the cases. | The regression **re-run** suite. Every `Regression` case is also `Automation`. |
| `UAT` | A **direct, primary** acceptance scenario in plain business language — what the **client** signs off on. | Client UAT document (the Drafter filters `Tag = UAT`). |

> **How to decide `Regression`:** the case is a MAIN functional scenario — the
> primary happy path and critical headline negative paths a real content editor or
> public visitor hits (e.g., "publish a news article," "submit a Tender EOI with
> valid data," "AD SSO login succeeds"). Do **not** tag deep field-validation,
> boundary, lookup-value, or RTL-cosmetic cases as `Regression`.
>
> **How to decide `UAT`:** a direct, primary scenario the client validates in plain
> language — main happy paths for the features the client will actually
> demo/sign-off on (About Us pages render, a webform submits and the applicant gets
> an email, a news article publishes and is visible, the chatbot answers a grounded
> question). Not every case is a UAT case.

### Axis 1b — Execution Method *(`Automation` / `Manual` — mandatory, exactly one)*
| Tag | Meaning |
|---|---|
| `Automation` | The case **can be automated** and therefore **will be**. Bias toward this. |
| `Manual` | The case **cannot reasonably be automated** — CAPTCHA solving, actual email inbox visual review, physical file/malware-scan verification requiring real infected samples, chatbot subjective response-quality judgment, cron-job timing verification requiring real clock waits beyond practical automation. |

> Decided by the automation engineer in the pre-injection classification pass, **not**
> by the `qa-engineer`. `Regression` ⊆ `Automation`.

### Axis 2 — Service
Per the **Service / Module Codes** table above: `ABOUT` · `SVC` · `ESERV` · `COMM` ·
`EVENT` · `EXPO` · `MEDIA` · `INVEST` · `B2B` · `CONTACT` · `CHATBOT` · `GLOBAL` ·
`CMS` · `LINKS`.

### Axis 3 — Platform / Surface
**Exactly one or more of:** `Web` · `Control_Panel` (see Platform / Surface Codes
above — no mobile tags on this project).

### Axis 4 — Category *(from the analysis framework)*
One of: `UI` · `Compatibility` · `Auth` · `Functional-High` · `Functional-Low` ·
`API` · `Edge`. *(The framework's "Additional / Conditional" bucket is **not** a tag
value — tag those cases with the concrete category they most resemble: e.g. a Flickr
cron-sync failure → `Edge`, an SSO deactivation-mid-session case → `Auth`.)*

### Axis 5 — Business keyword *(optional, but keep consistent)*
A single project domain keyword when it helps later filtering, e.g. `Webform`,
`Bilingual`, `Workflow`, `Redirect`, `Chatbot`, `LookupData`, `Newsletter`,
`Subscription`, `Approval`, `Accessibility`.

### Do not re-add the provenance tag
The MCP **automatically** applies `Ai_MCP_Injected` at injection — do **not** include
it in your `Tags`. There are **no** other auto-applied tags — `test_type`,
`scenario`, `execution_type`, `impact_area`, and language remain case **attributes**,
not auto-emitted tags.

## Webform / Approval-Workflow Rules (special attention)
This project's dominant pattern is the **generic webform → acknowledgement email →
admin Approve/Reject → (approval-only) confirmation email** flow, repeated across
~15 features. For any such feature, always:
- Verify the submission is actually **stored** before assuming the email fired.
- Verify **mandatory vs. conditional** fields per the specific form (they differ
  significantly feature to feature — e.g., Tender EOI's Commercial Registration
  Number is mandatory while CR Number/Establishment Card are conditional).
- Verify the **rejection path does NOT silently drop the record** — rejected
  requests must remain stored for reporting, even when no rejection email is sent
  (confirm per-feature whether rejection triggers an email — most do **not**, a few
  do — do not assume uniformly).
- Verify CAPTCHA is present and enforced on every public-facing form.
- Verify duplicate-submission handling per feature (some explicitly "allow but log,"
  others block via email+subject/company-name matching within a time window).
- Treat any submission-storage or email-notification failure as **P1**, mirroring
  how money flows are treated on payment-heavy projects.

## Bilingual Content Rules (special attention)
Nearly every field in this BRD is bilingual (EN/AR) by default. For any content or
form feature, always:
- Verify both language fields are enforced as mandatory where the BRD says so (most
  titles/descriptions are; some secondary fields are EN-only or AR-only by design —
  check the specific field table).
- Verify RTL rendering for Arabic and LTR for English, including in accordions,
  tables, and the chatbot.
- Verify the "if translation is missing, redirect to home page" fallback rule
  applies where explicitly stated (About Us pages), and does **not** get assumed on
  features where it wasn't stated.

## Definition of Done (coverage)
A feature's analysis is complete only when ALL are addressed **for the active
analysis mode** (Normal default / Deep — see `analysis-framework.md` → *Analysis
Modes*):
- Every **in-scope** analysis-framework category covered (or explicitly marked N/A
  with a reason). *In Normal mode, API, the Additional/Conditional category, and all
  non-functional/security/performance cases are out of scope by design — not gaps.*
- Happy + sad paths for each in-scope flow and each field.
- Edge cases derived via the 4-step methodology (**full** in Deep mode; a **lighter**
  key-edge sweep in Normal mode).
- Each acceptance criterion in the relevant FR maps to ≥ 1 test case (traceability).
- Webform storage + email-notification correctness applied wherever a submission
  changes state (per the Webform/Approval rules above).
- Bilingual completeness applied wherever content is authored (per the Bilingual
  rules above).
- Every test case carries a `Tags` value (≥1 tag — see Tag Taxonomy).
- `UAT` applied to the **direct, primary** acceptance scenarios for the client
  deliverable.
- `Regression` applied **only** to the feature's MAIN functional scenarios (the
  focused re-run subset) — never to deep field-validation, boundary, or edge cases.
- **Every case classified `Automation` or `Manual`** (Axis 1b) by the Automation
  engineer in the **pre-injection** pass.
- **Before analyzing a feature, check whether it (or a sub-capability of it) appears
  in the BRD's "Approved Out of Scope" or "Out of Scope" lists** — if so, either skip
  it or explicitly scope the analysis down to only the core FR behavior, noting the
  exclusion in the sign-off.

## Dev-Environment Navigation Quirks (apply on every page load, Web + Control_Panel)
Confirmed live on qcdev.ihorizons.com 2026-08-12 — handle both before any test
interacts with the page, same as the website flow. Restored 2026-08-18: this
section was silently dropped by commit `55a5c91` ("baselines from Phase 1/2 PBI
runs", 2026-08-16) — a routine baseline-sync commit that overwrote local
additions to this file. If you run `analyze-pbi`/baseline-sync tooling again,
diff this file afterward rather than assuming it's untouched.
- **Announcement popup dialog** (e.g. "إشعار عطلة عيد الأضحى") — appears on
  fresh page loads on both Web and Control_Panel. Click its `×` (`إغلاق`)
  close button first; it intercepts pointer events and blocks clicks
  underneath if left open.
- **Liferay "developer mode connection limit" license page**
  (`/c/portal/license_activation`) — a dev-instance-only quirk (too many
  concurrent dev connections), not a real license/product blocker. When
  Control_Panel navigation lands here, click the **"here"** link
  (`/c/portal/license?cmd=resetState&resetToken=...`) to reset connections;
  it redirects through to the intended page (e.g. `/home`). Dismiss the
  announcement popup first if it's also present. **The reset is scoped to the
  browser session/cookies that clicked it, not the whole server** — a fresh,
  cookie-less request (e.g. `curl`, or a new automated session) will hit the
  same block again even right after a successful reset elsewhere (confirmed
  2026-08-18, cost real time to re-diagnose). Automated runs must perform the
  reset-then-navigate sequence themselves, in the same browser context, not
  assume a prior manual reset carries over.

## Automation Structure — Project Deviation from the Plugin Default

The section that used to live here was **lost in an accidental overwrite** (commit
`55a5c91`, "baselines from Phase 1/2 PBI runs", 2026-08-16) — the same commit that
also dropped the Dev-Environment Navigation Quirks section above (restored
2026-08-18). While this doc was silently missing its rule, a `web/pages/control_panel/`
+ `web/pages/header/` tree was written directly against `qcdev` (real locators,
one passing web test, one `Control_Panel` RBAC test) — a **separate-tree** pattern
the original 2026-08-11 rule had explicitly rejected.

**Superseded 2026-09-01: the no-separate-tree rule no longer stands.** The
2026-08-19 re-confirmation above is kept for history only — do not follow it.
The QA Manager reviewed the co-located layout again and decided the CMS/Admin
side deserved its own top-level tree after all, for clearer ownership between
public-site and control-panel automation. Going forward:

- Framework lives at the **project root**, not `./automation/` (flattened
  2026-08-11 at the QA Manager's request) — this part is unchanged.
- **Separate top-level trees by surface**, each mirroring the same
  `pages/<page>/` + `tests/<page>/` layout internally:
  ```
  web/pages/<page>/<page>_page.py             # public-frontend locators/actions
  web/tests/<page>/test_<page>_web.py          # Web-tagged cases

  cms/pages/<page>/<page>_admin_page.py        # CMS/Control_Panel locators/actions
  cms/tests/<page>/test_<page>_control_panel.py # Control_Panel-tagged cases
  ```
  `cms/pages/control_panel/login_page.py` (shared CMS login) lives under the
  `cms/` tree too, not `web/`.
  `pytest.ini`'s `testpaths` is `web cms` (both trees collected by default).
  Marker-based selection (`pytest -m web` / `pytest -m control_panel`) still
  targets one surface without depending on the folder split — the markers and
  the trees are two independent, redundant ways to scope a run.

**Section folder naming — Sprint 1 (Home page), agreed 2026-08-18.** Skeleton
folders (empty, `__init__.py` only) were pre-created under `web/pages/` and
`web/tests/` ahead of `automate-test-case`, one per PBI below, using the file-suffix
pattern above. Phase 1 (now) fills in `<section>_page.py` / `test_<section>_web.py`;
Phase 2 (later) adds `<section>_admin_page.py` / `test_<section>_control_panel.py`
in the same folders — no new subfolders.

Cross-page globals (GLOBAL service) → `pages/components/` / `tests/components/`
(shared, per the plugin's component exception — flat inside `components/`, not their
own page folder):

| PBI | Section | File base |
|---|---|---|
| QC-GBL-001 | Site Header | `header` |
| QC-GBL-004 | Site Footer & Social Media Icons | `footer` |
| QC-GBL-002 | Language Switcher | `language_switcher` |
| QC-GBL-003 | Accessibility Tools | `accessibility_tools` |
| QC-GBL-005 | Newsletter Subscription | `newsletter_subscription` |

Home-page sections (each its own page/module folder):

| PBI | Section | Folder |
|---|---|---|
| QC-HOME-001 | Hero Banner | `home_hero_banner` |
| QC-HOME-002 | Promotional Banners / Ad Slots | `home_promo_banners` |
| QC-HOME-003 | Our Services Section | `home_services` |
| QC-HOME-004A | Latest News Section | `home_latest_news` |
| QC-HOME-004B | Social Media Icons (homepage widget — distinct from GBL-004's footer icons unless confirmed otherwise) | `home_social_icons` |
| QC-HOME-005 | Strategic Direction Section | `home_strategic_direction` |
| QC-HOME-006 | Upcoming Featured Event | `home_featured_event` |
| QC-HOME-007 | Business Events Section | `home_business_events` |
| QC-HOME-008 | Dynamic Widgets (Weather, Marhaba Guide, B2B) | `home_dynamic_widgets` |
| QC-HOME-009 | Community Partners | `home_community_partners` |
| QC-HOME-010 | Publications Section | `home_publications` |
| QC-HOME-011 | Qatar Chamber Podcast Section | `home_podcast` |
| QC-HOME-012 | Media Gallery Section | `home_media_gallery` |
| QC-HOME-013 | About Us Section & Last Year Achievements Counters (bundled as one Page Object — split later if the PBI is split) | `home_about_summary` |
| QC-HOME-014 | Quick Contact Us Section | `home_quick_contact` |
| QC-HOME-015 | Strategic Partners | `home_strategic_partners` |

## Writing Rules
- **Titles:** action + condition (e.g. "Submit Tender EOI with missing Commercial
  Registration Number").
- **Steps:** numbered, one action each, no ambiguity.
- **Expected results:** specific and verifiable — never "works correctly" (e.g. not
  "form submits successfully" but "submission is stored with status Pending, and an
  acknowledgement email is sent to the applicant's entered address").
- **Test data:** concrete values, not "valid data" (e.g. `Commercial Registration
  Number = 123456`, `Ad Type = Website Banner`).

## Default Scope
- **Surfaces:** default to `Web` for all public-facing features; add `Control_Panel`
  for the corresponding admin/CMS management cases of the same feature.
- **Languages:** Arabic (RTL) + English (LTR) unless told otherwise — this project
  treats bilingual coverage as core, not optional.
- **Theme + Contrast:** Light/Dark mode and the Normal/High-Contrast toggle are
  BRD-confirmed requirements, same coverage tier as bilingual — see
  `background.md`'s Accessibility/Theme entries for the source facts. (The
  detailed "2 languages × 2 themes × 2 contrast" test-matrix methodology that
  used to live here was lost in the same commit that dropped the section
  above; UI-rendering cases should still get real theme/contrast coverage,
  not just the default light/EN pass — restore the full matrix guidance here
  if the team wants it written back out.)

## Execution Process Conventions (agreed 2026-09-01)

**No full-batch reruns while actively fixing a failure.** While iterating on a fix for
one or a handful of failing tests, run only those specific test(s) by marker/nodeid
(e.g. `pytest -m tc_135453` or `pytest path::test_name`) — never the full suite or a
whole module. Reserve full-batch runs for final confirmation once the targeted fix is
verified green. A full rerun on every edit wastes qcdev session budget (see the
session-drop note below) and produces noisy, hard-to-diff evidence for what is really a
single-test question.

**No concurrent live-browser agents against the shared qcdev session.** Live-browser
exploration or mutation work against `qcdev.ihorizons.com` must run ONE agent at a time
— never two or more background agents driving real browsers against it simultaneously,
even though each uses its own separate Playwright browser instance. Confirmed live
2026-08-31: running multiple background agents concurrently caused agents to land on
each other's navigations mid-test. Root cause is that qcdev's `TEST_USER` session and
Liferay's server-side portlet-instance IDs are shared, server-scoped state — they are
NOT safely concurrent across independent browser processes, unlike a normal multi-tab
local test run. This compounds with `core/web/session_guard.py`'s documented ~30s
session-drop behavior under sustained automated traffic: concurrent agents multiply
load on the same dev-mode connection limit that already causes single-agent runs to
trip the license-activation gate. Sequence live qcdev work explicitly; parallelism is
fine only for work that never touches a live browser session (e.g. reading/writing
local files, static analysis).

## Fast Dev-Loop / `--lf` / `-x` (agreed 2026-09-01)

While iterating on a single fix, don't rerun the whole file or marker-set to get
feedback — use pytest's own re-run filters instead:
- `pytest --lf` — reruns only the tests that failed on the last invocation. Use this
  after a fix attempt whose correctness you're not yet sure of, to get fast signal
  before spending a full-batch run.
- `pytest -x` — stops at the first failure. Use this when running a small targeted
  set and you want to fail fast rather than let later tests in the same set burn
  qcdev session budget after the thing you're actually diagnosing has already failed.
Reserve a full-batch confirmation run (the whole marker set / module) for once the
targeted fix is verified green under `--lf`/`-x` — same rationale as the existing
"No full-batch reruns while actively fixing a failure" rule above, just naming the
concrete flags.

## Safe Parallelism — `xdist_group` and `--dist loadgroup` (agreed 2026-09-01)

`pytest.ini`'s `addopts` now runs `-n 3 --dist loadgroup` (was plain `-n 3`, i.e.
default load-balancing with no grouping guarantee). `--dist loadgroup` is required
for `@pytest.mark.xdist_group(...)` to have any effect — without it the mark is
inert and xdist load-balances across workers exactly as before.

**Why loadgroup, not loadscope:** the real constraint on this project is "two tests
must never touch the SAME shared qcdev record concurrently," not "two tests in the
same file/class must never run concurrently." `loadscope` groups by module/class,
which would either force far more tests onto one worker than necessary (coarser
than the real constraint) or fail to protect a shared record touched by tests in
two different modules. `loadgroup` lets you name the actual constraint.

**The 4 shared/singleton qcdev records and their group tags** — every test that
mutates one of these carries the matching `@pytest.mark.xdist_group(...)` so xdist
never schedules two of them on different workers at the same time. Everything else
is left ungrouped and free to parallelize normally:

| Record | ID | Group tag | Tests carrying it |
|---|---|---|---|
| GM Message singleton | 79878 | `xdist_group("gm_message_79878")` | `tc_135453` |
| Upcoming Event Pins singleton | 49205 | `xdist_group("pin_event_49205")` | `tc_135670` |
| Mission pillar card | 49082 | `xdist_group("mission_49082")` | `tc_135557`, `tc_135562` |
| Qatar Airways partner | 45776 | `xdist_group("qatar_airways_45776")` | `tc_135832` |

A test can only belong to one `xdist_group` — before adding a new one, grep the test
body for all 4 record IDs; if a test genuinely straddles two, merge those two
records' groups into one shared group name rather than picking one and leaving a
race on the other.

**A live loadgroup-vs-serial timing comparison was attempted 2026-09-01 and was not
obtainable — reported honestly rather than manufactured.** The `-n 0` serial baseline
run of the 13 runnable tests from this batch (`tc_135669` is disclosed-unautomated,
not a 14th runnable test) itself came back unusable: 6 errors, 3 failures, 3 passed,
1 skipped, with real `playwright._impl._errors.TimeoutError: Timeout 30000ms
exceeded` failures — the same class of qcdev session-drop this file's "No concurrent
live-browser agents" section already documents. Root-cause investigation during this
same session found an actual second agent/process concurrently restructuring this
framework's directory tree (`web/pages/<page>/cms/...` → a new top-level `cms/`
tree) while the serial run was executing — i.e. a real concurrency violation of the
one-agent-at-a-time rule occurred, most plausibly explaining the timeouts rather
than the grouping/addopts change itself. Running the 3-worker `loadgroup` comparison
on top of an already-unstable baseline, and with another actor confirmed active on
the same shared qcdev session, was assessed as compounding a known-bad condition
rather than producing a trustworthy number, so it was not run. **Action for the next
session:** confirm no other agent is active (re-check `git status`/file mtimes for
unexpected concurrent changes) before attempting this comparison, then run the same
13-marker set with `-n 0` and with the new `-n 3 --dist loadgroup` addopts
back-to-back and report both wall-clock times here.

**Default going forward:** `-n 3 --dist loadgroup` per `pytest.ini`'s `addopts`.
Reserve `-n 0` for deep debugging (a single flaky test, or when qcdev's dev-mode
connection-limit gate is firing often — per the existing pytest.ini comment, try
`-n 1` before adding more gate-tolerance machinery) — not as the default posture.

**Shared-record baseline re-verified live 2026-09-01** (sequential single-session
probe, after the serial-run instability above): Mission (49082) Pillar Title =
"Mission" (baseline); Qatar Airways (45776) Active = True (baseline); GM Message
(79878) Status = Published (baseline); Upcoming Event Pin (49205) pinnedEvent =
`/web/qatar-chamber/events/novgorod-delegation`, active = True (baseline). All 4
confirmed at baseline — no restore was needed.

## Wait-Strategy Audit (agreed 2026-09-01)

Audited every Page Object built in the 2026-08-31 CMS batch
(`gm_message_admin_page.py`, `home_business_events_admin_page.py`,
`home_dynamic_widgets_admin_page.py`, `home_strategic_direction_admin_page.py`,
`home_community_partners_admin_page.py`, `home_featured_event_admin_page.py`) for
blind `wait_for_timeout(...)` calls. Findings:

- **Converted:** `HomeBusinessEventsAdminPage.delete_row_by_title()`'s two fixed
  sleeps (300ms before reading the kebab menu, 1500ms after confirming delete) were
  replaced with condition-based waits — `delete_item.first.wait_for(state="visible")`
  for the menu opening, and `row.first.wait_for(state="detached")` for the delete
  commit — each keeping the old fixed value as the upper-bound timeout, not a
  mandatory sleep. Live-verified 2026-09-01: ran the real teardown path end-to-end
  against qcdev and confirmed via a direct admin-grid query that both
  `QCTEST-135747`/`QCTEST-135748` rows were fully deleted (0 rows each) — the
  teardown that exercises this method (`_best_effort_delete`) swallows exceptions,
  so this direct grid check, not the pytest summary, is the real verification.
- **Already condition-based with a bounded fallback (no change needed):**
  `CommunityPartnersAdminPage.upload_partner_logo()` and
  `HomeBusinessEventsAdminPage.upload_event_image()` both wait on the upload
  modal iframe's `state="detached"` first, falling back to a short fixed sleep only
  if that wait itself times out — already the target pattern, not a defect.
  `HomeBusinessEventsAdminPage.save()` already waits on `wait_for_url(...
  ENTRY_PERSISTED_URL_MARKER in url)` rather than a fixed sleep, with
  `is_entry_persisted()` for the caller to assert on.
- **Justified as genuinely fixed (left as-is, evidence-based, not a blind guess):**
  `SAVE_COMMIT_GRACE_MS = 2000` (used in `GmMessageAdminPage`,
  `CommunityPartnersAdminPage`, `HomeStrategicDirectionAdminPage`,
  `HomeDynamicWidgetsAdminPage`) and `FORM_MOUNT_GRACE_MS = 2500`
  (`HomeDynamicWidgetsAdminPage`) cover a confirmed-live Liferay write-vs-read-cache
  propagation gap (the object-entry write commits synchronously, but the list/detail
  read path a subsequent portlet render queries is served off an asynchronously
  updated index that lags a beat) with **no observable DOM/network signal** — no
  toast, spinner, or distinguishable request marks "the read-side index has caught
  up." The exact window was measured live against qcdev, not guessed, and is
  documented at each call site. `GmMessageAdminPage`'s extra 250ms settle after the
  Status combobox listbox reports hidden is the same class of finding (the button's
  own label re-render lags the popup-close event by ~100-250ms, confirmed live) and
  is likewise left as a disclosed, evidence-based grace on top of the real wait, not
  in place of it.

## Do / Don't
- ✅ State assumptions when requirements are incomplete (the BRD itself flags several
  open items — e.g., unspecified browser matrix, unspecified environment names).
- ✅ Ask for acceptance criteria before deep analysis when a description-only PBI is
  too thin (per the org-wide `analyze-pbi` policy).
- ✅ Treat the webform → email → approval pattern as the backbone of most business
  logic in this project — reuse the Webform/Approval Rules checklist every time.
- ✅ Distinguish Chamber Events (internal registration) from Global Events (external
  referral only) — they are not interchangeable.
- ❌ Don't apply money/payment-flow edge-case emphasis by default — this project has
  none, unless a specific future feature changes that.
- ❌ Don't invent mobile Platform tags — this BRD is Web + Control_Panel only.
- ❌ Don't merge multiple verifications into one case.
- ❌ Don't include internal-only fields in client deliverables.
- ❌ Don't test enhancements explicitly listed in the BRD's Out-of-Scope sections as
  if they were in-scope defects.
