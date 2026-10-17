"""
cms/tests/photo_gallery/test_photo_gallery_fields_control_panel.py —
Control_Panel field-validation cases for PBI 130714 ("QC - Insights & Media -
006 - Photo Gallery"), Azure plan 137724 / suite 140373 (Agent PB).

Objects (Object Authoring, read live 2026-10-05 as the Site Content Editor):
  manage-page-hero       "Photo Gallery Page Hero"      143147-143150
  manage-event-category  "Photo Gallery Event Category" 143151-143153
  manage-photo-album     "Photo Album"                   143157-143162
  (no object)            per-photo "Add Photo" panel     143164-143169 — BLOCKED

Pattern (PBI 130712 / 130952 editorial-workflow rework):
  - Every case runs as the Site Content Editor (156488) in an auth-free
    context; the signed-in userId is re-checked before every save. The
    Editor's submit button reads "Publish" (straight to Published). "Save" in
    a required/invalid-value case = Publish (Save as Draft skips required-field
    validation, standards.md), with an otherwise-valid form so the field under
    test is the only invalid one.
  - A rejection passes only with (a) refusal evidence pointing at the field and
    (b) NO record created / nothing changed. Wording-only differences (the block
    works, the message differs from the case) PASS and are logged as LOW wording
    findings in reports/evidence/130714_PB/findings.jsonl.
  - Validation runs on UNSAVED forms. Records that do get created are
    QCTEST-130714-PB-<tc>-<stamp> …, captured by list-id diff + form read-back,
    and removed in teardown only through PA's guarded delete_own_entry().
  - The Page Hero's two records are REAL (listing "Photo Albums", detail "Album
    details"). 143147/143148 edit the listing record's form, so the
    `hero_guard` fixture snapshots it (EN/AR title, Active, image name + bytes,
    row status) first and restores + re-verifies it in teardown.
  - Character-limit cases (143148, 143152, 143158; 143167 is blocked) also
    publish ONE record at the max length and read the logged-out listing +
    detail in EN and AR at 1920x1080 and 390x844 (rule 6). Layout findings are
    logged (findings.jsonl + screenshots); they do not change the CMS verdict.

Substitutions disclosed:
  - Case literals keep their text after a QCTEST-130714-PB-<tc>-<stamp> prefix
    ("Institutional", "Trade Summit 2026"); 143147 keeps "Photo Albums" (the
    real record's own EN title).
  - Display Order on records the test creates: 900 (100-grid, after the three
    real categories) — none of PB's cases names a value.
  - 143149 removes nothing from the real hero: the save attempt runs on the
    CREATE form (no image) with Active Status unticked; the real hero's
    Remove-file control and image are only read.
  - 143150: a 3.07 MB JPG (fixtures/pb_qctest_hero_3mb.jpg).
"""

from __future__ import annotations

import json
import os
import re
from datetime import date, datetime

import allure
import pytest

from cms.pages.components.object_authoring_page import STATUS_PUBLISHED
from cms.pages.photo_gallery.event_category_admin_page import (
    CATEGORY_NAME_LIMIT,
    K_CATEGORY_NAME,
    K_DISPLAY_ORDER,
    EventCategoryFieldsPB,
)
from cms.pages.photo_gallery.page_hero_admin_page import (
    HERO_LISTING_CODE,
    K_HERO_IMAGE,
    K_PAGE_TITLE,
    PAGE_TITLE_LIMIT,
    PageHeroAdminPage,
)
from cms.pages.photo_gallery.pb_form_support import (
    PB_EVIDENCE_DIR,
    PB_MSG_ARABIC_REQUIRED_AR,
    PB_MSG_ARABIC_REQUIRED_EN,
    PB_MSG_COVER_REQUIRED_AR,
    PB_MSG_COVER_REQUIRED_EN,
    PB_MSG_UNSUPPORTED_AR,
    PB_MSG_UNSUPPORTED_EN,
    PB_QCTEST_PREFIX,
    PB_ROLE_EDITOR,
    PB_ROLE_USER_IDS,
    PhotoGalleryPublicViewPB,
    dump,
    overflow_problems,
)
from cms.pages.photo_gallery.photo_album_admin_page import (
    ALBUM_TITLE_LIMIT,
    K_ALBUM_TITLE,
    K_COVER_IMAGE,
    K_EVENT_CATEGORY,
    K_PUBLISHED_DATE,
    PhotoAlbumFieldsPB,
)
from cms.pages.photo_gallery.album_photo_admin_page import (
    FRAMING_DEFAULT,
    K_PHOTO_DISPLAY_ORDER,
    K_PHOTO_TITLE,
    K_THUMBNAIL_FRAMING,
    MSG_UNSUPPORTED_TYPE,
    PHOTO_TITLE_LIMIT,
    unsupported_type_shown,
)
from cms.tests.photo_gallery.photo_support import (
    PHOTO_BMP,
    PHOTO_JPG,
    PhotoRegistry,
    add_photo,
    cleanup,
    photo_data,
    publish_album,
)
from core.web.browser import new_context

pytestmark = [pytest.mark.control_panel, pytest.mark.media, pytest.mark.pbi_130714,
              pytest.mark.functional_low, pytest.mark.xdist_group("photo_gallery_cms_fields_pb")]

AUTH_FREE_PAGE = pytest.mark.parametrize("page", [{"auth": False}], indirect=True)
FIXTURES = os.path.join(os.path.dirname(__file__), "fixtures")
COVER_JPG = os.path.join(FIXTURES, "pb_qctest_cover.jpg")
COVER_GIF = os.path.join(FIXTURES, "pb_qctest_cover.gif")
HERO_3MB_JPG = os.path.join(FIXTURES, "pb_qctest_hero_3mb.jpg")
STAMP = datetime.now().strftime("%m%d%H%M%S")
TODAY_DMY = date.today().strftime("%d/%m/%Y")
REAL_CATEGORY = "Institutional"
# Since ADO 148169 (2026-10-12) an album needs no photo source, and choosing a
# Flickr Source Folder IMPORTS that folder's photos as Draft photos — so test
# albums pick none; photos are added one by one (+ Add photo).
TEST_DISPLAY_ORDER = "900"
PUBLISH_CONFIRM_TIMEOUT = 120.0
PUBLIC_REFLECT_TIMEOUT = 5.0  # cms-profile.md: poll 5 s @ 0.5 s
VIEWPORTS = {"desktop": (1920, 1080), "mobile": (390, 844)}
FINDINGS_LOG = os.path.join(PB_EVIDENCE_DIR, "findings.jsonl")
ARABIC_PATTERN = r"Arabic content is required|المحتوى بالعربية مطلوب"
BLOCKED_DETAIL = ("ADO 148180 (reopened): the public Album Details page renders blank "
                  "(JS 'lastLabel is not defined')")


def _name(tc_id: str, suffix: str) -> str:
    return f"{PB_QCTEST_PREFIX}{tc_id}-{STAMP} {suffix}"


def _sized(tc_id: str, length: int, arabic: bool = False) -> str:
    """A QCTEST-prefixed string of exactly `length` characters."""
    head = f"{PB_QCTEST_PREFIX}{tc_id}-{STAMP} "
    filler = ("نص اختبار طويل " if arabic else "Long field limit check ") * 40
    value = (head + filler)[:length]
    return value[:-1] + "X" if value.endswith(" ") else value


