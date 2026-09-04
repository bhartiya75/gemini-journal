"""Render the LinkedIn card (1200x627) and a square variant for the feed post.

Style matches the operator's existing LinkedIn artwork: deep navy ground,
white display type, warm gold accent and rule, quiet constellation texture.
"""

from __future__ import annotations

import math
import random
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont

OUT = Path(__file__).parent
NAVY = (13, 18, 36)
NAVY_2 = (22, 28, 54)
WHITE = (245, 246, 250)
MUTED = (168, 176, 196)
GOLD = (246, 217, 138)
INDIGO = (129, 140, 248)
TEAL = (94, 210, 190)

FONT_BOLD = "/System/Library/Fonts/Supplemental/Arial Bold.ttf"
FONT_REG = "/System/Library/Fonts/Supplemental/Arial.ttf"


def font(path: str, size: int) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(path, size)


def background(w: int, h: int, seed: int = 7) -> Image.Image:
    img = Image.new("RGB", (w, h), NAVY)
    d = ImageDraw.Draw(img)
    # vertical gradient
    for y in range(h):
        t = y / h
        c = tuple(int(NAVY[i] * (1 - t) + NAVY_2[i] * t) for i in range(3))
        d.line([(0, y), (w, y)], fill=c)
    # soft glow top-right
    glow = Image.new("RGB", (w, h), (0, 0, 0))
    gd = ImageDraw.Draw(glow)
    gd.ellipse([w * 0.55, -h * 0.5, w * 1.25, h * 0.55], fill=(52, 46, 110))
    glow = glow.filter(ImageFilter.GaussianBlur(160))
    img = Image.blend(img, Image.composite(glow, img, glow.convert("L").point(lambda v: min(255, v * 3))), 0.55)
    d = ImageDraw.Draw(img)
    # constellation texture
    rnd = random.Random(seed)
    pts = [(rnd.uniform(0, w), rnd.uniform(0, h)) for _ in range(90)]
    for x, y in pts:
        r = rnd.choice([1, 1, 1, 2])
        d.ellipse([x - r, y - r, x + r, y + r], fill=(70, 78, 110))
    for i, (x1, y1) in enumerate(pts):
        for x2, y2 in pts[i + 1 :]:
            if math.dist((x1, y1), (x2, y2)) < 95:
                d.line([(x1, y1), (x2, y2)], fill=(38, 44, 72), width=1)
    return img


def chip(d: ImageDraw.ImageDraw, x: int, y: int, text: str, f: ImageFont.FreeTypeFont, color) -> int:
    pad_x, pad_y = 16, 9
    tw = d.textlength(text, font=f)
    box = [x, y, x + tw + pad_x * 2, y + f.size + pad_y * 2]
    d.rounded_rectangle(box, radius=999, outline=color, width=2, fill=(int(color[0] * 0.12), int(color[1] * 0.12), int(color[2] * 0.12) + 20))
    d.text((x + pad_x, y + pad_y - 1), text, font=f, fill=color)
    return int(box[2]) + 12


def reflections_panel(img: Image.Image, x: int, y: int, w: int, h: int) -> None:
    """A miniature of the app's Reflections card — the feature that sells it."""
    d = ImageDraw.Draw(img)
    d.rounded_rectangle([x, y, x + w, y + h], radius=18, fill=(24, 30, 58), outline=(60, 68, 104), width=2)
    f_t = font(FONT_BOLD, 22)
    f_s = font(FONT_REG, 17)
    f_l = font(FONT_BOLD, 15)
    d.text((x + 22, y + 18), "Reflections", font=f_t, fill=WHITE)
    d.text((x + 22 + d.textlength("Reflections ", font=f_t), y + 22), "— your patterns, noticed", font=f_s, fill=MUTED)
    cy = y + 66
    for label, note in [
        ("Rest & Recovery", "sleep keeps slipping after big pushes"),
        ("Work & Productivity", "finishing what you postponed"),
        ("Stress & Pressure", "deadlines circling at night"),
    ]:
        nx = chip(d, x + 22, cy, label, f_l, INDIGO)
        d.text((nx + 4, cy + 8), note, font=f_s, fill=MUTED)
        cy += 44
    cy += 6
    d.text((x + 22, cy), "Mood trend", font=f_l, fill=GOLD)
    d.text((x + 22, cy + 22), "relief → renewed pressure, over the week", font=f_s, fill=WHITE)
    cy += 62
    d.rounded_rectangle([x + 22, cy, x + w - 22, cy + 74], radius=12, fill=(38, 40, 86))
    d.text((x + 36, cy + 12), "Insight", font=f_l, fill=GOLD)
    d.text((x + 36, cy + 34), "Periods of relief are brief before new pressures", font=f_s, fill=WHITE)
    d.text((x + 36, cy + 54), "emerge — are you allowing full recovery?", font=f_s, fill=WHITE)


