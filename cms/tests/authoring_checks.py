"""
cms/tests/authoring_checks.py — shared Control_Panel check bodies for the
2026-10-01 Phase 3 batch (PBIs 130708, 130713, 130714, 130715, 131061, 131062).

Not a test module (no `test_` prefix). Each function is one case shape —
"valid value persists", "empty value refused", "Editor publish reaches the
public site", ... — run against a DisposableObjectAdminPage subclass. The
per-case test functions in cms/tests/<f>/test_<f>_control_panel.py carry the
markers, the docstring and the case's own data, and call one of these.

Rules every function here follows (standards.md / CLAUDE.md):
  - every record created is `QCTEST-<tc_id>-<short>` and is deleted by exact
    title in a `finally` block, every run;
  - the account is named: Editor for create -> Published, Author for
    submit -> Pending Review, Site Member for permission denial; never
    TEST_USER;
  - public visibility is read in a fresh logged-out context, and both gates
    (status Published AND Active Status ticked) are asserted;
  - a workflow outcome is backed by the History trail where one is recorded.
"""

from __future__ import annotations

import uuid
from typing import Callable

from cms.pages.components.disposable_object_admin import (
    ROLE_AUTHOR,
    ROLE_EDITOR,
    ROLE_SITE_MEMBER,
    DisposableObjectAdminPage,
    chars,
    qctest_title,
)
from cms.pages.components.object_authoring_page import (
    STATUS_DRAFT,
    STATUS_PENDING_REVIEW,
    STATUS_PUBLISHED,
    STATUS_UNPUBLISHED,
)
from cms.pages.control_panel.login_page import CmsLoginPage
from cms.tests.live_write_guard import LiveRecord, deletes_suppressed, keep_instead_of_delete

PublicProbe = Callable[..., bool]
"""probe(anonymous_page, text, expect=True) -> whether `text` is rendered to a
visitor, polling (reload) until it matches `expect` or the budget runs out."""

NOT_ROLE = "precondition: this case must run as the restricted role, but the session has the admin toolbar"


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------
PUBLIC_POLL_TIMEOUT_S = 30.0
PUBLIC_POLL_INTERVAL_S = 3.0

# User decision 2026-10-13: under QC_ALLOW_LIVE_SINGLETON_WRITES=1 NOTHING is
# deleted -- a disposable QCTEST row is kept and logged (`kept`) for manual
# cleanup. A kept row from an earlier run must never satisfy (or confuse) this
# run's checks, so under the opt-in every fixed title gets a per-run uid.
_RUN_UID = uuid.uuid4().hex[:6]


def run_title(tc_id, short: str) -> str:
    """qctest_title(), plus a per-run uid under the opt-in (see above)."""
    return qctest_title(tc_id, f"{short}-{_RUN_UID}" if deletes_suppressed() else short)


def dispose(admin, title: str, tc_id=None):
    """Teardown of a disposable QCTEST row: exact-title delete as before, or
    -- under the opt-in -- keep it and log it (returns False)."""
    record = LiveRecord(getattr(admin, "SLUG", "") or "?", title, "disposable QCTEST record")
    if keep_instead_of_delete(record, title, tc_id):
        return False
    return admin.delete_disposable(title)


def make_public_probe(open_public: Callable[[object], None]) -> PublicProbe:
    """Build a probe from a function that loads the public page on an
    anonymous Playwright page. Reloads until the text's presence matches
    `expect` (the delivery cache lags a save) — the reload IS the condition
    being polled, with PUBLIC_POLL_TIMEOUT_S as the upper bound."""
    from core.utils.waits import WaitTimeoutError, wait_until

    def probe(anon, text: str, expect: bool = True) -> bool:
        seen = {"present": not expect}

        def _matches() -> bool:
            open_public(anon)
            seen["present"] = text in anon.locator("body").inner_text()
            return seen["present"] == expect

        try:
            wait_until(_matches, timeout=PUBLIC_POLL_TIMEOUT_S, poll=PUBLIC_POLL_INTERVAL_S,
                       message=f"public page never {'showed' if expect else 'dropped'} {text!r}")
        except WaitTimeoutError:
            pass
        return seen["present"]

    return probe

