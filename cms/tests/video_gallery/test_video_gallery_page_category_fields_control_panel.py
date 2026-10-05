"""
cms/tests/video_gallery/test_video_gallery_page_category_fields_control_panel.py —
Control_Panel field cases for PBI 130715 ("QC - Insights & Media - 007 - Video
Gallery"), Azure plan 137724 / suite 140374, Agent VB.

Covers:
  - 143018-143025, 143028, 143029 — Video Library page content settings (Page
    Title, Hero Background Image, Page Status, Created / Last Modified).
    LIVE 2026-10-05 there is NO authoring object behind the Video Library page
    hero (see cms/pages/video_gallery/video_page_admin_page.py): the only
    "page hero" object, `manage-page-hero` (Photo Gallery Page Hero), renders on
    the Photo pages only. Each case runs a read-only discovery first and is
    reported BLOCKED (with evidence) while that holds — one bug candidate,
    the same pattern as the Tenders review-panel cases (PBI 130952).
  - 143030-143040 — `manage-video-category` (Category Name EN/AR, Display
    Order, Active Status, workflow status).

Pattern (PBI 130952 / 130712 editorial-workflow rework):
  - Every case signs in as the Site Content Editor (156488) in an auth-free
    context; the userId is re-checked before each save. The Editor's submit
    button reads "Publish" (direct to Published).
  - "Save" in a required/invalid-value case = Publish (Save as Draft skips
    required-field validation). Every rejection case fills an otherwise valid
    form, so the field under test is the only invalid one, and requires
    (a) refusal evidence and (b) NO record created.
  - Records are disposable: English name `QCTEST-130715-VB-<tc>-<stamp> …`;
    the Arabic name carries the same prefix in the rejection cases so a
    record saved with a blank / whitespace English name is still
    identifiable. Identity (name + entry id + code) is captured by diffing the
    list's entry ids; teardown removes only those captured records through VA's
    guarded delete (a blank-named one is first renamed into the namespace by
    its captured id/code). The six real categories are never touched.
  - Public checks: stored Active Status verified first, then a fresh logged-out
    context (cms-profile.md budget 5 s @ 0.5 s).

Substitutions disclosed (case literal -> what runs):
  - Names keep the case literal as a suffix after the QCTEST prefix
    ("Community Outreach" -> "QCTEST-130715-VB-143031-<stamp> Community Outreach").
  - 143035 Display Order 3 -> 100 (user rule: 100-grid, 100 = the valid
    positive integer); "position 3" -> the position the 100 value implies
    (1st or 2nd chip — tied with Institutional = 100).
  - 143030 "Category ID": the form has no Category ID field; the
    system-generated identifiers are the entry id and the external reference
    code (edit link), both checked.
  - 143040 "Publish Status dropdown": the form has no status dropdown; the
    stored workflow status (Save as Draft -> Draft, Publish -> Published) is
    what persists and is checked on reload.
  - 143033 rule 6: one max-length category is published together with a
    disposable QCTEST-130715-VB- video in it (the category name renders on the
    public card tag and the details page; the chip row is checked too) and the
    public pages are checked EN/AR at 1920 and 390.
"""

from __future__ import annotations

import json
import os
import re
from datetime import datetime

import allure
import pytest

from cms.pages.components.object_authoring_page import STATUS_DRAFT, STATUS_PUBLISHED
from cms.pages.video_gallery.video_category_admin_page import KC_DISPLAY_ORDER, KC_NAME
from cms.pages.video_gallery.video_page_admin_page import (
    VB_EVIDENCE_DIR,
    VB_PREFIX,
    VideoCategoryFieldsVB,
    VideoDetailsPublicViewVB,
    VideoLibraryPublicViewVB,
    VideoPageSettingsLookupVB,
)
from cms.pages.video_gallery.video_record_admin_page import (
    DEFAULT_THUMBNAIL,
    K_CATEGORY_REL,
    K_THUMBNAIL,
    K_TITLE,
    K_VIDEO_URL,
    MSG_ARABIC_SAVED,
    MSG_DRAFT_SAVED,
    MSG_SAVED_AND_PUBLISHED,
    ROLE_EDITOR,
    ROLE_USER_IDS,
    VideoGalleryEntry,
    VideoRecordAdminPage,
)
from core.utils.waits import WaitTimeoutError, wait_until
from core.web.browser import new_context

pytestmark = [pytest.mark.control_panel, pytest.mark.media, pytest.mark.pbi_130715,
              pytest.mark.functional_low, pytest.mark.xdist_group("video_gallery_cms_vb")]

AUTH_FREE_PAGE = pytest.mark.parametrize("page", [{"auth": False}], indirect=True)
STAMP = datetime.now().strftime("%m%d%H%M%S")
VALID_ORDER = "100"
PUBLIC_REFLECT_TIMEOUT = 5.0   # cms-profile.md: poll 5 s @ 0.5 s
PUBLIC_POLL = 0.5
DESKTOP = (1920, 1080)
MOBILE = (390, 844)
WORDING_LOG = os.path.join(VB_EVIDENCE_DIR, "wording_findings.jsonl")


