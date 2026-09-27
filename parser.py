import json
from datetime import datetime, timezone

from bs4 import BeautifulSoup

from config import PRODUCT_SELECTORS
from models import Product


def parse_gtm_info(card) -> dict:
    """Extracts the analytics JSON stashed in data-gtm-info.

    This attribute holds clean, structured fields (item_id, item_name,
    item_brand, item_category, price) that are more reliable than scraping
    the visible DOM. Returns {} if absent or unparseable, so callers can
    fall back to the DOM selectors.
    """
    raw = card.get("data-gtm-info")
    if not raw:
        return {}
    try:
        data = json.loads(raw)  # BeautifulSoup already unescapes the HTML entities
    except (json.JSONDecodeError, TypeError):
        return {}
    items = data.get("items") or []
    return items[0] if items else {}


def price_from_value_span(card, selector: str) -> float | None:
    """Reads a price from <span class="value" content="0.90">.

    Pingo Doce stores the clean numeric price in the `content` attribute,
    which is far more reliable than parsing the visible "0,90 €" text.
    Falls back to parsing the text if `content` is missing.
    """
    el = card.select_one(selector)
    if el is None:
        return None
    # Preferred: the machine-readable content attribute (already dot-decimal)
    content = el.get("content")
    if content:
        try:
            return float(content)
        except ValueError:
            pass
    # Fallback: parse the visible text like "0,90 €"
    raw = el.get_text(strip=True)
    cleaned = "".join(ch for ch in raw.replace(",", ".") if ch.isdigit() or ch == ".")
    try:
        return float(cleaned)
    except ValueError:
        return None


def parse_product_listing(html: str, page_url: str) -> list[Product]:
    """Parses a category/search page into a list of Product records."""
    soup = BeautifulSoup(html, "html.parser")
    products = []
    now = datetime.now(timezone.utc).isoformat()

    cards = soup.select(PRODUCT_SELECTORS["product_card"])
    for card in cards:
        gtm = parse_gtm_info(card)  # clean structured data, may be {}

        # DOM elements (used as fallback and for promo detection)
        name_el = card.select_one(PRODUCT_SELECTORS["name"])
        brand_el = card.select_one(PRODUCT_SELECTORS["brand"])
        unit_el = card.select_one(PRODUCT_SELECTORS["unit"])
        promo_el = card.select_one(PRODUCT_SELECTORS["promo_message"])
        link_el = card.select_one(PRODUCT_SELECTORS["link"])

        current_dom = price_from_value_span(card, PRODUCT_SELECTORS["current_price_value"])
        original = price_from_value_span(card, PRODUCT_SELECTORS["original_price_value"])

        # Prefer gtm-info fields, fall back to the visible DOM
        name = gtm.get("item_name") or (name_el.get_text(strip=True) if name_el else None)
        brand = gtm.get("item_brand") or (brand_el.get_text(strip=True) if brand_el else None)
        price = gtm.get("price") if gtm.get("price") is not None else current_dom

        if not name or price is None:
            continue  # skip malformed cards rather than crashing the whole run

        # Build category from the gtm category levels (most specific first)
        cat_levels = [gtm.get(f"item_category{'' if i == 1 else i}") for i in range(1, 6)]
        category = " > ".join(c for c in cat_levels if c) or None

        product_url = urljoin(page_url, link_el["href"]) if link_el and link_el.get("href") else page_url

        products.append(Product(
            store="Pingo Doce",
            product_id=str(gtm["item_id"]) if gtm.get("item_id") else card.get("data-pid"),
            name=name,
            brand=brand,
            category=category,
            price=price,
            original_price=original,
            on_promo=original is not None,
            promo_message=promo_el.get_text(strip=True) if promo_el else None,
            unit_price=unit_el.get_text(strip=True) if unit_el else None,
            url=product_url,
            scraped_at=now,
        ))

    return products
