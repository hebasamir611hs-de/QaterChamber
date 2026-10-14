"""
A5 manual-repro module for PBI 130716 product candidates (bug-rules Rule 3.2).
NOT part of the suite (not test_*.py; run only by explicit path). Records
observations + screenshots under reports/bug-evidence/130716-<group>/; nothing
is asserted. QCTEST records only, deleted BY ID in finally; Active left
UNTICKED except R1, where the case reads the public number.
"""

import json
from pathlib import Path

from cms.pages.components.disposable_object_admin import ROLE_EDITOR
from cms.pages.sectoral_committees.sectoral_committees_admin_page import (
    CommitteeCtaCardAdminPage as Cta,
    CommitteeItemAdminPage as Item,
    CommitteeLeaderCardAdminPage as Leader,
    CommitteeMandateItemAdminPage as Mandate,
    SectoralCommitteesPageAdminPage as Page,
)
from cms.tests.certificate_of_origin.b_checks import unique_qctest_titles  # noqa: F401 - autouse
from cms.tests.sectoral_committees import cc_checks as cc
from cms.tests.sectoral_committees import sc_fix as scf

EV = Path(__file__).resolve().parents[3] / "reports" / "bug-evidence"


def _ev(group, name, page, data):
    d = EV / f"130716-{group}"
    d.mkdir(parents=True, exist_ok=True)
    page.screenshot(path=str(d / f"{name}.png"), full_page=True)
    (d / f"{name}.json").write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"[repro {group}/{name}] {json.dumps(data, ensure_ascii=False)[:700]}")


def _spin(page, admin, key):
    return page.get_by_role("spinbutton", name=admin.label_pattern(admin.FIELDS[key].label)).first


def test_r1_leader_display_number(page, browser):
    """146935: type 99 in Display Number, publish (Active ticked), read the public card number."""
    admin = Leader(page)
    t = cc.title(146935, "num99")
    ctx, anon = cc._anon(browser)
    try:
        admin.open_form(ROLE_EDITOR)
        box = _spin(page, admin, "display_number")
        info = {"editable": box.is_editable(), "readonly_attr": box.get_attribute("readonly"),
                "disabled_attr": box.get_attribute("disabled")}
        admin.fill_required(t, active=True)
        admin.fill("display_number", "99")
        info["form_value_after_typing"] = box.input_value()
        _ev("leader-number", "form_typed_99", page, info)
        admin.submit_for_review()
        info["status"] = admin.status_of(t, ROLE_EDITOR)
        info["stored"] = {k: v for k, v in (admin.entry_json(t) or {}).items() if k in ("id", "displayNumber", "displayOrder", "cardActiveStatus")}
        sc = cc._open_sc(anon)
        cc._expand(anon, sc, "lead")
        anon.wait_for_timeout(1500)
        card = anon.locator("article.qc-sc-leader").filter(has_text=t).first
        info["public_card_number"] = card.locator("span.qc-sc-leader-num").inner_text() if card.count() else None
        info["public_numbers"] = anon.locator("span.qc-sc-leader-num").all_inner_texts()
        if card.count():
            card.scroll_into_view_if_needed()
        _ev("leader-number", "public_grid", anon, info)
    finally:
        cc._delete(admin, t)
        cc._close(ctx)


def test_r2_committee_number(page, browser):
    """146971: Display Order / Number = 99 on a QCTEST committee (Active ticked), read the public badge."""
    admin = Item(page)
    t = cc.title(146971, "num99")
    ctx, anon = cc._anon(browser)
    try:
        admin.open_form(ROLE_EDITOR)
        box = _spin(page, admin, "display_order")
        info = {"editable": box.is_editable(), "readonly_attr": box.get_attribute("readonly")}
        admin.fill_required(t, active=True)
        admin.fill("display_order", "99")
        info["form_value_after_typing"] = box.input_value()
        _ev("committee-number", "form_typed_99", page, info)
        admin.submit_for_review()
        info["status"] = admin.status_of(t, ROLE_EDITOR)
        info["stored"] = {k: v for k, v in (admin.entry_json(t) or {}).items() if k in ("id", "displayOrder", "itemActiveStatus")}
        cc.sc_probe(cc.DIRECTORY)(anon, t)
        row = anon.locator("div.qc-sc-row").filter(has_text=t).first
        info["public_badge"] = row.locator("span.qc-sc-row-num").inner_text() if row.count() else None
        info["public_badges"] = anon.locator("span.qc-sc-row-num").all_inner_texts()
        if row.count():
            row.scroll_into_view_if_needed()
        _ev("committee-number", "public_list", anon, info)
    finally:
        cc._delete(admin, t)
        cc._close(ctx)


