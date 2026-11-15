"""Cancer Care Atlas for Canva, told as a story: a hook, the gap, the question, two actions, the pilot.

Nine slides in the app's AstraZeneca palette: a light page, white cards, the purple plate for the map,
mulberry for action, lime for the one selected thing, gold and light blue for worse and better.
Two looping videos (make_videos.py) carry the motion: the county map and the days on two routes into care.
Every number comes from the running app (pathway-watch) or from the evaluation deck it built.
Coordinates are pixels of a 1600 x 900 slide; 120 px is one inch.

uv run --with python-pptx --with pillow python atlas_canva.py
"""
import os
from pptx import Presentation
from pptx.util import Emu, Pt
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.enum.shapes import MSO_SHAPE
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
A = lambda n: os.path.join(HERE, "assets", n)
OUT = os.path.join(HERE, "Cancer Care Atlas (story).pptx")


def c(h): return RGBColor.from_string(h.lstrip("#"))


MULBERRY, PURPLE, LIME, GOLD, LBLUE, NAVY = c("#830051"), c("#3c1053"), c("#c4d600"), c("#f0ab00"), c("#68d2df"), c("#003865")
BG, SURF, INK, MUTED, LINE, LINE2, CHIP = c("#f5f2f5"), c("#ffffff"), c("#231a26"), c("#5d5262"), c("#e4dce5"), c("#b6a9b9"), c("#f7e7f0")
BELOW, BELOW_BG, ABOVE = c("#a86400"), c("#fdf4e1"), c("#00728f")
PLATE_INK, PLATE_MUTED, PLATE_LINE = c("#f7f0f8"), c("#cdbad5"), c("#6e4c82")
GOLD_SOFT, BLUE_SOFT, NEAR = c("#b5841c"), c("#3b7f93"), c("#594470")
SEG_P, SEG_C, SEG_H = c("#6b5f70"), c("#c98a00"), MULBERRY
BODY, DISPLAY = "IBM Plex Sans", "IBM Plex Sans"  # Canva has no Familjen Grotesk, the display face of the app
PX = 914400 // 120


def px(v): return Emu(int(v * PX))


p = Presentation(); p.slide_width, p.slide_height = px(1600), px(900)
N = [0]; TOTAL = 11


def new(bg=BG):
    s = p.slides.add_slide(p.slide_layouts[6]); f = s.background.fill; f.solid(); f.fore_color.rgb = bg
    N[0] += 1
    return s


def text(s, x, y, w, h, t, size, color=INK, bold=False, align=PP_ALIGN.LEFT, anchor=MSO_ANCHOR.TOP, font=BODY, gap=0.0, spacing=None):
    b = s.shapes.add_textbox(px(x), px(y), px(w), px(h)); tf = b.text_frame
    tf.word_wrap = True; tf.vertical_anchor = anchor
    tf.margin_left = tf.margin_right = tf.margin_top = tf.margin_bottom = 0
    for i, line in enumerate(t if isinstance(t, list) else [t]):
        para = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        para.alignment = align; para.space_after = Pt(size * 0.75 * gap)
        for rt, rb in (line if isinstance(line, tuple) and isinstance(line[0], tuple) else ((line, bold),)):
            r = para.add_run(); r.text = rt
            r.font.size = Pt(size * 0.75); r.font.bold = rb; r.font.name = font; r.font.color.rgb = color
    return b


def rect(s, x, y, w, h, fill=SURF, line=LINE, lw=1, radius=10, shape=MSO_SHAPE.ROUNDED_RECTANGLE):
    r = s.shapes.add_shape(shape, px(x), px(y), px(w), px(h))
    if fill is None: r.fill.background()
    else: r.fill.solid(); r.fill.fore_color.rgb = fill
    if line is None: r.line.fill.background()
    else: r.line.color.rgb = line; r.line.width = Pt(lw * 0.75)
    if shape == MSO_SHAPE.ROUNDED_RECTANGLE: r.adjustments[0] = min(0.5, radius / min(w, h))
    r.shadow.inherit = False
    return r


def bar(s, x, y, w, h, color): return rect(s, x, y, w, h, fill=color, line=None, shape=MSO_SHAPE.RECTANGLE)
def hline(s, x, y, w, color=LINE):
    ln = s.shapes.add_connector(1, px(x), px(y), px(x + w), px(y)); ln.line.color.rgb = color; ln.line.width = Pt(0.75)


