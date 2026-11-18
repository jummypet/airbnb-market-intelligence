import sys
import duckdb
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

ROOT = Path(__file__).resolve().parent.parent
DB = ROOT / "data" / "processed" / "airbnb.duckdb"
OUT = ROOT / "data" / "processed" / "powerbi"
OUT.mkdir(parents=True, exist_ok=True)

con = duckdb.connect(str(DB))   # write mode

def yn(col):
    """Turn true/false into Yes/No/Unknown labels (slicer-friendly)."""
    return f"CASE WHEN l.{col} IS NULL THEN 'Unknown' WHEN l.{col} THEN 'Yes' ELSE 'No' END"

# ------------------------------------------------------------------
# 1. dim_city  (currency lookup = documented assumption, no conversion)
# ------------------------------------------------------------------
con.execute("""
CREATE OR REPLACE TABLE dim_city AS
SELECT * FROM (VALUES
    ('Paris',          'France',       'EUR'),
    ('New York',       'United States','USD'),
    ('Sydney',         'Australia',    'AUD'),
    ('Rome',           'Italy',        'EUR'),
    ('Rio de Janeiro', 'Brazil',       'BRL'),
    ('Istanbul',       'Turkey',       'TRY'),
    ('Mexico City',    'Mexico',       'MXN'),
    ('Bangkok',        'Thailand',     'THB'),
    ('Cape Town',      'South Africa', 'ZAR'),
    ('Hong Kong',      'Hong Kong',    'HKD')
) AS t(city, country, currency_code)
""")

# ------------------------------------------------------------------
# 2. dim_listing  (one row per listing, cleaned + flagged)
# ------------------------------------------------------------------
con.execute(f"""
CREATE OR REPLACE TABLE dim_listing AS
WITH top_props AS (
    SELECT property_type FROM raw_listings
    GROUP BY property_type ORDER BY COUNT(*) DESC LIMIT 15
),
city_p99 AS (
    SELECT city, quantile_cont(price, 0.99) AS p99
    FROM raw_listings WHERE price > 0 GROUP BY city
),
rev AS (
    SELECT listing_id, COUNT(*) AS review_records,
           MIN(date) AS first_review_date, MAX(date) AS last_review_date
    FROM raw_reviews GROUP BY listing_id
),
dup AS (
    SELECT DISTINCT listing_id FROM raw_reviews
    WHERE review_id IN (SELECT review_id FROM raw_reviews GROUP BY review_id HAVING COUNT(*) > 1)
),
hosts AS (
    SELECT host_id, DENSE_RANK() OVER (ORDER BY host_id) AS host_key
    FROM (SELECT DISTINCT host_id FROM raw_listings)
)
SELECT
    l.listing_id,
    h.host_key,
    l.host_since,
    COALESCE(l.host_response_time, 'No data')        AS host_response_time,
    ROUND(l.host_response_rate * 100, 1)             AS host_response_rate_pct,
    ROUND(l.host_acceptance_rate * 100, 1)           AS host_acceptance_rate_pct,
    {yn('host_is_superhost')}                        AS host_is_superhost,
    l.host_total_listings_count,
    {yn('host_has_profile_pic')}                     AS host_has_profile_pic,
    {yn('host_identity_verified')}                   AS host_identity_verified,
    l.city,
    l.neighbourhood,
    l.latitude,
    l.longitude,
    l.property_type,
    CASE WHEN l.property_type IN (SELECT property_type FROM top_props)
         THEN l.property_type ELSE 'Other' END       AS property_group,
    l.room_type,
    l.accommodates,
    CASE WHEN l.accommodates = 0 THEN 'Invalid (0)'
         WHEN l.accommodates = 1 THEN '1'
         WHEN l.accommodates = 2 THEN '2'
         WHEN l.accommodates BETWEEN 3 AND 4 THEN '3-4'
         WHEN l.accommodates BETWEEN 5 AND 6 THEN '5-6'
         ELSE '7+' END                               AS accommodates_band,
    l.bedrooms,
    l.price                                          AS price_local,
    CASE WHEN l.price > 0 THEN l.price END           AS price_for_analysis,
    l.minimum_nights,
    l.review_scores_rating,
    l.review_scores_accuracy,
    l.review_scores_cleanliness,
    l.review_scores_checkin,
    l.review_scores_communication,
    l.review_scores_location,
    l.review_scores_value,
    {yn('instant_bookable')}                         AS instant_bookable,
    COALESCE(rev.review_records, 0)                  AS review_records,
    rev.first_review_date,
    rev.last_review_date,
    CASE WHEN rev.listing_id IS NOT NULL THEN 1 ELSE 0 END      AS has_review_record,
    CASE WHEN l.review_scores_rating IS NOT NULL THEN 1 ELSE 0 END AS has_rating,
    CASE WHEN dup.listing_id IS NOT NULL THEN 1 ELSE 0 END      AS has_shared_review_id,
    CASE WHEN l.price <= 0 THEN 1 ELSE 0 END                    AS flag_zero_price,
    CASE WHEN l.price > cp.p99 THEN 1 ELSE 0 END                AS flag_price_above_city_p99,
    CASE WHEN l.accommodates = 0 THEN 1 ELSE 0 END              AS flag_accommodates_zero,
    CASE WHEN l.minimum_nights > 365 THEN 1 ELSE 0 END          AS flag_min_nights_over_365,
    CASE WHEN l.bedrooms >= 20 THEN 1 ELSE 0 END                AS flag_bedrooms_20_plus
FROM raw_listings l
LEFT JOIN hosts h    ON l.host_id = h.host_id
LEFT JOIN city_p99 cp ON l.city = cp.city
LEFT JOIN rev        ON l.listing_id = rev.listing_id
LEFT JOIN dup        ON l.listing_id = dup.listing_id
""")

