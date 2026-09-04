#!/usr/bin/env python3
"""Shekhar Bhartiya brand card template v2 — 'the brand rail' system.
1600x838 navy/gold editorial cards with a left vertical brand spine.

Usage:
  python3 card_template.py sample1 out.png       # Playbook rows sample
  python3 card_template.py sample2 out.png       # Numbers sample
  python3 card_template.py JSONFILE out.png      # custom card from JSON

JSON schema:
{
  "kicker": "THE AUTONOMOUS ENTERPRISE PLAYBOOK, PART 3",
  "headline": ["Two lines of", "Georgia headline"],
  "rows": [["01", "row text"], ...],          # optional (max 4)
  "sub": ["subtitle line 1", "line 2"],       # optional
  "note": "small source/disclaimer line",     # optional
  "footer_right": "AI Transformation Sales and Alliance Leader, APAC"
}
"""
import json
import os
import sys

from PIL import Image, ImageDraw, ImageFilter, ImageFont

W, H = 1600, 838
RAIL_W = 128
NAVY_TOP, NAVY_BOT = (9, 30, 52), (16, 48, 79)
RAIL_TOP, RAIL_BOT = (5, 18, 33), (8, 26, 45)
INK = (245, 241, 232)
GOLD = (201, 162, 39)
GOLD_HI = (255, 213, 106)
MUT = (200, 196, 186)
DIM = (130, 140, 150)
DIV = (54, 74, 91)
MX = 200          # content left margin (rail + 72)
MR = 96           # right margin

FONTS = {
    "georgia": ["/System/Library/Fonts/Supplemental/Georgia.ttf",
                "/System/Library/Fonts/Supplemental/Times New Roman.ttf"],
    "helv": ["/System/Library/Fonts/HelveticaNeue.ttc",
             "/System/Library/Fonts/Helvetica.ttc"],
}

def font(fam, size, index=0):
    for p in FONTS[fam]:
        if os.path.exists(p):
            try:
                return ImageFont.truetype(p, size, index=index)
            except Exception:
                continue
    raise SystemExit("font missing: " + fam)

def vgrad(size, top, bot, diag=False):
    w, h = size
    img = Image.new("RGB", size)
    d = ImageDraw.Draw(img)
    for y in range(h):
        t = y / h
        d.line([(0, y), (w, y)], fill=tuple(int(a + (b - a) * t) for a, b in zip(top, bot)))
    return img

def tracked(draw, xy, text, fnt, fill, tr):
    x, y = xy
    for ch in text:
        draw.text((x, y), ch, font=fnt, fill=fill)
        x += draw.textlength(ch, font=fnt) + tr

def tracked_w(draw, text, fnt, tr):
    return sum(draw.textlength(c, font=fnt) for c in text) + tr * max(0, len(text) - 1)

