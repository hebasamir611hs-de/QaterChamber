# QATAR CHAMBER — QA Standards & Conventions

> **Normative rules only.** This file is read at the start of every session, so
> it carries rules and nothing else — no incident narratives, no audit logs, no
> one-off measurements.
>
> - Domain / service / role facts → `@.claude/context/active/background.md`
> - qcdev environment facts, quirks, shared-record table → `@docs/qa-environment-notes.md`
> - Why a rule exists, incidents, superseded rules → `@docs/qa-decisions-log.md`
> - What counts as a bug, one-bug-per-root-cause filing, P1/P2-first run order → `@.claude/context/active/bug-rules.md` (binding, read with this file)
>
> Restructured 2026-09-30. Superseded rule text has been **deleted**, not kept
> inline — git history and the decisions log hold it. If you find a rule here
> annotated "do not follow this", that is a bug in this file; report it.
>
> ⚠ **Section headings here are cited by name from Page Object and test
> docstrings** (e.g. `per standards.md's "Destructive Operations Against qcdev"`).
> Before renaming a heading, grep `cms/ web/ core/ tools/` for the old name and
> update the citations in the same change — a rename alone silently orphans them.

---

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

The Platform tag is **exactly one (or more) of these two values** for this
project — there is no mobile app in scope:

| Code | Surface |
|---|---|
| `Web` | The public Qatar Chamber website (desktop/tablet/mobile responsive) |
| `Control_Panel` | Liferay CMS / admin backend |

If a future phase introduces `IOS`/`Android`, extend this table then — do not
invent mobile Platform tags against this BRD.

## Test Case ID Convention

`<SERVICE>-<FEATURE>-TC-<NNN>` — numbers zero-padded and sequential within a
feature. Examples: `SVC-MEMBERSHIP-TC-001` · `SVC-MEDIATION-TC-014` ·
`EVENT-CHAMBER-TC-007` · `MEDIA-PHOTOARCHIVE-TC-022` · `INVEST-TENDER-TC-003` ·
`CMS-LOOKUP-TC-005`

## Priority Rubric

This project has **no real payment processing** (see `background.md` —
E-Services, Tenders, Advertisements, Halls Reservation are all gateway /
lead-capture only). Priority is therefore driven by **access control, data
integrity of business-critical submissions, and public-facing content
correctness** rather than money handling.

- **P1 — Critical:** RBAC/permission bypass, AD SSO auth failures, any webform
  that silently fails to store a submission or fails to send the acknowledgement
  email, bilingual content completely missing (EN or AR blank on a published
  page), Commercial Directory / B2B Registration approval flow writing
  incorrect/duplicate data, chatbot returning ungrounded/hallucinated answers,
  CAPTCHA bypass.
- **P2 — High:** Core webform validation gaps (missing mandatory field
  enforcement: e.g. Tender EOI's Commercial Registration Number, QAFL's
  authorization letter), Approve/Reject workflow not updating status or not
  sending the correct email, Photo Archive Flickr import mismatches, event
  registration limit not enforced when configured, Global Events accidentally
  showing an internal registration form. Money is not on this list —
  page-load and content-lifecycle correctness are the closest analogue here.
- **P3 — Medium:** Search/filter/sort inaccuracies, secondary field validation,
  pagination edge cases, lookup master-data dropdown not reflecting a newly added
  value, Add-to-Calendar export field mismatches.
- **P4 — Low:** Cosmetic/RTL layout nuances, tooltip/label wording, non-blocking
  accessibility polish beyond the explicit keyboard-nav/contrast requirements.

---

## Tag Taxonomy

Every test case carries a **`Tags`** attribute. Tags are **queryable in Azure
DevOps** (they land in `System.Tags` via the MCP), so they are how the suite is
sliced later: the automation set (`Tag = Automation`), the regression re-run
subset (`Tag = Regression`), the client doc (`Tag = UAT`).

**The agent decides every tag.** Tag selection is QA judgement and lives here.
The MCP does **no** tag thinking: it injects the tags the agent decided,
verbatim, plus exactly one provenance tag of its own (Axis 0).

A typical case carries **one tag from several axes** — at minimum a Service, a
Platform, a Category, and any applicable Lifecycle tag.

### Axis 0 — Provenance *(MCP-applied — the ONLY automatic tag)*

| Tag | Applied by | Meaning |
|---|---|---|
| `Ai_MCP_Injected` | The MCP, automatically, on every injected case | Created through the AI/MCP pipeline. The **agent never adds this**; the **MCP always does**. |

### Axis 1 — Lifecycle / Suite

| Tag | Meaning | Used for |
|---|---|---|
| `Regression` | A **MAIN / basic functional scenario** — the feature's headline happy + critical-negative paths that must be **re-run after every change**. A focused subset, not most of the cases. | The regression re-run suite. Every `Regression` case is also `Automation`. |
| `UAT` | A **direct, primary** acceptance scenario in plain business language — what the **client** signs off on. | Client UAT document (the Drafter filters `Tag = UAT`). |

> **Deciding `Regression`:** the case is a MAIN functional scenario — the primary
> happy path and critical headline negative paths a real content editor or public
> visitor hits ("publish a news article", "submit a Tender EOI with valid data",
> "AD SSO login succeeds"). Do **not** tag deep field-validation, boundary,
> lookup-value, or RTL-cosmetic cases as `Regression`.
>
> **Deciding `UAT`:** a direct, primary scenario the client validates in plain
> language — main happy paths for features the client will demo or sign off
> (About Us pages render, a webform submits and the applicant gets an email, a
> news article publishes and is visible, the chatbot answers a grounded
> question). Not every case is a UAT case.

### Axis 1b — Execution Method *(mandatory, exactly one)*

| Tag | Meaning |
|---|---|
| `Automation` | The case **can be automated** and therefore **will be**. Bias toward this. |
| `Manual` | The case **cannot reasonably be automated** — CAPTCHA solving, actual email inbox visual review, physical file/malware-scan verification requiring real infected samples, chatbot subjective response-quality judgment, cron-job timing verification requiring real clock waits beyond practical automation. |

> Decided by the automation engineer in the pre-injection classification pass,
> **not** by the `qa-engineer`. `Regression` ⊆ `Automation`.
>
> **A permanently `@pytest.mark.skip`-ped automated test is not coverage.** If a
> case genuinely cannot be automated, it belongs under `Manual` in Azure, not
> skipped in code — see *Definition of Done*.

### Axis 2 — Service

Per the Service / Module Codes table: `ABOUT` · `SVC` · `ESERV` · `COMM` ·
`EVENT` · `EXPO` · `MEDIA` · `INVEST` · `B2B` · `CONTACT` · `CHATBOT` ·
`GLOBAL` · `CMS` · `LINKS`.

