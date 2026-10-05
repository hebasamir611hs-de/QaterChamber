"""
cms/tests/video_gallery/test_video_gallery_record_fields_control_panel.py —
Control_Panel Video Record FIELD cases for PBI 130715 ("QC - Insights & Media -
007 - Video Gallery"), Azure plan 137724 / suite 140374, on the Object
Authoring surface `manage-video-record` (Agent VC).

Covers 143041-143068, 143070-143073 (Video ID, Title, Category, Source Type +
conditional fields, Flickr Video ID, Video URL, Video File, Thumbnail,
Duration, Description, Published Date, Flickr Source Folder, Video Status,
Last Modified, missing Arabic content).

Pattern (Tenders PBI 130952 / Annual Reports PBI 130712 editorial rework):
  - Every case runs as the Site Content Editor (156488) in an auth-free
    context; the signed-in userId is re-checked before each save. The
    Editor's submit button reads "Publish".
  - "Save" in a required/invalid-value case = the Editor's Publish (Save as
    Draft skips required-field validation). Each rejection case fills a
    complete, otherwise-valid form so the field under test is the only
    invalid one and requires (a) refusal evidence and (b) NO record created.
    Validation is proven on the UNSAVED form wherever the case allows it.
  - Disposable records: title `QCTEST-130715-VC-<tc>-<stamp> …`; identity
    (title + entry id + code) is captured right after the save by diffing the
    list's ids; teardown deletes only those captured records through the
    core guarded delete. A record the product wrongly saves with a blank EN
    title is captured by its `QCTEST-130715-VC-` ARABIC title and removed by
    the VC blank-title guarded delete. Real QCDEMO-130715-VIDEO-* records and
    "Youtube" are only ever READ (143050 / 143070).
  - Public checks: stored Active Status is verified first (re-opened record),
    then a fresh logged-out context reads the listing (Load More expanded)
    and the Details page, polled per cms-profile.md (5 s @ 0.5 s once the CMS
    shows Published).
  - Wording-only differences (the block works, only the message differs from
    the case) PASS and are recorded as a LOW wording finding
    (reports/evidence/130715_vc/wording_findings.jsonl).
  - Character-limit cases (143044 title 200, 143063/143064 description 2000)
    also publish one max-length record and check the public listing + detail,
    EN and AR, at 1920 and 390 (rule 6); layout findings are recorded in
    reports/evidence/130715_vc/charlimit_findings.jsonl.

Substitutions disclosed (case literal -> what runs):
  - Titles carry the QCTEST-130715-VC- prefix; the case literal follows it.
  - 143059 "a record with Duration auto-populated as 08:31": the real
    record holding 08:31 (QCDEMO-130715-VIDEO-01) is never edited — the test
    creates its own record with 08:31, then edits it to 12:45.
  - 143057 "Thumbnail EN/AR": the form has ONE (non-localized) Video
    Thumbnail upload; a single PNG is used.
  - 143050 / 143070 (Flickr import): no import is triggered (shared real
    data, Administrator-only — brief rule 8); the existing records are only
    read, and the case is reported Blocked when no Flickr-IMPORTED record
    exists.
"""

from __future__ import annotations

import json
import os
import re
from datetime import date, datetime

import allure
import pytest

from cms.pages.components.object_authoring_page import STATUS_DRAFT, STATUS_PUBLISHED
from cms.pages.video_gallery.video_record_admin_page import (
    K_CATEGORY_REL,
    K_DESCRIPTION,
    K_DURATION,
    K_FLICKR_FOLDER_REL,
    K_FLICKR_SOURCE_FOLDER,
    K_FLICKR_VIDEO_ID,
    K_FLICKR_VIDEO_REL,
    K_PUBLISHED_DATE,
    K_SOURCE_TYPE,
    K_THUMBNAIL,
    K_TITLE,
    K_VIDEO_FILE,
    K_VIDEO_STATUS,
    K_VIDEO_URL,
    MSG_DRAFT_SAVED,
    MSG_SAVED_AND_PUBLISHED,
    REAL_CODE_PREFIX,
    ROLE_EDITOR,
    ROLE_USER_IDS,
    SOURCE_DIRECT_UPLOAD,
    SOURCE_EXTERNAL_URL,
    SOURCE_FLICKR,
    VC_CLIP_AVI,
    VC_CLIP_MP4,
    VC_PREFIX,
    VC_THUMBNAIL,
    VC_THUMBNAIL_BMP,
    VideoBlankTitleEntryVC,
    VideoGalleryEntry,
    VideoPublicViewVC,
    VideoRecordAdminPage,
    VideoRecordFieldsAdminPageVC,
)
from core.utils.waits import WaitTimeoutError, wait_until
from core.web.browser import new_context

pytestmark = [pytest.mark.control_panel, pytest.mark.media, pytest.mark.pbi_130715,
              pytest.mark.functional_low, pytest.mark.xdist_group("video_gallery_cms_fields_vc")]

AUTH_FREE_PAGE = pytest.mark.parametrize("page", [{"auth": False}], indirect=True)
STAMP = datetime.now().strftime("%m%d%H%M%S")
TODAY = date.today()
EDITOR_ID = ROLE_USER_IDS[ROLE_EDITOR]

PUBLISH_CONFIRM_TIMEOUT = 120.0
PUBLIC_REFLECT_TIMEOUT = 5.0   # cms-profile.md: poll 5 s @ 0.5 s
PUBLIC_POLL = 0.5
EVIDENCE_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__))))), "reports", "evidence", "130715_vc")
WORDING_LOG = os.path.join(EVIDENCE_DIR, "wording_findings.jsonl")
CHARLIMIT_LOG = os.path.join(EVIDENCE_DIR, "charlimit_findings.jsonl")
DESKTOP, MOBILE = (1920, 1080), (390, 844)
SERVER_REFUSAL = re.compile(r"was not saved|Nothing has been submitted|Please complete the required fields")


def _title(tc_id: str, suffix: str = "Video") -> str:
    return f"{VC_PREFIX}{tc_id}-{STAMP} {suffix}"


def _dmy(d: date) -> str:
    return d.strftime("%d/%m/%Y")


def _data(tc_id: str, suffix: str = "Video", **overrides) -> dict:
    data = VideoRecordAdminPage.default_video_data(
        _title(tc_id, suffix),
        **{K_THUMBNAIL: VC_THUMBNAIL, f"{K_THUMBNAIL}_stem": f"vc_qctest_thumb_{tc_id}",
           K_VIDEO_URL: "https://www.youtube.com/watch?v=jNQXAC9IVRw", K_PUBLISHED_DATE: _dmy(TODAY),
           K_CATEGORY_REL: "Institutional"})
    data.update(overrides)
    return data


# ===========================================================================
# Fixtures
# ===========================================================================
class DisposableRegistry:
    def __init__(self):
        self.entries: dict[str, VideoGalleryEntry] = {}
        self.blank_entries: dict[str, VideoBlankTitleEntryVC] = {}

    def track(self, entry):
        if isinstance(entry, VideoBlankTitleEntryVC):
            if not entry.in_namespace():
                raise ValueError(f"{entry} is not a {VC_PREFIX} record")
            self.blank_entries[entry.entry_id] = entry
        else:
            if not entry.in_namespace() or entry.prefix != VC_PREFIX:
                raise ValueError(f"{entry} is not a {VC_PREFIX} record")
            self.entries[entry.entry_id] = entry
        return entry


