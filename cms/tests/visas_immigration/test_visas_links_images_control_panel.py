"""
cms/tests/visas_immigration/test_visas_links_images_control_panel.py —
Agent D Control_Panel cases of PBI 130701 "Visas & Immigration" (Azure plan
137724 / suite 140362) on the Business Gateway Object Authoring surface
(`manage-bg-*`), checked on the public page
`/web/qatar-chamber/visas-immigration` (EN + `/ar/`).

Covers (duplicates carry the same outcome, extra tc_ marker on the test):
  140317                Arabic overview card / navigation path (real page, READ-ONLY) + Arabic CMS toast
  140455 (140507) .. 140460 (140512)   Supporting Image + alt text
  140461 (140513) .. 140472 (140524)   Official Source Link title / description / URL / Open Behavior
  140473 (140525) .. 140476 (140528)   Display Order
  140531, 140532                       repeatable item Active Status

How the "Section 0N of the Visas & Immigration record" wording is reproduced
(bg_rules.md ADDENDUM a, user decision 2026-10-06): the real page record and
its real sections / items are NEVER edited here. Each test creates its OWN
`QCTEST-130701-D-<tc>-<stamp>` BG Info Section with pageKey
`visas-immigration`, its own lower-case sectionKey and Display Order 800
(Agent D band 800-899; the only 100-grid value in it), attaches its own child
items to that sectionKey, and the public page renders that section as its own
row after the real ones (fragment JS, bg_recon.md §1). The renderer is
section-generic: the supporting photo, the source-link list, checklist and
sub-topic blocks use the same markup for any section, so a QCTEST row
reproduces "Section 02 / 04" exactly. Link sections carry a highlight card so
their row has a rail like the real Section 03 host (same 760 px article).
Item Display Orders use the 100-grid (case "1/3/4/5" -> 100/300/400/500).
Record titles carry the D prefix in front of the case literal (e.g. "QCTEST-
130701-D-140461-<stamp> Ministry of Interior") — the namespace the guarded
delete requires; alt texts / descriptions / URLs are the case literals.

Every test runs as the Site Content Editor (156488) in an auth-free context.
Public checks: the row status is Published and the stored Active Status is
re-read first, then a FRESH logged-out context reads the page. Teardown
deletes only the records this test captured (list-id diff + exact identity),
children first. Uploaded images stay in Documents & Media (as for every
other suite) and are listed in the report; nothing else is deleted.

Behaviour that differs from the case fails the test with the exact app
messages (bug candidate); wording-only differences pass with a LOW wording
note (reports/evidence/130701_D/findings.jsonl).
"""

from __future__ import annotations

import json
import os
import re
from datetime import datetime

import allure
import pytest

from cms.pages.visas_immigration.bg_admin_page import (
    MSG_DRAFT_SAVED,
    MSG_SAVED_AND_PUBLISHED,
    OPT_OPEN_NEW_TAB,
    OPT_OPEN_SAME_TAB,
    REAL_PAGE_LOCK,
    ROLE_EDITOR,
    ROLE_USER_IDS,
    SLUG_CHECKLIST,
    SLUG_LINK,
    SLUG_SECTION,
    SLUG_SUBTOPIC,
    STATUS_INACTIVE,
    BGAdminPageD,
    BGEntry,
    bg_data,
)
from cms.pages.components.object_authoring_page import STATUS_PUBLISHED
from config.settings import PROJECT_ROOT
from core.utils.waits import WaitTimeoutError, wait_until
from core.web.browser import new_context
from web.pages.visas_immigration.visas_immigration_page import VisasPublicViewD

pytestmark = [pytest.mark.control_panel, pytest.mark.web, pytest.mark.invest, pytest.mark.pbi_130701,
              pytest.mark.xdist_group("visas_cms_d")]

AUTH_FREE_PAGE = pytest.mark.parametrize("page", [{"auth": False}], indirect=True)
FIXTURES = os.path.join(os.path.dirname(__file__), "fixtures")
PNG_640KB = os.path.join(FIXTURES, "d_qctest_arrivals_640kb.png")      # 1200x800, 655,360 bytes
SVG_120KB = os.path.join(FIXTURES, "d_qctest_arrivals.svg")            # ~122 KB
PNG_UNDER = os.path.join(FIXTURES, "d_qctest_arrivals_under.png")      # 2,097,000 bytes
PNG_OVER = os.path.join(FIXTURES, "d_qctest_arrivals_over.png")        # 2,097,500 bytes
STAMP = datetime.now().strftime("%m%d%H%M%S")
AGENT = "D"
PREFIX = "QCTEST-130701-D-"
SECTION_ORDER = 800                    # Agent D band 800-899, 100-grid
EVIDENCE = os.path.join(str(PROJECT_ROOT), "reports", "evidence", "130701_D")
FINDINGS = os.path.join(EVIDENCE, "findings.jsonl")
CASE_BUDGET_S = 5.0                    # the cases' "within the 5 second budget"
PUBLIC_TIMEOUT_S = 45.0                # hard ceiling; > CASE_BUDGET_S is recorded as a latency finding
MOBILE = (390, 844)
DESKTOP = (1920, 1080)

ALT_EN = "QCTEST-130701 passengers arriving at Hamad International Airport"
ALT_AR = "المسافرون القادمون إلى مطار حمد الدولي"
MAROON = "rgb(145, 23, 49)"       # #911731
INK = "rgb(29, 29, 27)"           # #1D1D1B
PILL_INK = "rgb(52, 52, 50)"      # #343432
GREY = "rgb(108, 108, 107)"       # #6C6C6B
CARD_FILL = "rgb(246, 246, 246)"  # #F6F6F6
REQUIRED_PATTERN = r"required|mandatory|fill|enter|empty|blank|مطلوب"
URL_PATTERN = r"url|link|valid|format|http"
ORDER_PATTERN = r"positive|greater|minimum|at least|valid|integer|number|required"
TYPE_PATTERN = r"type|extension|jpg|jpeg|png|format|not allowed|unsupported|valid"
SIZE_PATTERN = r"size|large|exceed|2\s*MB|maximum"
ARABIC = re.compile(r"[؀-ۿ]")


# ===========================================================================
# Findings / evidence
# ===========================================================================
class Checks:
    """Collects every step outcome of one case so all steps run; fails at the end."""

    def __init__(self, tc: str):
        self.tc = tc
        self.failures: list[str] = []
        self.notes: list[str] = []

    def check(self, ok: bool, message: str) -> bool:
        if not ok:
            self.failures.append(message)
        return ok

    def note(self, kind: str, message: str, **extra) -> None:
        self.notes.append(f"[{kind}] {message}")
        os.makedirs(EVIDENCE, exist_ok=True)
        with open(FINDINGS, "a", encoding="utf-8") as handle:
            handle.write(json.dumps({"tc": self.tc, "kind": kind, "message": message, **extra},
                                    ensure_ascii=False) + "\n")

    def latency(self, label: str, seconds: float) -> None:
        if seconds > CASE_BUDGET_S:
            self.note("latency", f"{label}: first seen after {seconds:.1f}s (case budget {CASE_BUDGET_S}s; "
                                 "includes page load + client render)")

    def finish(self) -> None:
        allure.attach("\n".join(self.notes) or "none", name=f"{self.tc} notes")
        if self.failures:
            allure.attach("\n".join(self.failures), name=f"{self.tc} failures")
        assert not self.failures, f"{self.tc}: " + " || ".join(self.failures)


def _attach(name: str, value) -> None:
    allure.attach(json.dumps(value, ensure_ascii=False, indent=1, default=str), name=name,
                  attachment_type=allure.attachment_type.JSON)


def _has(pattern: str, texts) -> bool:
    blob = " | ".join(str(t) for t in (texts if isinstance(texts, (list, tuple)) else [texts]))
    return re.search(pattern, blob, re.I) is not None


def _published_message(save: dict) -> bool:
    return any(MSG_SAVED_AND_PUBLISHED in t for t in save.get("messages", []))


def _refusal_texts(save: dict) -> list[str]:
    ev = save.get("evidence", {})
    return (list(ev.get("field_errors", [])) + [o.get("text", "") for o in ev.get("field_error_owners", [])]
            + list(ev.get("native_messages", {}).values()) + [t for t in ev.get("editbar", [])
                                                              if "Editing" not in t[:8]])


def _errors_for(save: dict, key: str) -> list[str]:
    """Inline errors whose owning block holds `key`, plus native messages of that input."""
    ev = save.get("evidence", {})
    owned = [o["text"] for o in ev.get("field_error_owners", []) if key in (o.get("field") or "")]
    native = [m for k, m in ev.get("native_messages", {}).items() if key in k and m]
    return owned + native


# ===========================================================================
# Fixtures
# ===========================================================================
class Registry:
    """Records THIS test captured, in creation order (teardown deletes in reverse)."""

    def __init__(self):
        self.entries: list[BGEntry] = []

    def track(self, entry: BGEntry) -> BGEntry:
        if not isinstance(entry, BGEntry) or not entry.in_namespace() or entry.prefix != PREFIX:
            raise ValueError(f"{entry} is not a {PREFIX} record")
        if all(e.entry_id != entry.entry_id for e in self.entries):
            self.entries.append(entry)
        return entry


@pytest.fixture
def disposable(browser):
    """Deletes ONLY the records the test registered at creation (guarded delete,
    children before their section) from a fresh Site Content Editor context."""
    registry = Registry()
    yield registry
    if not registry.entries:
        return
    ctx = new_context(browser, use_auth_state=False)
    outcome, failures = [], []
    try:
        page = ctx.new_page()
        login = BGAdminPageD(page, SLUG_SECTION, AGENT)
        if login.login_as_role(ROLE_EDITOR) != "ok":
            login.open_list_all()
            if login.signed_in_user()[0] != ROLE_USER_IDS[ROLE_EDITOR]:
                raise AssertionError("teardown could not sign in as the Site Content Editor")
        for entry in reversed(registry.entries):
            label = f"{entry.slug} {entry.entry_value[:70]!r} (id {entry.entry_id}, code {entry.code})"
            cleaner = BGAdminPageD(page, entry.slug, AGENT)
            try:
                cleaner.open_list_all()
                if not cleaner.row_present(entry):
                    (outcome if cleaner.is_list_fully_expanded() else failures).append(f"not listed: {label}")
                    continue
                cleaner.adopt(entry)
                done = cleaner.delete_disposable_entry(entry)
                if not done and cleaner.restore_entry_value(entry):
                    done = cleaner.delete_disposable_entry(entry)
                (outcome if done else failures).append(("removed " if done else "NOT removed ") + label)
            except Exception as exc:  # noqa: BLE001 — collected below
                failures.append(f"{label}: {exc!r}")
    finally:
        ctx.close()
    allure.attach("\n".join(outcome + failures) or "nothing to remove", name="QCTEST teardown")
    if failures:
        raise AssertionError("TEARDOWN LEFT QCTEST DATA BEHIND:\n" + "\n".join(failures))


