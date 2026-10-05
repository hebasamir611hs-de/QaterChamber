"""
cms/tests/photo_gallery/test_photo_gallery_workflow_control_panel.py —
Control_Panel UI / auth / workflow / publish-lifecycle cases for PBI 130714
("QC - Insights & Media - 006 - Photo Gallery"), Azure suite 140373 in plan
137724 (Agent PA). Field-validation cases live in Agent PB's
test_photo_gallery_fields_control_panel.py.

Surfaces (Object Authoring, read live 2026-10-05):
  - manage-photo-album     (Photo Album)                 — PhotoAlbumAdminPage
  - manage-event-category  (Photo Gallery Event Category) — EventCategoryAdminPage
  - public listing /web/qatar-chamber/photo-gallery and detail
    /web/qatar-chamber/photo-album-details?erc=<code>   — PhotoGalleryPublicView

Pattern (Tenders PBI 130952, commit 1c88750):
  - Every case runs as the account it names — Site Content Editor (156488) or
    Site Content Author (156492) — in an auth-free context; the signed-in
    userId is re-checked before each save. Cases naming no role run as the
    Editor. Teardown also signs in as the Editor (no TEST_USER).
  - The Editor's form button reads "Publish" ("Saved and published."), the
    Author's "Submit for Review" ("Saved and submitted for review.").
    Unpublish is the row action (confirm() then UNPUBLISHED). "Audit log" maps
    onto the row's History trail.
  - Records are disposable `QCTEST-130714-PA-<tc>-<stamp> …` albums and
    categories; identity (title + entry id + code) is captured right after the
    save by diffing the list ids and reading the new record back; teardown
    deletes only that captured record through the guarded delete. Delete now
    moves a record to the object's Recycle Bin (Restore only — no purge for
    the Editor), so deleted QCTEST rows stay listed there.
  - Public visibility = workflow PUBLISHED + Active Status ticked: every public
    assertion first re-opens the record and checks the STORED Active Status,
    then reads a fresh logged-out context with Load More expanded.

How photos reach an album (live): NO Photos panel / Add Photo / per-photo
record exists. An album's photos are one Documents & Media folder selected
indirectly through "Flickr Source Folder" (a manage-flickr-album record) or
"Uploaded Photos Album" (a manage-uploaded-album record, none exist). The
disposable albums here therefore point at the REAL Flickr Album record
"First_Test_Album_QChamber" (folder 52245, 5 photos) as their photo source —
a reference only; that record is never edited. Cases whose subject is the
missing per-photo layer (Photos panel, Add Photo, per-photo publish status /
display order) fail on that absence and are reported as one bug candidate.

Substitutions disclosed:
  - Case data "Community Outreach", Display Order 4 -> a QCTEST category named
    "...Community Outreach", Display Order 100 (100-grid rule).
  - 143163 "one photo added but left Unpublished" -> an album with NO photo
    source (zero photos): per-photo status does not exist.
  - 143178 "Institutional" (real) -> a QCTEST category linked to a QCTEST
    published album (never delete-attempt a real category).

NOT SCRIPTED: 143146, 143177, 143186 (Manual). Blocked (skipped here, with the
reason): 143123 (no Administrator role account; no Flickr import UI exists),
143125 (no Flickr integration settings URL exists to attempt).
"""

from __future__ import annotations

import os
import re
from datetime import datetime
from time import monotonic

import allure
import pytest

from cms.pages.components.object_authoring_page import (
    STATUS_DRAFT,
    STATUS_PENDING_REVIEW,
    STATUS_PUBLISHED,
    STATUS_UNPUBLISHED,
)
from cms.pages.photo_gallery.event_category_admin_page import (
    K_CATEGORY_NAME,
    K_DISPLAY_ORDER,
    LABEL_ACTIVE_STATUS,
    LABEL_CATEGORY_NAME,
    LABEL_CATEGORY_NAME_AR,
    LABEL_DISPLAY_ORDER,
    EventCategoryAdminPage,
)
from cms.pages.photo_gallery.gallery_admin_base import (
    MSG_DRAFT_SAVED,
    MSG_SAVED_AND_PUBLISHED,
    MSG_SUBMITTED_FOR_REVIEW,
    ROLE_AUTHOR,
    ROLE_EDITOR,
    ROLE_USER_IDS,
    GalleryEntry,
)
from cms.pages.photo_gallery.photo_album_admin_page import (
    K_ALBUM_TITLE,
    K_PHOTO_COUNT,
    LABEL_ALBUM_TITLE,
    LABEL_ALBUM_TITLE_AR,
    LABEL_COVER_IMAGE,
    LABEL_EVENT_CATEGORY,
    LABEL_PUBLISHED_DATE,
    PhotoAlbumAdminPage,
)
from cms.pages.photo_gallery.photo_gallery_public_view import PhotoAlbumDetailView, PhotoGalleryPublicView
from config.settings import PROJECT_ROOT
from core.utils.waits import WaitTimeoutError, wait_until
from core.web.browser import new_context

AUTH_FREE_PAGE = pytest.mark.parametrize("page", [{"auth": False}], indirect=True)
GALLERY_PA_GROUP = pytest.mark.xdist_group("photo_gallery_cms_pa")
PA_PREFIX = "QCTEST-130714-PA-"
STAMP = datetime.now().strftime("%m%d%H%M%S")
EVIDENCE_DIR = os.path.join(str(PROJECT_ROOT), "reports", "evidence", "130714_PA")
FIXTURES = os.path.join(os.path.dirname(__file__), "fixtures")
COVER_JPG = os.path.join(FIXTURES, "pa_qctest_cover.jpg")

# The real Flickr Album record used as a READ-ONLY photo source (folder 52245).
PHOTO_SOURCE = "First_Test_Album_QChamber"
PHOTO_SOURCE_COUNT = 5
REAL_CATEGORY = "Institutional"

PUBLIC_REFLECT_TIMEOUT = 30.0
PUBLIC_POLL = 1.0

EPIC = "Insights & Media"
FEATURE = "Photo Gallery — Control Panel (workflow)"


def _title(tc_id: str, suffix: str) -> str:
    return f"{PA_PREFIX}{tc_id}-{STAMP} {suffix}"


def _album_data(title: str, **overrides) -> dict:
    data = {"title": title, "title_ar": f"ألبوم اختبار آلي {title[-10:]}", "published_date": "15/09/2026",
            "category": REAL_CATEGORY, "flickr_source": PHOTO_SOURCE}
    data.update(overrides)
    return data


def _category_data(name: str, **overrides) -> dict:
    data = {"name": name, "name_ar": "فئة اختبار آلي", "display_order": 100}
    data.update(overrides)
    return data


