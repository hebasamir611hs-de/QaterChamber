"""
UPDATE 2026-10-13 (P3/P4 batch -- user decision, read this first): with
QC_ALLOW_LIVE_SINGLETON_WRITES=1 the write guard below OPENS for this
module's real singleton (cms/tests/live_write_guard.py): tests write test
data to it, never delete anything, log every persisted write to
reports/live-writes-20261013.jsonl, and leave the record Published. Without
the variable nothing changes (NOT APPLICABLE). Only this batch's test cases
open it (live_write_guard.P34_BATCH_TCS); P1/P2 tests stay NOT APPLICABLE.
P1/P2 RERUN 2026-10-13 (user decision, supersedes that last clause): the
rerun ids (live_write_guard.P12_BATCH_TCS) open it too, plus the real About
Hero Banner rows; their writes are logged first, nothing is deleted (QCTEST
rows are kept and logged), and a record left Unpublished / Draft / Pending
Review is re-published in `finally` (cms/tests/live_end_published.py).
The P3/P4 cases are scripted OFFLINE, not yet executed -- search for
"P3/P4 BATCH".

cms/tests/chambers_law/test_chambers_law_control_panel.py --
Control_Panel-tagged cases for PBI 129394 (QC-ABOUT-003 -- Chamber's
Law), sourced from review_test_coverage(129394) (111 Control_Panel-tagged
cases, IDs 134850-134987).

═══════════════════════════════════════════════════════════════════════
THIS FEATURE IS BACKED BY **TWO** OBJECT AUTHORING OBJECTS
  1. **Chamber Laws Page** -- `manage-chamber-laws-page`, a SINGLETON whose
     one record is `QCDEMO-129394-CHAMBER_LAWS_PAGE-ENTRY`. Owns the
     PAGE-level content: Page Title, Intro Heading, Intro Content,
     **Content Image**, Content Image Alt Text, References Heading.
  2. **Law Entry** -- `manage-law-entry`, one record per CARD in the
     Official Legal References section: Law Number, Law Title, Law
     Description, External Link URL, **Law Icon**, Display Order, Active
     Status.

`Content Image` (page) and `Law Icon` (card) are two DIFFERENT images in
two DIFFERENT objects. A case about "the Content Image" belongs on the
Page record; a case about a card belongs on a Law Entry.
═══════════════════════════════════════════════════════════════════════

⚠ CORRECTION OF A FALSE, DATED "LIVE-VERIFIED FACT" (removed 2026-09-15).
From 2026-09-09 to 2026-09-15 this module's header asserted as verified
fact that "there is NO page-level Chamber's Law object", that
`manage-chamber-laws-page` returned HTTP 404, and that Page Title / Intro
Section Heading / Legal References Section Heading were unauthorable static
fragment content -- and on that basis 134871/134873/134874/134875/134882
were retargeted onto Law Entry and 134883 onto `Law Icon`.

**All of that was wrong.** Re-verified live 2026-09-15 (authenticated
headless Chromium against qcdev, `.auth/state.json`, a disclosed scoped CLI
Playwright probe -- never the Playwright MCP):
  - `/object-authoring` returns 200 and links "Chamber Laws Page" ->
    `/web/qatar-chamber/manage-chamber-laws-page`.
  - That page returns **HTTP 200**, title "Manage: Chamber Laws Page", and
    lists ONE record, `QCDEMO-129394-CHAMBER_LAWS_PAGE-ENTRY`, status
    APPROVED / ON THE WEBSITE.
  - Its live field accessible names (uniqueness count 1 for each):
    'Page Title' / 'Page Title — العربية *', 'Intro Heading' /
    'Intro Heading — العربية *', 'Intro Content' (rich text) /
    'Intro Content — العربية', 'Content Image' (Select File + Preview ·
    Download + Remove file), 'Content Image Alt Text' /
    'Content Image Alt Text — العربية *', 'References Heading' /
    'References Heading — العربية *'.
  - The CMS values match the anonymous public render character-for-
    character (`Chamber’s Law--1` -> `<h1>`; `Chamber Legal Framework
    Framework` -> intro `<h2>`; `Official Official Legal References` ->
    references `<h2>`), and the public intro image's own `src` carries
    `objectEntryExternalReferenceCode=QCDEMO-129394-CHAMBER_LAWS_PAGE-ENTRY`
    -- the delivered image names this record as its owner.

So the "DISCLOSED COVERAGE GAP" that claimed the page headings are
unauthorable, and the "RETARGETED ... after the previous target was proven
not to exist" rationale on 134871, were both false and are deleted rather
than softened. See `cms/pages/chambers_law/chambers_law_admin_page.py`'s
module docstring for the full evidence and for why the
`cms/Content-Admin-Guide.docx` §26 reading that produced the claim was an
argument from silence.

**Six cases are retargeted BACK onto the page record by this batch**:
134871 (publish the page -> page-level content becomes visible), 134873
(unpublish the page -> it stops being served), 134874 (draft page content
is CMS-only), 134875 (Preview renders unpublished page content), 134882
(first-time **Content Image** upload), 134883 (**Content Image** replace).
Six stay on Law Entry because they genuinely belong there: 134877 (a law
card's External Link URL), 134884 (create a law entry), 134885 (edit a law
entry), 134886 (reorder law entries), 134887/134888 (deactivate /
reactivate a law entry).

── Required-field asterisks are part of the accessible name ─────────────
On BOTH objects the ENGLISH half of each bilingual pair is NOT required
(no asterisk) while the ARABIC half IS (` *`). `ARABIC_SUFFIX` therefore
stays asterisk-free and the tolerance lives in the lookup:
`ObjectAuthoringPage.label_pattern()` matches an anchored label with an
OPTIONAL trailing ` *`. This is what previously made 134884 fail with
`actual 'Law Number — العربية *'` vs `lookup 'Law Number — العربية'` -> 0
matches.

── Entry-column identity differs PER OBJECT ─────────────────────────────
Chamber Laws Page renders the entry CODE in its Entry column (use the
`*_by_code` lookups); Law Entry renders the real Law TITLE (use the
title-keyed lookups). Its STATUS cell also reads "APPROVEDON THE WEBSITE"
rather than a bare badge -- handled once in
`ObjectAuthoringPage._normalize_status_label()`.

── Measured lifecycle timings (live, 3/3 iterations, 2026-09-15) ────────
  Unpublish button visible                    0.02-0.05 s
  status -> `Draft` after Unpublish           1.20-1.38 s
  status -> `Approved` after Submit           **27-30 s**
Unpublish is fast and reliable; PUBLISHING IS SLOW. Every wait budget
gated behind a publish is sized from these numbers -- see the timeout
constants below. The old blanket 20 s `_reflects_public` budget was far
too tight for anything behind a publish and is no longer used for those.

── TEST_OWNED restore is now CHECKED, not assumed ───────────────────────
A `finally` block that fires a restore action and returns cannot know the
restore committed -- and when it does not, a shared real record is left
broken and the NEXT tests fail on preconditions instead of on their own
behaviour (observed: `QCDEMO-129394-law-11-1996` left in Draft removed its
card from the live page and broke 134883/134886/134887 with
`ValueError: 'Law No. 11 of 1996' is not in list` and "precondition
failed: the 1996 card is not currently visible publicly"). Every mutating
test below now restores through `_test_owned_reset()`, which retries, then
RE-READS the record from a fresh navigation to prove the restore landed,
and shouts (Allure attachment + a raised error when the test body itself
passed) instead of silently leaving a broken record behind.

Baselines are always captured at runtime and restored to, never to a
literal: the live data is already polluted by earlier runs (`Page Title` is
`Chamber’s Law--1`, `Intro Heading` is `Chamber Legal Framework Framework`,
`References Heading` is `Official Official Legal References`, and the 1990
law entry's External Link URL and Display Order are still carrying values
a previous failed run left behind).

── Parallel safety ──────────────────────────────────────────────────────
ALL twelve mutating tests share `@CHAMBERS_LAW_XDIST_GROUP`. Six of them
(134883-134888) previously did not, so under `-n 3` they ran concurrently
against the same shared records: two identical parallel runs produced
different results (9 failed/3 passed, then 7/5), while 134886 and 134887
both PASSED when run in isolation after the shared state was repaired.
Any test in this module that touches a shared record MUST carry the
decorator.

── Former skip stubs -- status 2026-10-12 ───────────────────────────────
  - IMPLEMENTED (P1/P2, user scope 2026-10-12): 134853, 134867-134870
    (real role accounts via cms_role_credentials(), fresh contexts),
    134876 (Editor publish + anonymous cache check + Control Panel Audit
    portlet), 134889/890/893/894, 134897-134902 (hero banner: the About Hero
    Banner create form is hidden, so no disposable row can exist; the user
    approved writes to the REAL row QCDEMO-ABOUT-HERO-chamber-laws for 134897
    and 134899-134902 -- snapshotted before the module, restored at its end),
    134905/906/909/910, 134913/914/917/918,
    134921/922/925/926, 134929-134934.
  - IMPLEMENTED 2026-10-14: 134850 / 134851, the Control_Panel half of
    the two heading cases (read the page record first; write + publish only
    when the stored heading differs; public check in a fresh logged-out
    context). Their Web half stays in test_chambers_law_web.py under the
    same tc_ markers.
  - DEFERRED by user decision 2026-10-12 (P3, left as skip stubs for now):
    134891/892/895/896, 134903/904, 134907/908, 134911/912,
    134915/916, 134919/920, 134923/924, 134927/928, 134935-134939.
    Their shape helpers (_case_char_limit, _case_rich_no_limit, ...) are
    already in place below.
  - RESTORE MODEL (user decision 2026-10-12): the new tests do NOT restore
    the page record per test; `_chamber_laws_page_restored_once` restored it
    from reports/backups/chamber_laws_page_20261012/ at module end (CLI:
    tools/restore_chamber_laws_page.py). The twelve older lifecycle tests
    above keep their own TEST_OWNED restores.

── SINGLETON WRITES -- NOT APPLICABLE (user decision 2026-10-13) ────────
Automation no longer writes to the real Chamber Laws Page singleton
QCDEMO-129394-CHAMBER_LAWS_PAGE-ENTRY, nor to the real About Hero Banner row
QCDEMO-ABOUT-HERO-chamber-laws (one row per page, its create form is hidden,
so no disposable row can exist). Every case that needs a saved / published /
unpublished change on either record calls
`cms.tests.live_write_guard.block_live_singleton_write()` immediately before
its first persisting step and is reported NOT APPLICABLE. Refusal cases still
run and stop at once (`stop_unless_refused()`) if the refusal is not seen.
The module-start hero snapshot and module-end page/hero restore are no
longer wired (their code stays in cms/pages/chambers_law/page_record_backup.py);
the module-end fixture now only sweeps this run's QCTEST law entries and
resets the account language. Law Entry tests are untouched (multi-record
object; QCTEST rows deleted by exact title). FOLLOW-UP 2026-10-13: 134877
and 134885-134888 no longer touch the real QCDEMO-129394-law-11-1990/-1996
rows either -- each creates, asserts on and deletes its own disposable
`QCTEST-<tc>-LAW-<uid>` row. Older notes above about restores
and approved writes to the hero row are history.
"""

import sys

import allure
import pytest

from cms.pages.chambers_law.chambers_law_admin_page import (
    ChambersLawAdminPage,
    CHAMBERS_LAW_PAGE_ENTRY_CODE,
    LAW_1990_TITLE,  # read-only list check in 134884; no test writes the real 1990/1996 rows
)
from web.pages.chambers_law.chambers_law_page import ChambersLawPage
from core.web.browser import new_context
from core.utils.logger import get_logger
from core.utils.waits import wait_until
from cms.pages.components.object_authoring_page import (
    STATUS_DRAFT,
    STATUS_INACTIVE,
    STATUS_PUBLISHED,
    STATUS_UNPUBLISHED,
    ObjectAuthoringPage as _ListPage,
)
from cms.tests.live_end_published import leave_published
from cms.tests.singleton_baseline import drive_to_published
from cms.tests.live_write_guard import (
    LiveRecord,
    block_live_singleton_write,
    deletes_suppressed,
    gate_opened,
    keep_instead_of_delete,
    log_live_write,
    stop_unless_refused,
)

logger = get_logger("test_chambers_law_control_panel")

# All twelve mutating tests below write to one of TWO shared, real Object
# Authoring records (the Chamber Laws Page singleton, and the Law Entry
# list's 1990/1996 entries) -- one shared group so xdist (--dist loadgroup)
# never schedules two of them on different workers concurrently, mirroring
# this project's established convention (see e.g. web/tests/
# about_chairman_message/test_chairman_message_control_panel.py's
# xdist_group("chairman_message_78261")).
CHAMBERS_LAW_XDIST_GROUP = pytest.mark.xdist_group("chambers_law_129394")
# Record descriptions for the NOT APPLICABLE guard (user decision 2026-10-13).
PAGE_RECORD = "Chamber Laws Page QCDEMO-129394-CHAMBER_LAWS_PAGE-ENTRY"
HERO_RECORD = "About Hero Banner row QCDEMO-ABOUT-HERO-chamber-laws (create form hidden)"

# ---- Wait budgets, sized from live measurements (see module docstring) ----
# Unpublish commits in ~1.2-1.4s; a generous ceiling still fails fast.
UNPUBLISH_CONFIRM_TIMEOUT = 30.0
# Publish commits in 27-30s measured 3/3. 120s leaves real headroom for a
# slow qcdev without ever turning a genuine non-commit into a pass.
PUBLISH_CONFIRM_TIMEOUT = 120.0
# Public-surface reflection AFTER a change that is already committed in the
# CMS (unpublish, activeStatus flip, a draft save).
PUBLIC_REFLECT_TIMEOUT = 45.0
# Public-surface reflection gated BEHIND a publish -- the publish latency
# itself (up to ~30s) plus the delivery-cache refresh on top of it.
PUBLIC_REFLECT_AFTER_PUBLISH_TIMEOUT = 180.0
# How many times a TEST_OWNED restore is retried before it is declared
# failed. Restores are idempotent, so a retry is always safe.
RESTORE_ATTEMPTS = 3


def _reflects_public(
    check_fn,
    timeout: float = PUBLIC_REFLECT_TIMEOUT,
    poll: float = 2.0,
    message: str = "",
) -> None:
    """Polls `check_fn()` (which itself reloads the public page) until it
    returns True or `timeout` elapses -- the "wait for the standard cache
    refresh" step several cases call for, as a real condition-based wait
    (never `sleep()`). The default budget is for changes ALREADY committed
    in the CMS; pass PUBLIC_REFLECT_AFTER_PUBLISH_TIMEOUT for anything
    gated behind a Submit for Publishing (measured 27-30s on its own)."""
    wait_until(check_fn, timeout=timeout, poll=poll, message=message)


def _normalize_rich_text(text: str) -> str:
    """RETAINED, currently uncalled: no test in this module writes the page
    record's `Intro Content` rich text any more (tc_134874/tc_134875 use the
    plain-textbox `Intro Heading` instead, and cite this helper as the
    reason -- see their own comment blocks). Kept because it records a real
    live-confirmed behaviour any future Intro Content case must handle;
    delete it only together with that disclosure.

    REAL, LIVE-CONFIRMED FIX (2026-09-07): `ObjectAuthoringPage.
    fill_rich_text()` -> `BasePage.fill_iframe_editor()` types the given
    string via real keyboard events, where EVERY literal "\\n" character
    sends an Enter keypress (confirmed live: typing `PARA1 + "\\n" + PARA2`
    round-trips back through `rich_text_value()` as `PARA1 + "\\n\\n" +
    PARA2` -- CKEditor renders two adjacent `<p>` elements as
    "\\n\\n"-separated when read via `.inner_text()`). Feeding a
    PREVIOUSLY-READ value (already containing "\\n\\n" per paragraph break)
    straight back into `fill_rich_text()` therefore DOUBLES each paragraph
    break into an extra blank `<p>` every write/read/write cycle --
    reproduced live against `manage-chamber-laws-page`'s Intro Content
    field (each Save-as-Draft/Submit-for-Publishing round trip visibly
    inflated the gap between its two paragraphs). Collapsing every run of
    2+ newlines down to exactly one before re-typing keeps a baseline
    capture -> mutate -> restore cycle byte-for-byte stable instead of
    drifting the real record's content on every test run. Callers building
    a "baseline + appended marker" string must normalize the BASELINE half
    (already round-tripped through `rich_text_value()`) before concatenating
    a literal "\\n\\n" separator for the new paragraph."""
    import re

    return re.sub(r"\n{2,}", "\n", text)


def _same_target_url(actual: str, expected: str) -> bool:
    """URL comparison on a NORMALIZED basis: scheme + host + path plus the
    SIGNIFICANT query parameters, ignoring `language` and empty-valued
    params.

    REAL, LIVE-CONFIRMED PRODUCT BEHAVIOUR (2026-09-15, TC 134877) -- the
    product is FINE and the old exact-equality assertion could never have
    passed. The CMS stores the External Link URL verbatim:

        https://www.almeezan.qa/LawView.aspx?opt&LawID=2541

    and that URL does reach the intended public page. The front end
    re-serializes it when it renders the card's href:

        https://www.almeezan.qa/LawView.aspx?opt=&LawID=2541&language=en

    -- the bare, valueless `opt` becomes `opt=`, and a `language=<locale>`
    parameter is appended by the site's own locale handling. Both are
    normalizations of the SAME destination, so `actual == expected` is
    unsatisfiable by construction while the behaviour under test is
    correct. (The CMS-side read-back is still compared verbatim elsewhere
    in that test -- this tolerance applies only to the rendered public
    href.) Dropping empty-valued params also makes the comparison
    symmetric: `opt` and `opt=` both normalize away."""
    from urllib.parse import parse_qsl, urlsplit

    ignored = {"language"}

    def _key(url: str):
        parts = urlsplit((url or "").strip())
        significant = {
            name: value
            for name, value in parse_qsl(parts.query, keep_blank_values=True)
            if value != "" and name.lower() not in ignored
        }
        return (
            parts.scheme.lower(),
            parts.netloc.lower(),
            parts.path.rstrip("/"),
            significant,
        )

    return _key(actual) == _key(expected)


# ---------------------------------------------------------------------------
# Lifecycle helpers -- every state transition below is CONFIRMED, never
# assumed. See the module docstring's measured timings for why.
# ---------------------------------------------------------------------------
def _record_of(authoring):
    """The record an ObjectAuthoringPage is on, for the live-write log
    (user decision 2026-10-13: every persisted write is logged first)."""
    slug = getattr(authoring, "slug", "") or "?"
    code = getattr(authoring, "_entry_code", None) or ""
    if slug == "chamber-laws-page":
        return PAGE_RECORD
    if slug == "about-hero-banner":
        return HERO_RECORD
    return LiveRecord(slug, code or "<entry opened by title>", f"{slug} {code}".strip())


def _law_record(title: str) -> LiveRecord:
    """A disposable QCTEST Law Entry, named by its exact title."""
    return LiveRecord("law-entry", title, "disposable QCTEST Law Entry")


# Live 2026-10-13: a record PUBLISHED with Active Status unticked reads
# `Inactive` (badge INACTIVE, banner "(Inactive)") -- workflow-published,
# hidden by the second gate. Both count as "the publish landed".
_PUBLISHED_STATES = (STATUS_PUBLISHED, STATUS_INACTIVE)


def _list_key(authoring) -> str:
    """The text the record's entries-list row is found by: the Chamber Laws
    Page row renders its entry CODE, a Law Entry row its (EN) Law Title."""
    if authoring.slug == "law-entry":
        return authoring.field_value(ChambersLawAdminPage.LAW_TITLE_LABEL)
    return authoring._entry_code or ""


def _unpublish_and_confirm(authoring):
    """Takes the record off the live site and PROVES it landed in
    UNPUBLISHED (FIX 2026-10-13: Unpublish lands on `Unpublished`, its own
    state -- the old wait for "Draft" timed out on every run). Idempotent: a
    record already Draft / Unpublished is left alone. Logged first."""
    if authoring.current_status() in (STATUS_DRAFT, STATUS_UNPUBLISHED):
        return authoring
    log_live_write(_record_of(authoring), "<workflow>", STATUS_UNPUBLISHED, None, action="unpublish",
                   note="the form's Unpublish (lands on Unpublished)")
    authoring.unpublish_to_edit_as_draft()
    authoring.wait_for_status(STATUS_UNPUBLISHED, timeout=UNPUBLISH_CONFIRM_TIMEOUT)
    return authoring


def _publish_and_confirm(authoring):
    """Puts the form's current values live and PROVES the record is
    published on a fresh read (FIX 2026-10-13, read live):

      * Published / Inactive / Draft -- the form's value=0 control
        (`Publish` for this account) saves and publishes in one click;
      * Unpublished -- that control reads `Save Changes` and KEEPS the record
        Unpublished, so it saves the edits, then the row action
        `[data-qc-oel-publish]` (confirm/prompt chain accepted) publishes,
        verified on a fresh entries-list read (singleton_baseline
        .drive_to_published -- the GM/Chairman fix).

    Every persisting click is logged first."""
    status = authoring.current_status()
    record = _record_of(authoring)
    if status == STATUS_UNPUBLISHED:
        key = _list_key(authoring)
        log_live_write(record, "<form submit>", STATUS_UNPUBLISHED, None, action="save",
                       note="Save Changes (value=0) on the Unpublished record -- stores the edits")
        authoring.submit_via(ChambersLawAdminPage.PUBLISH_SUBMIT)
        log_live_write(record, "<workflow>", STATUS_PUBLISHED, None, action="publish",
                       note="row action [data-qc-oel-publish] from Unpublished (verified on a fresh list read)")
        drive_to_published(
            lambda: _ListPage(authoring.page, slug=authoring.slug).open_entries_list(locale="en"),
            key,
            lambda: authoring.reopen().submit_via(ChambersLawAdminPage.PUBLISH_SUBMIT),
            budget=PUBLISH_CONFIRM_TIMEOUT,
        )
    else:
        log_live_write(record, "<form submit>", STATUS_PUBLISHED, None, action="publish",
                       note=f"the form's Publish (value=0) from {status!r}")
        authoring.submit_via(ChambersLawAdminPage.PUBLISH_SUBMIT)
    wait_until(lambda: authoring.reopen().current_status() in _PUBLISHED_STATES,
               timeout=PUBLISH_CONFIRM_TIMEOUT, poll=3.0,
               message=f"{authoring._entry_code!r} on manage-{authoring.slug} never read "
                       f"Published/Inactive after the publish")
    return authoring


def _save_draft_and_confirm(authoring):
    """Saves a draft and PROVES the record is in Draft afterwards (read live
    2026-10-13: Save as Draft on an Unpublished record lands on Draft).
    Logged first."""
    log_live_write(_record_of(authoring), "<form submit>", STATUS_DRAFT, None, action="save-draft",
                   note="Save as Draft (the form's current values)")
    authoring.save_as_draft()
    authoring.wait_for_status(STATUS_DRAFT, timeout=UNPUBLISH_CONFIRM_TIMEOUT)
    return authoring


def _put_back_content_image(admin, tmp_dir, tc: str) -> None:
    """`finally`: the REAL page's Content Image back to its own picture
    (PAGE_BACKUP_IMAGE, byte-identical to the image read live 2026-10-13),
    uploaded as `chamber-laws-content.png` and published IN PLACE, then
    verified on a fresh read. Logged first; runs only when this test's write
    gate opened; nothing is deleted."""
    if not gate_opened(PAGE_RECORD):
        return
    authoring = admin.open_page_record()
    if authoring.current_file_name(admin.CONTENT_IMAGE_UPLOAD_LABEL).startswith("chamber-laws-content"):
        return
    original = _Path(tmp_dir) / "chamber-laws-content.png"
    original.write_bytes(PAGE_BACKUP_IMAGE.read_bytes())
    authoring.upload_file(admin.CONTENT_IMAGE_UPLOAD_LABEL, str(original))
    log_live_write(PAGE_RECORD, "Content Image", original.name, tc, action="upload",
                   note="finally: the page's own picture back (PAGE_BACKUP_IMAGE)")
    _publish_and_confirm(authoring)
    stored = admin.open_page_record().current_file_name(admin.CONTENT_IMAGE_UPLOAD_LABEL)
    if not stored.startswith("chamber-laws-content"):
        raise AssertionError(f"tc_{tc}: Content Image reads {stored!r} after the put-back")


def _put_back_intro_heading(admin, baseline_heading, tc: str) -> None:
    """`finally`, BEFORE the re-publish: the draft-only marker a case typed
    into the REAL page's Intro Heading is written back to the value captured
    at the start, so the re-publish does not put test text on the public
    page. Saved as a draft (the record is Draft / Unpublished here), logged
    first; nothing is deleted. Runs only when this test's write gate opened."""
    if baseline_heading is None or not gate_opened(PAGE_RECORD):
        return
    authoring = admin.open_page_record()
    if authoring.field_value(admin.INTRO_HEADING_LABEL) == baseline_heading:
        return
    if authoring.current_status() in _PUBLISHED_STATES:
        raise AssertionError(
            f"tc_{tc}: the page is already Published with a changed Intro Heading -- put "
            f"{baseline_heading!r} back by hand")
    authoring.fill_text(admin.INTRO_HEADING_LABEL, baseline_heading)
    log_live_write(PAGE_RECORD, "Intro Heading", baseline_heading, tc, action="save-draft",
                   note="finally: write the captured Intro Heading back before the re-publish")
    authoring.save_as_draft()
    stored = admin.open_page_record().field_value(admin.INTRO_HEADING_LABEL)
    if stored != baseline_heading:
        raise AssertionError(f"tc_{tc}: Intro Heading reads {stored!r} after the put-back, "
                             f"expected {baseline_heading!r}")


def _page_end_published(admin, tc: str):
    """P1/P2 RERUN 2026-10-13 (user decision): `finally` -- the Chamber Laws
    Page singleton back to Published when this test's write gate opened
    (Unpublished -> row action `[data-qc-oel-publish]`; Draft -> Submit for
    Review; verified on a fresh list read; logged first)."""
    return leave_published(PAGE_RECORD, lambda: admin.open_page_entries_list(),
                           CHAMBERS_LAW_PAGE_ENTRY_CODE,
                           lambda: admin.open_page_record().submit_via(admin.PUBLISH_SUBMIT), tc)


def _hero_end_published(admin, tc: str):
    """Same for the real `chamber-laws` About Hero Banner row. The hero
    list's Entry column renders the Page Key, so the row is addressed by
    `chamber-laws` (the only row whose text carries it)."""
    from cms.pages.components.object_authoring_page import ObjectAuthoringPage as _OAP

    return leave_published(HERO_RECORD,
                           lambda: _OAP(admin.page, slug="about-hero-banner").open_entries_list(locale="en"),
                           "chamber-laws",
                           lambda: _open_real_hero(admin).submit_for_review(), tc)