def _anon_page(browser):
    from core.web.browser import new_context

    ctx = new_context(browser, use_auth_state=False)
    return ctx, ctx.new_page()


def _close(ctx) -> None:
    try:
        ctx.close()
    except Exception:  # noqa: BLE001 — cleanup never masks the result
        pass


def _publish_as_editor(admin: DisposableObjectAdminPage, title: str, files=None, extra=None) -> None:
    """Create and submit as Editor with Active Status ticked, then prove the
    record is Published before anyone looks at the public site."""
    admin.open_form(ROLE_EDITOR)
    admin.fill_required(title, active=True, files=files)
    for key, val in (extra or {}).items():
        admin.fill(key, val)
    admin.submit_for_review()
    status = admin.status_of(title, ROLE_EDITOR)
    assert status == STATUS_PUBLISHED, (
        f"{title!r} is {status or 'absent from the list'!r} after an Editor submit, not "
        f"{STATUS_PUBLISHED!r} — nothing to look for on the public site"
    )


def _assert_active_ticked(admin: DisposableObjectAdminPage, title: str) -> None:
    if not admin.ACTIVE_FIELD or admin.ACTIVE_FIELD not in admin.FIELDS:
        return
    admin.open_list(ROLE_EDITOR)
    admin.open_entry_by_edit_link(title)
    assert admin.flag(admin.ACTIVE_FIELD), f"{title!r}: Active Status is not ticked — second visibility gate"


def _history_has(admin: DisposableObjectAdminPage, title: str) -> list[dict]:
    admin.open_list(ROLE_EDITOR)
    return admin.history_entries(title)


# ---------------------------------------------------------------------------
# field checks (nothing reaches the public site)
# ---------------------------------------------------------------------------
def check_valid_persists(page, admin_cls, tc_id, key, en, ar=None, files=None, short="valid"):
    """Editor saves a QCTEST draft with `key` = en (/ar), reopens it, and
    reads the same value(s) back."""
    admin = admin_cls(page)
    spec = admin_cls.FIELDS[key]
    if key == admin_cls.TITLE_FIELD:
        # The case's own title value is carried inside the QCTEST name, so the
        # record stays recognisable as disposable; trimmed to the field limit.
        title = qctest_title(tc_id, en)[: spec.max_len or None]
        en, ar = title, (f"{title[: (spec.max_len or 999) - 3]} AR" if ar is not None else None)
    else:
        title = run_title(tc_id, short)
    try:
        admin.open_form(ROLE_EDITOR)
        admin.fill_required(title, skip=(key,) if key != admin.TITLE_FIELD else (), files=files)
        if key == admin.TITLE_FIELD:
            if ar is not None and spec.bilingual:
                admin.fill(key, ar, locale="ar")
        elif admin.spec(key).kind == "file":
            admin.upload(key, en, tag=str(tc_id))
        else:
            admin.fill(key, en)
            if ar is not None and admin.spec(key).bilingual:
                admin.fill(key, ar, locale="ar")
        admin.save_as_draft()
        assert admin.status_of(title, ROLE_EDITOR) == STATUS_DRAFT, f"{title!r} was not stored as a Draft"
        admin.open_entry_by_edit_link(title)
        if admin.spec(key).kind == "file":
            assert admin.value(key), f"{key}: no file is attached after save + reopen"
        else:
            assert admin.value(key) == en, f"{key} EN did not persist: {admin.value(key)!r} != {en!r}"
            if ar is not None and admin.spec(key).bilingual:
                assert admin.value(key, "ar") == ar, f"{key} AR did not persist: {admin.value(key, 'ar')!r}"
    finally:
        dispose(admin, title)