def _album_data(tc_id: str, **overrides) -> dict:
    data = {"title": _name(tc_id, "Album"), "title_ar": _name(tc_id, "ألبوم تجريبي"),
            "published_date": TODAY_DMY, "category": REAL_CATEGORY,
            "cover": COVER_JPG,
            "cover_stem": f"qctest-130714-pb-{tc_id}-cover", "active": True}
    data.update(overrides)
    return data


def _category_data(tc_id: str, **overrides) -> dict:
    data = {"name": _name(tc_id, "Category"), "name_ar": _name(tc_id, "فئة تجريبية"),
            "display_order": TEST_DISPLAY_ORDER, "active": True}
    data.update(overrides)
    return data


# ===========================================================================
# Fixtures
# ===========================================================================
CLEANERS = {"page-hero": PageHeroAdminPage}


@pytest.fixture
def disposable(browser):
    """Removes ONLY the records the test registered at creation (photos, albums,
    categories through the shared guarded cleanup; page heroes through their own
    guarded delete), as the Site Content Editor. A delete the product refuses
    because the record is still referenced is LEFT unpublished and reported;
    any other leftover fails the teardown."""
    registry = PhotoRegistry(PB_QCTEST_PREFIX)
    yield registry
    outcome, failures = [f"LEFT (blank-title photo, not capturable): {u}" for u in registry.untracked], []
    if not registry.entries:
        if outcome:
            allure.attach(chr(10).join(outcome), name="QCTEST teardown")
        return
    ctx = new_context(browser, use_auth_state=False)
    try:
        page = ctx.new_page()
        gallery = [e for e in registry.entries if e.slug != "page-hero"]
        if gallery:
            done, failed = cleanup(page, PB_QCTEST_PREFIX, PB_EVIDENCE_DIR, gallery, registry.parents,
                                   PB_ROLE_EDITOR, lambda admin: admin.login_as_role(PB_ROLE_EDITOR) == "ok")
            outcome += done
            failures += failed
        for entry in [e for e in registry.entries if e.slug == "page-hero"]:
            label = f"{entry.slug} {entry.title[:80]!r} (id {entry.entry_id}, code {entry.code})"
            try:
                cleaner = CLEANERS[entry.slug](page)
                cleaner.login_pinned(PB_ROLE_EDITOR)
                cleaner.pinned_role = PB_ROLE_EDITOR
                cleaner.open_list_all()
                if not cleaner.row_present(entry):
                    outcome.append(f"already gone: {label}")
                    continue
                cleaner.adopt(entry)
                (outcome if cleaner.delete_own_entry(entry) else failures).append(f"delete {label}")
            except Exception as exc:  # noqa: BLE001 — collected below
                failures.append(f"{label}: {exc!r}")
    finally:
        ctx.close()
    allure.attach(chr(10).join(outcome + failures) or "nothing to remove", name="QCTEST teardown")
    if failures:
        raise AssertionError("TEARDOWN LEFT QCTEST DATA BEHIND:" + chr(10) + chr(10).join(failures))


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


@pytest.fixture
def hero_guard(browser):
    """TEST_OWNED guard for the REAL listing Page Hero: snapshot before the test,
    restore + re-verify after it (as the Editor, in its own context)."""
    ctx = new_context(browser, use_auth_state=False)
    page = ctx.new_page()
    hero = PageHeroAdminPage(page)
    if hero.login_pinned(PB_ROLE_EDITOR) != "ok":
        ctx.close()
        pytest.skip("PRECONDITION: could not sign in as the Site Content Editor for the hero snapshot")
    baseline = hero.snapshot(HERO_LISTING_CODE, keep_bytes_in=PageHeroAdminPage.scratch_dir())
    allure.attach(dump(baseline), name="Page Hero baseline (listing record)")
    if baseline.get("row_status") != STATUS_PUBLISHED or not baseline.get("title") or not baseline.get("image"):
        ctx.close()
        pytest.skip(f"PRECONDITION: the real listing Page Hero is not in its known published state: {baseline}")
    report: dict = {}
    try:
        yield baseline
    finally:
        try:
            report = hero.restore(baseline)
            allure.attach(dump(report), name="Page Hero restore report")
        finally:
            ctx.close()
        if report.get("remaining"):
            raise AssertionError(f"PAGE HERO NOT RESTORED — still differs in {report['remaining']}: "
                                 f"{dump(report['final'])}")


# ===========================================================================
# Helpers (test layer — no raw Playwright)
# ===========================================================================
def _editor(page, cls):
    admin = cls(page)
    outcome = admin.login_pinned(PB_ROLE_EDITOR)
    if outcome == "auth_failed":
        pytest.skip("PRECONDITION: Liferay refused the .env credentials for 'Site Content Editor'")
    if outcome != "ok":
        pytest.fail("login as 'Site Content Editor' neither succeeded nor showed Liferay's refusal banner")
    if isinstance(admin, PageHeroAdminPage):
        # Live 2026-10-13: manage-page-hero lists its 2 fixed records with no
        # create form (no Add New on fixed records, by design).
        admin.open_list_all()
    else:
        admin.open_create_form_en()
    user_id, _ = admin.signed_in_user()
    if user_id != PB_ROLE_USER_IDS[PB_ROLE_EDITOR]:
        pytest.skip(f"PRECONDITION: Editor credentials sign in as userId {user_id!r}, not 156488")
    return admin


def _pinned(admin) -> None:
    user_id, _ = admin.signed_in_user()
    assert user_id == PB_ROLE_USER_IDS[PB_ROLE_EDITOR], (
        f"the session is now userId {user_id!r}, not the pinned Site Content Editor (156488)")


def _log_finding(kind: str, tc_id: str, **details) -> None:
    finding = {"kind": kind, "tc": tc_id, **details}
    allure.attach(dump(finding), name=f"{kind} finding")
    os.makedirs(os.path.dirname(FINDINGS_LOG), exist_ok=True)
    with open(FINDINGS_LOG, "a", encoding="utf-8") as handle:
        handle.write(json.dumps(finding, ensure_ascii=False, default=str) + "\n")


def _register(admin, disposable, title: str, ids_before: set):
    try:
        entry = admin.identify_created_pb(title, ids_before)
        return disposable.track(entry) if entry else None
    except Exception as exc:  # noqa: BLE001 — registration must not mask the result
        allure.attach(repr(exc), name=f"registration of {title[:80]!r} failed")
        return None


def _publish_attempt(admin, tc_id: str, what: str) -> dict:
    _pinned(admin)
    admin.click_publish()
    shot = admin.evidence(f"{tc_id}_{what}_after_publish")
    return {"went_through": admin.save_went_through(), "refused": admin.save_was_refused(),
            "evidence": admin.pb_refusal_evidence(), "messages": admin.all_messages_text(), "screenshot": shot}