def _restore_record(open_record, baseline_status, apply_fields=None, verify=None):
    """One idempotent TEST_OWNED restore pass, then a VERIFIED re-read.

    `open_record()` returns a freshly opened `ObjectAuthoringPage` for the
    record. `apply_fields(authoring)` (optional) writes the captured
    baseline field values back; it is called with the record already
    unpublished, because `Save as Draft` is disabled while a record is
    Approved (Object Authoring guide §4). `verify(authoring)` (optional)
    asserts the field values really came back.

    Raises on any mismatch -- `_test_owned_reset()` below is what decides
    whether that raise is retried, reported, or re-raised."""
    authoring = open_record()

    if apply_fields is not None:
        _unpublish_and_confirm(authoring)
        apply_fields(authoring)
        if baseline_status == STATUS_PUBLISHED:
            _publish_and_confirm(authoring)
        else:
            _save_draft_and_confirm(authoring)
    else:
        # Status-only restore.
        if baseline_status == STATUS_PUBLISHED and authoring.current_status() != STATUS_PUBLISHED:
            _publish_and_confirm(authoring)
        elif baseline_status == "Draft" and authoring.current_status() == STATUS_PUBLISHED:
            _unpublish_and_confirm(authoring)

    # PROVE it committed -- re-read from a fresh navigation, never assume.
    authoring = open_record()
    actual_status = authoring.current_status()
    if actual_status != baseline_status:
        raise AssertionError(
            f"TEST_OWNED restore did not commit: record status is "
            f"{actual_status!r}, expected the captured baseline "
            f"{baseline_status!r}"
        )
    if verify is not None:
        verify(authoring)


def _test_owned_reset(restore_fn, label: str, attempts: int = RESTORE_ATTEMPTS) -> None:
    """Runs a TEST_OWNED restore so that it cannot fail silently.

    Called from a `finally` block. It retries `restore_fn` (restores are
    idempotent, so retrying is always safe), and on total failure it
    attaches the full error trail to Allure and logs it. It then re-raises
    ONLY when no exception is already propagating -- i.e. when the test
    body itself passed. That keeps two rules true at once:
      - a restore failure never MASKS a real product failure, and
      - a green test can never quietly leave a shared record broken for
        the tests that run after it (the exact cascade that turned one
        failure into three bogus precondition failures)."""
    propagating = sys.exc_info()[0] is not None
    errors = []
    for attempt in range(1, attempts + 1):
        try:
            restore_fn()
            if errors:
                logger.warning(
                    "TEST_OWNED reset %r succeeded on attempt %d after: %s",
                    label, attempt, " | ".join(errors),
                )
            return
        except Exception as exc:  # noqa: BLE001 -- retried, then reported loudly
            errors.append(f"attempt {attempt}: {exc!r}")

    detail = (
        f"TEST_OWNED RESET FAILED for {label} after {attempts} attempts.\n"
        "The shared qcdev record may be left in a non-baseline state, which "
        "will break the PRECONDITIONS of other tests in this module.\n"
        + "\n".join(errors)
    )
    logger.error(detail)
    try:
        allure.attach(detail, name=f"TEST_OWNED RESET FAILED - {label}")
    except Exception:  # noqa: BLE001 -- reporting must never mask anything
        pass
    if not propagating:
        raise AssertionError(detail)


# ---- Restore verifiers -- "the restore committed" must be OBSERVED -------
def _assert_field_restored(authoring, field_label: str, expected: str) -> None:
    actual = authoring.field_value(field_label)
    if actual != expected:
        raise AssertionError(
            f"TEST_OWNED restore did not commit: {field_label!r} reads "
            f"{actual!r}, expected the captured baseline {expected!r}"
        )


def _assert_number_restored(authoring, field_label: str, expected: str) -> None:
    actual = authoring.spinbutton_value(field_label)
    if (actual or "").strip() != (expected or "").strip():
        raise AssertionError(
            f"TEST_OWNED restore did not commit: {field_label!r} reads "
            f"{actual!r}, expected the captured baseline {expected!r}"
        )


def _assert_checkbox_restored(authoring, field_label: str, expected: bool) -> None:
    actual = authoring.is_checked(field_label)
    if actual is not expected:
        raise AssertionError(
            f"TEST_OWNED restore did not commit: {field_label!r} reads "
            f"{actual!r}, expected the captured baseline {expected!r}"
        )


def _restore_content_image(
    admin, baseline_status, download_path, original_filename
) -> None:
    """Byte-for-byte restore of the Chamber Laws Page record's Content
    Image, then a VERIFIED re-read.

    `download_path` holds the original file's real bytes, captured off the
    record's own Download link before anything was mutated (None when the
    field was already empty, in which case only the status is restored).

    A DIRECT `upload_file()` over whatever the field currently holds is the
    correct path here -- confirmed live (see
    `ObjectAuthoringPage.remove_current_file()`'s docstring): the
    two-phase remove+save dance is only needed to reach a genuinely EMPTY
    field, whereas a straight replace persists in ONE save. That holds
    whether the test left a replacement image in the field or left it
    empty, so this restore works from either state.

    Re-uploading creates a FRESH Documents & Media document rather than
    re-linking the original, so the restored file is byte-identical but may
    be named e.g. `chamber-laws-content (1).png` -- a disclosed, accepted
    side effect (the original document is not browsable in the picker to
    re-link). The verification therefore matches the file STEM, not the
    exact name."""
    authoring = admin.open_page_record()
    _unpublish_and_confirm(authoring)
    if download_path:
        authoring.upload_file(admin.CONTENT_IMAGE_UPLOAD_LABEL, download_path)
    if baseline_status == STATUS_PUBLISHED:
        _publish_and_confirm(authoring)
    else:
        _save_draft_and_confirm(authoring)

    # PROVE it committed -- fresh navigation, never a stale form read.
    authoring = admin.open_page_record()
    actual_status = authoring.current_status()
    if actual_status != baseline_status:
        raise AssertionError(
            f"TEST_OWNED restore did not commit: page record status is "
            f"{actual_status!r}, expected {baseline_status!r}"
        )
    if download_path and original_filename:
        stem = original_filename.rsplit(".", 1)[0]
        restored = authoring.current_file_name(admin.CONTENT_IMAGE_UPLOAD_LABEL)
        if stem not in restored:
            raise AssertionError(
                "TEST_OWNED restore did not commit: Content Image reads "
                f"{restored!r}, expected the original {original_filename!r} "
                "(or a Liferay-deduplicated variant of it)"
            )




# ===========================================================================
# PAGE-RECORD FIELD CASES (134853, 134867-134870, 134876, 134889-134939)
# Implemented 2026-10-12 -- every former skip stub is now a real test.
# ===========================================================================
# SUPERSEDED 2026-10-13 (user decision): the 2026-10-12 authorization to
# write to the live singleton QCDEMO-129394-CHAMBER_LAWS_PAGE-ENTRY (and the
# hero row) is withdrawn. Every case below that needs a successful save calls
# block_live_singleton_write() right before it -> NOT APPLICABLE. Refusal
# cases click the one control the case expects to be refused, then
# stop_unless_refused() ends the test the moment no refusal is seen.
#
# HOW "SAVE" WORKS ON THIS RECORD (read live 2026-10-12, as TEST_USER): the
# record is Published, so the form's Save as Draft is DISABLED and its
# submit control reads "Publish" ("As an Editor, what you publish here goes
# live straight away"). A case's "click Save" is therefore that Publish
# control, addressed by its Liferay status value (`[name=status][value=0]`)
# so the Arabic-UI repeats ("نشر") hit the same control.
#
# ORIGINALS (history). `reports/backups/chamber_laws_page_20261012/` holds
# the record's original values, captured 2026-10-12. Nothing restores from
# it automatically any more (2026-10-13).
#
# MESSAGE WORDING is recorded, never asserted (memory "not bugs: toast /
# wording"): an empty required control is blocked by the BROWSER's own
# `required` check, whose message is the browser's, not the case's literal.
# The behaviour -- blocked, nothing persisted -- is what is asserted.
#
# CHARACTER LIMITS follow bug-rules.md Rule 5: the IMPLEMENTED limit (the
# field's live "<n> / <max>" counter; no `maxlength` exists) is measured and
# tested; it must be >= the US limit, accept exactly <max> and not store
# <max>+1. Rich-text Intro Content has no limit by rule (Rule 5.1): those two
# cases record that no limit applies.
import time as _time
from pathlib import Path as _Path

# The snapshot/restore engine (snapshot_hero, restore_with_retries,
# restore_hero_with_retries) also lives in page_record_backup.py; it is no
# longer wired into this module (user decision 2026-10-13).
from cms.pages.chambers_law.page_record_backup import (
    PAGE_BACKUP_IMAGE,
    norm_html as _norm_html,
    read_page_state as _read_page_state,
    temp_dir as _tempdir,
)
from cms.pages.components.object_authoring_page import ObjectAuthoringPage
from cms.pages.control_panel.login_page import CmsLoginPage
from cms.tests.chambers_law.law_entry_form import _LawEntryForm as _FormProbe
from config.settings import cms_role_credentials
from tools.fixture_factory import make_bmp, make_gif, make_jpg, make_png
import re as _re
import uuid as _uuid

LAW_ICON_FIXTURE = _Path(__file__).resolve().parent / "fixtures" / "law_icon_qctest.svg"
SAVE_SETTLE_TIMEOUT = 90.0
PUBLIC_REFLECT_FIELD_TIMEOUT = 120.0
ONE_MB = 1024 * 1024
ROLE_EDITOR = "Site Content Editor"
ROLE_AUTHOR = "Site Content Author"
ROLE_MEMBER = "Site Member"
# Disposable rows created during this module run -- swept again at module end.
_QCTEST_CREATED = {"law": set()}


@pytest.fixture(scope="module", autouse=True)
def _chamber_laws_module_cleanup(browser):
    """Module-end cleanup that writes NOTHING to a singleton.

    USER DECISION 2026-10-13: the module-start hero snapshot and the
    module-end restore of the Chamber Laws Page record / chamber-laws hero
    row are NO LONGER WIRED -- no test writes to either record any more (see
    live_write_guard.py), so there is nothing to restore, and a restore is
    itself a live write. The engine stays in
    cms/pages/chambers_law/page_record_backup.py (`snapshot_hero`,
    `restore_with_retries`, `restore_hero_with_retries`), not called.

    What remains: delete every disposable QCTEST Law Entry this run created
    (by exact title), and put the shared TEST_USER account back to English."""
    yield
    context = new_context(browser)
    admin = ChambersLawAdminPage(context.new_page())
    problems = []
    try:
        for title in ([] if deletes_suppressed() else sorted(_QCTEST_CREATED["law"])):
            try:
                _delete_law_entry(admin, title)
            except Exception as exc:  # noqa: BLE001 -- reported below
                problems.append(f"law entry {title}: {exc!r}")
        # The AR-interface steps (`/ar/...` URLs) can leave the SHARED
        # TEST_USER account rendering Arabic for every later suite (seen
        # 2026-10-12: web/tests/chambers_law failing on Arabic headings, the
        # audit portlet dating rows in Arabic). Put it back to English.
        try:
            CmsLoginPage(admin.page)._force_english_locale()
        except Exception as exc:  # noqa: BLE001 -- reported below
            problems.append(f"language reset to en_US: {exc!r}")
    finally:
        try:
            context.close()
        except Exception:  # noqa: BLE001
            pass
    if problems:
        detail = "MODULE-END CLEANUP FAILED (QCTEST law entries / account language): " + " | ".join(problems)
        logger.error(detail)
        raise AssertionError(detail)


def _page_current(admin) -> dict:
    """The record's CURRENT values, read at runtime -- earlier tests in the
    run may have left it modified (restore happens once at module end)."""
    return _read_page_state(admin)


def _attach(name: str, body) -> None:
    try:
        allure.attach(body if isinstance(body, str) else repr(body), name=name)
    except Exception:  # noqa: BLE001 -- reporting must never mask anything
        pass


def _publish_edit(admin, authoring, action: str = "publish", note: str = "") -> dict:
    """Clicks the record's Publish control ("Save" on a published record)
    and captures what the page said, BEFORE anything navigates away. The
    click is logged first (`action="attempt"` for a save the case expects
    to be REFUSED)."""
    probe = _FormProbe(authoring)
    log_live_write(_record_of(authoring), "<form submit>", "Publish", None, action=action,
                   note=note or "the form's Publish control (status=0) with the values entered")
    authoring.submit_via(admin.PUBLISH_SUBMIT)
    return {
        "refusal": probe.save_refusal_text(),
        "success": probe.success_message_text(),
        "url": admin.page.url,
    }


def _wait_stored(admin, reader, expected, timeout: float = SAVE_SETTLE_TIMEOUT):
    """Re-opens the record until `reader()` returns `expected` or the budget
    ends; returns the last value read either way (the caller asserts)."""
    seen = {"value": None}

    def _check() -> bool:
        admin.open_page_record(locale="en")
        seen["value"] = reader()
        return seen["value"] == expected

    try:
        wait_until(_check, timeout=timeout, poll=5)
    except Exception:  # noqa: BLE001 -- the caller's assert reports it
        pass
    return seen["value"]


def _stored_now(admin, reader):
    admin.open_page_record(locale="en")
    return reader()


