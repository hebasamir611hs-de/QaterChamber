"""
cms/tests/video_gallery/test_video_gallery_workflow_control_panel.py —
Control_Panel auth / workflow / publish lifecycle / category lifecycle /
Flickr-import cases of PBI 130715 ("QC - Insights & Media - 007 - Video
Gallery"), Azure suite 140374 in plan 137724 (Agent VA).

Surfaces: `manage-video-record` and `manage-video-category` (Object
Authoring) — cms/pages/video_gallery/. Public checks reuse
web/pages/video_library/* (listing cards, category dropdown, chip row,
`video-details?erc=<code>`).

Pattern (PBI 130952 / 130712, commits 1c88750 / d422936):
  - Each case runs as the account it names — Site Content Editor (156488) or
    Site Content Author (156492) — in an auth-free context; the signed-in
    userId is re-checked before every save. Cases naming no role run as the
    Editor. TEST_USER is never used.
  - Editor's submit button reads "Publish" (goes live directly); Author's
    reads "Submit for Review" (-> Pending Review). Unpublish is the row action
    `data-qc-oel-unpublish` (-> Unpublished). The "audit log" is the row's
    History trail (the only audit surface these roles have).
  - Records are disposable `QCTEST-130715-VA-<tc>-<stamp> …` videos /
    categories. Identity (title + entry id + code) is captured right after
    creation by diffing list ids; teardown deletes ONLY those captured
    records via the guarded single-record delete, signed in as the Editor.
    The real QCDEMO-130715-* videos and categories are never acted on.
  - Every public check first re-opens the record and verifies the STORED
    Active Status, then reads a fresh logged-out context (Load More expanded).

Disclosed adaptations (case wording -> what runs):
  - Titles carry the QCTEST prefix: "Chamber Awards Night" ->
    "QCTEST-130715-VA-143001-<stamp> Chamber Awards Night" (same for 143002).
  - 143008 Display Order 7 -> 700 (user rule: 100-grid); "7th chip" is
    checked as "after every real category chip" (7th counting "All Videos"
    when no other test category is live).
  - 143011 "Events" (real, shared) -> this test's own QCTEST category with
    this test's own published QCTEST video assigned (never the real one).
  - 142970 "Flickr integration settings URL": no Flickr settings screen is
    reachable for any project role — the Editor is pointed at Liferay's
    System Settings and Instance Settings screens (where integration settings
    live) and must be refused.
  - 142972 "deep-link to the publish action URL": row workflow actions are
    JS controls (`href="#"`), there is no publish URL to deep-link; the case
    checks the Author is offered no Publish control in form or row and that
    the record stays unpublished.

Blocked (skipped with the reason; rule 8 — Administrator-only Flickr import,
would pull / overwrite real shared Flickr data; no Administrator role
account exists in .env): 142968, 143012, 143013, 143014, 143015, 143016.
"""

from __future__ import annotations

from datetime import date, datetime
from time import monotonic

import allure
import pytest

from cms.pages.components.object_authoring_page import (
    STATUS_DRAFT,
    STATUS_PENDING_REVIEW,
    STATUS_PUBLISHED,
    STATUS_UNPUBLISHED,
)
from cms.pages.video_gallery.video_category_admin_page import (
    KC_NAME,
    REAL_CATEGORY_NAMES,
    VideoCategoryAdminPage,
)
from cms.pages.video_gallery.video_record_admin_page import (
    K_CATEGORY_REL,
    K_SOURCE_TYPE,
    K_THUMBNAIL,
    K_TITLE,
    K_VIDEO_URL,
    MSG_DRAFT_SAVED,
    MSG_SAVED_AND_PUBLISHED,
    MSG_SUBMITTED_FOR_REVIEW,
    ROLE_AUTHOR,
    ROLE_EDITOR,
    ROLE_USER_IDS,
    VideoDetailsPublicView,
    VideoGalleryEntry,
    VideoLibraryPublicView,
    VideoRecordAdminPage,
)
from config.settings import control_panel_url
from core.utils.waits import WaitTimeoutError, wait_until
from core.web.browser import new_context

VA_PREFIX = "QCTEST-130715-VA-"
AUTH_FREE_PAGE = pytest.mark.parametrize("page", [{"auth": False}], indirect=True)
VA_GROUP = pytest.mark.xdist_group("video_gallery_cms_va")
STAMP = datetime.now().strftime("%m%d%H%M%S")
TODAY = date.today().strftime("%d/%m/%Y")

PUBLISH_CONFIRM_TIMEOUT = 120.0
PUBLIC_REFLECT_TIMEOUT = 30.0
PUBLIC_POLL = 1.0

EPIC = "Insights & Media"
FEATURE = "Video Gallery — Control Panel (workflow)"

FLICKR_BLOCK_REASON = (
    "BLOCKED (rule 8): Flickr integration settings / manual import are Administrator-only. The project defines "
    "no Administrator role account (.env has Editor/Author/Contributor/…; TEST_USER is a super-admin setup "
    "login, not a role account), no Flickr settings or import-log screen is reachable at any Object Authoring "
    "or Control Panel URL for the role accounts (manage-flickr-video has 0 entries; Liferay System/Instance "
    "Settings refuse the Editor), and an import run would pull from / overwrite the real shared Flickr album "
    "data (136 Flickr Album records). Question for the user: may an Administrator account be provisioned and "
    "a sandbox Flickr album be used, and where is the Flickr import configuration screen?"
)


def _title(tc_id: str, suffix: str) -> str:
    return f"{VA_PREFIX}{tc_id}-{STAMP} {suffix}"


# ===========================================================================
# Fixtures
# ===========================================================================
class DisposableRegistry:
    """Records THIS test created (captured identity). Only these are deleted."""

    def __init__(self):
        self.videos: dict[str, VideoGalleryEntry] = {}
        self.categories: dict[str, VideoGalleryEntry] = {}

    def track(self, entry: VideoGalleryEntry, kind: str) -> VideoGalleryEntry:
        if not entry.in_namespace() or entry.prefix != VA_PREFIX:
            raise ValueError(f"{entry} is not a {VA_PREFIX} record")
        (self.videos if kind == "video" else self.categories)[entry.entry_id] = entry
        return entry


