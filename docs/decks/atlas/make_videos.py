"""Two short loops for the Cancer Care Atlas deck in Canva.

map.mp4: the 22 counties fill in by their bowel cancer survival gap, then Satakunta lights up.
days.mp4: the two routes into care from Kuitunen and others (Cancer Medicine 2026) grow step by step.
Both open on their finished picture, so a PDF export, which keeps the first frame, shows it.

uv run --with pillow python make_videos.py <dir with map3627.json and evidence.json> <font dir>
The JSON files are answers of the running app: /api/map/3627 and /api/evidence.
"""
import json, math, os, subprocess, sys, tempfile
from PIL import Image, ImageDraw, ImageFont

DATA, FONTS = sys.argv[1], sys.argv[2]
HERE = os.path.dirname(os.path.abspath(__file__))
GEO = os.path.join(HERE, "..", "..", "..", "pathway-watch", "web", "counties.geojson")
FPS = 30


def font(size, weight="SemiBold", name="IBMPlexSans.ttf"):
    f = ImageFont.truetype(os.path.join(FONTS, name), size)
    try: f.set_variation_by_name(weight)
    except Exception: pass
    return f


def hexc(h, a=255): h = h.lstrip("#"); return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4)) + (a,)
def ease(t): return 1 - (1 - t) ** 3
def mix(a, b, t): return tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(4))


def encode(seq, out):
    with tempfile.TemporaryDirectory() as tmp:
        cache = {}
        for i, im in enumerate(seq):
            if id(im) not in cache: cache[id(im)] = im.convert("RGB")
            cache[id(im)].save(os.path.join(tmp, f"{i:05d}.png"), compress_level=1)
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-framerate", str(FPS), "-i", os.path.join(tmp, "%05d.png"),
                        "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "19", "-movflags", "+faststart", out], check=True)


# ---------------- map ----------------
PLATE, LINE, NEAR, NODATA = hexc("#3c1053"), hexc("#6e4c82"), hexc("#594470"), hexc("#432a57")
GOLD, GOLD_SOFT, BLUE, BLUE_SOFT, LIME, INK = hexc("#f0ab00"), hexc("#b5841c"), hexc("#68d2df"), hexc("#3b7f93"), hexc("#c4d600"), hexc("#f7f0f8")
layer = json.load(open(os.path.join(DATA, "map3627.json")))["counties"]
geo = json.load(open(GEO))
MW, MH, PAD = 760, 1120, 40


def colour(d):
    if d["direction"] == "near": return NEAR
    strong = abs(d["gap"]) >= 3
    if d["direction"] == "below": return GOLD if strong else GOLD_SOFT
    return BLUE if strong else BLUE_SOFT


K = math.cos(math.radians(64.5))
polys = {}
for f in geo["features"]:
    code = f["properties"]["hyvinvointialue"]
    g = f["geometry"]; parts = g["coordinates"] if g["type"] == "MultiPolygon" else [g["coordinates"]]
    polys[code] = [[(x * K, -y) for x, y in part[0]] for part in parts]
xs = [p[0] for ps in polys.values() for r in ps for p in r]; ys = [p[1] for ps in polys.values() for r in ps for p in r]
sc = min((MW - 2 * PAD) / (max(xs) - min(xs)), (MH - 2 * PAD) / (max(ys) - min(ys)))
ox = (MW - (max(xs) - min(xs)) * sc) / 2
for code in polys:
    polys[code] = [[((x - min(xs)) * sc + ox, (y - min(ys)) * sc + PAD) for x, y in r] for r in polys[code]]


def dashed(d, ring, fill, width=2, on=7, off=6):
    for (x1, y1), (x2, y2) in zip(ring, ring[1:] + ring[:1]):
        L = math.hypot(x2 - x1, y2 - y1); t = 0.0
        while t < L:
            a, b = t / L, min(t + on, L) / L
            d.line([(x1 + (x2 - x1) * a, y1 + (y2 - y1) * a), (x1 + (x2 - x1) * b, y1 + (y2 - y1) * b)], fill=fill, width=width)
            t += on + off