def _name(tc_id: str, suffix: str = "Category") -> str:
    return f"{VB_PREFIX}{tc_id}-{STAMP} {suffix}"


def _ar_marker(tc_id: str) -> str:
    return f"{VB_PREFIX}{tc_id}-{STAMP} تصنيف تجريبي"


def _exact_length(head: str, length: int, filler: str) -> str:
    text = head.rstrip()
    while len(text) < length:
        text += filler
    text = re.sub(r" {2,}", " ", text)[:length]  # HTML collapses double spaces
    return text[:-1] + "Z" if text.endswith(" ") else text


# ===========================================================================
# Fixtures
# ===========================================================================
class DisposableRegistry:
    """Records THIS test created: VideoGalleryEntry (category / video) or a
    blank-named category found by its Arabic VB marker."""

    def __init__(self):
        self.categories: dict[str, VideoGalleryEntry] = {}
        self.ar_marked: dict[str, dict] = {}
        self.videos: dict[str, VideoGalleryEntry] = {}

    def track(self, entry: VideoGalleryEntry) -> VideoGalleryEntry:
        if not entry.in_namespace() or entry.prefix != VB_PREFIX:
            raise ValueError(f"{entry} is not a {VB_PREFIX} record")
        self.categories[entry.entry_id] = entry
        return entry

    def track_ar_marked(self, found: dict) -> dict:
        if not found["stored_ar"].startswith(VB_PREFIX):
            raise ValueError(f"{found} carries no {VB_PREFIX} Arabic marker")
        self.ar_marked[found["entry_id"]] = found
        return found

    def track_video(self, entry: VideoGalleryEntry) -> VideoGalleryEntry:
        if not entry.in_namespace() or entry.prefix != VB_PREFIX:
            raise ValueError(f"{entry} is not a {VB_PREFIX} record")
        self.videos[entry.entry_id] = entry
        return entry

    def empty(self) -> bool:
        return not (self.categories or self.ar_marked or self.videos)


def _editor_session(page, admin_cls=VideoCategoryFieldsVB):
    admin = admin_cls(page)
    outcome = admin.login_as_role(ROLE_EDITOR)
    if outcome == "auth_failed":
        pytest.skip("PRECONDITION: Liferay refused the .env credentials for 'Site Content Editor'")
    if outcome != "ok":
        pytest.fail("login as 'Site Content Editor' neither succeeded nor showed Liferay's refusal banner")
    admin.open_list_all()
    user_id, _ = admin.signed_in_user()
    if user_id != ROLE_USER_IDS[ROLE_EDITOR]:
        pytest.skip(f"PRECONDITION: Editor credentials sign in as userId {user_id!r}, not 156488")
    return admin


def _remove(cleaner, entry: VideoGalleryEntry, label: str, outcome: list, failures: list) -> None:
    cleaner.open_list_all()
    if not cleaner.row_present(entry):
        if cleaner.is_list_fully_expanded():
            outcome.append(f"already gone: {label}")
        else:
            failures.append(f"{label}: not found and the list is NOT fully expanded")
        return
    cleaner.adopt(entry)
    if cleaner.delete_disposable_entry(entry):
        outcome.append(f"removed {label}")
    else:
        failures.append(f"NOT removed {label}: guarded delete refused/failed (see log)")


@pytest.fixture
def disposable(browser):
    """Deletes ONLY the records the test registered (videos first, then
    categories) from a fresh Site Content Editor context. Anything it cannot
    remove fails the teardown loudly with its exact identity."""
    registry = DisposableRegistry()
    yield registry
    if registry.empty():
        return
    ctx = new_context(browser, use_auth_state=False)
    outcome, failures = [], []
    try:
        page = ctx.new_page()
        videos = VideoRecordAdminPage(page, VB_PREFIX)
        if videos.login_as_role(ROLE_EDITOR) != "ok":
            raise AssertionError("teardown could not sign in as the Site Content Editor")
        for entry in registry.videos.values():
            label = f"video {entry.title!r} (id {entry.entry_id}, code {entry.code})"
            try:
                _remove(videos, entry, label, outcome, failures)
            except Exception as exc:  # noqa: BLE001 — collected below
                failures.append(f"{label}: {exc!r}")
        cats = VideoCategoryFieldsVB(page)
        for found in registry.ar_marked.values():
            label = (f"category stored as {found['stored_name']!r} / AR {found['stored_ar']!r} "
                     f"(id {found['entry_id']}, code {found['code']})")
            try:
                cats.owned_entry_ids.add(found["entry_id"])
                if found["stored_name"].startswith(VB_PREFIX):
                    entry = VideoGalleryEntry(title=found["stored_name"].strip(), entry_id=found["entry_id"],
                                              code=found["code"], prefix=VB_PREFIX)
                else:
                    entry = cats.rename_into_namespace(found, f"{VB_PREFIX}cleanup-{found['entry_id']}")
                if entry is None:
                    failures.append(f"NOT removed {label}: could not bring it into the namespace safely")
                    continue
                if entry.entry_id not in registry.categories:
                    registry.categories[entry.entry_id] = entry
            except Exception as exc:  # noqa: BLE001
                failures.append(f"{label}: {exc!r}")
        for entry in registry.categories.values():
            label = f"category {entry.title[:80]!r} (id {entry.entry_id}, code {entry.code})"
            try:
                _remove(cats, entry, label, outcome, failures)
            except Exception as exc:  # noqa: BLE001
                failures.append(f"{label}: {exc!r}")
    finally:
        ctx.close()
    allure.attach("\n".join(outcome + failures) or "nothing to remove", name="QCTEST teardown")
    if failures:
        raise AssertionError("TEARDOWN LEFT QCTEST DATA BEHIND:\n" + "\n".join(failures))


