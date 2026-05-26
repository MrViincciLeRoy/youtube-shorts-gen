#!/usr/bin/env python3
import os
import sys
import random
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from moviepy.editor import AudioFileClip, VideoClip

SCREENSHOT_PATH = "assets/analytics.png"
AUDIO_PATH      = "assets/sound.mp3"
OUTPUT_PATH     = "output/short.mp4"

DURATION = 10
FPS      = 30
W, H     = 1080, 1920

FONT_BOLD = "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf"
FONT_REG  = "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf"

POLL_BG    = (230, 239, 255, 245)
POLL_BLUE  = (0,   0,   178, 255)
OPTION_BG  = (202, 221, 255, 240)


def get_font(size, bold=False):
    path = FONT_BOLD if bold else FONT_REG
    try:
        return ImageFont.truetype(path, size)
    except Exception:
        return ImageFont.load_default()


def prepare_bg(path):
    img = Image.open(path).convert("RGB")
    iw, ih = img.size
    scale = max(W / iw, H / ih)
    nw, nh = int(iw * scale), int(ih * scale)
    img = img.resize((nw, nh), Image.LANCZOS)
    x0 = (nw - W) // 2
    y0 = (nh - H) // 2
    return np.array(img.crop((x0, y0, x0 + W, y0 + H)))


def zoom_frame(bg_np, t):
    scale = 1.0 + 0.05 * (t / DURATION)
    img = Image.fromarray(bg_np)
    nw, nh = int(W * scale), int(H * scale)
    img = img.resize((nw, nh), Image.LANCZOS)
    xo = (nw - W) // 2
    yo = (nh - H) // 2
    return img.crop((xo, yo, xo + W, yo + H)).convert("RGBA")


def make_sound_banner():
    bh = 190
    img  = Image.new("RGBA", (W, bh), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    font = get_font(100, bold=True)
    stroke = 8
    x, y = W // 2, bh // 2
    for dx in range(-stroke, stroke + 1):
        for dy in range(-stroke, stroke + 1):
            if dx == 0 and dy == 0:
                continue
            draw.text((x + dx, y + dy), "Use this sound", font=font,
                      fill=(0, 0, 0, 255), anchor="mm")
    draw.text((x, y), "Use this sound", font=font, fill=(255, 255, 255, 255), anchor="mm")
    return img


def format_votes(n):
    if n >= 1000:
        v = n / 1000
        s = f"{v:.1f}".rstrip('0').rstrip('.')
        return f"{s} thousand votes"
    return f"{n} votes"


def make_poll_sticker(show_pct=False, yes_pct=0, total_votes=0):
    pw, ph = 625, 460

    img  = Image.new("RGBA", (pw, ph), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    draw.rounded_rectangle([(0, 0), (pw - 1, ph - 1)], radius=28, fill=POLL_BG)

    title_f = get_font(42, bold=True)
    opt_f   = get_font(36, bold=True)
    pct_f   = get_font(34)
    vote_f  = get_font(26)

    draw.text((18, 82), "Please Subscribe", font=title_f, fill=POLL_BLUE, anchor="lm")

    draw.rounded_rectangle([(18, 118), (pw - 18, 238)], radius=16, fill=OPTION_BG)
    draw.text((52, 178), "Yes", font=opt_f, fill=POLL_BLUE, anchor="lm")
    if show_pct:
        draw.text((pw - 40, 178), f"{yes_pct}%", font=pct_f, fill=POLL_BLUE, anchor="rm")

    draw.rounded_rectangle([(18, 252), (pw - 18, 372)], radius=16, fill=OPTION_BG)
    draw.text((52, 312), "No but I'll like", font=opt_f, fill=POLL_BLUE, anchor="lm")
    if show_pct:
        draw.text((pw - 40, 312), f"{100 - yes_pct}%", font=pct_f, fill=POLL_BLUE, anchor="rm")
        draw.text((pw // 2, ph - 30), format_votes(total_votes), font=vote_f, fill=POLL_BLUE, anchor="mm")

    return img


def apply_alpha(img: Image.Image, scale: float) -> Image.Image:
    r, g, b, a = img.split()
    a = a.point(lambda v: int(v * scale))
    return Image.merge("RGBA", (r, g, b, a))


def build_make_frame(bg_np, banner, poll_plain, poll_pct):
    banner_y = int(H * 0.40)
    poll_x   = (W - poll_plain.width) // 2
    poll_y   = int(H * 0.58)

    def make_frame(t):
        base = zoom_frame(bg_np, t)
        base.paste(banner, (0, banner_y), banner)

        if t >= 0.5:
            poll = poll_pct if t >= 7.0 else poll_plain
            progress = min(1.0, (t - 0.5) / 0.4)
            card = apply_alpha(poll.copy(), progress)
            if t < 1.1:
                boom = 1.0 + 0.055 * np.sin(np.pi * (t - 0.5) / 0.4)
                nw = int(poll.width * boom)
                nh = int(poll.height * boom)
                card = card.resize((nw, nh), Image.LANCZOS)
                px = (W - nw) // 2
                py = poll_y - (nh - poll.height) // 2
            else:
                px, py = poll_x, poll_y
            base.paste(card, (px, py), card)

        return np.array(base.convert("RGB"))

    return make_frame


def main():
    if not os.path.exists(SCREENSHOT_PATH):
        print("[info] No analytics.png found — generating placeholder background.")
        os.makedirs("assets", exist_ok=True)
        placeholder = Image.new("RGB", (W, H), (15, 15, 30))
        draw = ImageDraw.Draw(placeholder)
        font = get_font(60, bold=True)
        draw.text((W // 2, 200), "Analytics Screenshot\nGoes Here",
                  font=font, fill=(100, 120, 200), anchor="mm", align="center")
        placeholder.save(SCREENSHOT_PATH)

    os.makedirs("output", exist_ok=True)

    total_votes = random.randint(60, 4000)
    yes_pct     = random.randint(20, 40)  # No but I'll like gets majority

    print("Preparing assets...")
    bg         = prepare_bg(SCREENSHOT_PATH)
    banner     = make_sound_banner()
    poll_plain = make_poll_sticker(show_pct=False)
    poll_pct   = make_poll_sticker(show_pct=True, yes_pct=yes_pct, total_votes=total_votes)

    print("Rendering frames...")
    clip = VideoClip(build_make_frame(bg, banner, poll_plain, poll_pct), duration=DURATION).set_fps(FPS)

    if os.path.exists(AUDIO_PATH):
        print(f"Adding audio: {AUDIO_PATH}")
        audio = AudioFileClip(AUDIO_PATH).subclip(0, DURATION)
        clip  = clip.set_audio(audio)
    else:
        print("[warn] No audio — silent.")

    print(f"Writing {OUTPUT_PATH} ...")
    clip.write_videofile(OUTPUT_PATH, fps=FPS, codec="libx264",
                         audio_codec="aac", preset="fast", threads=4, logger=None)
    print(f"Done → {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
