# Quick check: read a few rows from prices.db and print them.

import sqlite3

from config import DB_PATH

conn = sqlite3.connect(DB_PATH)
cur = conn.execute(
    "SELECT name, brand, price, unit_price, promo_message FROM price_history LIMIT 100"
)

for row in cur.fetchall():
    name, brand, price, unit_price, promo = row
    print(f"{name} ({brand}) - {price} EUR - {unit_price} - {promo or 'no promo'}")

conn.close()
