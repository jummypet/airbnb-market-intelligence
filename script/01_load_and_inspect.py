import sys
import duckdb
from pathlib import Path

# Let the console print any language/characters safely
sys.stdout.reconfigure(encoding="utf-8")

# ---------- Paths (relative to the project folder) ----------
ROOT = Path(__file__).resolve().parent.parent
RAW = ROOT / "data" / "raw"
PROC = ROOT / "data" / "processed"
DB = PROC / "airbnb.duckdb"
PROC.mkdir(parents=True, exist_ok=True)

# ---------- 1. Check the files exist ----------
print("=== FILE CHECK ===")
files = ["Listings.csv", "Reviews.csv",
         "Listings_data_dictionary.csv", "Reviews_data_dictionary.csv"]
all_found = True
for f in files:
    p = RAW / f
    if p.exists():
        print(f"OK       {f}  ({p.stat().st_size / 1_000_000:.1f} MB)")
    else:
        print(f"MISSING  {f}")
        all_found = False
if not all_found:
    sys.exit("Fix the missing files above, then run again.")

# ---------- 2. Repair the encoding of Listings.csv ----------
def make_utf8_copy(src, dst):
    """Copy a file line by line; replace only invalid UTF-8 bytes."""
    bad_lines = []
    with open(src, "rb") as fin, open(dst, "wb") as fout:
        for n, line in enumerate(fin, start=1):
            try:
                text = line.decode("utf-8")
            except UnicodeDecodeError:
                text = line.decode("utf-8", errors="replace")
                bad_lines.append(n)
            fout.write(text.encode("utf-8"))
    return bad_lines

print("\n=== ENCODING CHECK: Listings.csv ===")
LISTINGS_CLEAN = PROC / "Listings_utf8.csv"
bad = make_utf8_copy(RAW / "Listings.csv", LISTINGS_CLEAN)
print(f"Lines containing invalid UTF-8 bytes (repaired): {len(bad):,}")
print("First few affected line numbers:", bad[:10])

# ---------- 3. Load CSVs into DuckDB as raw_ tables ----------
con = duckdb.connect(str(DB))

def load(table, path):
    con.execute(
        f"CREATE OR REPLACE TABLE {table} AS "
        f"SELECT * FROM read_csv('{Path(path).as_posix()}', header=true, sample_size=-1)"
    )

print("\nLoading files (the reviews file may take up to a minute)...")
load("raw_listings", LISTINGS_CLEAN)
load("raw_reviews", RAW / "Reviews.csv")
load("raw_listings_dict", RAW / "Listings_data_dictionary.csv")
load("raw_reviews_dict", RAW / "Reviews_data_dictionary.csv")

# ---------- 4. Row and column counts ----------
print("\n=== ROW AND COLUMN COUNTS ===")
for t in ["raw_listings", "raw_reviews"]:
    rows = con.execute(f"SELECT COUNT(*) FROM {t}").fetchall()[0][0]
    cols = len(con.execute(f"DESCRIBE {t}").fetchall())
    print(f"{t}: {rows:,} rows, {cols} columns")

# ---------- 5. Column names and data types ----------
for t in ["raw_listings", "raw_reviews"]:
    print(f"\n=== COLUMNS AND TYPES: {t} ===")
    df = con.execute(f"SELECT column_name, column_type FROM (DESCRIBE {t})").df()
    print(df.to_string(index=False))

# ---------- 6. Data dictionaries ----------
for t in ["raw_listings_dict", "raw_reviews_dict"]:
    print(f"\n=== DATA DICTIONARY: {t} ===")
    print(con.execute(f"SELECT * FROM {t}").df().to_string(index=False))

# ---------- 7. Review date range ----------
print("\n=== REVIEW DATE RANGE ===")
print(con.execute("SELECT MIN(date) AS first_review, MAX(date) AS last_review FROM raw_reviews").df().to_string(index=False))

con.close()
print("\nDone. Database saved at:", DB)