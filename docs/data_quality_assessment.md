# Data-Quality Notes 

## Files and sizes
- Listings.csv: 279,712 rows x 33 columns | Reviews.csv: 5,373,143 rows x 4 columns
- Listings.csv had 981 lines with invalid UTF-8 bytes; a UTF-8 copy was made (invalid bytes replaced, no rows removed). Original untouched in data/raw/.

## Keys and relationships
- listing_id: unique, no nulls (valid primary key).
- review_id: 160 values repeat (each exactly twice). The pairs differ only by listing_id (same date, same reviewer). listing_id + review_id is unique. Decision: keep all rows, flag them.
- Orphan reviews: 0. Listings with reviews: 193,556 (69.2%). Without: 86,156 (30.8%).

## Missing values (Listings)
- district 86.77% | host_response_time/rate 46.04% | host_acceptance_rate 40.43%
- review scores 32.7-32.8% | bedrooms 10.52% | host profile fields ~0.06% (165 rows)
- Decision: no imputation; keep as NULL; report coverage beside averages; use neighbourhood instead of district.

## Prices (local currency, no currency column in source)
- 113 listings with price = 0 (Paris 62, New York 28, Rio 7, Mexico City 7, Rome 6, Istanbul 2, Bangkok 1). No negatives.
- Extreme highs exist in every city (e.g. Rio max 625,216 vs p99 5,693).
- Decision: exclude price = 0 from price metrics only; keep outliers but use medians; analyse each city in its own currency; never compare raw prices across cities.

## Other value issues
- maximum_nights max = 2,147,483,647 (placeholder) -> not used.
- minimum_nights max 9,999; bedrooms max 50; accommodates min 0 -> flagged.
- host rates are fractions 0-1 -> shown as %.

## Reviews over time
- 2008-11-16 to 2021-03-01; 2021 is partial; 2008-2010 very small; 2020 lower than 2019 (cause not established by this data).

## Limits
- Advertised price is not revenue; review records are not occupancy or satisfaction.