def _assert_blocked(admin, disposable, tc_id: str, what: str, title: str, fill, field_pattern: str,
                    expected_text: str | None = None, text_pattern: str | None = None) -> dict:
    """Fills a NEW form via `fill(admin)` and clicks Publish. Must be refused with
    evidence pointing at the field, and NO record may be created. A matching
    refusal whose wording differs from `text_pattern` is a LOW wording finding."""
    ids_before = admin.snapshot_ids()
    result = {}
    try:
        admin.open_create_form_en()
        admin.wait_arabic_ready()
        fill(admin)
        result = _publish_attempt(admin, tc_id, what)
    finally:
        entry = _register(admin, disposable, title, ids_before) if title.startswith(PB_QCTEST_PREFIX) else None
    allure.attach(dump(result), name=f"refusal evidence ({what})")
    if entry is not None:
        admin.open_list_all()
        pytest.fail(f"PRODUCT: Publish with {what} was NOT blocked — a record was created "
                    f"(status {admin.row_status(entry)!r}, entry id {entry.entry_id}, code {entry.code}); "
                    f"messages {result.get('messages')!r}; screenshot {result.get('screenshot')}")
    assert not result.get("went_through") and result.get("refused"), (
        f"Publish with {what} was neither refused with validation evidence nor saved: {dump(result)}")
    blob = json.dumps(result["evidence"], ensure_ascii=False)
    assert re.search(field_pattern, blob, re.I), (
        f"Publish was refused, but the validation evidence does not point at {what}: {dump(result['evidence'])}")
    if text_pattern and not re.search(text_pattern, result["messages"] + " " + blob, re.I):
        _log_finding("LOW wording", tc_id, field=what, expected=expected_text or text_pattern,
                     shown=result["messages"], screenshot=result["screenshot"])
    return result


def _create_published(admin, disposable, tc_id: str, title: str, fill, what: str):
    """Creates + publishes one record (registered for teardown), then asserts it."""
    ids_before = admin.snapshot_ids()
    result = {}
    try:
        admin.open_create_form_en()
        admin.wait_arabic_ready()
        fill(admin)
        result = _publish_attempt(admin, tc_id, what)
        if result["went_through"]:
            admin.wait_arabic_saved()
    finally:
        entry = _register(admin, disposable, title, ids_before)
    allure.attach(dump(result), name=f"create ({what})")
    assert result.get("went_through"), f"Publishing {what} did not go through: {dump(result)}"
    assert entry is not None, f"{what} went through but is not identifiable as exactly one NEW record"
    return entry


def _create_published_album(admin, disposable, tc_id: str, title: str, fill, what: str):
    """By design since ADO 148169 an album publishes only with >= 1 published
    photo: Save as Draft, add one published photo (+ Add photo), then Publish."""
    ids_before = admin.snapshot_ids()
    went_through = False
    try:
        admin.open_create_form_en()
        admin.wait_arabic_ready()
        fill(admin)
        _pinned(admin)
        admin.click_save_as_draft()
        went_through = admin.save_went_through()
        if went_through:
            admin.wait_arabic_saved()
        evidence = admin.pb_refusal_evidence()
    finally:
        entry = _register(admin, disposable, title, ids_before)
    assert went_through and entry is not None, f"{what}: the draft album was not saved: {dump(evidence)}"
    photo = add_photo(admin, disposable, entry.entry_id, photo_data(f"{title[:150]} Photo"), publish=True)
    assert photo["went_through"] and photo["entry"], f"{what}: the album's photo was not published: {photo['messages']}"
    out = publish_album(admin, entry)
    allure.attach(dump(out), name=f"publish ({what})")
    assert out["went_through"], f"Publishing {what} did not go through: {dump(out)}"
    return entry


def _published_and_active(admin, entry) -> None:
    status = admin.wait_status(entry, (STATUS_PUBLISHED,), timeout=PUBLISH_CONFIRM_TIMEOUT)
    assert status == STATUS_PUBLISHED, f"{entry.title[:80]!r} never reached Published (last {status!r})"
    admin.open_entry_en(entry.code)
    stored = admin.active_status_stored()
    allure.attach(f"stored Active Status: {stored!r}", name="Active Status precondition")
    if stored != "true":
        pytest.fail(f"PRECONDITION NOT MET — PRODUCT: {entry.title[:80]!r} stores Active Status {stored!r}; "
                    "the public step was not run")


def _render_check(view: PhotoGalleryPublicViewPB, tc_id: str, where: str, selectors: list[str],
                  expected: str, shown: str, only_text: str) -> dict:
    report = view.overflow_report(selectors, only_text=only_text[:30])
    shot = view.evidence(f"{tc_id}_{where}")
    problems = overflow_problems(report)
    cut = shown != expected
    result = {"where": where, "expected_len": len(expected), "shown_len": len(shown or ""),
              "text_differs": cut, "problems": problems, "screenshot": shot, "report": report}
    if cut or problems:
        _log_finding("frontend render", tc_id, where=where, expected=expected, shown=shown,
                     problems=problems, screenshot=shot)
    allure.attach(dump(result), name=f"render {where}")
    return result


def _public_album_checks(anon_pages, tc_id: str, code: str, expected: dict, mode: str) -> list[dict]:
    """Listing + detail, EN + AR, desktop + mobile, for one published album.
    `expected` = {"en": text, "ar": text}; `mode` "title" or "chip"."""
    results = []
    for vp_name, viewport in VIEWPORTS.items():
        view = PhotoGalleryPublicViewPB(anon_pages(viewport))
        for locale in ("en", "ar"):
            text = expected[locale]
            index = view.wait_card(code, locale, timeout=PUBLIC_REFLECT_TIMEOUT)
            if index < 0:
                shot = view.evidence(f"{tc_id}_listing_{locale}_{vp_name}_missing")
                pytest.fail(f"DELIVERY: album {code} never appeared on the logged-out {locale} listing "
                            f"({vp_name}); screenshot {shot}")
            view.scroll_card_into_view(index)
            card = view.cards()[index]
            shown = card["title"] if mode == "title" else card["chip"]
            sels = [view.CARD_TITLE] if mode == "title" else [view.CARD_CHIP, view.CAT_SELECT]
            results.append(_render_check(view, tc_id, f"listing_{locale}_{vp_name}", sels, text, shown, text))
            if mode == "chip":
                options = view.category_options()
                results.append({"where": f"listing_{locale}_{vp_name}_filter",
                                "option_present": text in options, "options": options})
            view.open_detail(code, locale)
            texts = view.detail_texts()
            if not any((texts.get(k) or "").strip() for k in view.DETAIL_TEXT_SELECTORS):
                results.append({"where": f"detail_{locale}_{vp_name}", "blocked": BLOCKED_DETAIL,
                                "screenshot": view.evidence(f"{tc_id}_detail_{locale}_{vp_name}_blank")})
                continue
            shown = texts.get(view.DETAIL_TITLE) if mode == "title" else texts.get(view.DETAIL_CHIP)
            results.append(_render_check(view, tc_id, f"detail_{locale}_{vp_name}", view.DETAIL_TEXT_SELECTORS,
                                         text, shown or "", text))
    allure.attach(dump(results), name="frontend render summary")
    return results


