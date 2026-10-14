"""
cms/tests/home_dynamic_widgets/test_home_dynamic_widgets_control_panel.py —
Control_Panel cases for PBI 129384 (QC-HOME-008 Dynamic Widgets), suite 134455.

REWRITTEN 2026-10-08 (Phase 3, user order of 2026-10-07):
  - Real shared data is untouched. The two real records
    (`QCDEMO-129384-directory` = the "Marhaba Guide" card,
    `QCDEMO-129384-b2b-verified` = the "B2B Platform" card) are READ only.
    Every case that configures "the Marhaba Guide widget" or "the B2B
    Platform widget" runs on a NEW disposable DynamicWidget record (the
    object has no widget-type field, so a new record of the same object IS
    a Marhaba/B2B widget configuration; its card renders in the same row).
  - Account: QC Site Content Editor via `cms_role_credentials()` (Editor ->
    Published directly); Site Member for denial; logged-out context for
    anonymous and for every public-page read. Never TEST_USER.
  - Both visibility gates: a record that must show publicly is Published
    AND Active; a record that must not is left Active unticked.
  - Identity: entry code from the post-save URL + the QCTEST marker in its
    Redirect URL (see the Page Object). Never row position.
  - Save is clicked ONCE (`click_submit_once`), never Save as Draft.
  - Teardown, every run: Active unticked first (off the public site), then
    deleted by verified code (`delete_qctest`).

Weather: the guide's DynamicWidget object has no Weather record or field and
the Object Authoring sidebar has no Weather object; the Weather card is the
`qc-weather-widget` client extension. The Weather-configuration cases assert
the case's own expectation (a Weather configuration exists) and fail with
that evidence; the PBI's own admin workflow step 3 lists only "Marhaba Guide,
or B2B Platform", so the verdict is an open PBI question, not a bug.
"""

from __future__ import annotations

import re
import time

import allure
import pytest

from cms.pages.components.disposable_object_admin import ROLE_EDITOR, ROLE_SITE_MEMBER
from cms.pages.components.object_authoring_page import (
    STATUS_PUBLISHED,
    STATUS_UNPUBLISHED,
)
from cms.pages.control_panel.login_page import CmsLoginPage
from cms.pages.home_dynamic_widgets.home_dynamic_widgets_admin_page import (
    B2B_ERC,
    MARHABA_ERC,
    DynamicWidgetAdminPage,
    marker_url,
)
from cms.tests import authoring_checks as checks
from cms.tests.live_write_guard import LiveRecord, keep_instead_of_delete
from cms.tests.home_dynamic_widgets import upload_files as uf
from config.settings import control_panel_url
from core.web.browser import new_context
from web.pages.home_dynamic_widgets.home_dynamic_widgets_page import HomeDynamicWidgetsPage

pytestmark = [pytest.mark.control_panel, pytest.mark.global_, pytest.mark.pbi_129384, pytest.mark.timeout(300)]

KB = 1024
MB = 1024 * 1024
PUBLIC_TIMEOUT_S = 120  # measured live 2026-10-08: see report §4 (propagation)
INACTIVE = "INACTIVE"

# Tests that put a disposable card on the public Home page, or assert the
# public card set, run one at a time.
PUBLIC_GROUP = pytest.mark.xdist_group("dynamic_widgets_public_row")

MARHABA_URL = "https://marhabaguide.qa/qatar-chamber"
B2B_URL = "https://b2b.qatarchamber.com/platform"


def tc(*ids):
    """allure + pytest marks for the given Azure test case ids."""
    def deco(fn):
        for i in ids:
            fn = getattr(pytest.mark, f"tc_{i}")(fn)
        fn = allure.label("testcase", ",".join(str(i) for i in ids))(fn)
        fn = allure.label("pbi", "129384")(fn)
        fn = allure.feature("Dynamic Widgets")(fn)
        return fn
    return deco


# ---------------------------------------------------------------------------
# fixtures
# ---------------------------------------------------------------------------
@pytest.fixture
def dw(page):
    """Editor-signed-in Page Object; tears down every record it created."""
    admin = DynamicWidgetAdminPage(page)
    admin.sign_in(ROLE_EDITOR)
    yield admin
    # Teardown: take every record this test created off the public site, then
    # delete it by its own entry code (user approval 2026-10-12). Codes are
    # also logged in .claude/qa-runs/129384_qctest_ledger.txt.
    report = []
    for code in list(admin.created):
        report.append(f"{code}: inactive={admin.deactivate(code)}")
    for _ in range(3):  # final guard: nothing this test made may stay public
        leaks = admin.public_leaks()
        if not leaks:
            break
        for code in leaks:
            admin.remember(code)
            report.append(f"{code}: leak found in public feed, inactive={admin.deactivate(code)}")
    left = admin.public_leaks()
    report.append(f"public leaks after teardown: {left}")
    # Then delete every record this test created (user approval 2026-10-12).
    undeleted = []
    for code in list(admin.created):
        # User decision 2026-10-13: under QC_ALLOW_LIVE_SINGLETON_WRITES=1
        # nothing is deleted -- the record (already deactivated above) is
        # kept and logged for manual cleanup.
        if keep_instead_of_delete(LiveRecord("dynamic-widget", code, "disposable QCTEST Dynamic Widget"), code,
                                  note="Active Status unticked; left for manual cleanup (nothing is deleted "
                                       "under the opt-in)"):
            report.append(f"{code}: kept (deletes suppressed)")
            continue
        ok = admin.delete_created(code)
        report.append(f"{code}: deleted={ok}")
        if not ok:
            undeleted.append(code)
    allure.attach(" | ".join(report), name="teardown (Active unticked, then deleted)")
    assert not left, f"TEARDOWN FAILED — QCTEST card(s) still public: {left}"
    assert not undeleted, f"TEARDOWN FAILED — test record(s) not deleted: {undeleted}"


@pytest.fixture(scope="module", autouse=True)
def _public_qctest_sweep(browser):
    """Run-level guard (per xdist worker): after this module, any public card
    with QCTEST-named images is unticked and re-read; a failure is loud."""
    yield
    ctx = new_context(browser, use_auth_state=False)
    try:
        admin = DynamicWidgetAdminPage(ctx.new_page())
        admin.sign_in(ROLE_EDITOR)
        swept = admin.sweep_public_qctest()
        with open(".claude/qa-runs/129384_sweep_log.txt", "a", encoding="utf-8") as fh:
            fh.write(f"{time.strftime('%H:%M:%S')} swept={swept} left={admin.public_leaks()}" + chr(10))
        assert all(swept.values()), f"QCTEST card(s) could not be taken off the public site: {swept}"
    finally:
        ctx.close()


