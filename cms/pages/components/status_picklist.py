"""
cms/pages/components/status_picklist.py -- one robust "pick an option in the
record's Status picklist" action for the qc-oel Object Authoring form.

Added 2026-10-13 (P3/P4 batch: About 134737/134738, Chairman 134835/134836,
Chamber Laws 134937/134938). Page Objects call `pick_status_option()` from
their own `pick_page_status()`; the combobox selector stays on the Page
Object.

Why one action instead of "read options" + "choose": on this form family the
list ignores Escape and its toggle TOGGLES (live 2026-10-13,
DisposableObjectAdminPage._open_options), so a read-then-reopen sequence
closes the list and the option click waits 30 s on a hidden <li>; and an
option click can intermittently leave the combobox empty. This opens the
list ONCE, reads every option, clicks the wanted one, verifies the value by
read-back and re-picks once if it did not take.
"""

from __future__ import annotations

OPTIONS_VISIBLE_MS = 10000
OPTION_CLICK_MS = 10000


def _norm(text: str) -> str:
    return " ".join((text or "").split()).casefold()


def _open_options(page, combobox):
    """Opens the list unless already open (toggle button first: a bare
    second click on the input toggles it shut)."""
    listbox_id = combobox.get_attribute("aria-controls")
    if combobox.get_attribute("aria-expanded") != "true":
        toggle = page.locator(f'button[aria-controls="{listbox_id}"]') if listbox_id else None
        if toggle is not None and toggle.count():
            toggle.first.click()
        else:
            combobox.click()
    if listbox_id:
        options = page.locator(f'[id="{listbox_id}"] [role="option"]')
    else:
        options = page.locator('[role="listbox"]:visible [role="option"]')
    options.first.wait_for(state="visible", timeout=OPTIONS_VISIBLE_MS)
    return options


def _close_options(page, combobox) -> None:
    page.keyboard.press("Escape")
    if combobox.get_attribute("aria-expanded") != "true":
        return
    listbox_id = combobox.get_attribute("aria-controls")
    toggle = page.locator(f'button[aria-controls="{listbox_id}"]') if listbox_id else None
    if toggle is not None and toggle.count():
        toggle.first.click()


FORM_FIELDS = '[name^="ObjectField_"]'
FORM_RENDERED_MS = 20000
PICKLIST_RENDERED_MS = 8000
NOT_RENDERED_PREFIX = "FINDING -- the record's edit form renders no Status picklist"


def require_status_picklist(page, *selectors: str) -> None:
    """Fails fast, with evidence, when the edit form renders none of
    `selectors` (2026-10-13, live: About / Chairman / Chamber Laws forms
    render no `pageStatus` / `publishStatus` field -- every read waited the
    default 30 s and burned the 480 s budget). Waits for the form's own
    fields first so a still-loading form is not mistaken for a missing
    field, then up to PICKLIST_RENDERED_MS for the picklist itself."""
    page.locator(FORM_FIELDS).first.wait_for(state="attached", timeout=FORM_RENDERED_MS)
    wanted = page.locator(", ".join(selectors))
    try:
        wanted.first.wait_for(state="attached", timeout=PICKLIST_RENDERED_MS)
        return
    except Exception:  # noqa: BLE001 -- reported below with what the form does render
        pass
    names = page.evaluate(
        "() => [...new Set(Array.from(document.querySelectorAll('[name^=\"ObjectField_\"]'))"
        ".map(e => e.name.replace(/_(en_US|ar_SA)$/, '')))]")
    body = page.locator("body").inner_text()
    banner = next((line.strip() for line in body.splitlines() if line.strip().startswith("Editing ")), "")
    raise AssertionError(
        f"{NOT_RENDERED_PREFIX} ({' | '.join(selectors)}). Editing banner: {banner[:160]!r}. "
        f"Fields the form renders: {names}")


def pick_status_option(page, combobox_selector: str, option: str, read_value) -> list:
    """Opens the picklist at `combobox_selector` once, returns EVERY option
    text it offered (in order), and selects `option` (exact, whitespace /
    case-normalized). `read_value()` reads the field back; one re-pick when
    the click left it on something else. Raises LookupError when `option`
    is not offered, naming what was."""
    require_status_picklist(page, combobox_selector)
    combobox = page.locator(combobox_selector).first
    options = _open_options(page, combobox)
    texts = [t.strip() for t in options.all_inner_texts()]
    pick = next((i for i, t in enumerate(texts) if _norm(t) == _norm(option)), None)
    if pick is None:
        _close_options(page, combobox)
        raise LookupError(f"Status picklist offers no {option!r}; it offers {texts}")
    options.nth(pick).click(timeout=OPTION_CLICK_MS)
    if _norm(read_value()) != _norm(option):
        _open_options(page, combobox).nth(pick).click(timeout=OPTION_CLICK_MS)
        got = read_value()
        if _norm(got) != _norm(option):
            raise LookupError(f"picked {option!r} but the Status field reads {got!r}")
    return texts