### Axis 3 — Platform / Surface

**Exactly one or more of:** `Web` · `Control_Panel`. No mobile tags on this
project.

### Axis 4 — Category *(from the analysis framework)*

One of: `UI` · `Compatibility` · `Auth` · `Functional-High` · `Functional-Low` ·
`API` · `Edge`. *(The framework's "Additional / Conditional" bucket is **not** a
tag value — tag those cases with the concrete category they most resemble: a
Flickr cron-sync failure → `Edge`, an SSO deactivation-mid-session case →
`Auth`.)*

### Axis 5 — Business keyword *(optional, but keep consistent)*

A single project domain keyword when it helps later filtering: `Webform`,
`Bilingual`, `Workflow`, `Redirect`, `Chatbot`, `LookupData`, `Newsletter`,
`Subscription`, `Approval`, `Accessibility`.

### Do not re-add the provenance tag

The MCP **automatically** applies `Ai_MCP_Injected` at injection — do **not**
include it in your `Tags`. There are **no** other auto-applied tags.
`test_type`, `scenario`, `execution_type`, `impact_area` and language remain
case **attributes**, not auto-emitted tags.

---

## Webform / Approval-Workflow Rules (special attention)

This project's dominant pattern is the **generic webform → acknowledgement email
→ admin Approve/Reject → (approval-only) confirmation email** flow, repeated
across ~15 features. For any such feature, always:

- Verify the submission is actually **stored** before assuming the email fired.
- Verify **mandatory vs. conditional** fields per the specific form (they differ
  significantly feature to feature — Tender EOI's Commercial Registration Number
  is mandatory while CR Number / Establishment Card are conditional).
- Verify the **rejection path does NOT silently drop the record** — rejected
  requests must remain stored for reporting, even when no rejection email is
  sent. Confirm per-feature whether rejection triggers an email (most do **not**,
  a few do) — do not assume uniformly.
- Verify CAPTCHA is present and enforced on every public-facing form.
- Verify duplicate-submission handling per feature (some explicitly "allow but
  log", others block via email+subject/company-name matching within a window).
- Treat any submission-storage or email-notification failure as **P1**.

## Bilingual Content Rules (special attention)

Nearly every field in this BRD is bilingual (EN/AR) by default. For any content
or form feature, always:

- Verify both language fields are enforced as mandatory where the BRD says so
  (most titles/descriptions are; some secondary fields are EN-only or AR-only by
  design — check the specific field table).
- Verify RTL rendering for Arabic and LTR for English, including in accordions,
  tables, and the chatbot.
- Verify the "if translation is missing, redirect to home page" fallback applies
  where explicitly stated (About Us pages), and do **not** assume it on features
  where it was not stated.

---

## Theme & Contrast Coverage Matrix *(reconstructed 2026-09-30)*

> **This is a reconstruction, not the original.** The 2026-08 "2 languages × 2
> themes × 2 contrast" methodology was lost in commit `55a5c91` and is not
> recoverable. What follows was authored 2026-09-30 from `background.md`'s BRD
> facts plus what the framework actually supports. Treat it as a working rule
> open to correction — not as ratified prior practice.

**Source facts** (`background.md`): the Normal/High-Contrast toggle is an
explicit BRD requirement; Light/Dark mode is confirmed live on the site and the
QA Manager ruled it **core, same coverage tier as bilingual**. Neither is
optional, and neither is a gap just because the BRD text is silent on Dark mode.

### Mechanism vs. rendering — test each once, in the right place

| What | Where | How often |
|---|---|---|
| **The toggle mechanism** — the switch flips, applies the state, and persists across navigation and route changes | `web/tests/components/` against `AccessibilityToolsComponent` | **Once, globally.** Never re-verified per feature. |
| **Rendering under a state** — this feature's content is correct/legible with Dark or High Contrast on | the feature's own module | Per feature, per the matrix below |

A per-feature case **asserts rendering under a state; it never re-tests the
switch**. Without this split, 40 features each re-verify the same toggle.

### Per-feature default — 4 cases, one per axis

For a feature's UI-rendering coverage, derive:

1. **EN · Light · Normal** — the baseline pass every UI case already does.
2. **AR · Light · Normal** — RTL (already required by the Bilingual rules).
3. **EN · Dark · Normal**
4. **EN · Light · High Contrast**

Each axis is represented once. This is the default, **not a ceiling** — and per
the tiered-derivation rule, the **last remaining case of any language, theme or
contrast axis is never folded**.

### When the full cross-product IS required

Derive the full 2 × 2 × 2 (8 combinations) when **either** holds — these are the
cases where the axes genuinely interact rather than compose:

1. **The feature's cases assert Figma colour or design-token values** (the case
   carries the `figma` marker, or uses `core/web/design_tokens.py`). A token that
   is correct in Light can fail contrast in Dark or be overridden in High
   Contrast.
2. **The feature renders text over an image, overlay or gradient** — hero
   banners, badge overlays, card collages. Legibility here is state-dependent
   and has already produced findings on this project.

### How to drive it — route through the shared component

Per-feature theme/contrast cases go through `AccessibilityToolsComponent`
(composed as `self.a11y` / `self.accessibility_tools`), **never a per-page
reimplementation of the toggle**. `about_chairman_message`,
`about_qatar_chamber` and `certificate_of_origin` already do this correctly.

**Assert the resulting document state, not the switch's `aria-checked`** — the
switch reporting "on" proves the control flipped, not that the theme applied:

| State | Authoritative signal |
|---|---|
| Dark mode | `<html data-theme="dark">` |
| High contrast | `<html>` carries class `qc-a11y-contrast` |

> **Known debt (target for cleanup, do not copy):**
> `web/pages/business_opportunities/listing_page.py` declares its **own** toggle
> locators and detects dark mode via `"dark" in html class` — a third, different
> signal from the two above. `AccessibilityToolsComponent` also exposes
> `switch_to_dark_mode()` and `enable_dark_mode()` as two names for one action.
> Both should converge on the component and the table above.

## Definition of Done (coverage)

A feature's analysis is complete only when ALL are addressed **for the active
analysis mode** (Normal default / Deep — see `analysis-framework.md`):

- Every **in-scope** analysis-framework category covered, or explicitly marked
  N/A with a reason. *In Normal mode, API, the Additional/Conditional category,
  and all non-functional/security/performance cases are out of scope by design —
  not gaps.*
- Happy + sad paths for each in-scope flow and each field.
- Edge cases derived via the 4-step methodology (**full** in Deep mode, a
  **lighter** key-edge sweep in Normal mode).
