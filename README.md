# Web Scraper — Pingo Doce Price Tracker

A small Python scraper that tracks product prices from [Pingo Doce](https://www.pingodoce.pt)'s online store over time. It pages through category listings, parses each product card, and appends the results to a local SQLite database — so running it daily (e.g. via a scheduled task) builds up a price-history dataset you can query later.

## Features

- **Respects `robots.txt`** — checks every URL before fetching and skips anything disallowed.
- **Rate-limited requests** — waits between requests (using the site's declared crawl delay when available) to avoid hammering the server.
- **Robust parsing** — prefers the structured `data-gtm-info` analytics JSON embedded in each product card, falling back to DOM selectors when it's missing.
- **Full category pagination** — follows the same `Search-UpdateGrid` endpoint the site's own "Ver mais" button uses, so it can walk an entire category without a browser.
- **SQLite storage** — every scrape appends rows to a `price_history` table, preserving prior prices instead of overwriting them.

## Requirements

- Python 3.10+
- [`requests`](https://pypi.org/project/requests/)
- [`beautifulsoup4`](https://pypi.org/project/beautifulsoup4/)

Install dependencies:

```bash
pip install requests beautifulsoup4
```

## Usage

Run the scraper:

```bash
python main.py
```

This fetches every category listed in `CATEGORIES` (produce, meat, dairy, drinks, cleaning, etc.), parses each product, and saves the results to `prices.db` in the current directory.

Inspect what was saved:

```bash
python checkdb.py
```

This prints the first 100 rows (`name`, `brand`, `price`, `unit_price`, `promo_message`) from `price_history`.

### Price reports

Once you have at least two runs saved, `report.py` compares them:

```bash
python report.py drops              # biggest price drops, latest run vs the previous one
python report.py rises              # biggest price increases
python report.py new                # products that appeared since the previous run
python report.py gone               # products that disappeared
python report.py history 41043      # price over time for one product id...
python report.py history "leite"    # ...or by part of the name
```

Options:

| Option           | Applies to                      | Description                                                                                                                   |
| ---------------- | ------------------------------- | ----------------------------------------------------------------------------------------------------------------------------- |
| `--old`, `--new` | `drops`, `rises`, `new`, `gone` | Compare two specific runs instead of the latest two. Accepts a prefix of the run id, e.g. `2026-09-17`. Pass both or neither. |
| `--min-pct`      | `drops`, `rises`                | Only show changes of at least this many percent (default `0`)                                                                 |
| `--limit`        | `drops`, `rises`, `new`, `gone` | Maximum rows to show (default `20`)                                                                                           |
| `--db`           | all                             | Path to the database (default: `DB_PATH` from `config.py`)                                                                    |

Example:

```bash
python report.py --db prices.db drops --old 2026-09-17 --new 2026-09-27 --min-pct 20 --limit 50
```

Only **complete** runs are considered when comparing: a run with fewer than 80% of the rows of the largest run (e.g. one that crashed halfway) is ignored, so it doesn't make half the catalogue look "gone". If a product name matches several products, `history` lists the matching ids so you can pick one.

## Project structure

| File             | Responsibility                                                                                    |
| ---------------- | ------------------------------------------------------------------------------------------------- |
| `main.py`        | Entry point — wires everything together and runs the scrape                                       |
| `config.py`      | All configuration: `BASE_URL`, `USER_AGENT`, delays, `DB_PATH`, `PRODUCT_SELECTORS`, `CATEGORIES` |
| `models.py`      | The `Product` dataclass                                                                           |
| `http_client.py` | `RobotsChecker` and `RateLimitedSession` (robots.txt + rate limiting)                             |
| `parser.py`      | Parses category/search page HTML into `Product` records                                           |
| `crawler.py`     | Pages through a whole category via the `Search-UpdateGrid` endpoint                               |
| `db.py`          | SQLite schema setup and inserts                                                                   |
| `report.py`      | CLI reports: price drops/rises, new/gone products, per-product price history                      |
| `checkdb.py`     | Standalone script to inspect saved rows                                                           |

## Database schema

Each run inserts one row per product into `price_history`:

| Column           | Description                                     |
| ---------------- | ----------------------------------------------- |
| `store`          | Retailer name (currently always "Pingo Doce")   |
| `product_id`     | Retailer SKU/PID, when available                |
| `name`           | Product name                                    |
| `brand`          | Product brand, if listed                        |
| `category`       | `>`-joined category path (most specific first)  |
| `price`          | Current price (what you'd pay now)              |
| `original_price` | Pre-discount price, if the item is on promotion |
| `on_promo`       | `1` if discounted, else `0`                     |
| `promo_message`  | Promo text shown on the card, if any            |
| `unit_price`     | Per-unit price string, e.g. `"0,9 €/L"`         |
| `url`            | Link to the product page                        |
| `scraped_at`     | UTC timestamp of the scrape (ISO 8601)          |

Rows are never updated in place — re-running the scraper adds a fresh snapshot, so you can track price changes over time with a simple `GROUP BY product_id ORDER BY scraped_at`.

## Configuration

All the knobs live in `config.py`:

- `BASE_URL` — the store's base URL.
- `USER_AGENT` — identifies the bot; update the contact email before running this against a real site.
- `MIN_DELAY_SECONDS` — floor for the delay between requests.
- `DB_PATH` — path to the SQLite file.
- `PRODUCT_SELECTORS` — CSS selectors used to parse each product card; update these if the site's markup changes.
- `CATEGORIES` — the list of categories to scrape (identified by their `cgid`).

## Notes

This project only fetches publicly listed prices and honors `robots.txt` and rate limits — it's meant for personal price tracking, not high-volume or commercial scraping. Sites can change their markup or terms at any time, so selectors in `PRODUCT_SELECTORS` may need updates if scraping stops working.