# ===========================================================================
# Fixtures
# ===========================================================================
class DisposableRegistry:
    """Records this test created (captured identity). Only these are deleted."""

    def __init__(self):
        self._entries: dict[tuple[str, str], GalleryEntry] = {}

    @property
    def entries(self) -> list[GalleryEntry]:
        # albums first: an album references its category
        return sorted(self._entries.values(), key=lambda e: 0 if e.slug == "photo-album" else 1)

    def track(self, entry: GalleryEntry) -> GalleryEntry:
        if not entry.in_namespace() or not entry.title.startswith(PA_PREFIX):
            raise ValueError(f"{entry} is not a {PA_PREFIX} record")
        self._entries[(entry.slug, entry.entry_id)] = entry
        return entry

    def forget(self, entry: GalleryEntry) -> None:
        self._entries.pop((entry.slug, entry.entry_id), None)


@pytest.fixture
def disposable(browser):
    """Deletes ONLY the records the test registered at creation, through the
    guarded single-record delete, signed in as the Site Content Editor.
    Anything it cannot remove fails the teardown."""
    registry = DisposableRegistry()
    yield registry
    if not registry.entries:
        return
    ctx = new_context(browser, use_auth_state=False)
    outcome, failures = [], []
    try:
        page = ctx.new_page()
        albums = PhotoAlbumAdminPage(page, PA_PREFIX, EVIDENCE_DIR)
        if albums.login_as_role(ROLE_EDITOR) != "ok":
            raise AssertionError("teardown could not sign in as the Site Content Editor")
        categories = EventCategoryAdminPage(page, PA_PREFIX, EVIDENCE_DIR)
        categories.pinned_role = albums.pinned_role
        for entry in registry.entries:
            cleaner = albums if entry.slug == albums.slug else categories
            label = f"{entry.slug} {entry.title} (id {entry.entry_id}, code {entry.code})"
            try:
                cleaner.open_list_all()
                if not cleaner.row_present(entry):
                    if cleaner.is_list_fully_expanded():
                        outcome.append(f"already gone: {label}")
                    else:
                        failures.append(f"{label}: not found and the list is NOT fully expanded")
                    continue
                cleaner.adopt(entry)
                if cleaner.delete_own_entry(entry):
                    outcome.append(f"removed (to Recycle Bin) {label}")
                elif any("does not allow deletes" in m for m in cleaner.last_delete_messages):
                    # A trashed child album still references this category
                    # (Recycle Bin is never purged): take it off the site and
                    # report the id instead (QA Manager instruction).
                    cleaner.open_list_all()
                    if "unpublish" in cleaner.row_actions(entry):
                        cleaner.run_row_action(entry, "unpublish")
                    cleaner.open_list_all()
                    outcome.append(f"LEFT (delete blocked by a trashed child: {cleaner.last_delete_messages}); "
                                   f"now {cleaner.row_status(entry)}: {label}")
                else:
                    failures.append(f"NOT removed {label}: guarded delete refused/failed "
                                    f"(dialogs {cleaner.last_delete_dialogs}, messages {cleaner.last_delete_messages})")
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
    """Fresh logged-out contexts for every public read (standards.md)."""
    contexts, make = _contexts(browser)
    yield make
    for ctx in contexts:
        try:
            ctx.close()
        except Exception:  # noqa: BLE001
            pass


@pytest.fixture
def role_pages(browser):
    """Extra auth-free pages for a second account in the same test."""
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
def _login(page, role: str) -> tuple[PhotoAlbumAdminPage, EventCategoryAdminPage]:
    """Signs in as `role` in this auth-free context; skips (never falls back)
    when the account cannot sign in or is not the pinned one."""
    albums = PhotoAlbumAdminPage(page, PA_PREFIX, EVIDENCE_DIR)
    outcome = albums.login_as_role(role)
    if outcome == "auth_failed":
        pytest.skip(f"PRECONDITION: Liferay refused the .env credentials for '{role}'")
    albums.open_list_all()
    if outcome != "ok" and not albums.signed_in_user()[0]:
        pytest.fail(f"login as '{role}' neither succeeded nor showed Liferay's refusal banner")
    user_id, _ = albums.signed_in_user()
    if user_id != ROLE_USER_IDS[role]:
        pytest.skip(f"PRECONDITION: '{role}' credentials sign in as userId {user_id!r}, "
                    f"not the pinned {ROLE_USER_IDS[role]}")
    albums.pinned_role = role
    categories = EventCategoryAdminPage(page, PA_PREFIX, EVIDENCE_DIR)
    categories.pinned_role = role
    return albums, categories


def _pinned(admin, role: str) -> None:
    user_id, _ = admin.signed_in_user()
    assert user_id == ROLE_USER_IDS[role], (
        f"the session is now userId {user_id!r}, not the pinned {role} ({ROLE_USER_IDS[role]}) — "
        f"nothing from here on is attributable to {role}")


def _register(admin, disposable, title: str, ids_before: set) -> GalleryEntry | None:
    """Registers for teardown the ONE new record titled `title`. Never raises."""
    try:
        entry = admin.identify_created(title, ids_before)
        return disposable.track(entry) if entry else None
    except Exception as exc:  # noqa: BLE001
        allure.attach(repr(exc), name=f"registration of {title!r} failed")
        return None


def _create(admin, disposable, title: str, fill, publish: bool, role: str = ROLE_EDITOR) -> GalleryEntry:
    """Creates one record (publish=True -> the role's submit button, else Save as
    Draft), registers whatever got created for teardown, THEN asserts.
    `admin.create_banners` holds the edit-bar messages shown after the save."""
    ids_before = admin.snapshot_ids()
    went_through, diagnostics, banners, arabic = False, {}, [], ""
    expected = (MSG_DRAFT_SAVED if not publish
                else MSG_SUBMITTED_FOR_REVIEW if role == ROLE_AUTHOR else MSG_SAVED_AND_PUBLISHED)
    try:
        admin.open_create_form_en()
        fill()
        _pinned(admin, role)
        admin.click_publish() if publish else admin.click_save_as_draft()
        went_through = admin.save_went_through()
        diagnostics = admin.refusal_evidence()
        if went_through:
            banners = admin.success_messages(expected, timeout=15.0)
            arabic = admin.wait_arabic_saved()
            admin.evidence(f"{title} after {'submit' if publish else 'draft'}")
        else:
            admin.evidence(f"{title} save refused")
    finally:
        entry = _register(admin, disposable, title, ids_before)
    admin.create_banners = banners
    allure.attach("\n".join(banners) or "(none)", name=f"edit-bar after creating {title}")
    allure.attach(arabic or "(no Arabic-save message within 25 s)", name="Arabic content save")
    assert went_through, f"creating {title!r} as {role} did not go through: {diagnostics}"
    assert entry is not None, f"{title!r} went through but is not identifiable as exactly one NEW record"
    return entry


def _create_album(albums, disposable, title: str, publish: bool, role: str = ROLE_EDITOR, **overrides):
    data = _album_data(title, **overrides)
    return _create(albums, disposable, title, lambda: albums.fill_album(data), publish, role)


def _create_category(categories, disposable, name: str, publish: bool, role: str = ROLE_EDITOR, **overrides):
    data = _category_data(name, **overrides)
    return _create(categories, disposable, name, lambda: categories.fill_category(data), publish, role)


