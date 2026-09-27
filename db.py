import sqlite3

from models import Product


def init_db(path: str) -> sqlite3.Connection:
    conn = sqlite3.connect(path)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS price_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            store TEXT NOT NULL,
            product_id TEXT,
            name TEXT NOT NULL,
            brand TEXT,
            category TEXT,
            price REAL,
            original_price REAL,
            on_promo INTEGER,
            promo_message TEXT,
            unit_price TEXT,
            url TEXT NOT NULL,
            scraped_at TEXT NOT NULL
        )
    """)
    conn.commit()
    return conn


def save_products(conn: sqlite3.Connection, products: list[Product]) -> None:
    conn.executemany(
        """INSERT INTO price_history
           (store, product_id, name, brand, category, price, original_price,
            on_promo, promo_message, unit_price, url, scraped_at)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        [(p.store, p.product_id, p.name, p.brand, p.category, p.price, p.original_price,
          int(p.on_promo), p.promo_message, p.unit_price, p.url, p.scraped_at) for p in products],
    )
    conn.commit()