@pytest.fixture
def anon(browser):
    """Fresh logged-out context (standards.md: Logged-Out Context). External
    widget targets are answered locally so a click proves the navigation
    target without depending on third-party sites."""
    ctx = new_context(browser, use_auth_state=False, viewport=(1920, 1080))
    ctx.route(re.compile(r"https://(qctest-\d+\.example\.com|marhabaguide\.qa|b2b\.qatarchamber\.com)/.*"),
              lambda r: r.fulfill(status=200, content_type="text/html",
                                  body="<html><body>QCTEST external target</body></html>"))
    home = HomeDynamicWidgetsPage(ctx.new_page())
    yield home
    ctx.close()


def wait_card(home: HomeDynamicWidgetsPage, erc: str, present: bool = True,
              timeout: float = PUBLIC_TIMEOUT_S) -> list[dict]:
    """Reload the public Home page until the card for `erc` is (not) there.
    The reload is the polled condition; `timeout` is the upper bound."""
    end = time.monotonic() + timeout
    items: list[dict] = []
    while True:
        home.open_home()
        items = home.row_items()
        if any(i["erc"] == erc and i["visible"] for i in items) == present:
            return items
        if time.monotonic() > end:
            raise AssertionError(
                f"card {erc} {'never appeared' if present else 'still rendered'} on the public Home page "
                f"within {timeout:.0f}s; row = {[(i['kind'], i['erc']) for i in items]}")
        home.page.wait_for_timeout(5000)


def ercs(items):
    return [i["erc"] for i in items if i["kind"] == "card"]


def create_public(dw, tc_id, short, **kw) -> str:
    kw.setdefault("active", True)
    code = dw.create(tc_id, short, **kw)
    assert dw.status_now() == STATUS_PUBLISHED, f"Editor submit did not land on Published ({dw.status_now()})"
    assert dw.flag("active_status") is True
    return code


def refused_create(dw, *, url=None, order="9900", image_en=True, image_ar=True, active=False, tag=""):
    """Fill a NEW form (as given), click Publish once, and return
    (outcome, refusal text, code-or-''). Rows are counted around it."""
    dw.snapshot_codes()
    before = dw.row_count()
    dw.open_new()
    dw.fill_form(url=url, order=order, active=active, new_tab=False,
                 image_en=uf.valid("marhaba_en.jpg") if image_en is True else (image_en or None),
                 image_ar=uf.valid("marhaba_ar.png") if image_ar is True else (image_ar or None), tag=tag)
    outcome = dw.click_submit_once()
    text = dw.refusal_text()
    code = dw.code_from_url() or dw.find_saved(url or "", timeout=10)
    allure.attach(f"order field held {dw.page.get_by_role('spinbutton', name=dw.label_pattern('Display Order')).input_value()!r}"
                  if dw.page.get_by_role('spinbutton', name=dw.label_pattern('Display Order')).count() else "", name="form state")
    if code:
        dw.remember(code, url)
    stored = dw.count_by_url(url) if url and "QCTEST-" in url else None
    dw.open_list_all()
    after = dw.row_count()
    return outcome, text, code, before, after, stored


def assert_refused(result, what: str):
    """Blocked = no record code after the single Publish click, no entry
    stored with the attempt's unique marker URL, and a refusal shown. Row
    counts are attached for information only (other xdist workers create
    records in parallel)."""
    outcome, text, code, before, after, stored = result
    allure.attach(f"outcome={outcome} | refusal={text} | rows {before}->{after} (info) | code={code} | "
                  f"entries with this marker URL={stored}", name="save attempt")
    assert not code, f"{what}: the save was ACCEPTED (record {code} created) — expected it to be blocked"
    assert not stored, f"{what}: {stored} entry stored with the attempt's URL"
    assert outcome == "refused" or text, f"{what}: no refusal shown (outcome={outcome!r})"


# ---------------------------------------------------------------------------
# Access control (P1/P2)
# ---------------------------------------------------------------------------
@tc(135950)
def test_unauthenticated_direct_url_is_refused_135950(browser):
    """Logged out (fresh context, bare goto — BasePage.open would auto-sign-in).
    Expected: redirected to the Liferay login page, no management content."""
    ctx = new_context(browser, use_auth_state=False)
    try:
        p = ctx.new_page()
        resp = p.goto(DynamicWidgetAdminPage(p).manage_url(), wait_until="domcontentloaded")
        _assert_sent_to_login(p, resp)
    finally:
        ctx.close()


def _assert_sent_to_login(p, resp):
    allure.attach(f"final URL {p.url} (HTTP {resp.status if resp else '?'})", name="landing")
    assert p.locator(DynamicWidgetAdminPage.SAVE_AS_DRAFT_BUTTON).count() == 0, "authoring form rendered"
    assert p.locator("table tbody tr a[data-qc-oel-delete], [data-qc-oel-history]").count() == 0, "entry rows rendered"
    redirected = "LoginPortlet" in p.url or "/login" in p.url.lower() or "c/portal/login" in p.url
    assert redirected or (resp is not None and resp.status in (401, 403, 404)), (
        f"not sent to the login page: {p.url} (HTTP {resp.status if resp else '?'})")


@tc(135952)
@pytest.mark.parametrize("page", [{"auth": False}], indirect=True)
def test_site_member_is_denied_135952(page):
    """Account: Site Member (signed in, no CMS role)."""
    checks.check_member_denied(page, DynamicWidgetAdminPage)


@tc(135954)
def test_public_visitor_session_cannot_reach_management_135954(browser):
    """Visitor browses the public Home page first (frontend session cookie),
    then requests the manage URL in that same logged-out context."""
    ctx = new_context(browser, use_auth_state=False)
    try:
        p = ctx.new_page()
        home = HomeDynamicWidgetsPage(p)
        home.open_home()
        assert home.is_section_visible()
        resp = p.goto(DynamicWidgetAdminPage(p).manage_url(), wait_until="domcontentloaded")
        _assert_sent_to_login(p, resp)
    finally:
        ctx.close()