@pytest.fixture
def disposable(browser):
    """Deletes ONLY the records the test registered at creation (guarded delete)."""
    registry = DisposableRegistry()
    yield registry
    if not registry.entries and not registry.blank_entries:
        return
    ctx = new_context(browser, use_auth_state=False)
    outcome, failures = [], []
    try:
        cleaner = VideoRecordFieldsAdminPageVC(ctx.new_page())
        if cleaner.login_as_role(ROLE_EDITOR) != "ok":
            failures.append("cleanup login as Site Content Editor failed")
        for entry in list(registry.entries.values()) + list(registry.blank_entries.values()):
            label = repr(entry)
            try:
                cleaner.open_list_all()
                if not any(r["entry_id"] == entry.entry_id for r in cleaner.list_rows()):
                    (outcome if cleaner.is_list_fully_expanded() else failures).append(
                        f"already gone: {label}" if cleaner.is_list_fully_expanded()
                        else f"{label}: not found and the list is NOT fully expanded")
                    continue
                if isinstance(entry, VideoBlankTitleEntryVC):
                    cleaner.owned_entry_ids.add(entry.entry_id)
                    ok = cleaner.delete_blank_title_entry(entry)
                else:
                    cleaner.adopt(entry)
                    ok = cleaner.delete_disposable_entry(entry)
                (outcome if ok else failures).append(
                    f"removed {label}" if ok else f"NOT removed {label}: guarded delete refused/failed")
            except Exception as exc:  # noqa: BLE001 — collected below
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
def _editor(page) -> VideoRecordFieldsAdminPageVC:
    admin = VideoRecordFieldsAdminPageVC(page)
    outcome = admin.login_as_role(ROLE_EDITOR)
    if outcome == "auth_failed":
        pytest.skip("PRECONDITION: Liferay refused the .env credentials for 'Site Content Editor'")
    if outcome != "ok":
        pytest.fail("login as 'Site Content Editor' neither succeeded nor showed Liferay's refusal banner")
    admin.open_list_all()
    user_id, _ = admin.signed_in_user()
    if user_id != EDITOR_ID:
        pytest.skip(f"PRECONDITION: Editor credentials sign in as userId {user_id!r}, not {EDITOR_ID}")
    return admin


def _pinned(admin) -> None:
    user_id, _ = admin.signed_in_user()
    assert user_id == EDITOR_ID, f"the session is now userId {user_id!r}, not the pinned Site Content Editor"


def _attach(name: str, payload) -> None:
    allure.attach(json.dumps(payload, ensure_ascii=False, indent=1, default=str), name=name,
                  attachment_type=allure.attachment_type.JSON)


def _log(path: str, finding: dict, name: str) -> None:
    _attach(name, finding)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "a", encoding="utf-8") as handle:
        handle.write(json.dumps(finding, ensure_ascii=False, default=str) + "\n")


def _record_wording(tc_id: str, field: str, expected: str, shown: str, png: str) -> None:
    _log(WORDING_LOG, {"tc": tc_id, "field": field, "expected": expected, "shown": shown, "screenshot": png},
         "LOW wording finding (block works)")


def _register(admin, disposable, data: dict, ids_before: set):
    """Captures whatever THIS attempt created (by EN title, else by the AR marker)."""
    try:
        title = (data.get(K_TITLE) or "")
        if title.strip().startswith(VC_PREFIX):
            entry = admin.identify_created(title, ids_before)
        else:
            entry = admin.identify_created_by_ar(data.get(f"{K_TITLE}_ar") or "", ids_before)
        return disposable.track(entry) if entry else None
    except Exception as exc:  # noqa: BLE001 — registration must not mask the result
        allure.attach(repr(exc), name="registration failed")
        return None


def _new_rows(admin, ids_before: set) -> list[dict]:
    admin.open_list_all()
    # rows of the other parallel agents' namespaces (QCTEST-<pbi>-<agent>-) are not ours
    return [r for r in admin.list_rows() if r["entry_id"] not in ids_before
            and not (r["title"].startswith("QCTEST-") and not r["title"].startswith(VC_PREFIX))]


def _attempt(admin, data: dict, tc_id: str, what: str, before_save=None, draft: bool = False) -> dict:
    """Fills a NEW form, optionally runs `before_save(admin)`, clicks Publish (or Save as Draft)."""
    admin.open_create_form_en()
    admin.fill_video(data)
    if before_save:
        before_save(admin)
    _pinned(admin)
    admin.click_save_as_draft() if draft else admin.click_publish()
    shot = admin.evidence(f"{tc_id}_{what}_after_{'draft' if draft else 'publish'}")
    went = admin.save_went_through()
    # a server-side refusal ("This record was not saved: ...") leaves the form in place with
    # no invalid event - it is a refusal too when nothing was saved
    server_refusal = any(SERVER_REFUSAL.search(t) for t in admin.editbar_texts())
    return {"went_through": went, "refused": admin.save_was_refused() or (not went and server_refusal),
            "evidence": admin.refusal_evidence(), "messages": admin.all_messages_text(), "screenshot": shot,
            "editbar": admin.editbar_texts()}


def _create(admin, disposable, data: dict, tc_id: str, draft: bool = False, before_save=None) -> VideoGalleryEntry:
    """Creates (publishes, or saves as draft) one record, registers it for teardown, THEN asserts."""
    ids_before = admin.snapshot_ids()
    result = {}
    try:
        result = _attempt(admin, data, tc_id, "create", before_save=before_save, draft=draft)
        expected = MSG_DRAFT_SAVED if draft else MSG_SAVED_AND_PUBLISHED
        result["success_messages"] = admin.success_messages(expected, 10.0) if result["went_through"] else []
    finally:
        entry = _register(admin, disposable, data, ids_before)
    _attach(f"create {data.get(K_TITLE)!r}", result)
    assert result.get("went_through"), (
        f"Saving {data.get(K_TITLE)!r} did not go through: {result.get('evidence')} | {result.get('messages')} "
        f"| screenshot {result.get('screenshot')}")
    assert entry is not None, f"{data.get(K_TITLE)!r} went through but is not identifiable as exactly one NEW record"
    return entry


def _assert_blocked(admin, disposable, data: dict, tc_id: str, what: str, field_pattern: str,
                    expected_kind: str | None = None, kind_pattern: str | None = None,
                    before_save=None) -> dict:
    """Publish must be refused with validation evidence pointing at the field and NO record created."""
    ids_before = admin.snapshot_ids()
    result = {}
    try:
        result = _attempt(admin, data, tc_id, what, before_save)
    finally:
        entry = _register(admin, disposable, data, ids_before)
        new = _new_rows(admin, ids_before) if entry is None else []
    _attach(f"refusal evidence ({what})", result)
    if entry is not None:
        admin.open_list_all()
        stored = getattr(entry, "title", "") or f"(blank EN title, AR {entry.ar_title!r})"
        pytest.fail(f"PRODUCT: Publish with {what} was NOT blocked — a record was created (entry id "
                    f"{entry.entry_id}, code {entry.code}, stored title {stored!r}, messages "
                    f"{result.get('editbar')}); screenshot {result.get('screenshot')}")
    assert not new, f"UNIDENTIFIED new rows appeared after the attempt (NOT deleted — report): {new}"
    assert not result.get("went_through") and result.get("refused"), (
        f"Publish with {what} was neither refused with validation evidence nor saved: {result}")
    blob = json.dumps(result["evidence"], ensure_ascii=False)
    assert re.search(field_pattern, blob, re.I), (
        f"Publish was refused, but the validation evidence does not point at {what}: {result['evidence']}")
    if kind_pattern and not re.search(kind_pattern, result["messages"], re.I):
        _record_wording(tc_id, what, expected_kind or kind_pattern, result["messages"], result["screenshot"])
    return result


def _wait_published(admin, entry) -> str:
    seen = {"status": ""}

    def _reached() -> bool:
        admin.open_list_all()
        seen["status"] = admin.row_status(entry)
        return seen["status"] == STATUS_PUBLISHED

    try:
        wait_until(_reached, timeout=PUBLISH_CONFIRM_TIMEOUT, poll=3.0)
    except WaitTimeoutError:
        pass
    assert seen["status"] == STATUS_PUBLISHED, f"{entry.title!r} never reached Published (last {seen['status']!r})"
    return seen["status"]


def _require_active_status(admin, entry) -> dict:
    admin.open_entry_en(entry.code)
    stored = admin.read_video()
    _attach("stored record before the public step", stored)
    if stored.get("active_status") != "true":
        pytest.fail(f"PRECONDITION NOT MET — PRODUCT: {entry.title!r} stores Active Status "
                    f"{stored.get('active_status')!r}; the public step was not run")
    return stored


