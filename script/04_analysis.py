import sys
import duckdb
import pandas as pd
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
pd.set_option("display.width", 250)
pd.set_option("display.max_columns", 50)

ROOT = Path(__file__).resolve().parent.parent
DB = ROOT / "data" / "processed" / "airbnb.duckdb"
con = duckdb.connect(str(DB))

def show(title, sql):
    print(f"\n=== {title} ===")
    print(con.execute(sql).df().to_string(index=False))

# ---------------- Q1: listings by city ----------------
show("Q1. LISTINGS BY CITY", """
    SELECT d.city, c.currency_code, COUNT(*) AS listings,
           ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER (), 1) AS pct_of_all
    FROM dim_listing d JOIN dim_city c ON d.city = c.city
    GROUP BY d.city, c.currency_code ORDER BY listings DESC
""")

# ---------------- Q2: room types ----------------
show("Q2a. ROOM TYPES (ALL CITIES)", """
    SELECT room_type, COUNT(*) AS listings,
           ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER (), 1) AS pct
    FROM dim_listing GROUP BY room_type ORDER BY listings DESC
""")
show("Q2b. ROOM TYPE SHARE (%) WITHIN EACH CITY", """
    SELECT city,
      ROUND(100.0 * SUM(CASE WHEN room_type = 'Entire place' THEN 1 ELSE 0 END) / COUNT(*), 1) AS entire_place_pct,
      ROUND(100.0 * SUM(CASE WHEN room_type = 'Private room' THEN 1 ELSE 0 END) / COUNT(*), 1) AS private_room_pct,
      ROUND(100.0 * SUM(CASE WHEN room_type = 'Hotel room'   THEN 1 ELSE 0 END) / COUNT(*), 1) AS hotel_room_pct,
      ROUND(100.0 * SUM(CASE WHEN room_type = 'Shared room'  THEN 1 ELSE 0 END) / COUNT(*), 1) AS shared_room_pct
    FROM dim_listing GROUP BY city ORDER BY city
""")

# ---------------- Q3: property types ----------------
show("Q3a. TOP 10 PROPERTY TYPES (ALL CITIES)", """
    SELECT property_type, COUNT(*) AS listings,
           ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER (), 1) AS pct
    FROM dim_listing GROUP BY property_type ORDER BY listings DESC LIMIT 10
""")
show("Q3b. MOST COMMON PROPERTY TYPE IN EACH CITY", """
    SELECT city, property_type, listings, pct_of_city FROM (
        SELECT city, property_type, COUNT(*) AS listings,
               ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER (PARTITION BY city), 1) AS pct_of_city,
               ROW_NUMBER() OVER (PARTITION BY city ORDER BY COUNT(*) DESC) AS rn
        FROM dim_listing GROUP BY city, property_type
    ) WHERE rn = 1 ORDER BY city
""")

# ---------------- Q4: prices (local currency, per city) ----------------
show("Q4a. ADVERTISED PRICE PER CITY (LOCAL CURRENCY; zero prices excluded)", """
    SELECT d.city, c.currency_code,
           COUNT(d.price_for_analysis) AS valid_prices,
           COUNT(*) - COUNT(d.price_for_analysis) AS excluded_zero_price,
           ROUND(quantile_cont(d.price_for_analysis, 0.25)) AS p25,
           ROUND(median(d.price_for_analysis)) AS median_price,
           ROUND(quantile_cont(d.price_for_analysis, 0.75)) AS p75,
           ROUND(AVG(d.price_for_analysis)) AS avg_price_skewed_by_outliers
    FROM dim_listing d JOIN dim_city c ON d.city = c.city
    GROUP BY d.city, c.currency_code ORDER BY d.city
""")
show("Q4b. MEDIAN PRICE BY ROOM TYPE WITHIN EACH CITY (local currency)", """
    SELECT city,
      ROUND(median(CASE WHEN room_type = 'Entire place' THEN price_for_analysis END)) AS entire_place,
      ROUND(median(CASE WHEN room_type = 'Private room' THEN price_for_analysis END)) AS private_room,
      ROUND(median(CASE WHEN room_type = 'Hotel room'   THEN price_for_analysis END)) AS hotel_room,
      ROUND(median(CASE WHEN room_type = 'Shared room'  THEN price_for_analysis END)) AS shared_room
    FROM dim_listing GROUP BY city ORDER BY city
""")
show("Q4c. MEDIAN PRICE BY GUEST CAPACITY WITHIN EACH CITY (local currency)", """
    SELECT city,
      ROUND(median(CASE WHEN accommodates_band = '1'   THEN price_for_analysis END)) AS guests_1,
      ROUND(median(CASE WHEN accommodates_band = '2'   THEN price_for_analysis END)) AS guests_2,
      ROUND(median(CASE WHEN accommodates_band = '3-4' THEN price_for_analysis END)) AS guests_3_4,
      ROUND(median(CASE WHEN accommodates_band = '5-6' THEN price_for_analysis END)) AS guests_5_6,
      ROUND(median(CASE WHEN accommodates_band = '7+'  THEN price_for_analysis END)) AS guests_7_plus
    FROM dim_listing GROUP BY city ORDER BY city
""")