@tc(135951)
def test_editor_can_access_and_configure_management_135951(dw):
    """Account: Site Content Editor. The case expects Weather, Marhaba Guide
    and B2B Platform entries, editable."""
    dw.open_list_all()
    codes = dw.codes_listed()
    assert MARHABA_ERC in codes and B2B_ERC in codes, f"real widget entries not listed: {codes}"
    assert dw.page.get_by_role("link", name="Edit").count() > 0, "entries are not editable for the Editor"
    dw.open_code(MARHABA_ERC)  # read only: the form opens for edit
    assert dw.page.locator(dw.SUBMIT_FOR_REVIEW_BUTTON).count() == 1
    body = dw.page.locator("body").inner_text()
    dw.open_list_all()
    listing = dw.page.locator("table").inner_text()
    assert re.search(r"weather", listing + body, re.I), (
        "no Weather widget entry/configuration on Dynamic Widgets Management (only the two image widgets)")


# Unique per run: nothing is deleted under the opt-in (user decision 2026-10-13), so a
# fixed marker could match a row kept from an earlier run.
_SESSION_SHORT = f"session-{time.strftime('%m%d%H%M%S')}"


@tc(135953)
def test_expired_session_discards_unsaved_edit_135953(dw):
    """Editor opens a new widget form with unsaved values, the session is
    expired (cookies cleared), then Publish is clicked once."""
    dw.snapshot_codes()
    before = dw.row_count()
    dw.open_new()
    dw.fill_form(url=marker_url(135953, _SESSION_SHORT), order="9900", active=False,
                 image_en=uf.valid("marhaba_en.jpg"), image_ar=uf.valid("marhaba_ar.png"), tag="135953")
    dw.page.context.clear_cookies()
    dw.click_submit_once()
    landed = dw.page.url
    login_prompt = CmsLoginPage(dw.page).login_form_visible() or "login" in landed.lower()
    dw.sign_in(ROLE_EDITOR)  # re-authenticate before looking the attempt up
    code = dw.code_from_url() or dw.find_saved(marker_url(135953, _SESSION_SHORT), timeout=15)
    if code:
        dw.remember(code)
    dw.open_list_all()
    after = dw.row_count()
    stored = dw.count_by_url(marker_url(135953, _SESSION_SHORT))
    allure.attach(f"landed={landed} | login_prompt={login_prompt} | rows {before}->{after} (info) | stored={stored}",
                  name="expired session")
    assert not code and not stored, f"the unsaved edit was persisted after session expiry (code={code}, stored={stored})"
    assert login_prompt, f"no re-authentication prompt after session expiry (landed on {landed})"


# ---------------------------------------------------------------------------
# End-to-end (P2)
# ---------------------------------------------------------------------------
@tc(135966)
@PUBLIC_GROUP
def test_marhaba_widget_full_journey_135966(dw, anon):
    """Editor configures a Marhaba Guide widget (new record): EN/AR images,
    URL, new tab, Display Order 1, Active, Publish -> Home page card."""
    code = create_public(dw, 135966, "marhaba", url=MARHABA_URL, order="1", new_tab=True,
                         image_en=uf.padded_copy("marhaba_en.jpg", "135966-en", 450 * KB),
                         image_ar=uf.padded_copy("marhaba_ar.png", "135966-ar", 450 * KB))
    allure.attach(f"toast={dw.last_toast!r}", name="post-save feedback")
    v = dw.values()
    assert v["redirect_url"] == MARHABA_URL and v["display_order"] == "1"
    assert v["open_new_tab"] == "True" and v["active_status"] == "True"
    assert "QCTEST-135966" in v["image_en"] and "QCTEST-135966" in v["image_ar"], v
    wait_card(anon, code)
    assert anon.card_href_for_erc(code) == MARHABA_URL
    assert anon.card_opens_new_tab_for_erc(code)
    info = anon.card_img_info_for_erc(code)
    assert info["complete"] and info["nw"] > 0, f"card image did not load: {info}"


@tc(135967)
@PUBLIC_GROUP
def test_b2b_widget_full_journey_135967(dw, anon):
    """Same journey for a B2B Platform widget (new record), Display Order 2."""
    code = create_public(dw, 135967, "b2b", url=B2B_URL, order="2", new_tab=True,
                         image_en=uf.padded_copy("b2b_en.jpg", "135967-en", 600 * KB),
                         image_ar=uf.big_svg("135967-ar", 300 * KB))
    v = dw.values()
    assert v["redirect_url"] == B2B_URL and v["display_order"] == "2"
    assert "QCTEST-135967" in v["image_en"] and "QCTEST-135967" in v["image_ar"], v
    wait_card(anon, code)
    assert anon.card_href_for_erc(code) == B2B_URL
    assert anon.card_opens_new_tab_for_erc(code)


@tc(135969)
def test_generic_success_toast_after_save_135969(dw):
    """Editor saves a valid widget; the case expects a Liferay success toast."""
    dw.create(135969, "toast", active=False)
    allure.attach(f"outcome={dw.last_outcome!r} toast={dw.last_toast!r}", name="post-save feedback")
    assert dw.last_toast.strip(), f"no success toast after a successful save (outcome={dw.last_outcome!r})"


@tc(135970)
@PUBLIC_GROUP
def test_unpublish_removes_widget_from_home_135970(dw, anon):
    """Editor publishes an Active widget, then Unpublishes it (row action)."""
    code = create_public(dw, 135970, "unpublish")
    wait_card(anon, code)
    dw.unpublish_code(code)
    assert dw.wait_status(code, STATUS_UNPUBLISHED), f"status after Unpublish: {dw.status_now()}"
    items = wait_card(anon, code, present=False)
    assert MARHABA_ERC in ercs(items) and B2B_ERC in ercs(items), "the other widgets were affected"
    assert any(i["kind"] == "weather" for i in items)


@tc(135971)
@PUBLIC_GROUP
def test_edit_redirect_url_updates_live_link_135971(dw, anon):
    """Editor edits a live widget's Redirect URL and republishes."""
    code = create_public(dw, 135971, "url", url=B2B_URL, new_tab=True)
    wait_card(anon, code)
    dw.edit(code, url=B2B_URL + "-v2")
    end = time.monotonic() + PUBLIC_TIMEOUT_S
    while anon.open_home() and anon.card_href_for_erc(code) != B2B_URL + "-v2":
        assert time.monotonic() < end, f"live link not updated: {anon.card_href_for_erc(code)}"
        anon.page.wait_for_timeout(5000)
    with anon.page.expect_popup() as pop:
        anon.card_by_entry_erc(code).first.click()
    popup = pop.value
    popup.wait_for_load_state("domcontentloaded")
    assert popup.url == B2B_URL + "-v2"


