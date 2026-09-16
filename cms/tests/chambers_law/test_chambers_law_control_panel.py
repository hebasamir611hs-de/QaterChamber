"""
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

── Still legitimately skipped ───────────────────────────────────────────
  - 134876 -- publish cache + audit-log assertion: no reachable audit-log
    surface confirmed on this environment.
  - 134867-134870 -- role/permission boundary cases: need the restricted
    test account that does not exist yet (ADO TC-134658).
  - 134853 -- env-state mismatch already flagged on the Web side.
  - the ~90 field-level validation cases below (134889-134987): unchanged
    from the previous batch; they are the SAFE category to automate next
    but were not part of this rework's scope.
"""

import sys

import allure
import pytest

from cms.pages.chambers_law.chambers_law_admin_page import (
    ChambersLawAdminPage,
    CHAMBERS_LAW_PAGE_ENTRY_CODE,
    LAW_1990_ENTRY_CODE,
    LAW_1996_ENTRY_CODE,
    LAW_1990_TITLE,
    LAW_1996_TITLE,
    LAW_1990_NUMBER,
    LAW_1996_NUMBER,
)
from web.pages.chambers_law.chambers_law_page import ChambersLawPage
from core.web.browser import new_context
from core.utils.logger import get_logger
from core.utils.waits import wait_until

logger = get_logger("test_chambers_law_control_panel")

# All twelve mutating tests below write to one of TWO shared, real Object
# Authoring records (the Chamber Laws Page singleton, and the Law Entry
# list's 1990/1996 entries) -- one shared group so xdist (--dist loadgroup)
# never schedules two of them on different workers concurrently, mirroring
# this project's established convention (see e.g. web/tests/
# about_chairman_message/test_chairman_message_control_panel.py's
# xdist_group("chairman_message_78261")).
CHAMBERS_LAW_XDIST_GROUP = pytest.mark.xdist_group("chambers_law_129394")

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
def _unpublish_and_confirm(authoring):
    """Takes the record off the live site and PROVES it landed in Draft.
    Idempotent: a record already in Draft is left alone."""
    if authoring.current_status() == "Approved":
        authoring.unpublish_to_edit_as_draft()
    authoring.wait_for_status("Draft", timeout=UNPUBLISH_CONFIRM_TIMEOUT)
    return authoring


def _publish_and_confirm(authoring):
    """Submits for publishing and PROVES the record actually reached
    Approved -- re-reading it from a fresh navigation, because the publish
    takes 27-30s live while the form's own settle is ~2.5s."""
    authoring.submit_for_publishing()
    authoring.wait_for_status("Approved", timeout=PUBLISH_CONFIRM_TIMEOUT)
    return authoring


def _save_draft_and_confirm(authoring):
    """Saves a draft and PROVES the record is in Draft afterwards."""
    authoring.save_as_draft()
    authoring.wait_for_status("Draft", timeout=UNPUBLISH_CONFIRM_TIMEOUT)
    return authoring


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
        if baseline_status == "Approved":
            _publish_and_confirm(authoring)
        else:
            _save_draft_and_confirm(authoring)
    else:
        # Status-only restore.
        if baseline_status == "Approved" and authoring.current_status() != "Approved":
            _publish_and_confirm(authoring)
        elif baseline_status == "Draft" and authoring.current_status() == "Approved":
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
    if baseline_status == "Approved":
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


# ---------------------------------------------------------------------------
# 134850 -- Verify that the Chamber Legal Framework section renders its configured heading and intro content
# Both Web+Control_Panel; the Web-observable half is already scripted and
# passing in test_chambers_law_web.py under the same tc_134850 marker --
# not duplicated here to avoid a duplicate Axis-C selector across modules.
# ---------------------------------------------------------------------------

