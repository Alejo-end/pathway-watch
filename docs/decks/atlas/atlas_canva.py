"""Cancer Care Atlas, the AstraZeneca entry, as a PowerPoint file for Canva.

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
OUT = os.path.join(HERE, "Cancer Care Atlas (Canva).pptx")


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
N = [0]; TOTAL = 9


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


# 1 Title -------------------------------------------------------------------------------------------
s = new(PURPLE)
bar(s, 0, 0, 1600, 6, LIME)
pic(s, A("brandmark.png"), 90, 110, h=64)
chip(s, 172, 126, "AstraZeneca · Equal Care Across Finland", PLATE_INK, c("#4a1f5e"))
text(s, 90, 205, 860, 240, ["Cancer", "Care Atlas"], 92, PLATE_INK, True, font=DISPLAY)
text(s, 90, 470, 760, 120, "Where cancer patients in a county fall behind, and what the county can start next month.", 28, PLATE_INK)
x = 90
for lab in ("Open data only", "Every number has a source", "22 counties"):
    x += chip(s, x, 610, lab, c("#26092f"), LIME) + 10
text(s, 90, 790, 700, 26, "Team Kindergarten Engineering · Junction 2026", 16, PLATE_MUTED)
rect(s, 90, 690, 236, 70, fill=SURF, line=None, radius=12)
pic(s, A("astrazeneca.png"), 108, 700, 200, 50)
text(s, 340, 690, 400, 70, "Challenge partner", 14, PLATE_MUTED, anchor=MSO_ANCHOR.MIDDLE)
s.shapes.add_movie(os.path.join(HERE, "map.mp4"), px(980), px(60), px(760 * 760 / 1120), px(760),
                   poster_frame_image=os.path.join(HERE, "map_poster.png"), mime_type="video/mp4")
legend(s, 1040, 836)

# 2 The problem -------------------------------------------------------------------------------------
s = new(); header(s, "The problem", "Finland cannot see where its cancer patients wait.")
cards = [("Sweden", "21 of 21", "Swedish regions report the share of patients who start treatment within the target time. In 2025 it was 47% against a target of 80%.", ABOVE, INK),
         ("Finland", "0 of 22", "Finnish wellbeing services counties have that number in any public source.", BELOW, BELOW),
         ("One Finnish lymphoma study", "127 vs 76 days", "Median time from first symptoms to treatment: first contact at a public health centre against private or occupational care. 48 and 39 of the study's 160 patients. The public group was older.", BELOW, BELOW)]
for k, (lab, val, note, acc, vc) in enumerate(cards):
    kpi(s, 80 + k * 488, 230, 464, 330, lab, val, note, acc, vc)
text(s, 80, 610, 1440, 100, "So a county leader cannot tell which step of the pathway to fix. Cancer Care Atlas shows what the open data can say, says what it cannot, and names the first step that a county can take itself.", 22, INK)
text(s, 80, 790, 1440, 22, "Sources: Regionala cancercentrum i samverkan, annual report 2025. Kuitunen and others, Cancer Medicine 2026.", 13, MUTED)

# 3 The finding -------------------------------------------------------------------------------------
s = new(); header(s, "Insight 1 of 2 · The gap", "Bowel cancer in Satakunta: 4 points below Finland.")
rect(s, 80, 220, 480, 610, fill=PURPLE, line=None, radius=12)
text(s, 104, 236, 440, 44, "Five-year relative survival against Finland, bowel cancer, 2024", 14, PLATE_INK, True)
s.shapes.add_movie(os.path.join(HERE, "map.mp4"), px(80 + (480 - 340) / 2), px(282), px(340), px(340 * 1120 / 760),
                   poster_frame_image=os.path.join(HERE, "map_poster.png"), mime_type="video/mp4")
legend(s, 115, 790)
kp = [("Satakunta, 2024", "64%", "Five-year relative survival", MULBERRY, INK),
      ("Finland, 2024", "68%", "Five-year relative survival", LINE2, INK),
      ("Gap to Finland", "−4 points", "Below Finland in 6 of 6 published years", BELOW, BELOW),
      ("Our rough 95% interval", "−6.3 to −1.7", "Excludes zero, also with the stricter limit for 22 counties", BELOW, BELOW)]
for k, (lab, val, note, acc, vc) in enumerate(kp):
    kpi(s, 584 + (k % 2) * 474, 220 + (k // 2) * 196, 462, 180, lab, val, note, acc, vc)
rect(s, 584, 612, 936, 218)
pts = [("1", "Survival is 64% against 68%, from about 1,870 patients. The interval is our estimate, and the true one is wider."),
       ("2", "Goal 3, cancer deaths: 79 bowel cancer deaths a year, SMR 115 (95% interval 101 to 131). 100 is what the age structure predicts."),
       ("3", "The open data cannot tell which step of the pathway the gap comes from: detection, referral, diagnosis or treatment.")]
for k, (n, t) in enumerate(pts):
    text(s, 608, 630 + k * 64, 30, 56, n, 20, MULBERRY, True, font=DISPLAY)
    text(s, 640, 632 + k * 64, 860, 60, t, 15.5, INK)

# 4 Where the days go -------------------------------------------------------------------------------
s = new(); header(s, "Insight 2 of 2 · Where on the pathway", "The public route ends 84 days later.", "Most of those days pass before the hospital.")
rect(s, 80, 230, 1440, 1440 * 450 / 1600 + 20)
s.shapes.add_movie(os.path.join(HERE, "days.mp4"), px(90), px(240), px(1420), px(1420 * 450 / 1600),
                   poster_frame_image=os.path.join(HERE, "days_poster.png"), mime_type="video/mp4")
stats = [("30 days", "before the first contact"), ("40 days", "in primary care, from first contact to referral"), ("14 days", "in the hospital, from referral to treatment")]
for k, (v, t) in enumerate(stats):
    x = 80 + k * 488
    rect(s, x, 670, 464, 110, fill=CHIP, line=None)
    text(s, x + 24, 684, 200, 50, v, 34, MULBERRY, True, font=DISPLAY)
    text(s, x + 24, 734, 420, 40, t, 15, INK)
text(s, 80, 800, 1440, 40, "One study of one lymphoma type: 87 of its 160 patients, copied from figure 1 of Kuitunen and others, Cancer Medicine 2026. The figure is close to the paper's means (201 and 126 days). It shows where days add up in that study, not in Satakunta.", 12.5, MUTED)

# 5 First step ---------------------------------------------------------------------------------------
s = new(); header(s, "Action 1 of 2 · The first step", "A step that one health centre can start next month.")
rect(s, 80, 220, 960, 610)
chip(s, 104, 240, "Team proposal: least-regret pathway audit", MULBERRY, CHIP)
steps = [("Start locally", "Take last year's patients with this cancer from the hospital records. Count the median days from first contact to referral, to diagnosis and to treatment, per health centre with at least 20 patients and for the smaller centres pooled."),
         ("Protocol before any change of care", "In 90 days: name a sponsor and a clinical lead, agree the data route with the data protection officer, take the dates of each step for last year's patients, and choose the measure for the slowest step."),
         ("Success is", "A baseline of the median days in each step, with at least 95% of the dates present, and a written choice of measure: 1.3.2 if patients come late, 2.5.2 if the delay is before referral, 3.1.2 if it is in diagnosis or treatment.")]
for k, (h, t) in enumerate(steps):
    y = 296 + k * 176
    rect(s, 104, y, 40, 40, fill=MULBERRY, line=None, shape=MSO_SHAPE.OVAL)
    text(s, 104, y, 40, 40, str(k + 1), 18, SURF, True, PP_ALIGN.CENTER, MSO_ANCHOR.MIDDLE, font=DISPLAY)
    text(s, 164, y + 2, 850, 30, h, 20, INK, True, font=DISPLAY)
    text(s, 164, y + 36, 850, 120, t, 15.5, MUTED)
rect(s, 1064, 220, 456, 610, fill=PURPLE, line=None, radius=12)
text(s, 1090, 244, 400, 22, "WHO ACTS", 13, LIME, True)
text(s, 1090, 270, 400, 60, "County cancer lead, with the primary care lead and the hospital quality lead.", 17, PLATE_INK)
text(s, 1090, 360, 400, 22, "WHY HERE", 13, LIME, True)
text(s, 1090, 386, 400, 120, "Survival is below the national value, and the data cannot tell which step. A measure chosen before the audit would be a guess.", 17, PLATE_INK)
text(s, 1090, 530, 400, 22, "IN SATAKUNTA", 13, LIME, True)
text(s, 1090, 556, 400, 60, "About 187 new bowel cancer cases and 79 deaths a year.", 17, PLATE_INK)
text(s, 1090, 760, 400, 50, "The audit chooses the roadmap measure. The data do not.", 14, PLATE_MUTED)

# 6 Reminder campaign -------------------------------------------------------------------------------
s = new(); header(s, "Action 2 of 2 · A reminder campaign", "Three yes or no rules decide who gets a reminder.")
kp = [("Satakunta, 2024", "72.6%", "Attendance in the public bowel screening programme. Finland: 73.5%", BELOW, BELOW),
      ("Target", "80%", "In every county, set by the national cancer strategy", LINE2, INK),
      ("No test in the programme", "about 4,950", "Of about 18,060 invited", MULBERRY, INK),
      ("To reach the target", "about 1,340", "More tests in the programme", MULBERRY, MULBERRY)]
for k, (lab, val, note, acc, vc) in enumerate(kp):
    kpi(s, 80 + k * 362, 220, 346, 190, lab, val, note, acc, vc)
# attendance meter
rect(s, 80, 432, 1440, 64)
text(s, 104, 432, 200, 64, "Attendance", 14, MUTED, True, anchor=MSO_ANCHOR.MIDDLE)
X, Wm = 260, 1200
bar(s, X, 456, Wm, 16, LINE)
bar(s, X, 456, Wm * 0.726, 16, GOLD)
bar(s, X + Wm * 0.80 - 1.5, 446, 3, 36, MULBERRY)
text(s, X + Wm * 0.726 - 70, 474, 140, 20, "72.6%", 12.5, BELOW, True, PP_ALIGN.CENTER)
text(s, X + Wm * 0.80 - 70, 474, 140, 20, "target 80%", 12.5, MULBERRY, True, PP_ALIGN.CENTER)
rect(s, 80, 516, 940, 314)
text(s, 104, 532, 600, 24, "Who is in the campaign: all three must be true", 15, INK, True)
rules = [("Rule 1", "The person is in the age and sex group of the national programme.", "Population register"),
         ("Rule 2", "The person lives in the county.", "Population register"),
         ("Rule 3", "The programme invited the person in this round, and the person has no test in the programme on the reply date.", "County's screening provider")]
for k, (r, t, src) in enumerate(rules):
    y = 570 + k * 82
    text(s, 104, y, 80, 24, r, 14.5, MULBERRY, True)
    text(s, 190, y, 560, 70, t, 14.5, INK)
    text(s, 770, y, 230, 50, src, 13, MUTED)
    if k < 2: hline(s, 104, y + 74, 892, LINE)
rect(s, 1044, 516, 476, 314, fill=BELOW_BG, line=None)
text(s, 1068, 534, 430, 24, "No diagnosis, no income, no language.", 16, BELOW, True)
text(s, 1068, 566, 430, 140, "The rules use the programme's own records. A test in private or occupational care is not counted, so some of these people have a recent test.", 15, INK)
text(s, 1068, 700, 430, 110, "Before the letters go out, ask the endoscopy unit how many more colonoscopies it can do. A positive stool test needs one.", 15, INK)

# 7 Trust -------------------------------------------------------------------------------------------
s = new(); header(s, "Data quality and transparency", "Every number names its source, and code checks it.")
items = [("Open data only", "THL Sotkanet, Statistics Finland, NORDCAN, the national strategy and its roadmap, and published studies."),
         ("Computed or copied, and the page says which", "Code computes the county numbers. One paper figure, NORDCAN and the Swedish report are copied by hand, and tests check their sums."),
         ("Where the AI is", "A language model writes three summary sentences from code-selected public facts. It sees no patient data and cannot choose the action."),
         ("Guardrails", "Code removes a sentence with no source or an unsupported number, and the fixed template takes its place."),
         ("Chance is counted", "22 counties are compared, so about one 95% interval excludes zero by chance. A stricter limit for 22 comparisons is shown."),
         ("Limits sit next to the numbers", "The interval is our rough estimate, survival describes care up to ten years ago, and attendance counts the public programme only.")]
for k, (h, t) in enumerate(items):
    x, y = 80 + (k % 3) * 488, 230 + (k // 3) * 300
    rect(s, x, y, 464, 280)
    rect(s, x + 24, y + 24, 36, 36, fill=CHIP, line=None, radius=8)
    text(s, x + 24, y + 24, 36, 36, str(k + 1), 16, MULBERRY, True, PP_ALIGN.CENTER, MSO_ANCHOR.MIDDLE, font=DISPLAY)
    text(s, x + 24, y + 78, 420, 60, h, 19, INK, True, font=DISPLAY)
    text(s, x + 24, y + 140, 420, 130, t, 15, MUTED)

# 8 Next ---------------------------------------------------------------------------------------------
s = new(); header(s, "What comes next", "A 90-day pilot with one wellbeing services county.")
text(s, 80, 210, 1440, 70, "The county holds the dates in its own records. The tool computes the five intervals from first symptoms to treatment every quarter, for each large health centre and one pooled group of the small ones. Patient records never leave the county.", 18, INK)
phases = [("Days 1 to 30", "Team and permission", "The county names a sponsor, a clinical lead and a patient representative. Its data protection officer reviews the data route."),
          ("Days 31 to 60", "Baseline", "The dates of each step for last year's patients, per health centre and pooled."),
          ("Days 61 to 90", "Decision", "Go only if at least 95% of the dates are present, the slowest step holds at least 20 patients, and the group agrees one change with an owner.")]
for k, (d, h, t) in enumerate(phases):
    x = 80 + k * 488
    rect(s, x, 320, 464, 260, fill=PURPLE if k == 2 else SURF, line=None if k == 2 else LINE)
    text(s, x + 24, 340, 300, 22, d.upper(), 13, LIME if k == 2 else MULBERRY, True)
    text(s, x + 24, 366, 420, 40, h, 24, PLATE_INK if k == 2 else INK, True, font=DISPLAY)
    text(s, x + 24, 414, 420, 160, t, 15.5, PLATE_INK if k == 2 else MUTED)
    if k < 2:
        arrow = s.shapes.add_shape(MSO_SHAPE.CHEVRON, px(x + 468), px(436), px(16), px(28))
        arrow.fill.solid(); arrow.fill.fore_color.rgb = MULBERRY; arrow.line.fill.background()
text(s, 80, 596, 1440, 24, "Otherwise no go: fix the records first and measure again in three months.", 15, MUTED)
rect(s, 80, 640, 1440, 190, fill=SURF)
text(s, 104, 656, 600, 22, "THREE LIMITS WE SAY OUT LOUD", 13, MULBERRY, True)
lims = ["The timeline is one study of one lymphoma type, and the public group was older.",
        "Survival describes patients diagnosed up to ten years ago. The rule compares counties, not patients, so it raises a question and names no cause.",
        "The local steps and the campaign are our proposals. No county and no data protection officer reviewed them."]
for k, t in enumerate(lims):
    text(s, 104 + k * 470, 690, 440, 130, t, 15, INK)

# 9 Sources -----------------------------------------------------------------------------------------
s = new(); header(s, "Sources", "Sources behind the slides.")
src = ["THL Sotkanet, indicator 3627: five-year relative survival rate of bowel cancer patients, %",
       "Rough 95% interval of a county survival gap, computed by the app",
       "Kuitunen J and others. Socioeconomic Status and Access to Treatment in Diffuse Large B-Cell Lymphoma. Cancer Medicine 2026;15(5):e71920. https://doi.org/10.1002/cam4.71920",
       "Regionala cancercentrum i samverkan, Standardiserade vårdförlopp: annual report 2025, appendix 1 (2026-03-27)",
       "Kansallisen syöpästrategian toimeenpanon tiekartta 2026–2031",
       "Kansallinen syöpästrategia 2026–2035, goals page (Goal 3)",
       "THL Sotkanet, indicator 6103: proportion of invited to colorectal cancer screening who attended, %",
       "Finnish Cancer Registry, cancer screening pages: who is invited to each national programme",
       "Statistics Finland: cancer deaths by county and age, and population by age (Goal 3, SMR)",
       "NORDCAN fact sheets: new cases and five-year survival for Finland, Sweden and Norway",
       "AstraZeneca answer to a team question, Junction 2026 challenge channel, 14 November 2026",
       "Cancer Care Atlas proposals for a first local step and a screening campaign, written by the team"]
for k, t in enumerate(src):
    x, y = 80 + (k // 6) * 730, 220 + (k % 6) * 100
    text(s, x, y, 40, 30, f"{k + 1}.", 15, MULBERRY, True)
    text(s, x + 40, y, 660, 90, t, 14.5, INK)
text(s, 80, 820, 1440, 22, "The app lists every source with its link in the view \"Sources\".", 13, MUTED)

p.save(OUT)
print(OUT, N[0], "slides")