@pytest.fixture
def anon_pages(browser):
    """Fresh logged-out contexts for every public read; `viewport` optional."""
    contexts = []

    def _make(viewport: tuple | None = None):
        ctx = new_context(browser, viewport=viewport, use_auth_state=False)
        contexts.append(ctx)
        return ctx.new_page()

    yield _make
    for ctx in contexts:
        try:
            ctx.close()
        except Exception:  # noqa: BLE001
            pass


# ===========================================================================
# Helpers (test layer — no raw Playwright)
# ===========================================================================
def _pinned(admin) -> None:
    user_id, _ = admin.signed_in_user()
    assert user_id == ROLE_USER_IDS[ROLE_EDITOR], (
        f"the session is now userId {user_id!r}, not the pinned Site Content Editor (156488)")


def _record_wording(tc_id: str, field: str, expected: str, shown: str, evidence_png: str) -> None:
    finding = {"tc": tc_id, "field": field, "expected": expected, "shown": shown, "screenshot": evidence_png}
    allure.attach(json.dumps(finding, ensure_ascii=False, indent=1), name="LOW wording finding (block works)")
    os.makedirs(os.path.dirname(WORDING_LOG), exist_ok=True)
    with open(WORDING_LOG, "a", encoding="utf-8") as handle:
        handle.write(json.dumps(finding, ensure_ascii=False) + "\n")


def _attempt(admin: VideoCategoryFieldsVB, tc_id: str, what: str, name, name_ar, order,
             active: bool = True, draft: bool = False) -> dict:
    admin.open_create_form_en()
    admin.fill_category_vb(name, name_ar, order, active)
    typed = {"name": admin.text_value(KC_NAME), "name_ar": admin.ar_value(KC_NAME),
             "display_order": admin.display_order_value()}
    _pinned(admin)
    admin.click_save_as_draft() if draft else admin.click_publish()
    shot = admin.evidence(f"{tc_id}_{what}_after_{'draft' if draft else 'publish'}")
    return {"went_through": admin.save_went_through(), "refused": admin.save_was_refused(),
            "evidence": admin.refusal_evidence(), "messages": admin.all_messages_text(),
            "typed": typed, "screenshot": shot}


def _register(admin, disposable, name: str, ids_before: set) -> VideoGalleryEntry | None:
    try:
        entry = admin.identify_created(name, ids_before)
        return disposable.track(entry) if entry else None
    except Exception as exc:  # noqa: BLE001 — registration must not mask the result
        allure.attach(repr(exc), name=f"registration of {name[:60]!r} failed")
        return None


def _register_ar(admin, disposable, ar_marker: str, ids_before: set) -> dict | None:
    try:
        found = admin.identify_created_by_ar(ar_marker, ids_before)
        return disposable.track_ar_marked(found) if found else None
    except Exception as exc:  # noqa: BLE001
        allure.attach(repr(exc), name=f"registration of AR marker {ar_marker!r} failed")
        return None


def _create(admin, disposable, tc_id: str, name: str, name_ar: str, order: str = VALID_ORDER,
            draft: bool = False) -> tuple[VideoGalleryEntry, dict]:
    """Creates one category (Publish, or Save as Draft), registers it, THEN asserts."""
    ids_before = admin.snapshot_ids()
    result = {}
    try:
        result = _attempt(admin, tc_id, "create", name, name_ar, order, draft=draft)
        if result["went_through"]:
            result["success_bar"] = admin.success_messages(MSG_DRAFT_SAVED if draft else MSG_SAVED_AND_PUBLISHED,
                                                           10.0)
            result["arabic"] = admin.wait_arabic_saved()
    finally:
        entry = _register(admin, disposable, name, ids_before)
    allure.attach(json.dumps(result, ensure_ascii=False, indent=1, default=str), name=f"create {tc_id}")
    assert result.get("went_through"), (
        f"Saving {name[:80]!r} did not go through: {result.get('evidence')} | {result.get('messages')}")
    assert entry is not None, f"{name[:80]!r} went through but is not identifiable as exactly one NEW record"
    return entry, result


