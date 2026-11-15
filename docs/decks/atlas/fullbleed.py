"""Put each animation on a full slide, so its colours can never differ from the slide behind it.

A video is decoded with slightly other colours than the flat slide fill, so a video placed on a coloured
slide shows a visible box. Here every video is 1920 x 1080 and carries its own slide background
(fill, top bar and panels). The PowerPoint file puts it first on the slide, under all text.

uv run --with pillow python fullbleed.py
"""
import os, subprocess
from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__))
K = 1.2  # 1600 px slide -> 1920 px video
PURPLE, LIME, BG, MULB, WHITE = "#3c1053", "#c4d600", "#f5f2f5", "#830051", "#ffffff"

# name: (source video, slide fill, top bar, panels [(x, y, w, h, fill)], video box (x, y, w, h)) in slide pixels
SLIDES = {
    "s1_map": ("map", PURPLE, LIME, [], (980, 60, 760 * 760 / 1120, 760)),
    "s2_count": ("count", PURPLE, LIME, [], (90, 200, 900, 420)),
    "s3_dots": ("dots", BG, MULB, [], (80, 270, 1440, 400)),
    "s4_map": ("map", BG, MULB, [(80, 210, 440, 610, PURPLE)], (80 + (440 - 330) / 2, 225, 330, 330 * 1120 / 760)),
    "s5_pathway": ("pathway", PURPLE, LIME, [], (80, 360, 1440, 380)),
    "s6_days": ("days", BG, MULB, [(70, 210, 1460, 1440 * 450 / 1600 + 20, WHITE)], (80, 220, 1440, 1440 * 450 / 1600)),
    "s8_meter": ("meter", BG, MULB, [], (80, 270, 1440, 300)),
}


def bg_image(fill, bar, panels):
    im = Image.new("RGB", (1920, 1080), fill); d = ImageDraw.Draw(im)
    d.rectangle((0, 0, 1920, round(6 * K)), fill=bar)
    for x, y, w, h, f in panels:
        d.rounded_rectangle((round(x * K), round(y * K), round((x + w) * K), round((y + h) * K)), radius=round(12 * K), fill=f)
    return im


for name, (src, fill, bar, panels, (x, y, w, h)) in SLIDES.items():
    bg = bg_image(fill, bar, panels)
    bgp = os.path.join(HERE, f"_bg_{name}.png"); bg.save(bgp)
    X, Y, Wv, Hv = round(x * K), round(y * K), round(w * K) // 2 * 2, round(h * K) // 2 * 2
    out = os.path.join(HERE, "full", name + ".mp4"); os.makedirs(os.path.dirname(out), exist_ok=True)
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-loop", "1", "-i", bgp, "-i", os.path.join(HERE, src + ".mp4"),
                    "-filter_complex", f"[1:v]scale={Wv}:{Hv}:flags=lanczos[v];[0:v][v]overlay={X}:{Y}:shortest=1,scale=out_color_matrix=bt709:out_range=tv,format=yuv420p",
                    "-r", "30", "-c:v", "libx264", "-crf", "18", "-colorspace", "bt709", "-color_primaries", "bt709",
                    "-color_trc", "bt709", "-movflags", "+faststart", out], check=True)
    poster = bg.copy(); poster.paste(Image.open(os.path.join(HERE, src + "_poster.png")).convert("RGB").resize((Wv, Hv), Image.LANCZOS), (X, Y))
    poster.save(os.path.join(HERE, "full", name + "_poster.png"))
    os.remove(bgp)
print("done")