def _photo_album(admin, disposable, tc_id: str):
    """A QCTEST Draft album (never published) to hold the case's photo form."""
    title = _name(tc_id, "Photo Host Album")
    ids_before = admin.snapshot_ids()
    try:
        admin.open_create_form_en()
        admin.wait_arabic_ready()
        admin.fill_album_pb(_album_data(tc_id, title=title))
        _pinned(admin)
        admin.click_save_as_draft()
        saved = admin.save_went_through()
    finally:
        entry = _register(admin, disposable, title, ids_before)
    assert saved and entry is not None, f"precondition: the host album was not saved as Draft: {admin.all_messages_text()}"
    return entry


def _photo_attempt(admin, disposable, album, tc_id: str, what: str, title: str | None, fill) -> dict:
    """Opens the album's '+ Add photo', runs `fill(photos)` and clicks Publish."""
    _pinned(admin)
    result = add_photo(admin, disposable, album.entry_id, photo_data(title), publish=True, fill=fill)
    result["screenshot"] = result["photos"].evidence(f"{tc_id}_{what}_after_publish")
    allure.attach(dump({k: v for k, v in result.items() if k != "photos"}), name=f"photo attempt ({what})")
    return result


def _assert_photo_blocked(result: dict, what: str, field_pattern: str) -> None:
    assert not result["new_rows"], (
        f"PRODUCT: Publish with {what} was NOT blocked - a photo was created: {result['new_rows']}; "
        f"messages {result['messages']!r}; screenshot {result['screenshot']}")
    assert not result["went_through"], f"Publish with {what} reported success but no row appeared: {dump(result)}"
    blob = json.dumps(result["evidence"], ensure_ascii=False)
    assert re.search(field_pattern, blob, re.I), (
        f"Publish was refused, but the evidence does not point at {what}: {dump(result['evidence'])}")


# ===========================================================================
# Page Hero (manage-page-hero) — 143147-143150
# ===========================================================================
@AUTH_FREE_PAGE
@allure.epic("Insights & Media")
@allure.feature("Photo Gallery — Control Panel")
@allure.story("Page Hero — Page Title")
@allure.title("Leaving the Page Title AR field empty is blocked with the bilingual-required message")
@pytest.mark.bilingual
@pytest.mark.tc_143147
def test_page_hero_title_ar_required(page, hero_guard):
    # Azure TC 143147 | real listing hero's own form (restored by hero_guard)
    admin = _editor(page, PageHeroAdminPage)
    admin.open_real(HERO_LISTING_CODE)
    admin.fill_en_change(K_PAGE_TITLE, "Photo Albums")
    admin.fill_ar_change(K_PAGE_TITLE, "")
    assert admin.text_value(K_PAGE_TITLE) == "Photo Albums" and admin.ar_value(K_PAGE_TITLE) == "", (
        "precondition: EN 'Photo Albums' / AR empty were not held by the form")
    result = _publish_attempt(admin, "143147", "empty_title_ar")
    allure.attach(dump(result), name="publish attempt")
    after = admin.snapshot(HERO_LISTING_CODE)
    allure.attach(dump(after), name="listing hero after the attempt")
    assert after["title_ar"] == hero_guard["title_ar"], (
        f"PRODUCT: the save was not blocked — the stored Arabic Page Title is now {after['title_ar']!r} "
        f"(was {hero_guard['title_ar']!r}); messages {result['messages']!r}; screenshot {result['screenshot']}")
    assert not result["went_through"] and result["refused"], (
        f"Publish with an empty Page Title AR was neither refused nor saved: {dump(result)}")
    blob = json.dumps(result["evidence"], ensure_ascii=False)
    assert re.search(r"qc-ar-pageTitle|Page Title|العربية|Arabic", blob, re.I), (
        f"the refusal evidence does not point at Page Title AR: {dump(result['evidence'])}")
    if not re.search(ARABIC_PATTERN, result["messages"] + " " + blob):
        _log_finding("LOW wording", "143147", field="Page Title AR (empty)",
                     expected=f"{PB_MSG_ARABIC_REQUIRED_EN} / {PB_MSG_ARABIC_REQUIRED_AR}",
                     shown=result["messages"], screenshot=result["screenshot"])


@AUTH_FREE_PAGE
@allure.epic("Insights & Media")
@allure.feature("Photo Gallery — Control Panel")
@allure.story("Page Hero — Page Title")
@allure.title("The Page Title EN field rejects input exceeding 100 characters")
@pytest.mark.tc_143148
def test_page_hero_title_en_max_100(page, hero_guard, anon_pages):
    # Azure TC 143148 | CMS: 101 chars on the real listing hero's form (restored by
    # hero_guard); rule 6: publish exactly 100 EN + 100 AR and read the public hero.
    admin = _editor(page, PageHeroAdminPage)
    over = _sized("143148", PAGE_TITLE_LIMIT + 1)
    admin.open_real(HERO_LISTING_CODE)
    admin.fill_en_change(K_PAGE_TITLE, over)
    held = admin.text_value(K_PAGE_TITLE)
    info = admin.control_info(K_PAGE_TITLE)
    result = _publish_attempt(admin, "143148", "title_en_101")
    after = admin.snapshot(HERO_LISTING_CODE)
    allure.attach(dump({"typed": len(over), "field_held": len(held), "control": info, "attempt": result,
                        "stored_after": after}), name="101-character attempt")
    cms_failure = ""
    if len(after["title"]) > PAGE_TITLE_LIMIT:
        cms_failure = (f"PRODUCT: a {len(after['title'])}-character Page Title EN was saved and published "
                       f"(limit {PAGE_TITLE_LIMIT}); messages {result['messages']!r}; screenshot {result['screenshot']}")
    elif not (result["refused"] or len(held) <= PAGE_TITLE_LIMIT):
        cms_failure = f"the 101-character save was neither refused nor truncated: {dump(result)}"

    # rule 6 — the max length really renders on the public listing hero
    exact_en = _sized("143148", PAGE_TITLE_LIMIT)
    exact_ar = _sized("143148", PAGE_TITLE_LIMIT, arabic=True)
    admin.open_real(HERO_LISTING_CODE)
    admin.fill_en_change(K_PAGE_TITLE, exact_en)
    admin.fill_ar_change(K_PAGE_TITLE, exact_ar)
    published = _publish_attempt(admin, "143148", "title_100_publish")
    stored = admin.snapshot(HERO_LISTING_CODE)
    allure.attach(dump({"publish": published, "stored": stored}), name="100-character publish")
    frontend = []
    if published["went_through"] and stored["title"] == exact_en and stored["active"] == "true":
        for vp_name, viewport in VIEWPORTS.items():
            view = PhotoGalleryPublicViewPB(anon_pages(viewport))
            for locale, text in (("en", exact_en), ("ar", exact_ar)):
                shown = view.wait_hero_title(text, locale, timeout=PUBLIC_REFLECT_TIMEOUT)
                frontend.append(_render_check(view, "143148", f"listing_hero_{locale}_{vp_name}",
                                              [view.HERO_TITLE, ".qc-pgl-crumb-current"], text, shown, text[:30]))
    else:
        frontend.append({"skipped": "the exact-100 publish did not go through", "publish": published,
                         "stored": stored})
    allure.attach(dump(frontend), name="frontend render summary (rule 6)")
    assert published["went_through"] and stored["title"] == exact_en, (
        f"a valid 100-character Page Title EN could not be published: {dump(published)} / stored {stored['title']!r}")
    assert not cms_failure, cms_failure