def _has(banners: list[str], expected: str) -> bool:
    return any(expected in b for b in banners)


def _history(admin, entry: GalleryEntry) -> list[dict]:
    trail = admin.history(entry)
    allure.attach("\n".join(repr(h) for h in trail) or admin.history_cell_text(entry) or "(empty)",
                  name=f"History of {entry.title}")
    return trail


def _require_active_status(admin, entry: GalleryEntry) -> None:
    """User rule: Active Status must be STORED as ticked before ANY public check."""
    admin.open_entry_en(entry.code)
    stored = admin.active_status_stored()
    allure.attach(f"stored Active Status: {stored!r}", name="public-visibility precondition")
    if stored != "true":
        pytest.fail(f"PRECONDITION NOT MET — PRODUCT: {entry.title!r} stores Active Status {stored!r}, "
                    f"not 'true'; the public-page step was not run")


def _public_until(anon_pages, predicate, message: str, locale: str = "en") -> tuple[PhotoGalleryPublicView, float]:
    view = PhotoGalleryPublicView(anon_pages(), EVIDENCE_DIR)
    started = monotonic()

    def _check() -> bool:
        view.open_listing_all(locale)
        return bool(predicate(view))

    try:
        wait_until(_check, timeout=PUBLIC_REFLECT_TIMEOUT, poll=PUBLIC_POLL, message=message)
    except WaitTimeoutError:
        view.evidence(f"public listing at timeout {message[:60]}")
        pytest.fail(f"{message} within {PUBLIC_REFLECT_TIMEOUT:.0f}s (cards: {[c['title'] for c in view.cards()]})")
    latency = monotonic() - started
    allure.attach(f"{latency:.1f}s", name="observed public-listing latency")
    return view, latency


def _visible_publicly(anon_pages, entry: GalleryEntry) -> tuple[PhotoGalleryPublicView, dict]:
    view, _ = _public_until(anon_pages, lambda v: bool(v.card_for(entry.code)),
                            f"DELIVERY: {entry.title!r} never appeared on the logged-out Photo Albums listing")
    return view, view.card_for(entry.code)


def _assert_not_public(anon_pages, entry: GalleryEntry) -> PhotoGalleryPublicView:
    """Absence that cannot pass vacuously: real cards must render first."""
    _public_until(anon_pages, lambda v: not v.card_for(entry.code) and len(v.cards()) > 0,
                  f"{entry.title!r} was still on the logged-out Photo Albums listing")
    view = PhotoGalleryPublicView(anon_pages(), EVIDENCE_DIR).open_listing_all()
    cards = view.cards()
    assert cards, f"cannot prove {entry.title!r} is absent: the logged-out listing shows no album cards"
    assert not view.card_for(entry.code), f"{entry.title!r} is on the logged-out Photo Albums listing"
    assert entry.title not in [c["title"] for c in cards], f"a card titled {entry.title!r} is on the listing"
    return view


def _per_photo_controls(albums: PhotoAlbumAdminPage) -> dict:
    found = albums.photos_panel_present()
    allure.attach(repr(found), name="photo controls the album form offers")
    return found


MISSING_PHOTO_LAYER = (
    "PRODUCT (case/PBI vs app): manage-photo-album has no Photos panel, no 'Add Photo' control and no "
    "per-photo record (Photo Title / Thumbnail Framing / Display Order / Publish Status). Photos come only from "
    "a Documents & Media folder chosen through 'Flickr Source Folder' or 'Uploaded Photos Album'. Form: {form}")


# ===========================================================================
# 143110 — UI: Event Category creation form
# ===========================================================================
@AUTH_FREE_PAGE
@allure.epic(EPIC)
@allure.feature(FEATURE)
@allure.story("Event Category form")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("The admin Event Category creation form renders Name, Display Order and Publish Status fields")
@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.ui
@pytest.mark.pbi_130714
@pytest.mark.tc_143110
@GALLERY_PA_GROUP
def test_event_category_form_renders_fields(page):
    # Azure TC 143110 | PBI 130714 | account: Site Content Editor (156488)
    _, categories = _login(page, ROLE_EDITOR)
    categories.open_create_form_en()
    labels = categories.form_labels()
    buttons = categories.form_buttons()
    categories.evidence("143110 event category create form")
    allure.attach(f"labels {labels}\nbuttons {buttons}", name="Event Category create form")
    for expected in (LABEL_CATEGORY_NAME, LABEL_CATEGORY_NAME_AR, LABEL_DISPLAY_ORDER):
        assert any(lbl.startswith(expected) for lbl in labels), f"no {expected!r} field on the form: {labels}"
    assert categories.has_field(K_CATEGORY_NAME) and categories.has_field(K_DISPLAY_ORDER)
    # "Publish Status": the form's publish-state controls are the Active Status
    # checkbox plus the Save as Draft / Publish buttons (no field named
    # "Publish Status" exists) — wording-only difference, reported LOW.
    assert any(lbl.startswith(LABEL_ACTIVE_STATUS) for lbl in labels), f"no Active Status control: {labels}"
    assert "Publish" in buttons and "Save as Draft" in buttons, f"publish-state buttons missing: {buttons}"
    if not any("Publish Status" in lbl for lbl in labels):
        allure.attach(f"labels {labels}", name="LOW finding: no field labelled 'Publish Status' (Active Status + "
                                               "Save as Draft/Publish instead)")


# ===========================================================================
# 143111 — UI: Album creation form
# ===========================================================================
@AUTH_FREE_PAGE
@allure.epic(EPIC)
@allure.feature(FEATURE)
@allure.story("Album form")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("The admin Album creation form renders Title, Event Category, Cover Image, Published Date and Photos")
@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.ui
@pytest.mark.pbi_130714
@pytest.mark.tc_143111
@GALLERY_PA_GROUP
def test_album_form_renders_fields(page):
    # Azure TC 143111 | PBI 130714 | account: Site Content Editor (156488)
    albums, _ = _login(page, ROLE_EDITOR)
    albums.open_create_form_en()
    labels = albums.form_labels()
    albums.evidence("143111 album create form")
    allure.attach(repr(labels), name="Album create form labels")
    missing = [name for name in (LABEL_ALBUM_TITLE, LABEL_ALBUM_TITLE_AR, LABEL_EVENT_CATEGORY, LABEL_COVER_IMAGE,
                                 LABEL_PUBLISHED_DATE) if not any(lbl.startswith(name) for lbl in labels)]
    assert not missing, f"fields missing from the Album create form: {missing} (labels {labels})"
    assert albums.page.get_by_role("button", name="Select File").count() > 0, "no Album Cover Image upload control"
    photos = _per_photo_controls(albums)
    assert photos["photos_panel"], MISSING_PHOTO_LAYER.format(form=photos["form_text"])


