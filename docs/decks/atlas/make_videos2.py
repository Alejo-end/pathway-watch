"""Four more loops for the Cancer Care Atlas deck. Each opens on its finished picture, for the PDF export.

count.mp4    84 days, counted up on the purple plate
dots.mp4     21 of 21 Swedish regions publish time to treatment, 0 of 22 Finnish counties do
pathway.mp4  the four steps of the care pathway, each one a question for the open data
meter.mp4    bowel screening attendance in Satakunta fills to 72.6%, the gap to 80% becomes 1,340 tests

uv run --with pillow python make_videos2.py <font dir with IBMPlexSans.ttf>
"""
import os, subprocess, sys, tempfile, math
from PIL import Image, ImageDraw, ImageFont

FONTS = sys.argv[1]
HERE = os.path.dirname(os.path.abspath(__file__))
FPS, SS = 30, 2


def font(size, weight="SemiBold"):
    f = ImageFont.truetype(os.path.join(FONTS, "IBMPlexSans.ttf"), int(size * SS))
    try: f.set_variation_by_name(weight)
    except Exception: pass
    return f


def hexc(h, a=255): h = h.lstrip("#"); return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4)) + (a,)
def ease(t): t = min(1, max(0, t)); return 1 - (1 - t) ** 3
def inout(t): t = min(1, max(0, t)); return 4 * t ** 3 if t < .5 else 1 - (-2 * t + 2) ** 3 / 2


PURPLE, LIME, GOLD, MULB, LBLUE = hexc("#3c1053"), hexc("#c4d600"), hexc("#f0ab00"), hexc("#830051"), hexc("#68d2df")
PINK_INK, PMUTED, PLINE = hexc("#f7f0f8"), hexc("#cdbad5"), hexc("#6e4c82")
BG, INK, MUTED, LINE, TEAL, BELOW = hexc("#f5f2f5"), hexc("#231a26"), hexc("#5d5262"), hexc("#e4dce5"), hexc("#00728f"), hexc("#a86400")


def canvas(w, h, bg): im = Image.new("RGBA", (w * SS, h * SS), bg); return im, ImageDraw.Draw(im)
def done(im, w, h): return im.resize((w, h), Image.LANCZOS)
def s(v): return int(v * SS)


def encode(frames, name, final_first=True, hold=2.5):
    """frames: a list of images that ends on the finished picture."""
    seq = ([frames[-1]] * int(hold * FPS) if final_first else []) + frames + [frames[-1]] * int(hold * FPS)
    with tempfile.TemporaryDirectory() as tmp:
        cache = {}
        for i, im in enumerate(seq):
            if id(im) not in cache: cache[id(im)] = im.convert("RGB")
            cache[id(im)].save(os.path.join(tmp, f"{i:05d}.png"), compress_level=1)
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-framerate", str(FPS), "-i", os.path.join(tmp, "%05d.png"),
                        "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "19", "-movflags", "+faststart",
                        os.path.join(HERE, name + ".mp4")], check=True)
    seq[0].convert("RGB").save(os.path.join(HERE, name + "_poster.png"))


# ---- count: 84 days ----
W, H = 900, 420
def count_frame(t):
    im, d = canvas(W, H, PURPLE)
    n = round(84 * ease(t))
    d.text((s(0), s(-30)), f"{n}", font=font(300, "Bold"), fill=LIME)
    x = d.textlength(f"{84}", font=font(300, "Bold")) / SS
    d.text((s(x + 24), s(190)), "days", font=font(72, "SemiBold"), fill=PINK_INK)
    return done(im, W, H)
fr = [count_frame((k + 1) / (1.6 * FPS)) for k in range(int(1.6 * FPS))]
fade = [Image.blend(count_frame(1), count_frame(0), (k + 1) / (.3 * FPS)) for k in range(int(.3 * FPS))]
encode(fade + fr, "count", hold=4.0)   # a longer still on 84, so a thumbnail or PDF frame shows the number

