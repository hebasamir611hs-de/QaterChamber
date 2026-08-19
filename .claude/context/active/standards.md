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

## Automation Structure — OPEN QUESTION, needs a team decision
The section that used to live here (`Automation Structure — Project Deviation from
the Plugin Default`, written 2026-08-11) was **lost in the same accidental
overwrite** as the Dev-Environment Navigation Quirks section above (commit
`55a5c91`, "baselines from Phase 1/2 PBI runs", 2026-08-16) — nobody deliberately
reversed it. It has **not** been restored yet, unlike the section above, so the
original rule is reconstructed here from git history for visibility, alongside
what's actually been built since:

**The original 2026-08-11 rule said:** framework at the project root (not
`./automation/`); test files split by **Platform suffix within each page's existing
folder** — `pages/<page>/<page>_page.py` + `<page>_admin_page.py`,
`tests/<page>/test_<page>_web.py` + `test_<page>_control_panel.py` — explicitly
**rejecting** a separate `control_panel/` tree, so `pytest -k _web` / `pytest -k
_control_panel` could target one surface without needing two folder trees.

**What's actually in the repo now contradicts that rule:** `web/pages/control_panel/`
exists as its own top-level folder (`login_page.py`, added for the shared CMS auth
flow), and `web/pages/header/` holds `site_header_page.py` +
`accessibility_settings_page.py` directly (not the `pages/components/` split used by
`web/pages/home_*`'s skeleton, added 2026-08-18 for the Sprint-1 home-page sections
below). Since the doc was silently missing when that code was written, this may not
have been a deliberate change of convention — it needs an explicit team decision:
**restore the no-separate-tree rule and refold `control_panel/`/`header/` into the
per-page file-suffix pattern, or formally adopt the separate-tree pattern already in
use and update the Sprint-1 skeleton to match.** Until decided, both patterns
coexist in the repo — do not add a third variant.

**Section folder naming — Sprint 1 (Home page), agreed 2026-08-18.** Skeleton
folders (empty, `__init__.py` only) were pre-created under `web/pages/` and
`web/tests/` ahead of `automate-test-case`, one per PBI below, using the file-suffix
pattern above (pending the open-question resolution just above). Phase 1 (now)
fills in `<section>_page.py` / `test_<section>_web.py`; Phase 2 (later) adds
`<section>_admin_page.py` / `test_<section>_control_panel.py` in the same folders —
no new subfolders, unless the open question above is resolved the other way.

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