def _public_card(anon_pages, entry, locale: str = "en", viewport=None) -> tuple[VideoPublicViewVC, dict]:
    view = VideoPublicViewVC(anon_pages(viewport))
    state = {"card": {}}

    def _check() -> bool:
        view.open_listing_all(locale)
        state["card"] = view.card_for_code(entry.code)
        return bool(state["card"])

    try:
        wait_until(_check, timeout=PUBLIC_REFLECT_TIMEOUT, poll=PUBLIC_POLL)
    except WaitTimeoutError:
        view.evidence(f"{entry.code}_listing_{locale}_not_found")
        pytest.fail(f"DELIVERY: {entry.title!r} (code {entry.code}) never appeared on the logged-out "
                    f"{locale.upper()} Video Library listing")
    return view, state["card"]


def _public_detail(anon_pages, entry, locale: str = "en", viewport=None) -> tuple[VideoPublicViewVC, dict]:
    view = VideoPublicViewVC(anon_pages(viewport))
    state = {"detail": {}}

    def _check() -> bool:
        view.open_detail(entry.code, locale)
        state["detail"] = view.detail()
        return not state["detail"]["not_found"] and bool(state["detail"]["title"])

    try:
        wait_until(_check, timeout=PUBLIC_REFLECT_TIMEOUT, poll=PUBLIC_POLL)
    except WaitTimeoutError:
        view.evidence(f"{entry.code}_detail_{locale}_not_found")
        pytest.fail(f"DELIVERY: the logged-out {locale.upper()} Details page of {entry.title!r} "
                    f"(erc {entry.code}) did not render it: {state['detail']}")
    return view, state["detail"]


def _published_and_public(admin, entry, anon_pages, locale: str = "en"):
    _wait_published(admin, entry)
    _require_active_status(admin, entry)
    return _public_card(anon_pages, entry, locale)


def _layout_sweep(anon_pages, entry, tc_id: str, label: str, needle_en: str, needle_ar: str,
                  listing: bool = True) -> list[dict]:
    """Rule 6: listing + detail, EN and AR, desktop 1920 and mobile 390 — returns findings."""
    findings = []
    for locale, needle in (("en", needle_en), ("ar", needle_ar)):
        for name, viewport in (("1920", DESKTOP), ("390", MOBILE)):
            pages = []
            if listing:
                view, card = _public_card(anon_pages, entry, locale, viewport)
                pages.append(("listing", view, view.LISTING_TEXT_SELECTORS, card.get("title", "")))
            view, detail = _public_detail(anon_pages, entry, locale, viewport)
            pages.append(("detail", view, view.DETAIL_TEXT_SELECTORS,
                          detail.get("title", "") + " " + detail.get("desc_text", "")))
            for surface, page_view, selectors, shown in pages:
                report = page_view.overflow_report(selectors)
                png = page_view.evidence(f"{tc_id}_{label}_{surface}_{locale}_{name}")
                own = [r for r in report if r["sel"] != "document"
                       and needle[:30].strip() and needle[:30].strip() in (r.get("text") or "")]
                doc = [r for r in report if r["sel"] == "document"][0]
                issues = [r for r in own if r["clipped"] or r["beyond_viewport"]]
                normalized = re.sub(r"\s+", "", shown)
                full = re.sub(r"\s+", "", needle) in normalized
                entry_f = {"tc": tc_id, "field": label, "surface": surface, "locale": locale, "viewport": name,
                           "full_text_rendered": full, "own_element_issues": issues,
                           "page_hscroll": doc["page_hscroll"], "scrollWidth": doc["scrollWidth"],
                           "vw": doc["vw"], "screenshot": png}
                findings.append(entry_f)
                _log(CHARLIMIT_LOG, entry_f, f"layout {surface} {locale} {name}")
    return findings


# ===========================================================================
# Video ID (143041)
# ===========================================================================
@AUTH_FREE_PAGE
@allure.epic("Insights & Media")
@allure.feature("Video Gallery — Control Panel")
@allure.story("Video Record fields")
@allure.title("A new Video Record's Video ID auto-generates a unique value")
@pytest.mark.tc_143041
def test_video_id_auto_generates_unique_value(page, disposable):
    # Azure TC 143041 | the record id = Liferay entry id + external reference code
    admin = _editor(page)
    first = _create(admin, disposable, _data("143041", "First", **{K_VIDEO_STATUS: "Draft"}), "143041", draft=True)
    second = _create(admin, disposable, _data("143041", "Second", **{K_VIDEO_STATUS: "Draft"}), "143041", draft=True)
    admin.open_create_form_en()
    labels = admin.form_field_labels()
    _attach("ids", {"first": first, "second": second, "form labels": labels})
    assert first.entry_id and second.entry_id and first.code and second.code
    assert first.entry_id != second.entry_id and first.code != second.code, (
        f"the two records share an id: {first} / {second}")
    assert re.fullmatch(r"\d+", first.entry_id) and re.fullmatch(r"\d+", second.entry_id)
    assert not any(re.fullmatch(r"\s*video id\s*\*?\s*", lab, re.I) for lab in labels), (
        f"a user-editable 'Video ID' field is on the create form: {labels}")


# ===========================================================================
# Video Title (143042-143045)
# ===========================================================================
@AUTH_FREE_PAGE
@allure.epic("Insights & Media")
@allure.feature("Video Gallery — Control Panel")
@allure.story("Video Title")
@allure.title("The Video Title field accepts a valid EN/AR value within 200 characters")
@pytest.mark.tc_143042
def test_video_title_valid_value_accepted(page, disposable, anon_pages):
    # Azure TC 143042
    admin = _editor(page)
    data = _data("143042", "Qatar Chamber Annual Forum Highlights",
                 **{f"{K_TITLE}_ar": f"{VC_PREFIX}143042-{STAMP} أبرز فعاليات المنتدى السنوي لغرفة قطر"})
    entry = _create(admin, disposable, data, "143042")
    _, card = _published_and_public(admin, entry, anon_pages)
    assert card["title"] == data[K_TITLE], f"EN card title {card['title']!r} != {data[K_TITLE]!r}"
    _, detail = _public_detail(anon_pages, entry)
    assert detail["title"] == data[K_TITLE], f"EN Details title {detail['title']!r}"
    _, card_ar = _public_card(anon_pages, entry, "ar")
    assert card_ar["title"] == data[f"{K_TITLE}_ar"], f"AR card title {card_ar['title']!r}"
    _, detail_ar = _public_detail(anon_pages, entry, "ar")
    assert detail_ar["title"] == data[f"{K_TITLE}_ar"], f"AR Details title {detail_ar['title']!r}"


@AUTH_FREE_PAGE
@allure.epic("Insights & Media")
@allure.feature("Video Gallery — Control Panel")
@allure.story("Video Title")
@allure.title("The Video Title field rejects an empty value")
@pytest.mark.tc_143043
def test_video_title_empty_rejected(page, disposable):
    # Azure TC 143043 | identity carried by the Arabic title marker
    admin = _editor(page)
    data = _data("143043", **{K_TITLE: "", f"{K_TITLE}_ar": f"{VC_PREFIX}143043-{STAMP} عنوان عربي"})
    _assert_blocked(admin, disposable, data, "143043", "an empty Video Title EN", r"videoTitle|Video Title",
                    "a required-field validation error", r"required|complete|fill")