@pytest.fixture
def disposable(browser):
    """Deletes ONLY the registered records through the guarded delete, signed
    in as the Site Content Editor (videos first, then categories). Anything it
    cannot remove fails the teardown loudly."""
    registry = DisposableRegistry()
    yield registry
    if not registry.videos and not registry.categories:
        return
    ctx = new_context(browser, use_auth_state=False)
    outcome, failures = [], []
    try:
        page = ctx.new_page()
        video_admin = VideoRecordAdminPage(page, VA_PREFIX)
        if video_admin.login_as_role(ROLE_EDITOR) == "auth_failed":
            raise AssertionError("teardown could not sign in as the Site Content Editor")
        category_admin = VideoCategoryAdminPage(page, VA_PREFIX)
        for admin, entries in ((video_admin, registry.videos), (category_admin, registry.categories)):
            for entry in entries.values():
                label = f"{admin.slug}: {entry.title} (id {entry.entry_id}, code {entry.code})"
                try:
                    admin.open_list_all()
                    if not admin.row_present(entry):
                        if admin.is_list_fully_expanded():
                            outcome.append(f"already gone: {label}")
                        else:
                            failures.append(f"{label}: not found and the list is NOT fully expanded")
                        continue
                    admin.adopt(entry)
                    if admin.delete_disposable_entry(entry):
                        outcome.append(f"removed {label}")
                    else:
                        failures.append(f"NOT removed {label}: guarded delete refused/failed "
                                        f"(dialogs {admin.last_delete_dialogs}, banners {admin.last_delete_banners})")
                except Exception as exc:  # noqa: BLE001 — collected and raised below
                    failures.append(f"{label}: {exc!r}")
    finally:
        ctx.close()
    allure.attach("\n".join(outcome + failures) or "nothing to remove", name="QCTEST teardown")
    if failures:
        raise AssertionError("TEARDOWN LEFT QCTEST DATA BEHIND:\n" + "\n".join(failures))


def _contexts(browser):
    contexts = []

    def _make():
        ctx = new_context(browser, use_auth_state=False)
        contexts.append(ctx)
        return ctx.new_page()

    return contexts, _make


@pytest.fixture
def anon_pages(browser):
    """Fresh logged-out contexts for every public read."""
    contexts, make = _contexts(browser)
    yield make
    for ctx in contexts:
        try:
            ctx.close()
        except Exception:  # noqa: BLE001
            pass


# ===========================================================================
# Helpers (test layer — no raw Playwright)
# ===========================================================================
def _login(page, role: str, kind: str = "video"):
    """Signs in as `role`; skips (never falls back to another account) when the
    account cannot sign in or is not the pinned userId."""
    admin = VideoRecordAdminPage(page, VA_PREFIX) if kind == "video" else VideoCategoryAdminPage(page, VA_PREFIX)
    outcome = admin.login_as_role(role)
    if outcome == "auth_failed":
        pytest.skip(f"PRECONDITION: Liferay refused the .env credentials for '{role}'")
    admin.open_list_all()
    user_id, _ = admin.signed_in_user()
    if not user_id:
        pytest.fail(f"login as '{role}' neither succeeded nor showed Liferay's refusal banner")
    if user_id != ROLE_USER_IDS[role]:
        pytest.skip(f"PRECONDITION: '{role}' signs in as userId {user_id!r}, not the pinned {ROLE_USER_IDS[role]}")
    return admin


def _category_admin(video_admin: VideoRecordAdminPage) -> VideoCategoryAdminPage:
    """Same signed-in page, category object."""
    return VideoCategoryAdminPage(video_admin.page, VA_PREFIX)


def _pinned(admin, role: str) -> None:
    user_id, _ = admin.signed_in_user()
    assert user_id == ROLE_USER_IDS[role], (
        f"the session is now userId {user_id!r}, not the pinned {role} ({ROLE_USER_IDS[role]})")


def _create(admin, disposable, data: dict, publish: bool, role: str, kind: str = "video") -> VideoGalleryEntry:
    """Creates one record (publish=True -> the role's submit button, else Save as
    Draft), registers whatever got created for teardown, THEN asserts.
    `admin.create_banners` keeps the edit-bar messages shown after the save."""
    title_key = K_TITLE if kind == "video" else KC_NAME
    ids_before = admin.snapshot_ids()
    went_through, diagnostics, banners, arabic = False, {}, [], ""
    expected = (MSG_DRAFT_SAVED if not publish
                else MSG_SUBMITTED_FOR_REVIEW if role == ROLE_AUTHOR else MSG_SAVED_AND_PUBLISHED)
    entry = None
    try:
        admin.open_create_form_en()
        admin.fill_video(data) if kind == "video" else admin.fill_category(data)
        _pinned(admin, role)
        admin.click_publish() if publish else admin.click_save_as_draft()
        went_through = admin.save_went_through()
        diagnostics = admin.refusal_evidence()
        if went_through:
            banners = admin.success_messages(expected, timeout=15.0)
            arabic = admin.wait_arabic_saved()
        admin.evidence(f"{data[title_key]} after {'submit' if publish else 'draft'}")
    finally:
        try:
            entry = admin.identify_created(data[title_key], ids_before)
            if entry:
                disposable.track(entry, kind)
        except Exception as exc:  # noqa: BLE001 — registration must not mask the result
            allure.attach(repr(exc), name=f"registration of {data[title_key]!r} failed")
    admin.create_banners = banners
    allure.attach("\n".join(banners) or "(none)", name=f"edit-bar after creating {data[title_key]}")
    allure.attach(arabic or "(no Arabic-save message within 25 s)", name="Arabic content save")
    assert went_through, f"creating {data[title_key]!r} as {role} did not go through: {diagnostics}"
    assert entry is not None, f"{data[title_key]!r} went through but is not identifiable as exactly one NEW record"
    return entry


