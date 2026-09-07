# CMS Profile — Qatar Chamber (Liferay DXP)

> Project-specific variables required by `${CLAUDE_PLUGIN_ROOT}/context/cms-testing.md`.
> That file supplies the CMS-testing methodology; this file supplies the values for
> *this* project. Read together, always in this order (cms-testing.md first).
>
> Drafted 2026-08-17 from this project's `.claude/context/active/background.md`,
> `standards.md`, and the team's live architecture discussion the same day. Sections
> marked **UNVERIFIED** or **BLOCKED** are deliberately left incomplete rather than
> guessed — per this project's `senior-web-automation-eng` contract, an agent hitting
> an incomplete field here must stop and report, not invent a value.

---

## CMS Product

- Product: **Liferay DXP**
- Architecture: **Coupled / traditional** — the public site is server-rendered by the
  same application that manages content. Not headless/API-first for the primary
  consumer.
- Instance (dev): `qcdev.ihorizons.com`, groupId `37246`, site "Qatar Chamber"

## Consumers (delivery surfaces)

- **Confirmed**: the public website (server-rendered HTML), bilingual EN/AR.
- **Undecided — needs an explicit team decision, do not assume either way**: is the
  Liferay Headless Delivery API (`/o/headless-delivery/...`) a consumer this project
  tests, because a real client reads it — or is it unused/internal-only? Per
  `cms-testing.md`, every *declared* consumer must be asserted on for every publish.
  Declaring a consumer that doesn't matter wastes effort; missing one that does is a
  real shippable gap. Resolve and update this line before writing any test that could
  plausibly need it.

## Publish / Propagation Latency Budget

**MEASURED** — 2026-08-25, via `tools/propagation_probe.py` against the live
`/o/qc-board/members` JAX-RS endpoint (Board Members data source), manually
triggered publish (admin Save on a Board Member's Short Bio field, unique
`QCTEST-PROBE-*` marker), QA Manager + human tester live session.

- **Observed propagation delay: ~0s (sub-second, first poll after Save already
  showed the new value).** No caching layer or reindex delay detected on this
  endpoint.
- **Budget to use in tests: poll with a 5s timeout, 0.5s interval**, as a safety
  margin over the measured near-instant delivery (network/render variance,
  not a real propagation mechanism) — still poll, never a bare `sleep()`.
- Suspected mechanism: **no intermediate cache** between the Save action and the
  JAX-RS endpoint response — Liferay serves this Object Definition data live,
  not through a CDN/portal-cache layer. Not verified for every endpoint (only
  the Board Members data source was probed) — re-measure per-endpoint if a
  different content type shows different behavior.

**Important scope note for automation**: the public Board of Directors pages
are **client-rendered from this JAX-RS API** (`/o/qc-board/members`), not
server-rendered HTML — confirmed live during this probe (plain `curl` on the
page URL returns only the page shell/title, not member content; the data
only appears via the API). Any propagation assertion for these pages should
poll the rendered DOM after page load (through Playwright, which executes
the client JS), not raw HTML fetch — a raw-HTML propagation check will always
read stale/empty regardless of actual latency.

**Not yet measured**: whether this ~0s figure holds for other content types on
this project (e.g. rich-text CMS pages, other Object Definitions) — this
budget is confirmed for the Board Members data source only. Re-probe before
assuming it generalizes.

## Cache / CDN Behavior

**UNVERIFIED** — same status as above. Record once confirmed: is there a CDN in front
of `qcdev`? Liferay portal-level cache? Both? This determines whether a
"cache-buster or preview token" bypass (`cms-testing.md` §6.8) is even meaningful here.

## Roles

Source: `.claude/context/active/background.md` → *User Roles*.

| Role | Notes |
|---|---|
| Public Visitor | Unauthenticated |
| Site Content Author | Create/edit own content, submit for review; no direct publish (a few named exceptions) |
| Site Content Editor | Full content lifecycle: create, edit, preview, publish, unpublish, delete |
| Form Manager | Manages webform submissions; layered with Editor/Author on form-heavy features |
| QC Admin Reviewer | Approves/rejects specific submission types (Advertisement, Business Opportunity) |
| Administrator | Full system control: users, roles, integrations, lookup data, audit logs |

**Test accounts by role** — fill in as provisioned; do not leave a row blank once a
test needs it:

| Role needed for | `.env` keys | Status |
|---|---|---|
| Administrator / general authoring | `TEST_USER` / `TEST_PASSWORD` | Exists (used by `tools/save_auth.py`) — **exact role mapping unconfirmed**, do not assume it has every permission |
| Restricted — no Header Management permission | `TEST_USER_RESTRICTED` / `TEST_PASSWORD_RESTRICTED` | **BLOCKED — account does not exist yet** (see ADO TC-134658) |

## Locales

`en_US` (LTR, default), `ar_SA` (RTL) — path-prefixed (`/ar`). See
`config/settings.py`'s `web_url(locale="ar")` / `ARABIC_PATH_PREFIX`.

## Delivery Endpoints

- Web: `WEB_BASE_URL` (`.env`)
- Control Panel: `CONTROL_PANEL_URL` (`.env`)
- Headless Delivery API: not currently declared as a consumer — see *Consumers* above.

## Test-Data Policy

Ownership model agreed with the QA Lead, 2026-08-17:

- **DISPOSABLE** — test creates a `QCTEST-`-prefixed row; cleanup = delete. Default
  for nearly all cases.
- **TEST_OWNED** — a dedicated QA-only row; reset to a **fixed, known baseline value**
  rather than "restore whatever it was before" — reading current UI state reliably to
  snapshot it before mutating is the fragile part without an API read.
- **SNAPSHOT_RESTORE** — touching real editorial content. **Prohibited in automation**
  outside an explicit, documented exception. DB-level recovery is an emergency
  procedure, never a normal test step.

### ⚠️ Open conflict — flagged here on purpose, not silently resolved

This project's team decided (2026-08-17) on **zero API calls anywhere in CMS
automation, including fixture setup/teardown** — UI-only end to end.

This directly contradicts `cms-testing.md` §6.1: *"Seed via API, verify via the
surface... never drive the authoring UI to set up state for a test whose subject is
delivery... the largest stability and token win available in CMS automation."*

Until the team resolves this explicitly:
- Every fixture create/delete goes through the Control Panel UI, not REST.
- Cleanup verification also goes through the UI (re-check the Admin listing shows
  zero matches) — there is no API read available to confirm state independently.
- This means "no programmatic way to delete created content" is a live condition —
  `cms-testing.md` §9 lists that as an **escalate, don't route around** trigger. Record
  the team's final position here once decided; do not leave this contradiction
  standing indefinitely while agents keep re-discovering it per test.

**Namespace prefix**: `QCTEST-` (carried over from the earlier REST-based framework's
convention — confirm it's still the agreed prefix now that fixture creation happens
through a UI form rather than a JSON payload).

## Teardown Path

UI-only per the current team decision above: Admin listing → search by prefix →
delete → re-open the listing and confirm zero matches. No API-based teardown under
current policy.

---

## Change log

- 2026-08-17 — Initial draft, based on `background.md`/`standards.md` plus the team's
  UI-only decision and the TC-134658 blocker investigation. Propagation latency and
  cache/CDN behavior still unmeasured; Headless Delivery API consumer status still
  undecided; UI-only vs API-seeding conflict still unresolved.