@pytest.fixture
def anon(browser):
    """Factory of FRESH logged-out public views: anon(viewport=(w, h)) -> VisasPublicViewD."""
    contexts = []

    def _make(viewport: tuple = DESKTOP) -> VisasPublicViewD:
        ctx = new_context(browser, viewport=viewport, use_auth_state=False)
        contexts.append(ctx)
        return VisasPublicViewD(ctx.new_page())

    yield _make
    for ctx in contexts:
        try:
            ctx.close()
        except Exception:  # noqa: BLE001
            pass


# ===========================================================================
# Test-layer helpers (no raw Playwright)
# ===========================================================================
class D:
    """One Site Content Editor session: per-object drivers sharing one page."""

    def __init__(self, page, registry: Registry):
        self.registry = registry
        self.false_errors: list[dict] = []
        self.drivers: dict[str, BGAdminPageD] = {}
        self.page = page
        first = self.drv(SLUG_SECTION)
        outcome = first.login_as_role(ROLE_EDITOR)
        if outcome == "unknown":
            first.open_list_all()
            if first.signed_in_user()[0] == ROLE_USER_IDS[ROLE_EDITOR]:
                outcome = "ok"
        if outcome == "auth_failed":
            pytest.skip("PRECONDITION: Liferay refused the .env credentials for 'Site Content Editor'")
        if outcome != "ok":
            pytest.fail("login as 'Site Content Editor' neither succeeded nor showed Liferay's refusal banner")
        first.open_list_all()
        user_id, _ = first.signed_in_user()
        if user_id != ROLE_USER_IDS[ROLE_EDITOR]:
            pytest.skip(f"PRECONDITION: Editor credentials sign in as userId {user_id!r}, not 156488")

    def drv(self, slug: str) -> BGAdminPageD:
        if slug not in self.drivers:
            self.drivers[slug] = BGAdminPageD(self.page, slug, AGENT)
        return self.drivers[slug]

    def pinned(self) -> None:
        user_id, _ = self.drv(SLUG_SECTION).signed_in_user()
        assert user_id == ROLE_USER_IDS[ROLE_EDITOR], f"session is userId {user_id!r}, not the Editor 156488"

    # ---- create ---------------------------------------------------------------------
    def create(self, slug: str, data: dict, publish: bool = True, before_save=None) -> tuple:
        self.pinned()
        entry, evidence = self.drv(slug).create_with(data, publish=publish, before_save=before_save)
        _attach(f"create {slug} {str(data.get(self.drv(slug).entry_field))[:60]}", evidence)
        if entry is None:
            if evidence["save"]["went_through"]:
                pytest.fail(f"PRECONDITION: the {slug} record saved but could not be identified uniquely "
                            f"— STOP, check the list for {data.get(self.drv(slug).entry_field)!r}")
            return None, evidence
        self.registry.track(entry)
        if evidence.get("created_despite_error"):
            self.false_errors.append({"slug": slug, "entry_id": entry.entry_id, "messages": evidence["save"]["messages"],
                                      "requests": evidence["save"]["evidence"].get("save_requests"),
                                      "responses": evidence["save"]["evidence"].get("save_responses")})
            os.makedirs(EVIDENCE, exist_ok=True)
            with open(FINDINGS, "a", encoding="utf-8") as handle:
                handle.write(json.dumps({"kind": "false_save_error", "slug": slug, "entry_id": entry.entry_id,
                                         "status": self.status(entry), **self.false_errors[-1]},
                                        ensure_ascii=False) + "\n")
        return entry, evidence

    def saved_ok(self, evidence: dict) -> bool:
        """The record exists AND the form confirmed it (no false 'not saved' bar)."""
        return evidence["save"]["went_through"] and not evidence.get("created_despite_error")

    def must_create(self, slug: str, data: dict, publish: bool = True) -> BGEntry:
        entry, evidence = self.create(slug, data, publish=publish)
        if entry is None:
            pytest.fail(f"PRECONDITION: creating the {slug} record was refused: {evidence['save']}")
        return entry

    def section_data(self, tc: str, card: bool = False, **overrides) -> dict:
        title = f"{PREFIX}{tc}-{STAMP}"
        data = bg_data(SLUG_SECTION, title, section_key=title.lower(), displayOrder=SECTION_ORDER,
                       sectionTitle_ar=f"قسم اختبار {tc}-{STAMP}",
                       sectionBody=f"{title} QCTEST section body.", sectionBody_ar="نص قسم اختبار آلي.")
        if card:
            data.update(highlightCardEyebrow="QCTEST card", highlightCardEyebrow_ar="بطاقة اختبار",
                        highlightCardHeading=f"{title} card heading", highlightCardHeading_ar="عنوان بطاقة اختبار")
        data.update(overrides)
        return data

    def section(self, tc: str, card: bool = False, publish: bool = True, **overrides) -> tuple:
        data = self.section_data(tc, card=card, **overrides)
        entry = self.must_create(SLUG_SECTION, data, publish=publish)
        return entry, data

    # ---- state checks ------------------------------------------------------------------
    def status(self, entry: BGEntry) -> str:
        drv = self.drv(entry.slug)
        drv.open_list_all()
        return drv.row_status_of(entry)

    def live(self, *entries: BGEntry) -> list[str]:
        """Rule 3: each record Published in the list AND stored Active Status ticked (re-opened)."""
        problems = []
        for entry in entries:
            status = self.status(entry)
            active = self.drv(entry.slug).stored(entry)["activeStatus"]
            if status != STATUS_PUBLISHED or active != "true":
                problems.append(f"{entry.slug} {entry.entry_value[:60]!r}: status {status!r}, active {active!r}")
        return problems

    def require_live(self, *entries: BGEntry) -> None:
        problems = self.live(*entries)
        if problems:
            pytest.fail("PRECONDITION: not published + active before the public check: " + "; ".join(problems))


def _wait_page_rendered(view: VisasPublicViewD, locale: str = "en") -> None:
    """The real page may be briefly unpublished by Agent A (lock held). Wait it out."""
    view.open_page(locale)
    if view.is_rendered():
        return

    def _back() -> bool:
        view.open_page(locale)
        return view.is_rendered()

    try:
        wait_until(_back, timeout=1200.0 if os.path.exists(REAL_PAGE_LOCK) else 60.0, poll=15.0)
    except WaitTimeoutError:
        pytest.fail(f"PRECONDITION: the public Visas & Immigration page ({locale}) does not render "
                    f"(lock present: {os.path.exists(REAL_PAGE_LOCK)})")


def _public_row(anon, title: str, predicate, locale: str = "en", viewport: tuple = DESKTOP) -> tuple:
    """Fresh anonymous context; polls until the QCTEST row satisfies `predicate`."""
    view = anon(viewport)
    _wait_page_rendered(view, locale)
    ok, seconds, row = view.d_poll_row(title, predicate, timeout=PUBLIC_TIMEOUT_S, locale=locale)
    return view, ok, seconds, row


def _px(value: str) -> float:
    try:
        return float(str(value).replace("px", ""))
    except ValueError:
        return -1.0


def _style_diff(style: dict | None, size: str, weight: str, color: str) -> list[str]:
    if not style:
        return ["element not found"]
    out = []
    if "Cairo" not in style.get("font_family", ""):
        out.append(f"font {style.get('font_family')!r}")
    if style.get("font_size") != size:
        out.append(f"size {style.get('font_size')}")
    if style.get("font_weight") != weight:
        out.append(f"weight {style.get('font_weight')}")
    if style.get("color") != color:
        out.append(f"colour {style.get('color')}")
    return out


def _right_aligned(style: dict | None) -> bool:
    return bool(style) and (style.get("text_align") == "right"
                            or (style.get("direction") == "rtl" and style.get("text_align") in ("start", "")))


def _same_url(a: str, b: str) -> bool:
    return (a or "").rstrip("/") == (b or "").rstrip("/")


def _shot(view: VisasPublicViewD, name: str) -> str:
    return view.d_evidence(EVIDENCE, f"{name}_{STAMP}")


def _admin_shot(drv: BGAdminPageD, name: str) -> str:
    return drv.evidence(f"{name}_{STAMP}")


def _image_section(s: D, tc: str, file_path: str, stem: str, alt_en: str = ALT_EN, alt_ar: str = ALT_AR,
                   **overrides) -> tuple:
    data = s.section_data(tc, supportingImage_file=file_path, supportingImage_stem=stem,
                          supportingImageAltText=alt_en, supportingImageAltText_ar=alt_ar, **overrides)
    entry = s.must_create(SLUG_SECTION, data)
    return entry, data


def _link_data(key: str, title: str, **overrides) -> dict:
    return bg_data(SLUG_LINK, title, section_key=key, **overrides)


def _photo_ok(row: dict) -> bool:
    return bool(row and row.get("photo") and row["photo"].get("src"))


def _check_public_photo(c: Checks, view: VisasPublicViewD, title: str, stem: str, alt: str | None) -> dict:
    row = view.d_scroll_photo_into_view(title) or {}
    photo = row.get("photo") or {}
    _attach(f"public photo {title}", row)
    src = photo.get("src") or ""
    fetched = view.d_fetch_status(src) if src else {}
    _attach("photo GET (anonymous)", fetched)
    c.check(fetched.get("status") == 200, f"supporting image GET returned {fetched.get('status')} for {src!r}")
    c.check(stem.casefold() in src.casefold(), f"image src {src!r} does not resolve to the uploaded {stem}*.png")
    c.check(photo.get("complete") and photo.get("natural_w", 0) > 0, f"image did not load: {photo}")
    if alt is not None:
        c.check(photo.get("alt") == alt, f"alt attribute {photo.get('alt')!r} != {alt!r}")
    return row