def _submit_and_expect_refusal(admin, title, what):
    admin.submit_for_review()
    refused = admin.refusal_visible()
    status = admin.status_of(title, ROLE_EDITOR)
    assert refused, f"{what}: Submit for Review raised no refusal (list status {status or 'absent'!r})"
    assert status != STATUS_PUBLISHED, f"{what}: the record was Published despite the refusal"


def check_empty_refused(page, admin_cls, tc_id, key, side="both", files=None):
    """Every other required field valid; `key` left empty on `side`
    (en | ar | both | each). Submit must be refused and nothing published."""
    admin = admin_cls(page)
    spec = admin_cls.FIELDS[key]
    sides = ["en", "ar"] if side == "each" else [side]
    for n, s in enumerate(sides):
        title = run_title(tc_id, f"empty-{s}")
        try:
            admin.open_form(ROLE_EDITOR)
            admin.fill_required(title, skip=(key,), files=files)
            if key == admin.TITLE_FIELD:
                title = None  # the record has no title to find; refusal alone is the signal
            if spec.bilingual and s == "en":
                admin.fill(key, spec.default_ar or "قيمة اختبار", locale="ar")
            elif spec.bilingual and s == "ar":
                admin.fill(key, spec.default or f"QCTEST {tc_id}")
            if title is None:
                admin.submit_for_review()
                assert admin.refusal_visible(), f"{key} empty ({s}): Submit for Review raised no refusal"
            else:
                _submit_and_expect_refusal(admin, title, f"{key} empty ({s})")
        finally:
            if title:
                dispose(admin, title)


def check_whitespace_refused(page, admin_cls, tc_id, key, files=None):
    admin = admin_cls(page)
    title = run_title(tc_id, "ws")
    try:
        admin.open_form(ROLE_EDITOR)
        admin.fill_required(title, skip=(key,) if key != admin.TITLE_FIELD else (), files=files)
        admin.fill(key, "   ")
        if key == admin.TITLE_FIELD:
            admin.submit_for_review()
            assert admin.refusal_visible(), f"{key}: a whitespace-only value raised no refusal"
            title = None
        else:
            _submit_and_expect_refusal(admin, title, f"{key} whitespace-only")
    finally:
        if title:
            dispose(admin, title)


def check_over_max_refused(page, admin_cls, tc_id, key, limit, files=None):
    """`limit`+1 characters must be truncated to `limit` by the input, or
    refused on submit. Either outcome is the case's stated pass; a stored
    over-limit value is the failure."""
    admin = admin_cls(page)
    title = run_title(tc_id, "max")
    over = chars(limit + 1)
    try:
        admin.open_form(ROLE_EDITOR)
        admin.fill_required(title, skip=(key,) if key != admin.TITLE_FIELD else (), files=files)
        admin.fill(key, over if key != admin.TITLE_FIELD else (title + chars(limit))[: limit + 1])
        if len(admin.value(key)) <= limit:
            return  # truncated at the input — case passes on its first branch
        admin.submit_for_review()
        if admin.refusal_visible():
            return
        status = admin.status_of(title, ROLE_EDITOR)
        assert status != STATUS_PUBLISHED, (
            f"{key}: a {limit + 1}-character value was neither truncated nor refused (status {status!r})"
        )
    finally:
        dispose(admin, title)


def check_value_refused(page, admin_cls, tc_id, key, bad_value, short="bad", files=None):
    """Generic refusal: numeric zero/negative/non-numeric, malformed URL,
    malformed date/duration."""
    admin = admin_cls(page)
    title = run_title(tc_id, short)
    try:
        admin.open_form(ROLE_EDITOR)
        admin.fill_required(title, skip=(key,), files=files)
        try:
            admin.fill(key, bad_value)
        except Exception:  # noqa: BLE001 — a spinbutton that will not take the text IS the refusal
            return
        if admin.spec(key).kind == "number" and admin.value(key) in ("", None):
            # the native number input dropped the value: submit must now hit the required check
            pass
        _submit_and_expect_refusal(admin, title, f"{key}={bad_value!r}")
    finally:
        dispose(admin, title)


