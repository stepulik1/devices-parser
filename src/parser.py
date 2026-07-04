import asyncio
import random
import logging
from lxml import etree
from src.browser import BrowserManager
from src.database import Database
from config.settings import TARGET_URL, MIN_DELAY, MAX_DELAY

logger = logging.getLogger(__name__)

class WorldDevicesParser:
    def __init__(self, browser: BrowserManager, db: Database):
        self.browser = browser
        self.db = db
 
        self.visited_urls = set() 

    async def parse_categories(self) -> list[dict]:
        """Сбор категорий с главной страницы (CSS-селекторы)"""
        page = await self.browser.fetch_page(TARGET_URL, "div.category_icons")
        if not page: return []

        html = await page.content()
        await page.close()

        dom = etree.HTML(html)
 
        nodes = dom.xpath('//div[contains(@class, "category_icons")]//div[contains(@class, "blocks")]/a')
        
        categories = []
        for node in nodes:
            href = node.get('href')
            name = node.xpath('.//div[@class="name"]/text()')[0].strip() if node.xpath('.//div[@class="name"]/text()') else "N/A"
            if href and not href.startswith('http'):
                href = TARGET_URL + href
            categories.append({"name": name, "url": href})
            
        logger.info(f"Найдено {len(categories)} категорий.")
        return categories


    async def parse_first_product(self, category_url: str) -> tuple[str | None, str | None]:
        """Поиск первых 5 товаров в категории и их названий (CSS/DevTools)"""
 
        page = await self.browser.fetch_page(category_url, "div.products-block")
        if not page: 
            return []

        html = await page.content()
        await page.close()

        dom = etree.HTML(html)
 
        products_node = dom.xpath('//div[contains(@class, "product-thumb__caption")]//a[contains(@class, "product-thumb__name")]')
        
        products = []

        for product_node in products_node[:5]:
            url = product_node.get('href')
            name = product_node.text.strip() if product_node.text else "Без названия"
            
            if url and not url.startswith('http'):
                url = TARGET_URL + url
                
            products.append((url, name))
            
        logger.info(f"Найдено {len(products)} продуктов.")
        return products


    async def parse_product_details(self, product_url: str, product_name: str, category_id: int):
        """Парсинг карточки товара (XPath для сложной таблицы характеристик)"""
        if product_url in self.visited_urls:
            return
        self.visited_urls.add(product_url)

        page = await self.browser.fetch_page(product_url, "h1")
        if not page: return

        html = await page.content()
        await page.close()

        dom = etree.HTML(html)
        
        product_id = await self.db.upsert_product(category_id, product_name, product_url)
        await self.db.clear_specs(product_id)

        spec_tab = dom.xpath('//div[@id="tab-specification"]')
        if not spec_tab:
            logger.info(f"Характеристики отсутствуют для товара: {product_name}")

        spec_groups = dom.xpath('//div[@id="tab-specification"]//h4[@class="heading"]')
        
        for group_node in spec_groups:
            group_name = group_node.xpath('.//span/text()')[0].strip() if group_node.xpath('.//span/text()') else "Прочее"
            
            data_div = group_node.xpath('./following-sibling::div[contains(@class, "product-data")][1]')
            if not data_div: continue
            
            items = data_div[0].xpath('.//div[@class="product-data__item"]')
            for item in items:
                key = "".join(item.xpath('./div[@class="product-data__item-div"][1]//text()')).strip()
                value = "".join(item.xpath('./div[@class="product-data__item-div"][2]//text()')).strip()
                
                if key and value:
                    await self.db.insert_spec(product_id, group_name, key, value)

        logger.info(f"Сохранен продукт: {product_name}")


    async def run(self):
        """Оркестрация процессов"""
        categories = await self.parse_categories()

        for cat in categories:
            logger.info(f"Категория: {cat['name']} ---")
            cat_id = await self.db.upsert_category(cat['name'], cat['url'])
            
            await asyncio.sleep(random.uniform(MIN_DELAY, MAX_DELAY))
            
            products = await self.parse_first_product(cat['url'])

            if not products:
                logger.warning(f"Нет продуктов в категории: {cat['name']}")
                continue

            for product_url, product_name in products:
                await asyncio.sleep(random.uniform(MIN_DELAY, MAX_DELAY))
                await self.parse_product_details(product_url, product_name, cat_id)