# ===========================================================================
# 140317 — Arabic overview card + navigation path (REAL page, read-only) + Arabic CMS toast
# ===========================================================================
@AUTH_FREE_PAGE
@pytest.mark.ui
@pytest.mark.bilingual
@pytest.mark.tc_140317
@allure.title("Arabic variant renders the Arabic Reference overview card, the Arabic navigation path and the Arabic CMS success toast")
def test_140317_arabic_overview_card_nav_path_and_toast(page, browser, anon, disposable):
    c = Checks("140317")
    # Steps 1-3: public AR page, anonymous, the REAL rows (read-only).
    view = anon(DESKTOP)
    _wait_page_rendered(view, "ar")
    model = view.model()
    c.check(model["dir"] == "rtl", f"AR root dir {model['dir']!r}")
    c.check(model["crumbs"] == ["الرئيسية", "بوابة الأعمال"], f"AR navigation path {model['crumbs']}")
    s01, s03 = view.d_row_card(0), view.d_row_card(2)
    _attach("AR Section 01 card", s01)
    _attach("AR Section 03 card", s03)
    _shot(view, "140317_ar_public")
    card, checks = (s01 or {}).get("card"), (s01 or {}).get("checks")
    c.check(bool(card), "Section 01 renders no highlight card")
    if card:
        c.check(card["background_color"] == CARD_FILL,
                f"Section 01 card fill is {card['background_color']} (background-image {card['background_image']!r}), "
                f"not #F6F6F6 = {CARD_FILL}")
        c.check(bool(checks) and card["right"] <= checks["x"],
                f"card is not mirrored to the LEFT of the checklist (card x {card['x']}-{card['right']}, "
                f"checklist x {checks and checks['x']})")
    eyebrow, heading = (s01 or {}).get("eyebrow"), (s01 or {}).get("heading")
    c.check(bool(eyebrow) and eyebrow["text"] == "نظرة عامة مرجعية", f"card eyebrow {eyebrow and eyebrow['text']!r}")
    c.check(not _style_diff(eyebrow, "12px", "600", MAROON), f"card eyebrow style {_style_diff(eyebrow, '12px', '600', MAROON)}")
    want_heading = "تم تنظيم الصفحة حول رحلة المسافر عبر الوصول والمغادرة."
    c.check(bool(heading) and heading["text"] == want_heading, f"card heading {heading and heading['text']!r}")
    c.check(not _style_diff(heading, "20px", "700", INK), f"card heading style {_style_diff(heading, '20px', '700', INK)}")
    pills = (s01 or {}).get("pills") or []
    want_pills = ["الوصول", "إرشادات التأشيرة والبوابة الإلكترونية", "المغادرة"]
    c.check([p["text"] for p in pills] == want_pills, f"chips {[p['text'] for p in pills]} != {want_pills}")
    for pill in pills:
        c.check(not _style_diff(pill, "14px", "400", PILL_INK), f"chip {pill['text']!r} style {_style_diff(pill, '14px', '400', PILL_INK)}")
    eb3 = (s03 or {}).get("eyebrow")
    c.check(bool(eb3) and eb3["text"] == "قبل المغادرة", f"Section 03 card eyebrow {eb3 and eb3['text']!r}")
    c.check(not _style_diff(eb3, "12px", "600", MAROON), f"Section 03 eyebrow style {_style_diff(eb3, '12px', '600', MAROON)}")

    # Step 4: Arabic Control Panel session — change Card Eyebrow AR on our OWN
    # QCTEST section (the real Section 01 is never edited) and save.
    s = D(page, disposable)
    entry, data = s.section("140317", card=True)
    s.require_live(entry)
    new_eyebrow = f"نظرة عامة محدثة {STAMP[-4:]}"
    drv = s.drv(SLUG_SECTION)
    drv.open_owned(entry, locale="ar")
    c.check(drv.page.evaluate("() => document.documentElement.lang").startswith("ar"), "manage page did not open in Arabic")
    save = drv.edit_publish_typed(entry, {"highlightCardEyebrow_ar": new_eyebrow}, locale="ar")
    _attach("AR save evidence", save)
    _admin_shot(drv, "140317_ar_cms_after_save")
    c.check(save["went_through"], f"AR save did not go through: {save}")
    msgs = [m for m in save["messages"] if not m.startswith("Editing")]
    c.check(any(ARABIC.search(m) for m in msgs) and not any(MSG_SAVED_AND_PUBLISHED in m for m in msgs),
            f"the success message is not in Arabic: {msgs}")
    c.check(drv.stored(entry)["highlightCardEyebrow_ar"] == new_eyebrow, "Card Eyebrow AR not stored")
    s.require_live(entry)
    view2, ok, seconds, row = _public_row(
        anon, data["sectionTitle_ar"], lambda r: True, locale="ar")
    card_now = None

    def _eyebrow_updated() -> bool:
        nonlocal card_now
        view2.open_page("ar")
        rows = view2.model()["rows"]
        idx = next((i for i, r in enumerate(rows) if r["title"] == data["sectionTitle_ar"]), -1)
        card_now = view2.d_row_card(idx) if idx >= 0 else None
        return bool(card_now and card_now.get("eyebrow") and card_now["eyebrow"]["text"] == new_eyebrow)

    try:
        wait_until(_eyebrow_updated, timeout=PUBLIC_TIMEOUT_S, poll=0.5)
        shown = True
    except WaitTimeoutError:
        shown = False
    _attach("AR public QCTEST card after save", card_now)
    c.check(shown, f"updated Arabic eyebrow {new_eyebrow!r} not on the anonymous AR page: {card_now}")
    c.finish()


# ===========================================================================
# 140455 / 140507 — Supporting Image accepts a valid PNG < 2 MB and renders it
# ===========================================================================
@AUTH_FREE_PAGE
@pytest.mark.functional_low
@pytest.mark.tc_140455
@pytest.mark.tc_140507
@allure.title("Section Supporting Image accepts a valid PNG under 2 MB and renders it on the public page")
def test_140455_supporting_image_valid_png(page, anon, disposable):
    c = Checks("140455")
    s = D(page, disposable)
    stem = f"{PREFIX}ARRIVALS"
    data = s.section_data("140455", supportingImageAltText=ALT_EN, supportingImageAltText_ar=ALT_AR)

    def _upload(drv: BGAdminPageD) -> dict:
        control = drv.upload_field_state("supportingImage")
        result = drv.attempt_upload("supportingImage", PNG_640KB, stem)
        return {"control": control, "upload": result, "after": drv.upload_field_state("supportingImage"),
                "errors": drv.field_errors()}

    entry, evidence = s.create(SLUG_SECTION, data, before_save=_upload)
    before = evidence["before"]
    c.check("Select File" in before["control"]["text"], f"no Supporting Image upload control: {before['control']}")
    c.check(before["upload"]["attached"] and not before["upload"]["errors"],
            f"PNG not accepted cleanly: {before['upload']}")
    c.check(before["after"]["thumbnail"],
            f"no thumbnail preview after the upload (only the file name is shown until the record is saved): "
            f"{before['after']['text'][:200]!r}")
    c.check(entry is not None, f"save refused: {evidence['save']}")
    if entry is None:
        c.finish()
    c.check(_published_message(evidence["save"]), f"no 'Saved and published.': {evidence['save']['messages']}")
    stored = s.drv(SLUG_SECTION).upload_field_state("supportingImage")
    _attach("stored upload block", stored)
    c.check(stem.casefold() in stored["current_file"].casefold(), f"stored file {stored['current_file']!r}")
    c.check(stored["thumbnail"], f"no thumbnail preview on the saved record: {stored['text'][:200]}")
    c.check(s.status(entry) == STATUS_PUBLISHED, f"status {s.status(entry)!r}")
    s.require_live(entry)
    view, ok, seconds, row = _public_row(anon, data["sectionTitle"], _photo_ok)
    c.check(ok, f"public row shows no supporting image: {row}")
    c.latency("supporting image", seconds)
    if ok:
        row = _check_public_photo(c, view, data["sectionTitle"], stem, ALT_EN)
        photo = row.get("photo") or {}
        box = photo.get("box") or {}
        fit = photo.get("object_fit")
        natural = (photo.get("natural_w") or 0) / max(photo.get("natural_h") or 1, 1)
        rendered = (box.get("width") or 0) / max(box.get("height") or 1, 1)
        c.check(fit in ("cover", "contain", "scale-down") or abs(natural - rendered) < 0.02,
                f"image distorted: object-fit {fit!r}, natural ratio {natural:.3f}, box ratio {rendered:.3f}")
        c.check((photo.get("natural_w"), photo.get("natural_h")) == (1200, 800),
                f"served image is {photo.get('natural_w')}x{photo.get('natural_h')}, not 1200x800")
        _shot(view, "140455_public_photo")
    c.finish()


# ===========================================================================
# 140456 / 140508 — Supporting Image rejects SVG
# ===========================================================================
@AUTH_FREE_PAGE
@pytest.mark.functional_low
@pytest.mark.tc_140456
@pytest.mark.tc_140508
@allure.title("Section Supporting Image rejects a file type outside JPG and PNG")
def test_140456_supporting_image_rejects_svg(page, anon, disposable):
    c = Checks("140456")
    s = D(page, disposable)
    stem = f"{PREFIX}ARRIVALS"
    entry, data = _image_section(s, "140456", PNG_640KB, stem)
    drv = s.drv(SLUG_SECTION)
    drv.open_owned(entry)
    current = drv.upload_field_state("supportingImage")
    c.check(current["thumbnail"] and stem.casefold() in current["current_file"].casefold(),
            f"existing thumbnail / file not shown: {current}")
    result = drv.attempt_upload("supportingImage", SVG_120KB, f"{PREFIX}ARRIVALS-SVG")
    _attach("SVG upload attempt", result)
    _admin_shot(drv, "140456_svg_attempt")
    c.check(not result["attached"], f"SVG was attached to Supporting Image: {result['field_text'][:200]}")
    messages = result["errors"] + result.get("field_errors", []) + [result.get("picker_text", "")[:300]]
    c.check(_has(TYPE_PATTERN, result["errors"] + result.get("field_errors", [])),
            f"no file-type validation message: errors={result['errors']} field={result.get('field_errors')} "
            f"picker={result.get('picker_text', '')[:300]!r}")
    if result["errors"] and not _has(r"jpg|png", result["errors"]):
        c.note("wording", f"type error does not name JPG/PNG: {result['errors']}")
    save = drv.publish_open()
    _attach("publish after SVG attempt", save)
    stored = drv.stored(entry)
    c.check(stem.casefold() in stored["supportingImage_uploaded_as"].casefold()
            and stored["supportingImage_uploaded_as"].lower().endswith(".png"),
            f"stored Supporting Image is now {stored['supportingImage_uploaded_as']!r}")
    s.require_live(entry)
    view, ok, _, row = _public_row(anon, data["sectionTitle"], _photo_ok)
    c.check(ok and stem.casefold() in row["photo"]["src"].casefold() and ".svg" not in row["photo"]["src"].lower(),
            f"public image no longer the PNG: {row and row.get('photo')}")
    _ = messages
    c.finish()