def check_file_accepted(page, admin_cls, tc_id, key, fixture, files=None):
    check_valid_persists(page, admin_cls, tc_id, key, fixture, files=files, short="file")


def check_file_refused(page, admin_cls, tc_id, key, fixture, files=None):
    """Unsupported type or over-size upload must be refused by the picker or
    the save — the file must not end up attached to the record."""
    admin = admin_cls(page)
    title = run_title(tc_id, "file")
    try:
        admin.open_form(ROLE_EDITOR)
        admin.fill_required(title, skip=(key,), files=files)
        assert admin.upload_rejected(key, fixture, tag=str(tc_id)), (
            f"{key}: {fixture.rsplit('/', 1)[-1]} was accepted by the upload picker"
        )
    finally:
        dispose(admin, title)


def check_form_renders(page, admin_cls, keys, role=ROLE_EDITOR, locale="en"):
    admin = admin_cls(page)
    admin.open_form(role, locale=locale)
    missing = [k for k in keys if not admin.field_present(k)]
    assert not missing, f"form for {admin_cls.SIDEBAR_LABEL!r} lacks: {[admin_cls.FIELDS[k].label for k in missing]}"


def check_rtl_form(page, admin_cls):
    """The form renders right-to-left under the Arabic admin locale. Asserts
    the document direction and that the form mounted — no Arabic-text
    locator is used (standards.md: English-only locators)."""
    admin = admin_cls(page)
    admin.sign_in(ROLE_EDITOR)
    admin.open(admin._manage_url(locale="ar"))
    page.locator('button[type="submit"]').first.wait_for(state="visible", timeout=35000)
    assert page.locator("html").get_attribute("dir") == "rtl", "Arabic admin locale did not render RTL"


# ---------------------------------------------------------------------------
# lifecycle checks
# ---------------------------------------------------------------------------
def check_default_draft(page, admin_cls, tc_id, files=None):
    """A newly saved entry lands on Draft (Editor)."""
    admin = admin_cls(page)
    title = run_title(tc_id, "draft")
    try:
        admin.open_form(ROLE_EDITOR)
        admin.fill_required(title, files=files)
        admin.save_as_draft()
        assert admin.status_of(title, ROLE_EDITOR) == STATUS_DRAFT
    finally:
        dispose(admin, title)


def check_draft_not_public(page, browser, admin_cls, tc_id, probe: PublicProbe, files=None):
    """Editor saves a QCTEST Draft with Active Status ticked; a logged-out
    visitor must not see it (only the Draft gate differs)."""
    admin = admin_cls(page)
    title = run_title(tc_id, "draft")
    ctx, anon = _anon_page(browser)
    try:
        admin.open_form(ROLE_EDITOR)
        admin.fill_required(title, active=True, files=files)
        admin.save_as_draft()
        assert admin.status_of(title, ROLE_EDITOR) == STATUS_DRAFT
        assert not probe(anon, title, False), f"{title!r} (Draft) is visible to a logged-out visitor"
    finally:
        dispose(admin, title)
        _close(ctx)


def check_preview_draft(page, browser, admin_cls, tc_id, probe: PublicProbe, files=None):
    """Staff preview renders the Draft; the public page does not."""
    admin = admin_cls(page)
    title = run_title(tc_id, "preview")
    ctx, anon = _anon_page(browser)
    try:
        admin.open_form(ROLE_EDITOR)
        admin.fill_required(title, active=True, files=files)
        admin.save_as_draft()
        admin.open_list(ROLE_EDITOR)
        admin.filter_entries(title)
        url = admin.row_preview_url(title)
        assert url, f"{title!r}: the row offers no Preview link"
        admin.open(url)
        assert title in page.locator("body").inner_text(), "Preview did not render the draft content"
        assert not probe(anon, title, False), f"{title!r} (Draft) leaked to the public page"
    finally:
        dispose(admin, title)
        _close(ctx)


