import os
import asyncio
from contextlib import asynccontextmanager
from playwright.async_api import async_playwright

USER_DATA_DIR = os.getenv("USER_DATA_DIR")

@asynccontextmanager
async def browser_context(provider: str):
    async with async_playwright() as p:
        browser = await p.chromium.launch_persistent_context(
            USER_DATA_DIR or f".user-{provider}",
            headless=False,
            viewport={"width": 1360, "height": 900},
            args=[
                '--disable-blink-features=AutomationControlled',
                '--disable-web-security',
                '--disable-dev-shm-usage',
                '--no-sandbox',
                '--disable-infobars',
                '--start-maximized',
                '--enable-features=NetworkService,NetworkServiceInProcess'
            ],
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        )
        
        await browser.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', { get: () => undefined });
            Object.defineProperty(navigator, 'platform', { get: () => 'Win32' });
            Object.defineProperty(navigator, 'languages', { get: () => ['en-US', 'en'] });
            Object.defineProperty(navigator, 'plugins', { get: () => [1, 2, 3, 4] });
            Object.defineProperty(navigator, 'hardwareConcurrency', { get: () => 8 });
            Object.defineProperty(navigator, 'deviceMemory', { get: () => 8 });
            """)

        extra_headers = {
            "Accept-Language": "en-US,en;q=0.9",
            "Origin": "https://outlook.office.com",
            "Referer": "https://outlook.office.com/",
            "Sec-Ch-Ua": '"Chromium";v="120", "Not A(Brand";v="24", "Google Chrome";v="120"',
            "Sec-Ch-Ua-Mobile": "?0",
            "Sec-Ch-Ua-Platform": '"Windows"',
        }
        await browser.set_extra_http_headers(extra_headers)

        try:
            yield browser
        finally:
            print("Browser will close in 10 seconds... Press Ctrl+C to keep it open longer")
            try:
                await asyncio.sleep(10)
            except KeyboardInterrupt:
                print("Keeping browser open...")
                await asyncio.sleep(3000)
            await browser.close()