SS = 2  # draw at twice the size, then shrink, for smooth edges
F_PILL, F_SUB = font(30 * SS, "Bold"), font(22 * SS, "Medium")
order = sorted([c for c in polys if c in layer], key=lambda c: -layer[c]["gap"])  # better counties first, the worst last
OTHER = [c for c in polys if c not in layer]  # no survival value: drawn as no data


def map_frame(fill_t, hi_t):
    """fill_t: 0..1 how far the counties have filled in. hi_t: 0..1 the Satakunta highlight."""
    im = Image.new("RGBA", (MW * SS, MH * SS), PLATE); d = ImageDraw.Draw(im)
    n = len(order)
    for code in OTHER:
        for ring in polys[code]: d.polygon([(x * SS, y * SS) for x, y in ring], fill=NODATA)
    for i, code in enumerate(order):
        k = ease(min(1, max(0, fill_t * (n + 4) / 5 - i / 5 * 1.0)))
        c = mix(NODATA, colour(layer[code]), k)
        for ring in polys[code]:
            pts = [(x * SS, y * SS) for x, y in ring]
            d.polygon(pts, fill=c, outline=None)
    for code in order:
        for ring in polys[code]:
            pts = [(x * SS, y * SS) for x, y in ring]
            if layer[code]["interval"]["excludes_zero"]: d.line(pts + pts[:1], fill=PLATE, width=2 * SS)
            else:
                d.line(pts + pts[:1], fill=PLATE, width=2 * SS)
                if fill_t > .95: dashed(d, pts, INK[:3] + (200,), width=2 * SS, on=6 * SS, off=5 * SS)
    if hi_t > 0:
        a = int(255 * hi_t)
        for ring in polys["06"]:
            pts = [(x * SS, y * SS) for x, y in ring]
            d.line(pts + pts[:1], fill=LIME[:3] + (a,), width=int(5 * SS), joint="curve")
        cx = sum(x for r in polys["06"] for x, _ in r) / sum(len(r) for r in polys["06"])
        cy = sum(y for r in polys["06"] for _, y in r) / sum(len(r) for r in polys["06"])
        # a pill to the left of the county, with a leader line
        px, py = 24 * SS, cy * SS - 300 * SS
        d.line([(cx * SS, cy * SS), (px + 120 * SS, py + 64 * SS)], fill=LIME[:3] + (a,), width=3 * SS)
        d.ellipse((cx * SS - 7 * SS, cy * SS - 7 * SS, cx * SS + 7 * SS, cy * SS + 7 * SS), fill=LIME[:3] + (a,))
        d.rounded_rectangle((px, py - 34 * SS, px + 300 * SS, py + 64 * SS), radius=14 * SS, fill=LIME[:3] + (a,))
        d.text((px + 18 * SS, py - 20 * SS), "Satakunta", font=F_PILL, fill=(38, 9, 47, a))
        d.text((px + 18 * SS, py + 20 * SS), "−4 points, 6 of 6 years", font=F_SUB, fill=(38, 9, 47, a))
    return im.resize((MW, MH), Image.LANCZOS)


final = map_frame(1, 1)
seq = [final] * int(2.5 * FPS)
for k in range(int(.5 * FPS)): seq.append(Image.blend(final, map_frame(0, 0), (k + 1) / (.5 * FPS)))
for k in range(int(2.6 * FPS)): seq.append(map_frame((k + 1) / (2.6 * FPS), 0))
for k in range(int(.6 * FPS)): seq.append(map_frame(1, (k + 1) / (.6 * FPS)))
seq += [final] * int(2.5 * FPS)
encode(seq, os.path.join(HERE, "map.mp4")); final.convert("RGB").save(os.path.join(HERE, "map_poster.png"))