# ===========================================================================
# 140457 / 140509 — Supporting Image 2 MB boundary
# ===========================================================================
@AUTH_FREE_PAGE
@pytest.mark.functional_low
@pytest.mark.tc_140457
@pytest.mark.tc_140509
@allure.title("Section Supporting Image enforces the 2 MB size limit at the boundary")
def test_140457_supporting_image_2mb_boundary(page, anon, disposable):
    c = Checks("140457")
    s = D(page, disposable)
    under, over = f"{PREFIX}ARRIVALS-UNDER", f"{PREFIX}ARRIVALS-OVER"
    data = s.section_data("140457", supportingImageAltText=ALT_EN, supportingImageAltText_ar=ALT_AR)

    def _upload(drv):
        return drv.attempt_upload("supportingImage", PNG_UNDER, under)

    entry, evidence = s.create(SLUG_SECTION, data, before_save=_upload)
    c.check(evidence["before"]["attached"] and not evidence["before"]["errors"],
            f"2,097,000-byte PNG not accepted cleanly: {evidence['before']}")
    c.check(entry is not None and _published_message(evidence["save"]), f"publish failed: {evidence['save']}")
    if entry is None:
        c.finish()
    s.require_live(entry)
    view, ok, seconds, row = _public_row(anon, data["sectionTitle"], _photo_ok)
    c.check(ok, f"no public image: {row}")
    c.latency("UNDER image", seconds)
    if ok:
        _check_public_photo(c, view, data["sectionTitle"], under, None)
    drv = s.drv(SLUG_SECTION)
    drv.open_owned(entry)
    result = drv.attempt_upload("supportingImage", PNG_OVER, over)
    _attach("OVER upload attempt", result)
    _admin_shot(drv, "140457_over_attempt")
    rejected_inline = _has(r"choose a smaller|accepts files up to|too large|exceed", result["field_text"])
    c.check(not result["attached"] or rejected_inline, f"2,097,500-byte PNG was attached: {result['field_text'][:200]}")
    if rejected_inline and re.search(r"is 2(\.0)? MB", result["field_text"]):
        c.note("wording", "the over-limit message says the 2,097,500-byte file 'is 2.0 MB' while the limit reads "
                          f"'up to 2 MB': {result['field_text'][:220]!r}")
    c.check(_has(SIZE_PATTERN, result["errors"] + result.get("field_errors", [])),
            f"no maximum-size message: errors={result['errors']} picker={result.get('picker_text', '')[:300]!r}")
    save = drv.publish_open()
    _attach("publish after OVER attempt", save)
    stored = drv.stored(entry)["supportingImage_uploaded_as"]
    c.check(under.casefold() in stored.casefold(), f"stored Supporting Image is now {stored!r}")
    view2, ok2, _, row2 = _public_row(anon, data["sectionTitle"], _photo_ok)
    c.check(ok2 and under.casefold() in row2["photo"]["src"].casefold(),
            f"public image changed: {row2 and row2.get('photo')}")
    c.finish()


# ===========================================================================
# 140458 / 140510 — section publishes with the optional Supporting Image empty
# ===========================================================================
@AUTH_FREE_PAGE
@pytest.mark.functional_low
@pytest.mark.tc_140458
@pytest.mark.tc_140510
@allure.title("A section saves and publishes with the optional Supporting Image left empty")
def test_140458_supporting_image_optional(page, anon, disposable):
    c = Checks("140458")
    s = D(page, disposable)
    data = s.section_data("140458")
    key = data["sectionKey"]
    blocks = []
    for n in range(1, 9):
        heading = f"{PREFIX}140458-{STAMP} block {n}"
        blocks.append(s.must_create(SLUG_SUBTOPIC, bg_data(
            SLUG_SUBTOPIC, heading, section_key=key, displayOrder=n * 100,
            blockHeading_ar=f"كتلة اختبار {n}", blockBody=f"QCTEST block {n} body.", blockBody_ar=f"نص كتلة {n}.")))

    def _empty_image(drv):
        return {"state": drv.upload_field_state("supportingImage"), "required": drv.field_required("supportingImage"),
                "errors": drv.field_errors()}

    entry, evidence = s.create(SLUG_SECTION, data, publish=False, before_save=_empty_image)
    before = evidence["before"]
    _attach("empty Supporting Image", before)
    c.check(not before["state"]["current_file"] and not before["state"]["thumbnail"], f"field not empty: {before['state']}")
    c.check(not before["required"]["native"] and not before["required"]["marked"],
            f"Supporting Image flagged mandatory: {before['required']}")
    c.check(not before["errors"], f"validation message shown: {before['errors']}")
    c.check(entry is not None and any(MSG_DRAFT_SAVED in m for m in evidence["save"]["messages"]),
            f"draft save failed: {evidence['save']}")
    if entry is None:
        c.finish()
    save = s.drv(SLUG_SECTION).edit_publish_typed(entry, {})
    _attach("publish", save)
    c.check(save["went_through"] and _published_message(save), f"publish failed: {save['messages']}")
    c.check(s.status(entry) == STATUS_PUBLISHED, f"status {s.status(entry)!r}")
    s.require_live(entry, *blocks)
    view, ok, seconds, row = _public_row(anon, data["sectionTitle"], lambda r: len(r["blocks"]) == 8)
    _attach("public row", row)
    c.check(ok, f"row does not render 8 blocks: {row and [b['heading'] for b in row['blocks']]}")
    c.latency("8 blocks", seconds)
    if row:
        c.check(row["photo"] is None and row["imgs_in_row"] == 0, f"image element rendered: {row['photo']}")
        c.check(row["rail"] is None and row["full"], f"empty rail / placeholder box rendered: rail={row['rail']}")
        c.check([b["heading"] for b in row["blocks"]] == [f"{PREFIX}140458-{STAMP} block {n}" for n in range(1, 9)],
                f"block order {[b['heading'] for b in row['blocks']]}")
    _shot(view, "140458_public_no_image")
    c.finish()


# ===========================================================================
# 140459 / 140511 — alt text stored bilingually and rendered
# ===========================================================================
@AUTH_FREE_PAGE
@pytest.mark.functional_low
@pytest.mark.accessibility
@pytest.mark.tc_140459
@pytest.mark.tc_140511
@allure.title("Supporting Image alt text is stored bilingually and rendered on the public page")
def test_140459_supporting_image_alt_bilingual(page, anon, disposable):
    c = Checks("140459")
    s = D(page, disposable)
    stem = f"{PREFIX}ARRIVALS"
    data = s.section_data("140459", supportingImage_file=PNG_640KB, supportingImage_stem=stem)

    def _alt(drv):
        drv.fill_en("supportingImageAltText", ALT_EN)
        drv.fill_ar("supportingImageAltText", ALT_AR)
        return {"errors": drv.field_errors()}

    entry, evidence = s.create(SLUG_SECTION, data, before_save=_alt)
    c.check(not evidence["before"]["errors"], f"validation message: {evidence['before']['errors']}")
    c.check(entry is not None and _published_message(evidence["save"]), f"publish failed: {evidence['save']}")
    if entry is None:
        c.finish()
    stored = s.drv(SLUG_SECTION).stored(entry)
    c.check(stored["supportingImageAltText"] == ALT_EN and stored["supportingImageAltText_ar"] == ALT_AR,
            f"stored alt EN {stored['supportingImageAltText']!r} / AR {stored['supportingImageAltText_ar']!r}")
    s.require_live(entry)
    view, ok, seconds, row = _public_row(anon, data["sectionTitle"], lambda r: _photo_ok(r) and r["photo"]["alt"] == ALT_EN)
    c.check(ok, f"EN alt {row and row.get('photo')}")
    c.latency("EN alt", seconds)
    view_ar, ok_ar, _, row_ar = _public_row(anon, data["sectionTitle_ar"],
                                            lambda r: _photo_ok(r) and r["photo"]["alt"] == ALT_AR, locale="ar")
    c.check(ok_ar, f"AR alt {row_ar and row_ar.get('photo')}")
    c.finish()


# ===========================================================================
# 140460 / 140512 — Supporting Image cannot be published with empty alt
# ===========================================================================
@AUTH_FREE_PAGE
@pytest.mark.functional_low
@pytest.mark.accessibility
@pytest.mark.tc_140460
@pytest.mark.tc_140512
@allure.title("A Supporting Image cannot be published with empty alt text")
def test_140460_supporting_image_empty_alt_blocked(page, anon, disposable):
    c = Checks("140460")
    s = D(page, disposable)
    stem = f"{PREFIX}ARRIVALS"
    entry, data = _image_section(s, "140460", PNG_640KB, stem)
    drv = s.drv(SLUG_SECTION)
    drv.open_owned(entry)
    drv.fill_en("supportingImageAltText", "")
    c.check(drv.text_value("supportingImageAltText") == "" and stem.casefold() in drv.stored_file_name("supportingImage").casefold(),
            "alt not empty / image not attached before publish")
    save = drv.publish_open()
    _attach("publish with empty alt", save)
    _admin_shot(drv, "140460_after_publish_empty_alt")
    c.check(not save["went_through"] and not _published_message(save),
            f"Publish was NOT blocked with an empty Alt Text EN; messages {save['messages']}")
    c.check(_has(r"alt|required|mandatory", _errors_for(save, "supportingImageAltText")),
            f"no validation error against Alt Text EN: {_refusal_texts(save)}")
    stored_alt = drv.stored(entry)["supportingImageAltText"]
    s.require_live(entry)
    view, ok, _, row = _public_row(anon, data["sectionTitle"], _photo_ok)
    alt = row and row["photo"] and row["photo"]["alt"]
    c.check(ok and alt == ALT_EN, f"public alt is now {alt!r} (stored Alt Text EN {stored_alt!r})")
    c.check(bool(alt), "public image rendered with an EMPTY alt attribute")
    _shot(view, "140460_public_alt")
    c.finish()