@tc(135972, 135963, 135964)
@PUBLIC_GROUP
@pytest.mark.parametrize("kind", ["marhaba", "b2b"])
def test_active_off_removes_only_that_widget_135972(dw, anon, kind, request):
    """Editor switches one live widget's Active Status True -> False and
    saves; only that card leaves the Home page (Weather and the other cards
    stay). 135972/135963 = Marhaba Guide widget, 135964 = B2B widget."""
    files = ({"image_en": uf.valid("marhaba_en.jpg"), "image_ar": uf.valid("marhaba_ar.png")} if kind == "marhaba"
             else {"image_en": uf.valid("b2b_en.jpg"), "image_ar": uf.valid("b2b_ar.svg")})
    code = create_public(dw, 135972, kind, **files)
    before = wait_card(anon, code)
    dw.edit(code, active=False)
    dw.open_code(code)
    assert dw.flag("active_status") is False
    after = wait_card(anon, code, present=False)
    assert set(ercs(before)) - {code} == set(ercs(after)), f"other cards changed: {ercs(before)} -> {ercs(after)}"
    assert any(i["kind"] == "weather" for i in after), "Weather widget disappeared"


@pytest.mark.web
@PUBLIC_GROUP
@pytest.mark.parametrize("url,files", [
    pytest.param(MARHABA_URL, ("marhaba_en.jpg", "marhaba_ar.png"), marks=pytest.mark.tc_135957, id="135957-marhaba"),
    pytest.param(B2B_URL, ("b2b_en.jpg", "b2b_ar.svg"), marks=pytest.mark.tc_135958, id="135958-b2b"),
])
def test_visitor_click_opens_platform_in_new_tab(dw, anon, url, files):
    """Precondition (case): the widget is configured with this Redirect URL
    and Open in New Tab = True — built on a new widget record (Editor). The
    visitor (logged out) clicks the card: a new tab opens on the URL and the
    Home tab stays open."""
    code = create_public(dw, 135957, "click", url=url, new_tab=True,
                         image_en=uf.valid(files[0]), image_ar=uf.valid(files[1]))
    wait_card(anon, code)
    home_url = anon.page.url
    with anon.page.expect_popup() as pop:
        anon.card_by_entry_erc(code).first.click()
    pop.value.wait_for_load_state("domcontentloaded")
    assert pop.value.url == url
    assert anon.page.url == home_url and not anon.page.is_closed()


# ---------------------------------------------------------------------------
# Widget Image (EN / AR) — Marhaba Guide (1359xx) and B2B Platform (1360xx)
# ---------------------------------------------------------------------------
VALID_IMAGES = [
    pytest.param("image_en", "marhaba_en.jpg", 450 * KB, marks=pytest.mark.tc_135973, id="135973-marhaba-en"),
    pytest.param("image_ar", "marhaba_ar.png", 450 * KB, marks=pytest.mark.tc_135979, id="135979-marhaba-ar"),
    pytest.param("image_en", "b2b_en.jpg", 600 * KB, marks=pytest.mark.tc_136011, id="136011-b2b-en"),
    pytest.param("image_ar", "b2b_ar.svg", 300 * KB, marks=pytest.mark.tc_136017, id="136017-b2b-ar"),
]


@pytest.mark.parametrize("key,fixture,size", VALID_IMAGES)
def test_valid_widget_image_uploads_and_is_stored(dw, key, fixture, size):
    """Editor uploads a valid JPG/PNG/SVG of the case's size and saves."""
    path = (uf.big_svg(f"{fixture}", size) if fixture.endswith(".svg")
            else uf.padded_copy(fixture, fixture.split(".")[0], size))
    other = "image_ar" if key == "image_en" else "image_en"
    kw = {key: path, other: uf.valid("marhaba_ar.png" if other == "image_ar" else "marhaba_en.jpg")}
    code = dw.create(135973, "img", active=False, **kw)
    stored = dw.value(key)
    assert stored and stored.startswith("QCTEST-"), f"{key} not stored on {code}: {stored!r}"


MISSING_IMAGE = [
    pytest.param("image_en", False, marks=pytest.mark.tc_135974, id="135974-marhaba-no-en"),
    pytest.param("image_ar", False, marks=pytest.mark.tc_135980, id="135980-marhaba-no-ar"),
    pytest.param("image_ar", False, marks=pytest.mark.tc_135985, id="135985-en-only-ar-missing"),
    pytest.param("image_en", False, marks=pytest.mark.tc_136012, id="136012-b2b-no-en"),
    pytest.param("image_ar", False, marks=pytest.mark.tc_136018, id="136018-b2b-no-ar"),
    pytest.param("image_en", False, marks=pytest.mark.tc_136023, id="136023-ar-only-en-missing"),
    pytest.param("image_en", True, marks=pytest.mark.tc_136009, id="136009-active-no-en"),
]


@pytest.mark.parametrize("missing,active", MISSING_IMAGE)
def test_save_without_widget_image_is_blocked(dw, missing, active):
    """Editor leaves one Widget Image empty (everything else valid) and
    clicks Publish once: blocked, nothing saved, the other image kept."""
    res = refused_create(dw, url=marker_url(135974, f"no-{missing}"), active=active,
                         image_en=missing != "image_en", image_ar=missing != "image_ar", tag="135974")
    assert_refused(res, f"missing {missing}")
    label = dw.spec(missing).label
    assert label.split(" (")[0].lower() in (res[1] or "").lower() or "required" in (res[1] or "").lower(), (
        f"refusal does not name the missing image: {res[1]!r}")


BAD_FORMAT = [
    pytest.param("image_en", "pdf", marks=pytest.mark.tc_135975, id="135975-en-pdf"),
    pytest.param("image_ar", "docx", marks=pytest.mark.tc_135981, id="135981-ar-docx"),
    pytest.param("image_en", "bmp", marks=pytest.mark.tc_136013, id="136013-en-bmp"),
    pytest.param("image_ar", "tiff", marks=pytest.mark.tc_136019, id="136019-ar-tiff"),
]


@pytest.mark.parametrize("key,fmt", BAD_FORMAT)
def test_unsupported_image_format_is_rejected(dw, key, fmt):
    """Editor attempts an unsupported format (only JPG/PNG/SVG allowed). The
    file must be refused at the picker or at Publish; nothing is stored."""
    path = getattr(uf, fmt)(f"{fmt}")
    dw.snapshot_codes()
    before = dw.row_count()
    dw.open_new()
    picker = dw.try_upload(key, path, tag="fmt")
    if picker:
        allure.attach(picker, name="refused at picker")
        assert not dw.value(key).endswith(path.rsplit(".", 1)[-1]), "field shows the refused file"
        return
    other = "image_ar" if key == "image_en" else "image_en"
    dw.fill_form(url=marker_url(135975, fmt), order="9900", active=False,
                 **{other: uf.valid("marhaba_ar.png" if other == "image_ar" else "marhaba_en.jpg")})
    dw.click_submit_once()
    code = dw.code_from_url() or dw.find_saved(marker_url(135975, fmt), timeout=15)
    if code:
        dw.remember(code)
    assert not code and not dw.count_by_url(marker_url(135975, fmt)), f".{fmt} accepted as {key} (record {code})"


