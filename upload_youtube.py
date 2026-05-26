import os
import pickle
import datetime
import sys

from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

TOKEN_PATH = "token.pkl"
VIDEO_PATH = "output/short.mp4"


def get_service():
    if not os.path.exists(TOKEN_PATH):
        raise FileNotFoundError(f"{TOKEN_PATH} not found")
    with open(TOKEN_PATH, "rb") as f:
        creds = pickle.load(f)
    if creds.expired and creds.refresh_token:
        print("Token expired — refreshing...")
        creds.refresh(Request())
        with open(TOKEN_PATH, "wb") as f:
            pickle.dump(creds, f)
    return build("youtube", "v3", credentials=creds)


def main():
    if not os.path.exists(VIDEO_PATH):
        print(f"No video at {VIDEO_PATH} — skipping upload.")
        sys.exit(0)

    today = datetime.date.today().strftime("%B %d, %Y")
    title = f"{today} #Shorts"

    body = {
        "snippet": {
            "title":       title,
            "description": "#Shorts",
            "tags":        ["Shorts", "Reddit", "AITA", "Viral"],
            "categoryId":  "24",
            "defaultLanguage":      "en",
            "defaultAudioLanguage": "en",
        },
        "status": {
            "privacyStatus":           "public",
            "selfDeclaredMadeForKids": False,
            "madeForKids":             False,
        },
    }

    media = MediaFileUpload(
        VIDEO_PATH, mimetype="video/mp4",
        resumable=True, chunksize=8 * 1024 * 1024
    )

    youtube = get_service()
    request = youtube.videos().insert(part="snippet,status", body=body, media_body=media)

    print(f"Uploading: {VIDEO_PATH}")
    print(f"  Title: {title}")

    response = None
    while response is None:
        status, response = request.next_chunk()
        if status:
            print(f"  {int(status.progress() * 100)}%")

    print(f"Done: https://www.youtube.com/shorts/{response['id']}")


if __name__ == "__main__":
    main()