@AUTH_FREE_PAGE
@allure.epic("Insights & Media")
@allure.feature("Video Gallery — Control Panel")
@allure.story("Video Title")
@allure.title("The Video Title field enforces the 200-character maximum")
@pytest.mark.tc_143044
def test_video_title_200_character_maximum(page, disposable, anon_pages):
    # Azure TC 143044 | + rule 6 public layout check on the 200-character title
    admin = _editor(page)
    head = f"{VC_PREFIX}143044-{STAMP} "
    words = "Qatar Chamber hosts business delegation to discuss trade investment and partnership opportunities "
    ar_words = "غرفة قطر تستضيف وفدا تجاريا لبحث فرص التجارة والاستثمار والشراكة "
    title_200 = (head + words * 4)[:199] + "Z"  # no trailing space
    ar_200 = (head + ar_words * 5)[:199] + "ة"
    assert len(title_200) == 200 and len(ar_200) == 200
    entry = _create(admin, disposable, _data("143044", **{K_TITLE: title_200, f"{K_TITLE}_ar": ar_200}), "143044")
    admin.open_entry_en(entry.code)
    stored = admin.text_value(K_TITLE)
    assert stored == title_200, f"the 200-character title was stored as {len(stored)} chars: {stored!r}"
    _wait_published(admin, entry)
    _require_active_status(admin, entry)
    layout = _layout_sweep(anon_pages, entry, "143044", "title200", title_200, ar_200)

    title_201 = (head + "Over limit " + words * 4)[:200] + "X"
    data_201 = _data("143044", **{K_TITLE: title_201, f"{K_TITLE}_ar": f"{head}عنوان زائد"})
    ids_before = admin.snapshot_ids()
    result, typed = {}, ""

    def _type_201(a):
        a.type_into(K_TITLE, title_201)
        result["typed_value"] = a.text_value(K_TITLE)

    try:
        result.update(_attempt(admin, data_201, "143044", "title_201", before_save=_type_201))
        typed = result.get("typed_value", "")
    finally:
        created = None
        for candidate in {title_201, typed}:
            if candidate and candidate.startswith(VC_PREFIX) and created is None:
                try:
                    created = admin.identify_created(candidate, ids_before)
                    if created:
                        disposable.track(created)
                except Exception as exc:  # noqa: BLE001
                    allure.attach(repr(exc), name="201 registration failed")
    _attach("201-character attempt", result)
    # the listing card title is clamped to 2 lines with an ellipsis BY DESIGN (every real card
    # does the same) — only an un-clamped clip, overflow or horizontal scroll is a finding
    def _real_issues(f):
        return [i for i in f["own_element_issues"]
                if i["beyond_viewport"] or not (f["surface"] == "listing" and i.get("line_clamp") not in (None, "none"))]

    layout_bad = [f for f in layout if not f["full_text_rendered"] or _real_issues(f) or f["page_hscroll"]]
    _attach("rule-6 layout findings (bad)", layout_bad)
    if created is not None:
        admin.open_entry_en(created.code)
        stored_201 = admin.text_value(K_TITLE)
        if len(stored_201) > 200:
            pytest.fail(f"PRODUCT: a 201-character Video Title was accepted and stored ({len(stored_201)} chars, "
                        f"entry id {created.entry_id}); expected save blocked or truncated with a max-length "
                        f"indication. Messages {result.get('editbar')}; screenshot {result.get('screenshot')}")
    assert len(typed) <= 200 or (not result.get("went_through") and result.get("refused")), (
        f"201 characters: neither blocked nor truncated: {result}")
    assert not layout_bad, f"rule 6 — the 200-character title does not render cleanly: {layout_bad}"


@AUTH_FREE_PAGE
@allure.epic("Insights & Media")
@allure.feature("Video Gallery — Control Panel")
@allure.story("Video Title")
@allure.title("The Video Title field rejects a whitespace-only value")
@pytest.mark.tc_143045
def test_video_title_whitespace_only_rejected(page, disposable):
    # Azure TC 143045
    admin = _editor(page)
    data = _data("143045", **{K_TITLE: "     ", f"{K_TITLE}_ar": f"{VC_PREFIX}143045-{STAMP} مسافات"})
    _assert_blocked(admin, disposable, data, "143045", "a whitespace-only Video Title EN", r"videoTitle|Video Title",
                    "save blocked as equivalent to empty", r"required|complete|fill|empty|blank")


# ===========================================================================
# Video Category (143046-143047)
# ===========================================================================
@AUTH_FREE_PAGE
@allure.epic("Insights & Media")
@allure.feature("Video Gallery — Control Panel")
@allure.story("Video Category")
@allure.title("Video Category accepts a valid selection from published categories")
@pytest.mark.tc_143046
def test_video_category_valid_selection(page, disposable, anon_pages, browser):
    # Azure TC 143046
    admin = _editor(page)
    admin.open_create_form_en()
    options = admin.picklist_options(K_CATEGORY_REL)
    cat_ctx = new_context(browser, use_auth_state=False)
    try:
        from cms.pages.video_gallery.video_record_admin_page import VideoGalleryAdminPage  # noqa: PLC0415
        cats = VideoGalleryAdminPage(cat_ctx.new_page(), "video-category", VC_PREFIX)
        cats.TITLE_KEY = "categoryName"
        assert cats.login_as_role(ROLE_EDITOR) == "ok"
        cats.open_list_all()
        categories = [{"title": r["title"], "status": r["status"]} for r in cats.list_rows()]
    finally:
        cat_ctx.close()
    _attach("category options vs Video Category records", {"options": options, "records": categories})
    published = {c["title"] for c in categories if "PUBLISHED" in c["status"].upper()
                 and "UNPUBLISHED" not in c["status"].upper()}
    assert "Institutional" in options, f"'Institutional' is not selectable: {options}"
    not_published = [o for o in options if o not in published]
    entry = _create(admin, disposable, _data("143046", "Category Institutional",
                                             **{K_CATEGORY_REL: "Institutional"}), "143046")
    admin.open_entry_en(entry.code)
    assert admin.picklist_value(K_CATEGORY_REL), "no Video Category stored"
    _, card = _published_and_public(admin, entry, anon_pages)
    assert card["tag"] == "Institutional", f"card chip shows {card['tag']!r}, not 'Institutional'"
    assert not not_published, f"PRODUCT: non-published categories are selectable: {not_published} ({categories})"


@AUTH_FREE_PAGE
@allure.epic("Insights & Media")
@allure.feature("Video Gallery — Control Panel")
@allure.story("Video Category")
@allure.title("Video Category is blocked when not selected")
@pytest.mark.tc_143047
def test_video_category_required(page, disposable):
    # Azure TC 143047
    admin = _editor(page)
    data = _data("143047", "No Category")
    data.pop(K_CATEGORY_REL)
    _assert_blocked(admin, disposable, data, "143047", "no Video Category", r"videoCategory|Video Category",
                    "a required-field validation error", r"required|complete|select")


# ===========================================================================
# Video Source Type (143048-143049)
# ===========================================================================
@AUTH_FREE_PAGE
@allure.epic("Insights & Media")
@allure.feature("Video Gallery — Control Panel")
@allure.story("Video Source Type")
@allure.title("Video Source Type accepts one selection and reveals its conditional field")
@pytest.mark.tc_143048
def test_video_source_type_reveals_conditional_field(page):
    # Azure TC 143048 | unsaved form only
    admin = _editor(page)
    admin.open_create_form_en()
    options = admin.picklist_options(K_SOURCE_TYPE)
    before = admin.source_dependent_states()
    admin.pick(K_SOURCE_TYPE, SOURCE_EXTERNAL_URL)
    after = admin.source_dependent_states()
    selected = admin.picklist_label(K_SOURCE_TYPE)
    png = admin.evidence("143048_source_external_url")
    _attach("source-dependent fields", {"options": options, "before": before, "after_external_url": after,
                                        "selected": selected, "screenshot": png})
    assert options == [SOURCE_FLICKR, SOURCE_EXTERNAL_URL, SOURCE_DIRECT_UPLOAD], f"options {options}"
    assert selected == SOURCE_EXTERNAL_URL, f"selected {selected!r}"
    problems = []
    if not after[K_VIDEO_URL]["visible"]:
        problems.append("Video URL is not shown")
    if not after[K_VIDEO_URL]["required"]:
        problems.append("Video URL is not marked required")
    for key in (K_FLICKR_VIDEO_ID, K_VIDEO_FILE):
        if after[key]["visible"] and not after[key]["disabled"] and not after[key]["readonly"]:
            problems.append(f"{after[key].get('label') or key} is still shown and editable")
    assert not problems, f"PRODUCT: with Source Type = External URL: {problems}; screenshot {png}"


