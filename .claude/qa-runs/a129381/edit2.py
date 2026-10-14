p="cms/tests/home_strategic_direction/test_home_strategic_direction_control_panel.py"
s=open(p,encoding="utf-8").read()
old="""    ac.check_author_submit_pending(page, ADMIN, 135551, files=FILES)
"""
new="""    admin = ADMIN(page)
    title = qctest_title(135551, "author")
    try:
        admin.open_form(ROLE_AUTHOR)
        assert not admin.has_admin_toolbar(), ac.NOT_ROLE
        admin.fill_required(title, active=True, files=FILES)
        admin.save_as_draft()
        assert admin.status_of(title, ROLE_AUTHOR) == STATUS_DRAFT, "Author's draft did not save as Draft"
        admin.open_entry_by_edit_link(title)
        # The submit label differs per object/role (Submit for Review /
        # Submit for Publishing / Publish) — recorded, not asserted (Rule 5).
        allure.attach(admin.submit_button_label(), "Author submit button label", allure.attachment_type.TEXT)
        admin.submit_for_review()
        assert admin.status_of(title, ROLE_AUTHOR) == STATUS_PENDING_REVIEW, (
            "Author's submit did not land on Pending Review (publish was not blocked)"
        )
        assert not admin.row_offers_action(title, "approve"), "Author is offered Approve on its own entry"
        assert not admin.row_offers_action(title, "publish"), "Author is offered Publish on its own entry"
    finally:
        admin.delete_disposable(title, ROLE_EDITOR)
"""
assert old in s
s=s.replace(old,new)
open(p,"w",encoding="utf-8").write(s)