def _has(banners: list[str], expected: str) -> bool:
    return any(expected in b for b in banners)


def _publish_open_record(admin, entry: VideoGalleryEntry, role: str = ROLE_EDITOR) -> list[str]:
    """Re-opens the captured record and clicks the role's submit button."""
    admin.open_entry_en(entry.code)
    _pinned(admin, role)
    admin.click_publish()
    banners = (admin.success_messages(MSG_SAVED_AND_PUBLISHED if role == ROLE_EDITOR else MSG_SUBMITTED_FOR_REVIEW)
               if admin.save_went_through() else admin.editbar_texts())
    admin.evidence(f"{entry.title} after publish click")
    allure.attach("\n".join(banners) or "(none)", name=f"edit-bar after publishing {entry.title}")
    return banners


def _history(admin, entry: VideoGalleryEntry) -> list[dict]:
    trail = admin.history(entry)
    allure.attach("\n".join(repr(h) for h in trail) or admin.history_cell_text(entry) or "(empty)",
                  name=f"History of {entry.title}")
    return trail


def _require_active_status(admin, entry: VideoGalleryEntry) -> None:
    """User rule: Active Status must be STORED as ticked before ANY public check."""
    admin.open_entry_en(entry.code)
    stored = admin.active_status_stored()
    allure.attach(f"stored Active Status: {stored!r}", name="public-visibility precondition")
    if stored != "true":
        pytest.fail(f"PRECONDITION NOT MET — PRODUCT: {entry.title!r} stores Active Status {stored!r}, not 'true'; "
                    f"the public step was not run")


def _public_until(anon_pages, predicate, message: str, locale: str = "en") -> VideoLibraryPublicView:
    """Publish-then-poll on the logged-out Video Library (one context)."""
    view = VideoLibraryPublicView(anon_pages())
    started = monotonic()

    def _check() -> bool:
        view.open_listing_all(locale)
        return bool(predicate(view))

    try:
        wait_until(_check, timeout=PUBLIC_REFLECT_TIMEOUT, poll=PUBLIC_POLL, message=message)
    except WaitTimeoutError:
        view.screenshot("public video library at timeout")
        pytest.fail(f"{message} within {PUBLIC_REFLECT_TIMEOUT:.0f}s "
                    f"(cards: {[c['title'] for c in view.cards()]}, chips: {view.chip_texts()})")
    allure.attach(f"{monotonic() - started:.1f}s", name="observed public latency")
    return view


def _card_public(anon_pages, entry: VideoGalleryEntry) -> dict:
    view = _public_until(anon_pages, lambda v: bool(v.card_for_code(entry.code)),
                         f"DELIVERY: {entry.title!r} never appeared on the logged-out Video Library")
    return view.card_for_code(entry.code)


def _assert_video_not_public(anon_pages, entry: VideoGalleryEntry, titles: tuple = ()) -> None:
    """Absence that cannot pass vacuously: the listing must render real cards first."""
    _public_until(anon_pages, lambda v: not v.card_for_code(entry.code) and len(v.cards()) > 0,
                  f"{entry.title!r} was still on the logged-out Video Library")
    view = VideoLibraryPublicView(anon_pages()).open_listing_all()
    cards = view.cards()
    assert cards, f"cannot prove {entry.title!r} is absent: the logged-out listing shows no cards"
    assert not view.card_for_code(entry.code), f"{entry.title!r} is on the logged-out Video Library"
    for title in (entry.title,) + tuple(titles):
        assert title not in [c["title"] for c in cards], f"a card titled {title!r} is on the listing"


def _details(anon_pages, entry: VideoGalleryEntry) -> dict:
    state = VideoDetailsPublicView(anon_pages()).details_state(entry.code)
    allure.attach(repr(state), name=f"logged-out details URL of {entry.title}")
    return state


def _category_public(view: VideoLibraryPublicView, name: str) -> dict:
    return {"chip": name in view.chip_texts(), "dropdown": name in view.dropdown_texts(),
            "chips": view.chip_texts(), "options": view.dropdown_texts()}


def _video_data(tc_id: str, suffix: str, **overrides) -> dict:
    return VideoRecordAdminPage.default_video_data(_title(tc_id, suffix), **{"publishedDate": TODAY, **overrides})


def _new_published_video(admin, disposable, tc_id: str, suffix: str, **overrides) -> VideoGalleryEntry:
    entry = _create(admin, disposable, _video_data(tc_id, suffix, **overrides), publish=True, role=ROLE_EDITOR)
    assert _has(admin.create_banners, MSG_SAVED_AND_PUBLISHED), (
        f"publishing {entry.title!r} showed {admin.create_banners}, not {MSG_SAVED_AND_PUBLISHED!r}")
    status = admin.wait_status(entry, (STATUS_PUBLISHED,), timeout=PUBLISH_CONFIRM_TIMEOUT)
    assert status == STATUS_PUBLISHED, f"{entry.title!r} reads {status!r} after Publish, not Published"
    return entry


def _case_markers(tc: str, *extra):
    def _wrap(fn):
        for mark in (pytest.mark.control_panel, pytest.mark.media, pytest.mark.pbi_130715,
                     getattr(pytest.mark, f"tc_{tc}"), *extra, VA_GROUP):
            fn = mark(fn)
        return fn
    return _wrap