def _assert_blocked(admin, disposable, tc_id: str, what: str, name, order, field_pattern: str,
                    kind_pattern: str | None = None, expected_kind: str = "") -> dict:
    """Publish must be refused with evidence pointing at the field; NO record may
    be created (identity by the Arabic VB marker, so a blank English name is
    still caught). A working block with a different message passes + LOW wording."""
    ar_marker = _ar_marker(tc_id)
    ids_before = admin.snapshot_ids()
    result = {}
    try:
        result = _attempt(admin, tc_id, what, name, ar_marker, order)
    finally:
        found = _register_ar(admin, disposable, ar_marker, ids_before)
    allure.attach(json.dumps(result, ensure_ascii=False, indent=1, default=str), name=f"refusal evidence ({what})")
    if found is not None:
        pytest.fail(f"PRODUCT: Publish with {what} was NOT blocked — a record was created and published "
                    f"(entry id {found['entry_id']}, code {found['code']}, stored name {found['stored_name']!r}, "
                    f"row status {found.get('status')!r}); messages {result.get('messages')!r}; "
                    f"screenshot {result.get('screenshot')}")
    assert not result.get("went_through") and result.get("refused"), (
        f"Publish with {what} was neither refused with validation evidence nor saved: {result}")
    blob = json.dumps(result["evidence"], ensure_ascii=False)
    assert re.search(field_pattern, blob, re.I), (
        f"Publish was refused, but the validation evidence does not point at {what}: {result['evidence']}")
    if kind_pattern and not re.search(kind_pattern, result["messages"], re.I):
        _record_wording(tc_id, what, expected_kind or kind_pattern, result["messages"], result["screenshot"])
    return result


def _reopen(admin: VideoCategoryFieldsVB, entry: VideoGalleryEntry) -> dict:
    admin.open_entry_en(entry.code)
    try:
        wait_until(lambda: admin.ar_value(KC_NAME) != "", timeout=15.0, poll=0.5)
    except WaitTimeoutError:
        pass
    stored = admin.read_category()
    stored["edit_bar_status"] = admin.edit_bar_status()
    admin.open_list_all()
    stored["row_status"] = admin.row_status(entry)
    stored["row_last_modified"] = admin.row_last_modified(entry)
    allure.attach(json.dumps(stored, ensure_ascii=False, indent=1), name=f"stored {entry.code}")
    return stored


def _require_active(stored: dict, entry: VideoGalleryEntry) -> None:
    if stored.get("active_status") != "true":
        pytest.fail(f"PRECONDITION NOT MET — PRODUCT: {entry.title[:80]!r} stores Active Status "
                    f"{stored.get('active_status')!r}; the public step was not run")


def _public_categories(anon_pages, locale: str, expected: str, tc_id: str) -> dict:
    """Polls a fresh logged-out Video Library for `expected` in the chip row or
    the category dropdown. Returns what was shown + evidence."""
    view = VideoLibraryPublicViewVB(anon_pages(DESKTOP))
    state = {"chips": [], "dropdown": []}

    def _shown() -> bool:
        view.open_video_library(locale)
        state["chips"] = view.wait_for_categories(timeout=4.0)
        state["dropdown"] = view.dropdown_texts()
        return expected in state["chips"] or expected in state["dropdown"]

    try:
        wait_until(_shown, timeout=PUBLIC_REFLECT_TIMEOUT, poll=PUBLIC_POLL)
        state["found"] = True
    except WaitTimeoutError:
        state["found"] = False
    state["screenshot"] = view.evidence(f"{tc_id}_public_categories_{locale}")
    allure.attach(json.dumps(state, ensure_ascii=False, indent=1), name=f"public categories {locale}")
    return state


# ===========================================================================
# 143018-143025, 143028, 143029 — Video Library page content settings
# ===========================================================================
_PAGE_SETTINGS_LOOKUP: dict = {}


def _video_page_settings(page, anon_pages) -> dict:
    """One read-only discovery per module run (cached): is there an authoring
    object behind the Video Library page title / hero image / status?"""
    if _PAGE_SETTINGS_LOOKUP:
        return _PAGE_SETTINGS_LOOKUP
    lookup = _editor_session(page, VideoPageSettingsLookupVB)
    found = {"video_page_objects": lookup.video_page_objects()}
    found["index_screenshot"] = lookup.evidence("video_page_settings_object_index")
    found["page_hero_rows"] = [{"title": r["title"], "code": r["code"]} for r in lookup.page_hero_rows()]
    found["page_hero_fields"] = lookup.page_hero_form_fields()
    found["page_hero_preview_tabs"] = lookup.preview_panel_text("page-hero")
    found["page_hero_screenshot"] = lookup.evidence("video_page_settings_manage_page_hero")
    found["video_category_preview_tabs"] = lookup.preview_panel_text("video-category")
    public = VideoLibraryPublicViewVB(anon_pages(DESKTOP))
    public.open_video_library("en")
    found["public_hero_en"] = public.hero_state()
    found["public_screenshot"] = public.evidence("video_page_settings_public_video_library_hero", full_page=False)
    found["blocked"] = (not found["video_page_objects"]
                        and "video" not in found["page_hero_preview_tabs"].lower())
    _PAGE_SETTINGS_LOOKUP.update(found)
    return found