# ===========================================================================
# 143112 — UI: Add Photo offers Documents & Media and device upload
# ===========================================================================
@AUTH_FREE_PAGE
@allure.epic(EPIC)
@allure.feature(FEATURE)
@allure.story("Photos panel")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("The admin photo-add panel offers selecting from Documents & Media and uploading from device")
@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.ui
@pytest.mark.pbi_130714
@pytest.mark.tc_143112
@GALLERY_PA_GROUP
def test_add_photo_offers_library_and_device(page):
    # Azure TC 143112 | PBI 130714 | account: Site Content Editor (156488).
    # Read-only: a real album's edit form is OPENED (never saved) so "existing
    # photos, if any" could be listed.
    albums, _ = _login(page, ROLE_EDITOR)
    albums.open_entry_en("QCDEMO-130714-PHOTO_ALBUM-first-test-album")
    photos = _per_photo_controls(albums)
    albums.evidence("143112 album edit form has no photos panel")
    assert photos["photos_panel"] and photos["add_photo"], MISSING_PHOTO_LAYER.format(form=photos["form_text"])


# ===========================================================================
# 143115 — UI / Bilingual: Arabic title entry
# ===========================================================================
@AUTH_FREE_PAGE
@allure.epic(EPIC)
@allure.feature(FEATURE)
@allure.story("Bilingual entry")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("The CMS Album creation form renders correctly for bilingual field entry in Arabic")
@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.ui
@pytest.mark.bilingual
@pytest.mark.pbi_130714
@pytest.mark.tc_143115
@GALLERY_PA_GROUP
def test_album_form_arabic_title_entry(page):
    # Azure TC 143115 | PBI 130714 | account: Site Content Editor (156488).
    # Nothing is saved: the case is about rendering the entry.
    albums, _ = _login(page, ROLE_EDITOR)
    albums.open_create_form_en()
    title_en = _title("143115", "Bilingual Album")
    title_ar = "ألبوم يوم المجتمع ٢٠٢٦ — اختبار"
    albums.fill_en(K_ALBUM_TITLE, title_en)
    albums.fill_ar(K_ALBUM_TITLE, title_ar)
    ar_dir = albums.text_direction(K_ALBUM_TITLE, arabic=True)
    en_dir = albums.text_direction(K_ALBUM_TITLE)
    albums.evidence("143115 arabic title entry")
    allure.attach(f"AR box {ar_dir}\nEN box {en_dir}", name="text direction")
    assert albums.ar_value(K_ALBUM_TITLE) == title_ar, f"the Arabic box holds {albums.ar_value(K_ALBUM_TITLE)!r}"
    assert albums.text_value(K_ALBUM_TITLE) == title_en, (
        f"typing Arabic changed the English title: {albums.text_value(K_ALBUM_TITLE)!r}")
    assert ar_dir["direction"] == "rtl", f"the Arabic title box renders {ar_dir}, not right-to-left"
    assert en_dir["direction"] == "ltr", f"the English title box renders {en_dir}, not left-to-right"


# ===========================================================================
# 143116 — UI: per-photo Publish Status in the Photos panel
# ===========================================================================
@AUTH_FREE_PAGE
@allure.epic(EPIC)
@allure.feature(FEATURE)
@allure.story("Photos panel")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Each photo row in the admin Photos panel displays its current Publish Status accurately")
@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.ui
@pytest.mark.pbi_130714
@pytest.mark.tc_143116
@GALLERY_PA_GROUP
def test_photo_rows_show_publish_status(page):
    # Azure TC 143116 | PBI 130714 | account: Site Content Editor (156488). Read-only.
    albums, _ = _login(page, ROLE_EDITOR)
    albums.open_entry_en("QCDEMO-130714-PHOTO_ALBUM-first-test-album")
    photos = _per_photo_controls(albums)
    albums.evidence("143116 no per-photo rows")
    assert photos["photos_panel"], MISSING_PHOTO_LAYER.format(form=photos["form_text"])


# ===========================================================================
# 143123 / 143125 — Flickr integration (Blocked)
# ===========================================================================
@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.auth
@pytest.mark.pbi_130714
@pytest.mark.tc_143123
@GALLERY_PA_GROUP
def test_admin_triggers_flickr_manual_import():
    # Azure TC 143123 | PBI 130714
    pytest.skip("BLOCKED: the project defines no Administrator role account (config.settings has none) and no "
                "Flickr integration settings / manual-import screen exists on qcdev (System + Instance Settings "
                "search 'flickr': 0 results; Object Authoring offers only the Flickr Album / Flickr Video records). "
                "A manual import would also pull/overwrite shared Documents & Media data.")


@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.auth
@pytest.mark.pbi_130714
@pytest.mark.tc_143125
@GALLERY_PA_GROUP
def test_editor_denied_flickr_settings():
    # Azure TC 143125 | PBI 130714
    pytest.skip("BLOCKED: there is no Flickr integration settings URL to attempt — none exists in System Settings, "
                "Instance Settings or Object Authoring. Needs the settings URL (or confirmation the feature is "
                "not built).")


