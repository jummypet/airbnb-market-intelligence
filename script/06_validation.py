import sys
import duckdb
from pathlib import Path
from datetime import date

sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(__file__).resolve().parent.parent
DB = ROOT / "data" / "processed" / "airbnb.duckdb"
OUT = ROOT / "docs" / "validation_evidence.md"
OUT.parent.mkdir(parents=True, exist_ok=True)
con = duckdb.connect(str(DB), read_only=True)

def one(sql):
    return con.execute(sql).fetchall()[0][0]

def fmt(v, d=0):
    return f"{v:,.{d}f}"

JOIN = "FROM raw_reviews r JOIN raw_listings l ON r.listing_id = l.listing_id"

# (id, what, where to read it in the dashboard, SQL on RAW tables, decimals)
checks = [
 ("V1", "Total listings", "Page 1 card Total Listings (no filters)", "SELECT COUNT(*) FROM raw_listings", 0),
 ("V2", "Cities represented", "Page 1 card Cities Represented", "SELECT COUNT(DISTINCT city) FROM raw_listings", 0),
 ("V3", "Total review records", "Page 4 card Total Review Records (no filters)", "SELECT COUNT(*) FROM raw_reviews", 0),
 ("V4", "% of listings without review records", "Page 4 card (percent)",
  "SELECT ROUND(100.0 * (SELECT COUNT(*) FROM raw_listings WHERE listing_id NOT IN (SELECT DISTINCT listing_id FROM raw_reviews)) / (SELECT COUNT(*) FROM raw_listings), 1)", 1),
 ("V5", "Paris listings", "Page 1: City = Paris, card Total Listings", "SELECT COUNT(*) FROM raw_listings WHERE city = 'Paris'", 0),
 ("V6", "Hong Kong listings", "Page 1: City = Hong Kong, card Total Listings", "SELECT COUNT(*) FROM raw_listings WHERE city = 'Hong Kong'", 0),
 ("V7", "Hotel room listings", "Page 1: Room type = Hotel room, card Total Listings", "SELECT COUNT(*) FROM raw_listings WHERE room_type = 'Hotel room'", 0),
 ("V8", "Median advertised price, Paris (EUR, price > 0)", "Page 2: City = Paris, card Median Advertised Price",
  "SELECT median(price) FROM raw_listings WHERE city = 'Paris' AND price > 0", 0),
 ("V9", "Median advertised price, Hong Kong (HKD, price > 0)", "Page 2: City = Hong Kong, card Median Advertised Price",
  "SELECT median(price) FROM raw_listings WHERE city = 'Hong Kong' AND price > 0", 0),
 ("V10", "Review records, Paris", "Page 4: City = Paris, card Total Review Records",
  f"SELECT COUNT(*) {JOIN} WHERE l.city = 'Paris'", 0),
 ("V11", "Review records dated 2020", "Page 4 year chart, hover over 2020",
  "SELECT COUNT(*) FROM raw_reviews WHERE year(date) = 2020", 0),
 ("V12", "Distinct hosts", "Page 3 card Hosts (no filters)", "SELECT COUNT(DISTINCT host_id) FROM raw_listings", 0),
 ("V13", "Average host response rate %, Hong Kong", "Page 3: City = Hong Kong, Avg Response Rate %",
  "SELECT ROUND(AVG(host_response_rate) * 100, 1) FROM raw_listings WHERE city = 'Hong Kong'", 1),
 ("V14", "Average listing rating (all listings with a rating)", "Page 4 card Average Rating",
  "SELECT ROUND(AVG(review_scores_rating), 2) FROM raw_listings", 2),
 ("V15", "Average review records per listing, Mexico City", "Page 4 city table, Mexico City row",
  f"SELECT ROUND(1.0 * (SELECT COUNT(*) {JOIN} WHERE l.city = 'Mexico City') / (SELECT COUNT(*) FROM raw_listings WHERE city = 'Mexico City'), 1)", 1),
 ("V16", "Listings with a valid price (price > 0)", "Page 2 card Listings with Valid Price (no filters)",
  "SELECT COUNT(*) FROM raw_listings WHERE price > 0", 0),
]

filters = [
 ("F1", "City = Paris; Room type = Private room", "l.city = 'Paris' AND l.room_type = 'Private room'"),
 ("F2", "City = Paris and Rome", "l.city IN ('Paris', 'Rome')"),
 ("F3", "City = New York; Room type = Hotel room", "l.city = 'New York' AND l.room_type = 'Hotel room'"),
 ("F4", "City = Rome; Property group = Entire apartment", "l.city = 'Rome' AND l.property_type = 'Entire apartment'"),
 ("F5", "City = Sydney; Room type = Entire place; Property group = Entire house",
  "l.city = 'Sydney' AND l.room_type = 'Entire place' AND l.property_type = 'Entire house'"),
]

