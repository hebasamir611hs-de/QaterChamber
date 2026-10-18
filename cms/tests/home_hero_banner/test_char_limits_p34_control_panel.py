"""
cms/tests/home_hero_banner/test_char_limits_p34_control_panel.py — the
character-limit cases of PBIs 129367 (Hero Banner) and 129371 (Our Services),
added 2026-10-15 on the QA lead's instruction ("run the char limits; anything not
as the PBI says is a bug").

Method (QA lead, 2026-10-14): type the PBI limit + 1 characters and submit.
Cut to the limit at the input, or refused on submit, is a pass. A value stored
over the limit is the failure. "Exactly N accepted" cases also save N characters
and read them back.

Records: disposable QCTEST slides / counters / cards / tabs (kept and logged,
never deleted). The Our Services Section cases write to the ONE live record and
restore its snapshot, left Published, in `finally`.
"""

from __future__ import annotations

import allure
import pytest

from cms.pages.components.disposable_object_admin import ROLE_EDITOR, chars
from cms.pages.components.object_authoring_page import STATUS_PUBLISHED
from cms.pages.home_hero_banner.hero_banner_fields_admin_page import (
    AchievementCounterFieldsAdminPage as Counter,
    HeroSlideFieldsAdminPage as Slide,
)
from cms.pages.home_services.our_services_admin_page import (
    OSS_ENTRY_CODE,
    FilterTabAdminPage as Tab,
    OurServicesSectionAdminPage as Section,
    ServiceCardAdminPage as Card,
)
from cms.tests import authoring_checks as ac
from cms.tests.home_services.test_our_services_p12_control_panel import OSS, _edit_section, _section_restore
from cms.tests.live_write_guard import LiveRecord, log_live_write

pytestmark = [pytest.mark.control_panel]


def _over_limit(page, admin_cls, tc: int, key: str, limit: int, at_limit_too: bool = False) -> None:
    """Disposable record: limit+1 must be cut or refused, never stored."""
    admin = admin_cls(page)
    title = ac.run_title(tc, "max")
    try:
        admin.open_form(ROLE_EDITOR)
        if admin_cls is Counter:
            admin.fill("title_en", title if key != "title_en" else title)
            admin.fill("display_order", "9900")
            if key != "value":
                admin.fill("value", "50K+")
        else:
            admin.fill_required(title, skip=(key,) if key != admin.TITLE_FIELD else ())
        over = chars(limit + 1) if key != admin_cls.TITLE_FIELD else (title + chars(limit))[: limit + 1]
        admin.fill(key, over)
        typed = admin.value(key)
        allure.attach(f"limit {limit}; typed {len(over)}; field holds {len(typed)}", name="lengths",
                      attachment_type=allure.attachment_type.TEXT)
        if len(typed) <= limit:
            return  # cut at the input — pass
        log_live_write(LiveRecord(admin_cls.SLUG, title, "disposable QCTEST record"), key, f"{len(over)} chars",
                       tc, action="attempt", note="char-limit check")
        admin.submit_for_review()
        if admin.refusal_visible(4000):
            return
        lookup = title if key != admin_cls.TITLE_FIELD else over
        status = admin.status_of(lookup, ROLE_EDITOR)
        stored = ""
        if status:
            admin.open_entry_by_edit_link(lookup)
            stored = admin.value(key)
        assert len(stored) <= limit and status != STATUS_PUBLISHED, (
            f"{admin_cls.FIELDS[key].label}: {limit + 1} characters were accepted "
            f"(status {status!r}, stored length {len(stored)}; PBI limit {limit})"
        )
    finally:
        ac.dispose(admin, title, tc)
    if at_limit_too and key != admin_cls.TITLE_FIELD:
        ac.check_valid_persists(page, admin_cls, tc, key, chars(limit, "A"), short="atmax")