# ===========================================================================
# 143124 — Auth: Editor full album lifecycle
# ===========================================================================
@AUTH_FREE_PAGE
@allure.epic(EPIC)
@allure.feature(FEATURE)
@allure.story("Auth / RBAC")
@allure.severity(allure.severity_level.BLOCKER)
@allure.title("A Site Content Editor can perform the full album lifecycle")
@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.auth
@pytest.mark.regression
@pytest.mark.pbi_130714
@pytest.mark.tc_143124
@GALLERY_PA_GROUP
def test_editor_full_album_lifecycle(page, disposable, anon_pages):
    # Azure TC 143124 | PBI 130714 | account: Site Content Editor (156488)
    albums, _ = _login(page, ROLE_EDITOR)
    title = _title("143124", "Auth Album")
    failures = []

    # create
    entry = _create_album(albums, disposable, title, publish=False)
    if not _has(albums.create_banners, MSG_DRAFT_SAVED):
        failures.append(f"create: no {MSG_DRAFT_SAVED!r} ({albums.create_banners})")
    albums.open_list_all()
    created_status = albums.row_status(entry)
    if created_status != STATUS_DRAFT:
        failures.append(f"create: 'Save as Draft' said {albums.create_banners} but the album is "
                        f"{created_status!r}, not Draft (History {[h['action'] for h in _history(albums, entry)]})")

    # edit (a published record offers only Publish, which updates it)
    albums.open_entry_en(entry.code)
    new_ar = "ألبوم المحرر بعد التعديل"
    albums.fill_ar(K_ALBUM_TITLE, new_ar)
    albums.set_date("publishedDate", "16/09/2026")
    _pinned(albums, ROLE_EDITOR)
    as_draft = "Save as Draft" in albums.form_buttons()
    albums.click_save_as_draft() if as_draft else albums.click_publish()
    expected_msg = MSG_DRAFT_SAVED if as_draft else MSG_SAVED_AND_PUBLISHED
    edit_banners = albums.success_messages(expected_msg) if albums.save_went_through() else albums.editbar_texts()
    if not albums.save_went_through():
        failures.append(f"edit: save refused: {albums.refusal_evidence()}")
    albums.open_entry_en(entry.code)
    stored = albums.read_album()
    if stored["title_ar"] != new_ar or stored["published_date"] != "16/09/2026":
        failures.append(f"edit did not persist: {stored}")
    allure.attach(f"{edit_banners}\n{stored}", name="edit")

    # preview (row Preview link)
    albums.open_list_all()
    preview_url = albums.row_preview_href(entry)
    preview_text = albums.open_preview(preview_url, [title]) if preview_url else ""
    albums.evidence("143124 row preview")
    if title not in preview_text:
        failures.append(f"preview: the row Preview ({preview_url}) does not render the album "
                        f"(page text: {' '.join(preview_text.split())[:300]!r})")

    # publish
    albums.open_entry_en(entry.code)
    _pinned(albums, ROLE_EDITOR)
    albums.click_publish()
    pub_banners = albums.success_messages(MSG_SAVED_AND_PUBLISHED) if albums.save_went_through() else []
    albums.open_list_all()
    if albums.row_status(entry) != STATUS_PUBLISHED or not _has(pub_banners, MSG_SAVED_AND_PUBLISHED):
        failures.append(f"publish: status {albums.row_status(entry)!r}, messages {pub_banners or albums.editbar_texts()}")
    else:
        _require_active_status(albums, entry)
        _visible_publicly(anon_pages, entry)

    # unpublish
    albums.open_list_all()
    dialogs = albums.run_row_action(entry, "unpublish") if "unpublish" in albums.row_actions(entry) else []
    albums.open_list_all()
    if albums.row_status(entry) != STATUS_UNPUBLISHED:
        failures.append(f"unpublish: status {albums.row_status(entry)!r} (dialogs {dialogs})")
    else:
        _assert_not_public(anon_pages, entry)

    # delete
    albums.adopt(entry)
    deleted = albums.delete_own_entry(entry)
    allure.attach(f"dialogs {albums.last_delete_dialogs}\nmessages {albums.last_delete_messages}", name="delete")
    if deleted:
        disposable.forget(entry)
    else:
        failures.append(f"delete: refused/failed (dialogs {albums.last_delete_dialogs}, "
                        f"messages {albums.last_delete_messages})")
    permission = [m for m in (albums.last_delete_messages + albums.editbar_texts())
                  if re.search(r"permission|forbidden|access denied", m, re.I)]
    if permission:
        failures.append(f"permission error shown: {permission}")
    assert not failures, "Editor album lifecycle:\n- " + "\n- ".join(failures)


# ===========================================================================
# 143126 — Auth: Author creates, edits and submits for review
# ===========================================================================
@AUTH_FREE_PAGE
@allure.epic(EPIC)
@allure.feature(FEATURE)
@allure.story("Auth / RBAC")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("A Site Content Author can create and edit an album and submit it for review")
@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.auth
@pytest.mark.pbi_130714
@pytest.mark.tc_143126
@GALLERY_PA_GROUP
def test_author_creates_album_and_submits_for_review(page, disposable, anon_pages):
    # Azure TC 143126 | PBI 130714 | account: Site Content Author (156492)
    albums, _ = _login(page, ROLE_AUTHOR)
    title = _title("143126", "Author Album")

    # Step 2 — all mandatory fields, saved as Draft.
    entry = _create_album(albums, disposable, title, publish=False, role=ROLE_AUTHOR)
    albums.open_list_all()
    failures = []
    draft_status = albums.row_status(entry)
    if draft_status != STATUS_DRAFT:
        failures.append(f"step 2: 'Save as Draft' said {albums.create_banners} but the album is {draft_status!r}, "
                        f"not Draft (History {[h['action'] for h in _history(albums, entry)]})")
    assert _has(albums.create_banners, MSG_DRAFT_SAVED), f"no {MSG_DRAFT_SAVED!r}: {albums.create_banners}"
    permission = [m for m in albums.create_banners if re.search(r"permission|forbidden|denied", m, re.I)]
    assert not permission, f"permission error on the Author's save: {permission}"

    # edit (title says "create and edit")
    albums.open_entry_en(entry.code)
    albums.fill_ar(K_ALBUM_TITLE, "ألبوم المؤلف بعد التعديل")
    _pinned(albums, ROLE_AUTHOR)
    albums.click_save_as_draft()
    assert albums.save_went_through(), f"the Author could not edit its own draft: {albums.refusal_evidence()}"

    # Step 3 — Submit for Review -> Pending Review.
    albums.open_entry_en(entry.code)
    label = albums.submit_button_label()
    assert label == "Submit for Review", f"the Author's submit button reads {label!r}"
    _pinned(albums, ROLE_AUTHOR)
    albums.click_publish()
    banners = albums.success_messages(MSG_SUBMITTED_FOR_REVIEW) if albums.save_went_through() else albums.editbar_texts()
    albums.evidence("143126 author submitted for review")
    assert albums.save_went_through(), f"Submit for Review did not go through: {albums.refusal_evidence()}"
    status = albums.wait_status(entry, (STATUS_PENDING_REVIEW,), timeout=60.0)
    assert status == STATUS_PENDING_REVIEW, f"after Submit for Review the album is {status!r}, not Pending Review"
    assert _has(banners, MSG_SUBMITTED_FOR_REVIEW), f"no {MSG_SUBMITTED_FOR_REVIEW!r}: {banners}"
    _assert_not_public(anon_pages, entry)
    assert not failures, "143126:" + chr(10) + "- " + (chr(10) + "- ").join(failures)


# ===========================================================================
# 143127 — Auth: Author cannot publish directly
# ===========================================================================
@AUTH_FREE_PAGE
@allure.epic(EPIC)
@allure.feature(FEATURE)
@allure.story("Auth / RBAC")
@allure.severity(allure.severity_level.BLOCKER)
@allure.title("A Site Content Author cannot publish an album directly")
@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.auth
@pytest.mark.pbi_130714
@pytest.mark.tc_143127
@GALLERY_PA_GROUP
def test_author_cannot_publish_album_directly(page, disposable, anon_pages):
    # Azure TC 143127 | PBI 130714 | account: Site Content Author (156492)
    albums, _ = _login(page, ROLE_AUTHOR)
    title = _title("143127", "Author Draft")
    entry = _create_album(albums, disposable, title, publish=False, role=ROLE_AUTHOR)

    # Step 2 — the own Draft opens.
    albums.open_entry_en(entry.code)
    assert albums.text_value(K_ALBUM_TITLE) == title
    assert "Publish" not in albums.form_buttons(), f"a Publish button is offered to the Author: {albums.form_buttons()}"
    albums.open_list_all()
    before = albums.row_status(entry)
    failures = []
    if before != STATUS_DRAFT:
        failures.append(f"step 2: the Author's own 'Draft' opens as {before!r}, not Draft (Save as Draft "
                        f"said {albums.create_banners})")
    offered = albums.transitions(entry)
    allure.attach(repr(offered), name="transitions the server offers the Author")

    # Step 3 — invoke the Publish transition directly (no UI).
    _pinned(albums, ROLE_AUTHOR)
    response = albums.call_transition_directly(entry, "publish")
    allure.attach(repr(response), name="direct POST /o/qc-object-status/publish/<id> as the Author")
    albums.open_list_all()
    status = albums.row_status(entry)
    albums.evidence("143127 after direct publish attempt")
    assert status == before and status != STATUS_PUBLISHED, (
        f"PRODUCT: the Author's direct Publish call changed the album from {before!r} to {status!r} "
        f"(response {response})")
    assert response["status"] >= 400, f"the direct Publish call was not refused: {response}"
    _assert_not_public(anon_pages, entry)
    assert not failures, "143127:" + chr(10) + "- " + (chr(10) + "- ").join(failures)
    expected = "Access Denied. You do not have permission to perform this action."
    if expected not in response["body"]:
        allure.attach(f"expected {expected!r}\nactual {response}", name="LOW finding: refusal wording differs")