# ---- dots: Sweden against Finland ----
W, H = 1440, 400
def dots_frame(t):
    im, d = canvas(W, H, BG)
    rows = [("Sweden", "21 regions", 21, 21, TEAL, 70), ("Finland", "22 counties", 22, 0, BELOW, 250)]
    for name, sub, n, filled, col, y in rows:
        d.text((s(0), s(y - 6)), name, font=font(40, "Bold"), fill=INK)
        d.text((s(0), s(y + 46)), sub, font=font(22, "Regular"), fill=MUTED)
        for i in range(n):
            cx, cy, r = 300 + i * 40, y + 34, 15
            k = ease(t * (n + 6) / 6 - i / 6)
            if i < filled:
                rr = r * (0.3 + 0.7 * k)
                d.ellipse((s(cx - rr), s(cy - rr), s(cx + rr), s(cy + rr)), fill=col[:3] + (int(255 * k),))
            else:
                d.ellipse((s(cx - r), s(cy - r), s(cx + r), s(cy + r)), outline=hexc("#b6a9b9"), width=s(2.5))
        label = f"{filled} of {n}"
        d.text((s(1440), s(y + 4)), label, font=font(44, "Bold"), fill=col, anchor="ra")
    return done(im, W, H)
fr = [dots_frame((k + 1) / (2.2 * FPS)) for k in range(int(2.2 * FPS))]
fade = [Image.blend(dots_frame(1), dots_frame(0), (k + 1) / (.3 * FPS)) for k in range(int(.3 * FPS))]
encode(fade + fr, "dots")

# ---- pathway: four steps, four questions ----
W, H = 1440, 380
STEPS = ["Detection", "Referral", "Diagnosis", "Treatment"]
def path_frame(t):
    im, d = canvas(W, H, PURPLE)
    xs = [180 + i * 360 for i in range(4)]; y = 150
    d.line((s(xs[0]), s(y), s(xs[-1]), s(y)), fill=PLINE, width=s(6))
    p = inout(t)
    xp = xs[0] + (xs[-1] - xs[0]) * p
    d.line((s(xs[0]), s(y), s(xp), s(y)), fill=LIME, width=s(6))
    for i, x in enumerate(xs):
        reached = xp >= x - 1
        k = ease((xp - x) / 120 + 1) if reached else 0
        d.ellipse((s(x - 58), s(y - 58), s(x + 58), s(y + 58)), fill=PURPLE, outline=LIME if reached else PLINE, width=s(5))
        if reached:
            d.text((s(x), s(y)), "?", font=font(64, "Bold"), fill=LIME[:3] + (int(255 * k),), anchor="mm")
        d.text((s(x), s(y + 100)), STEPS[i], font=font(30, "SemiBold"), fill=PINK_INK if reached else PMUTED, anchor="mm")
    # the travelling pulse
    if p < 1:
        d.ellipse((s(xp - 14), s(y - 14), s(xp + 14), s(y + 14)), fill=LIME)
    return done(im, W, H)
fr = [path_frame((k + 1) / (3.0 * FPS)) for k in range(int(3.0 * FPS))]
fade = [Image.blend(path_frame(1), path_frame(0), (k + 1) / (.3 * FPS)) for k in range(int(.3 * FPS))]
encode(fade + fr, "pathway")

# ---- meter: 72.6% to 80% ----
W, H = 1440, 300
def meter_frame(t, gap):
    im, d = canvas(W, H, BG)
    X0, X1, y = 0, 1440, 120
    sc = lambda v: X0 + (X1 - X0) * v / 100
    d.rounded_rectangle((s(X0), s(y), s(X1), s(y + 40)), radius=s(20), fill=LINE)
    v = 72.6 * ease(t)
    d.rounded_rectangle((s(X0), s(y), s(sc(v)), s(y + 40)), radius=s(20), fill=GOLD)
    if gap > 0:
        a = int(255 * gap)
        d.rectangle((s(sc(72.6)), s(y), s(sc(80)), s(y + 40)), fill=MULB[:3] + (a,))
        d.text((s((sc(72.6) + sc(80)) / 2), s(y + 80)), "+1,340 tests", font=font(34, "Bold"), fill=MULB[:3] + (a,), anchor="mm")
    d.line((s(sc(80)), s(y - 26), s(sc(80)), s(y + 66)), fill=MULB, width=s(4))
    d.text((s(sc(80)), s(y - 52)), "Target 80%", font=font(24, "SemiBold"), fill=MULB, anchor="mm")
    d.text((s(min(sc(v), sc(66))), s(y - 52)), f"{v:.1f}%", font=font(30, "Bold"), fill=BELOW, anchor="mm")
    return done(im, W, H)
fr = [meter_frame((k + 1) / (2.0 * FPS), 0) for k in range(int(2.0 * FPS))]
fr += [meter_frame(1, (k + 1) / (.6 * FPS)) for k in range(int(.6 * FPS))]
fade = [Image.blend(meter_frame(1, 1), meter_frame(0, 0), (k + 1) / (.3 * FPS)) for k in range(int(.3 * FPS))]
encode(fade + fr, "meter")
print("done")