def pic(s, path, x, y, w=None, h=None):
    iw, ih = Image.open(path).size
    if w and h:
        k = min(w / iw, h / ih); ww, hh = iw * k, ih * k; x += (w - ww) / 2; y += (h - hh) / 2; w, h = ww, hh
    elif w: h = ih * w / iw
    else: w = iw * h / ih
    s.shapes.add_picture(path, px(x), px(y), px(w), px(h)); return w, h


def chip(s, x, y, label, fg=MULBERRY, bg=CHIP, line=None, size=14):
    w = 8.4 * len(label) * size / 14 + 28
    rect(s, x, y, w, 30, fill=bg, line=line, radius=15)
    text(s, x + 14, y, w, 30, label, size, fg, True, anchor=MSO_ANCHOR.MIDDLE)
    return w


def header(s, eyebrow, title, sub=None):
    bar(s, 0, 0, 1600, 6, MULBERRY)
    pic(s, A("brandmark.png"), 80, 36, h=30)
    text(s, 120, 36, 400, 30, "CANCER CARE ATLAS", 15, INK, True, anchor=MSO_ANCHOR.MIDDLE)
    text(s, 900, 36, 620, 30, "AstraZeneca · Equal Care Across Finland", 14, MUTED, align=PP_ALIGN.RIGHT, anchor=MSO_ANCHOR.MIDDLE)
    bar(s, 80, 100, 12, 12, MULBERRY)
    text(s, 102, 94, 900, 24, eyebrow.upper(), 14, MULBERRY, True)
    text(s, 80, 124, 1440, 60, title, 40, INK, True, font=DISPLAY)
    if sub: text(s, 80, 182, 1440, 30, sub, 18, MUTED)
    text(s, 80, 856, 900, 22, "A planning tool for a wellbeing services county. It gives no advice about one patient.", 12.5, MUTED)
    text(s, 1320, 856, 200, 22, f"{N[0]} / {TOTAL}", 12.5, MUTED, align=PP_ALIGN.RIGHT)


def kpi(s, x, y, w, h, label, value, note, accent, value_color=INK):
    rect(s, x, y, w, h)
    bar(s, x, y + 1, 5, h - 2, accent)
    text(s, x + 24, y + 18, w - 40, 22, label, 13.5, MUTED, True)
    text(s, x + 24, y + 42, w - 40, 56, value, 40, value_color, True, font=DISPLAY)
    text(s, x + 24, y + 100, w - 40, h - 110, note, 14, MUTED)


def legend(s, x, y, dark=True):
    items = (("3+ below", GOLD), ("1–3 below", GOLD_SOFT), ("near", NEAR), ("1–3 above", BLUE_SOFT), ("3+ above", LBLUE))
    for k, (lab, col) in enumerate(items):
        bar(s, x + k * 82, y, 78, 10, col)
        text(s, x + k * 82, y + 16, 78, 18, lab, 11.5, PLATE_MUTED if dark else MUTED, align=PP_ALIGN.CENTER)



# A sleeker deck: one idea per slide, few words, big numbers.

def big(s, x, y, w, value, caption, color=INK, size=72):
    text(s, x, y, w, size * 1.2, value, size, color, True, font=DISPLAY)
    text(s, x, y + size * 1.5, w, 60, caption, 18, MUTED)


def quiet_header(s, title):
    bar(s, 0, 0, 1600, 6, MULBERRY)
    pic(s, A("brandmark.png"), 80, 40, h=28)
    text(s, 1320, 40, 200, 28, f"{N[0]} / {TOTAL}", 13, MUTED, align=PP_ALIGN.RIGHT, anchor=MSO_ANCHOR.MIDDLE)
    text(s, 80, 110, 1440, 64, title, 44, INK, True, font=DISPLAY)



def full(s, name):
    """The animation as the whole slide: video and slide background are one picture, so no colour box shows."""
    s.shapes.add_movie(os.path.join(HERE, "full", name + ".mp4"), 0, 0, px(1600), px(900),
                       poster_frame_image=os.path.join(HERE, "full", name + "_poster.png"), mime_type="video/mp4")