def card_wide() -> Path:
    w, h = 1200, 627
    img = background(w, h)
    d = ImageDraw.Draw(img)
    f_kicker = font(FONT_BOLD, 17)
    f_title = font(FONT_BOLD, 60)
    f_sub = font(FONT_REG, 25)
    f_chip = font(FONT_BOLD, 15)
    f_tag = font(FONT_BOLD, 19)

    d.text((70, 60), "GOOGLE CLOUD GEN AI ACADEMY — APAC  ·  IDEATHON CHALLENGE", font=f_kicker, fill=GOLD)
    d.text((70, 104), "Personal Gemini", font=f_title, fill=WHITE)
    d.text((70, 170), "Journal", font=f_title, fill=WHITE)
    d.line([(70, 252), (430, 252)], fill=GOLD, width=3)
    d.text((70, 272), "A security-first AI journal that", font=f_sub, fill=WHITE)
    d.text((70, 306), "reads you back to yourself.", font=f_sub, fill=WHITE)

    cx = 70
    cy = 372
    for label, color in [
        ("Firebase Auth", GOLD),
        ("Gemini", INDIGO),
        ("Firestore", TEAL),
    ]:
        cx = chip(d, cx, cy, label, f_chip, color)
    cx = 70
    cy += 46
    for label, color in [("Secret Manager", GOLD), ("Cloud Run", INDIGO)]:
        cx = chip(d, cx, cy, label, f_chip, color)

    d.text((70, h - 70), "#AccelerateAIwithCloudRun", font=f_tag, fill=GOLD)

    reflections_panel(img, 640, 92, 490, 440)
    out = OUT / "card_1200x627.png"
    img.save(out, optimize=True)
    return out


def card_square() -> Path:
    w, h = 1080, 1080
    img = background(w, h, seed=11)
    d = ImageDraw.Draw(img)
    f_kicker = font(FONT_BOLD, 19)
    f_title = font(FONT_BOLD, 74)
    f_sub = font(FONT_REG, 30)
    f_chip = font(FONT_BOLD, 18)
    f_tag = font(FONT_BOLD, 22)

    d.text((70, 70), "GEN AI ACADEMY APAC  ·  IDEATHON", font=f_kicker, fill=GOLD)
    d.text((70, 118), "Personal Gemini", font=f_title, fill=WHITE)
    d.text((70, 200), "Journal", font=f_title, fill=WHITE)
    d.line([(70, 300), (520, 300)], fill=GOLD, width=3)
    d.text((70, 324), "A security-first AI journal that", font=f_sub, fill=WHITE)
    d.text((70, 364), "reads you back to yourself.", font=f_sub, fill=WHITE)

    cx, cy = 70, 434
    for label, color in [("Firebase Auth", GOLD), ("Gemini", INDIGO), ("Firestore", TEAL)]:
        cx = chip(d, cx, cy, label, f_chip, color)
    cx, cy = 70, 490
    for label, color in [("Secret Manager", GOLD), ("Cloud Run", INDIGO)]:
        cx = chip(d, cx, cy, label, f_chip, color)

    reflections_panel(img, 70, 570, 940, 420)
    d.text((70, h - 62), "#AccelerateAIwithCloudRun", font=f_tag, fill=GOLD)
    out = OUT / "card_1080x1080.png"
    img.save(out, optimize=True)
    return out


if __name__ == "__main__":
    print(card_wide())
    print(card_square())