# ===========================================================================
# 142969 — Editor publishes a complete draft
# ===========================================================================
@AUTH_FREE_PAGE
@allure.epic(EPIC)
@allure.feature(FEATURE)
@allure.story("Auth / RBAC")
@allure.title("Site Content Editor can publish a video record")
@_case_markers("142969", pytest.mark.auth)
def test_editor_can_publish_video_record(page, disposable, anon_pages):
    # Azure TC 142969 | PBI 130715 | account: Site Content Editor (156488)
    editor = _login(page, ROLE_EDITOR)
    entry = _create(editor, disposable, _video_data("142969", "Editor publish"), publish=False, role=ROLE_EDITOR)
    assert _has(editor.create_banners, MSG_DRAFT_SAVED), f"no {MSG_DRAFT_SAVED!r}: {editor.create_banners}"

    # Step 2 — open the complete draft: Publish is offered and enabled.
    editor.open_entry_en(entry.code)
    buttons = editor.form_buttons()
    allure.attach(repr(buttons), name="enabled form buttons on the draft")
    assert "Publish" in buttons, f"the Editor's draft offers no enabled Publish button: {buttons}"

    # Step 3 — Publish -> Published + on the public Video Library.
    banners = _publish_open_record(editor, entry)
    assert editor.save_went_through(), f"Publish did not go through: {editor.refusal_evidence()}"
    assert _has(banners, MSG_SAVED_AND_PUBLISHED), f"Publish showed {banners}"
    status = editor.wait_status(entry, (STATUS_PUBLISHED,), timeout=PUBLISH_CONFIRM_TIMEOUT)
    assert status == STATUS_PUBLISHED, f"status after Publish is {status!r}, not Published"
    _require_active_status(editor, entry)
    card = _card_public(anon_pages, entry)
    assert card["title"] == entry.title, f"public card reads {card}"


# ===========================================================================
# 142970 — Editor is denied Flickr integration settings
# ===========================================================================
SETTINGS_URLS = {
    "System Settings": "/group/guest/~/control_panel/manage?p_p_id="
                       "com_liferay_configuration_admin_web_portlet_SystemSettingsPortlet",
    "Instance Settings": "/group/guest/~/control_panel/manage?p_p_id="
                         "com_liferay_configuration_admin_web_portlet_InstanceSettingsPortlet",
}
EXPECTED_DENIED_EN = "Access Denied. You do not have permission to perform this action."


@AUTH_FREE_PAGE
@allure.epic(EPIC)
@allure.feature(FEATURE)
@allure.story("Auth / RBAC")
@allure.title("Site Content Editor is denied access to Flickr integration settings")
@_case_markers("142970", pytest.mark.auth)
def test_editor_denied_flickr_integration_settings(page):
    # Azure TC 142970 | PBI 130715 | account: Site Content Editor (156488).
    # Substitution disclosed in the module docstring: the integration
    # settings screens are Liferay's System / Instance Settings.
    editor = _login(page, ROLE_EDITOR)
    results, findings = {}, []
    for name, path in SETTINGS_URLS.items():
        editor.open(control_panel_url(path))
        body = editor.rendered_body_text()
        editor.evidence(f"142970 editor direct {name}")
        refused = "do not have the roles required" in body or "do not have permission" in body \
            or "Access Denied" in body
        shows_flickr = "flickr" in body.casefold()
        results[name] = {"refused": refused, "flickr_settings_shown": shows_flickr, "text": " ".join(body.split())[:300]}
        if refused and EXPECTED_DENIED_EN not in body:
            findings.append(f"{name}: refusal reads {' '.join(body.split())[:160]!r}, not {EXPECTED_DENIED_EN!r}")
    allure.attach(repr(results), name="direct-URL attempts as the Editor")
    allure.attach("\n".join(findings) or "none", name="LOW-priority wording findings (block works)")
    for name, res in results.items():
        assert res["refused"], f"PRODUCT: the Editor opened {name} without an access refusal: {res}"
        assert not res["flickr_settings_shown"], f"PRODUCT: Flickr settings are shown to the Editor on {name}"


# ===========================================================================
# 142971 — Author creates and submits for review
# ===========================================================================
@AUTH_FREE_PAGE
@allure.epic(EPIC)
@allure.feature(FEATURE)
@allure.story("Auth / RBAC")
@allure.title("Site Content Author can create and submit a video record for review")
@_case_markers("142971", pytest.mark.auth)
def test_author_creates_and_submits_for_review(page, disposable):
    # Azure TC 142971 | PBI 130715 | account: Site Content Author (156492)
    author = _login(page, ROLE_AUTHOR)
    entry = _create(author, disposable, _video_data("142971", "Author submit"), publish=False, role=ROLE_AUTHOR)
    assert _has(author.create_banners, MSG_DRAFT_SAVED), f"no {MSG_DRAFT_SAVED!r}: {author.create_banners}"
    author.open_list_all()
    assert author.row_status(entry) == STATUS_DRAFT, f"new record reads {author.row_status_raw(entry)!r}, not Draft"

    author.open_entry_en(entry.code)
    buttons = author.form_buttons(enabled_only=False)
    allure.attach(repr(buttons), name="Author form buttons")
    assert "Publish" not in buttons, f"the Author's form offers Publish: {buttons}"
    banners = _publish_open_record(author, entry, role=ROLE_AUTHOR)
    assert author.save_went_through(), f"Submit for Review did not go through: {author.refusal_evidence()}"
    assert _has(banners, MSG_SUBMITTED_FOR_REVIEW), f"Submit for Review showed {banners}"
    status = author.wait_status(entry, (STATUS_PENDING_REVIEW, STATUS_PUBLISHED), timeout=60.0)
    assert status == STATUS_PENDING_REVIEW, f"after Submit for Review the record reads {status!r}, not Pending Review"
    actions = author.row_actions(entry)
    allure.attach(repr(actions), name="Author row actions on the submitted record")
    assert "publish" not in actions and "approve" not in actions, f"the Author is offered {actions}"


