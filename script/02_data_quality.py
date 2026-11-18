import sys
import duckdb
import pandas as pd
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
pd.set_option("display.width", 250)
pd.set_option("display.max_columns", 50)

ROOT = Path(__file__).resolve().parent.parent
DB = ROOT / "data" / "processed" / "airbnb.duckdb"
con = duckdb.connect(str(DB), read_only=True)

def show(title, sql):
    print(f"\n=== {title} ===")
    print(con.execute(sql).df().to_string(index=False))

# ---------- 1. Listings primary key ----------
show("1. LISTING_ID UNIQUENESS", """
    SELECT COUNT(*) AS total_rows,
           COUNT(DISTINCT listing_id) AS distinct_listing_ids,
           COUNT(*) - COUNT(listing_id) AS null_listing_ids
    FROM raw_listings
""")

# ---------- 2. Reviews: duplicate review_id ----------
show("2a. REVIEW_ID UNIQUENESS", """
    SELECT COUNT(*) AS total_rows,
           COUNT(DISTINCT review_id) AS distinct_review_ids,
           COUNT(*) - COUNT(DISTINCT review_id) AS extra_rows_from_repeats
    FROM raw_reviews
""")

show("2b. IS LISTING_ID + REVIEW_ID UNIQUE?", """
    SELECT (SELECT COUNT(*) FROM raw_reviews) AS total_rows,
           (SELECT COUNT(*) FROM (SELECT DISTINCT listing_id, review_id FROM raw_reviews)) AS distinct_pairs,
           (SELECT COUNT(*) FROM (SELECT DISTINCT * FROM raw_reviews)) AS distinct_full_rows
""")

show("2c. HOW DO THE REPEATED REVIEW_IDs DIFFER?", """
    SELECT COUNT(*) AS repeated_review_ids,
           SUM(CASE WHEN n_listings  > 1 THEN 1 ELSE 0 END) AS differ_by_listing,
           SUM(CASE WHEN n_dates     > 1 THEN 1 ELSE 0 END) AS differ_by_date,
           SUM(CASE WHEN n_reviewers > 1 THEN 1 ELSE 0 END) AS differ_by_reviewer
    FROM (
        SELECT review_id, COUNT(*) AS n_rows,
               COUNT(DISTINCT listing_id)  AS n_listings,
               COUNT(DISTINCT date)        AS n_dates,
               COUNT(DISTINCT reviewer_id) AS n_reviewers
        FROM raw_reviews GROUP BY review_id HAVING COUNT(*) > 1
    )
""")

show("2d. SAMPLE OF REPEATED REVIEW_IDs (first 10 rows)", """
    SELECT r.review_id, r.listing_id, r.date
    FROM raw_reviews r
    WHERE r.review_id IN (SELECT review_id FROM raw_reviews GROUP BY review_id HAVING COUNT(*) > 1)
    ORDER BY r.review_id, r.listing_id
    LIMIT 10
""")

# ---------- 3 & 4. Listing <-> review relationship ----------
show("3. ORPHAN REVIEWS (review points to a listing that does not exist)", """
    SELECT COUNT(*) AS orphan_reviews
    FROM raw_reviews r
    LEFT JOIN raw_listings l ON r.listing_id = l.listing_id
    WHERE l.listing_id IS NULL
""")

show("4. LISTINGS WITH / WITHOUT REVIEW RECORDS", """
    SELECT COUNT(*) AS total_listings,
           SUM(CASE WHEN EXISTS (SELECT 1 FROM raw_reviews r WHERE r.listing_id = l.listing_id) THEN 1 ELSE 0 END) AS with_reviews,
           SUM(CASE WHEN NOT EXISTS (SELECT 1 FROM raw_reviews r WHERE r.listing_id = l.listing_id) THEN 1 ELSE 0 END) AS without_reviews
    FROM raw_listings l
""")

# ---------- 5. Missing values ----------
print("\n=== 5. MISSING VALUES IN LISTINGS (sorted, worst first) ===")
total = con.execute("SELECT COUNT(*) FROM raw_listings").fetchall()[0][0]
cols = [r[0] for r in con.execute("DESCRIBE raw_listings").fetchall()]
rows = []
for c in cols:
    n = con.execute(f'SELECT COUNT(*) - COUNT("{c}") FROM raw_listings').fetchall()[0][0]
    rows.append((c, n, round(100 * n / total, 2)))
miss = pd.DataFrame(rows, columns=["column", "missing_count", "missing_pct"])
print(miss.sort_values("missing_pct", ascending=False).to_string(index=False))

# ---------- 6. Cities and categories ----------
show("6a. LISTINGS PER CITY", """
    SELECT city, COUNT(*) AS listings
    FROM raw_listings GROUP BY city ORDER BY listings DESC
""")

show("6b. CITY SPELLING CHECK (the two numbers should be equal)", """
    SELECT COUNT(DISTINCT city) AS distinct_cities,
           COUNT(DISTINCT TRIM(LOWER(city))) AS distinct_after_trim_lower
    FROM raw_listings
""")

show("6c. ROOM TYPES", """
    SELECT room_type, COUNT(*) AS listings
    FROM raw_listings GROUP BY room_type ORDER BY listings DESC
""")

show("6d. PROPERTY TYPES (count of distinct, then top 15)", """
    SELECT COUNT(DISTINCT property_type) AS distinct_property_types FROM raw_listings
""")
show("6e. TOP 15 PROPERTY TYPES", """
    SELECT property_type, COUNT(*) AS listings
    FROM raw_listings GROUP BY property_type ORDER BY listings DESC LIMIT 15
""")

show("6f. HOST RESPONSE TIME VALUES", """
    SELECT host_response_time, COUNT(*) AS listings
    FROM raw_listings GROUP BY host_response_time ORDER BY listings DESC
""")

# ---------- 7. Prices PER CITY (never mixed across currencies) ----------
show("7. PRICE CHECK PER CITY (each city in its own local currency)", """
    SELECT city,
           COUNT(*) AS listings,
           COUNT(*) - COUNT(price) AS null_price,
           SUM(CASE WHEN price <= 0 THEN 1 ELSE 0 END) AS zero_or_negative,
           MIN(price) AS min_price,
           ROUND(quantile_cont(price, 0.01)) AS p01,
           ROUND(median(price)) AS median_price,
           ROUND(quantile_cont(price, 0.99)) AS p99,
           MAX(price) AS max_price
    FROM raw_listings
    GROUP BY city ORDER BY listings DESC
""")

# ---------- 8. Numeric range checks ----------
print("\n=== 8. NUMERIC RANGE CHECKS ===")
num_cols = ["host_response_rate", "host_acceptance_rate", "host_total_listings_count",
            "latitude", "longitude", "accommodates", "bedrooms", "price",
            "minimum_nights", "maximum_nights", "review_scores_rating",
            "review_scores_accuracy", "review_scores_cleanliness", "review_scores_checkin",
            "review_scores_communication", "review_scores_location", "review_scores_value"]
rng = []
for c in num_cols:
    r = con.execute(f'SELECT MIN("{c}"), MAX("{c}"), ROUND(AVG("{c}"), 2) FROM raw_listings').fetchall()[0]
    rng.append((c, r[0], r[1], r[2]))
print(pd.DataFrame(rng, columns=["column", "min", "max", "average"]).to_string(index=False))

# ---------- 9. Reviews per year ----------
show("9. REVIEW RECORDS PER YEAR", """
    SELECT year(date) AS year, COUNT(*) AS review_records
    FROM raw_reviews GROUP BY 1 ORDER BY 1
""")

con.close()
print("\nDone.")