#!/usr/bin/env python3
"""Event cover in the brand-rail system (1600x838) — information-dense variant.

Left: kicker, three-line Georgia headline (last line gold), sub, four numbered
stack rows. Right: gold event panel (what, who, when, result). Footer: links.
Primitives (rail, fonts, gradient, tracking) come from card_template.py.
"""

import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter

sys.path.insert(0, str(Path(__file__).parent))
from card_template import (  # noqa: E402
    DIM, DIV, GOLD, GOLD_HI, H, INK, MR, MUT, MX, NAVY_BOT, NAVY_TOP, RAIL_BOT,
    RAIL_TOP, RAIL_W, W, font, tracked, tracked_w, vgrad,
)

PANEL_INK, PANEL_SUB = (9, 30, 52), (30, 54, 84)

# LinkedIn article covers are shown center-cropped to 16:9, so render at 1600x900
# rather than the template's 1600x838 — otherwise the rail loses ~55px on the left.
H = 900

CARD = {
    "kicker": "Google Cloud Gen AI Academy — APAC Edition  ·  Cohort 3  ·  Ideathon Challenge",
    "headline": ["Personal Gemini Journal:", "a security-first AI app,", "from Academy to Ideathon"],
    "sub": "Built for the Ideathon capstone run by Google Cloud with Hack2skill  ·  September 2026",
    "rows": [
        ["01", "Firebase Authentication", "every request carries a verified ID token"],
        ["02", "Gemini", "multi-turn journaling, structured session summaries"],
        ["03", "Cloud Firestore", "users/{uid}/… — isolation by structure, not by filter"],
        ["04", "Secret Manager + Cloud Run", "no keys in code, one container, scales to zero"],
    ],
    "panel": {
        "kicker": "The event",
        "big": "Gen AI Academy APAC · Cohort 3",
        "lines": [
            "Academy phase — Cloud Run track,",
            "codelab + quizzes: 10/10, graduated",
            "Capstone — the Ideathon Challenge:",
            "Personal Gemini Journal, live on Cloud Run",
            "Unique feature — Reflections:",
            "recurring themes · mood trend · one insight",
        ],
    },
    "links": "Live: gemini-journal-716080261877.us-east1.run.app   ·   Code: github.com/bhartiya75/gemini-journal   ·   #AccelerateAIwithCloudRun",
    "footer_right": "AI Transformation Sales and Alliance Leader, APAC",
}


