p="cms/tests/home_strategic_direction/test_home_strategic_direction_control_panel.py"
s=open(p,encoding="utf-8").read()
a=s.index('    """TC 135606 — account: QC Site Content Editor. Types plain text')
b=s.index("@_marks(135607")
body=s[a:b]
new_fn='''    """TC 135606 — account: QC Site Content Editor. Types plain text, then a
    bold phrase (Ctrl+B) in the EN editor; after save + reopen the text and
    a <strong>/<b> element survive."""
    _bold_description(page, 135606)


def _bold_description(page, tc: int) -> None:
    admin = ADMIN(page)
    title = qctest_title(tc, "bold")
'''
rest=body[body.index("    try:"):]
s=s[:a]+new_fn+rest+s[b:]
s+=open(".claude/qa-runs/a129381/append_cms.txt",encoding="utf-8").read()
open(p,"w",encoding="utf-8").write(s)