def _blocked_without_page_object(page, anon_pages, tc_id: str, subject: str) -> None:
    found = _video_page_settings(page, anon_pages)
    allure.attach(json.dumps(found, ensure_ascii=False, indent=1), name="Video Library page settings lookup")
    if found["blocked"]:
        pytest.skip(
            f"BLOCKED ({tc_id}) — no Video Library page content settings exist to test {subject}: the "
            f"Object Authoring index has no Video page/hero object; the only page-hero object "
            f"(manage-page-hero 'Photo Gallery Page Hero', rows {[r['title'] for r in found['page_hero_rows']]}) "
            f"previews on {found['page_hero_preview_tabs']!r}; the public hero "
            f"{found['public_hero_en'].get('title')!r} is fixed in the page fragment. "
            f"Evidence: {found['index_screenshot']}, {found['page_hero_screenshot']}, {found['public_screenshot']}")
    pytest.fail(f"A Video Library page-settings object now exists ({found['video_page_objects']}); "
                f"this case must be automated against it")


@AUTH_FREE_PAGE
@pytest.mark.tc_143018
@allure.title("143018 — Page Title accepts a valid value within 100 characters")
def test_143018_page_title_accepts_valid_value(page, anon_pages):
    _blocked_without_page_object(page, anon_pages, "143018", "Page Title = 'Video Library'")


@AUTH_FREE_PAGE
@pytest.mark.tc_143019
@allure.title("143019 — Page Title rejects an empty value")
def test_143019_page_title_rejects_empty(page, anon_pages):
    _blocked_without_page_object(page, anon_pages, "143019", "an empty Page Title")


@AUTH_FREE_PAGE
@pytest.mark.tc_143020
@allure.title("143020 — Page Title enforces the 100-character maximum")
def test_143020_page_title_max_length(page, anon_pages):
    _blocked_without_page_object(page, anon_pages, "143020", "the 100/101-character Page Title")


@AUTH_FREE_PAGE
@pytest.mark.tc_143021
@allure.title("143021 — Page Title rejects a whitespace-only value")
def test_143021_page_title_rejects_whitespace(page, anon_pages):
    _blocked_without_page_object(page, anon_pages, "143021", "a whitespace-only Page Title")


@AUTH_FREE_PAGE
@pytest.mark.tc_143022
@allure.title("143022 — Hero Background Image accepts a valid PNG under 2 MB")
def test_143022_hero_image_accepts_valid_png(page, anon_pages):
    _blocked_without_page_object(page, anon_pages, "143022", "a 500 KB PNG Hero Background Image")


@AUTH_FREE_PAGE
@pytest.mark.tc_143023
@allure.title("143023 — Hero Background Image is required")
def test_143023_hero_image_required(page, anon_pages):
    _blocked_without_page_object(page, anon_pages, "143023", "an empty Hero Background Image")


@AUTH_FREE_PAGE
@pytest.mark.tc_143024
@allure.title("143024 — Hero Background Image rejects a file over 2 MB")
def test_143024_hero_image_rejects_oversize(page, anon_pages):
    _blocked_without_page_object(page, anon_pages, "143024", "a 3.5 MB JPG Hero Background Image")


@AUTH_FREE_PAGE
@pytest.mark.tc_143025
@allure.title("143025 — Hero Background Image rejects an unsupported format")
def test_143025_hero_image_rejects_gif(page, anon_pages):
    _blocked_without_page_object(page, anon_pages, "143025", "a GIF Hero Background Image")


@AUTH_FREE_PAGE
@pytest.mark.tc_143028
@allure.title("143028 — Page Status persists each selectable value")
def test_143028_page_status_persists(page, anon_pages):
    _blocked_without_page_object(page, anon_pages, "143028", "the page Status Draft/Published/Unpublished")


@AUTH_FREE_PAGE
@pytest.mark.tc_143029
@allure.title("143029 — Page Created / Last Modified date updates on edit")
def test_143029_page_last_modified_updates(page, anon_pages):
    _blocked_without_page_object(page, anon_pages, "143029", "the page's Last Modified timestamp")