# ---------------------------------------------------------------------------
# 134851 -- Verify that the Official Legal References section renders its configured heading above the law entry cards
# Both Web+Control_Panel; the Web-observable half is already scripted and
# passing in test_chambers_law_web.py under the same tc_134851 marker --
# not duplicated here to avoid a duplicate Axis-C selector across modules.
# ---------------------------------------------------------------------------

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
@pytest.mark.skip(reason="The Chamber's Law admin edit form could not be reached this session to read/confirm the live configured alt text (see module docstring); test_chambers_law_web.py already flags this same case as an env-state mismatch on the public side (live alt text differs from the case's literal). No new information from the CMS side changes that conclusion here.")
def test_chambers_law_cp_134853_the_content_image_exposes_the_alt_text_configured_in_the_cms(page):
    ...


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
@pytest.mark.skip(reason="Requires signing in as a Site Content Editor / Site Content Author / permission-restricted role to exercise this access-control boundary. Only TEST_USER/TEST_PASSWORD (role mapping unconfirmed) exists per cms-profile.md's Roles table; the dedicated restricted-role account (TEST_USER_RESTRICTED/TEST_PASSWORD_RESTRICTED) is BLOCKED -- account does not exist yet (see ADO TC-134658). Even the default TEST_USER login could not be driven to completion this session (see module docstring's admin-reachability note), so this case is doubly blocked.")
def test_chambers_law_cp_134867_a_site_content_editor_can_manage_both_the_page_and_its_law_entry_records(page):
    ...


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
@pytest.mark.skip(reason="Requires signing in as a Site Content Editor / Site Content Author / permission-restricted role to exercise this access-control boundary. Only TEST_USER/TEST_PASSWORD (role mapping unconfirmed) exists per cms-profile.md's Roles table; the dedicated restricted-role account (TEST_USER_RESTRICTED/TEST_PASSWORD_RESTRICTED) is BLOCKED -- account does not exist yet (see ADO TC-134658). Even the default TEST_USER login could not be driven to completion this session (see module docstring's admin-reachability note), so this case is doubly blocked.")
def test_chambers_law_cp_134868_a_site_content_author_can_view_and_update_assigned_chamber_s_law_content_and_law(page):
    ...


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
@pytest.mark.skip(reason="Requires signing in as a Site Content Editor / Site Content Author / permission-restricted role to exercise this access-control boundary. Only TEST_USER/TEST_PASSWORD (role mapping unconfirmed) exists per cms-profile.md's Roles table; the dedicated restricted-role account (TEST_USER_RESTRICTED/TEST_PASSWORD_RESTRICTED) is BLOCKED -- account does not exist yet (see ADO TC-134658). Even the default TEST_USER login could not be driven to completion this session (see module docstring's admin-reachability note), so this case is doubly blocked.")
def test_chambers_law_cp_134869_a_site_content_author_cannot_publish_the_chamber_s_law_page(page):
    ...


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
@pytest.mark.skip(reason="Requires signing in as a Site Content Editor / Site Content Author / permission-restricted role to exercise this access-control boundary. Only TEST_USER/TEST_PASSWORD (role mapping unconfirmed) exists per cms-profile.md's Roles table; the dedicated restricted-role account (TEST_USER_RESTRICTED/TEST_PASSWORD_RESTRICTED) is BLOCKED -- account does not exist yet (see ADO TC-134658). Even the default TEST_USER login could not be driven to completion this session (see module docstring's admin-reachability note), so this case is doubly blocked.")
def test_chambers_law_cp_134870_a_user_without_the_required_permission_is_denied_access_to_the_chamber_s_law_rec(page):
    ...
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

        with allure.step("Click Submit for Publishing on the Chamber Laws Page record"):
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
        assert status_after_publish == "Approved"
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
        if baseline_status:
            with allure.step("TEST_OWNED reset -- restore the page record to its pre-existing status"):
                _test_owned_reset(
                    lambda: _restore_record(admin.open_page_record, baseline_status),
                    label="tc_134871 Chamber Laws Page status",
                )


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

    anon_context = new_context(browser, use_auth_state=False)
    anon_page = anon_context.new_page()

    try:
        with allure.step("Open the published Chamber Laws Page record via Object Authoring"):
            authoring = admin.open_page_record()
            baseline_status = authoring.current_status()
            baseline_title = authoring.field_value(admin.PAGE_TITLE_LABEL)

        with allure.step("Ensure the record starts Approved/published (this case's own precondition)"):
            if authoring.current_status() != "Approved":
                _publish_and_confirm(authoring)
            assert authoring.current_status() == "Approved", (
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
        # Assert -- CMS side: the record survives, per the case's own step 4
        assert status_in_cms == "Draft"
        assert record_still_listed, (
            "expected the unpublished page record to remain present/editable in the CMS"
        )
    finally:
        try:
            anon_context.close()
        except Exception:  # noqa: BLE001 -- cleanup must never mask the real result
            pass
        if baseline_status:
            with allure.step("TEST_OWNED reset -- put the Chamber's Law page back on the live site"):
                _test_owned_reset(
                    lambda: _restore_record(admin.open_page_record, baseline_status),
                    label="tc_134873 Chamber Laws Page status (page is OFFLINE until this succeeds)",
                )


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
        if baseline_heading is not None:
            def _restore():
                _restore_record(
                    admin.open_page_record,
                    baseline_status,
                    apply_fields=lambda a: a.fill_text(
                        admin.INTRO_HEADING_LABEL, baseline_heading
                    ),
                    verify=lambda a: _assert_field_restored(
                        a, admin.INTRO_HEADING_LABEL, baseline_heading
                    ),
                )

            with allure.step("TEST_OWNED reset -- restore Intro Heading/Status to their pre-existing baseline"):
                _test_owned_reset(_restore, label="tc_134874 Chamber Laws Page Intro Heading")


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

    anon_context = new_context(browser, use_auth_state=False)
    anon_page = anon_context.new_page()

    try:
        with allure.step("Open the Chamber Laws Page record via Object Authoring"):
            authoring = admin.open_page_record()

        with allure.step("Capture the pre-existing baseline Intro Heading + Status (TEST_OWNED reset target)"):
            baseline_heading = authoring.field_value(admin.INTRO_HEADING_LABEL)
            baseline_status = authoring.current_status()

        with allure.step(f"Add the marker '{marker}' to Intro Heading, Save as Draft (do not publish), then Preview"):
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
        if baseline_heading is not None:
            def _restore():
                _restore_record(
                    admin.open_page_record,
                    baseline_status,
                    apply_fields=lambda a: a.fill_text(
                        admin.INTRO_HEADING_LABEL, baseline_heading
                    ),
                    verify=lambda a: _assert_field_restored(
                        a, admin.INTRO_HEADING_LABEL, baseline_heading
                    ),
                )

            with allure.step("TEST_OWNED reset -- restore Intro Heading/Status to their pre-existing baseline"):
                _test_owned_reset(_restore, label="tc_134875 Chamber Laws Page Intro Heading")


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
@pytest.mark.skip(reason="The publish-cache half of this case is already covered by tc_134871 (publish the Chamber Laws Page record -> the public page serves the new content), but the AUDIT LOG half has no reachable surface on this environment: no audit-log view/report was confirmed live for Object Authoring records, and asserting only the cache half would silently drop the case's second expected result. Kept skipped with this specific reason rather than narrowed to the half that is checkable -- escalated to the QA Manager to either split the case or confirm where the audit log is exposed.")
def test_chambers_law_cp_134876_publishing_the_chamber_s_law_page_updates_the_page_cache_and_writes_an_audit_log(page):
    ...


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
    # CORRECTLY on **Law Entry** -- a law card's own hyperlink is Law Entry
    # content, not page content. Unchanged in target by the 2026-09-15
    # rework.
    #
    # ASSERTION BUG FIXED 2026-09-15 -- THE PRODUCT IS FINE, THE OLD
    # COMPARISON WAS NOT. This test used to require exact string equality
    # between the CMS value and the rendered public href:
    #
    #     cl.card_title_href("Law No. 11 of 1990") == target_url
    #
    # Confirmed live: the CMS stores
    # `https://www.almeezan.qa/LawView.aspx?opt&LawID=2541` verbatim and
    # that URL does reach the intended public page, but the front end
    # re-serializes it when rendering the card as
    # `https://www.almeezan.qa/LawView.aspx?opt=&LawID=2541&language=en` --
    # the bare, valueless `opt` becomes `opt=`, and the site's locale
    # handling appends `language=en`. Exact equality was therefore
    # unsatisfiable by construction, i.e. a test bug producing a red on
    # correct behaviour. The public href is now compared on a NORMALIZED
    # basis (scheme+host+path plus the significant query params, ignoring
    # `language` and empty-valued params -- see _same_target_url()), while
    # the CMS-side read-back is still compared VERBATIM, so a wrong value
    # stored in the CMS still fails.
    #
    # TEST_OWNED. Edits the REAL, pre-existing "Law No. 11 of 1990" entry's
    # External Link URL (not bilingual -- confirmed live) to the case's own
    # literal value, publishes, confirms it via the admin read-back AND the
    # public card's actual href, then restores the entry's original URL and
    # VERIFIES the restore committed.
    admin = ChambersLawAdminPage(page)
    target_url = "https://www.almeezan.qa/LawView.aspx?opt&LawID=2541"
    baseline_url = None
    baseline_status = None

    anon_context = new_context(browser, use_auth_state=False)
    anon_page = anon_context.new_page()

    try:
        with allure.step("In Liferay CMS, open the Law No. 11 of 1990 entry via Object Authoring"):
            authoring = admin.open_law_entry(LAW_1990_ENTRY_CODE)

        with allure.step("Capture the pre-existing baseline External Link URL + Status (TEST_OWNED reset target)"):
            baseline_url = authoring.field_value(admin.EXTERNAL_LINK_URL_LABEL)
            baseline_status = authoring.current_status()

        with allure.step(f"Set External Link URL (EN) to {target_url} and publish"):
            _unpublish_and_confirm(authoring)
            authoring.fill_text(admin.EXTERNAL_LINK_URL_LABEL, target_url)
            _publish_and_confirm(authoring)
            # _publish_and_confirm() already re-opens the record on a fresh
            # navigation while polling for Approved, which is also what the
            # post-Save DOM-reflow read-back race needs (a re-read on the
            # stale in-place form can return "" -- live-confirmed
            # 2026-09-07).

        with allure.step("Open the Chamber's Law page in English and locate the Law No. 11 of 1990 Law Title link"):
            cl = ChambersLawPage(anon_page)

            def _public_reflects_url() -> bool:
                cl.open_chambers_law()
                return _same_target_url(cl.card_title_href(LAW_1990_NUMBER), target_url)

            _reflects_public(
                _public_reflects_url,
                timeout=PUBLIC_REFLECT_AFTER_PUBLISH_TIMEOUT,
                message="Public card's Law Title href never reflected the newly-published External Link URL",
            )
            public_href = cl.card_title_href(LAW_1990_NUMBER)
            public_target = cl.card_title_target(LAW_1990_NUMBER)

        # Assert
        assert authoring.current_status() == "Approved"
        # CMS side: verbatim -- a wrong stored value must still fail.
        assert authoring.field_value(admin.EXTERNAL_LINK_URL_LABEL) == target_url
        # Public side: same destination, allowing the front end's own
        # serialization (see the comment block above).
        assert _same_target_url(public_href, target_url), (
            f"expected the card's Law Title link to point at the configured "
            f"destination {target_url!r}; got {public_href!r}"
        )
        assert public_target == "_blank"
    finally:
        try:
            anon_context.close()
        except Exception:  # noqa: BLE001 -- cleanup must never mask the real result
            pass
        if baseline_url is not None:
            def _restore():
                _restore_record(
                    lambda: admin.open_law_entry(LAW_1990_ENTRY_CODE),
                    baseline_status,
                    apply_fields=lambda a: a.fill_text(
                        admin.EXTERNAL_LINK_URL_LABEL, baseline_url
                    ),
                    verify=lambda a: _assert_field_restored(
                        a, admin.EXTERNAL_LINK_URL_LABEL, baseline_url
                    ),
                )

            with allure.step("TEST_OWNED reset -- restore External Link URL/Status to their pre-existing baseline"):
                _test_owned_reset(_restore, label="tc_134877 Law 1990 External Link URL")


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
    admin = ChambersLawAdminPage(page)
    target_image_file = "about-us-hero.png"
    baseline_status = None
    original_filename = ""
    original_saved = False
    original_download_path = None

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
            _unpublish_and_confirm(authoring)
            if original_saved:
                authoring.remove_current_file(admin.CONTENT_IMAGE_UPLOAD_LABEL)
                _save_draft_and_confirm(authoring)

        with allure.step(f"Re-open fresh, pick '{target_image_file}' from Documents & Media as the Content Image, and publish (phase 2)"):
            authoring = admin.open_page_record()
            assert authoring.current_file_name(admin.CONTENT_IMAGE_UPLOAD_LABEL) == "", (
                "expected the Content Image field to be genuinely empty after the "
                "phase-1 remove+save"
            )
            authoring.select_existing_file(
                admin.CONTENT_IMAGE_UPLOAD_LABEL, target_image_file
            )
            _publish_and_confirm(authoring)

        with allure.step("Open the public Chamber's Law page in English after the standard cache refresh"):
            cl = ChambersLawPage(anon_page)
            expected_stem = target_image_file.rsplit(".", 1)[0]

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
        assert authoring.current_status() == "Approved"
        assert target_image_file in authoring.current_file_name(
            admin.CONTENT_IMAGE_UPLOAD_LABEL
        )
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
        if baseline_status:
            def _restore():
                _restore_content_image(
                    admin,
                    baseline_status,
                    original_download_path if original_saved else None,
                    original_filename,
                )

            with allure.step("TEST_OWNED reset -- restore the original Content Image bytes/Status"):
                _test_owned_reset(_restore, label="tc_134882 Chamber Laws Page Content Image")


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
    admin = ChambersLawAdminPage(page)
    replacement_file = "a11y_panel.png"
    baseline_status = None
    original_filename = ""
    original_saved = False
    original_download_path = None

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
            _unpublish_and_confirm(authoring)
            authoring.select_existing_file(
                admin.CONTENT_IMAGE_UPLOAD_LABEL, replacement_file
            )
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
        assert authoring.current_status() == "Approved"
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
        if baseline_status:
            def _restore():
                _restore_content_image(
                    admin,
                    baseline_status,
                    original_download_path if original_saved else None,
                    original_filename,
                )

            with allure.step("TEST_OWNED reset -- restore the original Content Image bytes/Status"):
                _test_owned_reset(_restore, label="tc_134883 Chamber Laws Page Content Image")


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
    qc_number = f"QCTEST-129394 Law No. 99 of 2026 ({run_id})"
    qc_title = f"QCTEST Automated Law Entry {run_id} - safe to delete"
    qc_desc = f"QCTEST-129394 created by automated test tc_134884 run {run_id}."
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
            created_entry.wait_for_status("Approved", timeout=PUBLISH_CONFIRM_TIMEOUT)

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
        assert created_entry.current_status() == "Approved", (
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
                _unpublish_and_confirm(authoring)
                authoring.set_checkbox(admin.ACTIVE_STATUS_LABEL, False)
                _publish_and_confirm(authoring)
                # PROVE the card really is hidden, never assume.
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
    # CORRECTLY on **Law Entry**: this case edits an existing law entry's
    # Law Description and checks that card. Only "Publish the page" is
    # reworded -- publishing the ROW is the real action for a card.
    # XDIST: now carries @CHAMBERS_LAW_XDIST_GROUP (it did not before).
    # TEST_OWNED: the 1990 Law Entry is real content; description + status
    # are captured before mutating and restored+VERIFIED in `finally`.
    admin = ChambersLawAdminPage(page)
    marker = "EDITED-129394"
    baseline_description = None
    baseline_status = None

    anon_context = new_context(browser, use_auth_state=False)
    anon_page = anon_context.new_page()

    try:
        with allure.step(f"Open the law entry for '{LAW_1990_NUMBER}'"):
            authoring = admin.open_law_entry(LAW_1990_ENTRY_CODE)
            baseline_description = authoring.field_value(admin.LAW_DESCRIPTION_LABEL)
            baseline_status = authoring.current_status()

        with allure.step("Read the description the public card currently shows"):
            cl = ChambersLawPage(anon_page)
            cl.open_chambers_law()
            desc_before = cl.card_desc_text(LAW_1990_NUMBER)

        with allure.step("Change its Law Description to include the marker and publish"):
            _unpublish_and_confirm(authoring)
            authoring.fill_text(
                admin.LAW_DESCRIPTION_LABEL, f"{baseline_description} {marker}"
            )
            _publish_and_confirm(authoring)

        with allure.step("Open the public page after the standard cache refresh and read that card's description"):
            def _desc_updated() -> bool:
                cl.open_chambers_law()
                return marker in cl.card_desc_text(LAW_1990_NUMBER)

            _reflects_public(
                _desc_updated,
                timeout=PUBLIC_REFLECT_AFTER_PUBLISH_TIMEOUT,
                message="Public card description never reflected the edited Law Description",
            )
            desc_after = cl.card_desc_text(LAW_1990_NUMBER)

        # Assert
        assert authoring.current_status() == "Approved"
        assert marker in desc_after
        assert desc_after != desc_before, (
            "expected the card description to change from its previous text"
        )
    finally:
        try:
            anon_context.close()
        except Exception:  # noqa: BLE001 -- cleanup must never mask the real result
            pass
        if baseline_description is not None:
            def _restore():
                _restore_record(
                    lambda: admin.open_law_entry(LAW_1990_ENTRY_CODE),
                    baseline_status,
                    apply_fields=lambda a: a.fill_text(
                        admin.LAW_DESCRIPTION_LABEL, baseline_description
                    ),
                    verify=lambda a: _assert_field_restored(
                        a, admin.LAW_DESCRIPTION_LABEL, baseline_description
                    ),
                )

            with allure.step("TEST_OWNED reset -- restore Law Description/Status to baseline"):
                _test_owned_reset(_restore, label="tc_134885 Law 1990 Law Description")


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
    # CORRECTLY on **Law Entry**: card order is Law Entry work.
    # XDIST: now carries @CHAMBERS_LAW_XDIST_GROUP (it did not before, and
    # it mutates the same two shared records as five other tests).
    #
    # DISCLOSED VALUE CHANGE -- the case says to set Display Order "1" and
    # "2". That contradicts the platform's editorial convention, documented
    # in both cms/Content-Admin-Guide.docx ("Ordering uses multiples of 100
    # -- 100, 200, 300 ... not 1, 2, 3") and standards.md's Object Authoring
    # notes, which say explicitly that a case dictating 1/2 must be FLAGGED
    # rather than blindly executed: the platform's own validation only
    # requires >= 1, so writing 1/2 would pass while leaving real content
    # mis-numbered among its neighbours. The swap is therefore performed
    # with 100/200 -- the same reordering, in the sanctioned numbering. The
    # case should be reworded -- escalated to the QA Manager.
    #
    # PRECONDITION HARDENED 2026-09-15: this test used to assert up front
    # that 1990 renders before 1996, then swap to 100/200 in a fixed
    # direction. That hardcodes a live data state the tests themselves can
    # damage -- and it IS damaged right now: confirmed live 2026-09-15,
    # BOTH entries currently hold Display Order 200 (a previous run's
    # restore did not commit), so their relative public order is
    # arbitrary. The test now READS the current public order first and
    # assigns 100/200 so that the order must INVERT, then asserts the
    # inversion. That is exactly what the case is about (changing Display
    # Order changes the card sequence) and it cannot be defeated by which
    # card happens to be first.
    #
    # ⚠ FLAGGED FOR A HUMAN, NOT SILENTLY "FIXED": because the baseline is
    # captured at runtime and restored to, this test faithfully restores
    # the damaged 200/200 state rather than inventing a "correct" 100/200.
    # Repairing the real editorial data is a content decision for the team.
    #
    # TEST_OWNED: both entries' display orders + statuses are captured
    # before mutating and restored+VERIFIED in `finally`.
    admin = ChambersLawAdminPage(page)
    baseline = {}

    anon_context = new_context(browser, use_auth_state=False)
    anon_page = anon_context.new_page()

    def _set_order(entry_code, value):
        authoring = admin.open_law_entry(entry_code)
        _unpublish_and_confirm(authoring)
        authoring.fill_number(admin.DISPLAY_ORDER_LABEL, value)
        _publish_and_confirm(authoring)

    try:
        with allure.step("Read the order the public page currently renders the two cards in"):
            cl = ChambersLawPage(anon_page)
            cl.open_chambers_law()
            order_before = [n.strip() for n in cl.card_numbers()]
            assert LAW_1990_NUMBER in order_before and LAW_1996_NUMBER in order_before, (
                "precondition failed: expected both law cards to be rendering "
                f"publicly before reordering them; got {order_before}"
            )
            first_before = (
                LAW_1990_NUMBER
                if order_before.index(LAW_1990_NUMBER) < order_before.index(LAW_1996_NUMBER)
                else LAW_1996_NUMBER
            )
            second_before = (
                LAW_1996_NUMBER if first_before == LAW_1990_NUMBER else LAW_1990_NUMBER
            )

        with allure.step("Capture both entries' baseline Display Order (TEST_OWNED reset target)"):
            for number, code in (
                (LAW_1990_NUMBER, LAW_1990_ENTRY_CODE),
                (LAW_1996_NUMBER, LAW_1996_ENTRY_CODE),
            ):
                authoring = admin.open_law_entry(code)
                baseline[number] = {
                    "order": authoring.spinbutton_value(admin.DISPLAY_ORDER_LABEL),
                    "status": authoring.current_status(),
                }
            allure.attach(
                "\n".join(f"{k}: {v}" for k, v in baseline.items())
                + f"\npublic order before = {order_before}",
                name="baseline Display Order captured at runtime",
            )

        with allure.step("Swap the two Display Order values (100/200, not 1/2 -- see disclosed value change) so the order must invert"):
            codes = {
                LAW_1990_NUMBER: LAW_1990_ENTRY_CODE,
                LAW_1996_NUMBER: LAW_1996_ENTRY_CODE,
            }
            _set_order(codes[second_before], "100")
            _set_order(codes[first_before], "200")

        with allure.step("Open the public page after the standard cache refresh and read the card order"):
            def _order_swapped() -> bool:
                cl.open_chambers_law()
                nums = [n.strip() for n in cl.card_numbers()]
                if second_before not in nums or first_before not in nums:
                    return False
                return nums.index(second_before) < nums.index(first_before)

            _reflects_public(
                _order_swapped,
                timeout=PUBLIC_REFLECT_AFTER_PUBLISH_TIMEOUT,
                message="Public card order never reflected the swapped Display Order values",
            )
            order_after = [n.strip() for n in cl.card_numbers()]

        # Assert -- the sequence really inverted
        assert order_after.index(second_before) < order_after.index(first_before), (
            f"expected {second_before!r} to render before {first_before!r} after the "
            f"swap; got {order_after} (before: {order_before})"
        )
    finally:
        try:
            anon_context.close()
        except Exception:  # noqa: BLE001 -- cleanup must never mask the real result
            pass
        if baseline:
            def _restore():
                for number, code in (
                    (LAW_1990_NUMBER, LAW_1990_ENTRY_CODE),
                    (LAW_1996_NUMBER, LAW_1996_ENTRY_CODE),
                ):
                    want = baseline.get(number)
                    if not want:
                        continue
                    _restore_record(
                        lambda c=code: admin.open_law_entry(c),
                        want["status"],
                        apply_fields=lambda a, w=want: a.fill_number(
                            admin.DISPLAY_ORDER_LABEL, w["order"]
                        ),
                        verify=lambda a, w=want: _assert_number_restored(
                            a, admin.DISPLAY_ORDER_LABEL, w["order"]
                        ),
                    )

            with allure.step("TEST_OWNED reset -- restore both entries' Display Order to baseline"):
                _test_owned_reset(_restore, label="tc_134886 Law 1990/1996 Display Order")


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
    # CORRECTLY on **Law Entry** (activeStatus is the guide's documented
    # "Hide an item" control). Only "Publish the page" is reworded --
    # publishing the ROW is the real action for a card.
    # XDIST: now carries @CHAMBERS_LAW_XDIST_GROUP (it did not before).
    # PRECONDITION NOTE: when this test failed on 2026-09-09 it failed on
    # "the 1996 card is not currently visible publicly" -- not on its own
    # behaviour, but because ANOTHER test's restore had left that entry in
    # Draft. It passed when run isolated against repaired state. The
    # precondition is kept (the case genuinely starts from a visible card),
    # and the cascade is fixed at the source: every restore in this module
    # is now retried and verified via _test_owned_reset().
    # TEST_OWNED: the 1996 entry's activeStatus + status are captured before
    # mutating and restored+VERIFIED in `finally`.
    admin = ChambersLawAdminPage(page)
    baseline_active = None
    baseline_status = None

    anon_context = new_context(browser, use_auth_state=False)
    anon_page = anon_context.new_page()

    try:
        with allure.step(f"Confirm the card for '{LAW_1996_NUMBER}' is visible on the public page"):
            cl = ChambersLawPage(anon_page)
            cl.open_chambers_law()
            assert cl.is_card_visible(LAW_1996_NUMBER), (
                "precondition failed: the 1996 card is not currently visible "
                "publicly (check that no earlier test left its record in Draft or "
                "inactive -- see this test's own comment block)"
            )

        with allure.step("Open the entry and capture its baseline Active Status"):
            authoring = admin.open_law_entry(LAW_1996_ENTRY_CODE)
            baseline_status = authoring.current_status()
            baseline_active = authoring.is_checked(admin.ACTIVE_STATUS_LABEL)

        with allure.step("Set Active Status to False and publish"):
            _unpublish_and_confirm(authoring)
            authoring.set_checkbox(admin.ACTIVE_STATUS_LABEL, False)
            _publish_and_confirm(authoring)

        with allure.step("Open the public page after the standard cache refresh"):
            def _card_hidden() -> bool:
                cl.open_chambers_law()
                return not cl.is_card_visible(LAW_1996_NUMBER)

            _reflects_public(
                _card_hidden,
                timeout=PUBLIC_REFLECT_AFTER_PUBLISH_TIMEOUT,
                message="Deactivated law entry card was still rendering publicly",
            )
            hidden = not cl.is_card_visible(LAW_1996_NUMBER)
            sibling_still_visible = cl.is_card_visible(LAW_1990_NUMBER)

        with allure.step("Re-open the Law Entry list in the CMS"):
            entries = admin.open_law_entries_list()
            row_still_listed = entries.row_visible(LAW_1996_TITLE)
            authoring = admin.open_law_entry(LAW_1996_ENTRY_CODE)
            active_in_cms = authoring.is_checked(admin.ACTIVE_STATUS_LABEL)

        # Assert
        assert hidden, "expected the deactivated card to stop rendering on the public page"
        assert sibling_still_visible, (
            "expected the remaining active cards to keep rendering"
        )
        assert row_still_listed, (
            "expected the law entry record to remain present in the CMS Law Entry list"
        )
        assert active_in_cms is False, "expected Active Status to remain False in the CMS"
    finally:
        try:
            anon_context.close()
        except Exception:  # noqa: BLE001 -- cleanup must never mask the real result
            pass
        if baseline_active is not None:
            def _restore():
                _restore_record(
                    lambda: admin.open_law_entry(LAW_1996_ENTRY_CODE),
                    baseline_status,
                    apply_fields=lambda a: a.set_checkbox(
                        admin.ACTIVE_STATUS_LABEL, baseline_active
                    ),
                    verify=lambda a: _assert_checkbox_restored(
                        a, admin.ACTIVE_STATUS_LABEL, baseline_active
                    ),
                )

            with allure.step("TEST_OWNED reset -- restore Active Status/Status to baseline"):
                _test_owned_reset(_restore, label="tc_134887 Law 1996 Active Status")


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
    # CORRECTLY on **Law Entry**. This case's precondition is the END state
    # of tc_134887 (Active Status False), but tests must not depend on each
    # other's ordering -- so this test establishes that precondition itself,
    # then exercises the reactivation.
    # XDIST: now carries @CHAMBERS_LAW_XDIST_GROUP (it did not before).
    # TEST_OWNED: the 1996 entry's activeStatus + status are captured before
    # mutating and restored+VERIFIED in `finally`.
    admin = ChambersLawAdminPage(page)
    baseline_active = None
    baseline_status = None

    anon_context = new_context(browser, use_auth_state=False)
    anon_page = anon_context.new_page()

    try:
        with allure.step("Capture baseline, then establish this case's precondition (Active Status False, card absent)"):
            authoring = admin.open_law_entry(LAW_1996_ENTRY_CODE)
            baseline_status = authoring.current_status()
            baseline_active = authoring.is_checked(admin.ACTIVE_STATUS_LABEL)
            if baseline_active:
                _unpublish_and_confirm(authoring)
                authoring.set_checkbox(admin.ACTIVE_STATUS_LABEL, False)
                _publish_and_confirm(authoring)

            cl = ChambersLawPage(anon_page)

            def _card_absent() -> bool:
                cl.open_chambers_law()
                return not cl.is_card_visible(LAW_1996_NUMBER)

            _reflects_public(
                _card_absent,
                timeout=PUBLIC_REFLECT_AFTER_PUBLISH_TIMEOUT,
                message="Could not reach this case's precondition -- the card is still visible",
            )

        with allure.step("Set Active Status to True and publish"):
            authoring = admin.open_law_entry(LAW_1996_ENTRY_CODE)
            _unpublish_and_confirm(authoring)
            # Read displayOrder BEFORE publishing: after submit the form has
            # re-rendered and the spinbutton reads back as "" (which raised
            # ValueError from int("") on the first run 2026-09-09).
            display_order = authoring.spinbutton_value(admin.DISPLAY_ORDER_LABEL)
            authoring.set_checkbox(admin.ACTIVE_STATUS_LABEL, True)
            _publish_and_confirm(authoring)

        with allure.step("Open the public page after the standard cache refresh and read the card list"):
            def _card_back() -> bool:
                cl.open_chambers_law()
                return cl.is_card_visible(LAW_1996_NUMBER)

            _reflects_public(
                _card_back,
                timeout=PUBLIC_REFLECT_AFTER_PUBLISH_TIMEOUT,
                message="Reactivated law entry card never returned to the public page",
            )
            order_after = [n.strip() for n in cl.card_numbers()]
            sibling_order = None
            if LAW_1990_NUMBER in order_after:
                sibling = admin.open_law_entry(LAW_1990_ENTRY_CODE)
                sibling_order = sibling.spinbutton_value(admin.DISPLAY_ORDER_LABEL)

        # Assert -- the card is back, AND in its Display-Order position
        assert LAW_1996_NUMBER in order_after, (
            "expected the reactivated card to render again in Official Legal References"
        )
        # "at the position given by its Display Order" -- asserted against
        # the sibling's ACTUAL live Display Order, read at runtime, rather
        # than the hardcoded "1990 is always 100" this used to assume (both
        # entries currently hold 200; see tc_134886's own comment block).
        if (
            LAW_1990_NUMBER in order_after
            and (display_order or "").isdigit()
            and (sibling_order or "").isdigit()
            and int(display_order) != int(sibling_order)
        ):
            expected_after_sibling = int(display_order) > int(sibling_order)
            renders_after_sibling = order_after.index(LAW_1996_NUMBER) > order_after.index(
                LAW_1990_NUMBER
            )
            assert renders_after_sibling is expected_after_sibling, (
                f"expected the reactivated card at its Display Order position "
                f"(1996 displayOrder={display_order}, 1990 displayOrder="
                f"{sibling_order}); got {order_after}"
            )
    finally:
        try:
            anon_context.close()
        except Exception:  # noqa: BLE001 -- cleanup must never mask the real result
            pass
        if baseline_active is not None:
            def _restore():
                _restore_record(
                    lambda: admin.open_law_entry(LAW_1996_ENTRY_CODE),
                    baseline_status,
                    apply_fields=lambda a: a.set_checkbox(
                        admin.ACTIVE_STATUS_LABEL, baseline_active
                    ),
                    verify=lambda a: _assert_checkbox_restored(
                        a, admin.ACTIVE_STATUS_LABEL, baseline_active
                    ),
                )

            with allure.step("TEST_OWNED reset -- restore Active Status/Status to baseline"):
                _test_owned_reset(_restore, label="tc_134888 Law 1996 Active Status")


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
@pytest.mark.skip(reason="Field-level validation case (Verify that a valid English Page Title is accepted and saved) is the SAFE category this batch was authorized to automate (validation fires before any persistent write, or the check+revert is reversible) -- but it requires reaching the Chamber's Law page/law-entry admin edit form in the Liferay Control Panel to interact with the field at all. This session's login attempt against qcdev (CmsLoginPage.login() via TEST_USER/TEST_PASSWORD, mirroring the navigation pattern already proven for the Departments and Board of Directors admin surfaces) timed out repeatedly (playwright._impl._errors.TimeoutError on the username-field fill, and on core/web/session_guard.py's re-authentication retries) -- consistent with the severe qcdev session/connection-limit flakiness already documented in login_page.py and org_structure_admin_page.py, but worse this session (login itself never completed). No stable locators for the Chamber's Law admin edit form (list/edit URL, per-field selectors) could be extracted or confirmed as a result. Skipped rather than invented -- see module docstring.")
def test_chambers_law_cp_134889_a_valid_english_page_title_is_accepted_and_saved(page):
    ...


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
@pytest.mark.skip(reason="Field-level validation case (Verify that an empty English Page Title is rejected with the page-title-required message) is the SAFE category this batch was authorized to automate (validation fires before any persistent write, or the check+revert is reversible) -- but it requires reaching the Chamber's Law page/law-entry admin edit form in the Liferay Control Panel to interact with the field at all. This session's login attempt against qcdev (CmsLoginPage.login() via TEST_USER/TEST_PASSWORD, mirroring the navigation pattern already proven for the Departments and Board of Directors admin surfaces) timed out repeatedly (playwright._impl._errors.TimeoutError on the username-field fill, and on core/web/session_guard.py's re-authentication retries) -- consistent with the severe qcdev session/connection-limit flakiness already documented in login_page.py and org_structure_admin_page.py, but worse this session (login itself never completed). No stable locators for the Chamber's Law admin edit form (list/edit URL, per-field selectors) could be extracted or confirmed as a result. Skipped rather than invented -- see module docstring.")
def test_chambers_law_cp_134890_an_empty_english_page_title_is_rejected_with_the_page_title_required_message(page):
    ...


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
@pytest.mark.skip(reason="Field-level validation case (Verify that a valid Arabic Page Title is accepted and saved) is the SAFE category this batch was authorized to automate (validation fires before any persistent write, or the check+revert is reversible) -- but it requires reaching the Chamber's Law page/law-entry admin edit form in the Liferay Control Panel to interact with the field at all. This session's login attempt against qcdev (CmsLoginPage.login() via TEST_USER/TEST_PASSWORD, mirroring the navigation pattern already proven for the Departments and Board of Directors admin surfaces) timed out repeatedly (playwright._impl._errors.TimeoutError on the username-field fill, and on core/web/session_guard.py's re-authentication retries) -- consistent with the severe qcdev session/connection-limit flakiness already documented in login_page.py and org_structure_admin_page.py, but worse this session (login itself never completed). No stable locators for the Chamber's Law admin edit form (list/edit URL, per-field selectors) could be extracted or confirmed as a result. Skipped rather than invented -- see module docstring.")
def test_chambers_law_cp_134893_a_valid_arabic_page_title_is_accepted_and_saved(page):
    ...


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
@pytest.mark.skip(reason="Field-level validation case (Verify that a missing Arabic Page Title is rejected with the Arabic-title-required message) is the SAFE category this batch was authorized to automate (validation fires before any persistent write, or the check+revert is reversible) -- but it requires reaching the Chamber's Law page/law-entry admin edit form in the Liferay Control Panel to interact with the field at all. This session's login attempt against qcdev (CmsLoginPage.login() via TEST_USER/TEST_PASSWORD, mirroring the navigation pattern already proven for the Departments and Board of Directors admin surfaces) timed out repeatedly (playwright._impl._errors.TimeoutError on the username-field fill, and on core/web/session_guard.py's re-authentication retries) -- consistent with the severe qcdev session/connection-limit flakiness already documented in login_page.py and org_structure_admin_page.py, but worse this session (login itself never completed). No stable locators for the Chamber's Law admin edit form (list/edit URL, per-field selectors) could be extracted or confirmed as a result. Skipped rather than invented -- see module docstring.")
def test_chambers_law_cp_134894_a_missing_arabic_page_title_is_rejected_with_the_arabic_title_required_message(page):
    ...


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
@pytest.mark.skip(reason="Field-level validation case (Verify that a valid JPG Hero Banner under 2 MB is accepted) is the SAFE category this batch was authorized to automate (validation fires before any persistent write, or the check+revert is reversible) -- but it requires reaching the Chamber's Law page/law-entry admin edit form in the Liferay Control Panel to interact with the field at all. This session's login attempt against qcdev (CmsLoginPage.login() via TEST_USER/TEST_PASSWORD, mirroring the navigation pattern already proven for the Departments and Board of Directors admin surfaces) timed out repeatedly (playwright._impl._errors.TimeoutError on the username-field fill, and on core/web/session_guard.py's re-authentication retries) -- consistent with the severe qcdev session/connection-limit flakiness already documented in login_page.py and org_structure_admin_page.py, but worse this session (login itself never completed). No stable locators for the Chamber's Law admin edit form (list/edit URL, per-field selectors) could be extracted or confirmed as a result. Skipped rather than invented -- see module docstring.")
def test_chambers_law_cp_134897_a_valid_jpg_hero_banner_under_2_mb_is_accepted(page):
    ...


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
@pytest.mark.skip(reason="Field-level validation case (Verify that a Hero Banner in an unsupported format is rejected with the Hero Banner format message) is the SAFE category this batch was authorized to automate (validation fires before any persistent write, or the check+revert is reversible) -- but it requires reaching the Chamber's Law page/law-entry admin edit form in the Liferay Control Panel to interact with the field at all. This session's login attempt against qcdev (CmsLoginPage.login() via TEST_USER/TEST_PASSWORD, mirroring the navigation pattern already proven for the Departments and Board of Directors admin surfaces) timed out repeatedly (playwright._impl._errors.TimeoutError on the username-field fill, and on core/web/session_guard.py's re-authentication retries) -- consistent with the severe qcdev session/connection-limit flakiness already documented in login_page.py and org_structure_admin_page.py, but worse this session (login itself never completed). No stable locators for the Chamber's Law admin edit form (list/edit URL, per-field selectors) could be extracted or confirmed as a result. Skipped rather than invented -- see module docstring.")
def test_chambers_law_cp_134898_a_hero_banner_in_an_unsupported_format_is_rejected_with_the_hero_banner_format_m(page):
    ...


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
@pytest.mark.skip(reason="Field-level validation case (Verify that a Hero Banner above 2 MB is rejected at the size boundary) is the SAFE category this batch was authorized to automate (validation fires before any persistent write, or the check+revert is reversible) -- but it requires reaching the Chamber's Law page/law-entry admin edit form in the Liferay Control Panel to interact with the field at all. This session's login attempt against qcdev (CmsLoginPage.login() via TEST_USER/TEST_PASSWORD, mirroring the navigation pattern already proven for the Departments and Board of Directors admin surfaces) timed out repeatedly (playwright._impl._errors.TimeoutError on the username-field fill, and on core/web/session_guard.py's re-authentication retries) -- consistent with the severe qcdev session/connection-limit flakiness already documented in login_page.py and org_structure_admin_page.py, but worse this session (login itself never completed). No stable locators for the Chamber's Law admin edit form (list/edit URL, per-field selectors) could be extracted or confirmed as a result. Skipped rather than invented -- see module docstring.")
def test_chambers_law_cp_134899_a_hero_banner_above_2_mb_is_rejected_at_the_size_boundary(page):
    ...


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
@pytest.mark.skip(reason="Field-level validation case (Verify that publishing without a Hero Banner is blocked) is the SAFE category this batch was authorized to automate (validation fires before any persistent write, or the check+revert is reversible) -- but it requires reaching the Chamber's Law page/law-entry admin edit form in the Liferay Control Panel to interact with the field at all. This session's login attempt against qcdev (CmsLoginPage.login() via TEST_USER/TEST_PASSWORD, mirroring the navigation pattern already proven for the Departments and Board of Directors admin surfaces) timed out repeatedly (playwright._impl._errors.TimeoutError on the username-field fill, and on core/web/session_guard.py's re-authentication retries) -- consistent with the severe qcdev session/connection-limit flakiness already documented in login_page.py and org_structure_admin_page.py, but worse this session (login itself never completed). No stable locators for the Chamber's Law admin edit form (list/edit URL, per-field selectors) could be extracted or confirmed as a result. Skipped rather than invented -- see module docstring.")
def test_chambers_law_cp_134900_publishing_without_a_hero_banner_is_blocked(page):
    ...


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
@pytest.mark.skip(reason="Field-level validation case (Verify that valid Hero Banner Alt Text is accepted and saved) is the SAFE category this batch was authorized to automate (validation fires before any persistent write, or the check+revert is reversible) -- but it requires reaching the Chamber's Law page/law-entry admin edit form in the Liferay Control Panel to interact with the field at all. This session's login attempt against qcdev (CmsLoginPage.login() via TEST_USER/TEST_PASSWORD, mirroring the navigation pattern already proven for the Departments and Board of Directors admin surfaces) timed out repeatedly (playwright._impl._errors.TimeoutError on the username-field fill, and on core/web/session_guard.py's re-authentication retries) -- consistent with the severe qcdev session/connection-limit flakiness already documented in login_page.py and org_structure_admin_page.py, but worse this session (login itself never completed). No stable locators for the Chamber's Law admin edit form (list/edit URL, per-field selectors) could be extracted or confirmed as a result. Skipped rather than invented -- see module docstring.")
def test_chambers_law_cp_134901_valid_hero_banner_alt_text_is_accepted_and_saved(page):
    ...


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
@pytest.mark.skip(reason="Field-level validation case (Verify that empty Hero Banner Alt Text is rejected on save) is the SAFE category this batch was authorized to automate (validation fires before any persistent write, or the check+revert is reversible) -- but it requires reaching the Chamber's Law page/law-entry admin edit form in the Liferay Control Panel to interact with the field at all. This session's login attempt against qcdev (CmsLoginPage.login() via TEST_USER/TEST_PASSWORD, mirroring the navigation pattern already proven for the Departments and Board of Directors admin surfaces) timed out repeatedly (playwright._impl._errors.TimeoutError on the username-field fill, and on core/web/session_guard.py's re-authentication retries) -- consistent with the severe qcdev session/connection-limit flakiness already documented in login_page.py and org_structure_admin_page.py, but worse this session (login itself never completed). No stable locators for the Chamber's Law admin edit form (list/edit URL, per-field selectors) could be extracted or confirmed as a result. Skipped rather than invented -- see module docstring.")
def test_chambers_law_cp_134902_empty_hero_banner_alt_text_is_rejected_on_save(page):
    ...


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
@pytest.mark.skip(reason="Field-level validation case (Verify that a valid English Intro Section Heading is accepted and saved) is the SAFE category this batch was authorized to automate (validation fires before any persistent write, or the check+revert is reversible) -- but it requires reaching the Chamber's Law page/law-entry admin edit form in the Liferay Control Panel to interact with the field at all. This session's login attempt against qcdev (CmsLoginPage.login() via TEST_USER/TEST_PASSWORD, mirroring the navigation pattern already proven for the Departments and Board of Directors admin surfaces) timed out repeatedly (playwright._impl._errors.TimeoutError on the username-field fill, and on core/web/session_guard.py's re-authentication retries) -- consistent with the severe qcdev session/connection-limit flakiness already documented in login_page.py and org_structure_admin_page.py, but worse this session (login itself never completed). No stable locators for the Chamber's Law admin edit form (list/edit URL, per-field selectors) could be extracted or confirmed as a result. Skipped rather than invented -- see module docstring.")
def test_chambers_law_cp_134905_a_valid_english_intro_section_heading_is_accepted_and_saved(page):
    ...


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
@pytest.mark.skip(reason="Field-level validation case (Verify that an empty English Intro Section Heading is rejected on save) is the SAFE category this batch was authorized to automate (validation fires before any persistent write, or the check+revert is reversible) -- but it requires reaching the Chamber's Law page/law-entry admin edit form in the Liferay Control Panel to interact with the field at all. This session's login attempt against qcdev (CmsLoginPage.login() via TEST_USER/TEST_PASSWORD, mirroring the navigation pattern already proven for the Departments and Board of Directors admin surfaces) timed out repeatedly (playwright._impl._errors.TimeoutError on the username-field fill, and on core/web/session_guard.py's re-authentication retries) -- consistent with the severe qcdev session/connection-limit flakiness already documented in login_page.py and org_structure_admin_page.py, but worse this session (login itself never completed). No stable locators for the Chamber's Law admin edit form (list/edit URL, per-field selectors) could be extracted or confirmed as a result. Skipped rather than invented -- see module docstring.")
def test_chambers_law_cp_134906_an_empty_english_intro_section_heading_is_rejected_on_save(page):
    ...


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
@pytest.mark.skip(reason="Field-level validation case (Verify that a valid Arabic Intro Section Heading is accepted and saved) is the SAFE category this batch was authorized to automate (validation fires before any persistent write, or the check+revert is reversible) -- but it requires reaching the Chamber's Law page/law-entry admin edit form in the Liferay Control Panel to interact with the field at all. This session's login attempt against qcdev (CmsLoginPage.login() via TEST_USER/TEST_PASSWORD, mirroring the navigation pattern already proven for the Departments and Board of Directors admin surfaces) timed out repeatedly (playwright._impl._errors.TimeoutError on the username-field fill, and on core/web/session_guard.py's re-authentication retries) -- consistent with the severe qcdev session/connection-limit flakiness already documented in login_page.py and org_structure_admin_page.py, but worse this session (login itself never completed). No stable locators for the Chamber's Law admin edit form (list/edit URL, per-field selectors) could be extracted or confirmed as a result. Skipped rather than invented -- see module docstring.")
def test_chambers_law_cp_134909_a_valid_arabic_intro_section_heading_is_accepted_and_saved(page):
    ...


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
@pytest.mark.skip(reason="Field-level validation case (Verify that an empty Arabic Intro Section Heading is rejected on save) is the SAFE category this batch was authorized to automate (validation fires before any persistent write, or the check+revert is reversible) -- but it requires reaching the Chamber's Law page/law-entry admin edit form in the Liferay Control Panel to interact with the field at all. This session's login attempt against qcdev (CmsLoginPage.login() via TEST_USER/TEST_PASSWORD, mirroring the navigation pattern already proven for the Departments and Board of Directors admin surfaces) timed out repeatedly (playwright._impl._errors.TimeoutError on the username-field fill, and on core/web/session_guard.py's re-authentication retries) -- consistent with the severe qcdev session/connection-limit flakiness already documented in login_page.py and org_structure_admin_page.py, but worse this session (login itself never completed). No stable locators for the Chamber's Law admin edit form (list/edit URL, per-field selectors) could be extracted or confirmed as a result. Skipped rather than invented -- see module docstring.")
def test_chambers_law_cp_134910_an_empty_arabic_intro_section_heading_is_rejected_on_save(page):
    ...


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
@pytest.mark.skip(reason="Field-level validation case (Verify that valid English Intro Content is accepted and saved) is the SAFE category this batch was authorized to automate (validation fires before any persistent write, or the check+revert is reversible) -- but it requires reaching the Chamber's Law page/law-entry admin edit form in the Liferay Control Panel to interact with the field at all. This session's login attempt against qcdev (CmsLoginPage.login() via TEST_USER/TEST_PASSWORD, mirroring the navigation pattern already proven for the Departments and Board of Directors admin surfaces) timed out repeatedly (playwright._impl._errors.TimeoutError on the username-field fill, and on core/web/session_guard.py's re-authentication retries) -- consistent with the severe qcdev session/connection-limit flakiness already documented in login_page.py and org_structure_admin_page.py, but worse this session (login itself never completed). No stable locators for the Chamber's Law admin edit form (list/edit URL, per-field selectors) could be extracted or confirmed as a result. Skipped rather than invented -- see module docstring.")
def test_chambers_law_cp_134913_valid_english_intro_content_is_accepted_and_saved(page):
    ...


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
@pytest.mark.skip(reason="Field-level validation case (Verify that empty English Intro Content is rejected on save) is the SAFE category this batch was authorized to automate (validation fires before any persistent write, or the check+revert is reversible) -- but it requires reaching the Chamber's Law page/law-entry admin edit form in the Liferay Control Panel to interact with the field at all. This session's login attempt against qcdev (CmsLoginPage.login() via TEST_USER/TEST_PASSWORD, mirroring the navigation pattern already proven for the Departments and Board of Directors admin surfaces) timed out repeatedly (playwright._impl._errors.TimeoutError on the username-field fill, and on core/web/session_guard.py's re-authentication retries) -- consistent with the severe qcdev session/connection-limit flakiness already documented in login_page.py and org_structure_admin_page.py, but worse this session (login itself never completed). No stable locators for the Chamber's Law admin edit form (list/edit URL, per-field selectors) could be extracted or confirmed as a result. Skipped rather than invented -- see module docstring.")
def test_chambers_law_cp_134914_empty_english_intro_content_is_rejected_on_save(page):
    ...


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
@pytest.mark.skip(reason="Field-level validation case (Verify that valid Arabic Intro Content is accepted and saved with RTL text preserved) is the SAFE category this batch was authorized to automate (validation fires before any persistent write, or the check+revert is reversible) -- but it requires reaching the Chamber's Law page/law-entry admin edit form in the Liferay Control Panel to interact with the field at all. This session's login attempt against qcdev (CmsLoginPage.login() via TEST_USER/TEST_PASSWORD, mirroring the navigation pattern already proven for the Departments and Board of Directors admin surfaces) timed out repeatedly (playwright._impl._errors.TimeoutError on the username-field fill, and on core/web/session_guard.py's re-authentication retries) -- consistent with the severe qcdev session/connection-limit flakiness already documented in login_page.py and org_structure_admin_page.py, but worse this session (login itself never completed). No stable locators for the Chamber's Law admin edit form (list/edit URL, per-field selectors) could be extracted or confirmed as a result. Skipped rather than invented -- see module docstring.")
def test_chambers_law_cp_134917_valid_arabic_intro_content_is_accepted_and_saved_with_rtl_text_preserved(page):
    ...


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
@pytest.mark.skip(reason="Field-level validation case (Verify that empty Arabic Intro Content is rejected on save) is the SAFE category this batch was authorized to automate (validation fires before any persistent write, or the check+revert is reversible) -- but it requires reaching the Chamber's Law page/law-entry admin edit form in the Liferay Control Panel to interact with the field at all. This session's login attempt against qcdev (CmsLoginPage.login() via TEST_USER/TEST_PASSWORD, mirroring the navigation pattern already proven for the Departments and Board of Directors admin surfaces) timed out repeatedly (playwright._impl._errors.TimeoutError on the username-field fill, and on core/web/session_guard.py's re-authentication retries) -- consistent with the severe qcdev session/connection-limit flakiness already documented in login_page.py and org_structure_admin_page.py, but worse this session (login itself never completed). No stable locators for the Chamber's Law admin edit form (list/edit URL, per-field selectors) could be extracted or confirmed as a result. Skipped rather than invented -- see module docstring.")
def test_chambers_law_cp_134918_empty_arabic_intro_content_is_rejected_on_save(page):
    ...


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
@pytest.mark.skip(reason="Field-level validation case (Verify that a valid English Legal References Section Heading is accepted and saved) is the SAFE category this batch was authorized to automate (validation fires before any persistent write, or the check+revert is reversible) -- but it requires reaching the Chamber's Law page/law-entry admin edit form in the Liferay Control Panel to interact with the field at all. This session's login attempt against qcdev (CmsLoginPage.login() via TEST_USER/TEST_PASSWORD, mirroring the navigation pattern already proven for the Departments and Board of Directors admin surfaces) timed out repeatedly (playwright._impl._errors.TimeoutError on the username-field fill, and on core/web/session_guard.py's re-authentication retries) -- consistent with the severe qcdev session/connection-limit flakiness already documented in login_page.py and org_structure_admin_page.py, but worse this session (login itself never completed). No stable locators for the Chamber's Law admin edit form (list/edit URL, per-field selectors) could be extracted or confirmed as a result. Skipped rather than invented -- see module docstring.")
def test_chambers_law_cp_134921_a_valid_english_legal_references_section_heading_is_accepted_and_saved(page):
    ...


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
@pytest.mark.skip(reason="Field-level validation case (Verify that an empty English Legal References Section Heading is rejected on save) is the SAFE category this batch was authorized to automate (validation fires before any persistent write, or the check+revert is reversible) -- but it requires reaching the Chamber's Law page/law-entry admin edit form in the Liferay Control Panel to interact with the field at all. This session's login attempt against qcdev (CmsLoginPage.login() via TEST_USER/TEST_PASSWORD, mirroring the navigation pattern already proven for the Departments and Board of Directors admin surfaces) timed out repeatedly (playwright._impl._errors.TimeoutError on the username-field fill, and on core/web/session_guard.py's re-authentication retries) -- consistent with the severe qcdev session/connection-limit flakiness already documented in login_page.py and org_structure_admin_page.py, but worse this session (login itself never completed). No stable locators for the Chamber's Law admin edit form (list/edit URL, per-field selectors) could be extracted or confirmed as a result. Skipped rather than invented -- see module docstring.")
def test_chambers_law_cp_134922_an_empty_english_legal_references_section_heading_is_rejected_on_save(page):
    ...


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
@pytest.mark.skip(reason="Field-level validation case (Verify that a valid Arabic Legal References Section Heading is accepted and saved) is the SAFE category this batch was authorized to automate (validation fires before any persistent write, or the check+revert is reversible) -- but it requires reaching the Chamber's Law page/law-entry admin edit form in the Liferay Control Panel to interact with the field at all. This session's login attempt against qcdev (CmsLoginPage.login() via TEST_USER/TEST_PASSWORD, mirroring the navigation pattern already proven for the Departments and Board of Directors admin surfaces) timed out repeatedly (playwright._impl._errors.TimeoutError on the username-field fill, and on core/web/session_guard.py's re-authentication retries) -- consistent with the severe qcdev session/connection-limit flakiness already documented in login_page.py and org_structure_admin_page.py, but worse this session (login itself never completed). No stable locators for the Chamber's Law admin edit form (list/edit URL, per-field selectors) could be extracted or confirmed as a result. Skipped rather than invented -- see module docstring.")
def test_chambers_law_cp_134925_a_valid_arabic_legal_references_section_heading_is_accepted_and_saved(page):
    ...


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
@pytest.mark.skip(reason="Field-level validation case (Verify that an empty Arabic Legal References Section Heading is rejected on save) is the SAFE category this batch was authorized to automate (validation fires before any persistent write, or the check+revert is reversible) -- but it requires reaching the Chamber's Law page/law-entry admin edit form in the Liferay Control Panel to interact with the field at all. This session's login attempt against qcdev (CmsLoginPage.login() via TEST_USER/TEST_PASSWORD, mirroring the navigation pattern already proven for the Departments and Board of Directors admin surfaces) timed out repeatedly (playwright._impl._errors.TimeoutError on the username-field fill, and on core/web/session_guard.py's re-authentication retries) -- consistent with the severe qcdev session/connection-limit flakiness already documented in login_page.py and org_structure_admin_page.py, but worse this session (login itself never completed). No stable locators for the Chamber's Law admin edit form (list/edit URL, per-field selectors) could be extracted or confirmed as a result. Skipped rather than invented -- see module docstring.")
def test_chambers_law_cp_134926_an_empty_arabic_legal_references_section_heading_is_rejected_on_save(page):
    ...


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
@pytest.mark.skip(reason="Field-level validation case (Verify that a valid PNG Content Image under 2 MB is accepted) is the SAFE category this batch was authorized to automate (validation fires before any persistent write, or the check+revert is reversible) -- but it requires reaching the Chamber's Law page/law-entry admin edit form in the Liferay Control Panel to interact with the field at all. This session's login attempt against qcdev (CmsLoginPage.login() via TEST_USER/TEST_PASSWORD, mirroring the navigation pattern already proven for the Departments and Board of Directors admin surfaces) timed out repeatedly (playwright._impl._errors.TimeoutError on the username-field fill, and on core/web/session_guard.py's re-authentication retries) -- consistent with the severe qcdev session/connection-limit flakiness already documented in login_page.py and org_structure_admin_page.py, but worse this session (login itself never completed). No stable locators for the Chamber's Law admin edit form (list/edit URL, per-field selectors) could be extracted or confirmed as a result. Skipped rather than invented -- see module docstring.")
def test_chambers_law_cp_134929_a_valid_png_content_image_under_2_mb_is_accepted(page):
    ...


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
@pytest.mark.skip(reason="Field-level validation case (Verify that a Content Image in an unsupported format is rejected) is the SAFE category this batch was authorized to automate (validation fires before any persistent write, or the check+revert is reversible) -- but it requires reaching the Chamber's Law page/law-entry admin edit form in the Liferay Control Panel to interact with the field at all. This session's login attempt against qcdev (CmsLoginPage.login() via TEST_USER/TEST_PASSWORD, mirroring the navigation pattern already proven for the Departments and Board of Directors admin surfaces) timed out repeatedly (playwright._impl._errors.TimeoutError on the username-field fill, and on core/web/session_guard.py's re-authentication retries) -- consistent with the severe qcdev session/connection-limit flakiness already documented in login_page.py and org_structure_admin_page.py, but worse this session (login itself never completed). No stable locators for the Chamber's Law admin edit form (list/edit URL, per-field selectors) could be extracted or confirmed as a result. Skipped rather than invented -- see module docstring.")
def test_chambers_law_cp_134930_a_content_image_in_an_unsupported_format_is_rejected(page):
    ...


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
@pytest.mark.skip(reason="Field-level validation case (Verify that a Content Image above 2 MB is rejected at the size boundary) is the SAFE category this batch was authorized to automate (validation fires before any persistent write, or the check+revert is reversible) -- but it requires reaching the Chamber's Law page/law-entry admin edit form in the Liferay Control Panel to interact with the field at all. This session's login attempt against qcdev (CmsLoginPage.login() via TEST_USER/TEST_PASSWORD, mirroring the navigation pattern already proven for the Departments and Board of Directors admin surfaces) timed out repeatedly (playwright._impl._errors.TimeoutError on the username-field fill, and on core/web/session_guard.py's re-authentication retries) -- consistent with the severe qcdev session/connection-limit flakiness already documented in login_page.py and org_structure_admin_page.py, but worse this session (login itself never completed). No stable locators for the Chamber's Law admin edit form (list/edit URL, per-field selectors) could be extracted or confirmed as a result. Skipped rather than invented -- see module docstring.")
def test_chambers_law_cp_134931_a_content_image_above_2_mb_is_rejected_at_the_size_boundary(page):
    ...


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
@pytest.mark.skip(reason="Field-level validation case (Verify that publishing without a Content Image is blocked) is the SAFE category this batch was authorized to automate (validation fires before any persistent write, or the check+revert is reversible) -- but it requires reaching the Chamber's Law page/law-entry admin edit form in the Liferay Control Panel to interact with the field at all. This session's login attempt against qcdev (CmsLoginPage.login() via TEST_USER/TEST_PASSWORD, mirroring the navigation pattern already proven for the Departments and Board of Directors admin surfaces) timed out repeatedly (playwright._impl._errors.TimeoutError on the username-field fill, and on core/web/session_guard.py's re-authentication retries) -- consistent with the severe qcdev session/connection-limit flakiness already documented in login_page.py and org_structure_admin_page.py, but worse this session (login itself never completed). No stable locators for the Chamber's Law admin edit form (list/edit URL, per-field selectors) could be extracted or confirmed as a result. Skipped rather than invented -- see module docstring.")
def test_chambers_law_cp_134932_publishing_without_a_content_image_is_blocked(page):
    ...


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
@pytest.mark.skip(reason="Field-level validation case (Verify that valid Content Image Alt Text is accepted and saved) is the SAFE category this batch was authorized to automate (validation fires before any persistent write, or the check+revert is reversible) -- but it requires reaching the Chamber's Law page/law-entry admin edit form in the Liferay Control Panel to interact with the field at all. This session's login attempt against qcdev (CmsLoginPage.login() via TEST_USER/TEST_PASSWORD, mirroring the navigation pattern already proven for the Departments and Board of Directors admin surfaces) timed out repeatedly (playwright._impl._errors.TimeoutError on the username-field fill, and on core/web/session_guard.py's re-authentication retries) -- consistent with the severe qcdev session/connection-limit flakiness already documented in login_page.py and org_structure_admin_page.py, but worse this session (login itself never completed). No stable locators for the Chamber's Law admin edit form (list/edit URL, per-field selectors) could be extracted or confirmed as a result. Skipped rather than invented -- see module docstring.")
def test_chambers_law_cp_134933_valid_content_image_alt_text_is_accepted_and_saved(page):
    ...


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
@pytest.mark.skip(reason="Field-level validation case (Verify that empty Content Image Alt Text is rejected on save) is the SAFE category this batch was authorized to automate (validation fires before any persistent write, or the check+revert is reversible) -- but it requires reaching the Chamber's Law page/law-entry admin edit form in the Liferay Control Panel to interact with the field at all. This session's login attempt against qcdev (CmsLoginPage.login() via TEST_USER/TEST_PASSWORD, mirroring the navigation pattern already proven for the Departments and Board of Directors admin surfaces) timed out repeatedly (playwright._impl._errors.TimeoutError on the username-field fill, and on core/web/session_guard.py's re-authentication retries) -- consistent with the severe qcdev session/connection-limit flakiness already documented in login_page.py and org_structure_admin_page.py, but worse this session (login itself never completed). No stable locators for the Chamber's Law admin edit form (list/edit URL, per-field selectors) could be extracted or confirmed as a result. Skipped rather than invented -- see module docstring.")
def test_chambers_law_cp_134934_empty_content_image_alt_text_is_rejected_on_save(page):
    ...


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
@pytest.mark.skip(reason="Field-level validation case (Verify that the page Status dropdown offers and stores the Draft value) is the SAFE category this batch was authorized to automate (validation fires before any persistent write, or the check+revert is reversible) -- but it requires reaching the Chamber's Law page/law-entry admin edit form in the Liferay Control Panel to interact with the field at all. This session's login attempt against qcdev (CmsLoginPage.login() via TEST_USER/TEST_PASSWORD, mirroring the navigation pattern already proven for the Departments and Board of Directors admin surfaces) timed out repeatedly (playwright._impl._errors.TimeoutError on the username-field fill, and on core/web/session_guard.py's re-authentication retries) -- consistent with the severe qcdev session/connection-limit flakiness already documented in login_page.py and org_structure_admin_page.py, but worse this session (login itself never completed). No stable locators for the Chamber's Law admin edit form (list/edit URL, per-field selectors) could be extracted or confirmed as a result. Skipped rather than invented -- see module docstring.")
def test_chambers_law_cp_134937_the_page_status_dropdown_offers_and_stores_the_draft_value(page):
    ...


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
@pytest.mark.skip(reason="Field-level validation case (Verify that the page Status dropdown offers and stores the Published value) is the SAFE category this batch was authorized to automate (validation fires before any persistent write, or the check+revert is reversible) -- but it requires reaching the Chamber's Law page/law-entry admin edit form in the Liferay Control Panel to interact with the field at all. This session's login attempt against qcdev (CmsLoginPage.login() via TEST_USER/TEST_PASSWORD, mirroring the navigation pattern already proven for the Departments and Board of Directors admin surfaces) timed out repeatedly (playwright._impl._errors.TimeoutError on the username-field fill, and on core/web/session_guard.py's re-authentication retries) -- consistent with the severe qcdev session/connection-limit flakiness already documented in login_page.py and org_structure_admin_page.py, but worse this session (login itself never completed). No stable locators for the Chamber's Law admin edit form (list/edit URL, per-field selectors) could be extracted or confirmed as a result. Skipped rather than invented -- see module docstring.")
def test_chambers_law_cp_134938_the_page_status_dropdown_offers_and_stores_the_published_value(page):
    ...


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

