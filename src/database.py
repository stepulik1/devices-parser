import aiosqlite
import logging
from config.settings import DB_PATH

logger = logging.getLogger(__name__)

class Database:
    def __init__(self):
        self.db_path = DB_PATH

    async def init(self):
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("PRAGMA foreign_keys = ON")
            await db.executescript("""
                CREATE TABLE IF NOT EXISTS categories (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT UNIQUE NOT NULL,
                    url TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS products (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    category_id INTEGER NOT NULL,
                    name TEXT NOT NULL,
                    url TEXT UNIQUE NOT NULL,
                    FOREIGN KEY (category_id) REFERENCES categories (id)
                );
                CREATE TABLE IF NOT EXISTS specifications (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    product_id INTEGER NOT NULL,
                    group_name TEXT,
                    key_name TEXT,
                    value_name TEXT,
                    FOREIGN KEY (product_id) REFERENCES products (id) ON DELETE CASCADE
                );
            """)
            await db.commit()

    async def upsert_category(self, name: str, url: str) -> int:
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("PRAGMA foreign_keys = ON")
            cursor = await db.execute(
                "INSERT INTO categories (name, url) VALUES (?, ?) ON CONFLICT(name) DO UPDATE SET url=excluded.url RETURNING id",
                (name, url)
            )
            row = await cursor.fetchone()
            await db.commit()
            return row[0]

    async def upsert_product(self, category_id: int, name: str, url: str) -> int:
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("PRAGMA foreign_keys = ON")
            cursor = await db.execute(
                "INSERT INTO products (category_id, name, url) VALUES (?, ?, ?) ON CONFLICT(url) DO UPDATE SET name=excluded.name RETURNING id",
                (category_id, name, url)
            )
            row = await cursor.fetchone()
            await db.commit()
            return row[0]

    async def clear_specs(self, product_id: int):
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("DELETE FROM specifications WHERE product_id = ?", (product_id,))
            await db.commit()

    async def insert_spec(self, product_id: int, group: str, key: str, value: str):
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                "INSERT INTO specifications (product_id, group_name, key_name, value_name) VALUES (?, ?, ?, ?)",
                (product_id, group, key, value)
            )
            await db.commit()