# ---------------- Q5: neighbourhoods ----------------
show("Q5a. NUMBER OF NEIGHBOURHOODS PER CITY", """
    SELECT city, COUNT(DISTINCT neighbourhood) AS neighbourhoods
    FROM dim_listing GROUP BY city ORDER BY city
""")
show("Q5b. TOP 3 NEIGHBOURHOODS BY LISTINGS IN EACH CITY", """
    SELECT city, neighbourhood, listings, pct_of_city FROM (
        SELECT city, neighbourhood, COUNT(*) AS listings,
               ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER (PARTITION BY city), 1) AS pct_of_city,
               ROW_NUMBER() OVER (PARTITION BY city ORDER BY COUNT(*) DESC) AS rn
        FROM dim_listing GROUP BY city, neighbourhood
    ) WHERE rn <= 3 ORDER BY city, rn
""")

# ---------------- Q6: review scores ----------------
show("Q6a. TOP 10 RATED LISTINGS (min 20 review records; ties are common at 100)", """
    SELECT listing_id, city, room_type, review_scores_rating, review_records
    FROM dim_listing
    WHERE has_rating = 1 AND review_records >= 20
    ORDER BY review_scores_rating DESC, review_records DESC LIMIT 10
""")
show("Q6b. RATING BY CITY (with coverage)", """
    SELECT city, COUNT(*) AS listings, SUM(has_rating) AS listings_with_rating,
           ROUND(100.0 * SUM(has_rating) / COUNT(*), 1) AS coverage_pct,
           ROUND(AVG(review_scores_rating), 1) AS avg_rating,
           ROUND(median(review_scores_rating), 1) AS median_rating
    FROM dim_listing GROUP BY city ORDER BY avg_rating DESC
""")
show("Q6c. RATING BY ROOM TYPE (with coverage)", """
    SELECT room_type, COUNT(*) AS listings,
           ROUND(100.0 * SUM(has_rating) / COUNT(*), 1) AS coverage_pct,
           ROUND(AVG(review_scores_rating), 1) AS avg_rating
    FROM dim_listing GROUP BY room_type ORDER BY avg_rating DESC
""")
show("Q6d. RATING BY PROPERTY GROUP (with coverage)", """
    SELECT property_group, COUNT(*) AS listings,
           ROUND(100.0 * SUM(has_rating) / COUNT(*), 1) AS coverage_pct,
           ROUND(AVG(review_scores_rating), 1) AS avg_rating
    FROM dim_listing GROUP BY property_group ORDER BY listings DESC
""")

