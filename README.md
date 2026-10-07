# Web Scraper — Pingo Doce Price Tracker

A small Python scraper that tracks product prices from [Pingo Doce](https://www.pingodoce.pt)'s online store over time. It pages through category listings, parses each product card, and appends the results to a local SQLite database — so running it daily (e.g. via a scheduled task) builds up a price-history dataset you can query later.

## Features

- **Respects `robots.txt`** — checks every URL before fetching and skips anything disallowed.
- **Rate-limited requests** — waits between requests (using the site's declared crawl delay when available) to avoid hammering the server.
- **Robust parsing** — prefers the structured `data-gtm-info` analytics JSON embedded in each product card, falling back to DOM selectors when it's missing.
- **Full category pagination** — follows the same `Search-UpdateGrid` endpoint the site's own "Ver mais" button uses, so it can walk an entire category without a browser.
- **SQLite storage** — every run appends a snapshot to a `price_history` table, preserving prior prices instead of overwriting them. Products listed in several categories (e.g. promotions and their own aisle) are saved once per run.
- **Price reports** — `report.py` shows price drops/rises, new/gone products and per-product price history between runs.

## Requirements

- Python 3.10+
- [`requests`](https://pypi.org/project/requests/)
- [`beautifulsoup4`](https://pypi.org/project/beautifulsoup4/)

Install dependencies:

```bash
pip install -r requirements.txt
```

## Usage

Run the scraper:

```bash
python main.py
```

This fetches every category listed in `CATEGORIES` (produce, meat, dairy, drinks, cleaning, etc.), parses each product, and saves the results to `prices.db` in the current directory. Progress is printed as it goes (numbers are illustrative):

```text
Scraping category: ec_talho_200
  [page 0] start=0 -> 14 products
  [page 1] start=14 -> 14 products
  ...
  [done] page 9 returned 0 products — end of category
  -> 98 new rows for ec_talho_200 (12 already seen this run)
Done. Run 2026-09-27T08:00:00: 6120 rows saved, 840 duplicates skipped -> prices.db
```

"Already seen this run" counts products that an earlier category in the same run had already saved (most often items from the promotions category showing up again in their own aisle). They are skipped, not saved twice.

Inspect what was saved with the `sqlite3` command-line tool:

```bash
sqlite3 prices.db "SELECT name, brand, price, unit_price, promo_message FROM price_history ORDER BY id DESC LIMIT 20"
```

Or use `report.py` (below) for comparisons between runs.

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

| File               | Responsibility                                                                                    |
| ------------------ | ------------------------------------------------------------------------------------------------- |
| `main.py`          | Entry point — wires everything together and runs the scrape                                       |
| `config.py`        | All configuration: `BASE_URL`, `USER_AGENT`, delays, `DB_PATH`, `PRODUCT_SELECTORS`, `CATEGORIES` |
| `models.py`        | The `Product` dataclass                                                                           |
| `http_client.py`   | `RobotsChecker` and `RateLimitedSession` (robots.txt + rate limiting)                             |
| `parser.py`        | Parses category/search page HTML into `Product` records                                           |
| `crawler.py`       | Pages through a whole category via the `Search-UpdateGrid` endpoint                               |
| `db.py`            | SQLite schema setup and inserts                                                                   |
| `report.py`        | CLI reports: price drops/rises, new/gone products, per-product price history                      |
| `requirements.txt` | Python dependencies                                                                               |

## Database schema

Each run inserts one row per product into `price_history`:

| Column           | Description                                                                                                           |
| ---------------- | --------------------------------------------------------------------------------------------------------------------- |
| `id`             | Auto-incrementing row id                                                                                              |
| `run_id`         | UTC timestamp of the run start (`YYYY-MM-DDTHH:MM:SS`), shared by every row saved in the same run                     |
| `store`          | Retailer name (currently always "Pingo Doce")                                                                         |
| `product_id`     | Retailer SKU/PID, when available                                                                                      |
| `name`           | Product name                                                                                                          |
| `brand`          | Product brand, if listed                                                                                              |
| `category`       | Category path from the card's analytics data, most specific first, joined with `>`, e.g. `"Vitela e Vitelão > Talho"` |
| `price`          | Current price (what you'd pay now)                                                                                    |
| `original_price` | Pre-discount price, if the item is on promotion                                                                       |
| `on_promo`       | `1` if discounted, else `0`                                                                                           |
| `promo_message`  | Promo text shown on the card, if any                                                                                  |
| `unit_price`     | Per-unit price string, e.g. `"0,9 €/L"`                                                                               |
| `url`            | Link to the product page                                                                                              |
| `scraped_at`     | UTC timestamp of the page the product was parsed from (ISO 8601); differs slightly between rows of the same run       |

Indexes:

- `ux_run_product`: unique on `(run_id, product_id)`, so there's at most one row per product per run.
- `ix_product_time`: on `(product_id, scraped_at)`, which speeds up per-product history lookups.

Rows are never updated in place. Each run adds a fresh snapshot tagged with its `run_id`, and within a run a product is saved only once: rows are inserted with `INSERT OR IGNORE`, so if the same product shows up in a later category, the copy saved first is kept. Use `run_id` (not `scraped_at`) to group rows by run, for example to get one product's price history:

```sql
SELECT run_id, price, original_price, on_promo
FROM price_history
WHERE product_id = '41043'
ORDER BY run_id;
```

Rows without a `product_id` aren't covered by the unique index (SQLite treats NULLs as distinct), so they could in theory be saved more than once per run.

**Upgrading an older database:** databases created before `run_id` existed are migrated automatically the first time `main.py` runs. The column is added, existing rows get their scrape date (`YYYY-MM-DD`) as their `run_id`, and duplicate rows for the same product on the same day are removed, keeping the first one.

## Configuration

All the knobs live in `config.py`:

- `BASE_URL` — the store's base URL.
- `USER_AGENT` — identifies the bot; update the contact email before running this against a real site.
- `MIN_DELAY_SECONDS` — floor for the delay between requests.
- `DB_PATH` — path to the SQLite file.
- `PRODUCT_SELECTORS` — CSS selectors used to parse each product card; update these if the site's markup changes.
- `CATEGORIES` — the list of categories to scrape. Each entry has:
  - `cgid`: the site's category id, e.g. `ec_talho_200` (take it from the category page's URL).
  - `extra_params` (optional): extra query parameters added to every page request for that category. All current entries use `{"pmin": "0.04"}`, a minimum-price filter.

  Categories are scraped in list order. Because a product is saved only once per run, a product in several categories gets the data from the first one where it appears. `ec_promos_1100000` comes first on purpose.

## Notes

This project only fetches publicly listed prices and honors `robots.txt` and rate limits — it's meant for personal price tracking, not high-volume or commercial scraping. Sites can change their markup or terms at any time, so selectors in `PRODUCT_SELECTORS` may need updates if scraping stops working.
