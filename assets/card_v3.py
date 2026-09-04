#!/usr/bin/env python3
"""Brand card v3 — the 1080x1350 portrait system used for the one-page diagnosis cards
(SAP, Vertiv, Microsoft) and now for the Playbook series.

Geometry deliberately mirrors the canvas version used to publish, coordinate for
coordinate, so the browser port is a mechanical translation rather than a redesign.
See reference_linkedin_publishing_mechanics: file_upload cannot reach disk, so the
published card is always canvas-drawn — this script exists so Shekhar can *see* it first.

Blocks, all optional except kicker/headline:
  kicker    "THE ONE-PAGE DIAGNOSIS  ·  MICROSOFT"
  headline  ["line one", "line two"]      last line renders gold
  sub       "one muted line under the headline"
  table     {"cols": ["1998","TODAY"], "rows": [[label,a,b,delta,good], ...]}
  rows      [[LABEL, "body line 1", "body line 2"], ...]   non-numeric alternative
  panel     {"kicker":..., "big":..., "lines":[...]}       gold callout
  columns   [[TITLE, [lines...]], ...]                     three-up
  closing   {"label":..., "lines":[...]}                   full-width serif block
  footer    {"left":..., "sub":..., "right":...}

Usage:
  python3 card_v3.py part3 out.png
  python3 card_v3.py spec.json out.png
"""
import json
import os
import sys

from PIL import Image, ImageDraw, ImageFilter, ImageFont

W, H = 1080, 1350
RAIL, MX, MR = 84, 152, 70

NAVY_TOP, NAVY_BOT = (9, 30, 52), (16, 48, 79)
RAIL_TOP, RAIL_BOT = (5, 18, 33), (8, 26, 45)
GOLD, GOLD_HI = (201, 162, 39), (255, 213, 106)
INK, MUT, DIM = (245, 241, 232), (200, 196, 186), (130, 140, 150)
DIV, PANEL = (54, 74, 91), (19, 43, 72)
PANEL_INK, PANEL_SUB = (9, 30, 52), (30, 54, 84)
GOOD, BAD = (126, 200, 140), (214, 140, 120)

FONTS = {
    "georgia": ["/System/Library/Fonts/Supplemental/Georgia.ttf",
                "/System/Library/Fonts/Supplemental/Times New Roman.ttf"],
    "helv": ["/System/Library/Fonts/HelveticaNeue.ttc",
             "/System/Library/Fonts/Helvetica.ttc"],
}


def font(fam, size, bold=False):
    for p in FONTS[fam]:
        if os.path.exists(p):
            try:
                return ImageFont.truetype(p, size, index=1 if (bold and fam == "helv") else 0)
            except Exception:
                continue
    raise SystemExit("font missing: " + fam)


def vgrad(size, top, bot):
    w, h = size
    img = Image.new("RGB", size)
    d = ImageDraw.Draw(img)
    for y in range(h):
        t = y / h
        d.line([(0, y), (w, y)], fill=tuple(int(a + (b - a) * t) for a, b in zip(top, bot)))
    return img


def tracked(d, xy, text, fnt, fill, tr):
    x, y = xy
    for ch in text:
        d.text((x, y), ch, font=fnt, fill=fill)
        x += d.textlength(ch, font=fnt) + tr