# ===========================================================================
# 143143 — E2E: category + album + photos + publish -> public
# ===========================================================================
@AUTH_FREE_PAGE
@allure.epic(EPIC)
@allure.feature(FEATURE)
@allure.story("Create / Publish")
@allure.severity(allure.severity_level.BLOCKER)
@allure.title("An Editor creates an Event Category and Album, adds photos and publishes; the album shows publicly")
@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_high
@pytest.mark.regression
@pytest.mark.uat
@pytest.mark.workflow
@pytest.mark.pbi_130714
@pytest.mark.tc_143143
@GALLERY_PA_GROUP
def test_editor_creates_category_album_and_publishes(page, disposable, anon_pages):
    # Azure TC 143143 | PBI 130714 | account: Site Content Editor (156488)
    albums, categories = _login(page, ROLE_EDITOR)
    failures = []

    # Step 1 — Event Category, Display Order 100 (100-grid), Published.
    cat_name = _title("143143", "Community Outreach")
    category = _create_category(categories, disposable, cat_name, publish=True, name_ar="التواصل المجتمعي")
    categories.open_list_all()
    if categories.row_status(category) != STATUS_PUBLISHED:
        failures.append(f"step 1: category status {categories.row_status(category)!r}")
    if not category.code or not category.entry_id:
        failures.append(f"step 1: no auto-generated id/code ({category})")
    if not _has(categories.create_banners, MSG_SAVED_AND_PUBLISHED):
        failures.append(f"step 1: no {MSG_SAVED_AND_PUBLISHED!r} ({categories.create_banners})")

    # Step 2 — Album with JPG cover, Published Date 15/09/2026, both titles.
    title = _title("143143", "Community Day 2026")
    title_ar = "يوم المجتمع ٢٠٢٦ اختبار"
    album = _create_album(albums, disposable, title, publish=False, title_ar=title_ar, category=cat_name,
                          cover=COVER_JPG, cover_stem="qctest-130714-pa-cover")
    albums.open_entry_en(album.code)
    stored = albums.read_album()
    allure.attach(repr(stored), name="album as stored")
    expected = {"title": title, "title_ar": title_ar, "published_date": "15/09/2026", "active": "true"}
    mismatched = {k: (stored[k], v) for k, v in expected.items() if stored[k] != v}
    if mismatched:
        failures.append(f"step 2: values not retained (got, want): {mismatched}")
    if not stored["cover_file"].startswith("qctest-130714-pa-cover"):
        failures.append(f"step 2: cover not stored: {stored['cover_file']!r}")
    if not stored["category_id"] or stored["category_id"] != category.entry_id:
        failures.append(f"step 2: album category id {stored['category_id']!r} is not {category.entry_id!r}")
    created = [h for h in _history(albums, album) if h["action"].lower().startswith("created")]
    if not created:
        failures.append("step 2: no 'Created' audit entry in History")

    # Step 3 — per-photo add (D&M + device, titles, framing, display order 1/2).
    photos = _per_photo_controls(albums.open_entry_en(album.code))
    if not (photos["photos_panel"] and photos["add_photo"]):
        failures.append("step 3: " + MISSING_PHOTO_LAYER.format(form=photos["form_text"]) +
                        f" — photos were attached instead through Flickr Source Folder {PHOTO_SOURCE!r}")

    # Step 4 — Draft -> Preview -> Publish (toast + audit entry).
    albums.open_list_all()
    if albums.row_status(album) != STATUS_DRAFT:
        failures.append(f"step 4: album is {albums.row_status(album)!r}, not Draft")
    preview_url = albums.row_preview_href(album)
    preview_text = albums.open_preview(preview_url, [title]) if preview_url else ""
    albums.evidence("143143 draft preview")
    if title not in preview_text:
        failures.append(f"step 4: Preview ({preview_url}) does not render the draft album "
                        f"(page text {' '.join(preview_text.split())[:200]!r})")
    albums.open_entry_en(album.code)
    _pinned(albums, ROLE_EDITOR)
    albums.click_publish()
    banners = albums.success_messages(MSG_SAVED_AND_PUBLISHED) if albums.save_went_through() else albums.editbar_texts()
    albums.open_list_all()
    status = albums.row_status(album)
    if status != STATUS_PUBLISHED or not _has(banners, MSG_SAVED_AND_PUBLISHED):
        failures.append(f"step 4: publish -> status {status!r}, messages {banners}")
    trail = _history(albums, album)
    if not any(re.search(r"publish", h["action"], re.I) for h in trail):
        failures.append(f"step 4: no Publish audit entry in History ({[h['action'] for h in trail]})")

    # Step 5 — public listing under the category chip, cover, photo count; detail.
    if status == STATUS_PUBLISHED:
        _require_active_status(albums, album)
        view, card = _visible_publicly(anon_pages, album)
        view.evidence("143143 public listing")
        allure.attach(repr(card), name="public card")
        if card.get("chip") != cat_name:
            failures.append(f"step 5: card chip {card.get('chip')!r}, not {cat_name!r}")
        if not card.get("cover_loaded"):
            failures.append(f"step 5: cover image did not load ({card.get('cover_src')!r})")
        if card.get("badge") != f"{PHOTO_SOURCE_COUNT} photos":
            failures.append(f"step 5: badge {card.get('badge')!r}, not '{PHOTO_SOURCE_COUNT} photos'")
        if cat_name not in view.filter_category_options():
            failures.append(f"step 5: {cat_name!r} not in the 'All Events' filter ({view.filter_category_options()})")
        detail = PhotoAlbumDetailView(anon_pages(), EVIDENCE_DIR)
        info = detail.open_code(album.code)
        detail.evidence("143143 public detail")
        allure.attach(repr({k: info[k] for k in ("status", "title", "chip", "meta", "boxes")}), name="public detail")
        if info["title"] != title or not info["boxes"] or not info["boxes"][0]["lead"]:
            failures.append(f"step 5: detail shows {info['title']!r} with {len(info['boxes'])} photos")
    assert not failures, "143143:\n- " + "\n- ".join(failures)