OVERSIZE = [
    pytest.param("image_en", "marhaba_en.jpg", 3_000_000, marks=pytest.mark.tc_135976, id="135976-en-3mb"),
    pytest.param("image_ar", "marhaba_ar.png", 2_500_000, marks=pytest.mark.tc_135982, id="135982-ar-2.5mb"),
    pytest.param("image_en", "b2b_en.jpg", 2_800_000, marks=pytest.mark.tc_136014, id="136014-en-2.8mb"),
    pytest.param("image_ar", "b2b_ar.svg", 4_000_000, marks=pytest.mark.tc_136020, id="136020-ar-4mb-svg"),
]


@pytest.mark.parametrize("key,fixture,size", OVERSIZE)
def test_oversize_widget_image(dw, key, fixture, size):
    """Editor attempts an image over the PBI's 2 MB. Team rule (2026-10):
    an accepted file up to 3 MB is OK; a file over 3 MB must be refused."""
    path = uf.big_svg("big", size) if fixture.endswith(".svg") else uf.padded_copy(fixture, "big", size)
    dw.snapshot_codes()
    before = dw.row_count()
    dw.open_new()
    picker = dw.try_upload(key, path, tag="big")
    accepted = False
    if not picker:
        other = "image_ar" if key == "image_en" else "image_en"
        dw.fill_form(url=marker_url(135976, f"{size}"), order="9900", active=False,
                     **{other: uf.valid("marhaba_ar.png" if other == "image_ar" else "marhaba_en.jpg")})
        dw.click_submit_once()
        code = dw.code_from_url() or dw.find_saved(marker_url(135976, f"{size}"), timeout=15)
        if code:
            dw.remember(code)
            accepted = True
    allure.attach(f"size={size} picker={picker!r} accepted={accepted} refusal={dw.refusal_text()!r}", name="oversize")
    if size > 3 * MB:
        assert not accepted, f"{size} bytes (> 3 MB) accepted as {key}"
    if not accepted and not picker:
        assert dw.refusal_text(), "an oversize file was neither accepted nor refused with a message"


CANCEL_IMAGE = [
    pytest.param("image_en", "marhaba_en.jpg", marks=pytest.mark.tc_135977, id="135977-en"),
    pytest.param("image_ar", "marhaba_ar.png", marks=pytest.mark.tc_135983, id="135983-ar"),
    pytest.param("image_en", "b2b_en.jpg", marks=pytest.mark.tc_136015, id="136015-b2b-en"),
    pytest.param("image_ar", "b2b_ar.svg", marks=pytest.mark.tc_136021, id="136021-b2b-ar"),
]


def _cancel(dw):
    """Cancel = leave the form without saving, via the form's own cancel
    control (the editing banner's "Cancel and add a new entry instead")."""
    link = dw.page.locator(dw.CANCEL_AND_ADD_NEW_LINK)
    if link.count():
        link.first.click()
        dw.page.wait_for_load_state("domcontentloaded")
    else:
        dw.page.go_back()


@pytest.mark.parametrize("key,fixture", CANCEL_IMAGE)
def test_cancel_after_image_upload_discards_it(dw, key, fixture):
    code = dw.create(135977, "cancel-img", active=False)
    saved = dw.value(key)
    dw.open_code(code)
    dw.upload(key, uf.valid(fixture), tag="cancelled")
    _cancel(dw)
    dw.open_code(code)
    assert dw.value(key) == saved, f"{key} changed after Cancel: {saved!r} -> {dw.value(key)!r}"


PERSIST_IMAGE = [
    pytest.param("image_en", marks=pytest.mark.tc_135978, id="135978-en"),
    pytest.param("image_ar", marks=pytest.mark.tc_135984, id="135984-ar"),
    pytest.param("image_en", marks=pytest.mark.tc_136016, id="136016-b2b-en"),
    pytest.param("image_ar", marks=pytest.mark.tc_136022, id="136022-b2b-ar"),
]


@pytest.mark.parametrize("key", PERSIST_IMAGE)
def test_saved_widget_image_persists_after_reload(dw, key):
    code = dw.create(135978, "persist-img", active=False)
    saved = dw.value(key)
    dw.open_list_all()
    dw.page.reload()
    dw.open_code(code)
    assert saved and dw.value(key) == saved


# ---------------------------------------------------------------------------
# Redirect URL
# ---------------------------------------------------------------------------
@pytest.mark.parametrize("url", [
    pytest.param(MARHABA_URL, marks=pytest.mark.tc_135986, id="135986"),
    pytest.param(B2B_URL, marks=pytest.mark.tc_136024, id="136024"),
])
def test_valid_redirect_url_saves(dw, url):
    """The case's exact URL is stored (identity: the code this test created)."""
    code = dw.create(135986, "url", url=url, active=False)
    dw.open_code(code)
    assert dw.value("redirect_url") == url


@pytest.mark.parametrize("bad,active", [
    pytest.param("", False, marks=pytest.mark.tc_135987, id="135987-empty"),
    pytest.param("", False, marks=pytest.mark.tc_136025, id="136025-empty"),
    pytest.param("", True, marks=pytest.mark.tc_136048, id="136048-active-empty"),
    pytest.param("marhaba guide site", False, marks=pytest.mark.tc_135988, id="135988-invalid"),
    pytest.param("b2b platform link", False, marks=pytest.mark.tc_136026, id="136026-invalid"),
    pytest.param("<script>alert(1)</script>", False, marks=pytest.mark.tc_135991, id="135991-script"),
    pytest.param("<script>alert('x')</script>", False, marks=pytest.mark.tc_136029, id="136029-script"),
])
def test_invalid_or_empty_redirect_url_is_blocked(dw, bad, active):
    res = refused_create(dw, url=bad, active=active, tag="url")
    assert_refused(res, f"Redirect URL {bad!r}")