@AUTH_FREE_PAGE
@allure.epic("Insights & Media")
@allure.feature("Photo Gallery — Control Panel")
@allure.story("Page Hero — Hero Background Image")
@allure.title("Leaving the Hero Background Image empty blocks save")
@pytest.mark.tc_143149
def test_page_hero_image_required(page, disposable):
    # Azure TC 143149 | create form (Active unticked), no image; the real hero is only read
    admin = _editor(page, PageHeroAdminPage)
    before = admin.snapshot(HERO_LISTING_CODE)
    admin.open_real(HERO_LISTING_CODE)
    remove_state = admin.remove_file_button_state(K_HERO_IMAGE)
    allure.attach(dump({"real_hero": before, "remove_file_button": remove_state}), name="real hero (read-only)")
    title = _name("143149", "Photo Albums")

    def _fill(a):
        a.fill_hero({"title": title, "title_ar": _name("143149", "ألبومات الصور"), "active": False})
        assert a.stored_file_placeholder_name(K_HERO_IMAGE) == "" and not a.file_field_value(K_HERO_IMAGE), (
            "precondition: the create form's Hero Background Image is not empty")

    _assert_blocked(admin, disposable, "143149", "an empty Hero Background Image", title, _fill,
                    r"heroBackgroundImage|Hero Background Image|image")
    after = admin.snapshot(HERO_LISTING_CODE)
    assert (after["image"], after["image_sha256"]) == (before["image"], before["image_sha256"]), (
        f"the real listing hero's image changed during the case: {before['image']} -> {after['image']}")


@AUTH_FREE_PAGE
@allure.epic("Insights & Media")
@allure.feature("Photo Gallery — Control Panel")
@allure.story("Page Hero — Hero Background Image")
@allure.title("A Hero Background Image upload larger than 2 MB is rejected")
@pytest.mark.tc_143150
def test_page_hero_image_over_2mb_rejected(page, disposable):
    # Azure TC 143150 | 3.07 MB JPG into the create form's picker. When the picker
    # takes it anyway, the save is attempted once (QCTEST title, Active unticked) to
    # record whether the limit is enforced later; such a record is removed.
    admin = _editor(page, PageHeroAdminPage)
    help_text = admin.image_help_text()
    result = admin.attempt_upload_pb(K_HERO_IMAGE, HERO_3MB_JPG, stem="qctest-130714-pb-143150-hero-3mb")
    shot = admin.evidence("143150_after_3mb_upload")
    allure.attach(dump({"help": help_text, "upload": result}), name="3 MB upload attempt")
    message = " | ".join([result["feedback"]] + result["errors"] + result["field_errors"]).strip(" |")
    if result["attached"]:
        title = _name("143150", "Photo Albums")
        ids_before = admin.snapshot_ids()
        save = {}
        try:
            admin.open_create_form_en()
            admin.wait_arabic_ready()
            admin.fill_hero({"title": title, "title_ar": _name("143150", "ألبومات الصور"), "active": False})
            admin.upload_pb(K_HERO_IMAGE, HERO_3MB_JPG, stem="qctest-130714-pb-143150-hero-3mb")
            save = _publish_attempt(admin, "143150", "publish_with_3mb_image")
        finally:
            created = _register(admin, disposable, title, ids_before)
        allure.attach(dump(save), name="save attempt with the 3 MB image attached")
        later = ("and the record SAVED with it (entry id %s)" % created.entry_id if created is not None
                 else f"; the save was then {'refused' if save.get('refused') else 'not completed'} with "
                      f"{save.get('messages')!r}")
        pytest.fail(f"PRODUCT: the {result['size']}-byte JPG was ACCEPTED by the Hero Background Image picker "
                    f"(help {help_text!r}, no size message) and attached to the field {later}; "
                    f"screenshots {result['picker_evidence']} / {save.get('screenshot')}")
    assert result["success"] is not True or message, f"no rejection evidence for the 3 MB file: {dump(result)}"
    assert message, f"the 3 MB file was not attached but no file-size message was shown: {dump(result)}"
    if not re.search(r"size|larger|2 MB|exceed|too large", message, re.I):
        _log_finding("LOW wording", "143150", field="Hero Background Image > 2 MB",
                     expected="a file-size validation message", shown=message, screenshot=shot)


# ===========================================================================
# Event Category (manage-event-category) — 143151-143153
# ===========================================================================
@AUTH_FREE_PAGE
@allure.epic("Insights & Media")
@allure.feature("Photo Gallery — Control Panel")
@allure.story("Event Category — Name")
@allure.title("Leaving the Event Category Name AR field empty is blocked with the bilingual-required message")
@pytest.mark.bilingual
@pytest.mark.tc_143151
def test_event_category_name_ar_required(page, disposable):
    # Azure TC 143151 | EN "…Institutional", AR empty
    admin = _editor(page, EventCategoryFieldsPB)
    title = _name("143151", "Institutional")
    _assert_blocked(admin, disposable, "143151", "an empty Event Category Name AR", title,
                    lambda a: a.fill_category_pb(_category_data("143151", name=title, name_ar="")),
                    r"qc-ar-categoryName|Category Name|العربية|Arabic",
                    expected_text=f"{PB_MSG_ARABIC_REQUIRED_EN} / {PB_MSG_ARABIC_REQUIRED_AR}",
                    text_pattern=ARABIC_PATTERN)


@AUTH_FREE_PAGE
@allure.epic("Insights & Media")
@allure.feature("Photo Gallery — Control Panel")
@allure.story("Event Category — Name")
@allure.title("The Event Category Name EN field rejects input exceeding 200 characters")
@pytest.mark.tc_143152
def test_event_category_name_en_max_200(page, disposable, anon_pages):
    # Azure TC 143152 | CMS: 201 chars on the create form; rule 6: a published
    # 200-char category (EN + AR) shown through one published QCTEST album.
    admin = _editor(page, EventCategoryFieldsPB)
    over = _sized("143152", CATEGORY_NAME_LIMIT + 1)
    ids_before = admin.snapshot_ids()
    result = {}
    try:
        admin.open_create_form_en()
        admin.wait_arabic_ready()
        admin.fill_category_pb(_category_data("143152", name=over))
        held = admin.text_value(K_CATEGORY_NAME)
        result = _publish_attempt(admin, "143152", "name_en_201")
        result["field_held"] = len(held)
    finally:
        created = _register(admin, disposable, over, ids_before)
    allure.attach(dump(result), name="201-character attempt")
    cms_failure = ""
    if created is not None:
        admin.open_entry_en(created.code)
        stored = admin.text_value(K_CATEGORY_NAME)
        if len(stored) > CATEGORY_NAME_LIMIT:
            cms_failure = (f"PRODUCT: a {len(stored)}-character Event Category Name EN was saved (entry id "
                           f"{created.entry_id}, limit {CATEGORY_NAME_LIMIT}); screenshot {result.get('screenshot')}")
    elif not result.get("refused"):
        cms_failure = f"the 201-character save was neither refused nor saved: {dump(result)}"

    # rule 6 — 200-character name (EN + AR) rendered through one published album
    exact_en = _sized("143152", CATEGORY_NAME_LIMIT)
    exact_ar = _sized("143152", CATEGORY_NAME_LIMIT, arabic=True)
    category = _create_published(admin, disposable, "143152", exact_en,
                                 lambda a: a.fill_category_pb(_category_data("143152", name=exact_en,
                                                                             name_ar=exact_ar)),
                                 "200-character category")
    _published_and_active(admin, category)
    album_admin = PhotoAlbumFieldsPB(page)
    album_admin.pinned_role = PB_ROLE_EDITOR
    album_title = _name("143152", "Album in long category")
    album = _create_published_album(album_admin, disposable, "143152", album_title,
                              lambda a: a.fill_album_pb(_album_data("143152", title=album_title,
                                                                    category=exact_en)),
                              "album in the 200-character category")
    _published_and_active(album_admin, album)
    _public_album_checks(anon_pages, "143152", album.code, {"en": exact_en, "ar": exact_ar}, mode="chip")
    assert not cms_failure, cms_failure