@AUTH_FREE_PAGE
@allure.epic("Insights & Media")
@allure.feature("Video Gallery — Control Panel")
@allure.story("Video Source Type")
@allure.title("Video Source Type is blocked when not selected")
@pytest.mark.tc_143049
def test_video_source_type_required(page, disposable):
    # Azure TC 143049
    admin = _editor(page)
    data = _data("143049", "No Source Type")
    data.pop(K_SOURCE_TYPE)
    hint = {}

    def _note_ids(a):
        hint["prefix"] = a._picklist_prefix(K_SOURCE_TYPE)

    result = _assert_blocked(admin, disposable, data, "143049", "no Video Source Type", r"select-from-list-input",
                             "a required-field validation error", r"required|complete|select|fill",
                             before_save=_note_ids)
    invalid = result["evidence"]["invalid_fields"]
    assert any(i.startswith(hint["prefix"]) for i in invalid), (
        f"the native refusal is not on the Video Source Type control ({hint['prefix']}): {invalid}")


# ===========================================================================
# Flickr Video ID / Flickr Source Folder (143050, 143070) — read-only
# ===========================================================================
def _scan_existing_records(admin) -> list[dict]:
    admin.open_list_all()
    rows = admin.list_rows()
    found = []
    for row in rows:
        admin.open_entry_en(row["code"])
        found.append({"code": row["code"], "title": row["title"][:60], "status": row["status"],
                      "source": admin.picklist_label(K_SOURCE_TYPE),
                      "flickr_video_id": admin.text_value(K_FLICKR_VIDEO_ID),
                      "flickr_video_rel": admin.picklist_label(K_FLICKR_VIDEO_REL),
                      "flickr_source_folder": admin.text_value(K_FLICKR_SOURCE_FOLDER),
                      "flickr_folder_rel": admin.picklist_label(K_FLICKR_FOLDER_REL),
                      "flickr_id_state": admin.field_state(K_FLICKR_VIDEO_ID),
                      "folder_state": admin.field_state(K_FLICKR_SOURCE_FOLDER)})
    return found


@AUTH_FREE_PAGE
@allure.epic("Insights & Media")
@allure.feature("Video Gallery — Control Panel")
@allure.story("Flickr Video ID")
@allure.title("The Flickr Video ID auto-populates and is stored on the record after import")
@pytest.mark.tc_143050
def test_flickr_video_id_populated_after_import(page):
    # Azure TC 143050 | NO import is triggered (rule 8) — read-only inspection
    admin = _editor(page)
    records = _scan_existing_records(admin)
    _attach("existing records (read-only)", records)
    imported = [r for r in records if r["source"] == SOURCE_FLICKR and (r["flickr_video_id"] or r["flickr_video_rel"])]
    if not imported:
        pytest.skip("BLOCKED: no Flickr-imported Video Record exists (Flickr-sourced records "
                    f"{[r['code'] for r in records if r['source'] == SOURCE_FLICKR]} have an empty Flickr Video ID; "
                    "the 'Flickr Video' relationship has 0 options) and the import is not triggered "
                    "(Administrator-only, would pull shared real data). Observed: Flickr Video ID is an "
                    f"editable text input (state {records[0]['flickr_id_state'] if records else 'n/a'}).")
    for rec in imported:
        assert rec["flickr_id_state"]["readonly"] or rec["flickr_id_state"]["disabled"], (
            f"PRODUCT: Flickr Video ID is editable on imported record {rec['code']}: {rec['flickr_id_state']}")


@AUTH_FREE_PAGE
@allure.epic("Insights & Media")
@allure.feature("Video Gallery — Control Panel")
@allure.story("Flickr Source Folder")
@allure.title("The Flickr Source Folder populates for Flickr-sourced videos and stays blank otherwise")
@pytest.mark.tc_143070
def test_flickr_source_folder_reference(page):
    # Azure TC 143070 | read-only inspection of existing records
    admin = _editor(page)
    records = _scan_existing_records(admin)
    _attach("existing records (read-only)", records)
    direct = [r for r in records if r["source"] == SOURCE_DIRECT_UPLOAD]
    assert direct, "no Direct-Upload record exists to inspect"
    filled_direct = [r for r in direct if r["flickr_source_folder"] or r["flickr_folder_rel"]]
    assert not filled_direct, f"PRODUCT: Direct-Upload records carry a Flickr Source Folder: {filled_direct}"
    imported = [r for r in records if r["source"] == SOURCE_FLICKR and (r["flickr_video_id"] or r["flickr_video_rel"])]
    if not imported:
        pytest.skip("BLOCKED (step 1): no Flickr-IMPORTED Video Record exists — the Flickr-sourced records "
                    f"{[(r['code'], r['flickr_source_folder'], r['flickr_folder_rel']) for r in records if r['source'] == SOURCE_FLICKR]} "
                    "are seeded rows with an empty Flickr Video ID and an empty Flickr Source Folder; the "
                    "import is not triggered (rule 8). Step 2 (Direct Upload record blank) PASSED.")
    missing = [r for r in imported if not (r["flickr_source_folder"] or r["flickr_folder_rel"])]
    assert not missing, f"PRODUCT: imported Flickr records without a Flickr Source Folder: {missing}"


# ===========================================================================
# Video URL (143051-143053)
# ===========================================================================
@AUTH_FREE_PAGE
@allure.epic("Insights & Media")
@allure.feature("Video Gallery — Control Panel")
@allure.story("Video URL")
@allure.title("Video URL accepts a valid YouTube URL when Source = External URL")
@pytest.mark.tc_143051
def test_video_url_valid_youtube_accepted(page, disposable, anon_pages):
    # Azure TC 143051 | URL as written: https://www.youtube.com/watch?v=abc123
    admin = _editor(page)
    url = "https://www.youtube.com/watch?v=abc123"
    entry = _create(admin, disposable, _data("143051", "YouTube URL", **{K_VIDEO_URL: url}), "143051")
    admin.open_entry_en(entry.code)
    assert admin.text_value(K_VIDEO_URL) == url, f"stored URL {admin.text_value(K_VIDEO_URL)!r}"
    _wait_published(admin, entry)
    _require_active_status(admin, entry)
    view, _ = _public_detail(anon_pages, entry)
    source = view.play_and_read_source()
    png = view.evidence("143051_detail_after_play")
    _attach("playback source", {**source, "screenshot": png})
    assert "abc123" in source["iframe_src"], f"the player does not play the stored URL: {source}"


@AUTH_FREE_PAGE
@allure.epic("Insights & Media")
@allure.feature("Video Gallery — Control Panel")
@allure.story("Video URL")
@allure.title("Video URL rejects a non-YouTube/Vimeo URL")
@pytest.mark.tc_143052
def test_video_url_non_youtube_vimeo_rejected(page, disposable):
    # Azure TC 143052
    admin = _editor(page)
    data = _data("143052", "Non YouTube URL", **{K_VIDEO_URL: "https://example.com/video.mp4"})
    _assert_blocked(admin, disposable, data, "143052", "a non-YouTube/Vimeo Video URL", r"videoUrl|Video URL|YouTube or Vimeo URL",
                    "must be a valid YouTube or Vimeo URL", r"youtube|vimeo")


@AUTH_FREE_PAGE
@allure.epic("Insights & Media")
@allure.feature("Video Gallery — Control Panel")
@allure.story("Video URL")
@allure.title("Video URL is blocked when left empty while Source = External URL")
@pytest.mark.tc_143053
def test_video_url_empty_rejected(page, disposable):
    # Azure TC 143053
    admin = _editor(page)
    data = _data("143053", "Empty URL", **{K_VIDEO_URL: ""})
    _assert_blocked(admin, disposable, data, "143053", "an empty Video URL", r"videoUrl|Video URL|video source",
                    "a required-field error naming Video URL", r"Video URL.{0,40}required|required.{0,40}Video URL")


