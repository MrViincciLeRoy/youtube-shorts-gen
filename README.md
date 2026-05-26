# YT Shorts Generator

Generates a 10-second vertical Short (1080×1920) from a YouTube Analytics screenshot with a fake "Please Subscribe" poll overlay and "Use this sound" banner.

## Setup

```bash
pip install -r requirements.txt
sudo apt-get install ffmpeg fonts-liberation
```

## Usage

1. Put your analytics screenshot at `assets/analytics.png`
2. Put your audio at `assets/sound.mp3`
3. Run:

```bash
python generate_video.py
```

Video is saved to `output/short.mp4`.

## GitHub Actions

Push to `main` (or trigger manually) — the workflow installs deps, runs the script, and uploads `short.mp4` as a downloadable artifact under **Actions → your run → Artifacts**.

> Replace `assets/analytics.png` and `assets/sound.mp3` in the repo with your own files before pushing.