@AUTH_FREE_PAGE
@allure.epic("Insights & Media")
@allure.feature("Photo Gallery — Control Panel")
@allure.story("Event Category — Display Order")
@allure.title("The Event Category Display Order rejects a negative value")
@pytest.mark.tc_143153
def test_event_category_display_order_negative(page, disposable):
    # Azure TC 143153 | Display Order -1
    admin = _editor(page, EventCategoryFieldsPB)
    title = _name("143153", "Category")
    info = {}

    def _fill(a):
        a.fill_category_pb(_category_data("143153", name=title, display_order="-1"))
        info.update(a.control_info(K_DISPLAY_ORDER), held=a.text_value(K_DISPLAY_ORDER))

    result = _assert_blocked(admin, disposable, "143153", "a negative Display Order (-1)", title, _fill,
                             r"displayOrder|Display Order|order")
    allure.attach(dump(info), name="Display Order control after typing -1")
    if not re.search(r"positive|greater|at least|minimum|0|1", result["messages"], re.I):
        _log_finding("LOW wording", "143153", field="Display Order -1",
                     expected="a validation message requiring a positive integer",
                     shown=result["messages"], screenshot=result["screenshot"])


# ===========================================================================
# Photo Album (manage-photo-album) — 143157-143162
# ===========================================================================
@AUTH_FREE_PAGE
@allure.epic("Insights & Media")
@allure.feature("Photo Gallery — Control Panel")
@allure.story("Album — Title")
@allure.title("Leaving the Album Title AR field empty is blocked with the bilingual-required message")
@pytest.mark.bilingual
@pytest.mark.tc_143157
def test_album_title_ar_required(page, disposable):
    # Azure TC 143157 | EN "…Trade Summit 2026", AR empty, every other field valid
    admin = _editor(page, PhotoAlbumFieldsPB)
    title = _name("143157", "Trade Summit 2026")
    _assert_blocked(admin, disposable, "143157", "an empty Album Title AR", title,
                    lambda a: a.fill_album_pb(_album_data("143157", title=title, title_ar="")),
                    r"qc-ar-albumTitle|Album Title|العربية|Arabic",
                    expected_text=f"{PB_MSG_ARABIC_REQUIRED_EN} / {PB_MSG_ARABIC_REQUIRED_AR}",
                    text_pattern=ARABIC_PATTERN)


@AUTH_FREE_PAGE
@allure.epic("Insights & Media")
@allure.feature("Photo Gallery — Control Panel")
@allure.story("Album — Title")
@allure.title("The Album Title EN field rejects input exceeding 200 characters")
@pytest.mark.tc_143158
def test_album_title_en_max_200(page, disposable, anon_pages):
    # Azure TC 143158 | CMS: 201 chars on the create form; rule 6: a published
    # album with a 200-char EN + AR title on the listing + detail.
    admin = _editor(page, PhotoAlbumFieldsPB)
    over = _sized("143158", ALBUM_TITLE_LIMIT + 1)
    ids_before = admin.snapshot_ids()
    result = {}
    try:
        admin.open_create_form_en()
        admin.wait_arabic_ready()
        admin.fill_album_pb(_album_data("143158", title=over))
        held = admin.text_value(K_ALBUM_TITLE)
        result = _publish_attempt(admin, "143158", "title_en_201")
        result["field_held"] = len(held)
    finally:
        created = _register(admin, disposable, over, ids_before)
    allure.attach(dump(result), name="201-character attempt")
    cms_failure = ""
    if created is not None:
        admin.open_entry_en(created.code)
        stored = admin.text_value(K_ALBUM_TITLE)
        if len(stored) > ALBUM_TITLE_LIMIT:
            cms_failure = (f"PRODUCT: a {len(stored)}-character Album Title EN was saved (entry id "
                           f"{created.entry_id}, limit {ALBUM_TITLE_LIMIT}); screenshot {result.get('screenshot')}")
    elif not result.get("refused"):
        cms_failure = f"the 201-character save was neither refused nor saved: {dump(result)}"

    exact_en = _sized("143158", ALBUM_TITLE_LIMIT)
    exact_ar = _sized("143158", ALBUM_TITLE_LIMIT, arabic=True)
    album = _create_published_album(admin, disposable, "143158", exact_en,
                              lambda a: a.fill_album_pb(_album_data("143158", title=exact_en, title_ar=exact_ar)),
                              "200-character album title")
    _published_and_active(admin, album)
    _public_album_checks(anon_pages, "143158", album.code, {"en": exact_en, "ar": exact_ar}, mode="title")
    assert not cms_failure, cms_failure


@AUTH_FREE_PAGE
@allure.epic("Insights & Media")
@allure.feature("Photo Gallery — Control Panel")
@allure.story("Album — Event Category")
@allure.title("Saving an album with no Event Category selected is blocked")
@pytest.mark.tc_143159
def test_album_event_category_required(page, disposable):
    # Azure TC 143159 | every field valid except Event Category
    admin = _editor(page, PhotoAlbumFieldsPB)
    title = _name("143159", "Album")

    def _fill(a):
        a.fill_album_pb(_album_data("143159", title=title, category=None))
        assert a.picklist_value(K_EVENT_CATEGORY) == "", "precondition: Event Category is not empty"

    _assert_blocked(admin, disposable, "143159", "no Event Category", title, _fill,
                    r"eventCategory|Event Category|category")