@pytest.mark.parametrize("length,over", [
    pytest.param(501, True, marks=pytest.mark.tc_135989, id="135989-501"),
    pytest.param(510, True, marks=pytest.mark.tc_136027, id="136027-510"),
    pytest.param(500, False, marks=pytest.mark.tc_135990, id="135990-500"),
    pytest.param(500, False, marks=pytest.mark.tc_136028, id="136028-500"),
])
def test_redirect_url_length_boundary(dw, length, over):
    """Bug-rules Rule 5: the implemented limit is read live (maxlength);
    an implemented limit above the US 500 with the UI intact passes."""
    base = marker_url(135990 if not over else 135989, "len") + "/"
    url = base + "q" * (length - len(base))
    dw.open_new()
    ml = dw.max_length_attr("redirect_url")
    allure.attach(f"maxlength={ml}", name="implemented limit")
    dw.fill_form(url=url, order="9900", active=False, new_tab=False,
                 image_en=uf.valid("marhaba_en.jpg"), image_ar=uf.valid("marhaba_ar.png"), tag="len")
    typed = dw.value("redirect_url")
    dw.click_submit_once()
    code = dw.code_from_url() or dw.find_saved(url, timeout=15)
    if code:
        dw.remember(code)
    if not over:
        assert code, f"a {length}-char URL was refused: {dw.refusal_text()!r}"
        dw.open_code(code)
        assert dw.value("redirect_url") == url, "the 500-char URL was not stored in full"
        return
    if ml is not None and ml < length:
        assert len(typed) == ml and ml >= 500, f"input truncated to {ml} (< 500?)"
        return
    if code:  # implemented limit above the US limit: Rule 5 — UI intact passes
        dw.open_code(code)
        stored = dw.value("redirect_url")
        allure.attach(f"stored {len(stored)} chars", name="Rule 5: implemented limit > 500")
        box = dw.page.get_by_role("textbox", name=dw.label_pattern("Redirect URL")).bounding_box()
        assert box and box["width"] < 2000, "the form field overflowed"
    else:
        assert dw.refusal_text(), "over-limit URL neither accepted nor refused with a message"


@pytest.mark.parametrize("original", [
    pytest.param(MARHABA_URL, marks=pytest.mark.tc_135992, id="135992"),
    pytest.param(B2B_URL, marks=pytest.mark.tc_136030, id="136030"),
])
def test_cancel_redirect_url_edit_discards_it(dw, original):
    code = dw.create(135992, "cancel-url", url=original, active=False)
    dw.open_code(code)
    dw.fill_form(url="https://example.com/temp")
    _cancel(dw)
    dw.open_code(code)
    assert dw.value("redirect_url") == original


@pytest.mark.parametrize("url", [
    pytest.param(MARHABA_URL, marks=pytest.mark.tc_135993, id="135993"),
    pytest.param(B2B_URL, marks=pytest.mark.tc_136031, id="136031"),
])
def test_saved_redirect_url_persists_after_reload(dw, url):
    code = dw.create(135993, "persist-url", url=url, active=False)
    dw.open_list_all()
    dw.page.reload()
    dw.open_code(code)
    assert dw.value("redirect_url") == url


# ---------------------------------------------------------------------------
# Open in New Tab
# ---------------------------------------------------------------------------
@PUBLIC_GROUP
@pytest.mark.parametrize("new_tab", [
    pytest.param(True, marks=pytest.mark.tc_135994, id="135994-marhaba-true"),
    pytest.param(False, marks=pytest.mark.tc_135995, id="135995-marhaba-false"),
    pytest.param(True, marks=pytest.mark.tc_136032, id="136032-b2b-true"),
    pytest.param(False, marks=pytest.mark.tc_136033, id="136033-b2b-false"),
])
def test_open_in_new_tab_drives_the_public_click(dw, anon, new_tab):
    url = marker_url(135994, f"tab-{new_tab}")
    code = create_public(dw, 135994, f"tab-{new_tab}", url=url, new_tab=new_tab)
    wait_card(anon, code)
    card = anon.card_by_entry_erc(code).first
    if new_tab:
        with anon.page.expect_popup() as pop:
            card.click()
        pop.value.wait_for_load_state("domcontentloaded")
        assert pop.value.url == url and "/home" in anon.page.url
    else:
        assert card.get_attribute("target") in (None, "", "_self")
        with anon.page.expect_navigation():
            card.click()
        assert anon.page.url == url and len(anon.page.context.pages) == 1


@pytest.mark.parametrize("x", [
    pytest.param(1, marks=pytest.mark.tc_135996, id="135996"),
    pytest.param(2, marks=pytest.mark.tc_136035, id="136035"),
])
def test_open_in_new_tab_persists_after_reload(dw, x):
    code = dw.create(135996, "tab-persist", new_tab=True, active=False)
    dw.open_list_all()
    dw.page.reload()
    dw.open_code(code)
    assert dw.flag("open_new_tab") is True


@pytest.mark.parametrize("x", [
    pytest.param(1, marks=pytest.mark.tc_136010, id="136010"),
    pytest.param(2, marks=pytest.mark.tc_136034, id="136034"),
])
def test_open_in_new_tab_defaults_to_false(dw, x):
    dw.open_new()
    default = dw.flag("open_new_tab")
    code = dw.create(136010, "tab-default", new_tab=None, active=False)
    assert default is False, "Open in New Tab is ticked by default on a new configuration"
    assert dw.flag("open_new_tab") is False, f"stored Open in New Tab = True on {code}"