# ===========================================================================
# 143030-143040 — Video Category
# ===========================================================================
@AUTH_FREE_PAGE
@pytest.mark.tc_143030
@allure.title("143030 — a new Video Category gets a distinct system-generated ID")
def test_143030_category_id_auto_unique(page, disposable):
    admin = _editor_session(page)
    admin.open_create_form_en()
    form_fields = admin.form_field_names()
    first, _ = _create(admin, disposable, "143030", _name("143030", "First"), _ar_marker("143030") + " 1",
                       draft=True)
    second, _ = _create(admin, disposable, "143030", _name("143030", "Second"), _ar_marker("143030") + " 2",
                        draft=True)
    ids = {"first": [first.entry_id, first.code], "second": [second.entry_id, second.code],
           "form_fields": form_fields}
    allure.attach(json.dumps(ids, indent=1), name="generated identifiers")
    assert first.entry_id and second.entry_id and first.code and second.code, ids
    assert re.fullmatch(r"\d+", first.entry_id) and re.fullmatch(r"\d+", second.entry_id), ids
    assert first.entry_id != second.entry_id, f"both categories got the same entry id: {ids}"
    assert first.code != second.code, f"both categories got the same reference code: {ids}"


@AUTH_FREE_PAGE
@pytest.mark.tc_143031
@allure.title("143031 — Category Name accepts a valid EN/AR value and shows on the frontend")
def test_143031_category_name_valid(page, disposable, anon_pages):
    admin = _editor_session(page)
    name, name_ar = _name("143031", "Community Outreach"), "التواصل المجتمعي"
    entry, created = _create(admin, disposable, "143031", name, name_ar)
    assert any(MSG_SAVED_AND_PUBLISHED in t for t in created.get("success_bar", [])), created
    stored = _reopen(admin, entry)
    if created.get("arabic") != MSG_ARABIC_SAVED:
        allure.attach(f"Arabic save notice seen: {created.get('arabic')!r}", name="Arabic notice (informational)")
    assert stored[KC_NAME] == name and stored[f"{KC_NAME}_ar"] == name_ar, stored
    assert stored[KC_DISPLAY_ORDER] == VALID_ORDER and stored["row_status"] == STATUS_PUBLISHED, stored
    _require_active(stored, entry)
    en = _public_categories(anon_pages, "en", name, "143031")
    ar = _public_categories(anon_pages, "ar", name_ar, "143031")
    assert en["found"] and ar["found"], (
        f"PRODUCT: the published, active category is not on the public Video Library chip row / dropdown. "
        f"EN chips {en['chips']} dropdown {en['dropdown']}; AR chips {ar['chips']} dropdown {ar['dropdown']}. "
        f"Screenshots {en['screenshot']}, {ar['screenshot']}")


@AUTH_FREE_PAGE
@pytest.mark.tc_143032
@allure.title("143032 — Category Name rejects an empty value")
def test_143032_category_name_rejects_empty(page, disposable):
    admin = _editor_session(page)
    _assert_blocked(admin, disposable, "143032", "an empty English Category Name", None, VALID_ORDER,
                    field_pattern=r"categoryName|Category Name", kind_pattern=r"required|fill out|complete the required",
                    expected_kind="a required-field validation error")


@AUTH_FREE_PAGE
@pytest.mark.tc_143033
@allure.title("143033 — Category Name enforces the 200-character maximum")
def test_143033_category_name_max_length(page, disposable):
    admin = _editor_session(page)
    problems = []
    name_200 = _exact_length(_name("143033", "Max"), 200, " Category name length boundary")
    assert len(name_200) == 200
    entry, created = _create(admin, disposable, "143033", name_200, _ar_marker("143033") + " 200")
    stored = _reopen(admin, entry)
    if stored[KC_NAME] != name_200:
        problems.append(f"the 200-character name did not persist exactly: stored {len(stored[KC_NAME])} chars "
                        f"{stored[KC_NAME]!r}")
    name_201 = name_200[:-1] + "YZ"
    ar_marker = _ar_marker("143033") + " 201"
    ids_before = admin.snapshot_ids()
    result = {}
    try:
        result = _attempt(admin, "143033", "201_chars", name_201, ar_marker, VALID_ORDER)
    finally:
        found = _register_ar(admin, disposable, ar_marker, ids_before)
    allure.attach(json.dumps(result, ensure_ascii=False, indent=1, default=str), name="201-character attempt")
    typed_len = len(result.get("typed", {}).get("name", ""))
    if found is not None:
        stored_len = len(found["stored_name"])
        if stored_len > 200:
            problems.append(f"PRODUCT: a 201-character Category Name was accepted and stored in full "
                            f"({stored_len} chars, entry id {found['entry_id']}, code {found['code']}); no "
                            f"max-length indication. Messages {result.get('messages')!r}; screenshot "
                            f"{result.get('screenshot')}")
        elif typed_len > 200:
            problems.append(f"PRODUCT: 201 characters were typed and the record was saved truncated to "
                            f"{stored_len} without any max-length indication; screenshot {result.get('screenshot')}")
    elif not result.get("refused") and typed_len > 200:
        problems.append(f"the 201-character attempt was neither saved nor refused: {result}")
    assert not problems, " || ".join(problems)