@AUTH_FREE_PAGE
@allure.epic("Insights & Media")
@allure.feature("Photo Gallery — Control Panel")
@allure.story("Album — Cover Image")
@allure.title("An album with no Cover Image is blocked from publishing")
@pytest.mark.tc_143160
def test_album_cover_required_to_publish(page, disposable):
    # Azure TC 143160 | Save as Draft without a cover (record created as written),
    # then Publish it from its own form.
    admin = _editor(page, PhotoAlbumFieldsPB)
    title = _name("143160", "Album without cover")
    ids_before = admin.snapshot_ids()
    draft = {}
    try:
        admin.open_create_form_en()
        admin.wait_arabic_ready()
        admin.fill_album_pb(_album_data("143160", title=title, cover=None))
        _pinned(admin)
        admin.click_save_as_draft()
        draft = {"went_through": admin.save_went_through(), "messages": admin.all_messages_text(),
                 "screenshot": admin.evidence("143160_after_save_as_draft")}
        if draft["went_through"]:
            admin.wait_arabic_saved()
    finally:
        entry = _register(admin, disposable, title, ids_before)
    allure.attach(dump(draft), name="Save as Draft without a cover")
    assert draft.get("went_through") and entry is not None, (
        f"step 1: the album could not be saved as Draft without a cover: {dump(draft)}")
    admin.open_list_all()
    saved_as = admin.row_status(entry)
    if saved_as == STATUS_PUBLISHED:
        pytest.fail(f"PRODUCT: 'Save as Draft' showed {draft['messages']!r} but the album without a cover image is "
                    f"PUBLISHED (entry id {entry.entry_id}) — the draft step published it, and nothing blocked a "
                    f"published album without '{PB_MSG_COVER_REQUIRED_EN}'; screenshot {draft['screenshot']}")
    assert saved_as == "Draft", f"step 1: the album saved as {saved_as!r}, not Draft"
    admin.open_entry_en(entry.code)
    assert admin.stored_file_name(K_COVER_IMAGE) == "", "step 1: the draft unexpectedly has a cover image"
    result = _publish_attempt(admin, "143160", "publish_without_cover")
    allure.attach(dump(result), name="Publish without a cover")
    status = admin.wait_status(entry, ("Published", "Pending Review"), timeout=20.0)
    assert status not in ("Published", "Pending Review"), (
        f"PRODUCT: the album without a cover image was published (status {status!r}); expected "
        f"'{PB_MSG_COVER_REQUIRED_EN}' / '{PB_MSG_COVER_REQUIRED_AR}'; messages {result['messages']!r}; "
        f"screenshot {result['screenshot']}")
    assert result["refused"] and not result["went_through"], f"Publish was neither refused nor saved: {dump(result)}"
    blob = json.dumps(result["evidence"], ensure_ascii=False)
    assert re.search(r"albumCoverImage|Cover Image|cover|غلاف", blob + result["messages"], re.I), (
        f"Publish was refused, but not for the missing cover image: {dump(result['evidence'])}")
    if not re.search(r"An album cover image is required|صورة غلاف الألبوم مطلوبة", result["messages"] + blob):
        _log_finding("LOW wording", "143160", field="Album Cover Image (publish)",
                     expected=f"{PB_MSG_COVER_REQUIRED_EN} / {PB_MSG_COVER_REQUIRED_AR}",
                     shown=result["messages"], screenshot=result["screenshot"])


@AUTH_FREE_PAGE
@allure.epic("Insights & Media")
@allure.feature("Photo Gallery — Control Panel")
@allure.story("Album — Cover Image")
@allure.title("Uploading an unsupported file format as the Album Cover Image is rejected")
@pytest.mark.tc_143161
def test_album_cover_unsupported_format_rejected(page):
    # Azure TC 143161 | a real .gif into the create form's picker; nothing is saved
    admin = _editor(page, PhotoAlbumFieldsPB)
    result = admin.attempt_upload_pb(K_COVER_IMAGE, COVER_GIF, stem="qctest-130714-pb-143161-cover")
    shot = admin.evidence("143161_after_gif_upload")
    allure.attach(dump(result), name=".gif upload attempt")
    message = " | ".join([result["feedback"]] + result["errors"] + result["field_errors"]).strip(" |")
    assert not result["attached"], (
        f"PRODUCT: a .gif was ACCEPTED as Album Cover Image (accept {admin.control_info(K_COVER_IMAGE)['accept']!r}); "
        f"picker {result['picker_text'][:300]!r}; screenshot {shot}")
    assert message, f"the .gif was not attached but no message was shown: {dump(result)}"
    if not (PB_MSG_UNSUPPORTED_EN in message or PB_MSG_UNSUPPORTED_AR in message):
        _log_finding("LOW wording", "143161", field="Album Cover Image (.gif)",
                     expected=f"{PB_MSG_UNSUPPORTED_EN} / {PB_MSG_UNSUPPORTED_AR}", shown=message, screenshot=shot)


@AUTH_FREE_PAGE
@allure.epic("Insights & Media")
@allure.feature("Photo Gallery — Control Panel")
@allure.story("Album — Published Date")
@allure.title("Leaving Album Published Date empty blocks save")
@pytest.mark.tc_143162
def test_album_published_date_required(page, disposable):
    # Azure TC 143162 | every field valid except Published Date
    admin = _editor(page, PhotoAlbumFieldsPB)
    title = _name("143162", "Album")

    def _fill(a):
        a.fill_album_pb(_album_data("143162", title=title, published_date=None))
        assert a.date_stored(K_PUBLISHED_DATE) == "", "precondition: Published Date is not empty"

    _assert_blocked(admin, disposable, "143162", "an empty Published Date", title, _fill,
                    r"publishedDate|Published Date|date")


# ===========================================================================
# Photo (Album Photo, + Add photo) — 143164-143169 (ADO 148169 per-photo model)
# ===========================================================================
@AUTH_FREE_PAGE
@allure.epic("Insights & Media")
@allure.feature("Photo Gallery — Control Panel")
@allure.story("Photo — Photo File")
@allure.title("Leaving the Photo File empty blocks saving a photo")
@pytest.mark.tc_143164
def test_photo_file_required(page, disposable):
    # Azure TC 143164 | Photo File unset, every other field valid
    admin = _editor(page, PhotoAlbumFieldsPB)
    album = _photo_album(admin, disposable, "143164")
    title = _name("143164", "Photo")

    def _fill(photos):
        photos.fill_photo(photo_data(title, file=None))
        assert photos.read_photo()["file"] == "", "step 1: a Photo File is selected"

    result = _photo_attempt(admin, disposable, album, "143164", "no_photo_file", title, _fill)
    _assert_photo_blocked(result, "an empty Photo File", r"photoFile|Photo File")


@AUTH_FREE_PAGE
@allure.epic("Insights & Media")
@allure.feature("Photo Gallery — Control Panel")
@allure.story("Photo — Photo File")
@allure.title("Uploading an unsupported file format as a Photo File is rejected")
@pytest.mark.tc_143165
def test_photo_file_unsupported_format(page, disposable):
    # Azure TC 143165 | a .bmp as the Photo File (device upload through the picker)
    admin = _editor(page, PhotoAlbumFieldsPB)
    album = _photo_album(admin, disposable, "143165")
    title = _name("143165", "Photo")
    upload = {}

    def _fill(photos):
        photos.fill_photo(photo_data(title, file=None))
        upload.update(photos.upload_attempt(PHOTO_BMP, f"qctest-130714-pb-143165"))

    result = _photo_attempt(admin, disposable, album, "143165", "bmp_photo_file", title, _fill)
    allure.attach(dump(upload), name=".bmp upload attempt")
    shown = " ".join(upload.get("errors", [])) + " " + upload.get("picker_text", "") + " " + result["messages"]
    assert not result["new_rows"], (
        f"PRODUCT: a .bmp Photo File was accepted and a photo created: {result['new_rows']} ({dump(upload)})")
    assert not upload.get("attached") or not result["went_through"], f"the .bmp was attached and saved: {dump(upload)}"
    assert unsupported_type_shown(shown), (
        f"the .bmp was refused without {MSG_UNSUPPORTED_TYPE!r}: picker {upload.get('errors')} / {result['messages']!r}")