- Each acceptance criterion in the relevant FR maps to ≥ 1 test case.
- Webform storage + email-notification correctness applied wherever a submission
  changes state.
- Bilingual completeness applied wherever content is authored.
- Every test case carries a `Tags` value (≥ 1 tag).
- `UAT` applied to the **direct, primary** acceptance scenarios.
- `Regression` applied **only** to the feature's MAIN functional scenarios —
  never to deep field-validation, boundary, or edge cases.
- **Every case classified `Automation` or `Manual`** (Axis 1b) by the Automation
  engineer in the **pre-injection** pass.
- **Before analyzing a feature, check whether it (or a sub-capability) appears in
  the BRD's "Approved Out of Scope" / "Out of Scope" lists** — if so, skip it or
  explicitly scope the analysis down to the core FR behavior, noting the
  exclusion in the sign-off.

---

## Field-Coverage Depth — Tiered Derivation

> **STATUS: TRIAL, binding but not yet ratified.** Added 2026-09-22; the review
> it requires is **overdue as of 2026-09-30** and a graduate-or-remove decision
> is owed by the QA Manager. It remains binding until that decision is made.
> Graduation criteria and status → `docs/qa-decisions-log.md`.

Applies at **Phase 1 derivation**, per inventory row, to `Control_Panel` and
`Web` alike. It changes **how many cases a field earns** — not how a case is
written, not the tag taxonomy, and not the phase structure.

**Every reduction under this section is named in the run's reductions list**
(`<rule> : <inventory-id> → <case-id>`), exactly like `SUBSUMED-BY-FLOW`. A case
folded here is *recorded as folded*, never silently dropped. An unnamed
reduction is a defect, not a saving.

### Tier 1 — always derived, per field, never reducible

- **1 positive** — the field accepts valid input and the value persists.
- **1 negative** — mandatory enforcement (empty → blocked), where mandatory.
- **Any negative that changes stored data or blocks a business flow.**

No rule below may remove one of these.

### Tier 2 — `REPRESENTATIVE-BY-FIELD-TYPE`

Boundary / max-length / format-rejection cases are derived **once per field
*type* per feature** — short text · long or rich text · numeric · URL · file
upload — not once per field instance. These assert the **input component's**
behaviour, not the field's business rule: proving the component once per type is
the coverage; repeating it per field is duplication.

Name the representative explicitly in the coverage plan, e.g.
`REPRESENTATIVE-BY-FIELD-TYPE : short-text → Section Heading`.

> **Exemption — a field gets its own full boundary/format treatment, regardless
> of type, if ANY of these hold:**
> 1. it **drives navigation** (a URL or link target);
> 2. it **feeds a calculation** or a stored numeric value;
> 3. it carries a **format or regulatory rule** (email, CR number, ID);
> 4. it **renders publicly into a size-constrained element**.
>
> Check every field against all four before folding it. Without this exemption
> the rule eventually folds a field like `Read More URL` — P1 on this project.

### Tier 3 — `COSMETIC-FOLD`

Pure presentation checks — position, spacing, overlay placement, the styling of
a single element — fold into the feature's single "renders per design" case (the
Figma-verified overview case, where one exists).

> **The dividing test, applied per case:**
> - **Does a CMS-configured value reach the delivery surface?** → Tier 1, keep.
>   This is the CMS value chain (`cms-testing.md`: no CMS case may stop at the
>   authoring UI).
> - **Is it positioned or styled per design?** → Tier 3, fold.
>
> Worked example (PBI 129389): `136090` "badge overlay displays the
> **configured** numeric value and label" is **Tier 1** — a CMS value reaching
> the page. `136089` (collage overlapping layout) and `136093` (sub-heading
> position) are **Tier 3**.

### Never reducible under any tier

- `Functional-High` end-to-end flows (happy and sad).
- `Auth` / RBAC cases.
- The **last remaining case** of any category, any `LNG-n` (language), or any
  `ENV-n` (browser / viewport) — per `analysis-framework.md`'s subsumption rule.
  A viewport, language, or browser is never folded: the tablet Compatibility case
  stays even when a mobile one exists.
- Anything tagged `UAT` or `Regression`.

### Expected magnitude — stated honestly

Measured against PBI 129389's real injected set (53 cases), this section folds
**8–10 cases, ~15–20%**. It does **not** produce a 50% reduction: per-field
positive + mandatory coverage is ~60% of a CMS suite by design, and Tier 1
protects all of it.

The larger Phase-3 cost on this project is **environmental**. Re-measured
2026-09-30: **447 of 1,098 `cms/tests` functions carry `@pytest.mark.skip`
(41%)**, against **193 of 1,715 in `web/tests` (11%)** — 640 skipped of 2,813
total (23%). The qcdev CMS login license/connection-limit gate is the dominant
named blocker. That is a larger loss than anything derivational, and it is
independent of this section; both are worth fixing.

---

## Automation Structure

- Framework lives at the **project root**, not `./automation/`.
- **Separate top-level trees by surface**, each mirroring the same
  `pages/<page>/` + `tests/<page>/` layout internally:

  ```
  web/pages/<page>/<page>_page.py               # public-frontend locators/actions
  web/tests/<page>/test_<page>_web.py           # Web-tagged cases

  cms/pages/<page>/<page>_admin_page.py         # CMS/Control_Panel locators/actions
  cms/tests/<page>/test_<page>_control_panel.py # Control_Panel-tagged cases
  ```

  `cms/pages/control_panel/login_page.py` (shared CMS login) lives under the
  `cms/` tree, not `web/`.

- `pytest.ini`'s `testpaths` is `web cms` (both trees collected by default).
  Marker-based selection (`pytest -m web` / `-m control_panel`) targets one
  surface without depending on the folder split — markers and trees are two
  independent, redundant ways to scope a run.
- Cross-page globals (GLOBAL service) → `pages/components/` / `tests/components/`
  (flat inside `components/`, not their own page folder).
- **Keep module docstrings true.** A docstring naming the wrong tree or a stale
  `-n` value is worse than none — correct it when you touch the file.

### Section folder naming

Cross-page globals:

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
| QC-HOME-004B | Social Media Icons (homepage widget) | `home_social_icons` |
| QC-HOME-005 | Strategic Direction Section | `home_strategic_direction` |
| QC-HOME-006 | Upcoming Featured Event | `home_featured_event` |
| QC-HOME-007 | Business Events Section | `home_business_events` |
| QC-HOME-008 | Dynamic Widgets (Weather, Marhaba Guide, B2B) | `home_dynamic_widgets` |
| QC-HOME-009 | Community Partners | `home_community_partners` |
| QC-HOME-010 | Publications Section | `home_publications` |
| QC-HOME-011 | Qatar Chamber Podcast Section | `home_podcast` |
| QC-HOME-012 | Media Gallery Section | `home_media_gallery` |
| QC-HOME-013 | About Us Section & Achievements Counters | `home_about_summary` |
| QC-HOME-014 | Quick Contact Us Section | `home_quick_contact` |
| QC-HOME-015 | Strategic Partners | `home_strategic_partners` |

