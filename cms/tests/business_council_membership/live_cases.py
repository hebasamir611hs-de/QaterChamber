"""
cms/tests/business_council_membership/live_cases.py - bodies of the PBI 130719
CONDITIONAL cases that act on the LIVE Business Council Request Page entry
183176 (user approval 2026-10-04, Engineer A6). Not a test module.

Every case runs only under reports/live-restore/live_restore.py's
snapshot -> run -> restore cycle (the test is skipped unless
QC_LIVE_SINGLETON_RUN=183176). The record is Editor-only (drafts off: the
form's submit IS the save).
"""

from __future__ import annotations

from pathlib import Path

from cms.pages.business_council_membership.business_council_membership_admin_page import (
    LIVE_PAGE_ID,
    BusinessCouncilRequestPageAdminPage as Page,
)
from cms.tests.sectoral_committees import cc_checks as cc
from cms.tests.sectoral_committees import live_checks as lc

LID = LIVE_PAGE_ID
PATH = lc.BCMR_PATH
H1 = "h1.qc-bcm-hero__title"
HERO_SUB = "p.qc-bcm-hero__subtitle"

# JSON refs of the form fields (read from the live record)
REF = {"page_title": "pageTitle", "hero_description": "heroDescription", "hero_image": "heroImage"}


def _clear_rich(admin, key, locale="en", value=""):
    sel = admin._rich_iframe(key, locale)
    body = admin.page.frame_locator(sel).locator("body")
    body.wait_for(state="visible", timeout=30000)
    body.click()
    kb = admin.page.keyboard
    kb.press("Control+A")
    kb.press("Delete")
    if value:
        kb.type(value)


def _set(admin, key, value, locale="en"):
    if Page.FIELDS[key].kind == "rich":
        _clear_rich(admin, key, locale, value)
    else:
        admin.fill(key, value, locale=locale)


def _i18n(data, key, locale):
    return ((data.get(f"{REF[key]}_i18n") or {}).get("ar_SA" if locale == "ar" else "en_US") or "")


def _refused_unchanged(admin, before, keys, what, targets=()):
    """Submit, then: a positive refusal signal AND the live record unchanged."""
    admin.submit_for_review()
    refused = admin.refusal_visible()
    after = lc.live_json(admin, LID)
    changed = [f"{k}/{loc}" for k in keys for loc in ("en", "ar") if _i18n(before, k, loc) != _i18n(after, k, loc)]
    assert refused and not changed, (
        f"{what}: refused={refused}, stored fields changed={changed} ({admin.save_counts()})")
    if targets:
        # Coordinator rule 2026-10-04: a refusal counts only when it points at the
        # emptied field(s) - every target flagged, and nothing else flagged (the
        # rich editors are primed in open_live, so a CKE flag means an emptied editor).
        inv = (admin.last_save or {}).get("invalid_fields") or []
        cke = sum(1 for f in inv if "ckeditor-required" in f)
        named = [f for f in inv if "ckeditor-required" not in f]
        want_named = [t for t in targets if t != "rich"]
        want_cke = sum(1 for t in targets if t == "rich")
        print(f"[refusal] {what}: invalid fields {inv}")
        assert sorted(named) == sorted(want_named) and cke == want_cke, (
            f"{what}: refused, but the refusal is not attributable to the emptied field(s): flagged {inv}, "
            f"expected exactly {list(targets)}")
    assert (after.get("status") or {}).get("label") == (before.get("status") or {}).get("label"), (
        f"{what}: the record's status moved to {after.get('status')}")