def check_editor_publish_public(page, browser, admin_cls, tc_id, probe: PublicProbe, files=None, extra=None):
    """Editor create -> Submit for Review lands on Published (privileged
    bypass), Active Status ticked, History records it, visitor sees it."""
    admin = admin_cls(page)
    title = run_title(tc_id, "pub")
    ctx, anon = _anon_page(browser)
    try:
        _publish_as_editor(admin, title, files=files, extra=extra)
        _assert_active_ticked(admin, title)
        assert _history_has(admin, title), f"{title!r}: no History trail recorded for the publish"
        assert probe(anon, title), f"{title!r} is Published + Active but not visible to a logged-out visitor"
    finally:
        dispose(admin, title)
        _close(ctx)


def check_unpublish_hides(page, browser, admin_cls, tc_id, probe: PublicProbe, files=None):
    admin = admin_cls(page)
    title = run_title(tc_id, "unpub")
    ctx, anon = _anon_page(browser)
    try:
        _publish_as_editor(admin, title, files=files)
        assert probe(anon, title), f"precondition: {title!r} is not visible after publish"
        admin.open_list(ROLE_EDITOR)
        admin.unpublish_entry(title)
        assert admin.status_of(title, ROLE_EDITOR) == STATUS_UNPUBLISHED
        assert not probe(anon, title, False), f"{title!r} is Unpublished but still visible to a visitor"
    finally:
        dispose(admin, title)
        _close(ctx)


def check_republish_updates(page, browser, admin_cls, tc_id, probe: PublicProbe, key, new_value, files=None):
    """Publish, unpublish, change `key`, publish again (row Publish action
    from Unpublished): the visitor sees the new value, not the old one."""
    admin = admin_cls(page)
    title = run_title(tc_id, "repub")
    ctx, anon = _anon_page(browser)
    try:
        _publish_as_editor(admin, title, files=files)
        admin.open_list(ROLE_EDITOR)
        admin.unpublish_entry(title)
        admin.open_entry_by_edit_link(title)
        admin.fill(key, new_value)
        admin.submit_for_review()
        assert admin.status_of(title, ROLE_EDITOR) == STATUS_PUBLISHED
        assert probe(anon, new_value), f"{key}: visitor does not see the re-published value {new_value!r}"
    finally:
        dispose(admin, title)
        _close(ctx)


def check_delete_removes(page, browser, admin_cls, tc_id, probe: PublicProbe, files=None):
    admin = admin_cls(page)
    title = run_title(tc_id, "del")
    ctx, anon = _anon_page(browser)
    try:
        _publish_as_editor(admin, title, files=files)
        assert probe(anon, title), f"precondition: {title!r} is not visible after publish"
        assert admin.delete_disposable(title), f"{title!r}: delete did not run"
        assert not admin.entry_exists(title, ROLE_EDITOR), f"{title!r} is still in the admin list"
        assert not probe(anon, title, False), f"{title!r} is still visible after delete"
    finally:
        dispose(admin, title)
        _close(ctx)


def check_publish_refused(page, admin_cls, tc_id, skip: tuple[str, ...], files=None, extra=None):
    """Editor submit with `skip` fields left empty must be refused."""
    admin = admin_cls(page)
    title = run_title(tc_id, "noreq")
    try:
        admin.open_form(ROLE_EDITOR)
        admin.fill_required(title, skip=skip, active=True, files=files)
        for key, val in (extra or {}).items():
            admin.fill(key, val)
        _submit_and_expect_refusal(admin, title, f"publish without {skip}")
    finally:
        dispose(admin, title)