L = []
L += ["# Validation Evidence", "",
      f"Date generated: {date.today()}  |  Project: Airbnb Market Intelligence (Track A)", "",
      "## 1. Method",
      "Each value below was recomputed with SQL directly on the RAW tables (raw_listings, raw_reviews), "
      "independently of the cleaned model and of Power BI. The dashboard value was then read from the Power BI report "
      "and compared. Counts must match exactly; medians must match exactly; averages must match at the displayed decimals.", "",
      "## 2. Independent calculation checks", "",
      "| ID | Check | Where to read it in the dashboard | Source value (SQL on raw) | Dashboard value | Match? |",
      "|---|---|---|---|---|---|"]
print("=== SOURCE VALUES (independent, from raw tables) ===")
for cid, what, where, sql, d in checks:
    v = one(sql)
    L.append(f"| {cid} | {what} | {where} | {fmt(v, d)} |  |  |")
    print(f"{cid}: {what} = {fmt(v, d)}")

L += ["", "## 3. Filter-response tests",
      "Set the slicers on Page 1 (they are synced to Page 4). Read Total Listings on Page 1 and Total Review Records on Page 4.", "",
      "| ID | Filters selected | Expected listings | Dashboard listings | Expected review records | Dashboard review records |",
      "|---|---|---|---|---|---|---|"]
print("\n=== FILTER TESTS (expected values) ===")
for fid, label, cond in filters:
    nl = one(f"SELECT COUNT(*) FROM raw_listings l WHERE {cond}")
    nr = one(f"SELECT COUNT(*) {JOIN} WHERE {cond}")
    L.append(f"| {fid} | {label} | {fmt(nl)} | | {fmt(nr)} | | |")
    print(f"{fid}: {label}: listings {fmt(nl)}, review records {fmt(nr)}")

L += ["", "## 4. Behaviour checks (tick when confirmed)",
      "- [ ] Clearing all filters returns Total Listings 279,712 and Total Review Records 5,373,143",
      "- [ ] City, Room type and Property group slicers are synced across all four pages",
      "- [ ] Sum of the city rows in the city tables equals the card totals",
      "- [ ] Median price shows blank (not a number) when more than one currency is selected",
      "- [ ] Selecting a bar in one chart cross-filters the other charts",
      "- [ ] Top 10 most reviewed listings table shows exactly 10 rows (first row 891 records, listing 17222007)", "",
      "## 5. Data-preparation reconciliation",
      "Automatic checks in script/03_build_model.py compared the model to the raw tables "
      "(row counts, review totals, zero-price flags, orphan checks). See docs/stage4_output.txt.", "",
      "## 6. Discrepancies found and how they were resolved", "",
      "| # | Issue | How it was found | Cause | Resolution |",
      "|---|---|---|---|---|",
      "| 1 | Listings.csv failed to load | DuckDB error at line 11,877 | 981 lines with invalid UTF-8 bytes | Repaired UTF-8 copy created; no rows removed; counts reconciled to the brief |",
      "| 2 | 160 repeated review_id values | Key check | Same review_id used for two different listings (same date and reviewer) | All rows kept; listing_id + review_id is unique; affected listings flagged |",
      "| 3 | dim_city header shown as a data row (Column3) | First dashboard test table | Power BI could not detect a header in an all-text file | First row promoted to headers; 10 rows confirmed |",
      "| 4 | Median shown on the Total row (150) | First dashboard test table | Median across ten currencies is meaningless | Measure returns blank unless exactly one currency is selected |",
      "| 5 | New columns missing after refresh | Field search in Power BI | Import step fixed at 42 columns | Updated import to 44 columns |",
      "| 6 | PERCENTILE error and text-typed numbers | Power BI error message | Column types lost after the import change | Explicit data types set for every column |",
      "| 7 | Guest capacity chart missing bars | Visual review against SQL results | accommodates_band typed as number | Column typed as text; five bars confirmed |",
      "| 8 | Top 10 table listed every listing; volume chart included the no-records band; monthly chart showed years | Visual review against SQL results | Visual filters or axis settings not applied | Filters and axis re-applied; values re-checked against SQL |", "",
      "## 7. Limitations that affect interpretation",
      "- Prices are advertised prices; the source has no currency field, so each city's currency is an assumption from its country. No conversion was done and prices are never compared across currencies.",
      "- Advertised price is not revenue; review records are not bookings, occupancy or guest satisfaction; no review text exists, so no sentiment analysis.",
      "- 113 listings with a price of 0 are excluded from price measures only.",
      "- Review scores exist for about 67% of listings; host response and acceptance data are missing for 40-46% (coverage varies by city and is shown beside averages).",
      "- 2021 contains data only to 1 March 2021; March 2021 is excluded from the monthly chart.",
      "- District is 87% missing, so neighbourhood is used; neighbourhood definitions differ by city.",
      "- Host IDs are anonymised; reviewer IDs are not exported.",
      "- The listings extract is a snapshot; counts describe this extract, not total Airbnb inventory.", "",
      "## 8. Screenshot evidence (dashboard/screenshots)",
      "page1_market_overview.png, page1_filtered_paris.png, page2_pricing_all.png, page2_pricing_paris.png, "
      "page3_host_all.png, page3_host_hongkong.png, page4_reviews_all.png, page4_reviews_paris.png "
      "(+ filter-test screenshots)."]

OUT.write_text("\n".join(L), encoding="utf-8")
con.close()
print("\nWrote", OUT)