def build(card, out):
    img = vgrad((W, H), NAVY_TOP, NAVY_BOT).convert("RGBA")

    glow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    ImageDraw.Draw(glow).ellipse([W - 620, -500, W + 300, 420], fill=(255, 205, 90, 56))
    img = Image.alpha_composite(img, glow.filter(ImageFilter.GaussianBlur(120)))

    img.paste(vgrad((RAIL, H), RAIL_TOP, RAIL_BOT).convert("RGBA"), (0, 0))
    d = ImageDraw.Draw(img)
    d.rectangle([RAIL, 0, RAIL + 1, H], fill=GOLD)

    # Rail identity is overridable so the same template serves the Ingentic page
    # (Engine Notes) without forking the generator.
    mono = card.get("monogram", "SB")
    d.rectangle([20, 34, 64, 78], outline=GOLD, width=2)
    f_mono = font("georgia", 24)
    d.text((20 + (44 - d.textlength(mono, font=f_mono)) / 2, 44), mono, font=f_mono, fill=GOLD_HI)

    f_name = font("helv", 20, bold=True)
    name = card.get("rail_name", "S H E K H A R   B H A R T I Y A")
    tmp = Image.new("RGBA", (int(d.textlength(name, font=f_name)) + 20, 34), (0, 0, 0, 0))
    ImageDraw.Draw(tmp).text((0, 0), name, font=f_name, fill=(232, 226, 214, 255))
    tmp = tmp.crop(tmp.getbbox()).rotate(90, expand=True)
    img.paste(tmp, ((RAIL - tmp.width) // 2, H - 150 - tmp.height), tmp)

    for i in range(3):
        d.rectangle([26 + i * 14, H - 78 - i * 9, 26 + i * 14 + 11, H - 66], fill=(201, 162, 39, 220))

    # ---------- content ----------
    y = 70
    if card.get("banner"):
        # One uniform top line — the whole event identity at the largest size that
        # fits the content width, instead of the small kicker + large firm split.
        text = card["banner"].upper()
        for size in (40, 36, 34, 32, 30, 28, 26):
            f_ban = font("helv", size, bold=True)
            tr = size * 0.07
            w = sum(d.textlength(ch, font=f_ban) for ch in text) + tr * max(0, len(text) - 1)
            if w <= (W - MR - MX):
                break
        tracked(d, (MX, y - 6), text, f_ban, GOLD_HI, tr)
    else:
        d.rectangle([MX, y + 8, MX + 56, y + 11], fill=GOLD)
        tracked(d, (MX + 74, y), card["kicker"].upper(), font("helv", 16, bold=True), GOLD, 3.0)

    # Firm name, set large and right-aligned on the kicker line. It reads as the subject of
    # the card rather than a tail on the series label, and it uses the dead space under the
    # glow instead of costing vertical rhythm. Shrinks to fit rather than colliding with the
    # kicker, so long names ("SINGAPORE AIRLINES") stay on one line.
    if card.get("firm") and not card.get("banner"):
        name = card["firm"].upper()
        kicker_end = MX + 74 + sum(
            d.textlength(ch, font=font("helv", 16, bold=True)) + 3.0 for ch in card["kicker"].upper()
        )
        for size in (46, 42, 38, 34, 30, 26):
            f_firm = font("helv", size, bold=True)
            tr = size * 0.06
            w = sum(d.textlength(ch, font=f_firm) for ch in name) + tr * max(0, len(name) - 1)
            if kicker_end + 40 + w <= (W - MR):
                tracked(d, (W - MR - w, y + 8 - size // 2), name, f_firm, GOLD_HI, tr)
                break

    f_head = font("georgia", 54)
    hy = y + 40
    for i, line in enumerate(card["headline"]):
        last = i == len(card["headline"]) - 1
        d.text((MX, hy), line, font=f_head, fill=GOLD_HI if last else INK)
        hy += 60
    y = hy - 60

    if card.get("sub"):
        d.text((MX, y + 76), card["sub"], font=font("helv", 20), fill=MUT)
        y = y + 76

    y += 46
    d.line([(MX, y), (W - MR, y)], fill=DIV, width=1)

    if card.get("table"):
        t = card["table"]
        f_col = font("helv", 16, bold=True)
        d.text((MX + 330, y + 12), t["cols"][0], font=f_col, fill=DIM)
        d.text((MX + 520, y + 12), t["cols"][1], font=f_col, fill=DIM)
        ry = y + 40
        for lab, a, b, delta, good in t["rows"]:
            d.text((MX, ry + 10), lab, font=font("helv", 20), fill=INK)
            f_num = font("georgia", 32)
            d.text((MX + 330, ry + 2), a, font=f_num, fill=MUT)
            d.text((MX + 520, ry + 2), b, font=f_num, fill=GOLD_HI if good else INK)
            f_delta = font("helv", 18, bold=True)
            # right-align the tag to the margin; shrink if it would collide with the value column
            dw = d.textlength(delta, font=f_delta)
            if dw > (W - MR) - (MX + 620):
                f_delta = font("helv", 15, bold=True); dw = d.textlength(delta, font=f_delta)
            d.text((W - MR - dw, ry + 11), delta, font=f_delta,
                   fill=GOOD if good else BAD)
            ry += 66
            d.line([(MX, ry - 8), (W - MR, ry - 8)], fill=DIV, width=1)
        y = ry - 8

    if card.get("rows"):
        f_lab = font("helv", 19, bold=True)
        f_b1 = font("helv", 21)
        for row in card["rows"]:
            label, lines = row[0], row[1:]
            tracked(d, (MX, y + 38), label.upper(), f_lab, GOLD_HI, 2.0)
            by = y + 26
            for j, ln in enumerate(lines):
                d.text((MX + 250, by), ln, font=f_b1, fill=INK if j == 0 else MUT)
                by += 34
            y += 132
            d.line([(MX, y), (W - MR, y)], fill=DIV, width=1)

    if card.get("panel"):
        p = card["panel"]
        iy = y + 18
        ph = 200
        d.rectangle([MX, iy, W - MR, iy + ph], fill=GOLD)
        tracked(d, (MX + 28, iy + 24), p["kicker"].upper(), font("helv", 17, bold=True), PANEL_INK, 1.5)
        d.text((MX + 28, iy + 56), p["big"], font=font("georgia", 34), fill=PANEL_INK)
        sy = iy + 116
        for ln in p.get("lines", []):
            d.text((MX + 28, sy), ln, font=font("helv", 19), fill=PANEL_SUB)
            sy += 30
        y = iy + ph

    if card.get("columns"):
        ay = y + 40
        tracked(d, (MX, ay), card.get("columns_label", "").upper(),
                font("helv", 17, bold=True), GOLD, 1.5)
        cw = (W - MR - MX) // 3
        # Columns give up height when an equation band follows them, so the band sits in
        # the gap above the footer rather than pushing the layout past it.
        cy, chh = ay + 34, (200 if card.get("equation") else 250)
        for i, (title, lines) in enumerate(card["columns"]):
            cx = MX + i * cw
            d.rectangle([cx, cy, cx + cw - 18, cy + chh], fill=PANEL)
            d.rectangle([cx, cy, cx + 2, cy + chh], fill=GOLD_HI)
            d.text((cx + 16, cy + 18), title, font=font("helv", 18, bold=True), fill=GOLD_HI)
            ly = cy + 56
            for ln in lines:
                d.text((cx + 16, ly), ln, font=font("helv", 15), fill=MUT)
                ly += 26
        y = cy + chh

    if card.get("scoreboard"):
        # Ten-row corpus roll-up: firm · best period · one-line verdict. Compact
        # 72px pitch so ten rows + a closing thesis fit above the footer.
        f_firm = font("helv", 20, bold=True)
        f_per = font("georgia", 20)
        f_verd = font("helv", 15)
        for firm, period, verdict in card["scoreboard"]:
            d.text((MX, y + 12), firm, font=f_firm, fill=INK)
            pw = d.textlength(period, font=f_per)
            d.text((W - MR - pw, y + 12), period, font=f_per, fill=GOLD_HI)
            d.text((MX, y + 38), verdict, font=f_verd, fill=MUT)
            y += 64
            d.line([(MX, y), (W - MR, y)], fill=DIV, width=1)

    if card.get("closing"):
        c = card["closing"]
        ay = y + 50
        cy, chh = ay, 225
        d.rectangle([MX, cy, W - MR, cy + chh], fill=PANEL)
        d.rectangle([MX, cy, MX + 3, cy + chh], fill=GOLD_HI)
        tracked(d, (MX + 26, cy + 30), c["label"].upper(), font("helv", 17, bold=True), GOLD, 1.5)
        ly = cy + 84
        for ln in c["lines"]:
            d.text((MX + 26, ly), ln, font=font("georgia", 32), fill=INK)
            ly += 44
        y = cy + chh

    f = card.get("footer", {})
    # The Transformation Equation band. Sits in the space above the footer, so it does
    # not push the three-column block around. Published only when the fit is honest —
    # see PUBLICATION-GATE: R2 above 0.90 on a short series is overfit and is withheld.
    if card.get("equation"):
        e = card["equation"]
        ey = y + 34
        d.line([(MX, ey), (W - MR, ey)], fill=GOLD, width=2)
        tracked(d, (MX, ey + 16), e.get("label", "The Transformation Equation").upper(),
                font("helv", 15, bold=True), GOLD, 1.5)
        f_stat = font("helv", 14)
        stat = e.get("stat", "")
        if stat:
            d.text((W - MR - d.textlength(stat, font=f_stat), ey + 17), stat, font=f_stat, fill=DIM)
        eyy = ey + 44
        for ln in e.get("lines", []):
            d.text((MX, eyy), ln, font=font("georgia", 20), fill=INK)
            eyy += 28
        if e.get("read"):
            d.text((MX, eyy + 4), e["read"], font=font("helv", 15), fill=MUT)

    fy = H - 98
    d.line([(MX, fy), (W - MR, fy)], fill=DIV, width=1)
    d.text((MX, fy + 18), f.get("left", ""), font=font("helv", 17, bold=True), fill=GOLD)
    if f.get("sub"):
        d.text((MX, fy + 44), f["sub"], font=font("helv", 15), fill=DIM)
    right = f.get("right", "linkedin.com/in/bshekhar")
    f_r = font("helv", 15)
    d.text((W - MR - d.textlength(right, font=f_r), fy + 44), right, font=f_r, fill=MUT)

    img.convert("RGB").save(out, "PNG")
    print("saved", out, "| content bottom y =", y, "| footer rule y =", fy)


PART3 = {
    "kicker": "The Autonomous Enterprise Playbook  ·  Part 3",
    "headline": ["You cannot automate", "what you cannot see."],
    "sub": "Process mining 101 for executives.",
    "rows": [
        ["Variants", "You designed one process.", "The system runs several hundred versions of it."],
        ["Rework", "Nine changes to one purchase order.", "One broken decision, repeated."],
        ["Waiting", "Most cycle time is not work.", "It is a document sitting in a queue."],
    ],
    "panel": {
        "kicker": "The part every programme gets wrong",
        "big": "Mine first. Then automate.",
        "lines": ["Automate a process you have not mined and you scale the rework with it.",
                  "Faster, cheaper, and still wrong."],
    },
    "closing": {
        "label": "The one question",
        "lines": ["Do you have the event log,", "and has anyone actually looked at it?"],
    },
    "footer": {
        "left": "The Autonomous Enterprise Playbook  ·  Part 3",
        "sub": "Part 4: where does AI actually show up in the P&L?",
        "right": "linkedin.com/in/bshekhar",
    },
}

SAMPLES = {"part3": PART3}

if __name__ == "__main__":
    src, out = sys.argv[1], sys.argv[2]
    build(SAMPLES.get(src) or json.load(open(src)), out)