# ===========================================================================
# Official Source Links
# ===========================================================================
def _link_section(s: D, tc: str) -> tuple:
    entry, data = s.section(tc, card=True)
    return entry, data, data["sectionKey"]


def _one_link(row: dict | None, title: str) -> dict | None:
    for link in (row or {}).get("links", []):
        if link["title"] and link["title"]["text"] == title:
            return link
    return None


@AUTH_FREE_PAGE
@pytest.mark.functional_low
@pytest.mark.bilingual
@pytest.mark.tc_140461
@pytest.mark.tc_140513
@allure.title("Official Source Link Title accepts a valid bilingual value and renders it on the public page")
def test_140461_link_title_bilingual(page, anon, disposable):
    c = Checks("140461")
    s = D(page, disposable)
    sec, sdata, key = _link_section(s, "140461")
    title, title_ar = f"{PREFIX}140461-{STAMP} Ministry of Interior", "وزارة الداخلية"
    data = _link_data(key, title, linkTitle_ar=title_ar, url="https://portal.moi.gov.qa",
                      openBehavior=OPT_OPEN_NEW_TAB, displayOrder=100)
    link, evidence = s.create(SLUG_LINK, data, before_save=lambda d: {"errors": d.field_errors()})
    c.check(not evidence["before"]["errors"], f"validation message: {evidence['before']['errors']}")
    c.check(link is not None and _published_message(evidence["save"]), f"publish failed: {evidence['save']}")
    if link is None:
        c.finish()
    s.require_live(sec, link)
    view, ok, seconds, row = _public_row(anon, sdata["sectionTitle"], lambda r: _one_link(r, title) is not None)
    c.check(ok, f"EN link title not rendered: {row and row.get('links')}")
    c.latency("EN link title", seconds)
    item = _one_link(row, title)
    if item:
        c.check(not _style_diff(item["title"], "14px", "700", MAROON), f"EN title style {_style_diff(item['title'], '14px', '700', MAROON)}")
        c.check(abs(item["title"]["width"] - 720) <= 1, f"EN title box {item['title']['width']}px wide, not 720px")
    _shot(view, "140461_en")
    view_ar, ok_ar, _, row_ar = _public_row(anon, sdata["sectionTitle_ar"], lambda r: _one_link(r, title_ar) is not None, locale="ar")
    c.check(ok_ar, f"AR link title not rendered: {row_ar and row_ar.get('links')}")
    item_ar = _one_link(row_ar, title_ar)
    if item_ar:
        c.check(not _style_diff(item_ar["title"], "14px", "700", MAROON), f"AR title style {_style_diff(item_ar['title'], '14px', '700', MAROON)}")
        c.check(_right_aligned(item_ar["title"]), f"AR title not right-aligned: {item_ar['title']}")
    _shot(view_ar, "140461_ar")
    c.finish()


def _blocked_edit(c: Checks, s: D, entry: BGEntry, field: str, typed: str, pattern: str, label: str) -> dict:
    drv = s.drv(entry.slug)
    save = drv.edit_publish_typed(entry, {}, typed={field: typed})
    _attach(f"publish with {label}", save)
    _admin_shot(drv, f"{c.tc}_{field}_{label}")
    c.check(not save["went_through"] and not _published_message(save),
            f"Publish was NOT blocked with {label} in {field}; messages {save['messages']}")
    c.check(_has(pattern, _errors_for(save, field)),
            f"no validation error against {field}: {_refusal_texts(save)}")
    return save


@AUTH_FREE_PAGE
@pytest.mark.functional_low
@pytest.mark.tc_140462
@pytest.mark.tc_140514
@allure.title("Official Source Link Title rejects an empty mandatory value")
def test_140462_link_title_empty_rejected(page, anon, disposable):
    c = Checks("140462")
    s = D(page, disposable)
    sec, sdata, key = _link_section(s, "140462")
    title = f"{PREFIX}140462-{STAMP} Hamad International Airport"
    link = s.must_create(SLUG_LINK, _link_data(key, title, displayOrder=100))
    _blocked_edit(c, s, link, "linkTitle", "", REQUIRED_PATTERN, "an empty title")
    stored = s.drv(SLUG_LINK).stored(link)["linkTitle"]
    c.check(stored == title, f"stored Link Title EN is now {stored!r}")
    s.drv(SLUG_LINK).restore_entry_value(link)
    s.require_live(sec, link)
    view, ok, _, row = _public_row(anon, sdata["sectionTitle"], lambda r: _one_link(r, title) is not None)
    c.check(ok, f"public link no longer renders {title!r}: {row and row.get('links')}")
    c.finish()


def _limit_value(head: str, n: int) -> str:
    return (head + "A" * n)[:n]


def _arabic_value(n: int) -> str:
    """Realistic Arabic max-length text WITH word spaces (wraps like real copy); last char is a letter."""
    text = ("وزارة الداخلية القطرية " * 20)[:n]
    return text[:-1] + "ة" if text.endswith(" ") else text


def _frontend_limit_check(c: Checks, anon, sdata: dict, en_value: str, ar_value: str, part: str, tc: str) -> None:
    """Rule 6: max-length value on the public page, EN + AR, 1920 and 390."""
    for locale, title, value in (("en", sdata["sectionTitle"], en_value), ("ar", sdata["sectionTitle_ar"], ar_value)):
        for viewport in (DESKTOP, MOBILE):
            view, ok, seconds, row = _public_row(
                anon, title, lambda r: any(l[part] and l[part]["text"] == value for l in r["links"]),
                locale=locale, viewport=viewport)
            tag = f"{tc}_{part}_{locale}_{viewport[0]}"
            shot = _shot(view, tag)
            link = next((l for l in (row or {}).get("links", []) if l[part] and l[part]["text"] == value), None)
            layout = view.layout_report()
            _attach(f"frontend {tag}", {"row_link": link, "layout": layout, "shot": shot})
            c.check(ok, f"[{tag}] full {len(value)}-char {part} not rendered (truncated?): "
                        f"{[(l[part] or {}).get('text', '')[:40] for l in (row or {}).get('links', [])]}")
            if link:
                box = link[part]
                clipped = box["scroll_width"] > box["client_width"] + 1
                c.check(not clipped, f"[{tag}] {part} overflows its box (scroll {box['scroll_width']} > client "
                                     f"{box['client_width']}) — screenshot {shot}")
                if viewport == DESKTOP:
                    c.check(box["width"] <= 721, f"[{tag}] {part} box {box['width']}px wider than 720px")
            c.check(not layout["horizontal_scroll"], f"[{tag}] page scrolls horizontally "
                                                     f"({layout['scroll_width']} > {layout['client_width']}) — {shot}")


@AUTH_FREE_PAGE
@pytest.mark.functional_low
@pytest.mark.tc_140463
@pytest.mark.tc_140515
@allure.title("Official Source Link Title enforces its 200-character maximum at the boundary")
def test_140463_link_title_200_boundary(page, anon, disposable):
    c = Checks("140463")
    s = D(page, disposable)
    sec, sdata, key = _link_section(s, "140463")
    title = _limit_value(f"{PREFIX}LINKTITLE-200-{STAMP}-", 200)
    title_ar = _arabic_value(200)
    assert len(title) == 200 and len(title_ar) == 200
    data = _link_data(key, title, linkTitle_ar=title_ar, displayOrder=100)

    def _check_form(drv):
        return {"len": len(drv.text_value("linkTitle")), "counter": drv.counter_limit("linkTitle"),
                "errors": drv.field_errors()}

    link, evidence = s.create(SLUG_LINK, data, before_save=_check_form)
    c.check(evidence["before"]["len"] == 200 and not evidence["before"]["errors"],
            f"200-char value not accepted as typed: {evidence['before']}")
    c.check(link is not None and _published_message(evidence["save"]), f"publish failed: {evidence['save']}")
    if link is None:
        c.finish()
    s.require_live(sec, link)
    _frontend_limit_check(c, anon, sdata, title, title_ar, "title", "140463")
    drv = s.drv(SLUG_LINK)
    drv.open_owned(link)
    drv.fill_en("linkTitle", title + "A")
    typed_len = len(drv.text_value("linkTitle"))
    form_errors = drv.field_errors()
    save = drv.publish_open()
    _attach("201-char attempt", {"typed_len": typed_len, "form_errors": form_errors, "save": save})
    _admin_shot(drv, "140463_201_attempt")
    if typed_len == 200:
        c.note("observation", "the field truncated the 201st character on input")
    c.check(typed_len == 200 or (not save["went_through"] and _has(r"200|maximum|max|long|characters", _refusal_texts(save) + form_errors)),
            f"201 characters were not truncated nor refused with a max-length error: typed {typed_len}, "
            f"saved={save['went_through']}, messages {save['messages']}")
    stored = drv.stored(link)["linkTitle"]
    c.check(stored == title, f"stored Link Title EN has {len(stored)} characters (expected the 200-char value)")
    if stored != title:
        drv.restore_entry_value(link)
    c.finish()


@AUTH_FREE_PAGE
@pytest.mark.functional_low
@pytest.mark.tc_140464
@pytest.mark.tc_140516
@allure.title("Official Source Link Title rejects a whitespace-only value")
def test_140464_link_title_whitespace_rejected(page, anon, disposable):
    c = Checks("140464")
    s = D(page, disposable)
    sec, sdata, key = _link_section(s, "140464")
    title = f"{PREFIX}140464-{STAMP} Ministry of Interior"
    link = s.must_create(SLUG_LINK, _link_data(key, title, displayOrder=100))
    _blocked_edit(c, s, link, "linkTitle", "   ", REQUIRED_PATTERN, "three spaces")
    stored = s.drv(SLUG_LINK).stored(link)["linkTitle"]
    c.check(stored == title, f"stored Link Title EN is now {stored!r}")
    s.drv(SLUG_LINK).restore_entry_value(link)
    s.require_live(sec, link)
    view, ok, _, row = _public_row(anon, sdata["sectionTitle"], lambda r: _one_link(r, title) is not None)
    c.check(ok, f"public link no longer renders {title!r}: {row and row.get('links')}")
    c.check(bool(row) and row["blank_anchors"] == 0, f"blank anchor rendered: {row and row['links']}")
    c.finish()