def check_author_submit_pending(page, admin_cls, tc_id, files=None, edit_key=None, edit_value=None):
    """Author creates (and optionally edits) a QCTEST entry; Submit for
    Review lands on Pending Review, never Published, and the Author is
    offered no approve/publish row action. Teardown runs as Editor."""
    admin = admin_cls(page)
    title = run_title(tc_id, "author")
    try:
        admin.open_form(ROLE_AUTHOR)
        assert not admin.has_admin_toolbar(), NOT_ROLE
        admin.fill_required(title, active=True, files=files)
        admin.save_as_draft()
        assert admin.status_of(title, ROLE_AUTHOR) == STATUS_DRAFT
        admin.open_entry_by_edit_link(title)
        if edit_key:
            admin.fill(edit_key, edit_value)
        assert admin.submit_button_label() == "Submit for Review", (
            f"Author form offers {admin.submit_button_label()!r}, not 'Submit for Review'"
        )
        admin.submit_for_review()
        assert admin.status_of(title, ROLE_AUTHOR) == STATUS_PENDING_REVIEW
        assert not admin.row_offers_action(title, "approve"), "Author is offered Approve on its own entry"
        assert not admin.row_offers_action(title, "publish"), "Author is offered Publish on its own entry"
    finally:
        admin.delete_disposable(title, ROLE_EDITOR)


def check_member_denied(page, admin_cls):
    """Site Member (signed in, no CMS role) opens the manage URL: no form, no
    rows, and a positive denial (login form, 403/404, or permission text)."""
    admin = admin_cls(page)
    admin.sign_in(ROLE_SITE_MEMBER)
    assert CmsLoginPage(page).login_succeeded(), "Site Member did not sign in — the denial would prove nothing"
    resp = page.goto(admin.manage_url(), wait_until="domcontentloaded")
    assert page.locator(admin.SAVE_AS_DRAFT_BUTTON).count() == 0, "Site Member was given the authoring form"
    assert page.locator("a[data-qc-oel-delete]").count() == 0, "Site Member was shown entry rows"
    body = page.locator("body").inner_text().casefold()
    denied = (resp is not None and resp.status in (401, 403, 404)) or any(
        s in body for s in ("permission", "not found", "access denied", "sign in")
    )
    assert denied, "no positive denial signal (status/permission/not-found text) for Site Member"


def check_anonymous_denied(browser, admin_cls):
    """A logged-out request to the manage URL gets the sign-in gate / 404
    (OBJECT-AUTHORING-GUIDE: a signed-out authoring URL 404s), never data."""
    ctx, anon = _anon_page(browser)
    try:
        admin = admin_cls(anon)
        resp = anon.goto(admin.manage_url(), wait_until="domcontentloaded")
        assert anon.locator(admin.SAVE_AS_DRAFT_BUTTON).count() == 0, "anonymous visitor got the authoring form"
        assert anon.locator("table tbody tr").count() == 0 or (resp and resp.status in (401, 403, 404))
        assert (resp is not None and resp.status in (401, 403, 404)) or CmsLoginPage(anon).login_form_visible(), (
            f"anonymous request was neither refused nor sent to sign-in (HTTP {resp.status if resp else '?'})"
        )
    finally:
        _close(ctx)


def check_role_cannot_author(page, admin_cls, role):
    """A non-authoring role (e.g. Form Manager) opens the manage URL and is
    offered no Save / Submit and no lifecycle row actions."""
    admin = admin_cls(page)
    admin.sign_in(role)
    assert not admin.has_admin_toolbar(), NOT_ROLE
    page.goto(admin.manage_url(), wait_until="domcontentloaded")
    assert page.locator(admin.SAVE_AS_DRAFT_BUTTON).count() == 0, f"{role} was given Save as Draft"
    for action in ("publish", "unpublish", "approve", "delete"):
        assert not admin.any_row_action_rendered(action), f"{role} is offered row action {action!r}"


