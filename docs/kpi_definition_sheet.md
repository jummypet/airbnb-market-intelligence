# KPI Sheet and Findings (Draft)
Prices are advertised prices in each city's local currency (assumed from the city's country; the source has no currency field). Zero prices (113) are excluded from price KPIs only.

## KPI 1: Listing count and share by city
Calculation: COUNT(listing_id) per city / total listings.
Result: Paris 64,690 (23.1%), New York 37,012 (13.2%), Sydney 33,630 (12.0%); Hong Kong lowest at 7,087 (2.5%). Top 4 cities = about 58% of listings.
Interpretation: Supply is concentrated in Paris; Hong Kong is a small market by listing count.
Caution: counts describe this extract, not total Airbnb inventory; count is not revenue or occupancy.

## KPI 2: Room type share
Calculation: listings per room type / listings (overall and per city).
Result: Entire place 65.1%, Private room 31.1%, Hotel room 2.1%, Shared room 1.7%. Paris 85.6% entire place; Hong Kong only 36.5% entire place and 54.9% private room.
Interpretation: Whole-home listings dominate most cities; Hong Kong has a different product mix.
Caution: share of listings, not of bookings.

## KPI 3: Property type share
Calculation: listings per property_type / listings; most common type per city.
Result: Entire apartment 138,989 (49.7%) and Private room in apartment 47,322 (16.9%) = 66.6%. Entire apartment is the top type in 9 of 10 cities (Paris 79.7%); Hong Kong's top is Private room in apartment (32.5%).
Interpretation: The market is apartment-centred.
Caution: 144 property types; the top 15 are shown and the rest grouped as Other (19,367 listings).

## KPI 4: Median advertised price by city (local currency)
Calculation: median of price_for_analysis per city (also P25, P75).
Result: Bangkok 1,100 THB | Cape Town 1,069 ZAR | Hong Kong 386 HKD | Istanbul 252 TRY | Mexico City 664 MXN | New York 99 USD | Paris 80 EUR | Rio 280 BRL | Rome 65 EUR | Sydney 120 AUD.
Mean exceeds median in every city (Rio mean 743 vs median 280), so medians are used. Same-currency comparison: Paris 80 EUR vs Rome 65 EUR (Paris about 23% higher).
Within cities: private rooms are cheaper than entire places and shared rooms are cheapest everywhere; hotel rooms are priced above entire places in 5 cities (Bangkok, Cape Town, Mexico City, New York, Paris) and below in 5. Median price rises with guest capacity in every city.
Caution: advertised prices, period not stated, currency assumed, never compared across different currencies.

## KPI 5: Neighbourhood concentration
Calculation: listings per neighbourhood / city listings (top 3 per city).
Result: Rome I Centro Storico 53.8%, Hong Kong Yau Tsim Mong 42.9%, Mexico City Cuauhtemoc 38.0%, Rio Copacabana 29.0%. New York is the most dispersed (largest neighbourhood Williamsburg 7.4%, 220 neighbourhoods).
Interpretation: Several cities have one dominant core area.
Caution: district is 86.8% missing so neighbourhood is used; neighbourhood definitions differ by city.

## KPI 6: Listing review score
Calculation: review_scores_rating (0-100) averaged with coverage; top listings need at least 20 review records.
Result: Rating available for about 67.3% of listings. City averages: Mexico City 94.8 (highest), Hong Kong 89.7 (lowest). Room type: Entire place 93.7, Hotel room 90.7. Property group: Entire guest suite 96.1 highest, Room in hotel 88.1 lowest.
Interpretation: Ratings are high and tightly clustered; differences between groups are small.
Caution: coverage varies (Istanbul 45.8% to Rome 75.6%); the rating is a listing-level aggregate, not guest sentiment.

## KPI 7: Review records per listing
Calculation: review_records per listing, grouped into bands.
Result: 0 records 30.8% (86,156 listings); 1-4 26.0%; 5-19 20.7%; 20-49 11.2%; 50-99 6.3%; 100+ 5.0% (13,926). Most reviewed listing has 891 records. Rome averages 40.3 per listing, Istanbul 7.9 (52.4% of Istanbul listings have none).
Interpretation: Review activity is concentrated in a minority of listings.
Caution: "no records" means none in this extract, not necessarily never booked.

## KPI 8: Review activity over time, and versus rating
Calculation: sum of monthly review records by year; year-on-year change; average rating by review-volume band.
Result: Records grew every year to 1,633,546 in 2019 (+43.0%), then fell to 755,324 in 2020 (-53.8%). Jan/Feb 2020 were +38.5%/+37.2% vs 2019; Mar -33.6%; Apr -91.7%; Dec -57.5%. 2021 is partial (to 1 March). Correlation of review records with rating = 0.066; listings with 1-4 records average 91.75, those with 20+ average 94.6-94.8.
Interpretation: Review activity rose steadily then dropped sharply during 2020; volume and rating are essentially unrelated.
Caution: review records are not bookings or satisfaction; the cause of the 2020 drop cannot be established from this data; the extract may under-represent older activity.

## KPI 9: Host indicators
Calculation: average host_response_rate_pct and host_acceptance_rate_pct by city, with coverage %; superhost share; listings per host.
Result: Avg response rate 83.0% (Istanbul) to 90.8% (Cape Town); acceptance 75.7% (Rio) to 90.5% (Bangkok); superhost 12.1% (Sydney) to 31.9% (Mexico City). Listings per host: Hong Kong 3.46, Paris 1.25. 53.7% of listings belong to single-listing hosts; 483 hosts with 21+ listings hold 8.3% of listings (23,315).
Interpretation: Host performance is broadly similar across cities; Hong Kong and Bangkok have more multi-listing hosts.
Caution: response coverage ranges from 36.1% (Paris) to 83.8% (Hong Kong); hosts are anonymised.

## KPI 10: What higher-priced listings have in common
Calculation: top 25% by price within each city vs the rest; compare composition.
Result: Top 25% = entire place 83.5% (vs 58.9% rest); 5+ guests 43.2% (vs 9.4%); entire house 11.9% (vs 2.3%); private room in apartment 4.5% (vs 21.1%). Median 4 guests and 2 bedrooms vs 2 and 1. Superhost share is almost identical (18.2% vs 17.9%).
Interpretation: Higher prices go with whole-home listings that sleep more guests.
Caution: an association, not a cause; guests and bedrooms are linked to each other.

## Draft findings (for the executive summary)
F1. Paris holds 23.1% of listings; Paris, New York and Sydney together hold 48.3%.
F2. The market is whole-home and apartment-based (65.1% entire places; 49.7% entire apartments); Hong Kong is the exception.
F3. Within each city prices are right-skewed: the mean exceeds the median everywhere (Rio 743 vs 280).
F4. Guest capacity is the clearest price pattern: median price rises with capacity in all 10 cities, and top-quartile listings are mostly entire places for 5+ guests.
F5. Several cities have one dominant core: Rome Centro Storico 53.8%, Hong Kong Yau Tsim Mong 42.9%.
F6. Review activity is concentrated: 30.8% of listings have no review records, only 5.0% have 100+.
F7. Review records rose to a 2019 peak, then fell 53.8% in 2020 (April 2020 was 91.7% below April 2019).
F8. Ratings are high and clustered (city medians 93-98), and nearly unrelated to review volume (r = 0.066).
F9. A small group of large hosts matters: 483 hosts (0.3%) hold 8.3% of listings.
F10. Superhost status shows no association with being in the higher-price tier (18.2% vs 17.9%).