# ---------------------------------------------------------------------------
# Display Order
# ---------------------------------------------------------------------------
@tc(135997)
@PUBLIC_GROUP
def test_display_order_one_renders_first_135997(dw, anon):
    """Valid Display Order saves for a (disposable) Marhaba Guide widget and
    the card takes its sorted place among the ACTIVE widgets.

    FIX PASS 7 (2026-10-14): the 2026-10-13 run used the case's value 1 and
    TIED with the real `QCDEMO-129384-directory` widget, which already holds
    displayOrder 1 (bug-verification-p3-20261013.md row 12: test data, not a
    bug). "First" is unreachable without a tie or reordering real data: 0 and
    negatives are refused (135999 / 136000). So the value is the smallest
    positive order NO active widget uses (read from the visitor's own feed
    first), and the assertion is the case's intent: the save succeeds, the
    stored value is that order on a fresh read, and the card renders after
    every lower order and before every higher one. Disposable QCTEST widget,
    Active only for the public check; the fixture unticks it (left Inactive,
    kept and logged -- nothing is deleted under the opt-in)."""
    with allure.step("Read the active widgets' Display Orders (visitor feed)"):
        before = anon.active_feed_orders()
        used = {int(v) for v in before.values() if v is not None}
        order = next(n for n in range(1, 10_000) if n not in used)
        allure.attach(f"active orders before: {before}\nchosen Display Order: {order} "
                      f"(the case's value 1 is held by {[e for e, v in before.items() if v == 1]})",
                      name="Display Order chosen (no collision)")
    code = create_public(dw, 135997, f"order{order}", order=str(order))
    with allure.step("Fresh read: the stored Display Order"):
        dw.open_code(code)
        stored = dw.value("display_order")
    assert stored == str(order), f"Display Order reads {stored!r} on {code}, expected {order}"
    items = wait_card(anon, code)
    orders = anon.active_feed_orders()
    rendered = ercs(items)
    pos = rendered.index(code)
    known = lambda e: orders.get(e) is not None  # noqa: E731
    out_of_place = ([e for e in rendered[:pos] if known(e) and int(orders[e]) > order]
                    + [e for e in rendered[pos + 1:] if known(e) and int(orders[e]) < order])
    allure.attach(f"rendered cards: {[(e, orders.get(e)) for e in rendered]}", name="public card order")
    assert orders.get(code) == order, f"the visitor feed carries Display Order {orders.get(code)!r} for {code}"
    assert not out_of_place, (f"the order-{order} card is not in its sorted place: "
                              f"{[(e, orders.get(e)) for e in rendered]}")


@tc(136036)
def test_display_order_two_saves_136036(dw):
    dw.create(136036, "order2", order="2", active=False)
    assert dw.value("display_order") == "2"


@pytest.mark.parametrize("order", [
    pytest.param("", marks=pytest.mark.tc_135998, id="135998-empty"),
    pytest.param("", marks=pytest.mark.tc_136037, id="136037-empty"),
    pytest.param("0", marks=pytest.mark.tc_135999, id="135999-zero"),
    pytest.param("0", marks=pytest.mark.tc_136038, id="136038-zero"),
    pytest.param("-3", marks=pytest.mark.tc_136000, id="136000-neg"),
    pytest.param("-5", marks=pytest.mark.tc_136039, id="136039-neg"),
    pytest.param("first", marks=pytest.mark.tc_136001, id="136001-text"),
    pytest.param("second", marks=pytest.mark.tc_136040, id="136040-text"),
    pytest.param("1.5", marks=pytest.mark.tc_136002, id="136002-decimal"),
    pytest.param("2.5", marks=pytest.mark.tc_136041, id="136041-decimal"),
])
def test_invalid_display_order_is_blocked(dw, order):
    res = refused_create(dw, url=marker_url(135998, f"order-{order or 'empty'}"), order=order)
    assert_refused(res, f"Display Order {order!r}")


@pytest.mark.parametrize("saved", [
    pytest.param("1", marks=pytest.mark.tc_136003, id="136003"),
    pytest.param("2", marks=pytest.mark.tc_136042, id="136042"),
])
def test_cancel_display_order_edit_discards_it(dw, saved):
    code = dw.create(136003, "cancel-order", order=saved, active=False)
    dw.open_code(code)
    dw.fill_form(order="5" if saved == "1" else "9")
    _cancel(dw)
    dw.open_code(code)
    assert dw.value("display_order") == saved


@pytest.mark.parametrize("order", [
    pytest.param("2", marks=pytest.mark.tc_136004, id="136004"),
    pytest.param("3", marks=pytest.mark.tc_136043, id="136043"),
])
def test_saved_display_order_persists_after_reload(dw, order):
    code = dw.create(136004, "persist-order", order=order, active=False)
    dw.open_list_all()
    dw.page.reload()
    dw.open_code(code)
    assert dw.value("display_order") == order


# ---------------------------------------------------------------------------
# Active Status
# ---------------------------------------------------------------------------
@PUBLIC_GROUP
@pytest.mark.parametrize("active", [
    pytest.param(True, marks=pytest.mark.tc_136005, id="136005-marhaba-on"),
    pytest.param(False, marks=pytest.mark.tc_136006, id="136006-marhaba-off"),
    pytest.param(True, marks=pytest.mark.tc_136044, id="136044-b2b-on"),
    pytest.param(False, marks=pytest.mark.tc_136045, id="136045-b2b-off"),
])
def test_active_status_gates_the_home_page(dw, anon, active):
    """Editor publishes with all mandatory fields; Active decides visibility."""
    code = dw.create(136005, f"active-{active}", active=active)
    assert dw.status_now() == STATUS_PUBLISHED or (not active and INACTIVE.lower() in dw.page.locator("body").inner_text().lower())
    if active:
        wait_card(anon, code)
    else:
        items = wait_card(anon, code, present=False, timeout=30)
        assert code not in ercs(items)


@pytest.mark.parametrize("x", [
    pytest.param(1, marks=pytest.mark.tc_136007, id="136007"),
    pytest.param(2, marks=pytest.mark.tc_136046, id="136046"),
])
@PUBLIC_GROUP
def test_cancel_active_toggle_discards_it(dw, x):
    code = create_public(dw, 136007, "cancel-active")
    dw.open_code(code)
    dw.set_flag("active_status", False)
    _cancel(dw)
    dw.open_code(code)
    assert dw.flag("active_status") is True


@pytest.mark.parametrize("x", [
    pytest.param(1, marks=pytest.mark.tc_136008, id="136008"),
    pytest.param(2, marks=pytest.mark.tc_136047, id="136047"),
])
@PUBLIC_GROUP
def test_saved_active_status_persists_after_reload(dw, x):
    code = create_public(dw, 136008, "persist-active")
    dw.open_list_all()
    dw.page.reload()
    dw.open_code(code)
    assert dw.flag("active_status") is True


# ---------------------------------------------------------------------------
# Weather widget configuration (P2/P3) — one root cause, one function
# ---------------------------------------------------------------------------
WEATHER_CASES = [135968, 135962, 136049, 136050, 136051, 136052, 136053, 136054, 136055, 136056]


@pytest.mark.parametrize("tc_id", [pytest.param(i, marks=getattr(pytest.mark, f"tc_{i}"), id=str(i))
                                   for i in WEATHER_CASES])