# 1 Title
s = new(PURPLE); full(s, "s1_map")
bar(s, 0, 0, 1600, 6, LIME)
pic(s, A("brandmark.png"), 90, 120, h=60)
text(s, 90, 220, 860, 240, ["Cancer", "Care Atlas"], 96, PLATE_INK, True, font=DISPLAY)
text(s, 90, 520, 700, 100, "Where patients fall behind, and the first step to take.", 28, PLATE_INK)
rect(s, 90, 700, 236, 70, fill=SURF, line=None, radius=12)
pic(s, A("astrazeneca.png"), 108, 710, 200, 50)
text(s, 90, 800, 700, 26, "Team Kindergarten Engineering · Junction 2026", 15, PLATE_MUTED)
legend(s, 1040, 836)

# 2 The hook
s = new(PURPLE); full(s, "s2_count")
bar(s, 0, 0, 1600, 6, LIME)
text(s, 1000, 300, 520, 200, "longer to treatment when the first visit is a public health centre.", 30, PLATE_INK, True)
text(s, 1000, 520, 520, 60, "One Finnish lymphoma study, 87 patients. The public group was older. Kuitunen and others, Cancer Medicine 2026.", 15, PLATE_MUTED)
text(s, 1440, 40, 80, 28, f"{N[0]} / {TOTAL}", 13, PLATE_MUTED, align=PP_ALIGN.RIGHT)

# 3 Nobody measures it
s = new(); full(s, "s3_dots"); quiet_header(s, "Sweden measures the wait. Finland does not.")
text(s, 80, 720, 1440, 40, "Regions that publish the share of patients treated within the target time. Sweden, 2025: 47% against a target of 80%.", 18, MUTED)
text(s, 80, 820, 1440, 22, "Regionala cancercentrum i samverkan, annual report 2025", 12.5, MUTED)

# 4 The finding
s = new(); full(s, "s4_map"); quiet_header(s, "Bowel cancer in Satakunta.")
legend(s, 95, 780)
big(s, 600, 240, 420, "64%", "five-year survival, 2024")
big(s, 1060, 240, 460, "68%", "Finland")
big(s, 600, 470, 420, "−4 points", "below Finland, 6 of 6 years", BELOW, 64)
big(s, 1060, 470, 460, "SMR 115", "bowel cancer deaths against the age structure", BELOW, 64)
rect(s, 600, 700, 920, 90, fill=CHIP, line=None)
text(s, 628, 700, 880, 90, "The open data cannot say which step of the pathway causes it.", 20, MULBERRY, True, anchor=MSO_ANCHOR.MIDDLE)

# 5 The question
s = new(PURPLE); full(s, "s5_pathway")
bar(s, 0, 0, 1600, 6, LIME)
text(s, 80, 120, 1440, 70, "Which step causes the gap?", 52, PLATE_INK, True, font=DISPLAY)
text(s, 80, 200, 1440, 40, "The open data cannot say. So the first action finds out.", 24, PLATE_MUTED)
text(s, 1440, 40, 80, 28, f"{N[0]} / {TOTAL}", 13, PLATE_MUTED, align=PP_ALIGN.RIGHT)

# 6 Where the days go
s = new(); full(s, "s6_days"); quiet_header(s, "Where the 84 days go.")
for k, (v, t) in enumerate((("+30", "before the first visit"), ("+40", "in primary care"), ("+14", "in the hospital"))):
    big(s, 120 + k * 480, 650, 400, v + " days", t, MULBERRY, 48)
text(s, 80, 830, 1440, 22, "One lymphoma study, 87 patients. Kuitunen and others, Cancer Medicine 2026.", 12.5, MUTED)

# 7 First step
s = new(); quiet_header(s, "First step: audit the pathway.")
steps = [("Count", "the days in each step, per health centre."), ("Agree", "the data route with the data protection officer."), ("Choose", "the roadmap measure for the slowest step.")]
for k, (h, t) in enumerate(steps):
    x = 80 + k * 380
    text(s, x, 260, 80, 80, f"0{k + 1}", 22, MULBERRY, True)
    text(s, x, 310, 340, 70, h, 48, INK, True, font=DISPLAY)
    text(s, x, 390, 330, 100, t, 19, MUTED)
rect(s, 1240, 230, 280, 560, fill=PURPLE, line=None, radius=12)
text(s, 1266, 260, 230, 22, "WHO", 13, LIME, True)
text(s, 1266, 290, 230, 90, "County cancer lead", 22, PLATE_INK, True)
text(s, 1266, 420, 230, 22, "WHEN", 13, LIME, True)
text(s, 1266, 450, 230, 90, "Next month, in one health centre", 22, PLATE_INK, True)
text(s, 1266, 580, 230, 22, "IN SATAKUNTA", 13, LIME, True)
text(s, 1266, 610, 230, 120, "About 187 new cases a year", 22, PLATE_INK, True)
text(s, 80, 700, 1100, 60, "The audit picks the measure. The data do not.", 24, MULBERRY, True)