@AUTH_FREE_PAGE
@allure.epic("Insights & Media")
@allure.feature("Photo Gallery — Control Panel")
@allure.story("Photo — Photo Title")
@allure.title("A photo can be saved with the Photo Title EN/AR fields left blank")
@pytest.mark.tc_143166
def test_photo_titles_optional(page, disposable):
    # Azure TC 143166 | valid JPG, Photo Title EN + AR empty. The saved photo has
    # no title, so it cannot be captured by name for the guarded delete: it is
    # left in its QCTEST Draft host album (never public) and reported.
    admin = _editor(page, PhotoAlbumFieldsPB)
    album = _photo_album(admin, disposable, "143166")
    held = {}

    def _fill(photos):
        photos.fill_photo(photo_data(None, file=PHOTO_JPG, file_stem="qctest-130714-pb-143166"))
        held.update(photos.read_photo())

    result = _photo_attempt(admin, disposable, album, "143166", "titles_blank", None, _fill)
    assert "qctest-130714-pb-143166" in held.get("file_field", ""), (
        f"step 1: the JPG was not accepted as the Photo File: {held}")
    assert result["went_through"], f"step 2: a photo with blank titles was not saved: {result['messages']!r}"
    assert len(result["new_rows"]) == 1, f"step 2: expected ONE new photo, got {result['new_rows']}"
    photos = result["photos"]
    photos.open_entry_en(result["new_rows"][0]["code"])
    stored = photos.read_photo()
    allure.attach(dump(stored), name="stored photo")
    assert stored["title"] == "" and stored["title_ar"] == "", f"the stored titles are not empty: {stored}"


@AUTH_FREE_PAGE
@allure.epic("Insights & Media")
@allure.feature("Photo Gallery — Control Panel")
@allure.story("Photo — Photo Title")
@allure.title("The Photo Title EN field rejects input exceeding 200 characters")
@pytest.mark.tc_143167
def test_photo_title_en_max_200(page, disposable):
    # Azure TC 143167 | 201 characters in Photo Title EN, then Publish
    admin = _editor(page, PhotoAlbumFieldsPB)
    album = _photo_album(admin, disposable, "143167")
    over = _sized("143167", PHOTO_TITLE_LIMIT + 1)
    held = {}

    def _fill(photos):
        photos.fill_photo(photo_data(None, file=PHOTO_JPG, file_stem="qctest-130714-pb-143167"))
        photos.fill_en(K_PHOTO_TITLE, over)
        held.update(photos.control_info(K_PHOTO_TITLE), held=len(photos.text_value(K_PHOTO_TITLE)))

    result = _photo_attempt(admin, disposable, album, "143167", "title_en_201", over, _fill)
    allure.attach(dump(held), name="Photo Title EN control after typing 201 characters")
    assert held["held"] > 0, "step 1: the field did not accept keystrokes"
    stored = []
    for row in result["new_rows"]:
        result["photos"].open_entry_en(row["code"])
        stored.append(len(result["photos"].text_value(K_PHOTO_TITLE)))
    assert all(n <= PHOTO_TITLE_LIMIT for n in stored), (
        f"PRODUCT: a {max(stored)}-character Photo Title EN was saved (limit {PHOTO_TITLE_LIMIT}); "
        f"screenshot {result['screenshot']}")
    assert not result["new_rows"] or held["held"] <= PHOTO_TITLE_LIMIT, (
        f"the 201-character title was neither blocked nor held to {PHOTO_TITLE_LIMIT}: {dump(result)}")
    if result["new_rows"]:
        _log_finding("NOTE", "143167", detail=f"the field holds at most {held['held']} characters "
                     f"(maxLength {held.get('maxLength')}); the save went through with a <=200 title")


@AUTH_FREE_PAGE
@allure.epic("Insights & Media")
@allure.feature("Photo Gallery — Control Panel")
@allure.story("Photo — Thumbnail Framing")
@allure.title("Saving a photo with Thumbnail Framing left unset is blocked")
@pytest.mark.tc_143168
def test_photo_thumbnail_framing_required(page, disposable):
    # Azure TC 143168 | valid JPG, Thumbnail Framing emptied, then Publish
    admin = _editor(page, PhotoAlbumFieldsPB)
    album = _photo_album(admin, disposable, "143168")
    title = _name("143168", "Photo")
    framing = {}

    def _fill(photos):
        photos.fill_photo(photo_data(title, file=PHOTO_JPG, file_stem="qctest-130714-pb-143168"))
        framing["default"] = photos.read_photo()["framing"]
        framing.update(photos.clear_framing())

    result = _photo_attempt(admin, disposable, album, "143168", "framing_unset", title, _fill)
    allure.attach(dump(framing), name="Thumbnail Framing before/after clearing")
    assert framing["default"] == FRAMING_DEFAULT, f"the form opens with framing {framing['default']!r}"
    if framing["value"]:
        stored = []
        for row in result["new_rows"]:
            result["photos"].open_entry_en(row["code"])
            stored.append(result["photos"].read_photo()["framing_value"])
        pytest.skip(f"NOT RUNNABLE AS WRITTEN (by design, ADO 148169: 'Thumbnail Framing: required, default "
                    f"Centre'): the select cannot be left unset - after clearing it still holds "
                    f"{framing['value']!r}; saved photo framing {stored}")
    _assert_photo_blocked(result, "an unset Thumbnail Framing", r"thumbnailFraming|Thumbnail Framing")


@AUTH_FREE_PAGE
@allure.epic("Insights & Media")
@allure.feature("Photo Gallery — Control Panel")
@allure.story("Photo — Display Order")
@allure.title("Photo Display Order rejects a negative value")
@pytest.mark.tc_143169
def test_photo_display_order_negative(page, disposable):
    # Azure TC 143169 | Display Order -2, then Publish
    admin = _editor(page, PhotoAlbumFieldsPB)
    album = _photo_album(admin, disposable, "143169")
    title = _name("143169", "Photo")
    held = {}

    def _fill(photos):
        photos.fill_photo(photo_data(title, file=PHOTO_JPG, file_stem="qctest-130714-pb-143169", display_order=-2))
        held.update(photos.control_info(K_PHOTO_DISPLAY_ORDER), held=photos.text_value(K_PHOTO_DISPLAY_ORDER))

    result = _photo_attempt(admin, disposable, album, "143169", "display_order_-2", title, _fill)
    allure.attach(dump(held), name="Display Order control after typing -2")
    assert held["held"] == "-2", f"step 1: the field holds {held['held']!r}, not -2"
    _assert_photo_blocked(result, "a negative Display Order (-2)", r"displayOrder|Display Order|order")
    if not re.search(r"positive|greater|at least|minimum", result["messages"], re.I):
        _log_finding("LOW wording", "143169", field="Photo Display Order -2",
                     expected="a validation message requiring a positive integer",
                     shown=result["messages"], screenshot=result["screenshot"])