def _pick_evidence(page, admin_cls, key, fixture, group, name):
    import os
    admin, seen = cc._pick(page, admin_cls, f"a5{name}", key, fixture)
    seen["fixture_bytes"] = os.path.getsize(fixture)
    _ev(group, name, page, seen)


def test_r3_hero_bg_size(page):
    """146904: exactly 2 MiB / 2 MiB + 1 byte / 3 MB on the + Add New Page form; nothing saved."""
    over = cc.runtime_fixture("hero-2MBplus1.png", "png", 2 * cc.MB + 1)
    _pick_evidence(page, Page, "hero_bg", cc.runtime_fixture("hero-2MB.png", "png", 2 * cc.MB), "hero-size", "exact_2MiB")
    _pick_evidence(page, Page, "hero_bg", over, "hero-size", "2MiB_plus_1")
    _pick_evidence(page, Page, "hero_bg", cc.BIG_JPG_3MB, "hero-size", "3MB_jpg")


def test_r4_cta_icon(page):
    """147008 / 147010: the Card Icon control on the + Add New CTA form; custom.svg attached; nothing saved."""
    admin = Cta(page)
    admin.open_form(ROLE_EDITOR)
    label = Cta.FIELDS["card_icon"].label
    info = {"file_upload_controls": page.get_by_role("textbox", name=f"{label} Select File").count(),
            "comboboxes": page.get_by_role("combobox", name=admin.label_pattern(label)).count(),
            "radiogroups": page.get_by_role("radiogroup", name=admin.label_pattern(label)).count()}
    _ev("cta-icon", "card_icon_control", page, info)
    _pick_evidence(page, Cta, "card_icon", cc.runtime_fixture("custom.svg", "svg", 2 * 1024), "cta-icon", "custom_svg")


def test_r5_cta_bad_target(page):
    """147023: target '/no-such-page-130716', Active UNTICKED, Submit; status + stored value; deleted by ID."""
    admin = Cta(page)
    t = cc.title(147023, "badurl")
    try:
        admin.open_form(ROLE_EDITOR)
        admin.fill_required(t, active=False, files={"card_icon": cc.VALID_PNG})
        admin.fill("target_url", "/no-such-page-130716")
        admin.submit_for_review()
        info = {"refusal_visible": admin.refusal_visible(), "status": admin.status_of(t, ROLE_EDITOR),
                "stored": {k: v for k, v in (admin.entry_json(t) or {}).items()
                           if k in ("id", "targetUrl", "targetURL", "targetLink", "cardActiveStatus", "status")}}
        _ev("cta-target", "submit_bad_target", page, info)
    finally:
        cc._delete(admin, t)


def test_r6_committee_without_bullet(page):
    """147048 root: a committee (Active UNTICKED) with NO mandate bullet is submitted; then one bullet is
    linked and removed. Records statuses; everything deleted by ID (mandate purged)."""
    item, mand = Item(page), Mandate(page)
    c, b = cc.title(147048, "nobullet"), cc.title(147048, "only")
    mid = None
    try:
        item.open_form(ROLE_EDITOR)
        item.fill_required(c, active=False)
        item.submit_for_review()
        info = {"committee_refusal_visible": item.refusal_visible(), "committee_status_no_bullet": item.status_of(c, ROLE_EDITOR)}
        _ev("mandate-min", "committee_without_bullet", page, info)
        cc._publish(mand, b, extra={"committee": c, "display_order": "100"}, ar_extra={"bullet": "بند وحيد اختبار"})
        mid = mand.id_for(b)
        ok = mand.delete_disposable(b)
        info.update({"bullet_id": mid, "remove_only_bullet_ran": ok, "bullet_still_listed": mand.entry_exists(b, ROLE_EDITOR),
                     "committee_status_after": item.status_of(c, ROLE_EDITOR)})
        _ev("mandate-min", "remove_only_bullet", page, info)
    finally:
        cc._delete(mand, b)
        erc = (item.entry_json(c) or {}).get("externalReferenceCode")
        scf._purge_trashed(mand, mid, erc)
        cc._delete(item, c)