@AUTH_FREE_PAGE
@pytest.mark.functional_low
@pytest.mark.bilingual
@pytest.mark.tc_140465
@pytest.mark.tc_140517
@allure.title("Official Source Link Description accepts a valid bilingual value and renders it on the public page")
def test_140465_link_description_bilingual(page, anon, disposable):
    c = Checks("140465")
    s = D(page, disposable)
    sec, sdata, key = _link_section(s, "140465")
    title = f"{PREFIX}140465-{STAMP} Ministry of Interior"
    desc = "QCTEST-130701 confirm current visa, immigration and departure requirements."
    desc_ar = "تأكد من متطلبات التأشيرة والهجرة والمغادرة الحالية."
    data = _link_data(key, title, linkDescription=desc, linkDescription_ar=desc_ar, displayOrder=100)
    link, evidence = s.create(SLUG_LINK, data, before_save=lambda d: {"errors": d.field_errors()})
    c.check(not evidence["before"]["errors"], f"validation message: {evidence['before']['errors']}")
    c.check(link is not None and _published_message(evidence["save"]), f"publish failed: {evidence['save']}")
    if link is None:
        c.finish()
    s.require_live(sec, link)
    view, ok, seconds, row = _public_row(anon, sdata["sectionTitle"],
                                         lambda r: (_one_link(r, title) or {}).get("desc") is not None)
    item = _one_link(row, title)
    c.check(ok and item and item["desc"]["text"] == desc, f"EN description {item and item.get('desc')}")
    c.latency("EN description", seconds)
    if item and item["desc"]:
        d, t = item["desc"], item["title"]
        c.check(not _style_diff(d, "14px", "400", GREY), f"EN description style {_style_diff(d, '14px', '400', GREY)}")
        c.check(abs(d["width"] - 720) <= 1, f"EN description box {d['width']}px, not 720px")
        c.check(d["y"] >= t["y"] + t["height"] - 1 and abs(d["x"] - t["x"]) <= 1,
                f"description not directly under the title (title {t['x']},{t['y']}+{t['height']}; desc {d['x']},{d['y']})")
    _shot(view, "140465_en")
    view_ar, ok_ar, _, row_ar = _public_row(anon, sdata["sectionTitle_ar"],
                                            lambda r: any(l["desc"] and l["desc"]["text"] == desc_ar for l in r["links"]),
                                            locale="ar")
    link_ar = next((l for l in (row_ar or {}).get("links", []) if l["desc"] and l["desc"]["text"] == desc_ar), None)
    c.check(ok_ar and link_ar is not None, f"AR description not rendered: {row_ar and row_ar.get('links')}")
    if link_ar:
        c.check(_right_aligned(link_ar["desc"]), f"AR description not right-aligned: {link_ar['desc']}")
    _shot(view_ar, "140465_ar")
    c.finish()


@AUTH_FREE_PAGE
@pytest.mark.functional_low
@pytest.mark.tc_140466
@pytest.mark.tc_140518
@allure.title("Official Source Link Description enforces its 250-character maximum at the boundary")
def test_140466_link_description_250_boundary(page, anon, disposable):
    c = Checks("140466")
    s = D(page, disposable)
    sec, sdata, key = _link_section(s, "140466")
    title = f"{PREFIX}140466-{STAMP} description boundary"
    desc = _limit_value("QCTEST-130701-LINKDESC-250-", 250)
    desc_ar = _arabic_value(250)
    assert len(desc) == 250 and desc.endswith("A" * 223) and len(desc_ar) == 250
    data = _link_data(key, title, linkDescription=desc, linkDescription_ar=desc_ar, displayOrder=100)

    def _check_form(drv):
        return {"len": len(drv.text_value("linkDescription")), "counter": drv.counter_limit("linkDescription"),
                "errors": drv.field_errors()}

    link, evidence = s.create(SLUG_LINK, data, before_save=_check_form)
    c.check(evidence["before"]["len"] == 250 and not evidence["before"]["errors"],
            f"250-char value not accepted as typed: {evidence['before']}")
    c.check(link is not None and _published_message(evidence["save"]), f"publish failed: {evidence['save']}")
    if link is None:
        c.finish()
    s.require_live(sec, link)
    _frontend_limit_check(c, anon, sdata, desc, desc_ar, "desc", "140466")
    drv = s.drv(SLUG_LINK)
    drv.open_owned(link)
    drv.fill_en("linkDescription", desc + "A")
    typed_len = len(drv.text_value("linkDescription"))
    form_errors = drv.field_errors()
    save = drv.publish_open()
    _attach("251-char attempt", {"typed_len": typed_len, "form_errors": form_errors, "save": save})
    _admin_shot(drv, "140466_251_attempt")
    if typed_len == 250:
        c.note("observation", "the field truncated the 251st character on input")
    c.check(typed_len == 250 or (not save["went_through"] and _has(r"250|maximum|max|long|characters", _refusal_texts(save) + form_errors)),
            f"251 characters were not truncated nor refused with a max-length error: typed {typed_len}, "
            f"saved={save['went_through']}, messages {save['messages']}")
    stored = drv.stored(link)["linkDescription"]
    c.check(stored == desc, f"stored Link Description EN has {len(stored)} characters (expected 250)")
    c.finish()


@AUTH_FREE_PAGE
@pytest.mark.functional_low
@pytest.mark.tc_140467
@pytest.mark.tc_140519
@allure.title("Official Source Link saves and publishes with the optional Link Description left empty")
def test_140467_link_description_optional(page, anon, disposable):
    c = Checks("140467")
    s = D(page, disposable)
    sec, sdata, key = _link_section(s, "140467")
    title = f"{PREFIX}140467-{STAMP} no description source"
    data = _link_data(key, title, linkDescription="", linkDescription_ar="", url="https://portal.moi.gov.qa",
                      openBehavior=OPT_OPEN_NEW_TAB, displayOrder=300)

    def _empty(drv):
        return {"en": drv.text_value("linkDescription"), "ar": drv.ar_value("linkDescription"),
                "required": drv.field_required("linkDescription"),
                "ar_label": drv.field_label("linkDescription"), "errors": drv.field_errors()}

    link, evidence = s.create(SLUG_LINK, data, publish=False, before_save=_empty)
    before = evidence["before"]
    _attach("empty descriptions", before)
    c.check(before["en"] == "" and before["ar"] == "", f"descriptions not empty: {before}")
    c.check(not before["required"]["native"] and not before["required"]["marked"], f"description flagged mandatory: {before}")
    c.check(not before["errors"], f"validation message: {before['errors']}")
    c.check(link is not None and any(MSG_DRAFT_SAVED in m for m in evidence["save"]["messages"]),
            f"save failed: {evidence['save']}")
    if link is None:
        c.finish()
    save = s.drv(SLUG_LINK).edit_publish_typed(link, {})
    c.check(save["went_through"] and _published_message(save), f"publish failed: {save['messages']}")
    c.check(s.status(link) == STATUS_PUBLISHED, f"status {s.status(link)!r}")
    s.require_live(sec, link)
    view, ok, seconds, row = _public_row(anon, sdata["sectionTitle"], lambda r: _one_link(r, title) is not None)
    item = _one_link(row, title)
    _attach("public link", item)
    c.check(ok, f"link not rendered: {row and row.get('links')}")
    if item:
        c.check(not _style_diff(item["title"], "14px", "700", MAROON), f"title style {_style_diff(item['title'], '14px', '700', MAROON)}")
        c.check(item["desc_nodes"] == 0 and item["empty_children"] == 0,
                f"description element / empty line rendered: desc_nodes {item['desc_nodes']}, empty {item['empty_children']}")
        c.check(item["href"] == "https://portal.moi.gov.qa", f"href {item['href']!r}")
    _shot(view, "140467_en")
    c.finish()


def _url_link(s: D, tc: str, open_behavior: str = OPT_OPEN_SAME_TAB, url: str = "https://portal.moi.gov.qa/en/services",
              suffix: str = "valid URL source", order: int = 400) -> tuple:
    sec, sdata, key = _link_section(s, tc)
    title = f"{PREFIX}{tc}-{STAMP} {suffix}"
    link = s.must_create(SLUG_LINK, _link_data(key, title, url=url, openBehavior=open_behavior, displayOrder=order))
    return sec, sdata, link, title


@AUTH_FREE_PAGE
@pytest.mark.functional_low
@pytest.mark.redirect
@pytest.mark.tc_140468
@pytest.mark.tc_140520
@allure.title("Official Source Link URL accepts a valid absolute URL and is used verbatim on the public page")
def test_140468_link_url_verbatim(page, anon, disposable):
    c = Checks("140468")
    s = D(page, disposable)
    url = "https://portal.moi.gov.qa/en/services"
    sec, sdata, key = _link_section(s, "140468")
    title = f"{PREFIX}140468-{STAMP} valid URL source"
    data = _link_data(key, title, url=url, openBehavior=OPT_OPEN_SAME_TAB, displayOrder=400)
    link, evidence = s.create(SLUG_LINK, data, before_save=lambda d: {"url": d.text_value("url"), "errors": d.field_errors()})
    c.check(evidence["before"]["url"] == url and not evidence["before"]["errors"], f"URL not accepted: {evidence['before']}")
    c.check(link is not None and _published_message(evidence["save"]), f"publish failed: {evidence['save']}")
    if link is None:
        c.finish()
    s.require_live(sec, link)
    view, ok, seconds, row = _public_row(anon, sdata["sectionTitle"], lambda r: _one_link(r, title) is not None)
    item = _one_link(row, title)
    c.check(ok and item and item["href"] == url, f"href {item and item['href']!r} != {url!r}")
    c.latency("href", seconds)
    if item:
        click = view.d_click_link(sdata["sectionTitle"], title)
        _attach("click", click)
        c.check(_same_url(click["nav_request_url"], url), f"navigation went to {click['nav_request_url']!r}")
        c.check(click["tabs_after"] == 1 and not click["popup_url"], f"a new tab opened: {click}")
    c.finish()


@AUTH_FREE_PAGE
@pytest.mark.functional_low
@pytest.mark.tc_140469
@pytest.mark.tc_140521
@allure.title("Official Source Link URL rejects a malformed value")
def test_140469_link_url_malformed_rejected(page, anon, disposable):
    c = Checks("140469")
    s = D(page, disposable)
    url, bad = "https://portal.moi.gov.qa/en/services", "htp:/portal moi gov qa"
    sec, sdata, link, title = _url_link(s, "140469")
    _blocked_edit(c, s, link, "url", bad, URL_PATTERN, "a malformed URL")
    stored = s.drv(SLUG_LINK).stored(link)["url"]
    c.check(stored == url, f"stored URL is now {stored!r}")
    s.require_live(sec, link)
    view, ok, _, row = _public_row(anon, sdata["sectionTitle"], lambda r: _one_link(r, title) is not None)
    item = _one_link(row, title)
    c.check(bool(item) and item["href"] == url, f"public href is {item and item['href']!r}")
    c.check(bad not in view.d_page_html(), "the malformed string appears in the public page")
    c.finish()


