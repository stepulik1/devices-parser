import asyncio
import logging
from playwright.async_api import async_playwright, Page, BrowserContext, Error as PlaywrightError
from playwright_stealth import Stealth 
from config.settings import MAX_RETRIES, BACKOFF_FACTOR

logger = logging.getLogger(__name__)

class BrowserManager:
    def __init__(self):
        self.playwright = None
        self.browser = None

    async def start(self):
        self.playwright = await async_playwright().start()
        self.browser = await self.playwright.chromium.launch(headless=True)

    async def stop(self):
        if self.browser: await self.browser.close()
        if self.playwright: await self.playwright.stop()

    async def fetch_page(self, url: str, wait_selector: str, attempt: int = 1) -> Page | None:
        """Загружает страницу с обработкой антибот-ошибок и повторными попытками"""
        context = await self.browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
            viewport={"width": 1920, "height": 1080},
            locale="ru-RU"
        )
        
        stealth = Stealth()

        await stealth.apply_stealth_async(context)

        page = await context.new_page()

        def handle_response(response):
            if response.status in [403, 429, 503]:
                logger.warning(f"Сработал антибот! Код ответа: {response.status} on {response.url}")

        page.on("Ответ", handle_response)

        try:
            logger.info(f"Загрузка страницы: {url}")
 
            await page.goto(url, wait_until="networkidle", timeout=60000)
            
 
            await page.wait_for_selector(wait_selector, timeout=15000, state="attached")
            return page

        except PlaywrightError as e:
            logger.error(f"Ошибка загрузки страницы {url}: {e}")
            await context.close()
            
 
            if attempt < MAX_RETRIES:
                wait_time = BACKOFF_FACTOR * attempt
                logger.info(f"Ждем {wait_time}s перед следующей попыткой...")
                await asyncio.sleep(wait_time)
                return await self.fetch_page(url, wait_selector, attempt + 1)
            return None