def test_weather_widget_configuration_exists(dw, tc_id):
    """Each case starts with "Open Weather widget configuration" as an
    Editor. Looks for it where an Editor manages content: the Object
    Authoring index and the Dynamic Widget entries list."""
    dw.page.goto(control_panel_url("/en/web/qatar-chamber/object-authoring"), wait_until="domcontentloaded")
    dw.page.wait_for_load_state("load")
    index_text = dw.page.locator("body").inner_text()
    weather_links = dw.page.locator('a[href*="manage-"]').filter(has_text=re.compile("weather", re.I)).count()
    dw.open_list_all()
    listing = dw.page.locator("table").inner_text()
    allure.attach(f"index weather links={weather_links}\nlist:\n{listing}", name="where an Editor looked")
    assert weather_links or re.search(r"weather", listing, re.I), (
        "no Weather widget configuration exists for the Editor: no Weather object on Object Authoring and no "
        "Weather entry on manage-dynamic-widget (the Weather card is the qc-weather-widget client extension)")


# ---------------------------------------------------------------------------
# Edge cases
# ---------------------------------------------------------------------------
@tc(136060)
@PUBLIC_GROUP
# Two public creates (~120 s each, measured: 136066's single create took
# 123 s on 2026-10-13) + two Home polls (PUBLIC_TIMEOUT_S each) + teardown of
# both records do not fit the module's 300 s; the run was hard-killed.
@pytest.mark.timeout(720)
def test_two_widgets_same_display_order_136060(dw, anon):
    a = create_public(dw, 136060, "tie-a", order="1")
    b = create_public(dw, 136060, "tie-b", order="1", image_en=uf.valid("b2b_en.jpg"), image_ar=uf.valid("b2b_ar.svg"))
    first = wait_card(anon, b)
    assert a in ercs(first)
    anon.page.wait_for_timeout(2000)
    second = wait_card(anon, b)
    pos = lambda items: [e for e in ercs(items) if e in (a, b)]
    assert pos(first) == pos(second), f"tie order not deterministic: {pos(first)} vs {pos(second)}"
    boxes = [i for i in second if i["erc"] in (a, b)]
    assert all(i["w"] > 0 and i["h"] > 0 for i in boxes)
    xa, xb = sorted(boxes, key=lambda i: (i["y"], i["x"]))
    assert xa["y"] != xb["y"] or xa["x"] + xa["w"] <= xb["x"] + 1, "the two cards overlap"


@tc(136061)
@PUBLIC_GROUP
def test_concurrent_invalid_edit_keeps_live_config_136061(dw, anon, browser):
    code = create_public(dw, 136061, "concurrent", url=B2B_URL, new_tab=True)
    wait_card(anon, code)
    ctx2 = new_context(browser, use_auth_state=False)
    try:
        second = DynamicWidgetAdminPage(ctx2.new_page())
        second.sign_in(ROLE_EDITOR)
        second.created = list(dw.created)
        second.open_code(code)
        second.fill_form(url="b2b platform link")
        out = second.click_submit_once()
        assert out == "refused" or second.refusal_text(), "second session's invalid URL was not blocked"
    finally:
        ctx2.close()
    dw.open_code(code)
    assert dw.value("redirect_url") == B2B_URL
    anon.open_home()
    assert anon.card_href_for_erc(code) == B2B_URL


@tc(136062)
@PUBLIC_GROUP
def test_disable_before_cache_refresh_136062(dw, anon):
    code = create_public(dw, 136062, "cache")
    wait_card(anon, code)
    dw.edit(code, active=False)
    anon.open_home()
    immediate = [i for i in anon.row_items() if i["erc"] == code]
    allure.attach(str(immediate), name="immediately after save")
    assert all(i["visible"] and i["w"] > 0 for i in immediate), "a broken/blank card rendered before refresh"
    items = wait_card(anon, code, present=False)
    assert all(i["w"] > 0 for i in items if i["kind"] == "card"), "broken remnant card left behind"


@tc(136063)
def test_aborted_large_upload_saves_nothing_136063(dw):
    code = dw.create(136063, "abort", active=False)
    saved = dw.value("image_en")
    dw.open_code(code)
    big = uf.padded_copy("marhaba_en.jpg", "136063-large", 15 * MB)
    hidden = dw.page.get_by_role("textbox", name="Widget Image (EN) Select File")
    hidden.locator("xpath=..").get_by_role("button", name="Select File").click()
    dw.page.frame_locator(dw.UPLOAD_MODAL_IFRAME).locator('input[type="file"]').set_input_files(big)
    dw.page.goto(control_panel_url("/en/web/qatar-chamber/object-authoring"), wait_until="domcontentloaded")
    dw.open_code(code)
    assert dw.value("image_en") == saved, f"image changed after an aborted upload: {dw.value('image_en')!r}"


@tc(136064)
@PUBLIC_GROUP
def test_clearing_url_on_live_widget_is_blocked_136064(dw, anon):
    code = create_public(dw, 136064, "clear", url=B2B_URL, new_tab=True)
    wait_card(anon, code)
    out = dw.edit(code, url="")
    assert out == "refused" or dw.refusal_text(), f"clearing the URL was not blocked (outcome={out!r})"
    dw.open_code(code)
    assert dw.value("redirect_url") == B2B_URL
    anon.open_home()
    with anon.page.expect_popup() as pop:
        anon.card_by_entry_erc(code).first.click()
    pop.value.wait_for_load_state("domcontentloaded")
    assert pop.value.url == B2B_URL


@tc(136065)
@PUBLIC_GROUP
def test_rapid_active_toggle_final_state_wins_136065(dw, anon):
    code = create_public(dw, 136065, "rapid")
    dw.edit(code, active=False)
    dw.edit(code, active=True)
    dw.open_code(code)
    assert dw.flag("active_status") is True
    items = wait_card(anon, code)
    assert ercs(items).count(code) == 1, f"duplicate/ghost cards: {ercs(items)}"


@tc(136066)
def test_back_after_save_does_not_resubmit_136066(dw):
    dw.open_list_all()
    before = dw.row_count()
    code = dw.create(136066, "back", active=False)
    toast = dw.last_toast
    dw.page.go_back()
    dw.page.wait_for_load_state("domcontentloaded")
    dw.page.wait_for_timeout(3000)  # measured: a resubmission would start within 1 s of the back
    # Counted from the entries list, not the headless API: the record is
    # saved with Active unticked, and the API omits inactive records (it read
    # 0 for this very save on 2026-10-13).
    stored = dw.count_saved_since_snapshot(marker_url(136066, "back"))
    dw.open_list_all()
    allure.attach(f"toast after save={toast!r} | rows {before}->{dw.row_count()} (info) | stored={stored}",
                  name="feedback")
    assert stored == 1, f"{stored} entries carry this save's URL after Back (expected exactly 1)"
    assert dw.row_status_for(code) or dw.codes_listed(), "list unreadable"