@AUTH_FREE_PAGE
@pytest.mark.functional_low
@pytest.mark.tc_140470
@pytest.mark.tc_140522
@allure.title("Official Source Link URL rejects a whitespace-only value")
def test_140470_link_url_whitespace_rejected(page, anon, disposable):
    c = Checks("140470")
    s = D(page, disposable)
    url = "https://portal.moi.gov.qa/en/services"
    sec, sdata, link, title = _url_link(s, "140470")
    _blocked_edit(c, s, link, "url", "   ", REQUIRED_PATTERN, "three spaces")
    stored = s.drv(SLUG_LINK).stored(link)["url"]
    c.check(stored == url, f"stored URL is now {stored!r}")
    s.require_live(sec, link)
    view, ok, _, row = _public_row(anon, sdata["sectionTitle"], lambda r: _one_link(r, title) is not None)
    item = _one_link(row, title)
    c.check(bool(item) and item["href"] == url, f"public href is {item and item['href']!r}")
    c.check(bool(row) and row["empty_href_anchors"] == 0, f"anchor with an empty href rendered: {row and row['links']}")
    c.finish()


@AUTH_FREE_PAGE
@pytest.mark.functional_low
@pytest.mark.redirect
@pytest.mark.tc_140471
@pytest.mark.tc_140523
@allure.title("Official Source Link with Open Behavior Same Tab opens in the current tab")
def test_140471_open_behavior_same_tab(page, anon, disposable):
    c = Checks("140471")
    s = D(page, disposable)
    url = "https://dohahamadairport.com"
    sec, sdata, key = _link_section(s, "140471")
    title = f"{PREFIX}140471-{STAMP} same tab source"
    data = _link_data(key, title, url=url, openBehavior=None, displayOrder=500)

    def _options(drv):
        options = drv.picklist_options("openBehavior")
        free = drv.picklist_free_text_stored("openBehavior", "Popup Window")
        drv.pick("openBehavior", OPT_OPEN_SAME_TAB)
        return {"options": options, "free_text": free, "selected": drv.picklist_value("openBehavior")}

    link, evidence = s.create(SLUG_LINK, data, before_save=_options)
    before = evidence["before"]
    _attach("Open Behavior options", before)
    c.check(before["options"]["labels"] == [OPT_OPEN_SAME_TAB, OPT_OPEN_NEW_TAB], f"options {before['options']}")
    # The combobox box is a typeahead filter: typed text must never become a stored value.
    c.check(before["free_text"]["stored_value"] == "" and before["free_text"]["stored_label"] == "",
            f"free text was accepted as an Open Behavior value: {before['free_text']}")
    c.check(before["selected"] == OPT_OPEN_SAME_TAB, f"selected {before['selected']!r}")
    c.check(link is not None and _published_message(evidence["save"]), f"publish failed: {evidence['save']}")
    if link is None:
        c.finish()
    s.require_live(sec, link)
    view, ok, seconds, row = _public_row(anon, sdata["sectionTitle"], lambda r: _one_link(r, title) is not None)
    item = _one_link(row, title)
    c.check(bool(item) and (not item["has_target"] or item["target"] == "_self"), f"target {item and item['target']!r}")
    c.latency("target", seconds)
    if item:
        click = view.d_click_link(sdata["sectionTitle"], title)
        _attach("click", click)
        c.check(click["tabs_after"] == 1 and not click["popup_url"], f"tab count {click['tabs_after']}: {click}")
        c.check(_same_url(click["nav_request_url"], url), f"current tab navigated to {click['nav_request_url']!r}")
    c.finish()


@AUTH_FREE_PAGE
@pytest.mark.functional_low
@pytest.mark.redirect
@pytest.mark.tc_140472
@pytest.mark.tc_140524
@allure.title("Official Source Link with Open Behavior New Tab opens in a new tab")
def test_140472_open_behavior_new_tab(page, anon, disposable):
    c = Checks("140472")
    s = D(page, disposable)
    url = "https://dohahamadairport.com"
    sec, sdata, link, title = _url_link(s, "140472", OPT_OPEN_SAME_TAB, url, "same tab source", 500)
    drv = s.drv(SLUG_LINK)
    drv.open_owned(link)
    c.check(drv.picklist_value("openBehavior") == OPT_OPEN_SAME_TAB, f"starts as {drv.picklist_value('openBehavior')!r}")
    drv.pick("openBehavior", OPT_OPEN_NEW_TAB)
    c.check(drv.picklist_value("openBehavior") == OPT_OPEN_NEW_TAB and not drv.field_errors(), "New Tab not selected cleanly")
    save = drv.publish_open()
    c.check(save["went_through"] and _published_message(save), f"publish failed: {save['messages']}")
    c.check(s.status(link) == STATUS_PUBLISHED, f"status {s.status(link)!r}")
    s.require_live(sec, link)
    view, ok, seconds, row = _public_row(anon, sdata["sectionTitle"],
                                         lambda r: (_one_link(r, title) or {}).get("target") == "_blank")
    item = _one_link(row, title)
    c.check(ok, f"target is {item and item['target']!r}, not _blank")
    c.latency("target _blank", seconds)
    if item:
        _attach("rel", item["rel"])
        click = view.d_click_link(sdata["sectionTitle"], title)
        _attach("click", click)
        c.check(click["tabs_after"] == 2, f"tab count {click['tabs_after']}")
        c.check(_same_url(click["popup_request_url"], url) or _same_url(click["popup_url"], url)
                or click["popup_url"].startswith(url), f"new tab at {click['popup_url']!r}")
        c.check("visas-immigration" in click["current_url"], f"original tab moved to {click['current_url']!r}")
    c.finish()


# ===========================================================================
# Display Order
# ===========================================================================
CHK_LINKED = "Use the linked official sources for the latest requirements, fees and airport procedures."
CHK_PASSPORT = "Keep your passport and required travel documents ready for immigration checks."
CHK_VISA = "Check visa and entry requirements before starting your journey."


def _checklist(s: D, key: str, text: str, order: int, active: bool = True) -> BGEntry:
    return s.must_create(SLUG_CHECKLIST, bg_data(SLUG_CHECKLIST, key, itemText=text, itemText_ar="بند اختبار",
                                                 displayOrder=order, activeStatus=active))


def _verify_text(c: Checks, s: D, entry: BGEntry, text: str) -> None:
    stored = s.drv(SLUG_CHECKLIST).stored(entry)["itemText"]
    c.check(" ".join(stored.split()) == text, f"item {entry.entry_id} reads {stored!r}, not {text!r}")


@AUTH_FREE_PAGE
@pytest.mark.functional_low
@pytest.mark.tc_140473
@pytest.mark.tc_140525
@allure.title("Display Order accepts a valid positive integer and orders the items accordingly on the public page")
def test_140473_display_order_reorders(page, anon, disposable):
    c = Checks("140473")
    s = D(page, disposable)
    sec, sdata = s.section("140473", card=True)
    key = sdata["sectionKey"]
    visa = _checklist(s, key, CHK_VISA, 100)
    passport = _checklist(s, key, CHK_PASSPORT, 200)
    linked = _checklist(s, key, CHK_LINKED, 300)
    drv = s.drv(SLUG_CHECKLIST)
    _verify_text(c, s, linked, CHK_LINKED)       # resolved by its exact text, not by grid position
    save1 = drv.edit_publish_typed(linked, {}, typed={"displayOrder": "100"})
    c.check(save1["went_through"] and not _errors_for(save1, "displayOrder"), f"100 not accepted: {save1['messages']}")
    _verify_text(c, s, visa, CHK_VISA)
    save2 = drv.edit_publish_typed(visa, {}, typed={"displayOrder": "300"})
    c.check(save2["went_through"] and not _errors_for(save2, "displayOrder"), f"300 not accepted: {save2['messages']}")
    c.check(_published_message(save1) and _published_message(save2), f"no 'Saved and published.': {save1['messages']} / {save2['messages']}")
    c.check(drv.stored(linked)["displayOrder"] == "100" and drv.stored(visa)["displayOrder"] == "300", "stored orders differ")
    s.require_live(sec, visa, passport, linked)
    want = [CHK_LINKED, CHK_PASSPORT, CHK_VISA]
    view, ok, seconds, row = _public_row(anon, sdata["sectionTitle"],
                                         lambda r: [x["text"] for x in r["checklist"]] == want)
    c.check(ok, f"checklist order {row and [x['text'] for x in row['checklist']]} != {want}")
    c.latency("reorder", seconds)
    c.finish()


def _two_blocks(s: D, tc: str, name: str, name_order: int, other_order: int) -> tuple:
    sec, sdata = s.section(tc)
    key = sdata["sectionKey"]
    other = s.must_create(SLUG_SUBTOPIC, bg_data(SLUG_SUBTOPIC, f"{PREFIX}{tc}-{STAMP} BLK-OTHER", section_key=key,
                                                 displayOrder=other_order))
    target = s.must_create(SLUG_SUBTOPIC, bg_data(SLUG_SUBTOPIC, f"{PREFIX}{tc}-{STAMP} {name}", section_key=key,
                                                  displayOrder=name_order))
    return sec, sdata, target, other


def _block_order(row: dict | None) -> list[str]:
    return [b["heading"] for b in (row or {}).get("blocks", [])]