# ---------------- Q7: reviews per listing ----------------
show("Q7a. REVIEW RECORDS PER LISTING (distribution)", """
    SELECT band, COUNT(*) AS listings, ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER (), 1) AS pct
    FROM (SELECT CASE WHEN review_records = 0 THEN '0 (no records)'
                      WHEN review_records < 5 THEN '1-4'
                      WHEN review_records < 20 THEN '5-19'
                      WHEN review_records < 50 THEN '20-49'
                      WHEN review_records < 100 THEN '50-99'
                      ELSE '100+' END AS band,
                 CASE WHEN review_records = 0 THEN 0 WHEN review_records < 5 THEN 1
                      WHEN review_records < 20 THEN 2 WHEN review_records < 50 THEN 3
                      WHEN review_records < 100 THEN 4 ELSE 5 END AS band_no
          FROM dim_listing)
    GROUP BY band, band_no ORDER BY band_no
""")
show("Q7b. TOP 10 LISTINGS BY REVIEW RECORDS", """
    SELECT listing_id, city, room_type, review_records
    FROM dim_listing ORDER BY review_records DESC LIMIT 10
""")
show("Q7c. REVIEW RECORDS BY CITY", """
    SELECT city, SUM(review_records) AS total_review_records,
           ROUND(AVG(review_records), 1) AS avg_per_listing,
           ROUND(100.0 * SUM(CASE WHEN has_review_record = 0 THEN 1 ELSE 0 END) / COUNT(*), 1) AS pct_listings_without_records
    FROM dim_listing GROUP BY city ORDER BY total_review_records DESC
""")

# ---------------- Q8: review activity over time ----------------
show("Q8a. REVIEW RECORDS PER YEAR (2021 is partial: data ends 1 March 2021)", """
    SELECT year, review_records,
           ROUND(100.0 * (review_records - LAG(review_records) OVER (ORDER BY year))
                 / LAG(review_records) OVER (ORDER BY year), 1) AS yoy_change_pct
    FROM (SELECT d.year, SUM(f.review_records) AS review_records
          FROM fact_review_monthly f JOIN dim_date d ON f.month_start = d.month_start
          GROUP BY d.year)
    ORDER BY year
""")
show("Q8b. 2019 vs 2020 BY MONTH", """
    SELECT month_number, month_name, y2019, y2020,
           ROUND(100.0 * (y2020 - y2019) / y2019, 1) AS change_pct
    FROM (SELECT d.month_number, d.month_name,
                 SUM(CASE WHEN d.year = 2019 THEN f.review_records END) AS y2019,
                 SUM(CASE WHEN d.year = 2020 THEN f.review_records END) AS y2020
          FROM fact_review_monthly f JOIN dim_date d ON f.month_start = d.month_start
          GROUP BY d.month_number, d.month_name)
    ORDER BY month_number
""")

# ---------------- Review activity vs rating ----------------
show("Q8c. REVIEW ACTIVITY vs RATING (listings with both)", """
    SELECT band, COUNT(*) AS listings, ROUND(AVG(review_scores_rating), 2) AS avg_rating,
           ROUND(median(review_scores_rating), 1) AS median_rating
    FROM (SELECT review_scores_rating,
                 CASE WHEN review_records < 5 THEN '1-4'
                      WHEN review_records < 20 THEN '5-19'
                      WHEN review_records < 50 THEN '20-49'
                      WHEN review_records < 100 THEN '50-99'
                      ELSE '100+' END AS band,
                 CASE WHEN review_records < 5 THEN 1 WHEN review_records < 20 THEN 2
                      WHEN review_records < 50 THEN 3 WHEN review_records < 100 THEN 4 ELSE 5 END AS band_no
          FROM dim_listing WHERE has_rating = 1 AND has_review_record = 1)
    GROUP BY band, band_no ORDER BY band_no
""")
show("Q8d. CORRELATION AND OVERLAP", """
    SELECT ROUND(corr(review_records, review_scores_rating), 3) AS correlation_records_vs_rating,
           SUM(CASE WHEN has_rating = 1 AND has_review_record = 0 THEN 1 ELSE 0 END) AS rating_but_no_review_records,
           SUM(CASE WHEN has_rating = 0 AND has_review_record = 1 THEN 1 ELSE 0 END) AS review_records_but_no_rating
    FROM dim_listing
""")