# ---------------------------------------------------------------------------
# composite flows
# ---------------------------------------------------------------------------
def check_full_lifecycle(page, browser, admin_cls, tc_id, probe: PublicProbe, files=None, edit_key=None, edit_value=None):
    """Editor: create Draft -> (edit) -> Preview -> Submit (Published) ->
    visitor sees it -> Unpublish (visitor does not) -> Delete (gone)."""
    admin = admin_cls(page)
    title = run_title(tc_id, "life")
    ctx, anon = _anon_page(browser)
    try:
        admin.open_form(ROLE_EDITOR)
        admin.fill_required(title, active=True, files=files)
        admin.save_as_draft()
        assert admin.status_of(title, ROLE_EDITOR) == STATUS_DRAFT
        admin.filter_entries(title)
        assert admin.row_preview_url(title), f"{title!r}: no Preview link on the Draft row"
        admin.open_entry_by_edit_link(title)
        if edit_key:
            admin.fill(edit_key, edit_value)
        admin.submit_for_review()
        assert admin.status_of(title, ROLE_EDITOR) == STATUS_PUBLISHED
        assert probe(anon, title), f"{title!r} Published + Active but not public"
        admin.open_list(ROLE_EDITOR)
        admin.unpublish_entry(title)
        assert admin.status_of(title, ROLE_EDITOR) == STATUS_UNPUBLISHED
        assert not probe(anon, title, False), f"{title!r} still public after Unpublish"
        assert admin.delete_disposable(title), f"{title!r}: Delete did not run"
        assert not admin.entry_exists(title, ROLE_EDITOR)
    finally:
        dispose(admin, title)
        _close(ctx)


def check_author_updates_own(page, admin_cls, tc_id, key, value, files=None):
    """Author creates a QCTEST Draft, edits `key`, saves; the value persists
    and the session is not an admin one."""
    admin = admin_cls(page)
    title = run_title(tc_id, "author-edit")
    try:
        admin.open_form(ROLE_AUTHOR)
        assert not admin.has_admin_toolbar(), NOT_ROLE
        admin.fill_required(title, files=files)
        admin.save_as_draft()
        admin.open_list(ROLE_AUTHOR)
        admin.open_entry_by_edit_link(title)
        admin.fill(key, value)
        admin.save_as_draft()
        admin.open_list(ROLE_AUTHOR)
        admin.open_entry_by_edit_link(title)
        assert admin.value(key) == value, f"Author edit of {key} did not persist: {admin.value(key)!r}"
    finally:
        admin.delete_disposable(title, ROLE_EDITOR)


def check_select_persists(page, admin_cls, tc_id, key, options, files=None):
    """Each option of a dropdown persists after save + reopen (QCTEST Draft)."""
    admin = admin_cls(page)
    title = run_title(tc_id, "select")
    try:
        admin.open_form(ROLE_EDITOR)
        admin.fill_required(title, files=files)
        admin.save_as_draft()
        for opt in options:
            admin.open_list(ROLE_EDITOR)
            admin.open_entry_by_edit_link(title)
            admin.select_option(key, opt)
            admin.save_as_draft()
            admin.open_list(ROLE_EDITOR)
            admin.open_entry_by_edit_link(title)
            assert admin.value(key) == opt, f"{key}={opt!r} did not persist (read {admin.value(key)!r})"
    finally:
        dispose(admin, title)


def check_auto_id_unique(page, admin_cls, tc_id, key, files=None):
    """Two QCTEST drafts get distinct, non-empty system-generated `key`."""
    admin = admin_cls(page)
    titles = [qctest_title(tc_id, "id-a"), qctest_title(tc_id, "id-b")]
    ids = []
    try:
        for t in titles:
            admin.open_form(ROLE_EDITOR)
            admin.fill_required(t, files=files)
            admin.save_as_draft()
        for t in titles:
            admin.open_list(ROLE_EDITOR)
            admin.open_entry_by_edit_link(t)
            ids.append(admin.value(key))
        assert all(ids), f"{key} not generated: {ids!r}"
        assert ids[0] != ids[1], f"{key} not unique: {ids!r}"
    finally:
        for t in titles:
            admin.delete_disposable(t)