def _text_of_length(length: int, locale: str, tc: str) -> str:
    seed = (f"QCTEST-{tc} قانون الغرفة " if locale == "ar" else f"QCTEST-{tc} Chamber law text ")
    return (seed * (length // len(seed) + 1))[:length]


# ---- Shapes shared by the per-case tests --------------------------------
def _case_valid_text(page, tc: str, key: str, locale: str, value: str, extra=None) -> None:
    admin = ChambersLawAdminPage(page)
    try:
        with allure.step("Open the Chamber's Law page record in Liferay CMS"):
            authoring = admin.open_page_record(locale="en")
            assert admin.page_has_edit_form(), "the page record did not open in an editable form"
        with allure.step(f"Enter {value!r} and click Save (Publish on this published record)"):
            admin.fill_page_text(key, value, locale)
            native = admin.page_text_validation_message(key, locale)
            _attach("client-side validation before Save", repr(native))
            block_live_singleton_write(PAGE_RECORD, f"{key} ({locale.upper()}) save of {value!r}")
            said = _publish_edit(admin, authoring)
            _attach("save outcome", said)
        with allure.step("Reload the record"):
            stored = _wait_stored(admin, lambda: admin.page_text(key, locale), value)
            extra_result = extra(admin) if extra else None
        assert native == "", f"the value raised a validation error: {native!r}"
        assert not said["refusal"], f"the save was refused: {said['refusal']!r}"
        assert stored == value, f"stored value is {stored!r}, expected {value!r}"
        if extra:
            assert extra_result is True, extra_result
    finally:
        pass  # nothing to restore: no successful write reaches the singleton (2026-10-13)


def _case_rejected_text(page, tc: str, key: str, locale: str, value: str,
                        ui_locales=("en",)) -> None:
    """Empty / whitespace-only value on a required field: the save must be
    blocked and the stored value left untouched (and never blank)."""
    admin = ChambersLawAdminPage(page)
    baseline = _page_current(admin)
    original = baseline[f"{key}_{locale}"]
    attempts = []
    try:
        for ui in ui_locales:
            with allure.step(f"[{ui.upper()} interface] Open the record, enter {value!r} and click Save"):
                authoring = admin.open_page_record(locale=ui)
                admin.fill_page_text(key, value, locale)
                native = admin.page_text_validation_message(key, locale)  # read BEFORE the click
                said = _publish_edit(admin, authoring)
            with allure.step(f"[{ui.upper()} interface] Reload the record and read the stored value"):
                stored = _stored_now(admin, lambda: admin.page_text(key, locale))
            attempts.append({"ui": ui, "native": native, **said, "stored": stored})
            # 2026-10-13: stop before the next interface's click if this one
            # was not refused -- nothing more may be written to the record.
            stop_unless_refused(
                stored == original, PAGE_RECORD,
                f"[{ui.upper()} UI] Save with {key} ({locale.upper()}) = {value!r}",
                {"native": native, "refusal": said["refusal"], "stored": stored, "was": original},
            )
        _attach("observed messages per interface language (recorded, not asserted)",
                "\n".join(repr(a) for a in attempts))
        for attempt in attempts:
            assert attempt["stored"] == original, (
                f"[{attempt['ui']} UI] the save was NOT blocked: the field now stores "
                f"{attempt['stored']!r} (was {original!r}); page said "
                f"native={attempt['native']!r} refusal={attempt['refusal']!r}"
            )
            assert attempt["native"] or attempt["refusal"], (
                f"[{attempt['ui']} UI] the value was not stored but no validation message "
                "was shown at all"
            )
    finally:
        pass  # nothing to restore: no successful write reaches the singleton (2026-10-13)


def _case_char_limit(page, tc: str, key: str, locale: str, us_limit: int) -> None:
    admin = ChambersLawAdminPage(page)
    try:
        with allure.step("Open the record and read the field's implemented limit off its live counter"):
            authoring = admin.open_page_record(locale="en")
            _, implemented = admin.page_text_counter(key, locale)
            limit = implemented if implemented > 0 else us_limit
            _attach("limits", f"US limit={us_limit}; implemented (counter)={implemented}; tested={limit}")
        at_limit = _text_of_length(limit, locale, tc)
        over_limit = at_limit + ("ب" if locale == "ar" else "X")
        with allure.step(f"Enter a {limit}-character value and click Save"):
            admin.fill_page_text(key, at_limit, locale)
            block_live_singleton_write(PAGE_RECORD, f"{key} ({locale.upper()}) save at the {limit}-character limit")
            said_at = _publish_edit(admin, authoring)
            stored_at = _wait_stored(admin, lambda: admin.page_text(key, locale), at_limit)
        with allure.step(f"Enter a {limit + 1}-character value and click Save"):
            authoring = admin.open_page_record(locale="en")
            admin.fill_page_text(key, over_limit, locale)
            typed = admin.page_text(key, locale)
            capped = len(typed) <= limit
            said_over = None
            stored_over = None
            if not capped:
                said_over = _publish_edit(admin, authoring)
                stored_over = _stored_now(admin, lambda: admin.page_text(key, locale))
            _attach("over-limit outcome", {"typed_len": len(typed), "capped": capped,
                                           "said": said_over, "stored_len": len(stored_over or "")})
        assert implemented > 0, "the field renders no '<n> / <max>' counter -- its limit is unmeasurable"
        assert limit >= us_limit, (
            f"implemented limit {limit} is LOWER than the US limit {us_limit}"
        )
        assert stored_at == at_limit, (
            f"the {limit}-character value was not stored (stored {len(stored_at or '')} chars); "
            f"save said {said_at!r}"
        )
        assert capped or stored_over != over_limit, (
            f"the {limit + 1}-character value was accepted and stored -- no limit is enforced"
        )
    finally:
        pass  # nothing to restore: no successful write reaches the singleton (2026-10-13)


def _case_rich_rejected(page, tc: str, locale: str, mode: str) -> None:
    """`mode` "empty" clears the editor; "spaces" types only spaces."""
    admin = ChambersLawAdminPage(page)
    baseline = _page_current(admin)
    try:
        with allure.step(f"Open the record and {'clear' if mode == 'empty' else 'type only spaces into'} "
                         f"Intro Content ({locale.upper()}), then click Save"):
            authoring = admin.open_page_record(locale="en")
            if mode == "empty":
                admin.set_intro_html("", locale)
            else:
                admin.set_intro_html("", locale)
                admin.type_into_intro("     ", locale)
            said = _publish_edit(admin, authoring)
        with allure.step("Reload the record"):
            stored = _stored_now(admin, lambda: admin.intro_html(locale))
        _attach("save outcome (wording recorded, not asserted)", said)
        stop_unless_refused(
            _norm_html(stored) == _norm_html(baseline[f"intro_{locale}"]), PAGE_RECORD,
            f"Save with Intro Content ({locale.upper()}) {mode}", {"said": said, "stored": stored[:200]},
        )
        assert _norm_html(stored) == _norm_html(baseline[f"intro_{locale}"]), (
            f"the save was NOT blocked: Intro Content ({locale.upper()}) now stores {stored!r}"
        )
    finally:
        pass  # nothing to restore: no successful write reaches the singleton (2026-10-13)


def _case_rich_no_limit(page, tc: str, locale: str) -> None:
    """bug-rules.md Rule 5.1: no character limit applies to a rich-text
    field -- the case is Not Applicable. The test measures and records the
    real behaviour: 5000 AND 5001 characters are both stored."""
    admin = ChambersLawAdminPage(page)
    char = "ق" if locale == "ar" else "a"
    stored = {}
    try:
        for size in (5000, 5001):
            with allure.step(f"Enter exactly {size} characters in Intro Content ({locale.upper()}) and click Save"):
                authoring = admin.open_page_record(locale="en")
                admin.set_intro_html(f"<p>{char * size}</p>", locale)
                block_live_singleton_write(PAGE_RECORD, f"Intro Content ({locale.upper()}) {size}-character save")
                said = _publish_edit(admin, authoring)
                text = _wait_stored(
                    admin, lambda: len(admin.intro_text(locale).strip()), size
                )
                stored[size] = text
                _attach(f"{size}-character save", {"said": said, "stored_len": text})
        allure.attach(
            "bug-rules.md Rule 5.1: rich-text fields carry no character limit -- this case is "
            f"Not Applicable. Observed: stored lengths {stored}.",
            name="Rule 5 -- Not Applicable (rich text)",
        )
        assert stored[5000] == 5000, f"the 5000-character content was not stored intact ({stored[5000]})"
        assert stored[5001] == 5001, (
            f"5001 characters were not stored intact ({stored[5001]}) -- a limit IS applied "
            "to this rich-text field, contrary to Rule 5.1"
        )
    finally:
        pass  # nothing to restore: no successful write reaches the singleton (2026-10-13)


def _fixture(name: str, maker, size: int) -> str:
    path = _Path(_tempdir()) / name
    if not path.exists() or path.stat().st_size != size:
        path.write_bytes(maker(size))
    return str(path)


_UPLOAD_COMPLAINT = _re.compile(r"valid (file )?extension|valid file size|بملحق|ملحق|حجم", _re.I)
_UPLOAD_SIZE_COMPLAINT = _re.compile(r"valid file size|حجم", _re.I)
_PICKER_ADD = _re.compile(r"^\s*(Add|أضف)\s*$")


def _attempt_upload(admin, authoring, field_name: str, file_path: str,
                    size_only: bool = False, add_if_accepted: bool = False) -> dict:
    """Drives the picker with one file and reports what was said about it.

    The picker itself rejects a wrong EXTENSION (live 2026-10-12: "Please
    enter a file with a valid extension (.jpg,.png,.svg)." / Arabic "...
    بملحق ... صالح."), but it uploads a file of ANY size into Documents &
    Media ("1 of 1"). The field's SIZE limit is only applied once the file is
    attached with Add, by the form -- so `add_if_accepted=True` clicks Add
    (a form-only change: nothing is saved unless the caller publishes) and
    then reads the form's own size complaint. Callers re-open the record
    afterwards, which discards the unsaved attachment."""
    probe = _FormProbe(authoring)
    frame = admin.open_file_picker(field_name)
    admin.picker_set_file(frame, file_path)
    reader = probe.size_rejection_text if size_only else probe.declared_rejection_text
    pattern = _UPLOAD_SIZE_COMPLAINT if size_only else _UPLOAD_COMPLAINT
    seen = {"rejection": "", "accepted": False, "form_rejection": ""}

    def _resolved() -> bool:
        seen["rejection"] = reader(frame) or probe._visible_text(frame, pattern) or seen["rejection"]
        if seen["rejection"]:
            return True
        if admin.picker_reports_uploaded(frame):
            seen["accepted"] = True
            return True
        return False

    try:
        wait_until(_resolved, timeout=25, poll=1.0)
    except Exception:  # noqa: BLE001 -- "neither" is itself the result
        pass
    seen["picker_text"] = probe.picker_body_text()
    if seen["accepted"] and add_if_accepted:
        frame.get_by_role("button", name=_PICKER_ADD).first.click(timeout=15000)
        probe._picker_closed(10000)

        def _form_said() -> bool:
            seen["form_rejection"] = (
                probe.size_rejection_text() or probe._visible_text(admin.page, pattern)
            )
            return bool(seen["form_rejection"])

        try:
            wait_until(_form_said, timeout=10, poll=1.0)
        except Exception:  # noqa: BLE001 -- no complaint is itself the result
            pass
        # Did Add actually attach it? The field's hidden input receives the
        # new file's id; it stays empty when the form refuses the file. (Its
        # `required` state is NOT a signal: on an edit form it reads empty
        # even while a stored file is kept.)
        try:
            wait_until(lambda: bool(admin.attachment_value(field_name)), timeout=10, poll=1.0)
        except Exception:  # noqa: BLE001 -- not attached is itself the result
            pass
        seen["attached"] = bool(admin.attachment_value(field_name))
    else:
        probe.close_picker()
    seen["rejected"] = bool(
        seen["rejection"] or seen["form_rejection"]
        or (add_if_accepted and seen["accepted"] and not seen.get("attached"))
    )
    return seen


# ---- AboutHeroBanner (hero cases 134897-134902) ---------------------------
# LIVE 2026-10-12: the About Hero Banner manage page renders its create form
# HIDDEN (`display:none`, no "+ Add New") -- one row per page -- so no
# disposable hero row can exist. The 2026-10-12 approval to write the REAL
# row QCDEMO-ABOUT-HERO-chamber-laws is withdrawn (user decision 2026-10-13):
# 134897, 134899 and 134901 are NOT APPLICABLE at their save; 134898 (picker
# only), 134900 and 134902 (refusal cases) still run.
_HERO_JPG = _re.compile(r"^hero( \(\d+\))?\.jpg$", _re.I)


def _open_real_hero(admin, locale: str = "en"):
    return admin.open_hero_record(admin.HERO_BANNER_CHAMBER_LAWS_CODE, locale=locale)


def _hero_stored(admin, reader, ok, timeout: float = SAVE_SETTLE_TIMEOUT):
    """Re-opens the hero row until `ok(reader(admin))` or the budget ends;
    returns the last value read (the caller asserts). `reader` gets the
    ChambersLawAdminPage (a BasePage), so it must use `hero_banner_file_name()`
    -- fix 2026-10-14: 134897/134899 passed `a.current_file_name(...)`, which
    the admin page does not have; every poll raised, wait_until swallowed it,
    and the test reported "stored None" for a save that had gone through."""
    seen = {"value": None}

    def _check() -> bool:
        _open_real_hero(admin)
        seen["value"] = reader(admin)
        return ok(seen["value"])

    try:
        wait_until(_check, timeout=timeout, poll=5)
    except Exception:  # noqa: BLE001 -- the caller's assert reports it
        pass
    return seen["value"]


def _audit_age_seconds(stamp: str) -> float:
    """Age of an audit row from its relative stamp ("42 Seconds Ago",
    "3 Minutes Ago"); infinity for anything older or unparseable. Minute
    stamps are whole minutes, so callers allow +60 s of slack."""
    # English ("42 Seconds Ago") or Arabic ("منذ 42 ثانية" / "منذ 8 دقائق") --
    # the portlet follows the account language, which drifts on qcdev.
    text = stamp or ""
    m = _re.match(r"\s*(\d+)\s+(Second|Minute)s?\s+Ago", text, _re.I)
    if m:
        return int(m.group(1)) * (1 if m.group(2).lower() == "second" else 60)
    m = _re.match(r"\s*منذ\s*(\d+)\s*(ثان|ثوان|دقي|دقا)", text)
    if m:
        return int(m.group(1)) * (1 if m.group(2).startswith("ث") else 60)
    return float("inf")


# ---- Role sessions (134867-134870, 134876) -------------------------------
def _role_session(browser, role: str):
    """A FRESH context signed in as `role` -- never the TEST_USER page, and
    never a saved role storageState (those had expired on 2026-10-12)."""
    context = new_context(browser, use_auth_state=False)
    role_page = context.new_page()
    email, password = cms_role_credentials(role)
    CmsLoginPage(role_page).open_login().login(email, password)
    return context, role_page


def _law_title(tc: str) -> str:
    """`QCTEST-<tc>-LAW-<uid>` -- unique per call, so two rows made in the same
    second (134886) never collide."""
    return f"QCTEST-{tc}-LAW-{_uuid.uuid4().hex[:8]}"


def _law_number(title: str) -> str:
    """The Law Number a disposable entry is created with -- also the text the
    public card renders in `.qc-cl-card-number` (ChambersLawPage keys cards on it)."""
    return f"{title} No."


def _create_law_entry(role_admin, title: str, publish: bool, active: bool = False,
                      display_order: str = "9900", url: str | None = None) -> None:
    """A disposable Law Entry. Defaults: Active Status UN-ticked and Display
    Order 9900, so it can never reach or reorder the public page. Cases that
    need a public card pass active=True; Display Order stays in the 9900+
    range, so the card always renders AFTER every real card."""
    _QCTEST_CREATED["law"].add(title)
    authoring = role_admin.open_new_law_entry_form(locale="en")
    ar = role_admin.ARABIC_SUFFIX
    for label, value in (
        (role_admin.LAW_NUMBER_LABEL, _law_number(title)),
        (role_admin.LAW_TITLE_LABEL, title),
        (role_admin.LAW_DESCRIPTION_LABEL, f"{title} created by automation."),
    ):
        authoring.fill_text(label, value)
        authoring.fill_text(label + ar, value)
    if url is not None:
        authoring.fill_text(role_admin.EXTERNAL_LINK_URL_LABEL, url)
    authoring.upload_file(role_admin.LAW_ICON_UPLOAD_LABEL, str(LAW_ICON_FIXTURE))
    authoring.fill_number(role_admin.DISPLAY_ORDER_LABEL, display_order)
    authoring.set_checkbox(role_admin.ACTIVE_STATUS_LABEL, active)
    log_live_write(_law_record(title), "<create>", title, None, action="create",
                   note=f"publish={publish}, active={active}, display order {display_order}; "
                        "disposable QCTEST row")
    if publish:
        authoring.submit_via(role_admin.PUBLISH_SUBMIT)
    else:
        authoring.save_as_draft()


def _law_listed(role_admin, title: str, timeout: float = 60.0) -> bool:
    try:
        wait_until(lambda: role_admin.open_law_entries_list(locale="en").row_visible(title),
                   timeout=timeout, poll=5)
        return True
    except Exception:  # noqa: BLE001
        return False


def _open_law(admin, title: str):
    """A disposable entry opened for edit through its own row's Edit link
    (Law Entry's Entry column renders the Law Title)."""
    return admin.open_law_entries_list(locale="en").open_entry_by_edit_link(title)


def _qctest_law(admin, tc: str, *, active: bool = True, display_order: str = "9900",
                url: str | None = None) -> tuple:
    """Creates and PUBLISHES a disposable `QCTEST-<tc>-LAW-<uid>` Law Entry
    (user decision 2026-10-13: never the real QCDEMO-129394-law-* rows) and
    proves it reached Published. Returns (title, law_number). The caller
    deletes it by exact title in its `finally`; the module-end sweep is the
    backstop."""
    title = _law_title(tc)
    _create_law_entry(admin, title, publish=True, active=active, display_order=display_order, url=url)
    if not _law_listed(admin, title, timeout=PUBLISH_CONFIRM_TIMEOUT):
        raise AssertionError(f"precondition: the disposable law entry {title!r} was not created")
    # Published + Active unticked badges `Inactive` (live 2026-10-13).
    _open_law(admin, title).wait_for_status(STATUS_PUBLISHED if active else STATUS_INACTIVE,
                                            timeout=PUBLISH_CONFIRM_TIMEOUT)
    return title, _law_number(title)


def _delete_disposable_laws(admin, titles, tc: str) -> None:
    """Teardown: delete every disposable row by EXACT title (never by position).

    Under QC_ALLOW_LIVE_SINGLETON_WRITES=1 NOTHING is deleted (user decision
    2026-10-13): each row is logged `kept` for manual cleanup and, when it is
    still Active, HIDDEN instead (Active Status un-ticked and re-published --
    the tc_134884 pattern), so no QCTEST card stays on the public page."""
    for title in titles:
        if keep_instead_of_delete(_law_record(title), title, tc,
                                  note="left for manual cleanup (nothing is deleted under the opt-in); "
                                       "hidden if active"):
            _test_owned_reset(lambda t=title: _hide_law_entry(admin, t, tc),
                              label=f"tc_{tc} hide disposable law entry {title}")
            continue
        _test_owned_reset(lambda t=title: _delete_law_entry(admin, t), label=f"tc_{tc} disposable law entry {title}")


def _hide_law_entry(admin, title: str, tc: str) -> None:
    """Keep-not-delete teardown: un-tick Active Status on the disposable
    QCTEST row (unpublish -> untick -> publish, each logged) and PROVE it."""
    if not title.startswith("QCTEST-"):
        raise AssertionError(f"refusing to touch non-disposable law entry {title!r}")
    authoring = _open_law(admin, title)
    if authoring.is_checked(admin.ACTIVE_STATUS_LABEL) is False:
        return
    # Edited IN PLACE (2026-10-13): a Published row's form publishes the change
    # straight away, so no Unpublish round trip; the row then reads Inactive.
    authoring.set_checkbox(admin.ACTIVE_STATUS_LABEL, False)
    log_live_write(_law_record(title), "Active Status", False, tc, action="status",
                   note="hide the kept QCTEST card from the public page")
    _publish_and_confirm(authoring)
    if _open_law(admin, title).is_checked(admin.ACTIVE_STATUS_LABEL) is not False:
        raise AssertionError(f"the QCTEST entry {title!r} is still Active -- its card may be public")


def _delete_law_entry(admin, title: str) -> None:
    if not title.startswith("QCTEST-"):
        raise AssertionError(f"refusing to delete non-disposable law entry {title!r}")
    if keep_instead_of_delete(_law_record(title), title):
        return
    admin.open_law_entries_list(locale="en").delete_all_entries_by_title(title)
    if admin.open_law_entries_list(locale="en").row_visible(title):
        raise AssertionError(f"disposable law entry {title!r} is still listed after delete")

# ---------------------------------------------------------------------------
# P3/P4 BATCH 2026-10-13 -- page Status picklist cases 134937 / 134938 on the
# REAL Chamber Laws Page singleton (user decision 2026-10-13; opt-in
# QC_ALLOW_LIVE_SINGLETON_WRITES=1, every write logged, nothing deleted).
# The case shape lives in cms/tests/live_status_cases.py.
# ---------------------------------------------------------------------------
from cms.tests.live_status_cases import PicklistRecord, status_draft_case, status_published_case

P34_WORKFLOW_BUDGET = 150.0


def _p34_picklist(editor) -> PicklistRecord:
    """The page singleton, driven through `editor` (a Site Content Editor
    session): the object's own `pageStatus` picklist on the form."""
    return PicklistRecord(
        record=PAGE_RECORD,
        entry_code=CHAMBERS_LAW_PAGE_ENTRY_CODE,
        form=editor,
        open_form=lambda: editor.open_page_record(locale="en"),
        save=lambda authoring: _publish_edit(editor, authoring),
        open_list=lambda: editor.open_page_entries_list(),
        budget=P34_WORKFLOW_BUDGET,
    )



# ---------------------------------------------------------------------------
# 134850 / 134851 -- the page-level section headings authored on the Chamber
# Laws Page record reach the public page (Control_Panel half, 2026-10-14).
#
# The Web-observable half lives in web/tests/chambers_law/test_chambers_law_web.py
# under the SAME tc_ marker. That is deliberate and safe: 75 tc_ markers are
# already shared by the web and cms trees (e.g. tc_134877), sync_tc_markers.py
# registers a marker once however many modules carry it, and the surface is
# selected by `-m control_panel` / `-m web`. Run one half by nodeid.
#
# Write model (P1/P2 rerun opt-in, QC_ALLOW_LIVE_SINGLETON_WRITES=1): the
# record is READ first; the case's heading is written (logged, then
# published) ONLY when the stored value differs or the record is not
# Published + Active. Nothing is restored afterwards; the record ends
# Published (`_page_end_published`).
# ---------------------------------------------------------------------------
CASE_INTRO_HEADING = "Chamber Legal Framework"
CASE_REFS_HEADING = "Official Legal References"
# The brand maroon the web suite already asserts on About pages
# (`MAROON = "rgb(145, 23, 49)"`, #911731, in
# web/tests/about_chairman_message/test_chairman_message_web.py and
# web/tests/b2b_matchmaking/test_b2b_matchmaking_web.py) -- copied, not
# imported from a test module.
BRAND_MAROON = "rgb(145, 23, 49)"
_HEADING_LABELS = {"intro_heading": ChambersLawAdminPage.INTRO_HEADING_LABEL,
                   "refs_heading": ChambersLawAdminPage.REFERENCES_HEADING_LABEL}
_STYLE_PROPS = ["color", "fontSize", "fontWeight"]


def _plain_text(html_or_text: str) -> str:
    """Tags stripped, entities decoded, whitespace collapsed -- compares the
    authored rich text with the rendered text by CONTENT, not markup."""
    import html as _html

    return " ".join(_html.unescape(_re.sub(r"<[^>]+>", " ", html_or_text or "")).split())


def _px(value: str) -> float:
    try:
        return float(str(value).rstrip("px"))
    except ValueError:
        return -1.0


def _close_quietly(context) -> None:
    try:
        if context is not None:
            context.close()
    except Exception:  # noqa: BLE001
        pass


def _ensure_page_headings(admin, tc: str, wanted: dict) -> dict:
    """Step 1 of 134850/134851: the Chamber Laws Page record (EN) must hold
    the case's heading(s) and be Published + Active. Reads first; writes
    (each logged BEFORE the click, old -> new) and publishes ONLY what
    differs. Returns the record's stored values after the step."""
    authoring = admin.open_page_record(locale="en")
    before = {key: admin.page_text(key) for key in wanted}
    status, active = authoring.current_status(), admin.active_status_checked()
    _attach(f"tc_{tc} Chamber Laws Page before step 1",
            {"values": before, "status": status, "active": active})
    changes = {key: value for key, value in wanted.items() if before[key] != value}
    if changes or status != STATUS_PUBLISHED or not active:
        block_live_singleton_write(PAGE_RECORD, f"set {sorted(changes)} and publish", tc_id=tc)
        for key, value in changes.items():
            log_live_write(PAGE_RECORD, f"{_HEADING_LABELS[key]} (EN)", value, tc, action="write",
                           note=f"old value {before[key]!r} -> new value {value!r}")
            admin.fill_page_text(key, value)
        if not active:
            log_live_write(PAGE_RECORD, "Active Status", True, tc, action="status",
                           note="old value False -> new value True")
            admin.set_active_status(True)
        _publish_and_confirm(authoring)
    else:
        _attach(f"tc_{tc} step 1 -- no write", "the record already held the case's values and was "
                "Published + Active; nothing was written")
    authoring = admin.open_page_record(locale="en")
    stored = {key: admin.page_text(key) for key in ("intro_heading", "refs_heading")}
    stored.update(intro_html=admin.intro_html("en"), status=authoring.current_status(),
                  active=admin.active_status_checked())
    _attach(f"tc_{tc} Chamber Laws Page after step 1", stored)
    return stored


def _anon_chambers_law(browser, stored: dict, extra=None,
                       timeout: float = PUBLIC_REFLECT_AFTER_PUBLISH_TIMEOUT):
    """A FRESH logged-out context on the public page (cache-busted), polled
    until it serves the stored headings (and `extra(public)` holds, if
    given). Returns (context, ChambersLawPage); the caller closes it."""
    context = new_context(browser, use_auth_state=False)
    public = ChambersLawPage(context.new_page())

    def _caught_up() -> bool:
        public.open_chambers_law(cache_bust=True)
        try:
            return (public.intro_heading_text().strip() == stored["intro_heading"].strip()
                    and public.refs_heading_text().strip() == stored["refs_heading"].strip()
                    and (extra is None or bool(extra(public))))
        except Exception:  # noqa: BLE001 -- a block not rendered on this load
            return False

    try:
        wait_until(_caught_up, timeout=timeout, poll=5)
    except Exception:  # noqa: BLE001 -- the caller's assertions name what differs
        _attach("public page never matched the stored values within the budget", public.body_text()[:2000])
    return context, public


def _active_published_laws(admin) -> list:
    """Entries of the Law Entry list whose badge is PUBLISHED -- both
    visibility gates hold (a Published row with Active unticked reads
    INACTIVE). The list shows every row (`open_entries_list`)."""
    rows = admin.open_law_entries_list(locale="en").row_statuses()
    _attach("Law Entry list (entry, status)", rows)
    return [entry for entry, status in rows if status == STATUS_PUBLISHED]


@allure.epic("About Us")
@allure.feature("Chamber's Law")
@allure.story("Intro block")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Verify that the Chamber Legal Framework section renders its configured heading and intro content (Control_Panel)")
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.ui
@pytest.mark.uat
@pytest.mark.pbi_129394
@pytest.mark.tc_134850
@pytest.mark.traceability("134850")
@allure.label("pbi", "129394")
@allure.label("testcase", "134850")
@CHAMBERS_LAW_XDIST_GROUP
@pytest.mark.timeout(480)
def test_chambers_law_cp_134850_legal_framework_heading_and_intro_render_from_the_cms(page, browser):
    # Account: TEST_USER (the module's `page`). The case is about a CMS value
    # reaching the page, not a workflow path, so the account does not decide
    # the outcome -- named here per standards.md.
    admin = ChambersLawAdminPage(page)
    anon_ctx = None
    with _page_end_published(admin, "134850"):
        try:
            with allure.step("Set Intro Heading (EN) to 'Chamber Legal Framework' with the configured "
                             "Intro Content (EN), and publish"):
                stored = _ensure_page_headings(admin, "134850", {"intro_heading": CASE_INTRO_HEADING})
            with allure.step("Open the Chamber's Law page in English (fresh logged-out context)"):
                anon_ctx, public = _anon_chambers_law(browser, stored)
                counts = public.section_counts()
                heading = public.intro_heading_text().strip()
                body = public.intro_body_text()
                page_text = public.body_text()
            with allure.step("Inspect the intro heading and the body beneath it"):
                tops = public.section_tops()
                heading_style = public.computed_style(public.INTRO_HEADING, _STYLE_PROPS)
                body_style = public.computed_style(public.INTRO_TEXT, _STYLE_PROPS)
                _attach("computed styles (heading / body)", {"heading": heading_style, "body": body_style,
                                                              "expected heading colour": BRAND_MAROON})
                _attach("rendered intro body", body)
        finally:
            _close_quietly(anon_ctx)

    authored = _plain_text(stored["intro_html"])
    first_sentence = authored.split(". ")[0]
    # Step 1 -- the record holds the case's heading and is live.
    assert stored["intro_heading"] == CASE_INTRO_HEADING, (
        f"Intro Heading (EN) reads {stored['intro_heading']!r} after step 1")
    assert stored["status"] == STATUS_PUBLISHED and stored["active"], (
        f"the record is {stored['status']!r} / active={stored['active']} after step 1")
    assert authored, "precondition: Intro Content (EN) is empty on the record"
    # Steps 2-3 -- heading text, position, colour, hierarchy.
    assert heading == stored["intro_heading"], f"public intro heading reads {heading!r}"
    assert counts["intro_heading"] == 1 and counts["intro_body"] == 1, f"intro blocks rendered: {counts}"
    assert None not in (tops["intro_heading"], tops["intro_body"]), f"missing block: {tops}"
    assert tops["intro_heading"] < tops["intro_body"], f"the heading is not above the body: {tops}"
    assert heading_style["color"] == BRAND_MAROON, (
        f"intro heading colour is {heading_style['color']!r}, expected the brand maroon {BRAND_MAROON}")
    assert _px(heading_style["fontSize"]) > _px(body_style["fontSize"]), (
        f"heading {heading_style['fontSize']} is not larger than body {body_style['fontSize']}")
    assert int(heading_style["fontWeight"]) > int(body_style["fontWeight"]), (
        f"heading weight {heading_style['fontWeight']} is not bolder than body {body_style['fontWeight']}")
    # Step 4 -- the body matches the authored source and renders once.
    assert _plain_text(body) == authored, (
        f"rendered intro body differs from the authored source:\n  rendered {_plain_text(body)!r}\n"
        f"  authored {authored!r}")
    assert page_text.count(first_sentence) == 1, (
        f"the intro's first sentence appears {page_text.count(first_sentence)} times on the page")
    assert page_text.count(CASE_INTRO_HEADING) == 1, (
        f"{CASE_INTRO_HEADING!r} appears {page_text.count(CASE_INTRO_HEADING)} times on the page")


@allure.epic("About Us")
@allure.feature("Chamber's Law")
@allure.story("Legal references section")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Verify that the Official Legal References section renders its configured heading above the law entry cards (Control_Panel)")
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.ui
@pytest.mark.uat
@pytest.mark.pbi_129394
@pytest.mark.tc_134851
@pytest.mark.traceability("134851")
@allure.label("pbi", "129394")
@allure.label("testcase", "134851")
@CHAMBERS_LAW_XDIST_GROUP
@pytest.mark.timeout(480)
def test_chambers_law_cp_134851_legal_references_heading_renders_above_the_law_cards(page, browser):
    # Account: TEST_USER (see 134850). The case's "two active published law
    # entries" is a precondition about the data; the number asserted is the
    # number of entries passing BOTH visibility gates on the list right now
    # (attached), so the check holds whatever that count is.
    admin = ChambersLawAdminPage(page)
    anon_ctx = None
    with _page_end_published(admin, "134851"):
        try:
            with allure.step("Set Legal References Section Heading (EN) to 'Official Legal References' "
                             "and publish"):
                stored = _ensure_page_headings(admin, "134851", {"refs_heading": CASE_REFS_HEADING})
            with allure.step("Read the Active + Published law entries"):
                live_laws = _active_published_laws(admin)
            with allure.step("Open the Chamber's Law page in English (fresh logged-out context)"):
                anon_ctx, public = _anon_chambers_law(
                    browser, stored, extra=lambda p: p.card_count() == len(live_laws))
                counts = public.section_counts()
                refs = public.refs_heading_text().strip()
                intro = public.intro_heading_text().strip()
                tops = public.section_tops()
                style = public.computed_style(public.REFS_HEADING, _STYLE_PROPS)
                _attach("computed style (references heading)", {"style": style, "expected": BRAND_MAROON})
                _attach("cards", {"public": public.card_titles(), "active+published entries": live_laws})
        finally:
            _close_quietly(anon_ctx)

    assert stored["refs_heading"] == CASE_REFS_HEADING, (
        f"References Heading (EN) reads {stored['refs_heading']!r} after step 1")
    assert stored["status"] == STATUS_PUBLISHED and stored["active"], (
        f"the record is {stored['status']!r} / active={stored['active']} after step 1")
    assert live_laws, "precondition: no Active + Published law entry exists"
    assert refs == stored["refs_heading"], f"public references heading reads {refs!r}"
    assert refs != intro, f"the references heading repeats the intro heading ({intro!r})"
    assert counts["refs_heading"] == 1, f"references heading rendered {counts['refs_heading']} times"
    assert None not in (tops["intro_body"], tops["refs_heading"], tops["first_card"]), f"missing block: {tops}"
    assert tops["intro_body"] < tops["refs_heading"] < tops["first_card"], (
        f"expected the intro block, then the references heading, then the cards: {tops}")
    assert style["color"] == BRAND_MAROON, (
        f"references heading colour is {style['color']!r}, expected the brand maroon {BRAND_MAROON}")
    assert counts["cards"] == len(live_laws), (
        f"{counts['cards']} law cards render, but {len(live_laws)} entries are Active + Published: {live_laws}")


@allure.epic("About Us")
@allure.feature("Chamber's Law")
@allure.story("CMS authoring / admin")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Verify that the Content Image exposes the alt text configured in the CMS")
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.ui
@pytest.mark.pbi_129394
@pytest.mark.tc_134853
@pytest.mark.traceability("134853")
@allure.label("pbi", "129394")
@allure.label("testcase", "134853")
@CHAMBERS_LAW_XDIST_GROUP
def test_chambers_law_cp_134853_the_content_image_exposes_the_alt_text_configured_in_the_cms(page, browser):
    admin = ChambersLawAdminPage(page)
    expected_alt = "Law book with scales of justice"
    anon_context = new_context(browser, use_auth_state=False)
    public = ChambersLawPage(anon_context.new_page())
    try:
        with allure.step(f"Set Content Image Alt Text (EN) to {expected_alt!r} and publish"):
            authoring = admin.open_page_record(locale="en")
            admin.fill_page_text("alt_text", expected_alt, "en")
            block_live_singleton_write(PAGE_RECORD, "Content Image Alt Text (EN) publish")
            said = _publish_edit(admin, authoring)
            stored = _wait_stored(admin, lambda: admin.page_text("alt_text", "en"), expected_alt)
            _attach("save outcome", said)
        assert stored == expected_alt, f"the alt text was not saved (stored {stored!r})"
        with allure.step("Open the Chamber's Law page in English as an anonymous visitor and inspect the image alt"):
            seen = {"alt": None}

            def _alt_live() -> bool:
                public.open_chambers_law()
                seen["alt"] = public.intro_image_alt()
                return seen["alt"] == expected_alt

            try:
                _reflects_public(_alt_live, timeout=PUBLIC_REFLECT_FIELD_TIMEOUT)
            except Exception:  # noqa: BLE001 -- asserted below with the evidence
                pass
            image_visible = public.is_intro_image_visible()
        assert image_visible, "the Content Image is not visible on the public page"
        assert seen["alt"] == expected_alt, (
            f"the public Content Image alt is {seen['alt']!r}, expected {expected_alt!r}"
        )
    finally:
        try:
            anon_context.close()
        except Exception:  # noqa: BLE001
            pass


@allure.epic("About Us")
@allure.feature("Chamber's Law")
@allure.story("CMS authoring / admin")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("Verify that a Site Content Editor can manage both the page and its law entry records")
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.regression
@pytest.mark.auth
@pytest.mark.pbi_129394
@pytest.mark.tc_134867
@pytest.mark.traceability("134867")
@allure.label("pbi", "129394")
@allure.label("testcase", "134867")
@CHAMBERS_LAW_XDIST_GROUP
def test_chambers_law_cp_134867_a_site_content_editor_can_manage_both_the_page_and_its_law_entry_records(page, browser):
    # Signed in as the real Site Content Editor account (never TEST_USER). The
    # "one law entry edit" runs on a DISPOSABLE QCTEST law entry (inactive,
    # Display Order 9900, so it never reaches or reorders the public page) --
    # the real 1990/1996 entries are not authorized for writes.
    admin = ChambersLawAdminPage(page)
    context, editor_page = _role_session(browser, ROLE_EDITOR)
    editor = ChambersLawAdminPage(editor_page)
    title = _law_title("134867")
    problems = []
    try:
        with allure.step("Sign in as Site Content Editor"):
            if not CmsLoginPage(editor_page).has_admin_toolbar():
                problems.append("the Editor session has no CMS toolbar after sign-in")
        with allure.step("Open the page record: Edit, Preview, Publish and Unpublish must be available"):
            editor.open_page_entries_list()
            actions = editor.page_row_actions()
            attrs = editor.page_row_action_attrs()
            authoring = editor.open_page_record(locale="en")
            controls = editor.publish_control_state()
            _attach("page-record controls", {"row actions": actions, "row attrs": attrs, "form": controls})
            for wanted in ("Edit", "Preview"):
                if wanted not in actions:
                    problems.append(f"page row offers no {wanted!r} action (has {actions})")
            if "data-qc-oel-unpublish" not in attrs:
                problems.append(f"page row offers no Unpublish action (attrs {attrs})")
            if not (controls["publish"][0] and controls["publish"][1]):
                problems.append(f"the form's Publish control is missing/disabled: {controls['publish']}")
            if editor.ACCESS_DENIED_EN in editor.body_text():
                problems.append("Access Denied is shown on the page record for the Editor")
        with allure.step("Open the Law Entry list: create, edit, reorder, activate and deactivate must be available"):
            editor.open_law_entries_list(locale="en")
            list_text = editor.body_text()
            if "+ Add New" not in list_text:
                problems.append("the Law Entry list offers no '+ Add New' (create)")
            if not editor.list_offers_row_link("Edit"):
                problems.append("no law entry row offers 'Edit'")
            form = editor.open_new_law_entry_form(locale="en")
            form_probe = _FormProbe(form)
            labels = form_probe.visible_control_labels()
            _attach("law entry form controls", labels)
            if not editor.form_has_control("spinbutton", editor.DISPLAY_ORDER_LABEL):
                problems.append("no Display Order control (reorder) on the law entry form")
            if not editor.form_has_control("checkbox", editor.ACTIVE_STATUS_LABEL):
                problems.append("no Active Status control (activate/deactivate) on the law entry form")
        with allure.step("Perform one law entry edit (disposable QCTEST entry) and publish the page"):
            _create_law_entry(editor, title, publish=True)
            if not _law_listed(editor, title):
                problems.append(f"the Editor could not create the disposable law entry {title!r}")
            else:
                entry = editor.open_law_entries_list(locale="en").open_entry_by_edit_link(title)
                new_desc = f"{title} edited by the Editor."
                entry.fill_text(editor.LAW_DESCRIPTION_LABEL, new_desc)
                entry.submit_via(editor.PUBLISH_SUBMIT)  # live-write-guard: disposable QCTEST law entry
                stored_desc = editor.open_law_entries_list(locale="en").open_entry_by_edit_link(title).field_value(editor.LAW_DESCRIPTION_LABEL)
                if stored_desc != new_desc:
                    problems.append(f"the law entry edit was not saved (reads {stored_desc!r})")
                if editor.ACCESS_DENIED_EN in editor.body_text():
                    problems.append("Access Denied shown on the law entry for the Editor")
            authoring = editor.open_page_record(locale="en")
            # The law-entry half above ran on a disposable QCTEST row; the
            # page publish would write the real singleton (2026-10-13).
            block_live_singleton_write(PAGE_RECORD, f"page publish as Editor; problems so far: {problems}")
            said = _publish_edit(editor, authoring)
            status = editor.open_page_record(locale="en").current_status()
            _attach("page publish as Editor", {"said": said, "status": status})
            if said["refusal"] or editor.ACCESS_DENIED_EN in editor.body_text():
                problems.append(f"publishing the page as Editor was refused: {said['refusal']!r}")
            if status != STATUS_PUBLISHED:
                problems.append(f"page status after the Editor's publish is {status!r}")
        assert not problems, "Site Content Editor permissions not as the case expects:\n" + "\n".join(problems)
    finally:
        try:
            context.close()
        except Exception:  # noqa: BLE001
            pass
        with allure.step(f"Teardown -- delete the disposable law entry {title} by exact title"):
            _test_owned_reset(lambda: _delete_law_entry(admin, title), label="tc_134867 disposable law entry")


@allure.epic("About Us")
@allure.feature("Chamber's Law")
@allure.story("CMS authoring / admin")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("Verify that a Site Content Author can view and update assigned Chamber's Law content and law entries")
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.regression
@pytest.mark.auth
@pytest.mark.pbi_129394
@pytest.mark.tc_134868
@pytest.mark.traceability("134868")
@allure.label("pbi", "129394")
@allure.label("testcase", "134868")
@CHAMBERS_LAW_XDIST_GROUP
def test_chambers_law_cp_134868_a_site_content_author_can_view_and_update_assigned_chamber_s_law_content_and_law(page, browser):
    # As the real Site Content Author. Live 2026-10-12: the page record is
    # Published, and the Author form shows "Access Denied ... Only a Content
    # Editor can change a record once it has reached the website" with both
    # submit controls disabled. The law-entry half runs on a DISPOSABLE QCTEST
    # entry the Author creates (as a draft) -- the real entries are not writable.
    admin = ChambersLawAdminPage(page)
    baseline = _page_current(admin)
    context, author_page = _role_session(browser, ROLE_AUTHOR)
    author = ChambersLawAdminPage(author_page)
    title = _law_title("134868")
    problems = []
    with _page_end_published(admin, "134868"):
        try:
            with allure.step("Open the page record as Author, update Intro Content (EN) and save"):
                author.open_page_record_as_viewer(locale="en")
                authoring = ObjectAuthoringPage(author_page, slug="chamber-laws-page")
                controls = author.publish_control_state()
                denied = author.ACCESS_DENIED_EN in author.body_text()
                _attach("Author page-record controls", {"form": controls, "access_denied": denied})
                if denied:
                    problems.append("Access Denied is shown on the page record for the Author")
                submit_ok = any(present and enabled for present, enabled, _ in controls.values())
                if not submit_ok:
                    problems.append(f"no enabled save control for the Author on the page record: {controls}")
                else:
                    author.set_intro_html(baseline["intro_en"] + "<p>QCTEST-134868 author update</p>", "en")
                    selector = author.SAVE_DRAFT_SUBMIT if controls["draft"][1] else author.PUBLISH_SUBMIT
                    # An enabled Author save would write the real singleton.
                    block_live_singleton_write(PAGE_RECORD, f"Author's Intro Content save; controls {controls}")
                    log_live_write(PAGE_RECORD, "Intro Content (EN)", "<current intro> + <p>QCTEST-134868 author update</p>",
                                   "134868", action="save-draft" if selector == author.SAVE_DRAFT_SUBMIT else "publish",
                                   note=f"Site Content Author save via {selector!r} (re-published in finally)")
                    authoring.submit_via(selector)
                    if author.ACCESS_DENIED_EN in author.body_text():
                        problems.append("Access Denied after the Author's page save")
                    stored = _stored_now(author, lambda: author.intro_html("en"))
                    if "QCTEST-134868 author update" not in stored:
                        problems.append("the Author's Intro Content change was not saved")
            with allure.step("Open an assigned law entry (disposable, created by the Author), update Law Description (EN) and save"):
                _create_law_entry(author, title, publish=False)
                if not _law_listed(author, title):
                    problems.append(f"the Author could not create the disposable law entry {title!r}")
                else:
                    entry = author.open_law_entries_list(locale="en").open_entry_by_edit_link(title)
                    new_desc = f"{title} edited by the Author."
                    entry.fill_text(author.LAW_DESCRIPTION_LABEL, new_desc)
                    log_live_write(_law_record(title), "Law Description (EN)", new_desc, "134868",
                                   action="save-draft", note="Site Content Author edit of the disposable row")
                    entry.save_as_draft()
                    if author.ACCESS_DENIED_EN in author.body_text():
                        problems.append("Access Denied on the Author's law entry save")
                    stored_desc = author.open_law_entries_list(locale="en").open_entry_by_edit_link(title).field_value(author.LAW_DESCRIPTION_LABEL)
                    if stored_desc != new_desc:
                        problems.append(f"the Author's law entry change was not saved (reads {stored_desc!r})")
            assert not problems, "Site Content Author could not view and update as the case expects:\n" + "\n".join(problems)
        finally:
            try:
                context.close()
            except Exception:  # noqa: BLE001
                pass
            with allure.step(f"Teardown -- delete the disposable law entry {title} by exact title"):
                _test_owned_reset(lambda: _delete_law_entry(admin, title), label="tc_134868 disposable law entry")


@allure.epic("About Us")
@allure.feature("Chamber's Law")
@allure.story("CMS authoring / admin")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("Verify that a Site Content Author cannot publish the Chamber's Law page")
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.auth
@pytest.mark.pbi_129394
@pytest.mark.tc_134869
@pytest.mark.traceability("134869")
@allure.label("pbi", "129394")
@allure.label("testcase", "134869")
@CHAMBERS_LAW_XDIST_GROUP
def test_chambers_law_cp_134869_a_site_content_author_cannot_publish_the_chamber_s_law_page(page, browser):
    admin = ChambersLawAdminPage(page)
    baseline = _page_current(admin)
    context, author_page = _role_session(browser, ROLE_AUTHOR)
    author = ChambersLawAdminPage(author_page)
    try:
        with allure.step("Open the page record as Author and locate the publish control"):
            author.open_page_entries_list()
            row_attrs = author.page_row_action_attrs()
            author.open_page_record_as_viewer(locale="en")
            controls = author.publish_control_state()
            body = author.body_text()
            _attach("Author controls", {"form": controls, "row attrs": row_attrs})
        with allure.step("Attempt to publish the page"):
            publish_present, publish_enabled, publish_label = controls["publish"]
            # 2026-10-13: an enabled publish control IS the finding -- it is
            # never clicked, because a click could publish the real singleton.
            stop_unless_refused(
                not (publish_present and publish_enabled), PAGE_RECORD,
                "the Author's publish control (offered enabled, not clicked)", controls["publish"],
            )
            status_after = admin.open_page_record(locale="en").current_status()
        assert not (publish_present and publish_enabled and publish_label == "Publish"), (
            f"an enabled 'Publish' control is offered to the Author: {controls['publish']}"
        )
        assert not publish_enabled, f"the Author's submit control is enabled: {controls['publish']}"
        for action in ("data-qc-oel-publish", "data-qc-oel-approve", "data-qc-oel-unpublish"):
            assert action not in row_attrs, f"the page row offers {action!r} to the Author"
        assert status_after == baseline["workflow"], (
            f"the page publication state changed to {status_after!r}"
        )
        assert author.ACCESS_DENIED_EN in body, (
            "the 'Access Denied. You do not have permission to perform this action.' message "
            "is not shown to the Author"
        )
    finally:
        try:
            context.close()
        except Exception:  # noqa: BLE001
            pass


@allure.epic("About Us")
@allure.feature("Chamber's Law")
@allure.story("CMS authoring / admin")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("Verify that a user without the required permission is denied access to the Chamber's Law records")
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.auth
@pytest.mark.pbi_129394
@pytest.mark.tc_134870
@pytest.mark.traceability("134870")
@allure.label("pbi", "129394")
@allure.label("testcase", "134870")
@CHAMBERS_LAW_XDIST_GROUP
def test_chambers_law_cp_134870_a_user_without_the_required_permission_is_denied_access_to_the_chamber_s_law_rec(page, browser):
    # A signed-in Site Member holds no content role. Read-only attempts only.
    from cms.pages.chambers_law.chambers_law_admin_page import LAW_1990_ENTRY_CODE as _LAW_CODE
    context, member_page = _role_session(browser, ROLE_MEMBER)
    member = ChambersLawAdminPage(member_page)
    results = {}
    try:
        for ui, message in (("en", member.ACCESS_DENIED_EN), ("ar", member.ACCESS_DENIED_AR)):
            with allure.step(f"[{ui.upper()}] Attempt to open the page record and a law entry for editing"):
                for label, slug, code in (
                    ("page record", "chamber-laws-page", CHAMBERS_LAW_PAGE_ENTRY_CODE),
                    ("law entry", "law-entry", _LAW_CODE),
                ):
                    member.open_manage_entry(slug, code, ui)
                    body = member.body_text()
                    editable = member.has_object_form()
                    results[(ui, label)] = (message in body, editable)
        _attach("per-attempt (message shown, editable form rendered)", results)
        for (ui, label), (shown, editable) in results.items():
            assert not editable, f"[{ui}] the {label} opened in editable mode for a Site Member"
            assert shown, f"[{ui}] the exact Access Denied message was not shown on the {label}"
    finally:
        try:
            context.close()
        except Exception:  # noqa: BLE001
            pass
@allure.epic("About Us")
@allure.feature("Chamber's Law")
@allure.story("CMS authoring / admin")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("Verify that publishing the Chamber's Law page makes the content visible on the website")
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.regression
@pytest.mark.functional_high
@pytest.mark.workflow
@pytest.mark.pbi_129394
@pytest.mark.tc_134871
@pytest.mark.traceability("134871")
@allure.label("pbi", "129394")
@allure.label("testcase", "134871")
@CHAMBERS_LAW_XDIST_GROUP
def test_chambers_law_cp_134871_publishing_the_chamber_s_law_page_makes_the_content_visible_on_the_website(page, browser):
    # RETARGETED BACK onto the **Chamber Laws Page** record 2026-09-15.
    # The previous version of this test published a LAW ENTRY and asserted a
    # card, under a comment claiming it had been "RETARGETED ... after the
    # previous target was proven not to exist", plus a "DISCLOSED COVERAGE
    # GAP" claiming Page Title / Intro Section Heading / Legal References
    # Section Heading "exist NOWHERE in Object Authoring". Both claims were
    # FALSE -- `manage-chamber-laws-page` returns HTTP 200, holds the
    # singleton QCDEMO-129394-CHAMBER_LAWS_PAGE-ENTRY, and authors exactly
    # those three fields (re-verified live 2026-09-15; see this module's
    # header for the evidence, including the public intro image whose own
    # `src` names this object entry as its owner).
    #
    # This test now does what the case actually asks: publish the PAGE
    # record and prove the PAGE-LEVEL content becomes visible to an
    # anonymous visitor. To make "publishing" a genuine action rather than a
    # no-op on an already-published record, the record is first taken off
    # the live site and its absence confirmed publicly.
    #
    # BASELINE IS CAPTURED AT RUNTIME, never hardcoded: the live values are
    # polluted by earlier runs ("Chamber's Law--1", "Chamber Legal Framework
    # Framework", "Official Official Legal References"), so the assertions
    # compare the public render against what the CMS ACTUALLY holds right
    # now -- which is the real expected result of this case anyway.
    #
    # TEST_OWNED: the page record is real editorial content; its status is
    # read BEFORE mutating and restored through _test_owned_reset(), which
    # re-reads the record to prove the restore committed.
    admin = ChambersLawAdminPage(page)
    baseline_status = None
    baseline = {}

    with _page_end_published(admin, "134871"):
        anon_context = new_context(browser, use_auth_state=False)
        anon_page = anon_context.new_page()

        try:
            with allure.step("Open the Chamber Laws Page record via Object Authoring"):
                authoring = admin.open_page_record()
                baseline_status = authoring.current_status()
                baseline = {
                    "page_title": authoring.field_value(admin.PAGE_TITLE_LABEL),
                    "intro_heading": authoring.field_value(admin.INTRO_HEADING_LABEL),
                    "refs_heading": authoring.field_value(admin.REFERENCES_HEADING_LABEL),
                    "content_image": authoring.current_file_name(
                        admin.CONTENT_IMAGE_UPLOAD_LABEL
                    ),
                }
                allure.attach(
                    "\n".join(f"{k} = {v!r}" for k, v in baseline.items()),
                    name="CMS baseline captured at runtime (the expected public content)",
                )

            with allure.step("Take the page off the live site first, so publishing is genuinely exercised"):
                block_live_singleton_write(PAGE_RECORD, "unpublish, then publish the page")
                _unpublish_and_confirm(authoring)

            with allure.step("Confirm an anonymous visitor is not served the unpublished page content"):
                cl = ChambersLawPage(anon_page)

                def _page_content_gone() -> bool:
                    cl.open_chambers_law()
                    return not cl.renders_page_level_content(baseline["page_title"])

                _reflects_public(
                    _page_content_gone,
                    message=(
                        "the unpublished Chamber Laws Page record's content was still "
                        "being served publicly before the publish step"
                    ),
                )

            with allure.step("Click Submit for Review on the Chamber Laws Page record"):
                _publish_and_confirm(authoring)
                status_after_publish = authoring.current_status()

            with allure.step("Wait for the standard cache refresh and re-open the page as a genuine anonymous visitor"):
                def _page_content_back() -> bool:
                    cl.open_chambers_law()
                    return cl.renders_page_level_content(baseline["page_title"])

                _reflects_public(
                    _page_content_back,
                    timeout=PUBLIC_REFLECT_AFTER_PUBLISH_TIMEOUT,
                    message="the public page never reflected the newly-published page record",
                )
                public_hero_title = cl.hero_title_text()
                public_intro_heading = cl.intro_heading_text()
                public_refs_heading = cl.refs_heading_text()
                public_image_visible = cl.is_intro_image_visible()
                public_image_src = cl.intro_image_src()

            # Assert -- the page-level content this record owns is now live
            assert status_after_publish == STATUS_PUBLISHED
            assert public_hero_title == baseline["page_title"], (
                "expected the published Page Title to render as the page's <h1>"
            )
            assert public_intro_heading == baseline["intro_heading"], (
                "expected the published Intro Heading to render as the intro section heading"
            )
            assert public_refs_heading == baseline["refs_heading"], (
                "expected the published References Heading to render above the law cards"
            )
            assert public_image_visible, (
                "expected the published Content Image to render in the intro section"
            )
            assert CHAMBERS_LAW_PAGE_ENTRY_CODE in public_image_src, (
                "expected the rendered intro image to be the Content Image of THIS "
                f"record; got src={public_image_src!r}"
            )
        finally:
            try:
                anon_context.close()
            except Exception:  # noqa: BLE001 -- cleanup must never mask the real result
                pass
        # No TEST_OWNED restore (2026-10-13): the test stops at the NOT APPLICABLE
        # guard before its first write, so there is nothing to put back.


@allure.epic("About Us")
@allure.feature("Chamber's Law")
@allure.story("CMS authoring / admin")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Verify that unpublishing the Chamber's Law page removes it from the website")
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.regression
@pytest.mark.functional_high
@pytest.mark.workflow
@pytest.mark.pbi_129394
@pytest.mark.tc_134873
@pytest.mark.traceability("134873")
@allure.label("pbi", "129394")
@allure.label("testcase", "134873")
@CHAMBERS_LAW_XDIST_GROUP
def test_chambers_law_cp_134873_unpublishing_the_chamber_s_law_page_removes_it_from_the_website(page, browser):
    # RETARGETED BACK onto the **Chamber Laws Page** record 2026-09-15 --
    # see tc_134871's comment block for the live evidence that the object
    # exists and owns the page-level content.
    #
    # THE OLD "DISCLOSED FINDING" ON THIS TEST STAYS WITHDRAWN, but for the
    # right reason now. It claimed unpublishing does not retract content
    # because `/about-us/chamber-laws` kept serving HTTP 200. That was
    # measured while this test pointed at a LAW ENTRY, so a still-serving
    # page proved nothing. The correct question -- and what this test now
    # asks -- is whether the PAGE-LEVEL CONTENT this record owns stops being
    # served. That is the behaviour the case is about; whether the URL
    # itself 404s or merely renders without this record's content is a
    # delivery detail, captured as Allure context rather than asserted, so
    # this test cannot fail for the wrong reason a second time.
    #
    # ⚠ THIS TEST TAKES THE PUBLIC CHAMBER'S LAW PAGE CONTENT OFFLINE for
    # the duration of the run. That is exactly what the case asks for, but
    # it is also why every test in this module shares
    # @CHAMBERS_LAW_XDIST_GROUP (nothing may run against this page
    # concurrently) and why the restore below is CHECKED, not assumed.
    #
    # TEST_OWNED: status captured before mutating, restored and VERIFIED.
    admin = ChambersLawAdminPage(page)
    baseline_status = None
    baseline_title = None

    with _page_end_published(admin, "134873"):
        anon_context = new_context(browser, use_auth_state=False)
        anon_page = anon_context.new_page()

        try:
            with allure.step("Open the published Chamber Laws Page record via Object Authoring"):
                authoring = admin.open_page_record()
                baseline_status = authoring.current_status()
                baseline_title = authoring.field_value(admin.PAGE_TITLE_LABEL)

            with allure.step("Ensure the record starts Approved/published (this case's own precondition)"):
                if authoring.current_status() != STATUS_PUBLISHED:
                    block_live_singleton_write(PAGE_RECORD, "precondition publish")
                    _publish_and_confirm(authoring)
                assert authoring.current_status() == STATUS_PUBLISHED, (
                    "precondition failed: the Chamber Laws Page record is not in the "
                    "Approved/published state this case starts from"
                )

            with allure.step("Confirm an anonymous visitor can see the page content before unpublishing"):
                cl = ChambersLawPage(anon_page)

                def _page_served() -> bool:
                    cl.open_chambers_law()
                    return cl.renders_page_level_content(baseline_title)

                _reflects_public(
                    _page_served,
                    timeout=PUBLIC_REFLECT_AFTER_PUBLISH_TIMEOUT,
                    message="the published page content was not publicly visible before unpublishing",
                )

            with allure.step("Click Unpublish to edit as draft on the page record"):
                block_live_singleton_write(PAGE_RECORD, "unpublish the page")
                _unpublish_and_confirm(authoring)

            with allure.step("Wait for the standard cache refresh, then open the public URL with no CMS login"):
                def _page_content_removed() -> bool:
                    cl.open_chambers_law()
                    return not cl.renders_page_level_content(baseline_title)

                _reflects_public(
                    _page_content_removed,
                    message=(
                        "the public page was still serving the unpublished page record's "
                        "content after the standard cache refresh window"
                    ),
                )
                still_renders_page_content = cl.renders_page_level_content(baseline_title)
                public_body = cl.body_text()
                # Delivery-detail context, deliberately NOT asserted (see the
                # comment block above): whether the URL keeps serving a shell or
                # stops entirely is not what this case is about.
                allure.attach(
                    f"hero section visible = {cl.is_hero_visible()}\n"
                    f"intro section visible = {cl.is_intro_section_visible()}\n"
                    f"law cards rendered = {cl.card_numbers()}",
                    name="public delivery state after unpublishing (context, not asserted)",
                )

            with allure.step("Re-open the record in the CMS"):
                authoring = admin.open_page_record()
                status_in_cms = authoring.current_status()
                entries = admin.open_page_entries_list()
                # This object's Entry column renders the CODE, not a title.
                record_still_listed = entries.row_visible_by_code(CHAMBERS_LAW_PAGE_ENTRY_CODE)

            # Assert -- public side: the page content this record owns is gone
            assert not still_renders_page_content, (
                "expected the Chamber's Law page-level content to stop being served "
                "after unpublishing its page record"
            )
            assert baseline_title not in public_body, (
                f"expected the unpublished Page Title {baseline_title!r} to appear "
                "nowhere on the public page"
            )
            # Assert -- CMS side: the record survives, per the case's own step 4.
            # Unpublish lands on `Unpublished` (its own state, not Draft).
            assert status_in_cms == STATUS_UNPUBLISHED, (
                f"expected the unpublished page record to read Unpublished in the CMS; it reads {status_in_cms!r}")
            assert record_still_listed, (
                "expected the unpublished page record to remain present/editable in the CMS"
            )
        finally:
            try:
                anon_context.close()
            except Exception:  # noqa: BLE001 -- cleanup must never mask the real result
                pass
        # No TEST_OWNED restore (2026-10-13): the test stops at the NOT APPLICABLE
        # guard before its first write, so there is nothing to put back.


@allure.epic("About Us")
@allure.feature("Chamber's Law")
@allure.story("CMS authoring / admin")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("Verify that draft Chamber's Law content is visible only in the CMS and not on the website")
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.regression
@pytest.mark.functional_high
@pytest.mark.workflow
@pytest.mark.pbi_129394
@pytest.mark.tc_134874
@pytest.mark.traceability("134874")
@allure.label("pbi", "129394")
@allure.label("testcase", "134874")
@CHAMBERS_LAW_XDIST_GROUP
def test_chambers_law_cp_134874_draft_chamber_s_law_content_is_visible_only_in_the_cms_and_not_on_the_website(page, browser):
    # RETARGETED BACK onto the **Chamber Laws Page** record 2026-09-15. The
    # previous version drove a Law Entry's `Law Description` on the false
    # premise that the page object did not exist; the page-level field this
    # case is about is authorable and is used again here.
    #
    # WHICH PAGE FIELD, AND WHY: the marker goes in `Intro Heading`, a plain
    # textbox that renders publicly as the intro section's `<h2>`. The
    # page record's `Intro Content` (a bilingual CKEditor rich text, also
    # confirmed live) would be the closer literal match to the case's
    # wording, but a rich-text round trip on this surface doubles paragraph
    # breaks on every write/read/write cycle (see _normalize_rich_text()),
    # so repeatedly mutating it drifts real editorial content. Intro Heading
    # is page-level content on the same record, publicly rendered, and
    # byte-stable -- a deliberate, disclosed substitution, not a retarget to
    # a different object.
    #
    # DISCLOSED OBJECT-MODEL CONSTRAINT (unchanged, and it applies to the
    # page record too): a record cannot be published and hold a draft edit
    # at the same time -- while it is Approved, `Save as Draft` is DISABLED
    # and the guide's only route to editing is "Unpublish to edit as draft",
    # which takes it off the live site immediately (guide §4). So this
    # case's "...and still shows the previously published content" clause
    # cannot refer to THIS record while it is drafted. What the public
    # surface does around the drafted page record is attached as context,
    # not asserted -- the case's real, checkable claim is the one asserted:
    # the draft text never reaches a visitor, and the CMS holds it.
    #
    # TEST_OWNED: Intro Heading + status captured before mutating, restored
    # and VERIFIED by re-reading the field back.
    admin = ChambersLawAdminPage(page)
    baseline_heading = None
    baseline_status = None
    marker = "DRAFT-ONLY-129394"

    with _page_end_published(admin, "134874"):
        anon_context = new_context(browser, use_auth_state=False)
        anon_page = anon_context.new_page()

        try:
            with allure.step("Open the Chamber Laws Page record via Object Authoring"):
                authoring = admin.open_page_record()

            with allure.step("Capture the pre-existing baseline Intro Heading + Status (TEST_OWNED reset target)"):
                baseline_heading = authoring.field_value(admin.INTRO_HEADING_LABEL)
                baseline_status = authoring.current_status()

            with allure.step(f"Add the marker '{marker}' to the page's Intro Heading and Save as Draft"):
                # Unpublish first: Save as Draft is disabled while Approved.
                block_live_singleton_write(PAGE_RECORD, "unpublish + Save as Draft of Intro Heading")
                _unpublish_and_confirm(authoring)
                authoring.fill_text(
                    admin.INTRO_HEADING_LABEL, f"{baseline_heading} {marker}"
                )
                _save_draft_and_confirm(authoring)

            with allure.step("Open the public Chamber's Law page as a genuine anonymous visitor and search for the draft-only marker"):
                cl = ChambersLawPage(anon_page)
                cl.open_chambers_law()
                public_body_text = cl.body_text()
                allure.attach(
                    f"hero section visible = {cl.is_hero_visible()}\n"
                    f"intro section visible = {cl.is_intro_section_visible()}\n"
                    f"law cards rendered = {cl.card_numbers()}",
                    name="public delivery state while the page record is drafted (context, not asserted)",
                )

            with allure.step("Re-open the record in the CMS"):
                authoring = admin.open_page_record()
                cms_heading = authoring.field_value(admin.INTRO_HEADING_LABEL)
                status_in_cms = authoring.current_status()

            # Assert -- the draft never leaks, and the CMS holds it
            assert status_in_cms == "Draft"
            assert marker in cms_heading, (
                "expected the CMS record to hold the draft-only marker"
            )
            assert marker not in public_body_text, (
                f"DRAFT LEAK: the marker '{marker}' saved only as a draft was found on "
                "the public Chamber's Law page"
            )
        finally:
            try:
                anon_context.close()
            except Exception:  # noqa: BLE001 -- cleanup must never mask the real result
                pass
            # 2026-10-13 opt-in: the marker is written back before the re-publish.
            _put_back_intro_heading(admin, baseline_heading, "134874")


@allure.epic("About Us")
@allure.feature("Chamber's Law")
@allure.story("CMS authoring / admin")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Verify that Preview renders unpublished Chamber's Law content without publishing it")
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.regression
@pytest.mark.functional_high
@pytest.mark.workflow
@pytest.mark.pbi_129394
@pytest.mark.tc_134875
@pytest.mark.traceability("134875")
@allure.label("pbi", "129394")
@allure.label("testcase", "134875")
@CHAMBERS_LAW_XDIST_GROUP
def test_chambers_law_cp_134875_preview_renders_unpublished_chamber_s_law_content_without_publishing_it(page, browser):
    # RETARGETED BACK onto the **Chamber Laws Page** record 2026-09-15 (same
    # correction as tc_134874 -- see that test's comment block for why the
    # marker goes in `Intro Heading`).
    #
    # Control_Panel only (no Web tag on this case) -- no public-side sibling
    # test needed. Preview is driven from the page object's OWN entries list
    # via the row-level Preview link, keyed BY CODE: this object's Entry
    # column renders `QCDEMO-129394-CHAMBER_LAWS_PAGE-ENTRY`, not a title
    # (the opposite of Law Entry, whose Entry column renders the Law Title).
    # Confirmed live 2026-09-15: that row's Preview link points at
    # `/web/qatar-chamber/about-us/chamber-laws?qcPreview=chamberlawspages:<id>`.
    #
    # Preview is a STAFF surface (guide §6: it renders drafts to signed-in
    # staff), so it is read through the AUTHENTICATED `page`, while the
    # public-visibility half is read through a fresh anonymous context --
    # per standards.md's mandatory logged-out-context rule. That split is
    # exactly what this case is about: staff can see the draft, visitors
    # cannot.
    #
    # TEST_OWNED: Intro Heading + status captured before mutating, restored
    # and VERIFIED.
    admin = ChambersLawAdminPage(page)
    baseline_heading = None
    baseline_status = None
    marker = "PREVIEW-ONLY-129394"

    with _page_end_published(admin, "134875"):
        anon_context = new_context(browser, use_auth_state=False)
        anon_page = anon_context.new_page()

        try:
            with allure.step("Open the Chamber Laws Page record via Object Authoring"):
                authoring = admin.open_page_record()

            with allure.step("Capture the pre-existing baseline Intro Heading + Status (TEST_OWNED reset target)"):
                baseline_heading = authoring.field_value(admin.INTRO_HEADING_LABEL)
                baseline_status = authoring.current_status()

            with allure.step(f"Add the marker '{marker}' to Intro Heading, Save as Draft (do not publish), then Preview"):
                block_live_singleton_write(PAGE_RECORD, "unpublish + Save as Draft of Intro Heading")
                _unpublish_and_confirm(authoring)
                authoring.fill_text(
                    admin.INTRO_HEADING_LABEL, f"{baseline_heading} {marker}"
                )
                _save_draft_and_confirm(authoring)
                status_before_preview = authoring.current_status()

                entries = admin.open_page_entries_list()
                preview_url = entries.row_preview_url_by_code(CHAMBERS_LAW_PAGE_ENTRY_CODE)
                assert preview_url, (
                    "could not resolve the page record's row-level Preview URL -- this "
                    "object's Entry column is keyed by CODE, not by title"
                )
                banner_text = entries.preview_banner_text(preview_url)  # navigates `page`
                preview_body_text = entries.rendered_body_text()

            with allure.step("Confirm the record status is unchanged after Preview"):
                authoring = admin.open_page_record()
                status_after_preview = authoring.current_status()

            with allure.step("Confirm the public page (fresh, anonymous context) does not contain the preview-only text"):
                cl = ChambersLawPage(anon_page)
                cl.open_chambers_law()
                public_body_text = cl.body_text()

            # Assert
            assert status_before_preview == "Draft"
            assert "draft" in banner_text.lower(), (
                f"expected the preview banner to disclose an unpublished/draft record; got {banner_text[:120]!r}"
            )
            assert marker in preview_body_text, (
                "expected Preview (a staff surface) to render the unpublished draft page content"
            )
            assert status_after_preview == "Draft", "expected Preview to leave the record status unchanged"
            assert marker not in public_body_text, (
                f"DRAFT LEAK: previewing must not publish -- the marker '{marker}' was "
                "found on the public Chamber's Law page"
            )
        finally:
            try:
                anon_context.close()
            except Exception:  # noqa: BLE001 -- cleanup must never mask the real result
                pass
            # 2026-10-13 opt-in: the marker is written back before the re-publish.
            _put_back_intro_heading(admin, baseline_heading, "134875")


@allure.epic("About Us")
@allure.feature("Chamber's Law")
@allure.story("CMS authoring / admin")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Verify that publishing the Chamber's Law page updates the page cache and writes an audit log entry")
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.functional_high
@pytest.mark.pbi_129394
@pytest.mark.tc_134876
@pytest.mark.traceability("134876")
@allure.label("pbi", "129394")
@allure.label("testcase", "134876")
@CHAMBERS_LAW_XDIST_GROUP
def test_chambers_law_cp_134876_publishing_the_chamber_s_law_page_updates_the_page_cache_and_writes_an_audit_log(page, browser):
    # Editor publishes; the cache half is checked as an anonymous visitor; the
    # audit half reads Liferay's Control Panel Audit portlet (reachable for the
    # TEST_USER admin session, read live 2026-10-12) for this record's own
    # entry id, and requires a NEW row by the Editor's own user id.
    admin = ChambersLawAdminPage(page)
    baseline = _page_current(admin)
    marker = "CACHE-CHECK-129394"
    context, editor_page = _role_session(browser, ROLE_EDITOR)
    editor = ChambersLawAdminPage(editor_page)
    anon_context = new_context(browser, use_auth_state=False)
    public = ChambersLawPage(anon_context.new_page())
    try:
        with allure.step("Sign in as Site Content Editor and note the current time"):
            admin.open_page_entries_list()
            entry_id = admin.page_row_entry_id()
            before = admin.audit_rows_for(entry_id)
            editor_id = editor.current_user_id()
            started = _time.monotonic()
            _attach("audit before", {"entry_id": entry_id, "editor_user_id": editor_id, "rows": before[:5]})
        with allure.step(f"Change Intro Content (EN) to include {marker!r} and click Publish"):
            authoring = editor.open_page_record(locale="en")
            editor.set_intro_html(baseline["intro_en"] + f"<p>{marker}</p>", "en")
            block_live_singleton_write(PAGE_RECORD, "Editor publish of Intro Content (EN)")
            said = _publish_edit(editor, authoring)
            stored = _wait_stored(editor, lambda: marker in editor.intro_html("en"), True)
            _attach("publish outcome", said)
        assert stored is True, f"the Editor's change was not saved/published ({said!r})"
        with allure.step("Open the public page after the standard cache refresh"):
            def _served() -> bool:
                public.open_chambers_law()
                return marker in public.body_text()

            served = True
            try:
                _reflects_public(_served, timeout=PUBLIC_REFLECT_FIELD_TIMEOUT)
            except Exception:  # noqa: BLE001
                served = False
        with allure.step("Open the Liferay audit log filtered to the Chamber's Law page record"):
            after = admin.audit_rows_for(entry_id)
            # Rows are matched by identity + age, NOT by count: the portlet
            # lists only the newest 200 events site-wide, so once that window
            # is full a before/after count never changes. A row counts when it
            # is by the acting Editor and no older than the time elapsed since
            # step 1 (+60 s for minute-granular stamps) -- so an earlier
            # Editor publish in the same run (e.g. tc_134867) cannot satisfy it.
            elapsed = _time.monotonic() - started
            new_rows = [r for r in after if _audit_age_seconds(r[-1]) <= elapsed + 60]
            _attach("audit after (recent rows)", new_rows or after[:5])
            by_editor = [r for r in new_rows if r[0] == editor_id]
        assert served, f"the public page did not serve {marker!r} after the cache refresh"
        assert by_editor, (
            f"no NEW audit-log entry for the page record (entry {entry_id}) by the acting Editor "
            f"(user {editor_id}); new rows: {new_rows}"
        )
    finally:
        for ctx in (context, anon_context):
            try:
                ctx.close()
            except Exception:  # noqa: BLE001
                pass


# ---------------------------------------------------------------------------
# 134877 -- Verify that clicking a Law Title hyperlink opens the configured external legal text
# Both Web+Control_Panel. The public CLICK-behaviour half is already
# scripted and passing in test_chambers_law_web.py under the same
# tc_134877 marker. THIS module adds the Control_Panel half: actually
# setting a law entry's External Link URL (EN) to the case's own literal
# value and publishing it, confirmed via the CMS and the public card's href.
# ---------------------------------------------------------------------------

@allure.epic("About Us")
@allure.feature("Chamber's Law")
@allure.story("CMS authoring / admin")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Verify that a law entry's External Link URL can be configured and published")
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.regression
@pytest.mark.functional_high
@pytest.mark.uat
@pytest.mark.redirect
@pytest.mark.pbi_129394
@pytest.mark.tc_134877
@pytest.mark.traceability("134877")
@allure.label("pbi", "129394")
@allure.label("testcase", "134877")
@CHAMBERS_LAW_XDIST_GROUP
def test_chambers_law_cp_134877_law_title_external_link_url_can_be_configured_and_published(page, browser):
    # RETARGETED 2026-10-13 (user decision: no test writes to REAL content):
    # runs on its own disposable `QCTEST-<tc>-LAW-<uid>` Law Entry created here
    # (Published, Display Order 9900+ so it renders after every real card),
    # never on the real QCDEMO-129394-law-11-1990 / -1996 rows. The public card
    # is read in a fresh logged-out context; the row is deleted by exact title.
    admin = ChambersLawAdminPage(page)
    target_url = "https://www.almeezan.qa/LawView.aspx?opt&LawID=2541"
    created = []
    anon_context = new_context(browser, use_auth_state=False)
    anon_page = anon_context.new_page()
    try:
        with allure.step(f"Create and publish a disposable law entry with External Link URL (EN) {target_url}"):
            title, number = _qctest_law(admin, "134877", url=target_url)
            created.append(title)
            authoring = _open_law(admin, title)
            stored_url = authoring.field_value(admin.EXTERNAL_LINK_URL_LABEL)
            status = authoring.current_status()

        with allure.step("Open the Chamber's Law page (logged out) and locate that card's Law Title link"):
            cl = ChambersLawPage(anon_page)

            def _public_reflects_url() -> bool:
                cl.open_chambers_law()
                return cl.is_card_visible(number) and _same_target_url(cl.card_title_href(number), target_url)

            _reflects_public(
                _public_reflects_url,
                timeout=PUBLIC_REFLECT_AFTER_PUBLISH_TIMEOUT,
                message="the QCTEST card's Law Title href never reflected the published External Link URL",
            )
            public_href = cl.card_title_href(number)
            public_target = cl.card_title_target(number)

        # CMS side verbatim; public side normalised (see _same_target_url()).
        assert status == STATUS_PUBLISHED
        assert stored_url == target_url, f"the CMS stores {stored_url!r}, expected {target_url!r}"
        assert _same_target_url(public_href, target_url), (
            f"expected the card's Law Title link to point at {target_url!r}; got {public_href!r}"
        )
        assert public_target == "_blank"
    finally:
        try:
            anon_context.close()
        except Exception:  # noqa: BLE001 -- cleanup must never mask the real result
            pass
        _delete_disposable_laws(admin, created, "134877")


@allure.epic("About Us")
@allure.feature("Chamber's Law")
@allure.story("CMS authoring / admin")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Verify that uploading a Content Image for the first time publishes it to the website")
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.regression
@pytest.mark.functional_high
@pytest.mark.pbi_129394
@pytest.mark.tc_134882
@pytest.mark.traceability("134882")
@allure.label("pbi", "129394")
@allure.label("testcase", "134882")
@CHAMBERS_LAW_XDIST_GROUP
def test_chambers_law_cp_134882_uploading_a_content_image_for_the_first_time_publishes_it_to_the_website(page, browser, tmp_path):
    # RETARGETED BACK onto the page record's **Content Image** 2026-09-15.
    # The previous version drove a Law Entry's `Law Icon` on the false
    # premise that no page-level Content Image field existed. It does:
    # confirmed live 2026-09-15 on manage-chamber-laws-page as
    # `Content Image` (hidden textbox "Content Image Select File", a
    # "Select File" button, a "Remove file" button, and a
    # `Current file: chamber-laws-content.png (173 KB) / Preview · Download`
    # meta block). `Content Image` and `Law Icon` are two different images
    # on two different objects.
    #
    # PRECONDITION HANDLING: the case's literal precondition is "a record
    # with no Content Image set", and this record HAS one. Because this
    # field exposes a real Download link, the original bytes can be captured
    # first and restored afterwards, so the empty-field precondition can be
    # reached safely instead of the case being skipped.
    #
    # CONFIRMED-LIVE TWO-PHASE SEQUENCE (see
    # ObjectAuthoringPage.remove_current_file()'s own docstring): Remove
    # file -> Select File -> Submit in ONE unsaved form session does NOT
    # persist the new file. Reaching a genuinely empty field and then
    # setting a new one needs (1) remove + its OWN save, (2) a fresh reopen,
    # then set + publish. Both the mutation and the restore below follow it.
    #
    # WHY THE PUBLIC `src` IS THE PROOF: the delivered intro image URL
    # carries `objectEntryExternalReferenceCode=
    # QCDEMO-129394-CHAMBER_LAWS_PAGE-ENTRY` plus the document's own name,
    # so it proves both WHICH record served the image and WHICH file it is.
    #
    # DISCLOSED DATA CHANGE: the case's literal `lawbook.png` fixture is not
    # used; the new image is an existing Documents & Media file picked via
    # Select File (`about-us-hero.png`, confirmed live at the picker root
    # 2026-09-15), per this project's instruction for attachment fields on
    # this surface.
    #
    # TEST_OWNED, byte-for-byte: the record's real Content Image is
    # downloaded via its own Download link BEFORE anything is removed and
    # re-uploaded in `finally`, then VERIFIED by re-reading the field.
    # Re-upload creates a fresh Documents & Media document rather than
    # re-linking the original one, so the restored image is byte-identical
    # but may carry a "(1)"-suffixed document name -- a disclosed, accepted
    # side effect, which is why the restore verifier matches on the file
    # STEM rather than the exact name.
    # CHANGED 2026-10-13: `about-us-hero.png` is no longer at the Documents &
    # Media picker root (live: Select File timed out on it), and that path
    # left the REAL page with NO Content Image. The image uploaded "for the
    # first time" is now the page's OWN original picture -- the bytes of
    # reports/backups/chamber_laws_page_20261012/content_image.png
    # (byte-identical to the live image read 2026-10-13) -- uploaded from disk
    # as `chamber-laws-content.png`. The case's behaviour is the same, and the
    # page ends on its own picture (Liferay may dedupe the name to "(<n>)").
    admin = ChambersLawAdminPage(page)
    target_image_file = "chamber-laws-content.png"
    expected_stem = target_image_file.rsplit(".", 1)[0]
    upload_path = tmp_path / target_image_file
    upload_path.write_bytes(PAGE_BACKUP_IMAGE.read_bytes())
    baseline_status = None
    original_filename = ""
    original_saved = False
    original_download_path = None

    with _page_end_published(admin, "134882"):
        anon_context = new_context(browser, use_auth_state=False)
        anon_page = anon_context.new_page()

        try:
            with allure.step("Open the Chamber Laws Page record via Object Authoring"):
                authoring = admin.open_page_record()

            with allure.step("Capture the pre-existing baseline Content Image (bytes, via its Download link) + Status"):
                baseline_status = authoring.current_status()
                original_filename = authoring.current_file_name(
                    admin.CONTENT_IMAGE_UPLOAD_LABEL
                )
                if original_filename:
                    original_download_path = str(tmp_path / original_filename)
                    original_saved = bool(
                        authoring.download_current_file(
                            admin.CONTENT_IMAGE_UPLOAD_LABEL, original_download_path
                        )
                    )

            with allure.step("Remove the current Content Image and save (phase 1) to reach this case's own empty-field precondition"):
                block_live_singleton_write(PAGE_RECORD, "remove + save the Content Image")
                _unpublish_and_confirm(authoring)
                if original_filename:
                    authoring.remove_current_file(admin.CONTENT_IMAGE_UPLOAD_LABEL)
                    _save_draft_and_confirm(authoring)

            with allure.step(f"Re-open fresh, pick '{target_image_file}' from Documents & Media as the Content Image, and publish (phase 2)"):
                authoring = admin.open_page_record()
                assert authoring.current_file_name(admin.CONTENT_IMAGE_UPLOAD_LABEL) == "", (
                    "expected the Content Image field to be genuinely empty after the "
                    "phase-1 remove+save"
                )
                authoring.upload_file(admin.CONTENT_IMAGE_UPLOAD_LABEL, str(upload_path))
                log_live_write(PAGE_RECORD, "Content Image", target_image_file, "134882", action="upload",
                               note="the page's own original image bytes (PAGE_BACKUP_IMAGE), published next")
                _publish_and_confirm(authoring)

            with allure.step("Open the public Chamber's Law page in English after the standard cache refresh"):
                cl = ChambersLawPage(anon_page)

                def _public_reflects_image() -> bool:
                    cl.open_chambers_law()
                    return expected_stem in cl.intro_image_src()

                _reflects_public(
                    _public_reflects_image,
                    timeout=PUBLIC_REFLECT_AFTER_PUBLISH_TIMEOUT,
                    message="the public intro image never reflected the newly-published Content Image",
                )
                public_image_src = cl.intro_image_src()
                public_image_visible = cl.is_intro_image_visible()

            # Assert
            assert authoring.current_status() == STATUS_PUBLISHED
            stored_image = authoring.current_file_name(admin.CONTENT_IMAGE_UPLOAD_LABEL)
            assert stored_image.startswith(expected_stem) and stored_image.endswith(".png"), (
                f"expected the Content Image to read {target_image_file!r} (or a deduped "
                f"variant); it reads {stored_image!r}")
            assert public_image_visible, (
                "expected the published Content Image to render on the public page"
            )
            assert expected_stem in public_image_src, (
                f"expected the public intro image to resolve to {target_image_file!r}; "
                f"got src={public_image_src!r}"
            )
            assert CHAMBERS_LAW_PAGE_ENTRY_CODE in public_image_src, (
                "expected the rendered image to be served from THIS page record; got "
                f"src={public_image_src!r}"
            )
        finally:
            try:
                anon_context.close()
            except Exception:  # noqa: BLE001 -- cleanup must never mask the real result
                pass
        # No TEST_OWNED restore (2026-10-13): the test stops at the NOT APPLICABLE
        # guard before its first write, so there is nothing to put back.


@allure.epic("About Us")
@allure.feature("Chamber's Law")
@allure.story("CMS authoring / admin")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Verify that replacing the Content Image updates the image shown on the website")
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.regression
@pytest.mark.functional_high
@pytest.mark.pbi_129394
@pytest.mark.tc_134883
@pytest.mark.traceability("134883")
@allure.label("pbi", "129394")
@allure.label("testcase", "134883")
@CHAMBERS_LAW_XDIST_GROUP
def test_chambers_law_cp_134883_replacing_the_content_image_updates_the_image_shown_on_the_website(page, browser, tmp_path):
    # RETARGETED BACK onto the page record's **Content Image** 2026-09-15 --
    # see tc_134882's comment block. Unlike that case (first-time set), this
    # one is a REPLACE, so the new file is selected straight over the
    # existing one: no remove, no two-phase step (confirmed live that a
    # direct replace persists in ONE save, which is exactly what the
    # widget's own "Select File only if you want to REPLACE it" help text
    # describes).
    # DISCLOSED: the case's literal `lawbook-new.jpg` is not the target; the
    # replacement is an existing Documents & Media file picked via Select
    # File (`a11y_panel.png`, confirmed live at the picker root 2026-09-15).
    # TEST_OWNED: original bytes are downloaded before mutating and restored
    # in `finally`, then VERIFIED (re-upload makes a fresh document -- byte
    # identical, possibly "(1)"-suffixed, so the verifier matches the stem).
    # XDIST: now carries @CHAMBERS_LAW_XDIST_GROUP -- it did not before, and
    # ran concurrently with the other tests against the same shared records.
    # CHANGED 2026-10-13: `a11y_panel.png` was picked from the Documents &
    # Media picker root, where files of that kind are no longer listed (the
    # sibling 134882 timed out on its root pick and left the REAL page with no
    # image). The replacement is now uploaded from disk: the page's own
    # picture bytes (PAGE_BACKUP_IMAGE) under a NEW name, so the public src
    # must change while visitors see the same picture. The record is edited
    # IN PLACE (a Published record's Publish puts the change live, no
    # Unpublish), and `finally` uploads the original back as
    # `chamber-laws-content.png` and re-publishes, verified.
    admin = ChambersLawAdminPage(page)
    replacement_file = "chamber-laws-replacement.png"
    replacement_path = tmp_path / replacement_file
    replacement_path.write_bytes(PAGE_BACKUP_IMAGE.read_bytes())
    baseline_status = None
    original_filename = ""
    original_saved = False
    original_download_path = None

    with _page_end_published(admin, "134883"):
        anon_context = new_context(browser, use_auth_state=False)
        anon_page = anon_context.new_page()

        try:
            with allure.step("Open the page record, which already has a Content Image set"):
                authoring = admin.open_page_record()
                baseline_status = authoring.current_status()
                original_filename = authoring.current_file_name(
                    admin.CONTENT_IMAGE_UPLOAD_LABEL
                )
                assert original_filename, (
                    "precondition failed: this case needs a record that ALREADY has a "
                    "Content Image set, but the field is empty"
                )
                original_download_path = str(tmp_path / original_filename)
                original_saved = bool(
                    authoring.download_current_file(
                        admin.CONTENT_IMAGE_UPLOAD_LABEL, original_download_path
                    )
                )

            with allure.step("Capture the image the public page currently serves"):
                cl = ChambersLawPage(anon_page)
                cl.open_chambers_law()
                image_src_before = cl.intro_image_src()

            with allure.step(f"Replace the Content Image with '{replacement_file}' and publish"):
                block_live_singleton_write(PAGE_RECORD, "replace + publish the Content Image")
                authoring = admin.open_page_record()
                authoring.upload_file(admin.CONTENT_IMAGE_UPLOAD_LABEL, str(replacement_path))
                log_live_write(PAGE_RECORD, "Content Image", replacement_file, "134883", action="upload",
                               note="replacement = the page's own picture under a new name; put back in finally")
                _publish_and_confirm(authoring)

            with allure.step("Open the public page after the standard cache refresh and read the intro image"):
                expected_stem = replacement_file.rsplit(".", 1)[0]

                def _image_replaced() -> bool:
                    cl.open_chambers_law()
                    return expected_stem in cl.intro_image_src()

                _reflects_public(
                    _image_replaced,
                    timeout=PUBLIC_REFLECT_AFTER_PUBLISH_TIMEOUT,
                    message="the public intro image never reflected the replacement Content Image",
                )
                image_src_after = cl.intro_image_src()

            # Assert
            assert authoring.current_status() == STATUS_PUBLISHED
            assert expected_stem in image_src_after, (
                f"expected the page to serve {replacement_file!r}; got {image_src_after!r}"
            )
            assert image_src_after != image_src_before, (
                "expected the page to STOP serving the previous image, but src is unchanged"
            )
        finally:
            try:
                anon_context.close()
            except Exception:  # noqa: BLE001 -- cleanup must never mask the real result
                pass
            # 2026-10-13 opt-in: the page's own picture goes back before the test ends.
            _put_back_content_image(admin, tmp_path, "134883")


@allure.epic("About Us")
@allure.feature("Chamber's Law")
@allure.story("CMS authoring / admin")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("Verify that creating a law entry publishes a new card to the website")
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.regression
@pytest.mark.functional_high
@pytest.mark.pbi_129394
@pytest.mark.tc_134884
@pytest.mark.traceability("134884")
@allure.label("pbi", "129394")
@allure.label("testcase", "134884")
@CHAMBERS_LAW_XDIST_GROUP
def test_chambers_law_cp_134884_creating_a_law_entry_publishes_a_new_card_to_the_website(page, browser):
    # CORRECTLY on **Law Entry** -- creating a law card is Law Entry work.
    # Unchanged in target by the 2026-09-15 rework.
    #
    # LOCATOR BUG FIXED 2026-09-15 (this is why the test failed, not the
    # product): the Arabic half of every bilingual field is REQUIRED, and
    # the required-field asterisk is part of the rendered <label> and
    # therefore part of the ACCESSIBLE NAME. Live:
    #     actual accessible name : 'Law Number — العربية *'
    #     old lookup             : 'Law Number — العربية'  -> 0 matches
    # `ARABIC_SUFFIX` + `fill_text()`'s `exact=True` could not match. Note
    # the ENGLISH fields are NOT required (no asterisk), so simply appending
    # " *" to ARABIC_SUFFIX would have broken the English half instead. The
    # fix is in the lookup: `ObjectAuthoringPage.label_pattern()` matches an
    # ANCHORED label with an OPTIONAL trailing " *", and every role-based
    # field accessor on that class now uses it -- so both objects' bilingual
    # fields resolve, in both shapes, without any test-side special-casing.
    # (`Intro Content — العربية` on the page object carries no asterisk at
    # all, which is why the tolerance has to be optional rather than
    # mandatory.)
    #
    # DISCLOSED DATA CHANGE -- the case's literal payload cannot be used.
    # It says to CREATE an entry with Law Number "Law No. 11 of 1996" /
    # title "Amending Certain Provisions of Law No. 11 of 1990", but that
    # record ALREADY EXISTS as real, pre-existing editorial content
    # (QCDEMO-129394-law-11-1996, confirmed live). Executing the case
    # literally would publish a DUPLICATE card of a real law onto the live
    # public page. A clearly-marked QCTEST payload is created instead, which
    # tests the same behaviour (a new entry publishes a new card) without
    # duplicating real content. The case should be reworded to use test data
    # -- escalated to the QA Manager.
    #
    # DATA POLICY: the created entry is NEVER deleted (standards.md ->
    # Destructive Operations, plus the standing "leave newly-created test
    # entries in place" instruction). To take the test card off the live
    # page without losing the record, its activeStatus is un-ticked at the
    # end -- the guide's own documented way to hide content. That cleanup
    # now runs through _test_owned_reset(), which retries and then RE-READS
    # the record to prove the card really is hidden: when it silently
    # failed on 2026-09-09 it left a PUBLISHED QCTEST card on the live
    # public page, twice.
    # IDEMPOTENCY: the payload carries a per-run timestamp suffix. With a
    # FIXED title, a rerun would either be refused as a duplicate name or
    # add an indistinguishable second row next to the one the previous run
    # created (and which policy forbids deleting). Consequence, disclosed
    # deliberately: each run leaves one more hidden QCTEST row behind. They
    # are never public (activeStatus is un-ticked at the end) but they DO
    # accumulate in the CMS list -- worth an occasional human bulk tidy-up,
    # a conscious trade against the never-delete-on-shared-content rule.
    import time as _time

    admin = ChambersLawAdminPage(page)
    run_id = _time.strftime("%m%d-%H%M%S")
    # QCTEST-<tc_id>-* naming (CLAUDE.md #8), unique per run.
    qc_number = f"QCTEST-134884 Law No. 99 of 2026 ({run_id})"
    qc_title = f"QCTEST-134884-LAW-{run_id} Automated Law Entry"
    qc_desc = f"QCTEST-134884 created by automated test tc_134884 run {run_id}."
    created = False

    anon_context = new_context(browser, use_auth_state=False)
    anon_page = anon_context.new_page()

    try:
        with allure.step("Open the Law Entry list and confirm existing entries are listed"):
            entries = admin.open_law_entries_list()
            assert entries.row_visible(LAW_1990_TITLE), (
                "expected the existing law entries to be listed before creating a new one"
            )

        with allure.step("Create a new law entry (QCTEST payload -- see disclosed data change) and publish it"):
            authoring = admin.open_new_law_entry_form()
            authoring.fill_text(admin.LAW_NUMBER_LABEL, qc_number)
            authoring.fill_text(admin.LAW_NUMBER_LABEL + admin.ARABIC_SUFFIX, qc_number)
            authoring.fill_text(admin.LAW_TITLE_LABEL, qc_title)
            authoring.fill_text(admin.LAW_TITLE_LABEL + admin.ARABIC_SUFFIX, qc_title)
            authoring.fill_text(admin.LAW_DESCRIPTION_LABEL, qc_desc)
            authoring.fill_text(admin.LAW_DESCRIPTION_LABEL + admin.ARABIC_SUFFIX, qc_desc)
            authoring.fill_text(admin.EXTERNAL_LINK_URL_LABEL, "https://www.almeezan.qa/")
            # displayOrder in multiples of 100, LAST in the list (guide's
            # ordering convention -- never an in-between value).
            authoring.fill_number(admin.DISPLAY_ORDER_LABEL, "900")
            authoring.set_checkbox(admin.ACTIVE_STATUS_LABEL, True)
            authoring.select_existing_file(
                admin.LAW_ICON_UPLOAD_LABEL,
                "qc-social-linkedin.svg",
                folder="QC Footer Social Icons",
            )
            log_live_write(_law_record(qc_title), "<create>", qc_title, "134884", action="create",
                           note="active, display order 900, published; hidden (never deleted) in finally")
            authoring.submit_for_publishing()
            created = True

        with allure.step("Confirm the new entry appears in the Law Entry list AND really published"):
            # The create's own form settle is ~2.5s while the publish takes
            # 27-30s live (see this module's measured timings), so neither
            # the row's presence nor its Approved status may be read
            # immediately -- both are polled as real conditions.
            entries = admin.open_law_entries_list()

            def _row_listed() -> bool:
                entries.open_entries_list()
                return entries.row_visible(qc_title)

            wait_until(
                _row_listed,
                timeout=PUBLISH_CONFIRM_TIMEOUT,
                poll=3.0,
                message="the newly-created law entry never appeared in the CMS Law Entry list",
            )
            row_listed = entries.row_visible(qc_title)
            # Title-keyed Edit link (Law Entry's Entry column renders the Law
            # Title), which also gives the new record's code to
            # wait_for_status()/reopen().
            created_entry = entries.open_entry_by_edit_link(qc_title)
            created_entry.wait_for_status(STATUS_PUBLISHED, timeout=PUBLISH_CONFIRM_TIMEOUT)

        with allure.step("Open the public Chamber's Law page after the standard cache refresh"):
            cl = ChambersLawPage(anon_page)

            def _new_card_present() -> bool:
                cl.open_chambers_law()
                return cl.is_card_visible(qc_number)

            _reflects_public(
                _new_card_present,
                timeout=PUBLIC_REFLECT_AFTER_PUBLISH_TIMEOUT,
                message="Public page never rendered a card for the newly-created law entry",
            )
            new_card_visible = cl.is_card_visible(qc_number)
            new_card_title = cl.card_title_text(qc_number)

        # Assert
        assert row_listed, "expected the new entry to appear in the CMS Law Entry list"
        assert created_entry.current_status() == STATUS_PUBLISHED, (
            "expected the newly-created law entry to reach the published/Approved state"
        )
        assert new_card_visible, (
            "expected a new card to render in Official Legal References for the "
            "newly-created, published law entry"
        )
        assert new_card_title == qc_title
    finally:
        try:
            anon_context.close()
        except Exception:  # noqa: BLE001 -- cleanup must never mask the real result
            pass
        if created:
            def _hide_qctest_entry():
                # TITLE-keyed via the row's own Edit link. An earlier version
                # used find_entry_code_by_field() + open_law_entry(code),
                # which is wrong for this object twice over: that helper is
                # documented for objects whose Entry column does NOT render
                # the real field value, whereas Law Entry's Entry column DOES
                # render the Law Title -- and it opens every row's form in
                # turn to find a match. It failed to resolve the code, so
                # this cleanup never ran and left a PUBLISHED QCTEST card on
                # the live public page twice (2026-09-09).
                entries = admin.open_law_entries_list()
                if not entries.row_visible(qc_title):
                    raise AssertionError(
                        f"cannot hide the QCTEST entry {qc_title!r} -- its row is "
                        "not listed"
                    )
                authoring = entries.open_entry_by_edit_link(qc_title)
                # Edited in place (2026-10-13) -- see _hide_law_entry().
                authoring.set_checkbox(admin.ACTIVE_STATUS_LABEL, False)
                log_live_write(_law_record(qc_title), "Active Status", False, "134884", action="status",
                               note="hide the kept QCTEST card from the public page")
                _publish_and_confirm(authoring)
                # PROVE the card really is hidden, never assume.
                authoring = admin.open_law_entries_list().open_entry_by_edit_link(qc_title)
                if authoring.is_checked(admin.ACTIVE_STATUS_LABEL) is not False:
                    raise AssertionError(
                        "the QCTEST entry's Active Status did not commit to False -- "
                        "a QCTEST card may still be live on the public page"
                    )

            with allure.step("DATA POLICY -- hide the QCTEST entry (activeStatus off), never delete it"):
                _test_owned_reset(
                    _hide_qctest_entry,
                    label=f"tc_134884 hide QCTEST law entry {qc_title!r}",
                )


@allure.epic("About Us")
@allure.feature("Chamber's Law")
@allure.story("CMS authoring / admin")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Verify that editing a law entry updates its card on the website")
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.regression
@pytest.mark.functional_high
@pytest.mark.pbi_129394
@pytest.mark.tc_134885
@pytest.mark.traceability("134885")
@allure.label("pbi", "129394")
@allure.label("testcase", "134885")
@CHAMBERS_LAW_XDIST_GROUP
def test_chambers_law_cp_134885_editing_a_law_entry_updates_its_card_on_the_website(page, browser):
    # RETARGETED 2026-10-13 (user decision: no test writes to REAL content):
    # runs on its own disposable `QCTEST-<tc>-LAW-<uid>` Law Entry created here
    # (Published, Display Order 9900+ so it renders after every real card),
    # never on the real QCDEMO-129394-law-11-1990 / -1996 rows. The public card
    # is read in a fresh logged-out context; the row is deleted by exact title.
    admin = ChambersLawAdminPage(page)
    marker = "EDITED-129394"
    created = []
    anon_context = new_context(browser, use_auth_state=False)
    anon_page = anon_context.new_page()
    try:
        with allure.step("Create and publish a disposable, active law entry"):
            title, number = _qctest_law(admin, "134885")
            created.append(title)
            description = _open_law(admin, title).field_value(admin.LAW_DESCRIPTION_LABEL)

        with allure.step("Read the description its public card currently shows (logged out)"):
            cl = ChambersLawPage(anon_page)

            def _card_live() -> bool:
                cl.open_chambers_law()
                return cl.is_card_visible(number)

            _reflects_public(_card_live, timeout=PUBLIC_REFLECT_AFTER_PUBLISH_TIMEOUT,
                             message="the disposable law entry's card never appeared publicly")
            desc_before = cl.card_desc_text(number)

        with allure.step("Change its Law Description to include the marker and publish"):
            authoring = _open_law(admin, title)  # edited in place (2026-10-13)
            authoring.fill_text(admin.LAW_DESCRIPTION_LABEL, f"{description} {marker}")
            _publish_and_confirm(authoring)

        with allure.step("Open the public page after the standard cache refresh and read that card's description"):
            def _desc_updated() -> bool:
                cl.open_chambers_law()
                return cl.is_card_visible(number) and marker in cl.card_desc_text(number)

            _reflects_public(_desc_updated, timeout=PUBLIC_REFLECT_AFTER_PUBLISH_TIMEOUT,
                             message="Public card description never reflected the edited Law Description")
            desc_after = cl.card_desc_text(number)

        assert authoring.current_status() == STATUS_PUBLISHED
        assert marker in desc_after
        assert desc_after != desc_before, "expected the card description to change from its previous text"
    finally:
        try:
            anon_context.close()
        except Exception:  # noqa: BLE001 -- cleanup must never mask the real result
            pass
        _delete_disposable_laws(admin, created, "134885")


@allure.epic("About Us")
@allure.feature("Chamber's Law")
@allure.story("CMS authoring / admin")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Verify that reordering law entries changes the card sequence on the website")
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.regression
@pytest.mark.functional_high
@pytest.mark.pbi_129394
@pytest.mark.tc_134886
@pytest.mark.traceability("134886")
@allure.label("pbi", "129394")
@allure.label("testcase", "134886")
@CHAMBERS_LAW_XDIST_GROUP
def test_chambers_law_cp_134886_reordering_law_entries_changes_the_card_sequence_on_the_website(page, browser):
    # RETARGETED 2026-10-13 (user decision: no test writes to REAL content):
    # runs on its own disposable `QCTEST-<tc>-LAW-<uid>` Law Entry created here
    # (Published, Display Order 9900+ so it renders after every real card),
    # never on the real QCDEMO-129394-law-11-1990 / -1996 rows. The public card
    # is read in a fresh logged-out context; the row is deleted by exact title.
    # Two disposable rows, A (Display Order 9910) and B (9920), are reordered
    # RELATIVE TO EACH OTHER (A -> 9930), so B must render before A. Display
    # Order stays in multiples of 10 within 9900+ (the guide's 100-step
    # convention governs real content; these rows always sort after it).
    admin = ChambersLawAdminPage(page)
    created = []
    anon_context = new_context(browser, use_auth_state=False)
    anon_page = anon_context.new_page()

    def _order(nums, first, second):
        return nums.index(first) < nums.index(second) if first in nums and second in nums else None

    try:
        with allure.step("Create and publish two disposable, active law entries: A (9910) and B (9920)"):
            title_a, number_a = _qctest_law(admin, "134886", display_order="9910")
            created.append(title_a)
            title_b, number_b = _qctest_law(admin, "134886", display_order="9920")
            created.append(title_b)

        with allure.step("Confirm the public page (logged out) renders A before B"):
            cl = ChambersLawPage(anon_page)

            def _a_first() -> bool:
                cl.open_chambers_law()
                return _order([n.strip() for n in cl.card_numbers()], number_a, number_b) is True

            _reflects_public(_a_first, timeout=PUBLIC_REFLECT_AFTER_PUBLISH_TIMEOUT,
                             message="precondition: the two QCTEST cards never rendered A before B")
            order_before = [n.strip() for n in cl.card_numbers()]

        with allure.step("Move A after B (Display Order 9930) and publish"):
            authoring = _open_law(admin, title_a)  # edited in place (2026-10-13)
            authoring.fill_number(admin.DISPLAY_ORDER_LABEL, "9930")
            _publish_and_confirm(authoring)

        with allure.step("Open the public page after the standard cache refresh and read the card order"):
            def _b_first() -> bool:
                cl.open_chambers_law()
                return _order([n.strip() for n in cl.card_numbers()], number_b, number_a) is True

            _reflects_public(_b_first, timeout=PUBLIC_REFLECT_AFTER_PUBLISH_TIMEOUT,
                             message="Public card order never reflected the changed Display Order")
            order_after = [n.strip() for n in cl.card_numbers()]

        _attach("card order", {"before": order_before, "after": order_after})
        assert _order(order_after, number_b, number_a) is True, (
            f"expected B to render before A after the reorder; got {order_after} (before: {order_before})"
        )
    finally:
        try:
            anon_context.close()
        except Exception:  # noqa: BLE001 -- cleanup must never mask the real result
            pass
        _delete_disposable_laws(admin, created, "134886")


@allure.epic("About Us")
@allure.feature("Chamber's Law")
@allure.story("CMS authoring / admin")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("Verify that deactivating a law entry hides its card from the website")
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.regression
@pytest.mark.functional_high
@pytest.mark.pbi_129394
@pytest.mark.tc_134887
@pytest.mark.traceability("134887")
@allure.label("pbi", "129394")
@allure.label("testcase", "134887")
@CHAMBERS_LAW_XDIST_GROUP
def test_chambers_law_cp_134887_deactivating_a_law_entry_hides_its_card_from_the_website(page, browser):
    # RETARGETED 2026-10-13 (user decision: no test writes to REAL content):
    # runs on its own disposable `QCTEST-<tc>-LAW-<uid>` Law Entry created here
    # (Published, Display Order 9900+ so it renders after every real card),
    # never on the real QCDEMO-129394-law-11-1990 / -1996 rows. The public card
    # is read in a fresh logged-out context; the row is deleted by exact title.
    admin = ChambersLawAdminPage(page)
    created = []
    anon_context = new_context(browser, use_auth_state=False)
    anon_page = anon_context.new_page()
    try:
        with allure.step("Create and publish a disposable, ACTIVE law entry; its card is visible publicly"):
            title, number = _qctest_law(admin, "134887")
            created.append(title)
            cl = ChambersLawPage(anon_page)

            def _card_live() -> bool:
                cl.open_chambers_law()
                return cl.is_card_visible(number)

            _reflects_public(_card_live, timeout=PUBLIC_REFLECT_AFTER_PUBLISH_TIMEOUT,
                             message="precondition: the disposable card never appeared publicly")

        with allure.step("Set its Active Status to False and publish"):
            authoring = _open_law(admin, title)  # edited in place (2026-10-13)
            authoring.set_checkbox(admin.ACTIVE_STATUS_LABEL, False)
            _publish_and_confirm(authoring)

        with allure.step("Open the public page after the standard cache refresh"):
            def _card_hidden() -> bool:
                cl.open_chambers_law()
                return not cl.is_card_visible(number)

            _reflects_public(_card_hidden, timeout=PUBLIC_REFLECT_AFTER_PUBLISH_TIMEOUT,
                             message="Deactivated law entry card was still rendering publicly")
            hidden = not cl.is_card_visible(number)
            other_cards = [n.strip() for n in cl.card_numbers()]  # read-only: the real cards

        with allure.step("Re-open the Law Entry list in the CMS"):
            row_still_listed = admin.open_law_entries_list(locale="en").row_visible(title)
            active_in_cms = _open_law(admin, title).is_checked(admin.ACTIVE_STATUS_LABEL)

        assert hidden, "expected the deactivated card to stop rendering on the public page"
        assert other_cards, "expected the remaining active cards to keep rendering"
        assert row_still_listed, "expected the law entry record to remain present in the CMS Law Entry list"
        assert active_in_cms is False, "expected Active Status to remain False in the CMS"
    finally:
        try:
            anon_context.close()
        except Exception:  # noqa: BLE001 -- cleanup must never mask the real result
            pass
        _delete_disposable_laws(admin, created, "134887")


@allure.epic("About Us")
@allure.feature("Chamber's Law")
@allure.story("CMS authoring / admin")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Verify that reactivating a law entry restores its card to the website")
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.regression
@pytest.mark.functional_high
@pytest.mark.pbi_129394
@pytest.mark.tc_134888
@pytest.mark.traceability("134888")
@allure.label("pbi", "129394")
@allure.label("testcase", "134888")
@CHAMBERS_LAW_XDIST_GROUP
def test_chambers_law_cp_134888_reactivating_a_law_entry_restores_its_card_to_the_website(page, browser):
    # RETARGETED 2026-10-13 (user decision: no test writes to REAL content):
    # runs on its own disposable `QCTEST-<tc>-LAW-<uid>` Law Entry created here
    # (Published, Display Order 9900+ so it renders after every real card),
    # never on the real QCDEMO-129394-law-11-1990 / -1996 rows. The public card
    # is read in a fresh logged-out context; the row is deleted by exact title.
    # The precondition (Active Status False, card absent) is the disposable
    # row's own creation state: it is published INACTIVE.
    admin = ChambersLawAdminPage(page)
    created = []
    display_order = "9900"
    anon_context = new_context(browser, use_auth_state=False)
    anon_page = anon_context.new_page()
    try:
        with allure.step("Create and publish a disposable law entry with Active Status False; its card is absent"):
            title, number = _qctest_law(admin, "134888", active=False, display_order=display_order)
            created.append(title)
            cl = ChambersLawPage(anon_page)
            cl.open_chambers_law()
            absent_before = not cl.is_card_visible(number)

        with allure.step("Set Active Status to True and publish"):
            authoring = _open_law(admin, title)  # edited in place (2026-10-13)
            authoring.set_checkbox(admin.ACTIVE_STATUS_LABEL, True)
            _publish_and_confirm(authoring)

        with allure.step("Open the public page after the standard cache refresh and read the card list"):
            def _card_back() -> bool:
                cl.open_chambers_law()
                return cl.is_card_visible(number)

            _reflects_public(_card_back, timeout=PUBLIC_REFLECT_AFTER_PUBLISH_TIMEOUT,
                             message="Reactivated law entry card never returned to the public page")
            order_after = [n.strip() for n in cl.card_numbers()]

        assert absent_before, "precondition: the INACTIVE disposable card was already rendering publicly"
        assert number in order_after, "expected the reactivated card to render in Official Legal References"
        # "at the position given by its Display Order": 9900 is above every
        # real entry's order, so the card must render after every other card.
        assert order_after[-1] == number, (
            f"expected the reactivated card (Display Order {display_order}) last; got {order_after}"
        )
    finally:
        try:
            anon_context.close()
        except Exception:  # noqa: BLE001 -- cleanup must never mask the real result
            pass
        _delete_disposable_laws(admin, created, "134888")


@allure.epic("About Us")
@allure.feature("Chamber's Law")
@allure.story("CMS authoring / admin")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Verify that a valid English Page Title is accepted and saved")
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.functional_low
@pytest.mark.pbi_129394
@pytest.mark.tc_134889
@pytest.mark.traceability("134889")
@allure.label("pbi", "129394")
@allure.label("testcase", "134889")
@CHAMBERS_LAW_XDIST_GROUP
def test_chambers_law_cp_134889_a_valid_english_page_title_is_accepted_and_saved(page):
    _case_valid_text(page, "134889", "page_title", "en", "Chamber's Law")


@allure.epic("About Us")
@allure.feature("Chamber's Law")
@allure.story("CMS authoring / admin")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Verify that an empty English Page Title is rejected with the page-title-required message")
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.functional_low
@pytest.mark.pbi_129394
@pytest.mark.tc_134890
@pytest.mark.traceability("134890")
@allure.label("pbi", "129394")
@allure.label("testcase", "134890")
@CHAMBERS_LAW_XDIST_GROUP
def test_chambers_law_cp_134890_an_empty_english_page_title_is_rejected_with_the_page_title_required_message(page):
    _case_rejected_text(page, "134890", "page_title", "en", "", ui_locales=("en", "ar"))


@allure.epic("About Us")
@allure.feature("Chamber's Law")
@allure.story("CMS authoring / admin")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Verify that the English Page Title accepts exactly 100 characters and rejects 101")
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.functional_low
@pytest.mark.pbi_129394
@pytest.mark.tc_134891
@pytest.mark.traceability("134891")
@allure.label("pbi", "129394")
@allure.label("testcase", "134891")
@pytest.mark.skip(reason="Field-level validation case (Verify that the English Page Title accepts exactly 100 characters and rejects 101) is the SAFE category this batch was authorized to automate (validation fires before any persistent write, or the check+revert is reversible) -- but it requires reaching the Chamber's Law page/law-entry admin edit form in the Liferay Control Panel to interact with the field at all. This session's login attempt against qcdev (CmsLoginPage.login() via TEST_USER/TEST_PASSWORD, mirroring the navigation pattern already proven for the Departments and Board of Directors admin surfaces) timed out repeatedly (playwright._impl._errors.TimeoutError on the username-field fill, and on core/web/session_guard.py's re-authentication retries) -- consistent with the severe qcdev session/connection-limit flakiness already documented in login_page.py and org_structure_admin_page.py, but worse this session (login itself never completed). No stable locators for the Chamber's Law admin edit form (list/edit URL, per-field selectors) could be extracted or confirmed as a result. Skipped rather than invented -- see module docstring.")
def test_chambers_law_cp_134891_the_english_page_title_accepts_exactly_100_characters_and_rejects_101(page):
    ...


@allure.epic("About Us")
@allure.feature("Chamber's Law")
@allure.story("CMS authoring / admin")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Verify that a whitespace-only English Page Title is rejected on save")
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.functional_low
@pytest.mark.pbi_129394
@pytest.mark.tc_134892
@pytest.mark.traceability("134892")
@allure.label("pbi", "129394")
@allure.label("testcase", "134892")
@pytest.mark.skip(reason="Field-level validation case (Verify that a whitespace-only English Page Title is rejected on save) is the SAFE category this batch was authorized to automate (validation fires before any persistent write, or the check+revert is reversible) -- but it requires reaching the Chamber's Law page/law-entry admin edit form in the Liferay Control Panel to interact with the field at all. This session's login attempt against qcdev (CmsLoginPage.login() via TEST_USER/TEST_PASSWORD, mirroring the navigation pattern already proven for the Departments and Board of Directors admin surfaces) timed out repeatedly (playwright._impl._errors.TimeoutError on the username-field fill, and on core/web/session_guard.py's re-authentication retries) -- consistent with the severe qcdev session/connection-limit flakiness already documented in login_page.py and org_structure_admin_page.py, but worse this session (login itself never completed). No stable locators for the Chamber's Law admin edit form (list/edit URL, per-field selectors) could be extracted or confirmed as a result. Skipped rather than invented -- see module docstring.")
def test_chambers_law_cp_134892_a_whitespace_only_english_page_title_is_rejected_on_save(page):
    ...


@allure.epic("About Us")
@allure.feature("Chamber's Law")
@allure.story("CMS authoring / admin")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Verify that a valid Arabic Page Title is accepted and saved")
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.functional_low
@pytest.mark.pbi_129394
@pytest.mark.tc_134893
@pytest.mark.traceability("134893")
@allure.label("pbi", "129394")
@allure.label("testcase", "134893")
@CHAMBERS_LAW_XDIST_GROUP
def test_chambers_law_cp_134893_a_valid_arabic_page_title_is_accepted_and_saved(page):
    _case_valid_text(page, "134893", "page_title", "ar", "قانون الغرفة")


@allure.epic("About Us")
@allure.feature("Chamber's Law")
@allure.story("CMS authoring / admin")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("Verify that a missing Arabic Page Title is rejected with the Arabic-title-required message")
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.functional_low
@pytest.mark.pbi_129394
@pytest.mark.tc_134894
@pytest.mark.traceability("134894")
@allure.label("pbi", "129394")
@allure.label("testcase", "134894")
@CHAMBERS_LAW_XDIST_GROUP
def test_chambers_law_cp_134894_a_missing_arabic_page_title_is_rejected_with_the_arabic_title_required_message(page):
    _case_rejected_text(page, "134894", "page_title", "ar", "", ui_locales=("en", "ar"))


@allure.epic("About Us")
@allure.feature("Chamber's Law")
@allure.story("CMS authoring / admin")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Verify that the Arabic Page Title accepts exactly 100 characters and rejects 101")
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.functional_low
@pytest.mark.pbi_129394
@pytest.mark.tc_134895
@pytest.mark.traceability("134895")
@allure.label("pbi", "129394")
@allure.label("testcase", "134895")
@pytest.mark.skip(reason="Field-level validation case (Verify that the Arabic Page Title accepts exactly 100 characters and rejects 101) is the SAFE category this batch was authorized to automate (validation fires before any persistent write, or the check+revert is reversible) -- but it requires reaching the Chamber's Law page/law-entry admin edit form in the Liferay Control Panel to interact with the field at all. This session's login attempt against qcdev (CmsLoginPage.login() via TEST_USER/TEST_PASSWORD, mirroring the navigation pattern already proven for the Departments and Board of Directors admin surfaces) timed out repeatedly (playwright._impl._errors.TimeoutError on the username-field fill, and on core/web/session_guard.py's re-authentication retries) -- consistent with the severe qcdev session/connection-limit flakiness already documented in login_page.py and org_structure_admin_page.py, but worse this session (login itself never completed). No stable locators for the Chamber's Law admin edit form (list/edit URL, per-field selectors) could be extracted or confirmed as a result. Skipped rather than invented -- see module docstring.")
def test_chambers_law_cp_134895_the_arabic_page_title_accepts_exactly_100_characters_and_rejects_101(page):
    ...


@allure.epic("About Us")
@allure.feature("Chamber's Law")
@allure.story("CMS authoring / admin")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Verify that a whitespace-only Arabic Page Title is rejected on save")
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.functional_low
@pytest.mark.pbi_129394
@pytest.mark.tc_134896
@pytest.mark.traceability("134896")
@allure.label("pbi", "129394")
@allure.label("testcase", "134896")
@pytest.mark.skip(reason="Field-level validation case (Verify that a whitespace-only Arabic Page Title is rejected on save) is the SAFE category this batch was authorized to automate (validation fires before any persistent write, or the check+revert is reversible) -- but it requires reaching the Chamber's Law page/law-entry admin edit form in the Liferay Control Panel to interact with the field at all. This session's login attempt against qcdev (CmsLoginPage.login() via TEST_USER/TEST_PASSWORD, mirroring the navigation pattern already proven for the Departments and Board of Directors admin surfaces) timed out repeatedly (playwright._impl._errors.TimeoutError on the username-field fill, and on core/web/session_guard.py's re-authentication retries) -- consistent with the severe qcdev session/connection-limit flakiness already documented in login_page.py and org_structure_admin_page.py, but worse this session (login itself never completed). No stable locators for the Chamber's Law admin edit form (list/edit URL, per-field selectors) could be extracted or confirmed as a result. Skipped rather than invented -- see module docstring.")
def test_chambers_law_cp_134896_a_whitespace_only_arabic_page_title_is_rejected_on_save(page):
    ...


@allure.epic("About Us")
@allure.feature("Chamber's Law")
@allure.story("CMS authoring / admin")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Verify that a valid JPG Hero Banner under 2 MB is accepted")
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.functional_low
@pytest.mark.pbi_129394
@pytest.mark.tc_134897
@pytest.mark.traceability("134897")
@allure.label("pbi", "129394")
@allure.label("testcase", "134897")
@CHAMBERS_LAW_XDIST_GROUP
def test_chambers_law_cp_134897_a_valid_jpg_hero_banner_under_2_mb_is_accepted(page):
    admin = ChambersLawAdminPage(page)
    path = _fixture("hero.jpg", make_jpg, 900 * 1024)
    with _hero_end_published(admin, "134897"):
        with allure.step("Open the chamber-laws hero record and upload hero.jpg (JPG, 900 KB) to the Hero Banner field"):
            authoring = _open_real_hero(admin)
            authoring.upload_file(admin.HERO_IMAGE_UPLOAD_LABEL, path)
        with allure.step("Click Save (Publish on this published record)"):
            block_live_singleton_write(HERO_RECORD, "save of a valid hero.jpg")
            said = _publish_edit(admin, authoring)
            _attach("save outcome", said)
        with allure.step("Reload the record"):
            name = _hero_stored(admin, lambda a: a.hero_banner_file_name(),
                                lambda v: bool(_HERO_JPG.match(v or "")))
        assert not said["refusal"], f"the upload/save was refused: {said['refusal']!r}"
        assert _HERO_JPG.match(name or ""), f"the Hero Banner field shows {name!r}, expected hero.jpg"


@allure.epic("About Us")
@allure.feature("Chamber's Law")
@allure.story("CMS authoring / admin")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Verify that a Hero Banner in an unsupported format is rejected with the Hero Banner format message")
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.functional_low
@pytest.mark.pbi_129394
@pytest.mark.tc_134898
@pytest.mark.traceability("134898")
@allure.label("pbi", "129394")
@allure.label("testcase", "134898")
@CHAMBERS_LAW_XDIST_GROUP
def test_chambers_law_cp_134898_a_hero_banner_in_an_unsupported_format_is_rejected_with_the_hero_banner_format_m(page):
    admin = ChambersLawAdminPage(page)
    path = _fixture("hero.gif", make_gif, 500 * 1024)
    outcomes = {}
    for ui in ("en", "ar"):
        with allure.step(f"[{ui.upper()} interface] Upload hero.gif (GIF, 500 KB) to the Hero Banner field"):
            authoring = _open_real_hero(admin, locale=ui)
            before = admin.hero_banner_file_name()
            outcomes[ui] = _attempt_upload(admin, authoring, "ObjectField_bannerImage", path)
            outcomes[ui]["stored_before"] = before
            outcomes[ui]["stored_after"] = admin.hero_banner_file_name()
    _attach("picker outcomes (wording recorded, not asserted)", outcomes)
    for ui, outcome in outcomes.items():
        assert outcome["rejected"], (
            f"[{ui}] the GIF Hero Banner was not rejected (accepted={outcome['accepted']}; "
            f"text={outcome['picker_text'][:300]!r})"
        )
        assert outcome["stored_after"] == outcome["stored_before"], (
            f"[{ui}] the stored Hero Banner changed: {outcome['stored_before']!r} -> {outcome['stored_after']!r}"
        )


@allure.epic("About Us")
@allure.feature("Chamber's Law")
@allure.story("CMS authoring / admin")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Verify that a Hero Banner above 2 MB is rejected at the size boundary")
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.functional_low
@pytest.mark.pbi_129394
@pytest.mark.tc_134899
@pytest.mark.traceability("134899")
@allure.label("pbi", "129394")
@allure.label("testcase", "134899")
@CHAMBERS_LAW_XDIST_GROUP
def test_chambers_law_cp_134899_a_hero_banner_above_2_mb_is_rejected_at_the_size_boundary(page):
    # File-size tolerance (project rule): up to 3 MB accepted is OK even where the
    # PBI says 2 MB; above 3 MB accepted is a defect. So the 2.1 MB file is
    # RECORDED and a 3.1 MB file is the asserted rejection boundary. The picker
    # uploads any size; the field applies its limit when the file is ADDED.
    admin = ChambersLawAdminPage(page)
    exact = _fixture("hero-2mb.jpg", make_jpg, 2 * ONE_MB)
    over = _fixture("hero-oversize.jpg", make_jpg, int(2.1 * ONE_MB))
    far_over = _fixture("hero-oversize-3mb.jpg", make_jpg, int(3.1 * ONE_MB))
    with _hero_end_published(admin, "134899"):
        outcomes = {}
        with allure.step("Upload hero-2mb.jpg (exactly 2 MB) to the Hero Banner field and click Save"):
            authoring = _open_real_hero(admin)
            authoring.upload_file(admin.HERO_IMAGE_UPLOAD_LABEL, exact)
            # The boundary case starts with a SUCCESSFUL 2 MB save (2026-10-13).
            block_live_singleton_write(HERO_RECORD, "save of the exactly-2 MB hero image")
            said = _publish_edit(admin, authoring)
            stored = _hero_stored(admin, lambda a: a.hero_banner_file_name(),
                                  lambda v: (v or "").startswith("hero-2mb"))
        with allure.step("Upload hero-oversize.jpg (2.1 MB) -- recorded under the 3 MB tolerance"):
            authoring = _open_real_hero(admin)
            outcomes["2.1MB"] = _attempt_upload(admin, authoring, "ObjectField_bannerImage", over,
                                                size_only=True, add_if_accepted=True)
        for ui in ("en", "ar"):
            with allure.step(f"[{ui.upper()} interface] Upload a 3.1 MB JPG -- must be rejected"):
                authoring = _open_real_hero(admin, locale=ui)
                outcomes[f"3.1MB-{ui}"] = _attempt_upload(
                    admin, authoring, "ObjectField_bannerImage", far_over, size_only=True,
                    add_if_accepted=True,
                )
        with allure.step("Reload the record -- the stored image is unchanged"):
            authoring = _open_real_hero(admin)
            after = authoring.current_file_name(admin.HERO_IMAGE_UPLOAD_LABEL)
        _attach("outcomes", {"2MB save": said, **outcomes})
        assert (stored or "").startswith("hero-2mb"), (
            f"the exactly-2 MB Hero Banner was not saved (stored {stored!r}; {said!r})"
        )
        for ui in ("en", "ar"):
            assert outcomes[f"3.1MB-{ui}"]["rejected"], f"[{ui}] a 3.1 MB Hero Banner was not rejected"
        assert after == stored, f"the stored Hero Banner changed to {after!r} after the rejected upload"


@allure.epic("About Us")
@allure.feature("Chamber's Law")
@allure.story("CMS authoring / admin")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Verify that publishing without a Hero Banner is blocked")
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.functional_low
@pytest.mark.pbi_129394
@pytest.mark.tc_134900
@pytest.mark.traceability("134900")
@allure.label("pbi", "129394")
@allure.label("testcase", "134900")
@CHAMBERS_LAW_XDIST_GROUP
def test_chambers_law_cp_134900_publishing_without_a_hero_banner_is_blocked(page):
    admin = ChambersLawAdminPage(page)
    with allure.step("Open the chamber-laws hero record with the Hero Banner field emptied, then click Publish"):
        authoring = _open_real_hero(admin)
        before_status = authoring.current_status()
        authoring.remove_current_file(admin.HERO_IMAGE_UPLOAD_LABEL)
        said = _publish_edit(admin, authoring, action="attempt",
                             note="Publish with the Hero Banner removed; expected REFUSED")
        _attach("publish outcome (wording recorded, not asserted)", said)
    with allure.step("Check the record status and stored image"):
        authoring = _open_real_hero(admin)
        image = authoring.current_file_name(admin.HERO_IMAGE_UPLOAD_LABEL)
        status = authoring.current_status()
    stop_unless_refused(bool(image) and status == before_status, HERO_RECORD,
                        "Publish with the Hero Banner removed", {"said": said, "image": image, "status": status})
    assert image, (
        "publishing WITHOUT a Hero Banner was NOT blocked: the hero record now has no image "
        f"(status {status!r}; page said {said!r})"
    )
    assert status == before_status, f"record status changed from {before_status!r} to {status!r}"


@allure.epic("About Us")
@allure.feature("Chamber's Law")
@allure.story("CMS authoring / admin")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Verify that valid Hero Banner Alt Text is accepted and saved")
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.functional_low
@pytest.mark.pbi_129394
@pytest.mark.tc_134901
@pytest.mark.traceability("134901")
@allure.label("pbi", "129394")
@allure.label("testcase", "134901")
@CHAMBERS_LAW_XDIST_GROUP
def test_chambers_law_cp_134901_valid_hero_banner_alt_text_is_accepted_and_saved(page):
    admin = ChambersLawAdminPage(page)
    expected = "Newspaper headlines background"
    with _hero_end_published(admin, "134901"):
        with allure.step(f"Open the chamber-laws hero record, enter {expected!r} in Hero Banner Alt Text and click Save"):
            authoring = _open_real_hero(admin)
            admin.fill_hero_alt_text(expected)
            native = admin.hero_alt_validation_message()
            block_live_singleton_write(HERO_RECORD, f"save of Hero Banner Alt Text {expected!r}")
            said = _publish_edit(admin, authoring)
            _attach("save outcome", said)
        with allure.step("Reload the record"):
            stored = _hero_stored(admin, lambda a: a.hero_alt_text(), lambda v: v == expected)
        assert native == "", f"the alt text raised a validation error: {native!r}"
        assert not said["refusal"], f"the save was refused: {said['refusal']!r}"
        assert stored == expected, f"Hero Banner Alt Text reads {stored!r}"


@allure.epic("About Us")
@allure.feature("Chamber's Law")
@allure.story("CMS authoring / admin")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Verify that empty Hero Banner Alt Text is rejected on save")
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.functional_low
@pytest.mark.pbi_129394
@pytest.mark.tc_134902
@pytest.mark.traceability("134902")
@allure.label("pbi", "129394")
@allure.label("testcase", "134902")
@CHAMBERS_LAW_XDIST_GROUP
def test_chambers_law_cp_134902_empty_hero_banner_alt_text_is_rejected_on_save(page):
    admin = ChambersLawAdminPage(page)
    with allure.step("Open the chamber-laws hero record with Hero Banner Alt Text populated"):
        authoring = _open_real_hero(admin)
        previous = admin.hero_alt_text()
        assert previous, "precondition: Hero Banner Alt Text is not populated"
    with allure.step("Clear Hero Banner Alt Text completely and click Save"):
        admin.fill_hero_alt_text("")
        native = admin.hero_alt_validation_message()
        said = _publish_edit(admin, authoring, action="attempt",
                             note=f"Save with an empty Hero Banner Alt Text (was {previous!r}); expected REFUSED")
        _attach("save outcome (wording recorded, not asserted)", {"native": native, **said})
    with allure.step("Reload the record"):
        authoring = _open_real_hero(admin)
        stored = admin.hero_alt_text()
    stop_unless_refused(stored == previous, HERO_RECORD, "Save with an empty Hero Banner Alt Text",
                        {"native": native, "refusal": said["refusal"], "stored": stored})
    assert stored == previous, (
        f"the empty alt text was NOT rejected: Hero Banner Alt Text now stores {stored!r} "
        f"(was {previous!r}); page said native={native!r} refusal={said['refusal']!r}"
    )


@allure.epic("About Us")
@allure.feature("Chamber's Law")
@allure.story("CMS authoring / admin")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Verify that Hero Banner Alt Text accepts exactly 150 characters and rejects 151")
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.functional_low
@pytest.mark.pbi_129394
@pytest.mark.tc_134903
@pytest.mark.traceability("134903")
@allure.label("pbi", "129394")
@allure.label("testcase", "134903")
@pytest.mark.skip(reason="Field-level validation case (Verify that Hero Banner Alt Text accepts exactly 150 characters and rejects 151) is the SAFE category this batch was authorized to automate (validation fires before any persistent write, or the check+revert is reversible) -- but it requires reaching the Chamber's Law page/law-entry admin edit form in the Liferay Control Panel to interact with the field at all. This session's login attempt against qcdev (CmsLoginPage.login() via TEST_USER/TEST_PASSWORD, mirroring the navigation pattern already proven for the Departments and Board of Directors admin surfaces) timed out repeatedly (playwright._impl._errors.TimeoutError on the username-field fill, and on core/web/session_guard.py's re-authentication retries) -- consistent with the severe qcdev session/connection-limit flakiness already documented in login_page.py and org_structure_admin_page.py, but worse this session (login itself never completed). No stable locators for the Chamber's Law admin edit form (list/edit URL, per-field selectors) could be extracted or confirmed as a result. Skipped rather than invented -- see module docstring.")
def test_chambers_law_cp_134903_hero_banner_alt_text_accepts_exactly_150_characters_and_rejects_151(page):
    ...


@allure.epic("About Us")
@allure.feature("Chamber's Law")
@allure.story("CMS authoring / admin")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Verify that whitespace-only Hero Banner Alt Text is rejected on save")
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.functional_low
@pytest.mark.pbi_129394
@pytest.mark.tc_134904
@pytest.mark.traceability("134904")
@allure.label("pbi", "129394")
@allure.label("testcase", "134904")
@pytest.mark.skip(reason="Field-level validation case (Verify that whitespace-only Hero Banner Alt Text is rejected on save) is the SAFE category this batch was authorized to automate (validation fires before any persistent write, or the check+revert is reversible) -- but it requires reaching the Chamber's Law page/law-entry admin edit form in the Liferay Control Panel to interact with the field at all. This session's login attempt against qcdev (CmsLoginPage.login() via TEST_USER/TEST_PASSWORD, mirroring the navigation pattern already proven for the Departments and Board of Directors admin surfaces) timed out repeatedly (playwright._impl._errors.TimeoutError on the username-field fill, and on core/web/session_guard.py's re-authentication retries) -- consistent with the severe qcdev session/connection-limit flakiness already documented in login_page.py and org_structure_admin_page.py, but worse this session (login itself never completed). No stable locators for the Chamber's Law admin edit form (list/edit URL, per-field selectors) could be extracted or confirmed as a result. Skipped rather than invented -- see module docstring.")
def test_chambers_law_cp_134904_whitespace_only_hero_banner_alt_text_is_rejected_on_save(page):
    ...


@allure.epic("About Us")
@allure.feature("Chamber's Law")
@allure.story("CMS authoring / admin")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Verify that a valid English Intro Section Heading is accepted and saved")
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.functional_low
@pytest.mark.pbi_129394
@pytest.mark.tc_134905
@pytest.mark.traceability("134905")
@allure.label("pbi", "129394")
@allure.label("testcase", "134905")
@CHAMBERS_LAW_XDIST_GROUP
def test_chambers_law_cp_134905_a_valid_english_intro_section_heading_is_accepted_and_saved(page):
    _case_valid_text(page, "134905", "intro_heading", "en", "Chamber Legal Framework")


@allure.epic("About Us")
@allure.feature("Chamber's Law")
@allure.story("CMS authoring / admin")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Verify that an empty English Intro Section Heading is rejected on save")
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.functional_low
@pytest.mark.pbi_129394
@pytest.mark.tc_134906
@pytest.mark.traceability("134906")
@allure.label("pbi", "129394")
@allure.label("testcase", "134906")
@CHAMBERS_LAW_XDIST_GROUP
def test_chambers_law_cp_134906_an_empty_english_intro_section_heading_is_rejected_on_save(page):
    _case_rejected_text(page, "134906", "intro_heading", "en", "")


@allure.epic("About Us")
@allure.feature("Chamber's Law")
@allure.story("CMS authoring / admin")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Verify that the English Intro Section Heading accepts exactly 150 characters and rejects 151")
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.functional_low
@pytest.mark.pbi_129394
@pytest.mark.tc_134907
@pytest.mark.traceability("134907")
@allure.label("pbi", "129394")
@allure.label("testcase", "134907")
@pytest.mark.skip(reason="Field-level validation case (Verify that the English Intro Section Heading accepts exactly 150 characters and rejects 151) is the SAFE category this batch was authorized to automate (validation fires before any persistent write, or the check+revert is reversible) -- but it requires reaching the Chamber's Law page/law-entry admin edit form in the Liferay Control Panel to interact with the field at all. This session's login attempt against qcdev (CmsLoginPage.login() via TEST_USER/TEST_PASSWORD, mirroring the navigation pattern already proven for the Departments and Board of Directors admin surfaces) timed out repeatedly (playwright._impl._errors.TimeoutError on the username-field fill, and on core/web/session_guard.py's re-authentication retries) -- consistent with the severe qcdev session/connection-limit flakiness already documented in login_page.py and org_structure_admin_page.py, but worse this session (login itself never completed). No stable locators for the Chamber's Law admin edit form (list/edit URL, per-field selectors) could be extracted or confirmed as a result. Skipped rather than invented -- see module docstring.")
def test_chambers_law_cp_134907_the_english_intro_section_heading_accepts_exactly_150_characters_and_rejects_151(page):
    ...


@allure.epic("About Us")
@allure.feature("Chamber's Law")
@allure.story("CMS authoring / admin")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Verify that a whitespace-only English Intro Section Heading is rejected on save")
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.functional_low
@pytest.mark.pbi_129394
@pytest.mark.tc_134908
@pytest.mark.traceability("134908")
@allure.label("pbi", "129394")
@allure.label("testcase", "134908")
@pytest.mark.skip(reason="Field-level validation case (Verify that a whitespace-only English Intro Section Heading is rejected on save) is the SAFE category this batch was authorized to automate (validation fires before any persistent write, or the check+revert is reversible) -- but it requires reaching the Chamber's Law page/law-entry admin edit form in the Liferay Control Panel to interact with the field at all. This session's login attempt against qcdev (CmsLoginPage.login() via TEST_USER/TEST_PASSWORD, mirroring the navigation pattern already proven for the Departments and Board of Directors admin surfaces) timed out repeatedly (playwright._impl._errors.TimeoutError on the username-field fill, and on core/web/session_guard.py's re-authentication retries) -- consistent with the severe qcdev session/connection-limit flakiness already documented in login_page.py and org_structure_admin_page.py, but worse this session (login itself never completed). No stable locators for the Chamber's Law admin edit form (list/edit URL, per-field selectors) could be extracted or confirmed as a result. Skipped rather than invented -- see module docstring.")
def test_chambers_law_cp_134908_a_whitespace_only_english_intro_section_heading_is_rejected_on_save(page):
    ...


@allure.epic("About Us")
@allure.feature("Chamber's Law")
@allure.story("CMS authoring / admin")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Verify that a valid Arabic Intro Section Heading is accepted and saved")
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.functional_low
@pytest.mark.pbi_129394
@pytest.mark.tc_134909
@pytest.mark.traceability("134909")
@allure.label("pbi", "129394")
@allure.label("testcase", "134909")
@CHAMBERS_LAW_XDIST_GROUP
def test_chambers_law_cp_134909_a_valid_arabic_intro_section_heading_is_accepted_and_saved(page):
    _case_valid_text(page, "134909", "intro_heading", "ar", "الإطار القانوني للغرفة")


@allure.epic("About Us")
@allure.feature("Chamber's Law")
@allure.story("CMS authoring / admin")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Verify that an empty Arabic Intro Section Heading is rejected on save")
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.functional_low
@pytest.mark.pbi_129394
@pytest.mark.tc_134910
@pytest.mark.traceability("134910")
@allure.label("pbi", "129394")
@allure.label("testcase", "134910")
@CHAMBERS_LAW_XDIST_GROUP
def test_chambers_law_cp_134910_an_empty_arabic_intro_section_heading_is_rejected_on_save(page):
    _case_rejected_text(page, "134910", "intro_heading", "ar", "")


@allure.epic("About Us")
@allure.feature("Chamber's Law")
@allure.story("CMS authoring / admin")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Verify that the Arabic Intro Section Heading accepts exactly 150 characters and rejects 151")
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.functional_low
@pytest.mark.pbi_129394
@pytest.mark.tc_134911
@pytest.mark.traceability("134911")
@allure.label("pbi", "129394")
@allure.label("testcase", "134911")
@pytest.mark.skip(reason="Field-level validation case (Verify that the Arabic Intro Section Heading accepts exactly 150 characters and rejects 151) is the SAFE category this batch was authorized to automate (validation fires before any persistent write, or the check+revert is reversible) -- but it requires reaching the Chamber's Law page/law-entry admin edit form in the Liferay Control Panel to interact with the field at all. This session's login attempt against qcdev (CmsLoginPage.login() via TEST_USER/TEST_PASSWORD, mirroring the navigation pattern already proven for the Departments and Board of Directors admin surfaces) timed out repeatedly (playwright._impl._errors.TimeoutError on the username-field fill, and on core/web/session_guard.py's re-authentication retries) -- consistent with the severe qcdev session/connection-limit flakiness already documented in login_page.py and org_structure_admin_page.py, but worse this session (login itself never completed). No stable locators for the Chamber's Law admin edit form (list/edit URL, per-field selectors) could be extracted or confirmed as a result. Skipped rather than invented -- see module docstring.")
def test_chambers_law_cp_134911_the_arabic_intro_section_heading_accepts_exactly_150_characters_and_rejects_151(page):
    ...


@allure.epic("About Us")
@allure.feature("Chamber's Law")
@allure.story("CMS authoring / admin")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Verify that a whitespace-only Arabic Intro Section Heading is rejected on save")
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.functional_low
@pytest.mark.pbi_129394
@pytest.mark.tc_134912
@pytest.mark.traceability("134912")
@allure.label("pbi", "129394")
@allure.label("testcase", "134912")
@pytest.mark.skip(reason="Field-level validation case (Verify that a whitespace-only Arabic Intro Section Heading is rejected on save) is the SAFE category this batch was authorized to automate (validation fires before any persistent write, or the check+revert is reversible) -- but it requires reaching the Chamber's Law page/law-entry admin edit form in the Liferay Control Panel to interact with the field at all. This session's login attempt against qcdev (CmsLoginPage.login() via TEST_USER/TEST_PASSWORD, mirroring the navigation pattern already proven for the Departments and Board of Directors admin surfaces) timed out repeatedly (playwright._impl._errors.TimeoutError on the username-field fill, and on core/web/session_guard.py's re-authentication retries) -- consistent with the severe qcdev session/connection-limit flakiness already documented in login_page.py and org_structure_admin_page.py, but worse this session (login itself never completed). No stable locators for the Chamber's Law admin edit form (list/edit URL, per-field selectors) could be extracted or confirmed as a result. Skipped rather than invented -- see module docstring.")
def test_chambers_law_cp_134912_a_whitespace_only_arabic_intro_section_heading_is_rejected_on_save(page):
    ...


@allure.epic("About Us")
@allure.feature("Chamber's Law")
@allure.story("CMS authoring / admin")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Verify that valid English Intro Content is accepted and saved")
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.functional_low
@pytest.mark.pbi_129394
@pytest.mark.tc_134913
@pytest.mark.traceability("134913")
@allure.label("pbi", "129394")
@allure.label("testcase", "134913")
@CHAMBERS_LAW_XDIST_GROUP
def test_chambers_law_cp_134913_valid_english_intro_content_is_accepted_and_saved(page):
    admin = ChambersLawAdminPage(page)
    paragraphs = [
        "QCTEST-134913 paragraph one. Qatar Chamber operates under a legal framework that "
        "defines its establishment, responsibilities and representative role for the private sector.",
        "QCTEST-134913 paragraph two. The founding law and its amendments set out how the "
        "Chamber is governed and how members, businesses and researchers may rely on it.",
        "QCTEST-134913 paragraph three. This text exists only to verify that three distinct "
        "paragraphs are accepted, saved and returned intact by the content management system.",
    ]
    body = "\n".join(paragraphs)
    pad = 500 - len(body)
    if pad > 0:
        paragraphs[2] = paragraphs[2] + " " + ("x" * (pad - 1))
        body = "\n".join(paragraphs)
    try:
        with allure.step(f"Enter a {len(body)}-character, three-paragraph body in Intro Content (EN) and click Save"):
            authoring = admin.open_page_record(locale="en")
            admin.type_into_intro(body, "en")
            block_live_singleton_write(PAGE_RECORD, "three-paragraph Intro Content (EN) save")
            said = _publish_edit(admin, authoring)
            _attach("save outcome", said)
        with allure.step("Reload the record"):
            stored = _wait_stored(admin, lambda: all(p in admin.intro_html("en") for p in paragraphs), True)
            html = admin.intro_html("en")
            stored_paras = [p for p in _re.findall(r"<p[^>]*>(.*?)</p>", html, _re.S) if p.strip() and p.strip() != "&nbsp;"]
        assert not said["refusal"], f"the save was refused: {said['refusal']!r}"
        assert stored is True, f"Intro Content (EN) does not hold the three paragraphs: {html!r}"
        assert len(stored_paras) == 3, f"expected 3 distinct paragraphs, found {len(stored_paras)}: {stored_paras!r}"
    finally:
        pass  # nothing to restore: no successful write reaches the singleton (2026-10-13)


@allure.epic("About Us")
@allure.feature("Chamber's Law")
@allure.story("CMS authoring / admin")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Verify that empty English Intro Content is rejected on save")
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.functional_low
@pytest.mark.pbi_129394
@pytest.mark.tc_134914
@pytest.mark.traceability("134914")
@allure.label("pbi", "129394")
@allure.label("testcase", "134914")
@CHAMBERS_LAW_XDIST_GROUP
def test_chambers_law_cp_134914_empty_english_intro_content_is_rejected_on_save(page):
    _case_rich_rejected(page, "134914", "en", "empty")


@allure.epic("About Us")
@allure.feature("Chamber's Law")
@allure.story("CMS authoring / admin")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Verify that English Intro Content accepts exactly 5000 characters and rejects 5001")
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.functional_low
@pytest.mark.pbi_129394
@pytest.mark.tc_134915
@pytest.mark.traceability("134915")
@allure.label("pbi", "129394")
@allure.label("testcase", "134915")
@pytest.mark.skip(reason="Field-level validation case (Verify that English Intro Content accepts exactly 5000 characters and rejects 5001) is the SAFE category this batch was authorized to automate (validation fires before any persistent write, or the check+revert is reversible) -- but it requires reaching the Chamber's Law page/law-entry admin edit form in the Liferay Control Panel to interact with the field at all. This session's login attempt against qcdev (CmsLoginPage.login() via TEST_USER/TEST_PASSWORD, mirroring the navigation pattern already proven for the Departments and Board of Directors admin surfaces) timed out repeatedly (playwright._impl._errors.TimeoutError on the username-field fill, and on core/web/session_guard.py's re-authentication retries) -- consistent with the severe qcdev session/connection-limit flakiness already documented in login_page.py and org_structure_admin_page.py, but worse this session (login itself never completed). No stable locators for the Chamber's Law admin edit form (list/edit URL, per-field selectors) could be extracted or confirmed as a result. Skipped rather than invented -- see module docstring.")
def test_chambers_law_cp_134915_english_intro_content_accepts_exactly_5000_characters_and_rejects_5001(page):
    ...


@allure.epic("About Us")
@allure.feature("Chamber's Law")
@allure.story("CMS authoring / admin")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Verify that whitespace-only English Intro Content is rejected on save")
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.functional_low
@pytest.mark.pbi_129394
@pytest.mark.tc_134916
@pytest.mark.traceability("134916")
@allure.label("pbi", "129394")
@allure.label("testcase", "134916")
@pytest.mark.skip(reason="Field-level validation case (Verify that whitespace-only English Intro Content is rejected on save) is the SAFE category this batch was authorized to automate (validation fires before any persistent write, or the check+revert is reversible) -- but it requires reaching the Chamber's Law page/law-entry admin edit form in the Liferay Control Panel to interact with the field at all. This session's login attempt against qcdev (CmsLoginPage.login() via TEST_USER/TEST_PASSWORD, mirroring the navigation pattern already proven for the Departments and Board of Directors admin surfaces) timed out repeatedly (playwright._impl._errors.TimeoutError on the username-field fill, and on core/web/session_guard.py's re-authentication retries) -- consistent with the severe qcdev session/connection-limit flakiness already documented in login_page.py and org_structure_admin_page.py, but worse this session (login itself never completed). No stable locators for the Chamber's Law admin edit form (list/edit URL, per-field selectors) could be extracted or confirmed as a result. Skipped rather than invented -- see module docstring.")
def test_chambers_law_cp_134916_whitespace_only_english_intro_content_is_rejected_on_save(page):
    ...


@allure.epic("About Us")
@allure.feature("Chamber's Law")
@allure.story("CMS authoring / admin")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Verify that valid Arabic Intro Content is accepted and saved with RTL text preserved")
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.functional_low
@pytest.mark.pbi_129394
@pytest.mark.tc_134917
@pytest.mark.traceability("134917")
@allure.label("pbi", "129394")
@allure.label("testcase", "134917")
@CHAMBERS_LAW_XDIST_GROUP
def test_chambers_law_cp_134917_valid_arabic_intro_content_is_accepted_and_saved_with_rtl_text_preserved(page):
    admin = ChambersLawAdminPage(page)
    para_one = ("QCTEST-134917 تعمل غرفة قطر للتجارة والصناعة ضمن إطار قانوني يحدد نشأتها ومسؤولياتها "
                "ودورها في تمثيل القطاع الخاص في دولة قطر وفي دعم بيئة الأعمال وتطويرها. ")
    para_two = ("توفر هذه الصفحة إمكانية الوصول إلى القوانين الرئيسية المتعلقة بالغرفة بما في ذلك قانون "
                "التأسيس والتعديلات اللاحقة بما يتيح للأعضاء والشركات والباحثين الرجوع إلى الأساس القانوني. ")
    para_one = (para_one * 3)[:250].strip()
    para_two = (para_two * 3)[:249].strip()
    body = para_one + "\n" + para_two
    try:
        with allure.step(f"Enter a {len(body)}-character, two-paragraph Arabic body in Intro Content (AR) and click Save"):
            authoring = admin.open_page_record(locale="en")
            admin.type_into_intro(body, "ar")
            block_live_singleton_write(PAGE_RECORD, "two-paragraph Intro Content (AR) save")
            said = _publish_edit(admin, authoring)
            _attach("save outcome", said)
        with allure.step("Reload the record"):
            stored = _wait_stored(admin, lambda: para_one in admin.intro_text("ar") and para_two in admin.intro_text("ar"), True)
            direction = admin.intro_direction("ar")
            text = admin.intro_text("ar")
        assert not said["refusal"], f"the save was refused: {said['refusal']!r}"
        assert stored is True, f"Intro Content (AR) did not keep the Arabic text intact: {text!r}"
        assert direction == "rtl", f"the Arabic editor renders {direction!r}, expected right-to-left"
    finally:
        pass  # nothing to restore: no successful write reaches the singleton (2026-10-13)


@allure.epic("About Us")
@allure.feature("Chamber's Law")
@allure.story("CMS authoring / admin")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Verify that empty Arabic Intro Content is rejected on save")
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.functional_low
@pytest.mark.pbi_129394
@pytest.mark.tc_134918
@pytest.mark.traceability("134918")
@allure.label("pbi", "129394")
@allure.label("testcase", "134918")
@CHAMBERS_LAW_XDIST_GROUP
def test_chambers_law_cp_134918_empty_arabic_intro_content_is_rejected_on_save(page):
    _case_rich_rejected(page, "134918", "ar", "empty")


@allure.epic("About Us")
@allure.feature("Chamber's Law")
@allure.story("CMS authoring / admin")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Verify that Arabic Intro Content accepts exactly 5000 characters and rejects 5001")
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.functional_low
@pytest.mark.pbi_129394
@pytest.mark.tc_134919
@pytest.mark.traceability("134919")
@allure.label("pbi", "129394")
@allure.label("testcase", "134919")
@pytest.mark.skip(reason="Field-level validation case (Verify that Arabic Intro Content accepts exactly 5000 characters and rejects 5001) is the SAFE category this batch was authorized to automate (validation fires before any persistent write, or the check+revert is reversible) -- but it requires reaching the Chamber's Law page/law-entry admin edit form in the Liferay Control Panel to interact with the field at all. This session's login attempt against qcdev (CmsLoginPage.login() via TEST_USER/TEST_PASSWORD, mirroring the navigation pattern already proven for the Departments and Board of Directors admin surfaces) timed out repeatedly (playwright._impl._errors.TimeoutError on the username-field fill, and on core/web/session_guard.py's re-authentication retries) -- consistent with the severe qcdev session/connection-limit flakiness already documented in login_page.py and org_structure_admin_page.py, but worse this session (login itself never completed). No stable locators for the Chamber's Law admin edit form (list/edit URL, per-field selectors) could be extracted or confirmed as a result. Skipped rather than invented -- see module docstring.")
def test_chambers_law_cp_134919_arabic_intro_content_accepts_exactly_5000_characters_and_rejects_5001(page):
    ...


@allure.epic("About Us")
@allure.feature("Chamber's Law")
@allure.story("CMS authoring / admin")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Verify that whitespace-only Arabic Intro Content is rejected on save")
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.functional_low
@pytest.mark.pbi_129394
@pytest.mark.tc_134920
@pytest.mark.traceability("134920")
@allure.label("pbi", "129394")
@allure.label("testcase", "134920")
@pytest.mark.skip(reason="Field-level validation case (Verify that whitespace-only Arabic Intro Content is rejected on save) is the SAFE category this batch was authorized to automate (validation fires before any persistent write, or the check+revert is reversible) -- but it requires reaching the Chamber's Law page/law-entry admin edit form in the Liferay Control Panel to interact with the field at all. This session's login attempt against qcdev (CmsLoginPage.login() via TEST_USER/TEST_PASSWORD, mirroring the navigation pattern already proven for the Departments and Board of Directors admin surfaces) timed out repeatedly (playwright._impl._errors.TimeoutError on the username-field fill, and on core/web/session_guard.py's re-authentication retries) -- consistent with the severe qcdev session/connection-limit flakiness already documented in login_page.py and org_structure_admin_page.py, but worse this session (login itself never completed). No stable locators for the Chamber's Law admin edit form (list/edit URL, per-field selectors) could be extracted or confirmed as a result. Skipped rather than invented -- see module docstring.")
def test_chambers_law_cp_134920_whitespace_only_arabic_intro_content_is_rejected_on_save(page):
    ...


@allure.epic("About Us")
@allure.feature("Chamber's Law")
@allure.story("CMS authoring / admin")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Verify that a valid English Legal References Section Heading is accepted and saved")
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.functional_low
@pytest.mark.pbi_129394
@pytest.mark.tc_134921
@pytest.mark.traceability("134921")
@allure.label("pbi", "129394")
@allure.label("testcase", "134921")
@CHAMBERS_LAW_XDIST_GROUP
def test_chambers_law_cp_134921_a_valid_english_legal_references_section_heading_is_accepted_and_saved(page):
    def _independent_of_intro(admin):
        intro = admin.page_text("intro_heading", "en")
        return True if intro != "Official Legal References" else (
            f"Intro Heading (EN) also reads {intro!r} -- not stored independently"
        )

    _case_valid_text(page, "134921", "refs_heading", "en", "Official Legal References", extra=_independent_of_intro)


@allure.epic("About Us")
@allure.feature("Chamber's Law")
@allure.story("CMS authoring / admin")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Verify that an empty English Legal References Section Heading is rejected on save")
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.functional_low
@pytest.mark.pbi_129394
@pytest.mark.tc_134922
@pytest.mark.traceability("134922")
@allure.label("pbi", "129394")
@allure.label("testcase", "134922")
@CHAMBERS_LAW_XDIST_GROUP
def test_chambers_law_cp_134922_an_empty_english_legal_references_section_heading_is_rejected_on_save(page):
    _case_rejected_text(page, "134922", "refs_heading", "en", "")


@allure.epic("About Us")
@allure.feature("Chamber's Law")
@allure.story("CMS authoring / admin")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Verify that the English Legal References Section Heading accepts exactly 150 characters and rejects 151")
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.functional_low
@pytest.mark.pbi_129394
@pytest.mark.tc_134923
@pytest.mark.traceability("134923")
@allure.label("pbi", "129394")
@allure.label("testcase", "134923")
@pytest.mark.skip(reason="Field-level validation case (Verify that the English Legal References Section Heading accepts exactly 150 characters and rejects 151) is the SAFE category this batch was authorized to automate (validation fires before any persistent write, or the check+revert is reversible) -- but it requires reaching the Chamber's Law page/law-entry admin edit form in the Liferay Control Panel to interact with the field at all. This session's login attempt against qcdev (CmsLoginPage.login() via TEST_USER/TEST_PASSWORD, mirroring the navigation pattern already proven for the Departments and Board of Directors admin surfaces) timed out repeatedly (playwright._impl._errors.TimeoutError on the username-field fill, and on core/web/session_guard.py's re-authentication retries) -- consistent with the severe qcdev session/connection-limit flakiness already documented in login_page.py and org_structure_admin_page.py, but worse this session (login itself never completed). No stable locators for the Chamber's Law admin edit form (list/edit URL, per-field selectors) could be extracted or confirmed as a result. Skipped rather than invented -- see module docstring.")
def test_chambers_law_cp_134923_the_english_legal_references_section_heading_accepts_exactly_150_characters_and_(page):
    ...


@allure.epic("About Us")
@allure.feature("Chamber's Law")
@allure.story("CMS authoring / admin")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Verify that a whitespace-only English Legal References Section Heading is rejected on save")
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.functional_low
@pytest.mark.pbi_129394
@pytest.mark.tc_134924
@pytest.mark.traceability("134924")
@allure.label("pbi", "129394")
@allure.label("testcase", "134924")
@pytest.mark.skip(reason="Field-level validation case (Verify that a whitespace-only English Legal References Section Heading is rejected on save) is the SAFE category this batch was authorized to automate (validation fires before any persistent write, or the check+revert is reversible) -- but it requires reaching the Chamber's Law page/law-entry admin edit form in the Liferay Control Panel to interact with the field at all. This session's login attempt against qcdev (CmsLoginPage.login() via TEST_USER/TEST_PASSWORD, mirroring the navigation pattern already proven for the Departments and Board of Directors admin surfaces) timed out repeatedly (playwright._impl._errors.TimeoutError on the username-field fill, and on core/web/session_guard.py's re-authentication retries) -- consistent with the severe qcdev session/connection-limit flakiness already documented in login_page.py and org_structure_admin_page.py, but worse this session (login itself never completed). No stable locators for the Chamber's Law admin edit form (list/edit URL, per-field selectors) could be extracted or confirmed as a result. Skipped rather than invented -- see module docstring.")
def test_chambers_law_cp_134924_a_whitespace_only_english_legal_references_section_heading_is_rejected_on_save(page):
    ...


@allure.epic("About Us")
@allure.feature("Chamber's Law")
@allure.story("CMS authoring / admin")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Verify that a valid Arabic Legal References Section Heading is accepted and saved")
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.functional_low
@pytest.mark.pbi_129394
@pytest.mark.tc_134925
@pytest.mark.traceability("134925")
@allure.label("pbi", "129394")
@allure.label("testcase", "134925")
@CHAMBERS_LAW_XDIST_GROUP
def test_chambers_law_cp_134925_a_valid_arabic_legal_references_section_heading_is_accepted_and_saved(page):
    _case_valid_text(page, "134925", "refs_heading", "ar", "المراجع القانونية الرسمية")


@allure.epic("About Us")
@allure.feature("Chamber's Law")
@allure.story("CMS authoring / admin")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Verify that an empty Arabic Legal References Section Heading is rejected on save")
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.functional_low
@pytest.mark.pbi_129394
@pytest.mark.tc_134926
@pytest.mark.traceability("134926")
@allure.label("pbi", "129394")
@allure.label("testcase", "134926")
@CHAMBERS_LAW_XDIST_GROUP
def test_chambers_law_cp_134926_an_empty_arabic_legal_references_section_heading_is_rejected_on_save(page):
    _case_rejected_text(page, "134926", "refs_heading", "ar", "")


@allure.epic("About Us")
@allure.feature("Chamber's Law")
@allure.story("CMS authoring / admin")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Verify that the Arabic Legal References Section Heading accepts exactly 150 characters and rejects 151")
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.functional_low
@pytest.mark.pbi_129394
@pytest.mark.tc_134927
@pytest.mark.traceability("134927")
@allure.label("pbi", "129394")
@allure.label("testcase", "134927")
@pytest.mark.skip(reason="Field-level validation case (Verify that the Arabic Legal References Section Heading accepts exactly 150 characters and rejects 151) is the SAFE category this batch was authorized to automate (validation fires before any persistent write, or the check+revert is reversible) -- but it requires reaching the Chamber's Law page/law-entry admin edit form in the Liferay Control Panel to interact with the field at all. This session's login attempt against qcdev (CmsLoginPage.login() via TEST_USER/TEST_PASSWORD, mirroring the navigation pattern already proven for the Departments and Board of Directors admin surfaces) timed out repeatedly (playwright._impl._errors.TimeoutError on the username-field fill, and on core/web/session_guard.py's re-authentication retries) -- consistent with the severe qcdev session/connection-limit flakiness already documented in login_page.py and org_structure_admin_page.py, but worse this session (login itself never completed). No stable locators for the Chamber's Law admin edit form (list/edit URL, per-field selectors) could be extracted or confirmed as a result. Skipped rather than invented -- see module docstring.")
def test_chambers_law_cp_134927_the_arabic_legal_references_section_heading_accepts_exactly_150_characters_and_r(page):
    ...


@allure.epic("About Us")
@allure.feature("Chamber's Law")
@allure.story("CMS authoring / admin")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Verify that a whitespace-only Arabic Legal References Section Heading is rejected on save")
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.functional_low
@pytest.mark.pbi_129394
@pytest.mark.tc_134928
@pytest.mark.traceability("134928")
@allure.label("pbi", "129394")
@allure.label("testcase", "134928")
@pytest.mark.skip(reason="Field-level validation case (Verify that a whitespace-only Arabic Legal References Section Heading is rejected on save) is the SAFE category this batch was authorized to automate (validation fires before any persistent write, or the check+revert is reversible) -- but it requires reaching the Chamber's Law page/law-entry admin edit form in the Liferay Control Panel to interact with the field at all. This session's login attempt against qcdev (CmsLoginPage.login() via TEST_USER/TEST_PASSWORD, mirroring the navigation pattern already proven for the Departments and Board of Directors admin surfaces) timed out repeatedly (playwright._impl._errors.TimeoutError on the username-field fill, and on core/web/session_guard.py's re-authentication retries) -- consistent with the severe qcdev session/connection-limit flakiness already documented in login_page.py and org_structure_admin_page.py, but worse this session (login itself never completed). No stable locators for the Chamber's Law admin edit form (list/edit URL, per-field selectors) could be extracted or confirmed as a result. Skipped rather than invented -- see module docstring.")
def test_chambers_law_cp_134928_a_whitespace_only_arabic_legal_references_section_heading_is_rejected_on_save(page):
    ...


@allure.epic("About Us")
@allure.feature("Chamber's Law")
@allure.story("CMS authoring / admin")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Verify that a valid PNG Content Image under 2 MB is accepted")
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.functional_low
@pytest.mark.pbi_129394
@pytest.mark.tc_134929
@pytest.mark.traceability("134929")
@allure.label("pbi", "129394")
@allure.label("testcase", "134929")
@CHAMBERS_LAW_XDIST_GROUP
def test_chambers_law_cp_134929_a_valid_png_content_image_under_2_mb_is_accepted(page):
    admin = ChambersLawAdminPage(page)
    path = _fixture("lawbook.png", make_png, int(1.3 * ONE_MB))
    try:
        with allure.step("Upload lawbook.png (PNG, 1.3 MB) to the Content Image field and click Save"):
            authoring = admin.open_page_record(locale="en")
            authoring.upload_file(admin.CONTENT_IMAGE_UPLOAD_LABEL, path)
            block_live_singleton_write(PAGE_RECORD, "save of a valid lawbook.png Content Image")
            said = _publish_edit(admin, authoring)
            _attach("save outcome", said)
        with allure.step("Reload the record"):
            stored = _wait_stored(
                admin, lambda: "lawbook" in authoring.current_file_name(admin.CONTENT_IMAGE_UPLOAD_LABEL), True
            )
            name = authoring.current_file_name(admin.CONTENT_IMAGE_UPLOAD_LABEL)
        assert not said["refusal"], f"the upload/save was refused: {said['refusal']!r}"
        assert stored is True, f"the Content Image field shows {name!r}, expected lawbook.png"
    finally:
        pass  # nothing to restore: no successful write reaches the singleton (2026-10-13)


@allure.epic("About Us")
@allure.feature("Chamber's Law")
@allure.story("CMS authoring / admin")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Verify that a Content Image in an unsupported format is rejected")
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.functional_low
@pytest.mark.pbi_129394
@pytest.mark.tc_134930
@pytest.mark.traceability("134930")
@allure.label("pbi", "129394")
@allure.label("testcase", "134930")
@CHAMBERS_LAW_XDIST_GROUP
def test_chambers_law_cp_134930_a_content_image_in_an_unsupported_format_is_rejected(page):
    admin = ChambersLawAdminPage(page)
    baseline = _page_current(admin)
    path = _fixture("lawbook.bmp", make_bmp, 400 * 1024)
    try:
        with allure.step("Upload lawbook.bmp (BMP, 400 KB) to the Content Image field"):
            authoring = admin.open_page_record(locale="en")
            outcome = _attempt_upload(admin, authoring, "ObjectField_contentImage", path)
            _attach("picker outcome (wording recorded, not asserted)", outcome)
            current = authoring.current_file_name(admin.CONTENT_IMAGE_UPLOAD_LABEL)
        assert outcome["rejected"], (
            f"the BMP upload was not rejected (picker accepted={outcome['accepted']}; "
            f"text={outcome['picker_text'][:300]!r})"
        )
        assert current == baseline["image"], f"the stored Content Image changed from {baseline['image']!r} to {current!r}"
    finally:
        pass  # nothing to restore: no successful write reaches the singleton (2026-10-13)


@allure.epic("About Us")
@allure.feature("Chamber's Law")
@allure.story("CMS authoring / admin")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Verify that a Content Image above 2 MB is rejected at the size boundary")
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.functional_low
@pytest.mark.pbi_129394
@pytest.mark.tc_134931
@pytest.mark.traceability("134931")
@allure.label("pbi", "129394")
@allure.label("testcase", "134931")
@CHAMBERS_LAW_XDIST_GROUP
def test_chambers_law_cp_134931_a_content_image_above_2_mb_is_rejected_at_the_size_boundary(page):
    # File-size tolerance (project rule): up to 3 MB accepted is OK even where the
    # PBI says 2 MB; above 3 MB accepted is a defect. So 2.1 MB is RECORDED and a
    # 3.1 MB file is the asserted rejection boundary.
    admin = ChambersLawAdminPage(page)
    exact = _fixture("content-2mb.png", make_png, 2 * ONE_MB)
    over = _fixture("content-oversize.png", make_png, int(2.1 * ONE_MB))
    far_over = _fixture("content-oversize-3mb.png", make_png, int(3.1 * ONE_MB))
    try:
        with allure.step("Upload content-2mb.png (exactly 2 MB) and click Save"):
            authoring = admin.open_page_record(locale="en")
            authoring.upload_file(admin.CONTENT_IMAGE_UPLOAD_LABEL, exact)
            # The boundary case starts with a SUCCESSFUL 2 MB save (2026-10-13).
            block_live_singleton_write(PAGE_RECORD, "save of the exactly-2 MB Content Image")
            said = _publish_edit(admin, authoring)
            stored = _wait_stored(
                admin, lambda: "content-2mb" in authoring.current_file_name(admin.CONTENT_IMAGE_UPLOAD_LABEL), True
            )
        with allure.step("Upload content-oversize.png (2.1 MB) -- recorded under the 3 MB tolerance"):
            authoring = admin.open_page_record(locale="en")
            tolerated = _attempt_upload(admin, authoring, "ObjectField_contentImage", over, size_only=True, add_if_accepted=True)
            _attach("2.1 MB outcome (tolerated either way)", tolerated)
        with allure.step("Upload a 3.1 MB PNG -- beyond the tolerance, must be rejected"):
            authoring = admin.open_page_record(locale="en")
            rejected = _attempt_upload(admin, authoring, "ObjectField_contentImage", far_over, size_only=True, add_if_accepted=True)
            _attach("3.1 MB outcome", rejected)
            authoring = admin.open_page_record(locale="en")
            current = authoring.current_file_name(admin.CONTENT_IMAGE_UPLOAD_LABEL)
        assert stored is True, f"the exactly-2 MB file was not saved ({said!r})"
        assert rejected["rejected"], (
            f"a 3.1 MB Content Image was not rejected (accepted={rejected['accepted']})"
        )
        assert "content-2mb" in current, f"the stored image changed after the rejected upload: {current!r}"
    finally:
        pass  # nothing to restore: no successful write reaches the singleton (2026-10-13)


@allure.epic("About Us")
@allure.feature("Chamber's Law")
@allure.story("CMS authoring / admin")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Verify that publishing without a Content Image is blocked")
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.functional_low
@pytest.mark.pbi_129394
@pytest.mark.tc_134932
@pytest.mark.traceability("134932")
@allure.label("pbi", "129394")
@allure.label("testcase", "134932")
@CHAMBERS_LAW_XDIST_GROUP
def test_chambers_law_cp_134932_publishing_without_a_content_image_is_blocked(page):
    admin = ChambersLawAdminPage(page)
    baseline = _page_current(admin)
    try:
        with allure.step("Open the record with the Content Image field emptied, then click Publish"):
            authoring = admin.open_page_record(locale="en")
            authoring.remove_current_file(admin.CONTENT_IMAGE_UPLOAD_LABEL)
            native = _FormProbe(authoring).attachment_validation_message(admin.CONTENT_IMAGE_UPLOAD_LABEL)
            said = _publish_edit(admin, authoring)
            _attach("publish outcome", {"native": native, **said})
        with allure.step("Check the record status and stored image"):
            authoring = admin.open_page_record(locale="en")
            status = authoring.current_status()
            image = authoring.current_file_name(admin.CONTENT_IMAGE_UPLOAD_LABEL)
        stop_unless_refused(bool(image) and status == baseline["workflow"], PAGE_RECORD,
                            "Publish with the Content Image removed",
                            {"native": native, "said": said, "image": image, "status": status})
        assert image, (
            "publishing WITHOUT a Content Image was not blocked: the record now has no image "
            f"(status {status!r}; page said {said!r})"
        )
        assert status == baseline["workflow"], f"record status changed to {status!r}"
    finally:
        pass  # nothing to restore: no successful write reaches the singleton (2026-10-13)


@allure.epic("About Us")
@allure.feature("Chamber's Law")
@allure.story("CMS authoring / admin")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Verify that valid Content Image Alt Text is accepted and saved")
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.functional_low
@pytest.mark.pbi_129394
@pytest.mark.tc_134933
@pytest.mark.traceability("134933")
@allure.label("pbi", "129394")
@allure.label("testcase", "134933")
@CHAMBERS_LAW_XDIST_GROUP
def test_chambers_law_cp_134933_valid_content_image_alt_text_is_accepted_and_saved(page):
    _case_valid_text(page, "134933", "alt_text", "en", "Law book with scales of justice")


@allure.epic("About Us")
@allure.feature("Chamber's Law")
@allure.story("CMS authoring / admin")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Verify that empty Content Image Alt Text is rejected on save")
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.functional_low
@pytest.mark.pbi_129394
@pytest.mark.tc_134934
@pytest.mark.traceability("134934")
@allure.label("pbi", "129394")
@allure.label("testcase", "134934")
@CHAMBERS_LAW_XDIST_GROUP
def test_chambers_law_cp_134934_empty_content_image_alt_text_is_rejected_on_save(page):
    _case_rejected_text(page, "134934", "alt_text", "en", "")


@allure.epic("About Us")
@allure.feature("Chamber's Law")
@allure.story("CMS authoring / admin")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Verify that Content Image Alt Text accepts exactly 150 characters and rejects 151")
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.functional_low
@pytest.mark.pbi_129394
@pytest.mark.tc_134935
@pytest.mark.traceability("134935")
@allure.label("pbi", "129394")
@allure.label("testcase", "134935")
@pytest.mark.skip(reason="Field-level validation case (Verify that Content Image Alt Text accepts exactly 150 characters and rejects 151) is the SAFE category this batch was authorized to automate (validation fires before any persistent write, or the check+revert is reversible) -- but it requires reaching the Chamber's Law page/law-entry admin edit form in the Liferay Control Panel to interact with the field at all. This session's login attempt against qcdev (CmsLoginPage.login() via TEST_USER/TEST_PASSWORD, mirroring the navigation pattern already proven for the Departments and Board of Directors admin surfaces) timed out repeatedly (playwright._impl._errors.TimeoutError on the username-field fill, and on core/web/session_guard.py's re-authentication retries) -- consistent with the severe qcdev session/connection-limit flakiness already documented in login_page.py and org_structure_admin_page.py, but worse this session (login itself never completed). No stable locators for the Chamber's Law admin edit form (list/edit URL, per-field selectors) could be extracted or confirmed as a result. Skipped rather than invented -- see module docstring.")
def test_chambers_law_cp_134935_content_image_alt_text_accepts_exactly_150_characters_and_rejects_151(page):
    ...


@allure.epic("About Us")
@allure.feature("Chamber's Law")
@allure.story("CMS authoring / admin")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Verify that whitespace-only Content Image Alt Text is rejected on save")
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.functional_low
@pytest.mark.pbi_129394
@pytest.mark.tc_134936
@pytest.mark.traceability("134936")
@allure.label("pbi", "129394")
@allure.label("testcase", "134936")
@pytest.mark.skip(reason="Field-level validation case (Verify that whitespace-only Content Image Alt Text is rejected on save) is the SAFE category this batch was authorized to automate (validation fires before any persistent write, or the check+revert is reversible) -- but it requires reaching the Chamber's Law page/law-entry admin edit form in the Liferay Control Panel to interact with the field at all. This session's login attempt against qcdev (CmsLoginPage.login() via TEST_USER/TEST_PASSWORD, mirroring the navigation pattern already proven for the Departments and Board of Directors admin surfaces) timed out repeatedly (playwright._impl._errors.TimeoutError on the username-field fill, and on core/web/session_guard.py's re-authentication retries) -- consistent with the severe qcdev session/connection-limit flakiness already documented in login_page.py and org_structure_admin_page.py, but worse this session (login itself never completed). No stable locators for the Chamber's Law admin edit form (list/edit URL, per-field selectors) could be extracted or confirmed as a result. Skipped rather than invented -- see module docstring.")
def test_chambers_law_cp_134936_whitespace_only_content_image_alt_text_is_rejected_on_save(page):
    ...


@allure.epic("About Us")
@allure.feature("Chamber's Law")
@allure.story("CMS authoring / admin")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Verify that the page Status dropdown offers and stores the Draft value")
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.functional_low
@pytest.mark.pbi_129394
@pytest.mark.tc_134937
@pytest.mark.traceability("134937")
@allure.label("pbi", "129394")
@allure.label("testcase", "134937")
@CHAMBERS_LAW_XDIST_GROUP
@pytest.mark.timeout(480)
def test_chambers_law_cp_134937_the_page_status_dropdown_offers_and_stores_the_draft_value(page, browser):
    # USER DECISION 2026-10-13 (P3/P4): runs only with
    # QC_ALLOW_LIVE_SINGLETON_WRITES=1 (else NOT APPLICABLE). As Site Content
    # Editor: Status picklist -> Draft, Save, reload reads Draft; the record
    # is then left Published (picklist + workflow). Every write is logged to
    # reports/live-writes-20261013.jsonl. The case says the dropdown lists
    # "exactly Draft and Published"; the Page Object notes a live third
    # option (Unpublished) -- asserted to the case, observed list attached.
    block_live_singleton_write(PAGE_RECORD, "Status picklist = Draft, then back to Published", tc_id="134937")
    ctx, editor_page = _role_session(browser, ROLE_EDITOR)
    try:
        status_draft_case(_p34_picklist(ChambersLawAdminPage(editor_page)), "134937", exact_options=True)
    finally:
        try:
            ctx.close()
        except Exception:  # noqa: BLE001
            pass


@allure.epic("About Us")
@allure.feature("Chamber's Law")
@allure.story("CMS authoring / admin")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Verify that the page Status dropdown offers and stores the Published value")
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.functional_low
@pytest.mark.pbi_129394
@pytest.mark.tc_134938
@pytest.mark.traceability("134938")
@allure.label("pbi", "129394")
@allure.label("testcase", "134938")
@CHAMBERS_LAW_XDIST_GROUP
@pytest.mark.timeout(480)
def test_chambers_law_cp_134938_the_page_status_dropdown_offers_and_stores_the_published_value(page, browser):
    # USER DECISION 2026-10-13 (P3/P4): runs only with
    # QC_ALLOW_LIVE_SINGLETON_WRITES=1 (else NOT APPLICABLE). As Site Content
    # Editor: precondition Status Draft (set + logged if needed), then
    # Published, Save, reload reads Published; left Published.
    block_live_singleton_write(PAGE_RECORD, "Status picklist Draft precondition, then Published", tc_id="134938")
    ctx, editor_page = _role_session(browser, ROLE_EDITOR)
    try:
        status_published_case(_p34_picklist(ChambersLawAdminPage(editor_page)), "134938")
    finally:
        try:
            ctx.close()
        except Exception:  # noqa: BLE001
            pass


@allure.epic("About Us")
@allure.feature("Chamber's Law")
@allure.story("CMS authoring / admin")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Verify that page Page ID, Created Date, and Last Modified Date are auto-populated and not editable")
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.functional_low
@pytest.mark.pbi_129394
@pytest.mark.tc_134939
@pytest.mark.traceability("134939")
@allure.label("pbi", "129394")
@allure.label("testcase", "134939")
@pytest.mark.skip(reason="Field-level validation case (Verify that page Page ID, Created Date, and Last Modified Date are auto-populated and not editable) is the SAFE category this batch was authorized to automate (validation fires before any persistent write, or the check+revert is reversible) -- but it requires reaching the Chamber's Law page/law-entry admin edit form in the Liferay Control Panel to interact with the field at all. This session's login attempt against qcdev (CmsLoginPage.login() via TEST_USER/TEST_PASSWORD, mirroring the navigation pattern already proven for the Departments and Board of Directors admin surfaces) timed out repeatedly (playwright._impl._errors.TimeoutError on the username-field fill, and on core/web/session_guard.py's re-authentication retries) -- consistent with the severe qcdev session/connection-limit flakiness already documented in login_page.py and org_structure_admin_page.py, but worse this session (login itself never completed). No stable locators for the Chamber's Law admin edit form (list/edit URL, per-field selectors) could be extracted or confirmed as a result. Skipped rather than invented -- see module docstring.")
def test_chambers_law_cp_134939_page_page_id_created_date_and_last_modified_date_are_auto_populated_and_not_edit(page):
    ...