# 8 Reminder campaign
s = new(); full(s, "s8_meter"); quiet_header(s, "1,340 more tests reach the target.")
text(s, 80, 190, 1440, 40, "Bowel cancer screening in Satakunta, 2024. Attendance 72.6%, target 80%.", 22, MUTED)
for k, r in enumerate(("In the age group", "Lives in the county", "No test this round")):
    x = 80 + k * 488
    rect(s, x, 610, 464, 120, fill=SURF)
    text(s, x + 28, 630, 120, 30, f"Rule {k + 1}", 14, MULBERRY, True)
    text(s, x + 28, 664, 420, 50, r, 26, INK, True, font=DISPLAY)
text(s, 80, 760, 1440, 30, "Three yes or no rules decide who gets a reminder. No diagnosis, no income, no language.", 18, MUTED)

# 9 Trust
s = new(); quiet_header(s, "Every number names its source.")
items = [("Open data", "Sotkanet, Statistics Finland, NORDCAN"), ("Code computes", "Tests trace numbers to raw files"),
         ("AI writes words only", "No patient data, no choice of action"), ("Limits in view", "Intervals and gaps sit by the number")]
for k, (h, t) in enumerate(items):
    x = 80 + k * 362
    rect(s, x, 300, 346, 360, fill=SURF)
    rect(s, x + 28, 330, 44, 44, fill=CHIP, line=None, radius=10)
    text(s, x + 28, 330, 44, 44, str(k + 1), 18, MULBERRY, True, PP_ALIGN.CENTER, MSO_ANCHOR.MIDDLE)
    text(s, x + 28, 410, 300, 80, h, 28, INK, True, font=DISPLAY)
    text(s, x + 28, 500, 290, 120, t, 18, MUTED)

# 10 Next
s = new(PURPLE)
bar(s, 0, 0, 1600, 6, LIME)
text(s, 80, 110, 1440, 70, "Next: a 90-day pilot with one county.", 48, PLATE_INK, True, font=DISPLAY)
for k, (d, h) in enumerate((("Days 1–30", "Team and permission"), ("Days 31–60", "Baseline"), ("Days 61–90", "Go or no go"))):
    x = 80 + k * 488
    rect(s, x, 260, 464, 260, fill=c("#4a1f5e") if k < 2 else LIME, line=None)
    text(s, x + 32, 290, 400, 24, d.upper(), 14, LIME if k < 2 else PURPLE, True)
    text(s, x + 32, 330, 400, 120, h, 36, PLATE_INK if k < 2 else PURPLE, True, font=DISPLAY)
text(s, 80, 600, 1440, 60, "Patient records never leave the county.", 40, LIME, True, font=DISPLAY)
text(s, 80, 680, 1100, 30, "The local steps are our proposals. No county reviewed them yet.", 18, PLATE_MUTED)
rect(s, 1284, 760, 236, 70, fill=SURF, line=None, radius=12)
pic(s, A("astrazeneca.png"), 1302, 770, 200, 50)
text(s, 1440, 40, 80, 28, f"{N[0]} / {TOTAL}", 13, PLATE_MUTED, align=PP_ALIGN.RIGHT)

# 11 Sources
s = new(); quiet_header(s, "Sources.")
src = ["THL Sotkanet, indicators 3627 and 6103", "Statistics Finland: cancer deaths and population by county",
       "NORDCAN fact sheets", "Kuitunen and others, Cancer Medicine 2026, doi 10.1002/cam4.71920",
       "Regionala cancercentrum i samverkan, SVF annual report 2025", "Kansallinen syöpästrategia 2026–2035 and its roadmap 2026–2031",
       "Finnish Cancer Registry, screening pages", "AstraZeneca answer, Junction 2026 challenge channel"]
for k, t in enumerate(src):
    text(s, 80 + (k // 4) * 730, 240 + (k % 4) * 70, 700, 60, t, 18, INK)
text(s, 80, 820, 1440, 22, "The app lists every source with its link in the view \"Sources\".", 13, MUTED)

p.save(OUT)
print(OUT, N[0], "slides")
