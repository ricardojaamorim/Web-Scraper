from dataclasses import dataclass


@dataclass
class Product:
    store: str
    product_id: str | None       # retailer's own SKU/PID, e.g. "41043"
    name: str
    brand: str | None
    category: str | None
    price: float | None          # current price (what you'd pay now)
    original_price: float | None  # pre-discount price, if on promotion
    on_promo: bool
    promo_message: str | None
    unit_price: str | None        # e.g. "0,9 €/L"
    url: str
    scraped_at: str
