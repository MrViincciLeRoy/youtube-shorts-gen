# YT Shorts Generator

Generates an 8-second vertical Short (1080×1920): 4s thumbnail intro + last 6s of the analytics clip, with audio over everything.

## Pipeline Flow

```
Tttt.yml (scheduled daily)
  → scrapes YT analytics screenshot
  → commits to assets/analytics.png
  → triggers Generate.yml

Generate.yml
  → downloads thumbnail.mp4 from Google Drive (GDRIVE_THUMBNAIL_ID)
  → downloads sound.mp3 from Google Drive (GDRIVE_SOUND_ID)
  → runs generate_video.py
  → uploads short.mp4 as artifact
  → deletes assets (commits with [skip-generate] to avoid re-triggering)
```

## Secrets Required

| Secret | Description |
|---|---|
| `GDRIVE_THUMBNAIL_ID` | Google Drive file ID for the 4s thumbnail video |
| `GDRIVE_SOUND_ID` | Google Drive file ID for the 8s audio |

Make Drive files public (Anyone with the link) so `gdown` can fetch them without auth.

## Local Run

```bash
pip install -r requirements.txt
sudo apt-get install ffmpeg fonts-liberation

# Place files manually
cp your_thumbnail.mp4 assets/thumbnail.mp4
cp your_sound.mp3 assets/sound.mp3
cp your_screenshot.png assets/analytics.png

python generate_video.py
# Output → output/short.mp4
```
