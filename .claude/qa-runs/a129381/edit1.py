p="cms/tests/home_strategic_direction/test_home_strategic_direction_control_panel.py"
s=open(p,encoding="utf-8").read()
old_helper=s[s.index("def _raw_row_status("):s.index("def _marks(")]
s=s.replace(old_helper,"")
s=s.replace("raw = _raw_row_status(admin, title)","raw = admin.raw_row_status(title)")
old=s[s.index("@_marks(135603"):s.index("@_marks(135606")]
new='''@_marks(135603, allure.severity_level.NORMAL)
@pytest.mark.tc_135603
@allure.title("Pillar Title (AR) empty is refused")
def test_title_ar_empty(page):
    """TC 135603 — account: QC Site Content Editor. EN title is a QCTEST
    title (so a wrongly-accepted record is still found and torn down), AR
    title empty; Submit for Review must be refused and nothing published."""
    admin = ADMIN(page)
    title = qctest_title(135603, "ar-empty")
    try:
        admin.open_form(ROLE_EDITOR)
        admin.fill_required(title, active=True, files=FILES)
        admin.fill("pillar_title", "", locale="ar")
        ac._submit_and_expect_refusal(admin, title, "Pillar Title (AR) empty")
    finally:
        admin.delete_disposable(title)


'''
s=s.replace(old,new)
open(p,"w",encoding="utf-8").write(s)
