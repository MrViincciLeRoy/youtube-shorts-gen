#!/usr/bin/env python3
import os
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

POLL_BG    = (224, 234, 255, 252)
POLL_BLUE  = (18,  18,  180, 255)
OPTION_BG  = (202, 221, 255, 255)
SOUND_BG   = (255, 255, 255, 255)
SOUND_TEXT = (0,   0,   0,   255)


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
    pad_x, pad_y = 40, 24
    img = Image.new("RGBA", (W, bh), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    draw.rounded_rectangle([(pad_x, pad_y), (W - pad_x, bh - pad_y)],
                            radius=18, fill=SOUND_BG)
    font = get_font(100, bold=True)
    draw.text((W // 2, bh // 2), "USE THIS SOUND!",
              font=font, fill=SOUND_TEXT, anchor="mm")
    return img


def format_votes(n):
    if n >= 1000:
        v = n / 1000
        s = f"{v:.1f}".rstrip('0').rstrip('.')
        return f"{s} thousand votes"
    return f"{n} votes"


def make_poll_sticker(show_pct=False, yes_votes=0, no_votes=0):
    # Full-width card matching reference — ~960px wide, left margin 60px from frame edge
    pw = 960
    # Heights: top pad 24, title row ~90, gap 12, option1 ~110, gap 14, option2 ~110, gap 20, votes ~50, pad 20
    ph = 24 + 90 + 12 + 110 + 14 + 110 + 20 + 50 + 20  # = 450

    img  = Image.new("RGBA", (pw, ph), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # Card background
    draw.rounded_rectangle([(0, 0), (pw - 1, ph - 1)], radius=36, fill=POLL_BG)

    title_f = get_font(62, bold=True)
    opt_f   = get_font(52, bold=True)
    pct_f   = get_font(52, bold=True)
    vote_f  = get_font(36)

    # Title — "Will you subscribe?" left aligned with padding 32
    title_y = 24 + 45   # vertical center of title row
    draw.text((32, title_y), "Will you subscribe?",
              font=title_f, fill=POLL_BLUE, anchor="lm")

    # Option rows
    opt1_y0 = 24 + 90 + 12                      # 126
    opt1_y1 = opt1_y0 + 110                      # 236
    opt2_y0 = opt1_y1 + 14                       # 250
    opt2_y1 = opt2_y0 + 110                      # 360

    # Yes row
    draw.rounded_rectangle([(16, opt1_y0), (pw - 16, opt1_y1)], radius=20, fill=OPTION_BG)
    opt1_mid = (opt1_y0 + opt1_y1) // 2
    draw.text((40, opt1_mid), "Yes", font=opt_f, fill=POLL_BLUE, anchor="lm")
    if show_pct:
        total = yes_votes + no_votes or 1
        yes_pct = int(round(yes_votes / total * 100))
        draw.text((pw - 40, opt1_mid), f"{yes_pct}%", font=pct_f, fill=POLL_BLUE, anchor="rm")

    # No row
    draw.rounded_rectangle([(16, opt2_y0), (pw - 16, opt2_y1)], radius=20, fill=OPTION_BG)
    opt2_mid = (opt2_y0 + opt2_y1) // 2
    draw.text((40, opt2_mid), "No but I'll like", font=opt_f, fill=POLL_BLUE, anchor="lm")
    if show_pct:
        no_pct = 100 - yes_pct
        draw.text((pw - 40, opt2_mid), f"{no_pct}%", font=pct_f, fill=POLL_BLUE, anchor="rm")

    # Vote count centered
    votes_y = opt2_y1 + 20 + 25
    total_votes = yes_votes + no_votes
    draw.text((pw // 2, votes_y), format_votes(total_votes),
              font=vote_f, fill=POLL_BLUE, anchor="mm")

    return img


def apply_alpha(img: Image.Image, scale: float) -> Image.Image:
    r, g, b, a = img.split()
    a = a.point(lambda v: int(v * scale))
    return Image.merge("RGBA", (r, g, b, a))


def build_make_frame(bg_np, banner):
    banner_y = int(H * 0.40)

    total_votes = random.randint(800, 3500)
    yes_votes   = int(total_votes * random.uniform(0.60, 0.80))
    no_votes    = total_votes - yes_votes

    poll_no_pct   = make_poll_sticker(show_pct=False, yes_votes=yes_votes, no_votes=no_votes)
    poll_with_pct = make_poll_sticker(show_pct=True,  yes_votes=yes_votes, no_votes=no_votes)

    # Left-align poll with 60px margin from left edge
    poll_x = 60
    poll_y = int(H * 0.57)

    def make_frame(t):
        base = zoom_frame(bg_np, t)
        base.paste(banner, (0, banner_y), banner)

        if t >= 2.0:
            poll = poll_with_pct if t >= 7.0 else poll_no_pct
            progress = min(1.0, (t - 2.0) / 0.4)
            card = apply_alpha(poll.copy(), progress)

            if t < 2.6:
                boom = 1.0 + 0.055 * np.sin(np.pi * (t - 2.0) / 0.4)
                nw = int(poll.width * boom)
                nh = int(poll.height * boom)
                card = card.resize((nw, nh), Image.LANCZOS)
                px = poll_x - (nw - poll.width) // 2
                py = poll_y - (nh - poll.height) // 2
            else:
                px, py = poll_x, poll_y

            base.paste(card, (px, py), card)

        return np.array(base.convert("RGB"))

    return make_frame


def main():
    if not os.path.exists(SCREENSHOT_PATH):
        print("[info] No analytics.png — generating placeholder.")
        os.makedirs("assets", exist_ok=True)
        placeholder = Image.new("RGB", (W, H), (15, 15, 30))
        draw = ImageDraw.Draw(placeholder)
        font = get_font(60, bold=True)
        draw.text((W // 2, 200), "Analytics Screenshot\nGoes Here",
                  font=font, fill=(100, 120, 200), anchor="mm", align="center")
        placeholder.save(SCREENSHOT_PATH)

    os.makedirs("output", exist_ok=True)
    print("Preparing assets...")
    bg     = prepare_bg(SCREENSHOT_PATH)
    banner = make_sound_banner()

    print("Rendering frames...")
    clip = VideoClip(build_make_frame(bg, banner), duration=DURATION).set_fps(FPS)

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