# ---------------- days ----------------
ev = json.load(open(os.path.join(DATA, "evidence.json")))["timeline"]
steps = ev["steps"]
OWNER = {"patient": hexc("#6b5f70"), "primary care": hexc("#c98a00"), "hospital": hexc("#830051")}
W, H = 1600, 450
WHITE, TXT, MUTED, RULE = hexc("#ffffff"), hexc("#231a26"), hexc("#5d5262"), hexc("#e4dce5")
F_L, F_S, F_N, F_B, F_T = font(30, "SemiBold"), font(24, "Regular"), font(22, "SemiBold"), font(34, "Bold"), font(26, "SemiBold")
X0, X1 = 500, 1440
scale = (X1 - X0) / 207
rows = [("public", "Public health centre", f"{ev['groups']['public']['patients']} patients", 40),
        ("private", "Private or occupational care", f"{ev['groups']['private']['patients']} patients", 180)]


def days_frame(t, bracket):
    im = Image.new("RGBA", (W * SS, H * SS), WHITE); d = ImageDraw.Draw(im)
    s = lambda v: int(v * SS)
    for key, name, sub, y in rows:
        d.text((s(40), s(y + 6)), name, font=font(30 * SS, "SemiBold"), fill=TXT)
        d.text((s(40), s(y + 46)), sub, font=font(24 * SS, "Regular"), fill=MUTED)
        x, total = X0, sum(st[f"{key}_days"] for st in steps)
        cum = 0
        for st in steps:
            days = st[f"{key}_days"]
            start, end = cum / 207, (cum + days) / 207       # a share of the longest route
            cum += days
            k = min(1, max(0, (t * 207 * 1.0 - (cum - days)) / max(days, 1)))
            w = days * scale * ease(k)
            if w > 0:
                d.rectangle((s(x), s(y), s(x + w), s(y + 78)), fill=OWNER[st["owner"]])
                d.line((s(x + w), s(y), s(x + w), s(y + 78)), fill=WHITE, width=s(3))
                if days >= 15 and k > .9:
                    d.text((s(x + w / 2), s(y + 39)), str(days), font=font(22 * SS, "SemiBold"), fill=WHITE, anchor="mm")
            x += days * scale
        shown = min(total, int(round(t * 207)))
        if t > 0:
            d.text((s(X0 + min(total, t * 207) * scale + 18), s(y + 14)), f"{shown}", font=font(40 * SS, "Bold"), fill=TXT)
            d.text((s(X0 + min(total, t * 207) * scale + 18), s(y + 56)), "days", font=font(20 * SS, "Regular"), fill=MUTED)
    if bracket > 0:
        a = int(255 * bracket); col = hexc("#830051")[:3] + (a,)
        x1, x2 = X0 + 123 * scale, X0 + 207 * scale
        y = 300
        d.line((s(x1), s(y), s(x2), s(y)), fill=col, width=s(3))
        for xx in (x1, x2): d.line((s(xx), s(y - 12), s(xx), s(y + 12)), fill=col, width=s(3))
        d.text((s((x1 + x2) / 2), s(y + 40)), "+84 days on the public route", font=font(30 * SS, "Bold"), fill=col, anchor="mm")
    # legend
    lx = 40
    for lab, key in (("Before the first contact", "patient"), ("Primary care: first contact to referral", "primary care"), ("Hospital: referral to treatment", "hospital")):
        d.rectangle((s(lx), s(402), s(lx + 22), s(424)), fill=OWNER[key])
        d.text((s(lx + 32), s(400)), lab, font=font(22 * SS, "Regular"), fill=MUTED)
        lx += 40 + d.textlength(lab, font=font(22 * SS, "Regular")) / SS + 30
    return im.resize((W, H), Image.LANCZOS)


final = days_frame(1, 1)
seq = [final] * int(2.5 * FPS)
for k in range(int(.4 * FPS)): seq.append(Image.blend(final, days_frame(0, 0), (k + 1) / (.4 * FPS)))
for k in range(int(3.2 * FPS)): seq.append(days_frame((k + 1) / (3.2 * FPS), 0))
for k in range(int(.6 * FPS)): seq.append(days_frame(1, (k + 1) / (.6 * FPS)))
seq += [final] * int(2.5 * FPS)
encode(seq, os.path.join(HERE, "days.mp4")); final.convert("RGB").save(os.path.join(HERE, "days_poster.png"))
print("done")