# ---------------- Q9: hosts ----------------
show("Q9a. HOST INDICATORS BY CITY (with coverage)", """
    SELECT city,
      ROUND(AVG(host_response_rate_pct), 1)   AS avg_response_rate_pct,
      ROUND(AVG(host_acceptance_rate_pct), 1) AS avg_acceptance_rate_pct,
      ROUND(100.0 * COUNT(host_response_rate_pct) / COUNT(*), 1)   AS response_coverage_pct,
      ROUND(100.0 * COUNT(host_acceptance_rate_pct) / COUNT(*), 1) AS acceptance_coverage_pct,
      ROUND(100.0 * SUM(CASE WHEN host_response_time = 'within an hour' THEN 1 ELSE 0 END)
            / NULLIF(SUM(CASE WHEN host_response_time <> 'No data' THEN 1 ELSE 0 END), 0), 1) AS pct_within_hour_of_known,
      ROUND(100.0 * SUM(CASE WHEN host_is_superhost = 'Yes' THEN 1 ELSE 0 END)
            / NULLIF(SUM(CASE WHEN host_is_superhost <> 'Unknown' THEN 1 ELSE 0 END), 0), 1) AS superhost_pct
    FROM dim_listing GROUP BY city ORDER BY city
""")
show("Q9b. HOSTS AND LISTINGS PER HOST (within this dataset)", """
    SELECT city, COUNT(DISTINCT host_key) AS hosts, COUNT(*) AS listings,
           ROUND(1.0 * COUNT(*) / COUNT(DISTINCT host_key), 2) AS listings_per_host
    FROM dim_listing GROUP BY city ORDER BY listings_per_host DESC
""")
show("Q9c. HOST SIZE GROUPS (all cities)", """
    WITH h AS (SELECT host_key, COUNT(*) AS n FROM dim_listing GROUP BY host_key)
    SELECT CASE WHEN n = 1 THEN '1' WHEN n BETWEEN 2 AND 5 THEN '2-5'
                WHEN n BETWEEN 6 AND 20 THEN '6-20' ELSE '21+' END AS listings_per_host,
           COUNT(*) AS hosts, SUM(n) AS listings,
           ROUND(100.0 * SUM(n) / SUM(SUM(n)) OVER (), 1) AS pct_of_listings
    FROM h GROUP BY 1 ORDER BY MIN(n)
""")

# ---------------- Q10: what do higher-priced listings have in common? ----------------
con.execute("""
CREATE OR REPLACE TEMP TABLE priced AS
WITH q AS (SELECT city, quantile_cont(price_for_analysis, 0.75) AS p75
           FROM dim_listing GROUP BY city)
SELECT d.*, CASE WHEN d.price_for_analysis >= q.p75 THEN 'Top 25%' ELSE 'Rest' END AS price_tier
FROM dim_listing d JOIN q ON d.city = q.city
WHERE d.price_for_analysis IS NOT NULL
""")

def composition(col, limit=10):
    show(f"Q10. {col.upper()}: share of 'top 25% in city' vs the rest", f"""
        SELECT {col} AS value,
          ROUND(100.0 * SUM(CASE WHEN price_tier = 'Top 25%' THEN 1 ELSE 0 END)
                / (SELECT COUNT(*) FROM priced WHERE price_tier = 'Top 25%'), 1) AS pct_of_top25,
          ROUND(100.0 * SUM(CASE WHEN price_tier = 'Rest' THEN 1 ELSE 0 END)
                / (SELECT COUNT(*) FROM priced WHERE price_tier = 'Rest'), 1) AS pct_of_rest
        FROM priced GROUP BY {col} ORDER BY pct_of_top25 DESC LIMIT {limit}
    """)

composition("room_type")
composition("accommodates_band")
composition("property_group", 8)
composition("host_is_superhost")
show("Q10. NUMERIC PROFILE OF THE TWO GROUPS", """
    SELECT price_tier, COUNT(*) AS listings,
           median(accommodates) AS median_guests, ROUND(AVG(accommodates), 2) AS avg_guests,
           median(bedrooms) AS median_bedrooms, ROUND(AVG(bedrooms), 2) AS avg_bedrooms,
           ROUND(AVG(review_scores_rating), 1) AS avg_rating
    FROM priced GROUP BY price_tier ORDER BY price_tier DESC
""")

con.close()
print("\nDone.")