# ===========================================================================
# Video File (143054-143056)
# ===========================================================================
@AUTH_FREE_PAGE
@allure.epic("Insights & Media")
@allure.feature("Video Gallery — Control Panel")
@allure.story("Video File")
@allure.title("Video File accepts a valid MP4 upload when Source = Direct Upload")
@pytest.mark.tc_143054
def test_video_file_valid_mp4_accepted(page, disposable, anon_pages):
    # Azure TC 143054
    admin = _editor(page)
    data = _data("143054", "Direct Upload MP4", **{K_SOURCE_TYPE: SOURCE_DIRECT_UPLOAD, K_VIDEO_URL: None,
                                                    K_VIDEO_FILE: VC_CLIP_MP4,
                                                    f"{K_VIDEO_FILE}_stem": "vc_qctest_clip_143054"})
    entry = _create(admin, disposable, data, "143054")
    admin.open_entry_en(entry.code)
    stored = admin.stored_file_name(K_VIDEO_FILE)
    _attach("stored video file", {"stored": stored, "uploaded_as": data.get(f"{K_VIDEO_FILE}_uploaded_as"),
                                  "block": admin.upload_block_text(K_VIDEO_FILE)})
    assert stored and os.path.splitext(data[f"{K_VIDEO_FILE}_uploaded_as"])[0] in stored, (
        f"the MP4 is not the stored Video File: {admin.upload_block_text(K_VIDEO_FILE)!r}")
    _wait_published(admin, entry)
    _require_active_status(admin, entry)
    view, _ = _public_detail(anon_pages, entry)
    source = view.play_and_read_source()
    png = view.evidence("143054_detail_after_play")
    _attach("playback source", {**source, "screenshot": png})
    assert source["video_src"] and not source["error"], f"the uploaded MP4 is not the playback source: {source}"


@AUTH_FREE_PAGE
@allure.epic("Insights & Media")
@allure.feature("Video Gallery — Control Panel")
@allure.story("Video File")
@allure.title("Video File rejects an unsupported (AVI) format")
@pytest.mark.tc_143055
def test_video_file_unsupported_format_rejected(page, disposable):
    # Azure TC 143055
    admin = _editor(page)
    data = _data("143055", "AVI Upload", **{K_SOURCE_TYPE: SOURCE_DIRECT_UPLOAD, K_VIDEO_URL: None})
    upload = {}

    def _try_avi(a):
        upload.update(a.attempt_upload(K_VIDEO_FILE, VC_CLIP_AVI, "vc_qctest_clip_143055"))

    try:
        result = _assert_blocked(admin, disposable, data, "143055", "an AVI Video File",
                                 r"videoFile|Video File|mp4|mov|avi|extension|type|video source", before_save=_try_avi)
    finally:
        _attach("AVI upload attempt", upload)
    assert not upload.get("attached"), (
        f"PRODUCT: the AVI was accepted and attached to Video File ({upload.get('field_text')!r}); "
        f"save blocked only afterwards: {result.get('messages')}")


@AUTH_FREE_PAGE
@allure.epic("Insights & Media")
@allure.feature("Video Gallery — Control Panel")
@allure.story("Video File")
@allure.title("Video File is blocked when left empty while Source = Direct Upload")
@pytest.mark.tc_143056
def test_video_file_empty_rejected(page, disposable):
    # Azure TC 143056
    admin = _editor(page)
    data = _data("143056", "No File", **{K_SOURCE_TYPE: SOURCE_DIRECT_UPLOAD, K_VIDEO_URL: None})
    _assert_blocked(admin, disposable, data, "143056", "an empty Video File", r"videoFile|Video File|video source",
                    "a required-field error naming Video File", r"Video File.{0,40}required|required.{0,40}Video File")


# ===========================================================================
# Video Thumbnail (143057-143058)
# ===========================================================================
@AUTH_FREE_PAGE
@allure.epic("Insights & Media")
@allure.feature("Video Gallery — Control Panel")
@allure.story("Video Thumbnail")
@allure.title("Video Thumbnail accepts a valid PNG upload")
@pytest.mark.tc_143057
def test_video_thumbnail_valid_png_accepted(page, disposable, anon_pages):
    # Azure TC 143057 | one non-localized thumbnail field
    admin = _editor(page)
    data = _data("143057", "PNG Thumbnail")
    entry = _create(admin, disposable, data, "143057")
    admin.open_entry_en(entry.code)
    stored = admin.stored_file_name(K_THUMBNAIL)
    assert stored and os.path.splitext(data[f"{K_THUMBNAIL}_uploaded_as"])[0] in stored, (
        f"the PNG is not the stored thumbnail: {admin.upload_block_text(K_THUMBNAIL)!r}")
    view, card = _published_and_public(admin, entry, anon_pages)
    loaded = view.card_thumb_loaded(entry.code)
    view_d, detail = _public_detail(anon_pages, entry)
    view_d.wait_images_settled(".qc-vdt-poster-img")
    detail = view_d.detail()
    png = view_d.evidence("143057_detail_poster")
    _attach("thumbnail delivery", {"card": card, "card_loaded": loaded, "detail": detail, "screenshot": png})
    assert card["thumb"] and loaded and not card["fallback"], f"the card does not show the thumbnail: {card}"
    assert detail["poster_src"] and detail["poster_loaded"], f"the player poster is not the thumbnail: {detail}"


@AUTH_FREE_PAGE
@allure.epic("Insights & Media")
@allure.feature("Video Gallery — Control Panel")
@allure.story("Video Thumbnail")
@allure.title("Video Thumbnail rejects an unsupported (BMP) file format")
@pytest.mark.tc_143058
def test_video_thumbnail_unsupported_format_rejected(page):
    # Azure TC 143058 | unsaved form only
    admin = _editor(page)
    admin.open_create_form_en()
    result = admin.attempt_upload(K_THUMBNAIL, VC_THUMBNAIL_BMP, "vc_qctest_thumb_143058")
    png = admin.evidence("143058_bmp_thumbnail_attempt")
    _attach("BMP upload attempt", {**result, "screenshot": png})
    assert not result["attached"], f"PRODUCT: a BMP was accepted as the Video Thumbnail: {result}"
    shown = " ".join(result.get("errors", [])) + " " + " ".join(result.get("field_errors", [])) + " " + \
        result.get("picker_text", "")
    expected = "Unsupported file type. Accepted formats: JPG, JPEG, PNG."
    assert result["success"] is not True or result["errors"], f"no rejection evidence: {result}"
    if expected not in shown:
        _record_wording("143058", "Video Thumbnail BMP", expected, shown.strip()[:400], png)


# ===========================================================================
# Duration (143059-143061)
# ===========================================================================
@AUTH_FREE_PAGE
@allure.epic("Insights & Media")
@allure.feature("Video Gallery — Control Panel")
@allure.story("Duration")
@allure.title("Duration accepts a valid mm:ss value and displays as a badge")
@pytest.mark.tc_143059
def test_duration_valid_mmss_displayed_as_badge(page, disposable, anon_pages):
    # Azure TC 143059 | own record 08:31 -> edited to 12:45
    admin = _editor(page)
    entry = _create(admin, disposable, _data("143059", "Duration", **{K_DURATION: "08:31"}), "143059")
    _wait_published(admin, entry)
    admin.open_entry_en(entry.code)
    assert admin.text_value(K_DURATION) == "08:31"
    admin.fill_en(K_DURATION, "12:45")
    assert admin.text_value(K_DURATION) == "12:45"
    _pinned(admin)
    admin.click_publish()
    png = admin.evidence("143059_edit_publish")
    assert admin.save_went_through(), f"the edit to 12:45 did not save: {admin.refusal_evidence()} | {png}"
    admin.open_entry_en(entry.code)
    assert admin.text_value(K_DURATION) == "12:45", f"stored {admin.text_value(K_DURATION)!r}"
    _, card = _published_and_public(admin, entry, anon_pages)
    _, detail = _public_detail(anon_pages, entry)
    assert card["duration"] == "12:45", f"card badge {card['duration']!r}"
    assert detail["duration"] == "12:45", f"player badge {detail['duration']!r}"


