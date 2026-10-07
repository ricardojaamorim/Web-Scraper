"""Price report on top of prices.db.

    python report.py drops              # biggest price drops, latest run vs previous
    python report.py rises
    python report.py new                # products that appeared
    python report.py gone               # products that disappeared
    python report.py history 41043      # price over time, by product id...
    python report.py history "leite"    # ...or by part of the name
    python report.py drops --old 2026-09-17 --new 2026-09-27 --min-pct 20 --limit 50

    python report.py drops --csv drops.csv      # any report -> CSV for Excel (all rows)
    python report.py export --csv run.csv       # whole latest run -> CSV
    python report.py export --run 2026-09-27 --csv run.csv
"""
import argparse
import csv
import sqlite3
import sys

from config import DB_PATH

# Product names/categories contain characters (e.g. zero-width spaces) that the
# default Windows console encoding can't print.
sys.stdout.reconfigure(encoding="utf-8", errors="replace")


def excel_cell(value):
    """Formats a value for Excel with Portuguese settings."""
    if value is None:
        return ""
    if isinstance(value, float):
        return f"{value:.2f}".replace(".", ",")
    if isinstance(value, str):
        return value.replace("​", "")
    return value


def write_csv(path, header, rows):
    # utf-8-sig adds a BOM so Excel detects UTF-8; ';' because PT Excel uses ',' for decimals
    with open(path, "w", newline="", encoding="utf-8-sig") as f:
        w = csv.writer(f, delimiter=";")
        w.writerow(header)
        w.writerows([excel_cell(v) for v in row] for row in rows)
    print(f"Saved {len(rows)} rows -> {path}")


def complete_runs(conn) -> list[str]:
    """Run ids oldest -> newest, ignoring runs far smaller than the biggest
    one (a crashed/partial run would make half the catalogue look 'gone')."""
    rows = conn.execute(
        "SELECT run_id, COUNT(*) FROM price_history GROUP BY run_id ORDER BY run_id"
    ).fetchall()
    if not rows:
        return []
    biggest = max(n for _, n in rows)
    return [run for run, n in rows if n >= 0.8 * biggest]


def pick_run(runs: list[str], prefix: str) -> str:
    matches = [r for r in runs if r.startswith(prefix)]
    if not matches:
        sys.exit(f"No complete run matches '{prefix}'. Available: {', '.join(runs)}")
    return matches[-1]


def resolve_runs(conn, old: str | None, new: str | None) -> tuple[str, str]:
    runs = complete_runs(conn)
    if old or new:
        if not (old and new):
            sys.exit("Pass both --old and --new, or neither.")
        return pick_run(runs, old), pick_run(runs, new)
    if len(runs) < 2:
        sys.exit("Need at least two complete runs to compare. Run main.py again later.")
    return runs[-2], runs[-1]


def short(text, width):
    text = text or ""
    return text if len(text) <= width else text[: width - 1] + "…"


def price_changes(conn, old, new, direction, min_pct, limit, csv_path=None):
    cmp_, order = ("<", "ASC") if direction == "drops" else (">", "DESC")
    rows = conn.execute(f"""
        SELECT n.product_id, n.name, n.brand, n.category, o.price, n.price,
               (n.price - o.price) * 100.0 / o.price AS pct, n.on_promo, n.url
        FROM price_history n
        JOIN price_history o ON o.product_id = n.product_id AND o.run_id = ?
        WHERE n.run_id = ? AND o.price > 0 AND n.price {cmp_} o.price
          AND ABS((n.price - o.price) * 100.0 / o.price) >= ?
        ORDER BY pct {order} LIMIT ?
    """, (old, new, min_pct, limit)).fetchall()

    if csv_path:
        write_csv(csv_path, ["product_id", "name", "brand", "category", "old_price",
                             "new_price", "pct_change", "on_promo", "url"], rows)
        return
    print(f"Price {direction}: {old} -> {new}\n")
    if not rows:
        print("Nothing matched.")
    for _pid, name, brand, _cat, p_old, p_new, pct, promo, _url in rows:
        flag = " [promo]" if promo else ""
        print(f"{pct:+6.1f}%  {p_old:7.2f} -> {p_new:7.2f}  {short(name, 48)} ({short(brand, 18)}){flag}")