---

## Content Editorial Workflow — Seven States, and the Account Decides the Path (agreed 2026-09-28)

The site runs a real Kaleo editorial workflow
(`build-resources/workflow/qc-editorial-approval.xml`, not in this repo). It has
**seven** states, not the two (`Draft` / `Approved`) this file and the Object
Authoring guide previously described.

Everything in this section was confirmed live 2026-09-28 by walking one probe record
end to end on `manage-law-entry` as Author (156492) then Editor (156488), and
cross-checked on seven further objects (news-article, promotional-banner,
hero-banner-slide, publication, about-hero-banner, social-media-icon,
strategic-partner). **The workflow is global, not per-object** — every object shows
the same buttons, badges and row actions.

### The rule that matters most

**The same "Submit for Review" button lands on different states depending on who is
signed in.** Confirmed on one record, submitted twice:

- as **Author** → `Pending Review` (not public)
- as **Editor** → `Published` directly

The workflow routes a *privileged* submitter past the review step. So:

> **Never assert a content lifecycle outcome without pinning the account that
> produced it.** A test that submits and asserts "appears live" is asserting the
> privilege of its login, not the behaviour of the system. State the account in the
> test's preconditions and pick it deliberately.

This is why the previous two-state model survived so long: every observation had been
made through the super-admin `TEST_USER`, which bypasses the workflow. Findings of the
form "this build has no Pending Review status" or "no Reject action exists anywhere"
were artifacts of that account and are **withdrawn**.

### States and transitions

| State | Badge | Visitor sees it? |
|---|---|---|
| Draft | `DRAFT` | no |
| Pending Review | `PENDING REVIEW` | no |
| Rejected | `REJECTED` | no |
| Published | `PUBLISHED` | **yes** — and only if Active Status is ticked |
| Unpublished | `UNPUBLISHED` | no |
| Archived | `ARCHIVED` | no |
| Scheduled | `SCHEDULED` | not yet — at the time set |

The badge reads **`PUBLISHED`, never `APPROVED`**. Any comparison against "Approved"
is stale.

```
Draft --submit(Author)--> Pending Review --approve--> Published
Draft --submit(Editor)--> Published                (privileged bypass)
Pending Review --reject--> Rejected --resubmit--> Pending Review
Published --unpublish--> Unpublished --archive--> Archived --restore--> Unpublished
Unpublished --return to author--> Draft
Unpublished --publish--> Published
```

Archive is reachable from **Unpublished only**, and Restore returns to **Unpublished**,
not to Published. Unpublish lands on **Unpublished**, which is its own state and *not*
Draft — code that polls for "Draft" after unpublishing is asserting the wrong thing.

Not yet exercised live: the `Scheduled` state and `publish` from Unpublished. Treat
those two as unverified until someone walks them.

### Mechanics automation must respect

- The form button reads **"Submit for Review"**. The old "Submit for Publishing"
  string matches nothing. Success toast: "Saved and submitted for review."
- The editing banner **capitalises** the state — `Editing <title> (Draft).` — so
  case-sensitive `"(draft)"` matching silently fails.
- Row actions carry stable `data-qc-oel-<action>="<entryId>"` attributes (`approve`,
  `reject`, `resubmit`, `publish`, `unpublish`, `archive`, `restore`, `return`,
  `schedule`, `history`, `delete`). **Locate by the attribute, not the visible label**
  — the label is localised, the attribute is not.
- Which actions a row renders depends on **both** its status and the signed-in role.
- Every transition drives **native `confirm()` / `prompt()` dialogs**, and several
  *chain two of them* (a confirm immediately followed by a prompt). Register a dialog
  handler that accepts a run of them, not exactly one.
- `Reject` and `Return to Author` raise a prompt whose comment reaches the author and
  is stored in History; **Return's comment is required**.
- Saving a Draft skips required-field validation; Submit for Review enforces it and
  refuses with "Please complete the required fields before proceeding with the
  workflow action for <title>. Nothing has been submitted." — nothing is written.
- Each row has a **History** trail (actor, timestamp, comment) that expands *inside*
  the entries table (`ul.qc-oel__history-list`) — it is **not** a modal. This is the
  strongest evidence for a workflow assertion: it proves a transition was recorded,
  not merely that a badge changed. Prefer it over a badge read alone.
- The entries list's Status filter is built from the statuses actually present, not
  from a fixed vocabulary — do not assert its option list.

`cms/pages/components/object_authoring_page.py` implements all of the above; use its
`STATUS_*` constants and `normalize_status()` rather than string literals.

## Locators and CMS Navigation

### CMS Admin UI Locale — English-Only Locators, No Arabic Fallback

**Every locator in this codebase is English-text-based, and stays that way.** Do
not add Arabic locator variants or bilingual fallback matching anywhere in
`cms/pages/` or `web/pages/` — not even as a safety net. If a test must assert
Arabic-rendered content, read/assert the field's **data value**, not the
surrounding UI chrome text.

> The shared account's Liferay locale can drift to Arabic mid-run and break every
> English locator. Before reporting a product bug on a mass locator failure, read
> `docs/qa-environment-notes.md` § 2.

### Object Authoring Is the Only Path for Content Operations — Not Content & Data (superseded/broadened 2026-09-07)