@AUTH_FREE_PAGE
@allure.epic("Insights & Media")
@allure.feature("Video Gallery — Control Panel")
@allure.story("Duration")
@allure.title("Duration rejects an invalid mm:ss format (8:99)")
@pytest.mark.tc_143060
def test_duration_invalid_format_rejected(page, disposable):
    # Azure TC 143060
    admin = _editor(page)
    _assert_blocked(admin, disposable, _data("143060", "Bad Duration", **{K_DURATION: "8:99"}), "143060",
                    "Duration 8:99", r"duration", "seconds must be 00–59", r"00.?59|mm:ss|format|seconds")


@AUTH_FREE_PAGE
@allure.epic("Insights & Media")
@allure.feature("Video Gallery — Control Panel")
@allure.story("Duration")
@allure.title("Duration is blocked when left empty")
@pytest.mark.tc_143061
def test_duration_empty_rejected(page, disposable):
    # Azure TC 143061
    admin = _editor(page)
    _assert_blocked(admin, disposable, _data("143061", "No Duration", **{K_DURATION: ""}), "143061",
                    "an empty Duration", r"duration", "a required-field validation error", r"required|complete")


# ===========================================================================
# Video Description (143062-143065)
# ===========================================================================
def _text_of_length(head: str, n: int, filler: str) -> str:
    body = head + filler * n
    return body[:n]


@AUTH_FREE_PAGE
@allure.epic("Insights & Media")
@allure.feature("Video Gallery — Control Panel")
@allure.story("Video Description")
@allure.title("Video Description accepts valid multi-paragraph text within 2000 characters")
@pytest.mark.tc_143062
def test_video_description_multi_paragraph_accepted(page, disposable, anon_pages):
    # Azure TC 143062 | 300 characters, three paragraphs
    admin = _editor(page)
    p1 = "Qatar Chamber hosted a business delegation to discuss trade, investment and partnership opportunities."
    p2 = "The meeting reviewed sectors such as logistics, food security, manufacturing and digital services."
    p3 = "Both sides agreed to follow up with B2B meetings and a joint business forum later this year."
    text = f"{p1}\n\n{p2}\n\n{p3}"
    text = (text + " " + "x" * 300)[:300] if len(text) < 300 else text[:300]
    entry = _create(admin, disposable, _data("143062", "Description", **{K_DESCRIPTION: text}), "143062")
    admin.open_entry_en(entry.code)
    raw = admin.raw_description()
    _wait_published(admin, entry)
    _require_active_status(admin, entry)
    view, detail = _public_detail(anon_pages, entry)
    png = view.evidence("143062_detail_description")
    _attach("description", {"typed": text, "stored_raw": raw, "detail": detail, "screenshot": png})
    shown = re.sub(r"\s+", " ", detail["desc_text"]).strip()
    for part in (p1, p2):
        assert part in shown, f"paragraph missing on the Details page: {part!r} in {shown!r}"
    assert detail["desc_paragraphs"] >= 3 or detail["desc_text"].count("\n") >= 2, (
        f"PRODUCT: paragraph breaks are not preserved on the Details page: {detail['desc_html'][:600]!r}; {png}")


@AUTH_FREE_PAGE
@allure.epic("Insights & Media")
@allure.feature("Video Gallery — Control Panel")
@allure.story("Video Description")
@allure.title("Video Description accepts exactly 2000 characters")
@pytest.mark.tc_143063
def test_video_description_exactly_2000_accepted(page, disposable, anon_pages):
    # Azure TC 143063 | + rule 6 public layout check (detail EN/AR, 1920/390)
    admin = _editor(page)
    en = _text_of_length(f"{VC_PREFIX}143063 description start. ", 2000, "Qatar Chamber video description. ")
    ar = _text_of_length(f"{VC_PREFIX}143063 بداية الوصف. ", 2000, "وصف فيديو غرفة قطر. ")
    assert len(en) == 2000 and len(ar) == 2000
    entry = _create(admin, disposable, _data("143063", "Description 2000",
                                             **{K_DESCRIPTION: en, f"{K_DESCRIPTION}_ar": ar}), "143063")
    admin.open_entry_en(entry.code)
    raw = admin.raw_description()
    stored = re.sub(r"<[^>]+>", "", raw)
    _attach("stored 2000", {"stored_len": len(stored), "raw_len": len(raw), "raw_head": raw[:120]})
    assert stored.strip() == en.strip(), f"the 2000-character text was not stored in full ({len(stored)} chars)"
    _wait_published(admin, entry)
    _require_active_status(admin, entry)
    layout = _layout_sweep(anon_pages, entry, "143063", "desc2000", en, ar, listing=True)
    bad = [f for f in layout if (f["surface"] == "detail" and not f["full_text_rendered"])
           or f["own_element_issues"] or f["page_hscroll"]]
    assert not bad, f"rule 6 — the 2000-character description does not render cleanly: {bad}"


@AUTH_FREE_PAGE
@allure.epic("Insights & Media")
@allure.feature("Video Gallery — Control Panel")
@allure.story("Video Description")
@allure.title("Video Description rejects content exceeding 2000 characters")
@pytest.mark.tc_143064
def test_video_description_over_2000_rejected(page, disposable):
    # Azure TC 143064
    admin = _editor(page)
    text = _text_of_length(f"{VC_PREFIX}143064 description start. ", 2001, "Qatar Chamber video description. ")
    data = _data("143064", "Description 2001", **{K_DESCRIPTION: text})
    ids_before = admin.snapshot_ids()
    result = {}
    try:
        result = _attempt(admin, data, "143064", "desc_2001",
                          before_save=lambda a: result.setdefault("typed_len", len(a.raw_description())))
    finally:
        entry = _register(admin, disposable, data, ids_before)
    _attach("2001-character attempt", result)
    if entry is not None:
        admin.open_entry_en(entry.code)
        stored = re.sub(r"<[^>]+>", "", admin.raw_description())
        if len(stored.strip()) > 2000:
            pytest.fail(f"PRODUCT: a 2001-character Video Description was accepted and stored in full "
                        f"({len(stored.strip())} chars, entry id {entry.entry_id}); expected save blocked or "
                        f"truncated with a max-length indication. Messages {result.get('editbar')}; "
                        f"screenshot {result.get('screenshot')}")
        pytest.fail(f"PRODUCT: the 2001-character description was silently truncated to {len(stored.strip())} "
                    f"characters with no max-length indication: {result.get('editbar')}")
    assert not result.get("went_through") and result.get("refused"), f"neither blocked nor saved: {result}"
    if not re.search(r"2000|2,000|maximum|max|exceed|long", result["messages"], re.I):
        _record_wording("143064", "Video Description 2001", "a max-length validation indication",
                        result["messages"], result["screenshot"])


@AUTH_FREE_PAGE
@allure.epic("Insights & Media")
@allure.feature("Video Gallery — Control Panel")
@allure.story("Video Description")
@allure.title("Video Description can be left empty")
@pytest.mark.tc_143065
def test_video_description_empty_allowed(page, disposable, anon_pages):
    # Azure TC 143065
    admin = _editor(page)
    data = _data("143065", "No Description", **{K_DESCRIPTION: None, f"{K_DESCRIPTION}_ar": None})
    entry = _create(admin, disposable, data, "143065")
    _, card = _published_and_public(admin, entry, anon_pages)
    assert card["title"] == data[K_TITLE]