# ===========================================================================
# 143144 — Unpublish removes the album from the public site
# ===========================================================================
@AUTH_FREE_PAGE
@allure.epic(EPIC)
@allure.feature(FEATURE)
@allure.story("Unpublish")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("Unpublishing an album removes it from the public listing and details page")
@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_high
@pytest.mark.regression
@pytest.mark.pbi_130714
@pytest.mark.tc_143144
@GALLERY_PA_GROUP
def test_unpublish_removes_album_from_public(page, disposable, anon_pages):
    # Azure TC 143144 | PBI 130714 | account: Site Content Editor (156488)
    albums, _ = _login(page, ROLE_EDITOR)
    title = _title("143144", "Community Day 2026")
    entry = _create_album(albums, disposable, title, publish=True)

    # Step 1 — visible on the public listing.
    _require_active_status(albums, entry)
    _visible_publicly(anon_pages, entry)

    # Step 2 — unpublish: Unpublished + message + audit entry.
    albums.open_list_all()
    dialogs = albums.run_row_action(entry, "unpublish")
    messages = albums.editbar_texts()
    albums.open_list_all()
    status = albums.row_status(entry)
    trail = _history(albums, entry)
    albums.evidence("143144 after unpublish")
    allure.attach(f"dialogs {dialogs}\nmessages after the action {messages}", name="unpublish")
    assert status == STATUS_UNPUBLISHED, f"after Unpublish the album is {status!r}"
    assert any(h["action"].lower().startswith("unpublish") for h in trail), (
        f"no Unpublished audit entry in History: {[h['action'] for h in trail]}")

    # Step 3 — gone from a fresh logged-out listing (and the detail URL).
    view = _assert_not_public(anon_pages, entry)
    view.evidence("143144 public listing after unpublish")
    detail = PhotoAlbumDetailView(anon_pages(), EVIDENCE_DIR).open_code(entry.code)
    assert not detail["found"] and not detail["boxes"], f"the unpublished album's detail still renders: {detail['title']!r}"
    success = [m for m in messages if re.search(r"unpublish", m, re.I)]
    if not success:
        allure.attach(f"{messages}", name="LOW finding: no success message after Unpublish (confirm() only)")


# ===========================================================================
# 143145 — Delete removes the album from the public site
# ===========================================================================
@AUTH_FREE_PAGE
@allure.epic(EPIC)
@allure.feature(FEATURE)
@allure.story("Delete")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("Deleting an album removes it from the public site")
@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_high
@pytest.mark.pbi_130714
@pytest.mark.tc_143145
@GALLERY_PA_GROUP
def test_delete_removes_album_from_public(page, disposable, anon_pages):
    # Azure TC 143145 | PBI 130714 | account: Site Content Editor (156488)
    albums, _ = _login(page, ROLE_EDITOR)
    title = _title("143145", "Community Day 2026")
    entry = _create_album(albums, disposable, title, publish=True)
    _require_active_status(albums, entry)
    _visible_publicly(anon_pages, entry)
    PhotoAlbumDetailView(anon_pages(), EVIDENCE_DIR).open_code(entry.code)  # known Details URL works

    # Step 1 — delete -> gone from the CMS list; trace kept (Recycle Bin).
    albums.adopt(entry)
    deleted = albums.delete_own_entry(entry)
    allure.attach(f"dialogs {albums.last_delete_dialogs}\nmessages {albums.last_delete_messages}", name="delete")
    assert deleted, f"the guarded delete did not remove {title!r}: {albums.last_delete_dialogs}"
    disposable.forget(entry)
    albums.open_list_all()
    binned = [line for line in albums.recycle_bin_items() if title in line]
    albums.evidence("143145 list after delete")
    allure.attach(repr(binned), name="Recycle Bin trace of the deleted album")
    assert binned, f"no trace of the deleted album in the list's Recycle Bin: {albums.recycle_bin_items()}"

    # Step 2 — gone from a fresh logged-out listing.
    _assert_not_public(anon_pages, entry)

    # Step 3 — the old Details URL shows a not-found state, not stale content.
    detail = PhotoAlbumDetailView(anon_pages(), EVIDENCE_DIR)
    info = detail.open_code(entry.code)
    detail.evidence("143145 deleted album details url")
    allure.attach(repr({k: info[k] for k in ("status", "title", "empty_text")}), name="deleted album Details URL")
    assert not info["found"] and not info["boxes"], f"stale album content at the deleted Details URL: {info['title']!r}"
    assert info["empty_text"], f"no not-found state at the deleted Details URL: {info['body'][:300]!r}"
    if info["status"] != 404:
        allure.attach(f"HTTP {info['status']} with in-page {info['empty_text']!r}",
                      name="LOW finding: soft not-found (HTTP 200) instead of a standard not-found page")


# ===========================================================================
# 143163 — Album with zero published photos cannot be published
# ===========================================================================
@AUTH_FREE_PAGE
@allure.epic(EPIC)
@allure.feature(FEATURE)
@allure.story("Publish rules")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("An album with zero published photos is blocked from publishing")
@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_low
@pytest.mark.pbi_130714
@pytest.mark.tc_143163
@GALLERY_PA_GROUP
def test_album_without_published_photos_cannot_publish(page, disposable, anon_pages):
    # Azure TC 143163 | PBI 130714 | account: Site Content Editor (156488).
    # Substitution: no per-photo status exists, so "zero published photos" =
    # an album with NO photo source (every one of the 136 Flickr Album records
    # holds >= 1 photo; no Uploaded Photos Album exists).
    albums, _ = _login(page, ROLE_EDITOR)
    title = _title("143163", "Zero Photos")
    ids_before = albums.snapshot_ids()
    data = _album_data(title, flickr_source=None)

    # Step 1 — mandatory fields, no photos, Save as Draft.
    albums.open_create_form_en()
    albums.fill_album(data)
    _pinned(albums, ROLE_EDITOR)
    albums.click_save_as_draft()
    draft_saved = albums.save_went_through()
    draft_messages = albums.all_messages_text()
    albums.evidence("143163 save as draft with zero photos")

    # Step 2 — attempt to publish.
    publish_messages, published = "", False
    if not draft_saved:
        albums.click_publish()
        published = albums.save_went_through()
        publish_messages = albums.all_messages_text()
        albums.evidence("143163 publish attempt with zero photos")
    entry = _register(albums, disposable, title, ids_before)
    status = ""
    if entry:
        albums.open_list_all()
        status = albums.row_status(entry)
    allure.attach(repr({"draft_saved": draft_saved, "draft_messages": draft_messages, "published": published,
                        "publish_messages": publish_messages, "record": entry, "status": status}),
                  name="zero-photo album")
    expected = "An album must contain at least one published photo."
    assert status != STATUS_PUBLISHED and not published, (
        f"PRODUCT: an album with zero photos was published (status {status!r}); messages {publish_messages!r}")
    assert draft_saved, (
        f"step 1 not reachable: an album with zero photos cannot even be saved as Draft — refused with "
        f"{draft_messages!r}; Publish refused with {publish_messages!r} (expected {expected!r} at publish time)")
    assert expected in publish_messages, f"publish refused with {publish_messages!r}, not {expected!r}"