HERO = [
    pytest.param(Slide, "title_en", 100, True, id="135037", marks=pytest.mark.tc_135037),
    pytest.param(Slide, "title_ar", 100, True, id="135041", marks=pytest.mark.tc_135041),
    pytest.param(Slide, "subtitle_en", 300, False, id="135045", marks=pytest.mark.tc_135045),
    pytest.param(Slide, "subtitle_ar", 300, False, id="135048", marks=pytest.mark.tc_135048),
    pytest.param(Slide, "b1_label_en", 50, True, id="135051", marks=pytest.mark.tc_135051),
    pytest.param(Slide, "b1_label_ar", 50, True, id="135055", marks=pytest.mark.tc_135055),
    pytest.param(Slide, "b1_link", 500, True, id="135060", marks=pytest.mark.tc_135060),
    pytest.param(Slide, "b2_label_en", 50, True, id="135064", marks=pytest.mark.tc_135064),
    pytest.param(Slide, "b2_label_ar", 50, True, id="135068", marks=pytest.mark.tc_135068),
    pytest.param(Slide, "b2_link", 500, True, id="135073", marks=pytest.mark.tc_135073),
    pytest.param(Counter, "title_en", 30, False, id="135082", marks=pytest.mark.tc_135082),
    pytest.param(Counter, "title_ar", 30, False, id="135085", marks=pytest.mark.tc_135085),
    pytest.param(Counter, "value", 10, False, id="135088", marks=pytest.mark.tc_135088),
    pytest.param(Card, "redirect_url", 500, False, id="135402", marks=pytest.mark.tc_135402),
]


@allure.title("Field over the PBI character limit is cut or refused")
@pytest.mark.parametrize("admin_cls,key,limit,at_limit", HERO)
def test_over_char_limit_refused(page, request, admin_cls, key, limit, at_limit):
    _over_limit(page, admin_cls, int(request.node.callspec.id), key, limit, at_limit)


TAB = [
    pytest.param("en", id="135394", marks=pytest.mark.tc_135394),
    pytest.param("ar", id="135398", marks=pytest.mark.tc_135398),
]


@allure.title("Tab Label over 50 characters is cut or refused")
@pytest.mark.parametrize("loc", TAB)
def test_tab_label_over_limit(page, request, loc):
    tc = int(request.node.callspec.id)
    admin = Tab(page)
    title = ac.run_title(tc, "tab")
    try:
        admin.open_form(ROLE_EDITOR)
        admin.fill("display_order", "9900")
        admin.fill("tab_label", title)
        admin.fill("tab_label", f"{title} AR", locale="ar")
        admin.fill("tab_label", chars(51) if loc == "ar" else (title + chars(51))[:51], locale=loc)
        typed = admin.value("tab_label", loc)
        if len(typed) <= 50:
            return
        lookup = typed if loc == "en" else title
        log_live_write(LiveRecord("filter-tab", lookup, "disposable QCTEST record"), f"Tab Label:{loc}", "51 chars",
                       tc, action="attempt")
        admin.submit_for_review()
        if admin.refusal_visible(4000):
            return
        status = admin.status_of(lookup, ROLE_EDITOR)
        assert status != STATUS_PUBLISHED, f"Tab Label ({loc}): 51 characters were accepted and published"
    finally:
        ac.dispose(admin, title, tc)


SECTION = [
    pytest.param("section_tag", "en", 20, id="135356", marks=pytest.mark.tc_135356),
    pytest.param("section_tag", "ar", 20, id="135360", marks=pytest.mark.tc_135360),
    pytest.param("section_heading", "en", 200, id="135364", marks=pytest.mark.tc_135364),
    pytest.param("section_heading", "ar", 200, id="135368", marks=pytest.mark.tc_135368),
    pytest.param("section_description", "en", 500, id="135372", marks=pytest.mark.tc_135372),
    pytest.param("section_description", "ar", 500, id="135375", marks=pytest.mark.tc_135375),
]


@allure.title("Our Services Section field over the PBI limit is cut or refused")
@pytest.mark.xdist_group("our_services_section")
@pytest.mark.parametrize("key,loc,limit", SECTION)
def test_section_over_limit(page, request, key, loc, limit):
    tc = int(request.node.callspec.id)
    section = Section(page).open_record(ROLE_EDITOR)
    snap = section.snapshot()
    try:
        _edit_section(section)
        section.fill(key, chars(limit + 1), locale=loc)
        typed = section.value(key, loc)
        if len(typed) <= limit:
            return
        log_live_write(OSS, f"{key}:{loc}", f"{limit + 1} chars", tc, action="attempt", note=f"snapshot {snap}")
        section.submit_for_review()
        if section.refusal_visible(4000):
            return
        section.open_entry_by_code(OSS_ENTRY_CODE)
        stored = section.value(key, loc)
        assert len(stored) <= limit, f"{key} ({loc}): {len(stored)} characters stored (PBI limit {limit})"
    finally:
        _section_restore(section, snap, tc)