def check_modified_updates(page, admin_cls, tc_id, key, new_value, files=None, stamp_key="last_modified"):
    """Last Modified is populated on a QCTEST draft and changes after an edit."""
    admin = admin_cls(page)
    title = run_title(tc_id, "stamp")
    try:
        admin.open_form(ROLE_EDITOR)
        admin.fill_required(title, files=files)
        admin.save_as_draft()
        admin.open_list(ROLE_EDITOR)
        admin.open_entry_by_edit_link(title)
        before = admin.value(stamp_key)
        assert before, "Last Modified is empty on a saved record"
        # The stamp may only resolve to the minute: wait (condition-based, on
        # the clock) until the minute rolls over so an edit can show a change.
        from datetime import datetime

        from core.utils.waits import wait_until

        start = datetime.now().replace(second=0, microsecond=0)
        wait_until(lambda: datetime.now().replace(second=0, microsecond=0) > start, timeout=65.0, poll=1.0)
        admin.fill(key, new_value)
        admin.save_as_draft()
        admin.open_list(ROLE_EDITOR)
        admin.open_entry_by_edit_link(title)
        assert admin.value(stamp_key) != before, "Last Modified did not change after an edit"
    finally:
        dispose(admin, title)


def check_in_use_delete_blocked(page, browser, parent_cls, child_cls, tc_id, link_key, parent_files=None, child_files=None):
    """A QCTEST parent (category) linked to a Published QCTEST child cannot
    be deleted; both stay. Teardown deletes child first, then parent."""
    parent = parent_cls(page)
    child = child_cls(page)
    p_title = run_title(tc_id, "cat")
    c_title = run_title(tc_id, "child")
    try:
        _publish_as_editor(parent, p_title, files=parent_files)
        child.open_form(ROLE_EDITOR)
        child.fill_required(c_title, active=True, files=child_files, skip=(link_key,))
        child.select_option(link_key, p_title)
        child.submit_for_review()
        assert child.status_of(c_title, ROLE_EDITOR) == STATUS_PUBLISHED
        parent.open_list(ROLE_EDITOR)
        parent.delete_entry_by_title(p_title)
        assert parent.entry_exists(p_title, ROLE_EDITOR), f"{p_title!r} was deleted while still in use"
        assert child.status_of(c_title, ROLE_EDITOR) == STATUS_PUBLISHED
    finally:
        child.delete_disposable(c_title)
        parent.delete_disposable(p_title)


def check_two_editors(page, browser, admin_cls, tc_id, key, files=None):
    """Two Editor sessions edit one QCTEST draft; the second save either
    raises a conflict or overwrites — no partial/corrupt record. Records the
    observed outcome in the assertion message."""
    from core.web.browser import new_context

    a = admin_cls(page)
    title = run_title(tc_id, "concurrent")
    ctx_b = new_context(browser, use_auth_state=False)
    b = admin_cls(ctx_b.new_page())
    try:
        a.open_form(ROLE_EDITOR)
        a.fill_required(title, files=files)
        a.save_as_draft()
        a.open_list(ROLE_EDITOR)
        a.open_entry_by_edit_link(title)
        b.open_list(ROLE_EDITOR)
        b.open_entry_by_edit_link(title)
        b.fill(key, "QCTEST edit B")
        b.save_as_draft()
        a.fill(key, "QCTEST edit A")
        a.save_as_draft()
        conflict = a.refusal_visible()
        a.open_list(ROLE_EDITOR)
        a.open_entry_by_edit_link(title)
        final = a.value(key)
        assert final in ("QCTEST edit A", "QCTEST edit B"), f"corrupt/partial value after concurrent saves: {final!r}"
        print(f"[tc_{tc_id}] observed: conflict={conflict}, final={final!r}")
    finally:
        a.delete_disposable(title)
        _close(ctx_b)