# ===========================================================================
# 143170 — Lowest Display Order photo is the lead photo
# ===========================================================================
@AUTH_FREE_PAGE
@allure.epic(EPIC)
@allure.feature(FEATURE)
@allure.story("Photo ordering")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("The photo with the lowest Display Order value renders as the full-width lead photo")
@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_low
@pytest.mark.pbi_130714
@pytest.mark.tc_143170
@GALLERY_PA_GROUP
def test_lowest_display_order_photo_is_lead(page):
    # Azure TC 143170 | PBI 130714 | account: Site Content Editor (156488). Read-only.
    albums, _ = _login(page, ROLE_EDITOR)
    albums.open_entry_en("QCDEMO-130714-PHOTO_ALBUM-first-test-album")
    photos = _per_photo_controls(albums)
    albums.evidence("143170 no per-photo display order")
    assert photos["photos_panel"], (
        "step 1 cannot be performed — " + MISSING_PHOTO_LAYER.format(form=photos["form_text"]))


# ===========================================================================
# 143176 — Photo count decreases when a photo is unpublished
# ===========================================================================
@AUTH_FREE_PAGE
@allure.epic(EPIC)
@allure.feature(FEATURE)
@allure.story("Photo count")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("The photo count automatically decreases when a published photo is unpublished")
@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_low
@pytest.mark.pbi_130714
@pytest.mark.tc_143176
@GALLERY_PA_GROUP
def test_photo_count_follows_unpublished_photo(page, disposable):
    # Azure TC 143176 | PBI 130714 | account: Site Content Editor (156488).
    albums, _ = _login(page, ROLE_EDITOR)
    title = _title("143176", "Photo Count")
    # A hand-typed count of 2 shows whether Photo Count is derived (folder has 5).
    entry = _create_album(albums, disposable, title, publish=False, photo_count=2)
    albums.open_entry_en(entry.code)
    stored = albums.text_value(K_PHOTO_COUNT)
    allure.attach(f"typed 2, stored {stored!r} (source folder holds {PHOTO_SOURCE_COUNT})",
                  name="Photo Count is derived from the source folder")
    photos = _per_photo_controls(albums)
    albums.evidence("143176 album form no per-photo unpublish")
    assert photos["photos_panel"], (
        "step 2 'unpublish one photo' cannot be performed — " + MISSING_PHOTO_LAYER.format(form=photos["form_text"]))


# ===========================================================================
# 143178 — Deleting an in-use Event Category is blocked
# ===========================================================================
@AUTH_FREE_PAGE
@allure.epic(EPIC)
@allure.feature(FEATURE)
@allure.story("Event Category integrity")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Deleting an Event Category linked to published albums is blocked until they are reassigned")
@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_low
@pytest.mark.pbi_130714
@pytest.mark.tc_143178
@GALLERY_PA_GROUP
def test_delete_category_in_use_is_blocked(page, disposable, anon_pages):
    # Azure TC 143178 | PBI 130714 | account: Site Content Editor (156488).
    # Substitution: a QCTEST category stands in for the real "Institutional".
    albums, categories = _login(page, ROLE_EDITOR)
    cat_name = _title("143178", "Institutional")
    category = _create_category(categories, disposable, cat_name, publish=True)
    album = _create_album(albums, disposable, _title("143178", "Linked Album"), publish=True, category=cat_name)
    _require_active_status(albums, album)
    view, card = _visible_publicly(anon_pages, album)
    assert cat_name in view.filter_category_options(), (
        f"precondition: {cat_name!r} is not in the public 'All Events' filter: {view.filter_category_options()}")

    # Step 1 — attempt to delete the category while a published album uses it.
    categories.adopt(category)
    deleted = categories.delete_own_entry(category)
    dialogs, messages = categories.last_delete_dialogs, categories.last_delete_messages
    categories.evidence("143178 delete in-use category attempt")
    allure.attach(f"deleted {deleted}\ndialogs {dialogs}\nmessages {messages}", name="delete attempt")
    if deleted:
        disposable.forget(category)
    categories.open_list_all()
    still_listed = categories.row_present(category)
    public = PhotoGalleryPublicView(anon_pages(), EVIDENCE_DIR).open_listing_all()
    options = public.filter_category_options()
    public.evidence("143178 public filter after delete attempt")
    allure.attach(f"in CMS list: {still_listed}\npublic filter: {options}\nalbum card: {public.card_for(album.code)}",
                  name="after the delete attempt")
    assert still_listed and not deleted, (
        f"PRODUCT: an Event Category used by a published album was deleted with no in-use block "
        f"(confirm {dialogs}, messages {messages}); public filter now {options}")
    assert messages, f"the delete was stopped silently (no message at all): dialogs {dialogs}"
    assert cat_name in options, f"{cat_name!r} disappeared from the public 'All Events' filter: {options}"
    # Live 2026-10-05: the block works but reads "Delete failed: Object
    # relationship 143395 does not allow deletes" — a raw technical message,
    # not an "in use / reassign" explanation: LOW wording finding.
    if not any(re.search(r"in use|reassign", m, re.I) for m in messages):
        allure.attach(repr(messages), name="LOW finding: raw in-use message on category delete")


# ===========================================================================
# 143185 — Every photo unpublished: not publishable, not listed
# ===========================================================================
@AUTH_FREE_PAGE
@allure.epic(EPIC)
@allure.feature(FEATURE)
@allure.story("Publish rules")
@allure.severity(allure.severity_level.MINOR)
@allure.title("An album where every photo is unpublished is not publishable and does not appear on the listing")
@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.edge
@pytest.mark.pbi_130714
@pytest.mark.tc_143185
@GALLERY_PA_GROUP
def test_album_with_all_photos_unpublished_not_publishable(page):
    # Azure TC 143185 | PBI 130714 | account: Site Content Editor (156488). Read-only.
    albums, _ = _login(page, ROLE_EDITOR)
    albums.open_entry_en("QCDEMO-130714-PHOTO_ALBUM-first-test-album")
    photos = _per_photo_controls(albums)
    albums.evidence("143185 no per-photo publish status")
    assert photos["photos_panel"], (
        "step 1 'unpublish both photos' cannot be performed — " + MISSING_PHOTO_LAYER.format(form=photos["form_text"]))


MANUAL_SKIP = pytest.mark.skip(reason="Manual case — not automated")


@MANUAL_SKIP
@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_high
@pytest.mark.regression
@pytest.mark.pbi_130714
@pytest.mark.tc_143146
def test_manual_flickr_import_lands_assets_unpublished():
    """Azure TC 143146 (Manual)."""


@MANUAL_SKIP
@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_low
@pytest.mark.bilingual
@pytest.mark.pbi_130714
@pytest.mark.tc_143177
def test_flickr_import_never_writes_arabic_metadata():
    """Azure TC 143177 (Manual)."""


@MANUAL_SKIP
@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.edge
@pytest.mark.pbi_130714
@pytest.mark.tc_143186
def test_flickr_reimport_duplicate_handling():
    """Azure TC 143186 (Manual)."""