> ### READ THIS FIRST — the authoritative guide is in the repo (added 2026-09-08)
>
> **`.claude/context/active/OBJECT-AUTHORING-GUIDE.md`** is the project team's own
> Content Editor Guide for this surface, supplied 2026-09-08. **Every agent that
> writes or runs a Control_Panel test, and every Page Object that drives Object
> Authoring, must read it before making any assumption about how the tool
> behaves.** Do not re-derive its contents by probing the live site, and do not
> contradict it from memory or from an older repo document.
>
> **Precedence:** the guide is authoritative on **tool mechanics** (URLs,
> buttons, statuses, bilingual field shapes, attachment behaviour, preview panel,
> error/success message text). This `standards.md` remains authoritative on **QA
> policy** — what we are permitted to do to `qcdev` — because policy is
> deliberately stricter than the tool. Where any other document
> (`cms/liferay-context.md`, a Page Object docstring, a test comment) disagrees
> with the guide on mechanics, **the guide wins**: fix the other document rather
> than working around it.
>
> Operational facts from the guide that automation must honour (each one has cost
> this project real time or real data):
>
> - **A 404 on an authoring URL means the session is signed out** — not a missing
>   page, not a bad slug, not a locator bug. Re-run `python tools/save_auth.py`
>   and retry before investigating anything else. (Diagnosed the hard way on the
>   PBI 129394 batch, 2026-09-07.)
> - **On a brand-new record the Arabic saves a moment *after* the record.** Wait
>   for **"Arabic content saved for this record."** before navigating away; if
>   *"the record was saved but its Arabic content was not"* appears, re-open Edit
>   and re-enter the Arabic. A test that creates a bilingual record and leaves the
>   page on a fixed timeout can silently lose the Arabic content on a real record.
> - **`Remove file` / `Undo remove` on an attachment field take effect only on
>   save, and a required attachment field refuses to be cleared.** So a
>   clear-the-field check can reach the empty state and then abandon without
>   saving. Re-evaluate any test skipped for "no safe file-restore path" against
>   this. If a *required* attachment field ever does end up empty on a live
>   record, that contradicts the guide and is a candidate **product bug** — report
>   it, do not silently repair it.
> - **`displayOrder` / `homeDisplayOrder` are numbered in multiples of 100**
>   (`100, 200, 300 …`, lowest first); never write an in-between value like `150`.
>   This is an editorial convention the platform does **not** enforce (its own
>   validation only requires `>= 1`), so a test case that dictates `1` / `2` will
>   pass validation while leaving real content mis-numbered among its neighbours
>   — flag the conflict to the QA Manager instead of just executing it.
> - **A refused save shows a red bar listing the reasons in plain words, and
>   nothing was saved.** Read that bar and assert on it; the expected per-object
>   message strings are catalogued in `cms/liferay-context.md` §6.
> - **Two independent visibility gates.** A saved record can be invisible to
>   visitors either because it is a **draft** *or* because its **`activeStatus`**
>   is off. Never conclude one from the other — check the gate the case actually
>   names.
> - **Preview is a staff surface.** The preview panel (including its `AR` toggle
>   and `Show all drafts`) renders drafts to signed-in staff, so it does **not**
>   satisfy the mandatory logged-out public-visibility check in the section above.
>   Use it to verify rendering; use a fresh logged-out context to verify
>   visibility.
> - **`Delete` has no undo and no recycle bin** — which is the tool-level
>   restatement of the never-delete-by-position rule in *Destructive Operations
>   Against qcdev* above. To take content off the site without losing it, un-tick
>   `activeStatus` or use **Unpublish to edit as draft**.

**Superseded same-day:** the rule below originally covered only publish/unpublish/
draft/preview lifecycle actions. The QA Manager has since broadened it: **`Content &
Data` is retired entirely as an automation path for any Object-Definition-backed
content record on this project — creating new content, editing field values, AND every
lifecycle action (save as draft, preview, submit for publishing, unpublish) must all go
through Object Authoring** (`https://qcdev.ihorizons.com/object-authoring`, reusable
component at `cms/pages/components/object_authoring_page.py`). Do not open `Content &
Data` for these records at all going forward, not even to fill in fields.

This does NOT apply to CMS surfaces that were never a Content & Data-vs-Object
Authoring choice in the first place — e.g. a plain widget-config toggle with no
content-lifecycle states (confirmed case: Upcoming Event Pins / record 49205, a
2-field Active-Status+pinnedEvent config, not an Object-Definition entity) stays on
its existing native mechanism. Before assuming a feature needs the Object Authoring
fix, check whether it's actually an Object-Definition-backed content record (has
workflow states — see "Content Editorial Workflow" — and an entries list on its
own `manage-<slug>` authoring page)
or a different kind of CMS surface (Events module, a dedicated portlet, a config
form) — apply this rule only to the former, and say explicitly which kind a feature
turned out to be before automating it.

Original rule text (still correct for the narrower lifecycle-action case, now
subsumed by the broader rule above): any test step that performs publish, unpublish,
set-to-draft, or preview on a content record must perform that action from Object
Authoring, not `Content & Data` — `Content & Data` is not a validated equivalent to
the real editor workflow a Site Content Editor actually uses.

Any existing Page Object/test that currently drives ANY content operation (not just
lifecycle actions) via `Content & Data` navigation should be corrected to go through
Object Authoring instead — this may change previously-observed behavior (including
bugs already filed), so re-verify rather than assume the old result still holds.

### Object Names Come From `cms/Content-Admin-Guide.docx` — Never Guessed, Never Probed First (agreed 2026-09-09)

**`cms/Content-Admin-Guide.docx`** is the team's own Content Admin Guide and is the
**single source of truth for which Object(s) back which page or section**. Before
writing or fixing any Control_Panel test, Page Object, or locator constant, read it
and take the object name from there. Do **not** derive an object name by probing
`/object-authoring`, by pattern-matching an existing sibling feature's slug, or from
a PBI's field tables.

**Why this rule exists (real cost, 2026-09-09):** `ChambersLawAdminPage` was written
against an invented page-level object, `chamber-laws-page`
(`manage-chamber-laws-page`), documented in its own docstring as "CONFIRMED LIVE
2026-09-07 … never guessed". That object does not exist and never did.
`manage-chamber-laws-page` returns **HTTP 404**, and none of the 21 page-level
(`*-page`) objects on the live `/object-authoring` index is Chamber's Law. Every
Control_Panel test for PBI 129394 failed at its first step, twice, before anyone
opened the guide — which states the answer plainly in §26.

**The guide's answers for this feature (§26 + §22):** the Chamber's Law page is backed
by exactly two objects — **`LawEntry`** (one entry per law/reference row: `lawNumber`,
`lawTitle`, `lawDescription`, `externalLinkUrl`, `lawIcon`, `displayOrder`,
`activeStatus`) and **`AboutHeroBanner`** (`pageKey = chamber-laws`, `bannerImage`,
`bannerImageAltText`) for the top banner photo. There is **no** page-level Chamber's
Law object, so `pageTitle` / `introContent` / `contentImage` / references-heading
fields **do not exist on this page** and cannot be authored by an editor.

**Object name → Object Authoring slug** is a mechanical transform: the guide's
CamelCase object name lower-kebabs into the manage URL — `LawEntry` →
`/web/qatar-chamber/manage-law-entry`, `AboutHeroBanner` → `manage-about-hero-banner`,
`AboutQatarChamberPage` → `manage-about-qatar-chamber-page`. Derive the slug this way
from the guide's name; do not invent one.