@AUTH_FREE_PAGE
@pytest.mark.functional_low
@pytest.mark.tc_140474
@pytest.mark.tc_140526
@allure.title("Display Order rejects a negative value")
def test_140474_display_order_negative_rejected(page, anon, disposable):
    c = Checks("140474")
    s = D(page, disposable)
    sec, sdata, egate, other = _two_blocks(s, "140474", "BLK-EGATE", 100, 200)
    s.require_live(sec, egate, other)
    want = [egate.entry_value, other.entry_value]
    _, ok0, _, row0 = _public_row(anon, sdata["sectionTitle"], lambda r: _block_order(r) == want)
    c.check(ok0, f"baseline block order {_block_order(row0)}")
    drv = s.drv(SLUG_SUBTOPIC)
    drv.open_owned(egate)
    drv.type_into("displayOrder", "-1")
    c.check(drv.text_value("displayOrder") == "-1", f"-1 not entered: {drv.text_value('displayOrder')!r}")
    save = drv.publish_open()
    _attach("publish with -1", save)
    _admin_shot(drv, "140474_minus_one")
    c.check(not save["went_through"] and not _published_message(save),
            f"Publish was NOT blocked with Display Order -1; messages {save['messages']}")
    c.check(_has(ORDER_PATTERN, _errors_for(save, "displayOrder")),
            f"no positive-integer error against Display Order: {_refusal_texts(save)}")
    stored = drv.stored(egate)["displayOrder"]
    c.check(stored == "100", f"stored Display Order is now {stored!r}")
    _, ok, _, row = _public_row(anon, sdata["sectionTitle"], lambda r: len(r["blocks"]) == 2)
    c.check(_block_order(row) == want, f"public block order changed: {_block_order(row)}")
    c.finish()


@AUTH_FREE_PAGE
@pytest.mark.functional_low
@pytest.mark.tc_140475
@pytest.mark.tc_140527
@allure.title("Display Order rejects zero as the boundary below the positive-integer minimum")
def test_140475_display_order_zero_rejected(page, anon, disposable):
    c = Checks("140475")
    s = D(page, disposable)
    sec, sdata, exit_block, other = _two_blocks(s, "140475", "BLK-EXIT", 300, 200)
    drv = s.drv(SLUG_SUBTOPIC)
    save1 = drv.edit_publish_typed(exit_block, {}, typed={"displayOrder": "100"})
    c.check(save1["went_through"] and _published_message(save1) and not _errors_for(save1, "displayOrder"),
            f"lowest valid value 100 not accepted: {save1['messages']}")
    s.require_live(sec, exit_block, other)
    want = [exit_block.entry_value, other.entry_value]
    _, ok1, seconds, row1 = _public_row(anon, sdata["sectionTitle"], lambda r: _block_order(r) == want)
    c.check(ok1, f"block does not render first: {_block_order(row1)}")
    c.latency("block first", seconds)
    drv.open_owned(exit_block)
    drv.type_into("displayOrder", "0")
    c.check(drv.text_value("displayOrder") == "0", f"0 not entered: {drv.text_value('displayOrder')!r}")
    save = drv.publish_open()
    _attach("publish with 0", save)
    _admin_shot(drv, "140475_zero")
    c.check(not save["went_through"] and not _published_message(save),
            f"Publish was NOT blocked with Display Order 0; messages {save['messages']}")
    c.check(_has(ORDER_PATTERN, _errors_for(save, "displayOrder")),
            f"no positive-integer error against Display Order: {_refusal_texts(save)}")
    stored = drv.stored(exit_block)["displayOrder"]
    c.check(stored == "100", f"stored Display Order is now {stored!r}")
    _, ok, _, row = _public_row(anon, sdata["sectionTitle"], lambda r: len(r["blocks"]) == 2)
    c.check(_block_order(row) == want, f"public block order changed: {_block_order(row)}")
    c.finish()


@AUTH_FREE_PAGE
@pytest.mark.functional_low
@pytest.mark.tc_140476
@pytest.mark.tc_140528
@allure.title("Display Order rejects a whitespace-only value")
def test_140476_display_order_whitespace_rejected(page, anon, disposable):
    c = Checks("140476")
    s = D(page, disposable)
    sec, sdata, key = _link_section(s, "140476")
    moi_title = f"{PREFIX}140476-{STAMP} Ministry of Interior"
    moi = s.must_create(SLUG_LINK, _link_data(key, moi_title, displayOrder=100))
    second = s.must_create(SLUG_LINK, _link_data(key, f"{PREFIX}140476-{STAMP} second source", displayOrder=200))
    drv = s.drv(SLUG_LINK)
    drv.open_owned(moi)
    drv.type_into("displayOrder", "   ")
    entered = drv.text_value("displayOrder")
    _attach("value after typing three spaces", repr(entered))
    if entered == "":
        c.note("observation", "the number input cannot hold spaces: typing three spaces leaves it empty")
    save = drv.publish_open()
    _attach("publish with whitespace", save)
    _admin_shot(drv, "140476_whitespace")
    c.check(not save["went_through"] and not _published_message(save),
            f"Publish was NOT blocked with a whitespace Display Order; messages {save['messages']}")
    c.check(_has(ORDER_PATTERN, _errors_for(save, "displayOrder")),
            f"no required / positive-integer error against Display Order: {_refusal_texts(save)}")
    stored = drv.stored(moi)["displayOrder"]
    c.check(stored == "100", f"stored Display Order is now {stored!r}")
    s.require_live(sec, moi, second)
    _, ok, _, row = _public_row(anon, sdata["sectionTitle"], lambda r: len(r["links"]) == 2)
    titles = [l["title"]["text"] for l in (row or {}).get("links", [])]
    c.check(bool(titles) and titles[0] == moi_title, f"Section link order {titles}")
    c.finish()


# ===========================================================================
# Repeatable item Active Status
# ===========================================================================
TOGGLE = "QCTEST-130701 toggle probe checklist item"
BASE_ITEMS = (CHK_VISA, CHK_PASSPORT, CHK_LINKED)


def _toggle_section(s: D, tc: str, toggle_active: bool) -> tuple:
    sec, sdata = s.section(tc, card=True)   # rail like the real Section 01 -> same 730 px item box
    key = sdata["sectionKey"]
    base = [_checklist(s, key, text, (i + 1) * 100) for i, text in enumerate(BASE_ITEMS)]
    toggle = _checklist(s, key, TOGGLE, 400, active=toggle_active)
    return sec, sdata, base, toggle


def _texts(row: dict | None) -> list[str]:
    return [x["text"] for x in (row or {}).get("checklist", [])]


@AUTH_FREE_PAGE
@pytest.mark.functional_low
@pytest.mark.tc_140531
@allure.title("Setting a repeatable item Active Status to Active makes the item appear on the public page")
def test_140531_item_active_makes_visible(page, anon, disposable):
    c = Checks("140531")
    s = D(page, disposable)
    sec, sdata, base, toggle = _toggle_section(s, "140531", toggle_active=False)
    s.require_live(sec, *base)
    view, ok0, _, row0 = _public_row(anon, sdata["sectionTitle"], lambda r: len(r["checklist"]) == 3)
    c.check(ok0 and _texts(row0) == list(BASE_ITEMS), f"baseline checklist {_texts(row0)}")
    c.check(TOGGLE not in view.d_page_html(), "the inactive item's text is in the public response")
    drv = s.drv(SLUG_CHECKLIST)
    actives = {e.entry_id: drv.stored(e)["activeStatus"] for e in base + [toggle]}
    c.check(actives[toggle.entry_id] == "false" and all(actives[e.entry_id] == "true" for e in base),
            f"four items with Active Status {actives}")
    _verify_text(c, s, toggle, TOGGLE)
    drv.open_owned(toggle)
    drv.set_active_status(True)
    c.check(drv.active_status_stored() == "true", "toggle does not read Active")
    save = drv.publish_open()
    c.check(save["went_through"] and _published_message(save), f"publish failed: {save['messages']}")
    c.check(s.status(toggle) == STATUS_PUBLISHED, f"status {s.status(toggle)!r}")
    s.require_live(toggle)
    view2, ok, seconds, row = _public_row(anon, sdata["sectionTitle"], lambda r: len(r["checklist"]) == 4)
    c.check(ok and _texts(row)[3:] == [TOGGLE], f"checklist {_texts(row)}")
    c.latency("activated item", seconds)
    if ok:
        fourth = row["checklist"][3]
        c.check(not _style_diff(fourth, "16px", "400", GREY), f"style {_style_diff(fourth, '16px', '400', GREY)}")
        c.check(abs(fourth["width"] - 730) <= 1, f"item box {fourth['width']}px, not 730px")
    c.finish()


@AUTH_FREE_PAGE
@pytest.mark.functional_low
@pytest.mark.tc_140532
@allure.title("A repeatable item Active Status toggle persists both states and re-activating restores the item")
def test_140532_item_active_toggle_persists(page, anon, disposable):
    c = Checks("140532")
    s = D(page, disposable)
    sec, sdata, base, toggle = _toggle_section(s, "140532", toggle_active=True)
    s.require_live(sec, *base, toggle)
    _, ok0, _, row0 = _public_row(anon, sdata["sectionTitle"], lambda r: len(r["checklist"]) == 4)
    c.check(ok0 and _texts(row0)[3:] == [TOGGLE], f"precondition: 4th item {_texts(row0)}")
    drv = s.drv(SLUG_CHECKLIST)
    _verify_text(c, s, toggle, TOGGLE)
    save = drv.edit_publish_typed(toggle, {"activeStatus": False})
    c.check(save["went_through"] and _published_message(save), f"deactivate publish failed: {save['messages']}")
    status = s.status(toggle)
    c.check(status in (STATUS_PUBLISHED, STATUS_INACTIVE), f"status after deactivation {status!r}")
    if status != STATUS_PUBLISHED:
        c.note("observation", f"the list badge reads {status!r} (not Published) for the deactivated item")
    actives = {e.entry_id: drv.stored(e)["activeStatus"] for e in base + [toggle]}
    c.check(actives[toggle.entry_id] == "false", f"Inactive did not persist: {actives}")
    c.check(all(actives[e.entry_id] == "true" for e in base), f"other items changed: {actives}")
    view, ok1, seconds, row1 = _public_row(anon, sdata["sectionTitle"], lambda r: len(r["checklist"]) == 3)
    c.check(ok1 and TOGGLE not in _texts(row1), f"after deactivation {_texts(row1)}")
    c.check(TOGGLE not in view.d_page_html(), "the deactivated item's text is in the public response")
    c.latency("deactivated item", seconds)
    save2 = drv.edit_publish_typed(toggle, {"activeStatus": True})
    c.check(save2["went_through"] and _published_message(save2), f"re-activate publish failed: {save2['messages']}")
    c.check(drv.stored(toggle)["activeStatus"] == "true", "Active did not persist on re-open")
    s.require_live(toggle)
    _, ok2, seconds2, row2 = _public_row(anon, sdata["sectionTitle"], lambda r: len(r["checklist"]) == 4)
    c.check(ok2 and _texts(row2) == list(BASE_ITEMS) + [TOGGLE], f"after re-activation {_texts(row2)}")
    c.latency("re-activated item", seconds2)
    c.finish()
