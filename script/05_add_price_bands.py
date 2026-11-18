import sys
import duckdb
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(__file__).resolve().parent.parent
DB = ROOT / "data" / "processed" / "airbnb.duckdb"
OUT = ROOT / "data" / "processed" / "powerbi" / "dim_listing.csv"

con = duckdb.connect(str(DB))

# Allow safe re-running: drop the new columns first if they already exist
cols = [r[0] for r in con.execute("DESCRIBE dim_listing").fetchall()]
excl = [c for c in ("price_vs_city_median", "price_band") if c in cols]
star = "d.*" + (f" EXCLUDE ({', '.join(excl)})" if excl else "")

con.execute(f"""
CREATE OR REPLACE TABLE dim_listing_new AS
WITH med AS (
    SELECT city, median(price_for_analysis) AS city_median
    FROM dim_listing GROUP BY city
)
SELECT {star},
    ROUND(d.price_for_analysis / m.city_median, 4) AS price_vs_city_median,
    CASE WHEN d.price_for_analysis IS NULL THEN NULL
         WHEN d.price_for_analysis / m.city_median < 0.5 THEN '1 Under 50% of city median'
         WHEN d.price_for_analysis / m.city_median < 0.8 THEN '2 50-80%'
         WHEN d.price_for_analysis / m.city_median < 1.2 THEN '3 80-120%'
         WHEN d.price_for_analysis / m.city_median < 2   THEN '4 120-200%'
         WHEN d.price_for_analysis / m.city_median < 5   THEN '5 200-500%'
         ELSE '6 Over 500%' END AS price_band
FROM dim_listing d JOIN med m ON d.city = m.city
""")
con.execute("DROP TABLE dim_listing")
con.execute("ALTER TABLE dim_listing_new RENAME TO dim_listing")

rows = con.execute("SELECT COUNT(*) FROM dim_listing").fetchall()[0][0]
priced = con.execute("SELECT COUNT(price_band) FROM dim_listing").fetchall()[0][0]
print(f"Rows: {rows:,} (expect 279,712) | rows with a price band: {priced:,} (expect 279,599)")

print("\nPrice bands (all cities):")
for b, n in con.execute("SELECT price_band, COUNT(*) FROM dim_listing GROUP BY 1 ORDER BY 1").fetchall():
    print(f"  {b}: {n:,}")

print("\nPrice index by room type, Paris only (check against Power BI later):")
for rt, v in con.execute("""SELECT room_type, ROUND(median(price_vs_city_median) * 100, 1)
                            FROM dim_listing WHERE city = 'Paris' GROUP BY 1 ORDER BY 1""").fetchall():
    print(f"  {rt}: {v}")

path = OUT.as_posix()
con.execute(f"COPY (SELECT * FROM dim_listing) TO '{path}' (HEADER, DELIMITER ',')")
con.close()
print("\nRe-exported", OUT)