@AUTH_FREE_PAGE
@pytest.mark.tc_143033
@allure.title("143033 (rule 6) — a 200-character category renders correctly on the public pages")
def test_143033_max_length_category_on_public_pages(page, disposable, anon_pages):
    admin = _editor_session(page)
    name_200 = _exact_length(_name("143033", "Public"), 200, " Category name length boundary")
    ar_200 = _exact_length(f"{VB_PREFIX}143033-{STAMP} ", 200, " تصنيف طويل لاختبار حد الطول")
    category, _ = _create(admin, disposable, "143033", name_200, ar_200)
    stored = _reopen(admin, category)
    _require_active(stored, category)

    videos = VideoRecordAdminPage(page, VB_PREFIX)
    title = _name("143033", "charlimit video")
    data = VideoRecordAdminPage.default_video_data(
        title, **{K_CATEGORY_REL: name_200, K_THUMBNAIL: DEFAULT_THUMBNAIL,
                  f"{K_THUMBNAIL}_stem": "vb-qctest-130715-thumb",
                  K_VIDEO_URL: "https://www.youtube.com/watch?v=jNQXAC9IVRw"})
    ids_before = videos.snapshot_ids()
    try:
        videos.open_create_form_en()
        videos.fill_video(data)
        _pinned(videos)
        videos.click_publish()
        published = videos.save_went_through()
        if published:
            videos.wait_arabic_saved()
    finally:
        video = videos.identify_created(title, ids_before)
        if video is not None:
            disposable.track_video(video)
    assert published and video is not None, f"the carrier video was not created: {videos.refusal_evidence()}"
    videos.open_entry_en(video.code)
    video_stored = videos.read_video()
    allure.attach(json.dumps(video_stored, ensure_ascii=False, indent=1), name="carrier video stored")
    if video_stored.get("active_status") != "true":
        pytest.fail(f"PRECONDITION NOT MET — the carrier video stores Active Status {video_stored.get('active_status')!r}")

    findings, report = [], {}
    for locale, expected in (("en", name_200), ("ar", ar_200)):
        for label, viewport in (("1920", DESKTOP), ("390", MOBILE)):
            listing = VideoLibraryPublicViewVB(anon_pages(viewport))
            state = {"card": {}}

            def _card(view=listing, loc=locale, state=state) -> bool:
                view.open_listing_all(loc)
                state["card"] = view.card_for_code(video.code)
                return bool(state["card"])

            try:
                wait_until(_card, timeout=PUBLIC_REFLECT_TIMEOUT, poll=PUBLIC_POLL)
            except WaitTimeoutError:
                pass
            key = f"{locale}_{label}"
            report[key] = {"card": state["card"], "chips": listing.chip_texts(),
                           "listing_layout": listing.overflow_report([".qc-vll-tag", "a.qc-vll-card", ".qc-vll-grid",
                                                                      ".qc-vll-chip"]),
                           "listing_png": listing.evidence(f"143033_charlimit_listing_{key}")}
            details = VideoDetailsPublicViewVB(anon_pages(viewport))
            report[key]["details"] = details.details_state(video.code, locale)
            report[key]["details_tag"] = details.category_tag_text()
            report[key]["details_layout"] = details.overflow_report([".qc-vdt-tag", ".qc-vdt-title", ".qc-vdt-shell"])
            report[key]["details_png"] = details.evidence(f"143033_charlimit_details_{key}")
            if not state["card"]:
                findings.append(f"{key}: the carrier video card is not on the public listing")
            elif state["card"]["tag"] != expected:
                findings.append(f"{key}: card tag shows {len(state['card']['tag'])} chars "
                                f"{state['card']['tag'][:60]!r}…, not the full {len(expected)}-char name")
            if report[key]["details_tag"] != expected:
                findings.append(f"{key}: details tag shows {report[key]['details_tag'][:60]!r} "
                                f"({len(report[key]['details_tag'])} chars), not the full name")
            for where in ("listing_layout", "details_layout"):
                for item in report[key][where]:
                    if item.get("page_hscroll"):
                        findings.append(f"{key} {where}: horizontal page scroll (scrollWidth {item['scrollWidth']} > "
                                        f"{item['vw']})")
                    if item.get("beyond_viewport"):
                        findings.append(f"{key} {where}: {item['sel']} extends beyond the viewport "
                                        f"({item['width']}px of {item['vw']})")
                    if item.get("clipped") and item["sel"] in (".qc-vll-tag", ".qc-vdt-tag", ".qc-vll-chip"):
                        findings.append(f"{key} {where}: {item['sel']} text is clipped "
                                        f"(ellipsis={item['ellipsis']}, clamp={item['line_clamp']})")
    allure.attach(json.dumps(report, ensure_ascii=False, indent=1, default=str), name="char-limit public report")
    with open(os.path.join(VB_EVIDENCE_DIR, "143033_charlimit_report.json"), "w", encoding="utf-8") as handle:
        json.dump({"findings": findings, "report": report}, handle, ensure_ascii=False, indent=1, default=str)
    assert not findings, "PRODUCT (char-limit frontend): " + " || ".join(findings)