**Precedence.** On *which object and which fields back a page*, this guide **wins over
everything** — over a PBI's own "Field Level Details (CMS)" table, over a Page Object
docstring's "confirmed live" claim, and over `cms/liferay-context.md`. It sits
alongside `OBJECT-AUTHORING-GUIDE.md`, which remains authoritative on *tool mechanics*
(URLs, buttons, statuses, messages); this one is authoritative on *content model*.
This `standards.md` still owns QA policy. Where a Page Object contradicts the guide,
fix the Page Object.

**When a PBI's AC names fields the guide does not list for that page** — as PBI 129394
does, requiring page-level authoring of Page Title / Intro Content / section headings
that no Chamber's Law object provides — that is a **requirements-vs-implementation
conflict to escalate to the QA Manager and the BA**, not something to satisfy by
inventing an object, retargeting the case to an unrelated field, or editing a page or
fragment (which the *Fragments and Page Layout Are Off-Limits* section forbids
outright). A frequent root cause is a case templated from a sibling page that genuinely
does have a page object (e.g. **§23 `AboutQatarChamberPage`** carries exactly the
`pageTitle` / `pageContent` / `contentImage` / `contentImageAltText` set that PBI
129394's blocked cases ask for) — check for that before assuming a product defect.

### Active Status Is a Precondition for Public-Site Visibility (agreed 2026-09-15)

**Content will not appear/propagate to the public site unless its Active Status is
checked/enabled**, regardless of its workflow state. Any test that edits a field
and then asserts the change is visible on the public-facing page (not just saved in the
CMS) must verify — and set, if not already true — Active Status = True as part of its
setup, before asserting public propagation. A propagation assertion that fails ("edited
value did not appear on the public listing within N seconds") is not automatically a
caching/timing bug or a product defect — check Active Status on the target record
first; it is a common, easy-to-miss root cause.

**Active Status defaults to UNCHECKED on a new entry** (confirmed live 2026-09-28 on
`manage-law-entry`). A test that creates a record, publishes it, and then asserts it
is visible to a visitor will fail unless it ticks Active Status explicitly — and the
failure looks exactly like a propagation bug.

Treat public visibility as **two independent gates**, both of which must hold:

1. the workflow state is `Published` (see "Content Editorial Workflow"), **and**
2. `Active Status` is ticked.

`Published` alone is not sufficient, and neither is Active Status alone. Assert both,
and when a visibility assertion fails, read both before calling it a defect.

### Draft/Unpublish Public-Visibility Checks — Mandatory Logged-Out Context (agreed 2026-09-07)

**Any test that checks what a public visitor sees while CMS content is in ANY
non-public state MUST load that public page in a fresh browser context with NO
logged-in CMS user**. As of 2026-09-28 that means six states, not two: `Draft`,
`Pending Review`, `Rejected`, `Unpublished`, `Archived`, and `Scheduled` before its
time — plus any record whose `Active Status` is unticked, whatever its state. Only
`Published` + Active Status ticked is publicly visible. The rule below was written
when only Draft and Unpublished were known; it applies unchanged to all of them.

**The original wording, still binding:** a test checking visitor-facing behaviour for
Draft, Unpublished, or mid-edit content MUST use a fresh context with no logged-in
CMS user — never the same `page`/session object the test used to
drive the CMS admin side. A test that reads the public page through an
authenticated/CMS session can observe CMS-only preview/editor rendering paths that a
real anonymous visitor never sees, producing a false read on whether the business rule
("Draft/Unpublished content is never visible publicly") actually holds.

This rule was already being applied ad hoc in some tests (e.g. the anon-context pattern
in `cms/tests/home_featured_event/test_home_featured_event_control_panel.py`) but had
never been written down here — it was silently lost/never captured once before (see the
Dev-Environment Navigation Quirks section's own note about `55a5c91` dropping
undocumented conventions). Any test asserting draft/unpublish/preview visibility must
explicitly open a new browser context with no auth state (`new_context(browser,
use_auth_state=False)` per this project's `core/web/browser.py` helper) to load the
public page, not reuse the authenticated `page` fixture.

**Re-verify any existing "confirmed bug" finding that was reached by reading the public
page through the wrong path** (CMS-authenticated session, or via `Content & Data`
instead of `Object Authoring` — see the next section) before treating it as final —
the wrong navigation path can itself produce a false blank-page symptom that looks like
a product defect but is actually a test/navigation artifact.

## Test Data and Destructive Operations

### Destructive Operations Against qcdev — Never Delete by Position or Assumption

Mandatory for any code or agent instruction that calls a `delete_*` / `remove_*`
method against qcdev or any other shared/live environment:

1. **Never delete by position** ("last row", "first row", "newest") on any list
   that can contain real content — **position is not identity**. Resolve the
   target by its known ID / external reference code, or by exact title match
   against a field confirmed live to actually hold the title.
2. **Before any delete runs, verify the target is disposable** — its title/ID
   must match `QCTEST-*` (or an equivalent clearly-fake pattern), or be a record
   the shared-record table marks as safe to mutate under its own test. If a
   delete target cannot be positively confirmed as test-created, **stop and ask
   the user**. Irreversible operations on shared data are never inferred from a
   general "fix it and re-run" instruction.
3. **A QA Manager / orchestrator instruction to "fix the framework and re-run"
   does NOT imply authorization for irreversible deletes on real content.**
   Delegated fix/rerun requests must call this out explicitly (e.g. "confirm
   every delete target by ID before executing it") rather than assuming the
   delegate will infer the caution.

> This rule exists because a real record was permanently destroyed. See
> `docs/qa-decisions-log.md` → *2026-09-03*.

### Fragments and Page Layout Are Off-Limits to Automation — Never Create, Edit, Move or Delete (agreed 2026-09-08)

**Scope note:** the *Destructive Operations* rule above governs **Object entries**
(content records). It says nothing about **fragments** or **page layout**, and that
gap was never explicit until now. This section closes it.

**Rule, absolute and with no exception for "just to reproduce the bug":** automation
on this project — every test, Page Object, helper, and delegated agent — operates
**only on content records via Object Authoring**. It must **never**:

- add, edit, duplicate, reorder, move, hide, or delete a **fragment** on any page;
- add, edit, reorder, or delete a **page**, a page section, or anything in a page's
  layout / Page Editor;
- enter the Page Editor, Fragment Collections, or the Look-and-Feel/Master-Template
  surfaces at all, on `qcdev` or any other shared environment.

**Why this is safe to state absolutely:** the three-layer model in
`cms/liferay-context.md` §2 puts Pages (layout) and Fragments (design blocks) *above*
the content layer, explicitly **"off-limits to editors"** — a fragment is shared
design used by every page that renders it, it has no draft/approved lifecycle to fall
back on, and it is **not exposed via headless REST on this instance**, so there is no
scripted restore path if one is damaged. `.claude/context/active/OBJECT-AUTHORING-GUIDE.md`
makes the same boundary from the tool side: Object Authoring edits content
*"without opening the Control Panel and without touching a page or a fragment."*
If a test's expected result appears to require a layout change, the test case is
wrong for this surface — escalate it to the QA Manager; do not satisfy it by editing
the page.

**If a page section is missing or renders empty, that is a finding, not a repair
job.** Report it with evidence and stop. Do **not** attempt to "put the section
back", re-drop a fragment, or re-edit the page — a well-meant repair on shared
`qcdev` is itself an unauthorized layout change, and it destroys the evidence needed
to diagnose the real cause.

Diagnose in this order before concluding anything:

1. **Check the content layer first** — the entries the section renders may simply be
   Draft, have `activeStatus` off, or have been unpublished. That is by far the
   commonest cause and it is fully reversible.
2. **Check for other actors.** `qcdev` is shared and this project has repeatedly had
   multiple concurrent sessions on it (see the concurrency violation recorded in the
   section above). Another session's page edit is a real and documented possibility.
3. **Only then** report a layout/fragment defect — naming what you checked, and
   stating plainly whether this session's own code could have caused it.

**Precedent (2026-09-07/08, PBI 129367 — Hero Banner):** the Hero Banner section
disappeared from the Home page during a test batch and the question was raised
whether automation had deleted the fragment. Investigation cleared it: all 10 slide
entries were present and the count had *increased*, no `delete_*` call existed
anywhere in the batch's code, the page rendered with 0 console errors, and 6 other
peer sessions were active on the same shared `qcdev`. **The automation never touches
page layout — and this section now says so in writing, so the same question does not
have to be re-investigated from scratch next time.**

### Destructive-Precondition Tests Must Use Disposable Test Data, Never Real Content

If a test case's precondition requires putting qcdev into a state that mutates or
removes real, shared content — permanently deleting a record, unpublishing down
to a count not otherwise reachable, leaving a record in Draft/blank-translation —
that test must be built against a **disposable test record**, never the site's
real shared content. This holds **even when the mutation is technically
reversible**: "reversible in principle" is not the bar.

**How to apply, per case:**

1. Create a clearly-named disposable record via Object Authoring
   (`QCTEST-<tc_id>-<short description>`), scoped to only the fields/state that
   test needs.
2. Run the test's real assertion against that disposable record.
3. Delete or otherwise tear down the disposable record afterward, **every run** —
   teardown is part of the test, not an afterthought.
4. If the CMS genuinely provides no path to create the needed record or state,
   the case stays `@pytest.mark.skip` **with the exact blocking reason**. This
   rule redirects destructive-but-buildable cases to test data; it does not
   invent automation where the CMS cannot support it.
5. Any exception that still requires touching a real shared record needs its own
   explicit, **ID-named** user approval — never inferred from a general "run the
   tests" or "fix and re-run" instruction.

### Named CMS User Roles (agreed 2026-09-06, re-provisioned 2026-09-27)

Restricted-role Control_Panel test cases (e.g. "Login succeeds with the restricted
role" style steps, RBAC/permission-bypass cases) must authenticate as the **specific
named role the case calls for** — never the default `TEST_USER`/`TEST_PASSWORD`
account, which is a super-admin-equivalent login meant only for setup/general
CMS access, not role-scoped permission testing.

**This is no longer only an RBAC concern.** The account also decides which *workflow
path* a save takes — see "Content Editorial Workflow" below. Choosing the login is a
test-design decision on every content lifecycle case, not just permission cases.

Eight accounts were provisioned by the team on 2026-09-27 and replace the three
`*@xyz.com` logins previously listed here, which were locked out (reproduced live:
Liferay's "Authentication failed due to incorrect credentials or account lockout"
for all three). All eight are `active = true`, `passwordReset = false`, and members
of `/qatar-chamber`. Editor and Author were re-confirmed signing in live 2026-09-28.

| Role | Email | userId | `.env` key prefix |
|---|---|---|---|
| `QC Site Content Editor` | `qc.editor.test@qatarchamber.local` | 156488 | `CMS_SITE_CONTENT_EDITOR_` |
| `QC Site Content Author` | `qc.author.test@qatarchamber.local` | 156492 | `CMS_SITE_CONTENT_AUTHOR_` |
| `QC Site Content Contributor` | `qc.contributor.test@qatarchamber.local` | 156496 | `CMS_CONTENT_CONTRIBUTOR_` |
| `QC Form Manager` | `qc.forms.test@qatarchamber.local` | 156500 | `CMS_FORM_MANAGER_` |
| `QC Event Organizer` | `qc.events.test@qatarchamber.local` | 156504 | `CMS_EVENT_ORGANIZER_` |
| `QC SEO Manager` | `qc.seomanager.test@qatarchamber.local` | 156508 | `CMS_SEO_MANAGER_` |
| `QC SEO Editor` | `qc.seoeditor.test@qatarchamber.local` | 156512 | `CMS_SEO_EDITOR_` |
| *(none — site member only)* | `qc.member.test@qatarchamber.local` | 156516 | `CMS_SITE_MEMBER_` |

Each prefix takes an `EMAIL` and a `PASSWORD` key (e.g.
`CMS_SITE_CONTENT_EDITOR_EMAIL` / `CMS_SITE_CONTENT_EDITOR_PASSWORD`).
**The password is not recorded in this file and must never be committed** — it lives
in `.env` only. The three `*@xyz.com` passwords that previously appeared here should
be treated as leaked and are dead anyway.

**The site-member account is not an oversight — it is the negative case.** Without an
account that can sign in and still be refused, an assertion like "this role cannot see
the authoring page" passes for any account that cannot see anything at all, including
a broken login. Permission-denial cases must use it.

**Usage:** in a `cms/` test that needs a specific role, resolve credentials via
`config.settings.cms_role_credentials("Site Content Editor")` and pass the result to
`CmsLoginPage.login(email, password)` — do **not** hard-code any of these emails/
passwords directly in a test or Page Object; always go through
`cms_role_credentials()` so a credential rotation only touches `.env`.

**Which role for which case:** the test case's own title/steps/preconditions name
the role required (e.g. "Verify Content Contributor cannot publish without
approval"). When a case doesn't name one explicitly but is clearly RBAC/permission
scoped, pick the role whose expected privilege level matches the scenario under
test — do not default to `TEST_USER` for a permission-boundary case.

**What each role gets** (from the team's 2026-09-27 role sheet; the Documents & Media
and Submissions columns are the ones that differ most and are easy to assume wrong):

| Role | Authoring pages | Add / edit content | Documents & Media | Submissions |
|---|---|---|---|---|
| Editor | yes | all content objects, plus publish / unpublish / archive / restore | add + folders | no |
| Author | yes | add + view all; edit / delete **own** via Owner | add | no |
| Contributor | yes | same as Author | **view only** — the single difference | no |
| Form Manager | yes | no | view | view + update |
| Event Organizer | yes | no | no | no |
| SEO Manager / Editor | yes | no | no | no |
| Site member (none) | **no** | no | no | no |

## Execution Process Conventions

### No concurrent live-browser agents against the shared qcdev session

**No concurrent live-browser agents against the shared qcdev session.**
Live-browser exploration or mutation work must run **one agent at a time** —
never two or more background agents driving real browsers against it
simultaneously, even with separate Playwright instances.

qcdev's `TEST_USER` session and Liferay's server-side portlet-instance IDs are
shared, **server-scoped** state — not safely concurrent across independent
browser processes, unlike a normal multi-tab local run. This compounds with the
documented ~30 s session-drop behaviour and the dev-mode connection-limit gate.

Sequence live qcdev work explicitly. Parallelism is fine only for work that never
touches a live browser session (reading/writing local files, static analysis).

### No full-batch reruns while fixing

While iterating on a fix for one or a handful of failing tests, run only those
tests by marker or nodeid (`pytest -m tc_135453`, `pytest path::test_name`) —
never the full suite or a whole module. Reserve full-batch runs for final
confirmation once the targeted fix is verified green. A full rerun on every edit
wastes qcdev session budget and produces noisy evidence for a single-test
question.

Use pytest's own re-run filters while iterating:

- `pytest --lf` — reruns only what failed last invocation. Use after a fix
  attempt whose correctness is not yet certain.
- `pytest -x` — stop at the first failure. Use on a small targeted set so later
  tests do not burn session budget after the thing being diagnosed has failed.

### Safe Parallelism — `xdist_group` and `--dist loadgroup`

`pytest.ini`'s `addopts` runs `-n 3 --dist loadgroup`. **`--dist loadgroup` is
required for `@pytest.mark.xdist_group(...)` to have any effect** — without it
the mark is inert and xdist load-balances exactly as before.

**Why loadgroup, not loadscope:** the real constraint is "two tests must never
touch the SAME shared qcdev record concurrently", not "two tests in the same
file/class must never run concurrently". `loadscope` groups by module/class,
which is both coarser than the real constraint and unable to protect a shared
record touched from two different modules. `loadgroup` names the actual
constraint.

**Every test that mutates a shared/singleton record carries the matching
`@pytest.mark.xdist_group(...)`.** Everything else is left ungrouped and
parallelises freely. Current group table and its audit →
`docs/qa-environment-notes.md` § 5.

**A test can only belong to one `xdist_group`.** Before adding a new one, grep
the test body for every shared record ID it touches; if a test genuinely
straddles two, **merge those two groups into one shared group name** rather than
picking one and leaving a race on the other.

**Default posture:** `-n 3 --dist loadgroup`. Reserve `-n 0` for deep debugging
(a single flaky test, or when the connection-limit gate is firing often — try
`-n 1` before adding more gate-tolerance machinery).

### Wait-Strategy Rule

Waits are **condition-based** — wait on the DOM/network signal that actually
marks the state change (`wait_for(state="visible"/"detached")`,
`wait_for_url(...)`), keeping any previous fixed value as an **upper-bound
timeout**, not a mandatory sleep.

A **fixed grace is permitted only** where all three hold: there is no observable
DOM or network signal to wait on, the window was **measured live** (not guessed),
and it is **disclosed in a comment at the call site**. Blind
`wait_for_timeout(...)` with none of these is a defect. Known justified graces →
`docs/qa-decisions-log.md`.

### `pytest.ini` marker registration is generated

The `pbi_*` / `tc_*` marker block in `pytest.ini` is **generated** by
`tools/sync_tc_markers.py` between its BEGIN/END sentinels — **never edit it by
hand.** Add the mark in the test, then run the tool. `--check` runs in the CI
collect gate. Hand-written taxonomy markers (Axis 2/4/5) live above the sentinel
and *are* maintained by hand.

---

## Writing Rules

- **Titles:** action + condition ("Submit Tender EOI with missing Commercial
  Registration Number").
- **Steps:** numbered, one action each, no ambiguity.
- **Expected results:** specific and verifiable — never "works correctly". Not
  "form submits successfully" but "submission is stored with status Pending, and
  an acknowledgement email is sent to the applicant's entered address".
- **Test data:** concrete values, not "valid data" (`Commercial Registration
  Number = 123456`, `Ad Type = Website Banner`).

## Default Scope

- **Surfaces:** default to `Web` for public-facing features; add `Control_Panel`
  for the corresponding admin/CMS management cases of the same feature.
- **Languages:** Arabic (RTL) + English (LTR) unless told otherwise — bilingual
  coverage is core, not optional.
- **Theme + Contrast:** Light/Dark mode and the Normal/High-Contrast toggle are
  BRD-confirmed requirements, **same coverage tier as bilingual** (see
  `background.md`). UI-rendering cases must get real theme/contrast coverage, not
  just a default light/EN pass — apply the **Theme & Contrast Coverage Matrix**
  section above (reconstructed 2026-09-30).

## Do / Don't

- ✅ State assumptions when requirements are incomplete (the BRD itself flags several
  open items — e.g., unspecified browser matrix, unspecified environment names).
- ✅ Ask for acceptance criteria before deep analysis when a description-only PBI is
  too thin (per the org-wide `analyze-pbi` policy).
- ✅ Treat the webform → email → approval pattern as the backbone of most business
  logic in this project — reuse the Webform/Approval Rules checklist every time.
- ✅ Distinguish Chamber Events (internal registration) from Global Events (external
  referral only) — they are not interchangeable.
- ✅ Name the CMS account a content-lifecycle case runs as, in its preconditions —
  the account decides whether a submit lands on Pending Review or goes straight
  live (see Content Editorial Workflow).
- ❌ Don't assert a lifecycle outcome reached through the super-admin `TEST_USER`
  and call it the system's behaviour — that account bypasses the review step.
- ❌ Don't compare a status against "Approved" — the badge reads `PUBLISHED`. Use
  `object_authoring_page.py`'s `STATUS_*` constants, never string literals.
- ❌ Don't apply money/payment-flow edge-case emphasis by default — this project has
  none, unless a specific future feature changes that.
- ❌ Don't invent mobile Platform tags — this BRD is Web + Control_Panel only.
- ❌ Don't merge multiple verifications into one case.
- ❌ Don't include internal-only fields in client deliverables.
- ❌ Don't test enhancements explicitly listed in the BRD's Out-of-Scope sections as
  if they were in-scope defects.
