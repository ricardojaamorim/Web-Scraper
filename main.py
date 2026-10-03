from datetime import datetime, timezone
 
from config import BASE_URL, CATEGORIES, DB_PATH, MIN_DELAY_SECONDS, USER_AGENT
from crawler import scrape_category
from db import init_db, save_products
from http_client import RateLimitedSession, RobotsChecker
 
 
def main():
    robots = RobotsChecker(BASE_URL, USER_AGENT)
    session = RateLimitedSession(USER_AGENT, delay=max(robots.crawl_delay, MIN_DELAY_SECONDS))
    conn = init_db(DB_PATH)
    run_id = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S")  # one id for the whole run
 
    saved = skipped = 0
    for cat in CATEGORIES:
        cgid = cat["cgid"]
        print(f"Scraping category: {cgid}")
        products = scrape_category(
            session, robots, cgid,
            extra_params=cat.get("extra_params"),
        )
        new = save_products(conn, products, run_id)
        saved += new
        skipped += len(products) - new
        print(f"  -> {new} new rows for {cgid} ({len(products) - new} already seen this run)")
 
    print(f"Done. Run {run_id}: {saved} rows saved, {skipped} duplicates skipped -> {DB_PATH}")
    conn.close()
 
 
if __name__ == "__main__":
    main()