@AUTH_FREE_PAGE
@pytest.mark.tc_143034
@allure.title("143034 — Category Name rejects a whitespace-only value")
def test_143034_category_name_rejects_whitespace(page, disposable):
    admin = _editor_session(page)
    _assert_blocked(admin, disposable, "143034", "a whitespace-only English Category Name", "   ", VALID_ORDER,
                    field_pattern=r"categoryName|Category Name", kind_pattern=r"space|empty|required|fill out|complete the required",
                    expected_kind="blocked as equivalent to empty")


@AUTH_FREE_PAGE
@pytest.mark.tc_143035
@allure.title("143035 — Display Order accepts a valid positive integer (100)")
def test_143035_display_order_valid(page, disposable, anon_pages):
    admin = _editor_session(page)
    name = _name("143035", "Ordered")
    entry, created = _create(admin, disposable, "143035", name, _ar_marker("143035"))
    stored = _reopen(admin, entry)
    assert stored[KC_DISPLAY_ORDER] == VALID_ORDER and stored["row_status"] == STATUS_PUBLISHED, stored
    _require_active(stored, entry)
    en = _public_categories(anon_pages, "en", name, "143035")
    assert en["found"], (
        f"PRODUCT: the published category (Display Order 100) is not on the public chip row / dropdown at all "
        f"(chips {en['chips']}, dropdown {en['dropdown']}); position cannot be checked. Screenshot {en['screenshot']}")
    chips = [c for c in en["chips"] if c not in ("All Videos",)]
    position = chips.index(name) + 1 if name in chips else -1
    assert position in (1, 2), (
        f"Display Order 100 should place the category 1st or 2nd (tied with Institutional = 100); "
        f"it is at {position} in {chips}")


@AUTH_FREE_PAGE
@pytest.mark.tc_143036
@allure.title("143036 — Display Order rejects an empty value")
def test_143036_display_order_rejects_empty(page, disposable):
    admin = _editor_session(page)
    _assert_blocked(admin, disposable, "143036", "an empty Display Order", _name("143036", "No Order"), "",
                    field_pattern=r"displayOrder|Display Order", kind_pattern=r"required|fill out|complete the required",
                    expected_kind="a required-field validation error")


@AUTH_FREE_PAGE
@pytest.mark.tc_143037
@allure.title("143037 — Display Order rejects zero")
def test_143037_display_order_rejects_zero(page, disposable):
    admin = _editor_session(page)
    _assert_blocked(admin, disposable, "143037", "Display Order = 0", _name("143037", "Zero Order"), "0",
                    field_pattern=r"displayOrder|Display Order", kind_pattern=r"positive|greater|at least|100|minimum",
                    expected_kind="0 is not a positive integer")


@AUTH_FREE_PAGE
@pytest.mark.tc_143038
@allure.title("143038 — Display Order rejects a negative value")
def test_143038_display_order_rejects_negative(page, disposable):
    admin = _editor_session(page)
    _assert_blocked(admin, disposable, "143038", "Display Order = -2", _name("143038", "Negative Order"), "-2",
                    field_pattern=r"displayOrder|Display Order", kind_pattern=r"negative|positive|greater|at least|100|minimum",
                    expected_kind="negative values are not permitted")


@AUTH_FREE_PAGE
@pytest.mark.tc_143039
@allure.title("143039 — Display Order rejects a non-numeric value")
def test_143039_display_order_rejects_non_numeric(page, disposable):
    admin = _editor_session(page)
    result = _assert_blocked(admin, disposable, "143039", "Display Order = 'abc'", _name("143039", "Alpha Order"),
                             "abc", field_pattern=r"displayOrder|Display Order", kind_pattern=r"number|numeric|valid value",
                             expected_kind="a numeric-format validation error")
    assert result["typed"]["display_order"] == "", (
        f"the number input kept a non-numeric value {result['typed']['display_order']!r}")


@AUTH_FREE_PAGE
@pytest.mark.tc_143040
@allure.title("143040 — the category's publish status persists (Draft, then Published)")
def test_143040_category_status_persists(page, disposable):
    admin = _editor_session(page)
    name = _name("143040", "Status")
    entry, created = _create(admin, disposable, "143040", name, _ar_marker("143040"), draft=True)
    assert any(MSG_DRAFT_SAVED in t for t in created.get("success_bar", [])), created
    as_draft = _reopen(admin, entry)
    assert as_draft["row_status"] == STATUS_DRAFT and as_draft["edit_bar_status"] == "Draft", as_draft
    admin.open_entry_en(entry.code)
    _pinned(admin)
    admin.click_publish()
    shot = admin.evidence("143040_publish_from_draft")
    assert admin.save_went_through(), f"Publish of the draft did not go through: {admin.refusal_evidence()} {shot}"
    as_published = _reopen(admin, entry)
    assert as_published["row_status"] == STATUS_PUBLISHED and as_published["edit_bar_status"] == "Published", \
        as_published
    assert as_published[KC_NAME] == name and as_published["active_status"] == "true", as_published
