# Contribution Statement and Improvement Log
Author: Adejumoke Awolu | Track A: Data Analytics

## 1. Individual contribution
I completed all Track A work myself: data loading and inspection, data-quality checks, the clean data model,
the SQL/Python scripts, the four-page Power BI dashboard (DAX measures included), validation, findings,
recommendations and documentation.
Integration: this dashboard does not consume the work of any other track, and no integration is claimed.
Shared definitions (listing count, advertised price, room type, property type, host indicators, review count,
review activity, listing-level ratings) follow the assignment brief.

## 2. Improvements made after feedback and review
Feedback sources: review of each draft page against independent SQL results, and error messages from the tools.

| # | Review finding | Change made | Evidence |
|---|---|---|---|
| 1 | Total row showed a median of 150 mixing ten currencies | Median, P25 and P75 measures return blank unless one currency is selected; added a currency-free Price Index | Page 2; validation V8, V9 |
| 2 | dim_city header read as a data row | Promoted first row to headers; confirmed 10 rows | docs/validation_evidence.md, issue 3 |
| 3 | New columns not appearing after refresh | Import column count updated from 42 to 44 | issue 5 |
| 4 | PERCENTILE error; numeric columns imported as text | Explicit data type for every column in the query | issue 6 |
| 5 | Top 10 table listed all listings; volume chart included the no-records band; monthly chart showed years | Reapplied Top N and band filters; fixed the date axis; rechecked values against SQL | issue 8; Page 4 tests |