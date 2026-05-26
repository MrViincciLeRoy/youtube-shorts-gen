import asyncio
import os
from pathlib import Path
from playwright.async_api import async_playwright

CHANNEL = os.getenv("CHANNEL_URL", "https://www.youtube.com/@ptanetwork")
PAGES_INPUT = os.getenv("PAGES", "about,channel")
FULL_PAGE = os.getenv("FULL_PAGE", "false").lower() == "true"
DEVICE_PRESET = os.getenv("DEVICE_PRESET", "pixel8")
WAIT_MS = int(os.getenv("WAIT_MS", "3000"))
HEADLESS = os.getenv("HEADLESS", "true").lower() == "true"
IMAGE_FORMAT = os.getenv("IMAGE_FORMAT", "png")
OUT_DIR = Path("screenshots")

PRESETS = {
    "pixel8": {
        "viewport": {"width": 393, "height": 852},
        "device_scale_factor": 2.75,
        "user_agent": "Mozilla/5.0 (Linux; Android 14; Pixel 8) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Mobile Safari/537.36",
    },
    "iphone15": {
        "viewport": {"width": 393, "height": 852},
        "device_scale_factor": 3.0,
        "user_agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1",
    },
    "galaxy_s23": {
        "viewport": {"width": 360, "height": 780},
        "device_scale_factor": 3.0,
        "user_agent": "Mozilla/5.0 (Linux; Android 13; SM-S911B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Mobile Safari/537.36",
    },
    "custom": {
        "viewport": {
            "width": int(os.getenv("VIEWPORT_WIDTH", "393")),
            "height": int(os.getenv("VIEWPORT_HEIGHT", "852")),
        },
        "device_scale_factor": float(os.getenv("SCALE_FACTOR", "2.75")),
        "user_agent": "Mozilla/5.0 (Linux; Android 14; Pixel 8) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Mobile Safari/537.36",
    },
}

PAGE_PATHS = {
    "channel": "",
    "about": "/about",
    "videos": "/videos",
    "shorts": "/shorts",
    "community": "/community",
}

def build_url(base, tab):
    return f"{base.rstrip('/')}{PAGE_PATHS.get(tab, f'/{tab}')}"

async def shoot(page, url, name):
    print(f"→ {url}")
    await page.goto(url, wait_until="networkidle", timeout=30_000)
    await page.wait_for_timeout(WAIT_MS)
    path = OUT_DIR / f"pta_{name}.{IMAGE_FORMAT}"
    await page.screenshot(
        path=str(path),
        full_page=FULL_PAGE,
        type=IMAGE_FORMAT,
        **({"quality": 85} if IMAGE_FORMAT == "jpeg" else {}),
    )
    print(f"  saved {path}")

async def main():
    OUT_DIR.mkdir(exist_ok=True)
    device = PRESETS.get(DEVICE_PRESET, PRESETS["pixel8"])
    tabs = [t.strip() for t in PAGES_INPUT.split(",") if t.strip()]

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=HEADLESS)
        ctx = await browser.new_context(**device, is_mobile=True, has_touch=True)
        page = await ctx.new_page()
        for tab in tabs:
            await shoot(page, build_url(CHANNEL, tab), tab)
        await browser.close()
        print("Done.")

if __name__ == "__main__":
    asyncio.run(main())
