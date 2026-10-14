"""
cms/tests/qafl_membership/qafl_checks.py — PBI 130718 overrides of shared A4 checks
(cms/tests/sectoral_committees/cc_checks.py is owned by Engineer A5 from 2026-10-04
and is not edited from here).

check_role_no_form: run 2026-10-04 (tc_146539) showed the second role's login never
completing after the Editor's create form was opened: leaving a dirty Object Authoring
form raises a `beforeunload` dialog, which Playwright dismisses by default, so the
navigation to the login page was cancelled. The dialog is accepted here (nothing was
typed into the form, so nothing is lost or saved).
"""

from cms.pages.components.disposable_object_admin import ROLE_EDITOR
from cms.pages.control_panel.login_page import CmsLoginPage


def check_role_no_form(page, admin_cls, role, positive_role=ROLE_EDITOR):
    """`role` opens the object's manage URL and is not given an enabled submit;
    positive control: `positive_role` gets the form at the same URL in the same run."""
    admin = admin_cls(page)
    admin.open_form(positive_role)
    assert page.locator(admin.SUBMIT_FOR_REVIEW_BUTTON).count(), f"control: {positive_role} got no form"
    page.on("dialog", lambda d: d.accept())  # beforeunload of the untouched create form
    admin.sign_in(role)
    assert CmsLoginPage(page).login_succeeded(), f"{role} did not sign in"
    page.goto(admin.manage_url(), wait_until="domcontentloaded")
    page.wait_for_timeout(6000)  # measured: the manage page mounts its list/form within ~5 s
    add = page.locator('button:has-text("+ Add New"), a:has-text("+ Add New")')
    if add.count():
        try:
            add.first.click(timeout=5000)
            page.wait_for_timeout(4000)
        except Exception:  # noqa: BLE001 - a hidden/disabled "+ Add New" is itself a denial
            pass
    enabled = page.locator(f"{admin.SUBMIT_FOR_REVIEW_BUTTON}:not([disabled])").count()
    assert enabled == 0, f"{role} is given an enabled submit on {admin_cls.SIDEBAR_LABEL}"
    for a in ("publish", "unpublish", "delete"):
        assert page.locator(f"[data-qc-oel-{a}]").count() == 0, f"{role} is offered row action {a!r}"