def build(card, out):
    img = vgrad((W, H), NAVY_TOP, NAVY_BOT).convert("RGBA")

    # soft gold glow upper right
    glow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    gd = ImageDraw.Draw(glow)
    gd.ellipse([W - 520, -240, W + 200, 340], fill=(255, 205, 90, 66))
    glow = glow.filter(ImageFilter.GaussianBlur(110))
    img = Image.alpha_composite(img, glow)

    # faint dot texture, right half
    dots = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    dd = ImageDraw.Draw(dots)
    for gx in range(900, W, 44):
        for gy in range(50, H - 40, 44):
            a = int(5 + 16 * (gx - 860) / (W - 860))
            dd.ellipse([gx - 1, gy - 1, gx + 1, gy + 1], fill=(245, 241, 232, a))
    img = Image.alpha_composite(img, dots)

    # ---- brand rail ----
    rail = vgrad((RAIL_W, H), RAIL_TOP, RAIL_BOT).convert("RGBA")
    img.paste(rail, (0, 0))
    d = ImageDraw.Draw(img)
    d.line([(RAIL_W, 0), (RAIL_W, H)], fill=GOLD, width=2)          # gold hairline
    d.line([(RAIL_W + 2, 0), (RAIL_W + 2, H)], fill=(201, 162, 39, 60), width=1)

    # monogram: thin gold square + SB
    ms, mx0, my0 = 56, (RAIL_W - 56) // 2, 46
    d.rectangle([mx0, my0, mx0 + ms, my0 + ms], outline=GOLD, width=2)
    f_mono = font("georgia", 30)
    tw = d.textlength("SB", font=f_mono)
    d.text((mx0 + (ms - tw) / 2, my0 + 9), "SB", font=f_mono, fill=GOLD_HI)

    # vertical name reading bottom-to-top
    f_name = font("helv", 23, index=1)
    name = "S H E K H A R   B H A R T I Y A"
    tmp = Image.new("RGBA", (int(f_name.size * 1.6) + 700, 40), (0, 0, 0, 0))
    td = ImageDraw.Draw(tmp)
    td.text((0, 0), name, font=f_name, fill=(232, 226, 214, 255))
    tmp = tmp.crop(tmp.getbbox()).rotate(90, expand=True)
    img.paste(tmp, ((RAIL_W - tmp.width) // 2, H - tmp.height - 120), tmp)

    # small gold rung glyph at rail bottom (three ascending steps = the Playbook mark)
    bx, by = (RAIL_W - 44) // 2, H - 88
    for i in range(3):
        d.rectangle([bx + i * 16, by - i * 10, bx + i * 16 + 12, by + 4], fill=(201, 162, 39, 220))

    # ---- content ----
    y = 84
    f_kick = font("helv", 16, index=1)
    tracked(d, (MX, y), card["kicker"].upper(), f_kick, GOLD, 4.0)

    y = 138
    f_head = font("georgia", 58 if len(card["headline"]) > 2 else 62)
    for line in card["headline"]:
        d.text((MX, y), line, font=f_head, fill=INK)
        y += int(f_head.size * 1.18)

    if card.get("sub"):
        y += 26
        f_sub = font("helv", 26)
        for line in card["sub"]:
            d.text((MX, y), line, font=f_sub, fill=MUT)
            y += 38

    if card.get("rows"):
        y += 40
        n_rows = len(card["rows"])
        pitch = 104 if n_rows <= 3 else 84
        f_num = font("georgia", 44 if n_rows <= 3 else 38)
        f_txt = font("helv", 26 if n_rows <= 3 else 25)
        num_w = max(tracked_w(d, r[0], f_num, 0) for r in card["rows"])
        tx = MX + max(96, int(num_w) + 44)
        for nlabel, txt in card["rows"]:
            d.line([(MX, y), (W - MR, y)], fill=DIV, width=1)
            d.text((MX, y + 20), nlabel, font=f_num, fill=GOLD)
            d.text((tx, y + (34 if n_rows <= 3 else 26)), txt, font=f_txt, fill=INK)
            y += pitch

    # footer: role only (name lives on the rail)
    fy = H - 78
    d.line([(MX, fy), (W - MR, fy)], fill=DIV, width=1)
    f_foot = font("helv", 16)
    right = card.get("footer_right", "AI Transformation Sales and Alliance Leader, APAC")
    d.text((MX, fy + 20), "The Autonomous Enterprise · linkedin.com/in/bshekhar", font=f_foot, fill=DIM)
    rw = d.textlength(right, font=f_foot)
    d.text((W - MR - rw, fy + 20), right, font=f_foot, fill=MUT)

    if card.get("note"):
        f_note = font("helv", 14)
        d.text((MX, fy + 46), card["note"], font=f_note, fill=DIM)   # bottom strip, never collides

    os.makedirs(os.path.dirname(os.path.abspath(out)), exist_ok=True)
    img.convert("RGB").save(out, "PNG")
    print("saved", out)

SAMPLES = {
    "sample1": {
        "kicker": "The Autonomous Enterprise Playbook, Part 3",
        "headline": ["Process mining 101", "for executives"],
        "sub": ["You cannot automate", "what you cannot see."],
        "rows": [
            ["01", "Your processes as they actually run, not as designed"],
            ["02", "Every deviation, delay and detour, measured"],
            ["03", "The evidence layer every agent will need"],
        ],
    },
    "sample2": {
        "kicker": "The Numbers, Decoded — Sample Edition",
        "headline": ["A record fall on", "a calm quarter"],
        "rows": [
            ["-25%", "the worst single trading day on record"],
            ["+1%", "actual revenue growth in the quarter"],
            ["-42%", "the mainframe cycle's cliff, not a collapse"],
        ],
        "note": "Reported results. Operational read, not investment advice.",
    },
}

if __name__ == "__main__":
    src, out = sys.argv[1], sys.argv[2]
    card = SAMPLES.get(src) or json.load(open(src))
    build(card, out)
