"""
cms/tests/sectoral_committees/ne_checks.py - body for the 2026-10-07 batch case
146887 of PBI 130716 (suite 140375). Not a test module. OFFLINE scripted, not
executed.
"""

from __future__ import annotations

from cms.pages.components.disposable_object_admin import ROLE_EDITOR


def check_field_not_editable(page, admin_cls, key: str, attempt: str):
    """Account: Site Content Editor (cms_role_credentials). The case: the field
    is read-only / derived from the menu - no text is accepted. The create form
    is reached through "+ Add New" (_Council guard: the live singleton entry is
    never opened) and is LEFT UNSAVED: no submit is ever clicked, so nothing is
    stored."""
    admin = admin_cls(page)
    spec = admin_cls.FIELDS[key]
    admin.open_form(ROLE_EDITOR)
    box = page.get_by_role("textbox", name=admin.label_pattern(spec.label)).first
    assert page.get_by_role("textbox", name=admin.label_pattern(spec.label)).count(), (
        f"no {spec.label!r} textbox on the form (recorded as confirmed live 2026-10-04): the label may have "
        "changed - re-read the form before judging the case")
    before = box.input_value()
    state = box.evaluate("e => ({ro: e.readOnly, dis: e.disabled, aria: e.getAttribute('aria-readonly')})")
    try:
        box.click(timeout=3000)
        page.keyboard.type(attempt)
    except Exception:  # noqa: BLE001 - a control that cannot be focused accepts no text
        pass
    after = box.input_value()
    assert attempt not in after and after == before, (
        f"{spec.label} accepted typed text: {before!r} -> {after!r} (readOnly/disabled state {state!r}); "
        "the case expects a read-only, menu-derived value")
