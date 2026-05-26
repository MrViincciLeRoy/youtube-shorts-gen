#!/usr/bin/env python3
import os
import sys
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from moviepy.editor import AudioFileClip, VideoClip

# ── Config ───────────────────────────────────────────────────────────────────
SCREENSHOT_PATH = "assets/analytics.png"
AUDIO_PATH      = "assets/sound.mp3"
OUTPUT_PATH     = "output/short.mp4"

DURATION = 10
FPS      = 30
W, H     = 1080, 1920

FONT_BOLD = "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf"
FONT_REG  = "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf"

# Exact pixel-sampled colors
POLL_BG    = (230, 239, 255, 245)   # #e6efff
POLL_BLUE  = (0,   0,   178, 255)   # #0000b2
OPTION_BG  = (219, 232, 255, 240)   # #dbe8ff
SOUND_BG   = (255, 255, 255, 255)   # white
SOUND_TEXT = (0,   0,   0,   255)   # black

# ── Helpers ──────────────────────────────────────────────────────────────────
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
    """White card, big black 'Use this sound'."""
    bh = 190
    pad_x, pad_y = 40, 24
    img = Image.new("RGBA", (W, bh), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    draw.rounded_rectangle([(pad_x, pad_y), (W - pad_x, bh - pad_y)],
                            radius=18, fill=SOUND_BG)
    font = get_font(100, bold=True)
    draw.text((W // 2, bh // 2), "Use this sound",
              font=font, fill=SOUND_TEXT, anchor="mm")
    return img


def make_poll_sticker():
    """
    Narrower + taller poll card matching real YT poll proportions.
    Width  = 625 px  (~58 % of 1080)
    Height = 420 px  (option rows are generously tall with real padding)
    """
    pw, ph = 625, 460

    img  = Image.new("RGBA", (pw, ph), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # ── card body ────────────────────────────────────────────────────────────
    draw.rounded_rectangle([(0, 0), (pw - 1, ph - 1)],
                            radius=28, fill=POLL_BG)

    title_f = get_font(42, bold=True)
    opt_f   = get_font(36, bold=True)
    pct_f   = get_font(34)
    vote_f  = get_font(26)

    # "Please Subscribe" — left-aligned, generous top padding
    draw.text((52, 82), "Please Subscribe",
              font=title_f, fill=POLL_BLUE, anchor="lm")

    # ── Yes row  (y 118 → 238) ───────────────────────────────────────────────
    draw.rounded_rectangle([(18, 118), (pw - 18, 238)],
                            radius=16, fill=OPTION_BG)
    draw.text((52, 178), "Yes",
              font=opt_f, fill=POLL_BLUE, anchor="lm")
    draw.text((pw - 40, 178), "0%",
              font=pct_f, fill=POLL_BLUE, anchor="rm")

    # ── No row  (y 252 → 372) ────────────────────────────────────────────────
    draw.rounded_rectangle([(18, 252), (pw - 18, 372)],
                            radius=16, fill=OPTION_BG)
    draw.text((52, 312), "No",
              font=opt_f, fill=POLL_BLUE, anchor="lm")
    draw.text((pw - 40, 312), "0%",
              font=pct_f, fill=POLL_BLUE, anchor="rm")

    # "0 votes"
    draw.text((pw // 2, ph - 30), "0 votes",
              font=vote_f, fill=POLL_BLUE, anchor="mm")

    return img


def apply_alpha(img: Image.Image, scale: float) -> Image.Image:
    r, g, b, a = img.split()
    a = a.point(lambda v: int(v * scale))
    return Image.merge("RGBA", (r, g, b, a))


# ── Frame factory ─────────────────────────────────────────────────────────────
def build_make_frame(bg_np, banner, poll):
    banner_y = int(H * 0.40)
    poll_x   = (W - poll.width) // 2
    poll_y   = int(H * 0.58)

    def make_frame(t):
        base = zoom_frame(bg_np, t)
        base.paste(banner, (0, banner_y), banner)

        if t >= 2.0:
            progress = min(1.0, (t - 2.0) / 0.4)
            card = apply_alpha(poll.copy(), progress)
            if t < 2.6:
                boom = 1.0 + 0.055 * np.sin(np.pi * (t - 2.0) / 0.4)
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


# ── Main ──────────────────────────────────────────────────────────────────────
def main():
    if not os.path.exists(SCREENSHOT_PATH):
        sys.exit(f"[error] screenshot not found: {SCREENSHOT_PATH}")

    os.makedirs("output", exist_ok=True)
    print("Preparing assets...")
    bg     = prepare_bg(SCREENSHOT_PATH)
    banner = make_sound_banner()
    poll   = make_poll_sticker()

    print("Rendering frames...")
    clip = VideoClip(build_make_frame(bg, banner, poll), duration=DURATION).set_fps(FPS)

    if os.path.exists(AUDIO_PATH):
        print(f"Adding audio: {AUDIO_PATH}")
        audio = AudioFileClip(AUDIO_PATH).subclip(0, DURATION)
        clip  = clip.set_audio(audio)
    else:
        print(f"[warn] No audio at {AUDIO_PATH} — silent.")

    print(f"Writing {OUTPUT_PATH} ...")
    clip.write_videofile(OUTPUT_PATH, fps=FPS, codec="libx264",
                         audio_codec="aac", preset="fast", threads=4, logger=None)
    print(f"Done → {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
