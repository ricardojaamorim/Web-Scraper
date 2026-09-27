from config import BASE_URL, CATEGORIES, DB_PATH, MIN_DELAY_SECONDS, USER_AGENT
from crawler import scrape_category
from db import init_db, save_products
from http_client import RateLimitedSession, RobotsChecker


def main():
    robots = RobotsChecker(BASE_URL, USER_AGENT)
    session = RateLimitedSession(USER_AGENT, delay=max(robots.crawl_delay, MIN_DELAY_SECONDS))
    conn = init_db(DB_PATH)

    total = 0
    for cat in CATEGORIES:
        cgid = cat["cgid"]
        print(f"Scraping category: {cgid}")
        products = scrape_category(
            session, robots, cgid,
            extra_params=cat.get("extra_params"),
        )
        save_products(conn, products)
        total += len(products)
        print(f"  -> {len(products)} total products saved for {cgid}")

    print(f"Done. {total} product rows saved to {DB_PATH}")
    conn.close()


if __name__ == "__main__":
    main()