# ===========================================================================
# 142972 — Author has no direct publish
# ===========================================================================
@AUTH_FREE_PAGE
@allure.epic(EPIC)
@allure.feature(FEATURE)
@allure.story("Auth / RBAC")
@allure.title("Site Content Author is denied direct publish action")
@_case_markers("142972", pytest.mark.auth)
def test_author_denied_direct_publish(page, disposable, anon_pages):
    # Azure TC 142972 | PBI 130715 | account: Site Content Author (156492)
    author = _login(page, ROLE_AUTHOR)
    entry = _create(author, disposable, _video_data("142972", "Author no publish"), publish=False, role=ROLE_AUTHOR)
    author.open_entry_en(entry.code)
    buttons = author.form_buttons(enabled_only=False)
    author.open_list_all()
    actions, labels = author.row_actions(entry), author.row_link_labels(entry)
    allure.attach(f"form {buttons}\nrow actions {actions}\nrow labels {labels}", name="Author publish controls")
    assert "Publish" not in buttons, f"PRODUCT: the Author's own draft offers a Publish button: {buttons}"
    assert "publish" not in actions and "Publish" not in labels, f"PRODUCT: the Author's row offers Publish: {labels}"
    assert author.row_status(entry) in (STATUS_DRAFT, STATUS_PENDING_REVIEW), (
        f"the Author's record reads {author.row_status_raw(entry)!r}")
    allure.attach("Row workflow actions are JS controls (href='#'); no publish-action URL exists to deep-link.",
                  name="deep-link sub-step")
    _assert_video_not_public(anon_pages, entry)


# ===========================================================================
# 143001 — create + publish -> visible publicly
# ===========================================================================
@AUTH_FREE_PAGE
@allure.epic(EPIC)
@allure.feature(FEATURE)
@allure.story("Publish lifecycle")
@allure.title("Creating a new video record and publishing it makes it visible on the public Video Library")
@_case_markers("143001", pytest.mark.functional_high, pytest.mark.regression, pytest.mark.uat)
def test_create_and_publish_video_visible_publicly(page, disposable, anon_pages):
    # Azure TC 143001 | PBI 130715 | account: Site Content Editor (156488)
    editor = _login(page, ROLE_EDITOR)
    data = _video_data("143001", "Chamber Awards Night", videoTitle_ar="حفل جوائز الغرفة",
                       duration="05:12", videoUrl="https://vimeo.com/123456789")
    entry = _create(editor, disposable, data, publish=False, role=ROLE_EDITOR)
    assert _has(editor.create_banners, MSG_DRAFT_SAVED), f"no {MSG_DRAFT_SAVED!r}: {editor.create_banners}"
    editor.open_entry_en(entry.code)
    stored = editor.read_video()
    allure.attach(repr(stored), name="stored values")
    assert stored[f"{K_SOURCE_TYPE}-label"] == "External URL" and stored[K_VIDEO_URL] == data[K_VIDEO_URL], stored
    assert stored[f"{K_THUMBNAIL}_uploaded_as"], f"the thumbnail was not stored: {stored}"

    banners = _publish_open_record(editor, entry)
    assert _has(banners, MSG_SAVED_AND_PUBLISHED), f"Publish showed {banners}"
    assert editor.wait_status(entry, (STATUS_PUBLISHED,), timeout=PUBLISH_CONFIRM_TIMEOUT) == STATUS_PUBLISHED
    _require_active_status(editor, entry)
    card = _card_public(anon_pages, entry)
    allure.attach(repr(card), name="public card")
    assert card["title"] == entry.title, card
    assert card["tag"] == "Events", f"card category reads {card['tag']!r}, not 'Events'"
    assert card["duration"] == "05:12", f"card duration reads {card['duration']!r}"
    assert card["thumb"] and not card["fallback"], f"card shows no thumbnail: {card}"


# ===========================================================================
# 143002 — edit published title + republish -> new value public
# ===========================================================================
@AUTH_FREE_PAGE
@allure.epic(EPIC)
@allure.feature(FEATURE)
@allure.story("Publish lifecycle")
@allure.title("Editing a published video and republishing shows the new value publicly, not the stale one")
@_case_markers("143002", pytest.mark.functional_high)
def test_edit_published_video_republish_shows_new_value(page, disposable, anon_pages):
    # Azure TC 143002 | PBI 130715 | account: Site Content Editor (156488)
    editor = _login(page, ROLE_EDITOR)
    entry = _new_published_video(editor, disposable, "143002", "Chamber Awards Night")
    _require_active_status(editor, entry)
    _card_public(anon_pages, entry)

    new_title = f"{entry.title} 2026"
    editor.open_entry_en(entry.code)
    editor.fill_en(K_TITLE, new_title)
    _pinned(editor, ROLE_EDITOR)
    editor.click_publish()
    banners = editor.success_messages(MSG_SAVED_AND_PUBLISHED) if editor.save_went_through() else editor.editbar_texts()
    editor.evidence("143002 after republish")
    renamed = entry.with_title(new_title)
    disposable.track(renamed, "video")
    assert editor.save_went_through(), f"republish did not go through: {editor.refusal_evidence()}"
    assert _has(banners, MSG_SAVED_AND_PUBLISHED), f"republish showed {banners}"
    assert editor.wait_status(renamed, (STATUS_PUBLISHED,), timeout=PUBLISH_CONFIRM_TIMEOUT) == STATUS_PUBLISHED
    _require_active_status(editor, renamed)
    view = _public_until(anon_pages, lambda v: v.card_for_code(entry.code).get("title") == new_title,
                         f"the public card never showed the new title {new_title!r}")
    titles = [c["title"] for c in view.cards()]
    assert entry.title not in titles, f"the stale title {entry.title!r} is still public: {titles}"


# ===========================================================================
# 143003 — preview a draft, never public
# ===========================================================================
@AUTH_FREE_PAGE
@allure.epic(EPIC)
@allure.feature(FEATURE)
@allure.story("Preview")
@allure.title("Previewing a draft video shows the draft content without exposing it publicly")
@_case_markers("143003", pytest.mark.functional_high)
def test_preview_draft_not_public(page, disposable, anon_pages):
    # Azure TC 143003 | PBI 130715 | account: Site Content Editor (156488)
    editor = _login(page, ROLE_EDITOR)
    entry = _create(editor, disposable, _video_data("143003", "Draft preview"), publish=False, role=ROLE_EDITOR)
    editor.open_list_all()
    href = editor.row_preview_href(entry)
    assert href, "the draft row offers no Preview link"
    text = editor.open_listing_preview_expanded(href, entry.title)
    editor.evidence("143003 draft preview")
    assert entry.title in text, f"the Preview never rendered the draft title {entry.title!r}"
    assert "PREVIEW" in text, "the Preview frame carries no PREVIEW banner"

    state = _details(anon_pages, entry)
    assert state["not_found"] and state["title"] != entry.title, (
        f"PRODUCT: the draft is reachable on its logged-out details URL: {state}")
    _assert_video_not_public(anon_pages, entry)


