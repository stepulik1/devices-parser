import asyncio
import logging
from datetime import datetime
from src.browser import BrowserManager
from src.database import Database
from src.parser import WorldDevicesParser
from config.settings import LOG_DIR

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_DIR / f"parser_{datetime.now().strftime('%Y%m%d')}.log", encoding='utf-8'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

async def main():   
    logger.info("--- СТАРТ ПАРСЕРА ---")
    
    db = Database()
    await db.init()
    
    browser = BrowserManager()
    await browser.start()
    
    try:
        parser = WorldDevicesParser(browser, db)
        await parser.run()
    except Exception as e:
        logger.critical(f"Критическая ошибка: {e}")
    finally:
        await browser.stop()
        logger.info("--- СТОП ПАРСЕРА ---")

if __name__ == "__main__":
    asyncio.run(main())