def appeared_or_vanished(conn, old, new, which, limit, csv_path=None):
    # 'new': in the new run but not the old one. 'gone': the reverse.
    here, there = (new, old) if which == "new" else (old, new)
    rows = conn.execute("""
        SELECT product_id, name, brand, price, category, url FROM price_history
        WHERE run_id = ?
          AND product_id NOT IN (SELECT product_id FROM price_history
                                 WHERE run_id = ? AND product_id IS NOT NULL)
        ORDER BY name LIMIT ?
    """, (here, there, limit)).fetchall()

    if csv_path:
        write_csv(csv_path, ["product_id", "name", "brand", "price", "category", "url"], rows)
        return
    print(f"Products {'new in' if which == 'new' else 'gone from'} {new}  (vs {old}): showing {len(rows)}\n")
    for _pid, name, brand, price, category, _url in rows:
        print(f"{price:7.2f}  {short(name, 48)} ({short(brand, 18)})  {short(category, 30)}")


def history(conn, query, csv_path=None):
    matches = conn.execute("""
        SELECT product_id, name, brand FROM price_history
        WHERE product_id = ? OR name LIKE ?
        GROUP BY product_id ORDER BY name LIMIT 15
    """, (query, f"%{query}%")).fetchall()
    if not matches:
        sys.exit(f"No product matches '{query}'.")
    if len(matches) > 1:
        print("Several products match, pass one of these ids:\n")
        for pid, name, brand in matches:
            print(f"  {pid:>10}  {short(name, 55)} ({short(brand, 18)})")
        return
    pid, name, brand = matches[0]
    rows = conn.execute(
        "SELECT run_id, price, original_price, on_promo FROM price_history "
        "WHERE product_id = ? ORDER BY run_id", (pid,)
    ).fetchall()

    if csv_path:
        write_csv(csv_path, ["run_id", "price", "original_price", "on_promo"], rows)
        return
    print(f"{name} ({brand})  id={pid}\n")
    prev = None
    for run, price, original, promo in rows:
        delta = "" if prev is None or price == prev else f"  ({price - prev:+.2f})"
        promo_txt = f"  promo, was {original:.2f}" if promo and original else ""
        print(f"{run[:19]:19}  {price:7.2f}{delta}{promo_txt}")
        prev = price


def export_run(conn, run, csv_path):
    cur = conn.execute(
        "SELECT * FROM price_history WHERE run_id = ? ORDER BY category, name", (run,))
    header = [d[0] for d in cur.description]
    write_csv(csv_path, header, cur.fetchall())


def main():
    ap = argparse.ArgumentParser(description="Price report for prices.db")
    ap.add_argument("--db", default=DB_PATH)
    sub = ap.add_subparsers(dest="cmd", required=True)
    for cmd in ("drops", "rises", "new", "gone"):
        p = sub.add_parser(cmd)
        p.add_argument("--old")
        p.add_argument("--new")
        p.add_argument("--limit", type=int, help="max rows (default 20, or all with --csv)")
        p.add_argument("--csv", metavar="FILE", help="save to a CSV file for Excel")
        if cmd in ("drops", "rises"):
            p.add_argument("--min-pct", type=float, default=0.0)
    h = sub.add_parser("history")
    h.add_argument("query", help="product id, or part of the name")
    h.add_argument("--csv", metavar="FILE", help="save to a CSV file for Excel")
    e = sub.add_parser("export", help="save a whole run to CSV")
    e.add_argument("--run", help="run id prefix (default: latest complete run)")
    e.add_argument("--csv", metavar="FILE", required=True)
    args = ap.parse_args()

    conn = sqlite3.connect(args.db)
    if args.cmd == "history":
        history(conn, args.query, args.csv)
        return
    if args.cmd == "export":
        runs = complete_runs(conn)
        if not runs:
            sys.exit("No runs in the database yet.")
        export_run(conn, pick_run(runs, args.run) if args.run else runs[-1], args.csv)
        return

    limit = args.limit
    if limit is None:
        limit = -1 if args.csv else 20  # SQLite: LIMIT -1 means no limit
    old, new = resolve_runs(conn, args.old, args.new)
    if args.cmd in ("drops", "rises"):
        price_changes(conn, old, new, args.cmd, args.min_pct, limit, args.csv)
    else:
        appeared_or_vanished(conn, old, new, args.cmd, limit, args.csv)


if __name__ == "__main__":
    main()