# ===========================================================================
# 143004 / 143005 — publish blocked without thumbnail / source
# ===========================================================================
def _publish_blocked_case(page, disposable, anon_pages, tc: str, suffix: str, overrides: dict,
                          expected_msg: str, field_hint: str):
    editor = _login(page, ROLE_EDITOR)
    data = _video_data(tc, suffix, **overrides)
    entry = _create(editor, disposable, data, publish=False, role=ROLE_EDITOR)
    assert _has(editor.create_banners, MSG_DRAFT_SAVED), f"the incomplete record did not save as Draft: " \
                                                         f"{editor.create_banners}"
    editor.open_entry_en(entry.code)
    _pinned(editor, ROLE_EDITOR)
    editor.click_publish()
    evidence = {"went_through": editor.save_went_through(), "refused": editor.save_was_refused(),
                "messages": editor.all_messages_text(), **editor.refusal_evidence()}
    editor.evidence(f"{tc} publish attempt")
    allure.attach(repr(evidence), name="publish attempt")
    status = editor.wait_status(entry, (STATUS_PUBLISHED, STATUS_DRAFT), timeout=30.0)
    assert status != STATUS_PUBLISHED, f"PRODUCT: the record without {field_hint} was PUBLISHED: {evidence}"
    _assert_video_not_public(anon_pages, entry)
    if expected_msg not in evidence["messages"]:
        allure.attach(f"expected {expected_msg!r}; shown {evidence['messages']!r}",
                      name="LOW-priority wording finding (block works)")
    return evidence


@AUTH_FREE_PAGE
@allure.epic(EPIC)
@allure.feature(FEATURE)
@allure.story("Publish validation")
@allure.title("Publish is blocked when the video record has no thumbnail")
@_case_markers("143004", pytest.mark.functional_high, pytest.mark.regression)
def test_publish_blocked_without_thumbnail(page, disposable, anon_pages):
    # Azure TC 143004 | PBI 130715 | account: Site Content Editor (156488)
    _publish_blocked_case(page, disposable, anon_pages, "143004", "No thumbnail", {K_THUMBNAIL: None},
                          "A video thumbnail is required.", "a thumbnail")


@AUTH_FREE_PAGE
@allure.epic(EPIC)
@allure.feature(FEATURE)
@allure.story("Publish validation")
@allure.title("Publish is blocked when the video record has no playable source")
@_case_markers("143005", pytest.mark.functional_high, pytest.mark.regression)
def test_publish_blocked_without_source(page, disposable, anon_pages):
    # Azure TC 143005 | PBI 130715 | account: Site Content Editor (156488)
    _publish_blocked_case(page, disposable, anon_pages, "143005", "No source",
                          {K_SOURCE_TYPE: None, K_VIDEO_URL: None},
                          "A video source is required.", "a source")


# ===========================================================================
# 143006 — unpublish removes listing + details URL
# ===========================================================================
@AUTH_FREE_PAGE
@allure.epic(EPIC)
@allure.feature(FEATURE)
@allure.story("Publish lifecycle")
@allure.title("Unpublishing a published video removes it from the public listing and its Details URL")
@_case_markers("143006", pytest.mark.functional_high, pytest.mark.regression, pytest.mark.uat)
def test_unpublish_removes_listing_and_details(page, disposable, anon_pages):
    # Azure TC 143006 | PBI 130715 | account: Site Content Editor (156488)
    editor = _login(page, ROLE_EDITOR)
    entry = _new_published_video(editor, disposable, "143006", "Chamber Awards Night 2026")
    _require_active_status(editor, entry)
    _card_public(anon_pages, entry)
    live = _details(anon_pages, entry)
    assert live["title"] == entry.title, f"the published video's details URL does not show it: {live}"

    editor.open_list_all()
    dialogs = editor.run_row_action(entry, "unpublish")
    allure.attach(repr(dialogs), name="unpublish dialogs")
    status = editor.wait_status(entry, (STATUS_UNPUBLISHED,), timeout=PUBLISH_CONFIRM_TIMEOUT)
    editor.evidence("143006 after unpublish")
    assert status == STATUS_UNPUBLISHED, f"after Unpublish the record reads {status!r}"

    _assert_video_not_public(anon_pages, entry)
    gone = _details(anon_pages, entry)
    assert gone["title"] != entry.title, f"PRODUCT: the unpublished video still renders on its URL: {gone}"
    assert gone["not_found"], f"the details URL shows neither the video nor a not-found state: {gone}"
    allure.attach(f"HTTP {gone['status']} with in-page not-found {gone['not_found_text']!r}",
                  name="details URL after unpublish (soft-404 shape)")


# ===========================================================================
# 143007 — delete removes permanently
# ===========================================================================
@AUTH_FREE_PAGE
@allure.epic(EPIC)
@allure.feature(FEATURE)
@allure.story("Delete")
@allure.title("Deleting a video record removes it permanently")
@_case_markers("143007", pytest.mark.functional_high)
def test_delete_video_record_permanently(page, disposable, anon_pages):
    # Azure TC 143007 | PBI 130715 | account: Site Content Editor (156488)
    editor = _login(page, ROLE_EDITOR)
    entry = _new_published_video(editor, disposable, "143007", "Disposable delete")
    _require_active_status(editor, entry)
    _card_public(anon_pages, entry)

    deleted = editor.delete_disposable_entry(entry)
    allure.attach(f"dialogs {editor.last_delete_dialogs}\nbanners {editor.last_delete_banners}", name="delete")
    editor.evidence("143007 after delete")
    assert deleted, f"the guarded delete of {entry.title!r} did not complete (see log)"
    editor.open_list_all()
    assert editor.is_list_fully_expanded() and not editor.row_present(entry) \
        and not editor.row_present_by_title(entry.title), f"{entry.title!r} is still in the admin listing"
    _assert_video_not_public(anon_pages, entry)
    state = _details(anon_pages, entry)
    assert state["title"] != entry.title, f"the deleted video still renders on its URL: {state}"