def rail(img: Image.Image) -> None:
    img.paste(vgrad((RAIL_W, H), RAIL_TOP, RAIL_BOT).convert("RGBA"), (0, 0))
    d = ImageDraw.Draw(img)
    d.line([(RAIL_W, 0), (RAIL_W, H)], fill=GOLD, width=2)
    d.line([(RAIL_W + 2, 0), (RAIL_W + 2, H)], fill=(201, 162, 39, 60), width=1)
    ms, mx0, my0 = 56, (RAIL_W - 56) // 2, 46
    d.rectangle([mx0, my0, mx0 + ms, my0 + ms], outline=GOLD, width=2)
    f_mono = font("georgia", 30)
    tw = d.textlength("SB", font=f_mono)
    d.text((mx0 + (ms - tw) / 2, my0 + 9), "SB", font=f_mono, fill=GOLD_HI)
    f_name = font("helv", 23, index=1)
    name = "S H E K H A R   B H A R T I Y A"
    tmp = Image.new("RGBA", (int(f_name.size * 1.6) + 700, 40), (0, 0, 0, 0))
    ImageDraw.Draw(tmp).text((0, 0), name, font=f_name, fill=(232, 226, 214, 255))
    tmp = tmp.crop(tmp.getbbox()).rotate(90, expand=True)
    img.paste(tmp, ((RAIL_W - tmp.width) // 2, H - tmp.height - 120), tmp)
    bx, by = (RAIL_W - 44) // 2, H - 88
    for i in range(3):
        d.rectangle([bx + i * 16, by - i * 10, bx + i * 16 + 12, by + 4], fill=(201, 162, 39, 220))


def build(card: dict, out: str) -> None:
    img = vgrad((W, H), NAVY_TOP, NAVY_BOT).convert("RGBA")
    glow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    ImageDraw.Draw(glow).ellipse([W - 520, -240, W + 200, 340], fill=(255, 205, 90, 66))
    img = Image.alpha_composite(img, glow.filter(ImageFilter.GaussianBlur(110)))
    dots = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    dd = ImageDraw.Draw(dots)
    for gx in range(900, W, 44):
        for gy in range(50, H - 40, 44):
            dd.ellipse([gx - 1, gy - 1, gx + 1, gy + 1], fill=(245, 241, 232, int(5 + 16 * (gx - 860) / (W - 860))))
    img = Image.alpha_composite(img, dots)
    rail(img)
    d = ImageDraw.Draw(img)

    # event line — the first thing the eye lands on: large, bright gold, tracked;
    # the cohort/challenge tag sits under it in the quieter kicker weight
    y = 52
    event, tag = card["kicker"].split("  ·  ", 1)
    for size in (28, 26, 24, 22):
        f_event = font("helv", size, index=1)
        if tracked_w(d, event.upper(), f_event, 2.4) <= (W - MR - MX):
            break
    tracked(d, (MX, y), event.upper(), f_event, GOLD_HI, 2.4)
    y += int(f_event.size * 1.35)
    tracked(d, (MX, y), tag.upper(), font("helv", 16, index=1), GOLD, 3.2)

    # headline — three lines, last gold
    y += 38
    f_head = font("georgia", 48)
    for i, line in enumerate(card["headline"]):
        last = i == len(card["headline"]) - 1
        d.text((MX, y), line, font=f_head, fill=GOLD_HI if last else INK)
        y += int(f_head.size * 1.14)

    y += 10
    d.text((MX, y), card["sub"], font=font("helv", 20), fill=MUT)
    y += 46

    # two columns: rows (left) and event panel (right)
    col_gap = 40
    panel_w = 470
    left_w = (W - MR - MX) - panel_w - col_gap
    top = y
    d.line([(MX, top), (MX + left_w, top)], fill=DIV, width=1)
    f_num = font("georgia", 34)
    f_lab = font("helv", 22, index=1)
    f_txt = font("helv", 19)
    pitch = 86
    ry = top
    for num, label, text in card["rows"]:
        d.text((MX, ry + 18), num, font=f_num, fill=GOLD)
        d.text((MX + 74, ry + 16), label, font=f_lab, fill=INK)
        d.text((MX + 74, ry + 48), text, font=f_txt, fill=MUT)
        ry += pitch
        d.line([(MX, ry), (MX + left_w, ry)], fill=DIV, width=1)

    p = card["panel"]
    px0 = MX + left_w + col_gap
    ph = pitch * len(card["rows"])
    d.rectangle([px0, top, W - MR, top + ph], fill=GOLD)
    tracked(d, (px0 + 26, top + 22), p["kicker"].upper(), font("helv", 15, index=1), PANEL_INK, 2.0)
    for size in (30, 28, 26, 24):  # shrink until the panel headline clears the right inset
        f_big = font("georgia", size)
        if d.textlength(p["big"], font=f_big) <= (W - MR) - px0 - 52:
            break
    d.text((px0 + 26, top + 50), p["big"], font=f_big, fill=PANEL_INK)
    sy = top + 104
    for i, ln in enumerate(p["lines"]):
        strong = i % 2 == 0
        d.text((px0 + 26, sy), ln, font=font("helv", 19, index=1 if strong else 0), fill=PANEL_INK if strong else PANEL_SUB)
        sy += 30 if strong else 44

    # footer
    fy = H - 92
    d.line([(MX, fy), (W - MR, fy)], fill=DIV, width=1)
    f_foot = font("helv", 16)
    d.text((MX, fy + 18), "The Autonomous Enterprise · linkedin.com/in/bshekhar", font=f_foot, fill=DIM)
    right = card["footer_right"]
    d.text((W - MR - d.textlength(right, font=f_foot), fy + 18), right, font=f_foot, fill=MUT)
    d.text((MX, fy + 48), card["links"], font=font("helv", 15), fill=GOLD)

    img.convert("RGB").save(out, "PNG")
    print("saved", out)


if __name__ == "__main__":
    build(CARD, sys.argv[1] if len(sys.argv) > 1 else "cover_event_1600x838.png")