# ------------------------------------------------------------------
# 3. fact_review_monthly
# ------------------------------------------------------------------
con.execute("""
CREATE OR REPLACE TABLE fact_review_monthly AS
SELECT listing_id,
       CAST(date_trunc('month', date) AS DATE) AS month_start,
       COUNT(*) AS review_records
FROM raw_reviews
GROUP BY listing_id, month_start
""")

# ------------------------------------------------------------------
# 4. dim_date (monthly)
# ------------------------------------------------------------------
con.execute("""
CREATE OR REPLACE TABLE dim_date AS
SELECT month_start,
       year(month_start)                    AS year,
       month(month_start)                   AS month_number,
       strftime(month_start, '%b')          AS month_name,
       strftime(month_start, '%Y-%m')       AS year_month,
       CASE WHEN year(month_start) = 2021 THEN 1 ELSE 0 END          AS is_partial_year,
       CASE WHEN month_start >= DATE '2021-03-01' THEN 1 ELSE 0 END  AS is_partial_month
FROM (SELECT CAST(range AS DATE) AS month_start
      FROM range(DATE '2008-11-01', DATE '2021-04-01', INTERVAL 1 MONTH))
""")

# ------------------------------------------------------------------
# 5. dq_duplicate_review_ids (evidence table, no reviewer id)
# ------------------------------------------------------------------
con.execute("""
CREATE OR REPLACE TABLE dq_duplicate_review_ids AS
SELECT review_id, listing_id, date AS review_date
FROM raw_reviews
WHERE review_id IN (SELECT review_id FROM raw_reviews GROUP BY review_id HAVING COUNT(*) > 1)
ORDER BY review_id, listing_id
""")

# ------------------------------------------------------------------
# 6. Automatic reconciliation checks (compared against RAW tables)
# ------------------------------------------------------------------
def one(sql):
    return con.execute(sql).fetchall()[0][0]

checks = [
    ("Listing rows match raw",
     one("SELECT COUNT(*) FROM dim_listing"), one("SELECT COUNT(*) FROM raw_listings")),
    ("listing_id still unique",
     one("SELECT COUNT(DISTINCT listing_id) FROM dim_listing"), one("SELECT COUNT(*) FROM dim_listing")),
    ("Review totals in dim_listing match raw",
     one("SELECT SUM(review_records) FROM dim_listing"), one("SELECT COUNT(*) FROM raw_reviews")),
    ("Review totals in monthly fact match raw",
     one("SELECT SUM(review_records) FROM fact_review_monthly"), one("SELECT COUNT(*) FROM raw_reviews")),
    ("Listings with review records match raw",
     one("SELECT SUM(has_review_record) FROM dim_listing"),
     one("SELECT COUNT(DISTINCT listing_id) FROM raw_reviews")),
    ("Zero-price flags match raw",
     one("SELECT SUM(flag_zero_price) FROM dim_listing"),
     one("SELECT COUNT(*) FROM raw_listings WHERE price <= 0")),
    ("Cities in dim_city",
     one("SELECT COUNT(*) FROM dim_city"), 10),
    ("Listings with no matching city row",
     one("SELECT COUNT(*) FROM dim_listing l LEFT JOIN dim_city c ON l.city = c.city WHERE c.city IS NULL"), 0),
    ("Monthly fact rows with no matching listing",
     one("SELECT COUNT(*) FROM fact_review_monthly f LEFT JOIN dim_listing l ON f.listing_id = l.listing_id WHERE l.listing_id IS NULL"), 0),
    ("Monthly fact rows with no matching month",
     one("SELECT COUNT(*) FROM fact_review_monthly f LEFT JOIN dim_date d ON f.month_start = d.month_start WHERE d.month_start IS NULL"), 0),
    ("Rows in duplicate-ID evidence table",
     one("SELECT COUNT(*) FROM dq_duplicate_review_ids"), 320),
]

print("=== RECONCILIATION CHECKS ===")
all_pass = True
for name, actual, expected in checks:
    ok = (actual == expected)
    all_pass = all_pass and ok
    print(f"{'PASS' if ok else 'FAIL'}  {name}: actual={actual:,} expected={expected:,}")
print("\nALL CHECKS PASSED" if all_pass else "\nSOME CHECKS FAILED - send me this output")

# ------------------------------------------------------------------
# 7. Export to CSV for Power BI
# ------------------------------------------------------------------
print("\n=== EXPORTING TO", OUT, "===")
for t in ["dim_city", "dim_listing", "fact_review_monthly", "dim_date", "dq_duplicate_review_ids"]:
    path = (OUT / f"{t}.csv").as_posix()
    con.execute(f"COPY (SELECT * FROM {t}) TO '{path}' (HEADER, DELIMITER ',')")
    n = one(f"SELECT COUNT(*) FROM {t}")
    mb = (OUT / f"{t}.csv").stat().st_size / 1_000_000
    print(f"{t}.csv: {n:,} rows, {mb:.1f} MB")

con.close()
print("\nDone.")