# ===========================================================================
# 143008 / 143009 / 143010 / 143011 — Video Category lifecycle
# ===========================================================================
def _category_data(tc: str, suffix: str, name_ar: str, order: int = 700) -> dict:
    return VideoCategoryAdminPage.default_category_data(_title(tc, suffix), name_ar=name_ar, display_order=order)


def _new_published_category(cat_admin, disposable, tc: str, suffix: str, name_ar: str) -> VideoGalleryEntry:
    entry = _create(cat_admin, disposable, _category_data(tc, suffix, name_ar), publish=True,
                    role=ROLE_EDITOR, kind="category")
    assert _has(cat_admin.create_banners, MSG_SAVED_AND_PUBLISHED), cat_admin.create_banners
    assert cat_admin.wait_status(entry, (STATUS_PUBLISHED,), timeout=PUBLISH_CONFIRM_TIMEOUT) == STATUS_PUBLISHED
    return entry


@AUTH_FREE_PAGE
@allure.epic(EPIC)
@allure.feature(FEATURE)
@allure.story("Video Category lifecycle")
@allure.title("Creating and publishing a Video Category adds it to the frontend dropdown and chip row in order")
@_case_markers("143008", pytest.mark.functional_high, pytest.mark.regression, pytest.mark.uat)
def test_publish_category_appears_in_dropdown_and_chips(page, disposable, anon_pages):
    # Azure TC 143008 | PBI 130715 | account: Site Content Editor (156488)
    editor = _login(page, ROLE_EDITOR, kind="category")
    entry = _create(editor, disposable, _category_data("143008", "Sustainability", "الاستدامة"),
                    publish=False, role=ROLE_EDITOR, kind="category")
    assert _has(editor.create_banners, MSG_DRAFT_SAVED), editor.create_banners
    editor.open_list_all()
    assert editor.row_status(entry) == STATUS_DRAFT, f"the new category reads {editor.row_status_raw(entry)!r}"
    banners = _publish_open_record(editor, entry)
    assert _has(banners, MSG_SAVED_AND_PUBLISHED), f"Publish showed {banners}"
    assert editor.wait_status(entry, (STATUS_PUBLISHED,), timeout=PUBLISH_CONFIRM_TIMEOUT) == STATUS_PUBLISHED
    _require_active_status(editor, entry)

    view = _public_until(anon_pages, lambda v: _category_public(v, entry.title)["chip"]
                         and _category_public(v, entry.title)["dropdown"],
                         f"DELIVERY: category {entry.title!r} never appeared in BOTH the dropdown and the chip row")
    seen = _category_public(view, entry.title)
    allure.attach(repr(seen), name="public dropdown / chips")
    chips = seen["chips"]
    real_positions = [chips.index(n) for n in REAL_CATEGORY_NAMES if n in chips]
    assert chips.index(entry.title) > max(real_positions), (
        f"Display Order 700 should place {entry.title!r} after every real category chip: {chips}")
    others = [c for c in chips if c.startswith("QCTEST-")]
    if others == [entry.title]:
        assert chips.index(entry.title) == 6, f"{entry.title!r} is not the 7th chip: {chips}"


@AUTH_FREE_PAGE
@allure.epic(EPIC)
@allure.feature(FEATURE)
@allure.story("Video Category lifecycle")
@allure.title("Unpublishing a Video Category removes it from the frontend dropdown and chip row")
@_case_markers("143009", pytest.mark.functional_high)
def test_unpublish_category_removed_from_frontend(page, disposable, anon_pages):
    # Azure TC 143009 | PBI 130715 | account: Site Content Editor (156488)
    editor = _login(page, ROLE_EDITOR, kind="category")
    entry = _new_published_category(editor, disposable, "143009", "Sustainability", "الاستدامة")
    _require_active_status(editor, entry)
    _public_until(anon_pages, lambda v: _category_public(v, entry.title)["chip"]
                  and _category_public(v, entry.title)["dropdown"],
                  f"PRECONDITION: category {entry.title!r} never became visible publicly")
    editor.open_list_all()
    editor.run_row_action(entry, "unpublish")
    status = editor.wait_status(entry, (STATUS_UNPUBLISHED,), timeout=PUBLISH_CONFIRM_TIMEOUT)
    editor.evidence("143009 after unpublish")
    assert status == STATUS_UNPUBLISHED, f"after Unpublish the category reads {status!r}"
    view = _public_until(anon_pages, lambda v: len(v.chip_texts()) > 1 and not _category_public(v, entry.title)["chip"]
                         and not _category_public(v, entry.title)["dropdown"],
                         f"category {entry.title!r} is still in the public dropdown / chip row")
    allure.attach(repr(_category_public(view, entry.title)), name="public dropdown / chips after unpublish")


@AUTH_FREE_PAGE
@allure.epic(EPIC)
@allure.feature(FEATURE)
@allure.story("Video Category lifecycle")
@allure.title("Deleting an unlinked Video Category succeeds")
@_case_markers("143010", pytest.mark.functional_high)
def test_delete_unlinked_category(page, disposable, anon_pages):
    # Azure TC 143010 | PBI 130715 | account: Site Content Editor (156488)
    editor = _login(page, ROLE_EDITOR, kind="category")
    entry = _new_published_category(editor, disposable, "143010", "Unlinked", "غير مرتبط")
    deleted = editor.delete_disposable_entry(entry)
    allure.attach(f"dialogs {editor.last_delete_dialogs}\nbanners {editor.last_delete_banners}", name="delete")
    editor.evidence("143010 after delete")
    assert deleted, f"deleting the unlinked category {entry.title!r} did not complete"
    editor.open_list_all()
    assert not editor.row_present(entry) and not editor.row_present_by_title(entry.title)
    _public_until(anon_pages, lambda v: len(v.chip_texts()) > 1 and not _category_public(v, entry.title)["chip"]
                  and not _category_public(v, entry.title)["dropdown"],
                  f"the deleted category {entry.title!r} is still on the frontend")


