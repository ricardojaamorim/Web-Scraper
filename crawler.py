from config import BASE_URL
from http_client import RateLimitedSession, RobotsChecker
from models import Product
from parser import parse_product_listing


def build_grid_url(cgid: str, start: int, page_size: int, extra_params: dict | None = None) -> str:
    """Builds a Search-UpdateGrid URL — the same endpoint the 'Ver mais' button
    calls under the hood. This is what lets us page through a whole category
    without clicking anything or scrolling: we just increment `start`.
    """
    params = {"cgid": cgid, "start": start, "sz": page_size}
    if extra_params:
        params.update(extra_params)
    query = "&".join(f"{k}={v}" for k, v in params.items())
    return f"{BASE_URL}/on/demandware.store/Sites-pingo-doce-Site/default/Search-UpdateGrid?{query}"


def scrape_category(
    session: RateLimitedSession,
    robots: RobotsChecker,
    cgid: str,
    page_size: int = 14,
    max_pages: int = 50,
    extra_params: dict | None = None,
) -> list[Product]:
    """Pages through an entire category using the same 'start'/'sz' pattern
    as the site's own button, stopping when a page returns no
    products (or after max_pages, as a safety net against an infinite loop
    if the site's response format ever changes unexpectedly).
    """
    all_products: list[Product] = []

    for page_num in range(max_pages):
        start = page_num * page_size
        url = build_grid_url(cgid, start, page_size, extra_params)

        if not robots.can_fetch(url):
            print(f"  [skip] robots.txt disallows: {url}")
            break

        response = session.get(url)
        if response is None:
            break  # network/HTTP error — stop rather than retry forever

        products = parse_product_listing(response.text, url)
        if not products:
            print(f"  [done] page {page_num} returned 0 products — end of category")
            break

        print(f"  [page {page_num}] start={start} -> {len(products)} products")
        all_products.extend(products)

    return all_products