# ===========================================================================
# Published Date (143066-143068)
# ===========================================================================
@AUTH_FREE_PAGE
@allure.epic("Insights & Media")
@allure.feature("Video Gallery — Control Panel")
@allure.story("Published Date")
@allure.title("Published Date accepts a valid date (2026-09-15)")
@pytest.mark.tc_143066
def test_published_date_valid_accepted(page, disposable, anon_pages):
    # Azure TC 143066
    admin = _editor(page)
    entry = _create(admin, disposable, _data("143066", "Published Date", **{K_PUBLISHED_DATE: "15/09/2026"}),
                    "143066")
    admin.open_entry_en(entry.code)
    assert admin.date_stored(K_PUBLISHED_DATE) == "2026-09-15", f"stored {admin.date_stored(K_PUBLISHED_DATE)!r}"
    view, card = _published_and_public(admin, entry, anon_pages)
    cards = view.cards()
    _, detail = _public_detail(anon_pages, entry)
    _attach("date delivery", {"card": card, "detail": detail, "order": [(c["title"][:40], c["meta"]) for c in cards],
                              "sort": view.sort_selected_label()})
    assert any("Sep 15, 2026" in m for m in card["meta"]), f"card date {card['meta']}"
    assert any("Sep 15, 2026" in m for m in detail["meta"]), f"Details date {detail['meta']}"

    def _parsed(meta: list) -> date | None:
        for m in meta:
            try:
                return datetime.strptime(m, "%b %d, %Y").date()
            except ValueError:
                continue
        return None

    dates = [_parsed(c["meta"]) for c in cards]
    dates = [d for d in dates if d]
    assert dates == sorted(dates, reverse=True), f"'Most Recent' order is not by Published Date: {dates}"


@AUTH_FREE_PAGE
@allure.epic("Insights & Media")
@allure.feature("Video Gallery — Control Panel")
@allure.story("Published Date")
@allure.title("Published Date is blocked when left empty")
@pytest.mark.tc_143067
def test_published_date_empty_rejected(page, disposable):
    # Azure TC 143067
    admin = _editor(page)
    _assert_blocked(admin, disposable, _data("143067", "No Date", **{K_PUBLISHED_DATE: ""}), "143067",
                    "an empty Published Date", r"publishedDate|Published Date", "a required-field validation error",
                    r"required|complete")


@AUTH_FREE_PAGE
@allure.epic("Insights & Media")
@allure.feature("Video Gallery — Control Panel")
@allure.story("Published Date")
@allure.title("Published Date rejects an invalid calendar date (31/02/2026)")
@pytest.mark.tc_143068
def test_published_date_invalid_rejected(page, disposable):
    # Azure TC 143068
    admin = _editor(page)
    seen = {}

    def _after(a):
        seen["box"] = a.date_text(K_PUBLISHED_DATE)
        seen["hidden"] = a.date_stored(K_PUBLISHED_DATE)

    result = _assert_blocked(admin, disposable, _data("143068", "Invalid Date", **{K_PUBLISHED_DATE: "31/02/2026"}),
                             "143068", "Published Date 31/02/2026", r"publishedDate|Published Date|date",
                             "a date-format/validity error", r"valid|date|format", before_save=_after)
    _attach("date field after typing 31/02/2026", {**seen, "messages": result["messages"]})


# ===========================================================================
# Video Status / Last Modified (143071-143072)
# ===========================================================================
@AUTH_FREE_PAGE
@allure.epic("Insights & Media")
@allure.feature("Video Gallery — Control Panel")
@allure.story("Video Status")
@allure.title("The Video Status dropdown persists each selectable value")
@pytest.mark.tc_143071
def test_video_status_persists_each_value(page, disposable):
    # Azure TC 143071 | own DRAFT record (Save as Draft) — never on the public site
    admin = _editor(page)
    entry = _create(admin, disposable, _data("143071", "Status", **{K_VIDEO_STATUS: "Draft"}), "143071", draft=True)
    admin.open_entry_en(entry.code)
    persisted = {"Draft": admin.picklist_label(K_VIDEO_STATUS)}
    options = admin.picklist_options(K_VIDEO_STATUS)
    for value in ("Published", "Unpublished"):
        admin.open_entry_en(entry.code)
        admin.pick(K_VIDEO_STATUS, value)
        _pinned(admin)
        admin.click_save_as_draft()
        assert admin.save_went_through(), f"saving Status={value} failed: {admin.refusal_evidence()}"
        admin.open_entry_en(entry.code)
        persisted[value] = admin.picklist_label(K_VIDEO_STATUS)
    admin.open_list_all()
    _attach("Video Status persistence", {"options": options, "persisted": persisted,
                                         "workflow": admin.row_status(entry)})
    assert options == ["Draft", "Published", "Unpublished"], f"options {options}"
    assert persisted == {"Draft": "Draft", "Published": "Published", "Unpublished": "Unpublished"}, persisted
    assert admin.row_status(entry) == STATUS_DRAFT


@AUTH_FREE_PAGE
@allure.epic("Insights & Media")
@allure.feature("Video Gallery — Control Panel")
@allure.story("Last Modified")
@allure.title("The video record's Last Modified date auto-populates and updates on edit")
@pytest.mark.tc_143072
def test_last_modified_updates_on_edit(page, disposable):
    # Azure TC 143072 | own DRAFT record
    admin = _editor(page)
    entry = _create(admin, disposable, _data("143072", "Modified", **{K_VIDEO_STATUS: "Draft"}), "143072", draft=True)
    admin.open_list_all()
    before = admin.row_modified_text(entry)
    assert before, "the Last Modified cell is empty for the new record"
    t_before = datetime.strptime(before, "%m/%d/%Y, %I:%M:%S %p")
    admin.open_entry_en(entry.code)
    admin.fill_en(K_DURATION, "04:44")
    _pinned(admin)
    admin.click_save_as_draft()
    assert admin.save_went_through(), f"the edit did not save: {admin.refusal_evidence()}"
    seen = {"after": ""}

    def _changed() -> bool:
        admin.open_list_all()
        seen["after"] = admin.row_modified_text(entry)
        return bool(seen["after"]) and seen["after"] != before

    try:
        wait_until(_changed, timeout=30.0, poll=3.0)
    except WaitTimeoutError:
        pass
    _attach("Last Modified", {"before": before, "after": seen["after"]})
    assert seen["after"] != before, f"PRODUCT: Last Modified did not change after the edit ({before!r})"
    assert datetime.strptime(seen["after"], "%m/%d/%Y, %I:%M:%S %p") > t_before


# ===========================================================================
# Missing Arabic content (143073)
# ===========================================================================
@AUTH_FREE_PAGE
@allure.epic("Insights & Media")
@allure.feature("Video Gallery — Control Panel")
@allure.story("Bilingual content")
@allure.title("Publishing is blocked when Arabic content is missing while English content is filled")
@pytest.mark.bilingual
@pytest.mark.regression
@pytest.mark.tc_143073
def test_publish_blocked_when_arabic_missing(page, disposable):
    # Azure TC 143073
    admin = _editor(page)
    data = _data("143073", "No Arabic", **{f"{K_TITLE}_ar": "", f"{K_DESCRIPTION}_ar": "",
                                           K_VIDEO_STATUS: "Draft"})
    ids_before = admin.snapshot_ids()
    draft = {}
    try:
        draft = _attempt(admin, data, "143073", "draft_no_arabic", draft=True)
    finally:
        entry = _register(admin, disposable, data, ids_before)
    _attach("Save as Draft without Arabic", draft)
    assert draft.get("went_through") and entry is not None, (
        f"step 1: the record did not save as Draft without the Arabic title: {draft.get('evidence')} | "
        f"{draft.get('messages')} | {draft.get('screenshot')}")
    admin.open_list_all()
    assert admin.row_status(entry) == STATUS_DRAFT, f"step 1: status {admin.row_status(entry)!r}"
    admin.open_entry_en(entry.code)
    admin.pick(K_VIDEO_STATUS, "Published")
    _pinned(admin)
    admin.click_publish()
    png = admin.evidence("143073_publish_without_arabic")
    publish = {"went_through": admin.save_went_through(), "refused": admin.save_was_refused(),
               "evidence": admin.refusal_evidence(), "messages": admin.all_messages_text(), "screenshot": png}
    _attach("Publish without Arabic", publish)
    admin.open_list_all()
    status = admin.row_status(entry)
    assert status != STATUS_PUBLISHED and not publish["went_through"], (
        f"PRODUCT: the record was published without Arabic content (status {status!r}, messages "
        f"{publish['messages']!r}); screenshot {png}")
    assert publish["refused"], f"Publish neither refused nor saved: {publish}"
    if "Arabic content is required." not in publish["messages"]:
        _record_wording("143073", "missing Arabic content", "Arabic content is required. / المحتوى بالعربية مطلوب.",
                        publish["messages"], png)