@AUTH_FREE_PAGE
@allure.epic(EPIC)
@allure.feature(FEATURE)
@allure.story("Video Category lifecycle")
@allure.title("Deleting a Video Category linked to published videos is blocked until reassigned")
@_case_markers("143011", pytest.mark.functional_high)
def test_delete_category_linked_to_published_video_blocked(page, disposable, anon_pages):
    # Azure TC 143011 | PBI 130715 | account: Site Content Editor (156488).
    # Own QCTEST category + own QCTEST video (never the real "Events").
    video_admin = _login(page, ROLE_EDITOR)
    cat_admin = _category_admin(video_admin)
    category = _new_published_category(cat_admin, disposable, "143011", "Linked", "مرتبط")
    video = _new_published_video(video_admin, disposable, "143011", "Linked video",
                                 **{K_CATEGORY_REL: category.title})
    video_admin.open_entry_en(video.code)
    assert video_admin.picklist_value(K_CATEGORY_REL) == category.entry_id, (
        f"the video is not linked to {category.title!r}: {video_admin.picklist_label(K_CATEGORY_REL)!r}")
    _require_active_status(video_admin, video)
    _card_public(anon_pages, video)

    cat_admin.adopt(category)
    deleted = cat_admin.delete_disposable_entry(category)
    messages = cat_admin.last_delete_dialogs + cat_admin.last_delete_banners
    cat_admin.evidence("143011 after delete attempt")
    allure.attach(repr(messages), name="delete attempt messages")
    cat_admin.open_list_all()
    still_listed = cat_admin.row_present(category)
    video_admin.open_entry_en(video.code)
    link_after = video_admin.picklist_value(K_CATEGORY_REL)
    card = VideoLibraryPublicView(anon_pages()).open_listing_all().card_for_code(video.code)
    allure.attach(f"category listed: {still_listed}\nvideo category id now {link_after!r}\ncard {card}",
                  name="state after the delete attempt")
    assert not deleted and still_listed, (
        f"PRODUCT: the category linked to a published video was DELETED (no in-use block); messages {messages}; "
        f"video's category now {link_after!r}; public card {card}")
    assert link_after == category.entry_id, f"the video's category link changed to {link_after!r}"
    assert card, "the linked published video disappeared from the public listing"
    # User rule: the block works -> wording-only gaps are LOW findings, not failures.
    # Live 2026-10-05 the refusal reads "Delete failed: Object relationship 135056 does not allow deletes".
    if not any("in use" in m.casefold() or "assigned" in m.casefold() or "reassign" in m.casefold() for m in messages):
        allure.attach(f"no 'category is in use' wording; shown {messages}", name="LOW-priority wording finding")


# ===========================================================================
# 143017 — publish shows success message + audit (History) entry
# ===========================================================================
@AUTH_FREE_PAGE
@allure.epic(EPIC)
@allure.feature(FEATURE)
@allure.story("Audit")
@allure.title("Admin publish shows the Liferay success message and records an audit log entry")
@_case_markers("143017", pytest.mark.functional_high)
def test_publish_shows_success_and_audit_entry(page, disposable):
    # Azure TC 143017 | PBI 130715 | account: Site Content Editor (156488)
    editor = _login(page, ROLE_EDITOR)
    _, user_name = editor.signed_in_user()
    entry = _create(editor, disposable, _video_data("143017", "Audit"), publish=False, role=ROLE_EDITOR)
    banners = _publish_open_record(editor, entry)
    assert _has(banners, MSG_SAVED_AND_PUBLISHED), f"Publish showed {banners}, not {MSG_SAVED_AND_PUBLISHED!r}"
    assert editor.wait_status(entry, (STATUS_PUBLISHED,), timeout=PUBLISH_CONFIRM_TIMEOUT) == STATUS_PUBLISHED
    trail = _history(editor, entry)
    editor.evidence("143017 history")
    # Live 2026-10-05: the Editor's Publish is recorded as "Submitted for review"
    # followed by "Approved" (privileged bypass) — "Approved" is the publish transition.
    published = [h for h in trail if h["action"].casefold() in ("approved", "published", "publish")]
    assert published, f"no publish entry in the record's History: {trail or editor.history_cell_text(entry)}"
    last = published[0]  # newest first
    assert last["who"], f"the publish History entry names no actor: {last}"
    assert user_name.split()[0].casefold() in last["text"].casefold() or "editor" in last["text"].casefold(), (
        f"the publish History entry does not name the Editor ({user_name!r}): {last}")
    assert last["when"], f"the publish History entry has no timestamp: {last}"


# ===========================================================================
# Blocked — Administrator-only Flickr import (rule 8)
# ===========================================================================
_BLOCKED = {
    "142968": "Administrator can access and configure Flickr integration settings",
    "143012": "Manual Flickr import creates one folder per album and imports videos unpublished",
    "143013": "Imported video over 10 minutes is flagged, requiring External URL before publish",
    "143014": "An individual video import failure is logged and the run continues",
    "143015": "Re-running import applies the configured duplicate-handling rule",
    "143016": "Administrator can view the import log per run",
}


@pytest.mark.parametrize("tc_id", [pytest.param(tc, marks=getattr(pytest.mark, f"tc_{tc}"), id=f"tc_{tc}")
                                   for tc in _BLOCKED])
@allure.epic(EPIC)
@allure.feature(FEATURE)
@allure.story("Flickr import (blocked)")
@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_high
@pytest.mark.pbi_130715
@VA_GROUP
def test_flickr_import_blocked(tc_id):
    allure.dynamic.title(f"[BLOCKED] {_BLOCKED[tc_id]}")
    pytest.skip(f"TC {tc_id}: {FLICKR_BLOCK_REASON}")