# ---------------------------------------------------------------------------
def tc_144500(page, browser):
    admin = Page(page)
    lc.open_live(admin, LID)
    lc.fill_bi(admin, "page_title", "QCTEST 144500 Business Council Joining Request", "طلب انضمام اختبار 144500")
    _set(admin, "hero_description", "QCTEST 144500 hero description.")
    _set(admin, "hero_description", "وصف اختبار 144500.", "ar")
    admin.upload("hero_image", cc.VALID_JPG, tag="144500")
    lc.fill_bi(admin, "section_badge", "QCTEST 144500 Badge", "شارة اختبار 144500")
    lc.fill_bi(admin, "section_title", "QCTEST 144500 Section", "قسم اختبار 144500")
    _set(admin, "overview_body", "QCTEST 144500 overview body.")
    _set(admin, "overview_body", "نص نظرة عامة اختبار 144500.", "ar")
    lc.fill_bi(admin, "card_title", "QCTEST 144500 Card", "بطاقة اختبار 144500")
    _set(admin, "card_description", "QCTEST 144500 card description.")
    _set(admin, "card_description", "وصف بطاقة اختبار 144500.", "ar")
    # step 4: Save as Draft -> Draft, visible only in Object Authoring
    lc.save_draft_live(admin, LID)
    ok, got, _ = lc.poll_text(browser, PATH, H1, "QCTEST 144500", timeout=10, expect=False)
    assert ok, f"the Draft is already on the public page: {got!r}"
    # step 6: Publish -> EN and AR content live
    lc.open_live(admin, LID)
    lc.publish_live(admin, LID)
    lc.check_text_both(browser, PATH, H1, "QCTEST 144500 Business Council Joining Request", "طلب انضمام اختبار 144500")


def tc_144506(page, browser):
    admin = Page(page)
    before = lc.open_live(admin, LID)
    admin.fill("page_title", "QCTEST 144506 title")
    admin.fill("page_title", "", locale="ar")
    _set(admin, "hero_description", "QCTEST 144506 hero description.")
    _clear_rich(admin, "hero_description", "ar")
    _refused_unchanged(admin, before, ("page_title", "hero_description"), "AR Page Title + AR Hero Description empty",
                       ("qc-ar-pageTitle", "rich"))


def _empty_case(page, key, locale, value=""):
    admin = Page(page)
    before = lc.open_live(admin, LID)
    _set(admin, key, value, locale)
    ref = REF[key]
    tgt = ("rich",) if Page.FIELDS[key].kind == "rich" else ((f"qc-ar-{ref}",) if locale == "ar" else (f"ObjectField_{ref}",))
    _refused_unchanged(admin, before, (key,), f"{key} {locale.upper()}={value!r}", tgt)


def tc_144508(page, browser):
    _empty_case(page, "page_title", "en")


def tc_144511(page, browser):
    _empty_case(page, "page_title", "ar")


def tc_144514(page, browser):
    _empty_case(page, "hero_description", "en")


def tc_144516(page, browser):
    _empty_case(page, "hero_description", "ar")


def tc_144510(page, browser):
    _empty_case(page, "page_title", "en", "   ")


def tc_144513(page, browser):
    _empty_case(page, "page_title", "ar", "   ")


def tc_144515(page, browser):
    _empty_case(page, "hero_description", "en", "   ")


def tc_144517(page, browser):
    _empty_case(page, "hero_description", "ar", "   ")


def _pick_then_save(admin, fixture, tc):
    """Attach `fixture` to Hero Image on the live form and click Save.
    Returns (picker_message, readout, stored_image_id_before, after)."""
    import re as _re

    before = lc.open_live(admin, LID)
    msg, readout = "", None
    try:
        admin.upload("hero_image", fixture, tag=str(tc))
    except Exception as exc:  # noqa: BLE001 - the picker itself refusing the file
        # Run 2026-10-04 (tc_144518): the modal's "Add" never became clickable.
        # A timeout is not a refusal: read the modal's own text for the error.
        shot = Path(__file__).resolve().parents[3] / "reports" / "live-restore" / LID / f"{tc}_picker.png"
        try:
            admin.page.screenshot(path=str(shot))
        except Exception:  # noqa: BLE001
            pass
        modal = ""
        try:
            modal = " ".join(admin.page.frame_locator(admin.UPLOAD_MODAL_IFRAME).locator("body")
                             .inner_text(timeout=5000).split())
        except Exception:  # noqa: BLE001
            pass
        err = _re.search(r"[^.]*(?:" + cc._SIZE_RE + r"|extension|format|file type|maximum|size)[^.]*\.?", modal, _re.I)
        msg = f"picker modal: {err.group(0).strip()[:200]}" if err else ""
        print(f"[tc_{tc}] picker did not attach ({str(exc)[:80]}); modal text: {modal[:400]!r}")
        for name in ("Cancel", "Close"):
            try:
                admin.page.frame_locator(admin.UPLOAD_MODAL_IFRAME).get_by_role("button", name=name).first.click(
                    timeout=3000)
                break
            except Exception:  # noqa: BLE001
                try:
                    admin.page.get_by_role("button", name=name).last.click(timeout=3000)
                    break
                except Exception:  # noqa: BLE001
                    continue
    admin.page.wait_for_timeout(2000)  # the size/type check runs after the readout (b9 probe)
    texts = admin.page.locator(".alert-danger, .form-feedback-item, [role=alert]").all_inner_texts()
    hits = [" ".join(t.split()) for t in texts if _re.search(cc._SIZE_RE, t, _re.I)]
    msg = msg or (hits[0] if hits else "")
    try:
        readout = admin.uploaded_filename(Page.FIELDS["hero_image"].label)
    except Exception:  # noqa: BLE001
        readout = None
    print(f"[tc_{tc}] {Path(fixture).name}: message={msg!r} readout={readout!r}")
    admin.submit_for_review()
    after = lc.live_json(admin, LID)
    return msg, readout, lc.file_id(before, "heroImage"), after


