# Airbnb Market Intelligence: Listing Insights Dashboard (Track A: Data Analytics)
AnalystLab Africa Experience Lab, Week 1 | Author: Adejumoke Awolu |(https://github.com/jummypet/airbnb-market-intelligence)

## Purpose
A four-page Power BI dashboard that lets stakeholders explore Airbnb listing distribution, advertised pricing,
property and room types, host indicators and historical review activity across 10 cities.
It answers the business questions in the assignment brief (questions 1 to 8).

## Data
- Listings.csv: 279,712 listings, 33 columns | Reviews.csv: 5,373,143 review records, 4 columns
- Two data dictionaries. The raw data is not included in this repository because of its size.
- Dataset: Airbnb Listings and Reviews Dataset supplied by AnalystLab Africa.

## Key assumptions
- Prices are advertised prices in each city's local currency. There is no currency field, so the currency is
  assumed from the city's country (EUR, USD, AUD, BRL, TRY, MXN, THB, ZAR, HKD). No conversion was applied.
- 113 listings with price 0 are excluded from price measures only.
- Missing values are not imputed; coverage is reported.
- Duplicate review_id values (160) are kept and flagged.

## Project structure

## Tools
Python (pandas, DuckDB), SQL, Power BI Desktop, DAX, VS Code, Git/GitHub. 

## How to reproduce
1. Install Python and run: `pip install pandas duckdb`
2. Place the four supplied files in `data/raw/` with the original names.
3. Run the scripts in order from the project folder:
   - `python script/01_load_and_inspect.py` (loads raw tables, repairs encoding)
   - `python script/02_data_quality.py` (data-quality checks)
   - `python script/03_build_model.py` (clean model and Power BI input files)
   - `python script/04_analysis.py` (analysis of the business questions)
   - `python script/05_add_price_bands.py` (currency-free price columns; re-exports dim_listing.csv)
   - `python script/06_validation.py` (independent validation values)
4. Open `dashboard/airbnb_market_dashboard.pbix` in Power BI Desktop. If prompted, update the file paths under
   **File > Options and settings > Data source settings > Change source** to your `data/processed/powerbi/` folder.

## Data model
dim_city 1-to-many dim_listing 1-to-many fact_review_monthly many-to-1 dim_date (single-direction filters).

## Dashboard pages
1. Market Overview | 2. Pricing and Property | 3. Host Performance | 4. Review Activity and Scores
Filters for city, room type and property group are synced across pages. A currency-safe design is used: price
measures show blank unless one currency is selected; cross-city price comparison uses a currency-free Price Index.

## Validation
16 independent checks and 5 filter-response tests against the raw tables (docs/validation_evidence.md).

## Deliverables
Dashboard (.pbix), scripts, data-quality assessment, KPI definition sheet, screenshots, validation evidence,
executive summary, README.

## Limitations
Advertised price is not revenue. Review records are not bookings, occupancy or satisfaction. There is no review
text, so no sentiment analysis. Currency is assumed. 2021 is partial. Host and rating fields have incomplete
coverage.

## Contribution and integration
This dashboard was built by the author. It does not use outputs from other tracks. Definitions of listing count,
advertised price, room type, property type, host indicators, review count and ratings follow the assignment brief.
if (Test-Path docs\README.md) { Move-Item docs\README.md README.md }
Add-Content README.md "`n## Licence`nCode and documentation are released under the MIT Licence (see LICENSE). The Airbnb dataset is not covered by this licence and is not included."