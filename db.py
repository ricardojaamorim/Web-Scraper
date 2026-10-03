import sqlite3

from models import Product


def init_db(path: str) -> sqlite3.Connection:
    conn = sqlite3.connect(path)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS price_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            run_id TEXT,
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
    _migrate(conn)
    # One row per product per run, enforced by the database itself.
    conn.execute("CREATE UNIQUE INDEX IF NOT EXISTS ux_run_product ON price_history(run_id, product_id)")
    conn.execute("CREATE INDEX IF NOT EXISTS ix_product_time ON price_history(product_id, scraped_at)")
    conn.commit()
    return conn


def _migrate(conn: sqlite3.Connection) -> None:
    """Upgrades a database created before run_id existed. Runs once."""
    cols = {row[1] for row in conn.execute("PRAGMA table_info(price_history)")}
    if "run_id" in cols:
        return
    conn.execute("ALTER TABLE price_history ADD COLUMN run_id TEXT")
    # Old rows have no run_id; the scrape day is a good stand-in
    conn.execute("UPDATE price_history SET run_id = substr(scraped_at, 1, 10)")
    # Keep the first copy of each product per run, delete the rest
    conn.execute("""
        DELETE FROM price_history
        WHERE product_id IS NOT NULL
          AND id NOT IN (SELECT MIN(id) FROM price_history
                         WHERE product_id IS NOT NULL
                         GROUP BY run_id, product_id)
    """)


def save_products(conn: sqlite3.Connection, products: list[Product], run_id: str) -> int:
    """Inserts products for this run. Returns how many were actually new."""
    before = conn.total_changes
    conn.executemany(
        """INSERT OR IGNORE INTO price_history
           (run_id, store, product_id, name, brand, category, price, original_price,
            on_promo, promo_message, unit_price, url, scraped_at)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        [(run_id, p.store, p.product_id, p.name, p.brand, p.category, p.price, p.original_price,
          int(p.on_promo), p.promo_message, p.unit_price, p.url, p.scraped_at) for p in products],
    )
    conn.commit()
    return conn.total_changes - before