def tc_144518(page, browser):
    admin = Page(page)
    msg, readout, old, after = _pick_then_save(admin, cc.runtime_fixture("hero_200kb.gif", "gif", 200 * 1024), 144518)
    new = lc.file_id(after, "heroImage")
    assert new == old, f"the .gif was SAVED as Hero Image (file id {old} -> {new}; picker message {msg!r})"
    assert msg or not readout, f"the .gif stayed attached ({readout!r}) with no unsupported-format error"


def tc_144519(page, browser):
    admin = Page(page)
    msg, readout, old, after = _pick_then_save(admin, cc.BIG_JPG_3MB, 144519)
    new = lc.file_id(after, "heroImage")
    assert new == old, f"the 3 MB .jpg was SAVED as Hero Image (file id {old} -> {new}; picker message {msg!r})"
    assert msg or not readout, f"the 3 MB .jpg stayed attached ({readout!r}) with no file-size error"


def tc_144595(page, browser):
    admin = Page(page)
    fx = cc.runtime_fixture("hero_2mb.jpg", "jpg", 2 * cc.MB)
    assert Path(fx).stat().st_size == 2 * cc.MB
    msg, readout, old, after = _pick_then_save(admin, fx, 144595)
    new = lc.file_id(after, "heroImage")
    assert not msg and readout, f"the exactly-2.00 MB JPG was refused at the picker ({msg!r}, readout {readout!r})"
    assert lc.saved(admin, LID) and new and new != old, (
        f"the exactly-2.00 MB JPG was not saved at Save (file id {old} -> {new}; {admin.save_counts()})")


def tc_144520(page, browser):
    admin = Page(page)
    before = lc.open_live(admin, LID)
    how = lc.clear_file(admin, "hero_image")
    print(f"[tc_144520] Hero Image cleared via {how!r}")
    admin.submit_for_review()
    refused = admin.refusal_visible()
    after = lc.live_json(admin, LID)
    assert refused and lc.file_id(after, "heroImage") == lc.file_id(before, "heroImage"), (
        f"Hero Image empty: refused={refused}, stored image {lc.file_id(before, 'heroImage')} -> "
        f"{lc.file_id(after, 'heroImage')} ({admin.save_counts()})")
    inv = (admin.last_save or {}).get("invalid_fields") or []
    print(f"[refusal] Hero Image empty: invalid fields {inv}")
    assert inv == ["ObjectField_heroImage"], (
        f"Hero Image empty: refused, but the refusal is not attributable to Hero Image (flagged {inv})")


def tc_144576(page, browser):
    admin = Page(page)
    lc.open_live(admin, LID)
    new = "QCTEST 144576 draft hero description."
    _set(admin, "hero_description", new)
    lc.save_draft_live(admin, LID)
    ok, got, _ = lc.poll_text(browser, PATH, HERO_SUB, "QCTEST 144576", timeout=10, expect=False)
    assert ok, f"the live public page shows the draft value: {got!r}"


def tc_144577(page, browser):
    admin = Page(page)
    lc.row_action_live(admin, LID, "unpublish")
    st = lc.wait_status(admin, LID, "Unpublished")
    assert st == "Unpublished", f"after Unpublish the record is {st!r}"
    lc.assert_not_served(browser, PATH, H1, "en")
