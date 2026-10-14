import re
p="web/tests/home_strategic_direction/test_home_strategic_direction_web.py"
s=open(p,encoding="utf-8").read()
helper='''

# Rule 1 (bug-rules.md): images +/-5 px, layout +/-2 px, text exact.
IMG_TOL, LAYOUT_TOL = 5, 2


def _near(value, target, tol=LAYOUT_TOL) -> bool:
    v = float(str(value).replace("px", "")) if value not in (None, "") else float("nan")
    return abs(v - target) <= tol
'''
anchor='PBI = "129381"\n'
s=s.replace(anchor, anchor+helper,1)
rep=[
 ('assert style["width"] == "516px", f"expected card width 516px', 'assert _near(style["width"], 516), f"expected card width 516px (+/-2)'),
 ('assert round(next_size["width"]) == 40 and round(next_size["height"]) == 40,', 'assert _near(next_size["width"], 40) and _near(next_size["height"], 40),'),
 ('assert round(prev_size["width"]) == 40 and round(prev_size["height"]) == 40,', 'assert _near(prev_size["width"], 40) and _near(prev_size["height"], 40),'),
 ('assert round(gaps["left"]) == 300,', 'assert _near(gaps["left"], 300),'),
 ('assert round(gaps["right"]) == 300,', 'assert _near(gaps["right"], 300),'),
 ('assert round(box["width"]) == 636,', 'assert _near(box["width"], 636),'),
 ('assert round(prev_gap) == 20,', 'assert _near(prev_gap, 20),'),
 ('assert round(next_gap) == 20,', 'assert _near(next_gap, 20),'),
 ('assert round(icon_size["width"]) == 72 and round(icon_size["height"]) == 72,', 'assert _near(icon_size["width"], 72, IMG_TOL) and _near(icon_size["height"], 72, IMG_TOL),'),
 ('assert card_style["paddingTop"] == "20px",', 'assert _near(card_style["paddingTop"], 20),'),
 ('assert card_style["paddingBottom"] == "20px",', 'assert _near(card_style["paddingBottom"], 20),'),
 ('assert card_style["paddingLeft"] == "24px"', 'assert _near(card_style["paddingLeft"], 24)'),
 ('assert card_style["paddingRight"] == "24px"', 'assert _near(card_style["paddingRight"], 24)'),
 ('assert round(carousel_box["width"]) == 636,', 'assert _near(carousel_box["width"], 636),'),
]
for a,b in rep:
    n=s.count(a); assert n>=1,(a,n); s=s.replace(a,b)
open(p,"w",encoding="utf-8").write(s)
print("ok")
