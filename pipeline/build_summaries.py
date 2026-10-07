"""Build the operations summaries from the raw trip files.

Reads every row in data/raw/ with DuckDB and writes small CSV files to data/summaries/.
The dashboard reads only those summaries, never the raw rows.

Run it from the project root:

    uv run python pipeline/build_summaries.py
"""

import json
from email.utils import parsedate_to_datetime
from pathlib import Path

import duckdb

ROOT = Path(__file__).resolve().parent.parent
RAW_DIR = ROOT / "data" / "raw"
ZONES = ROOT / "data" / "reference" / "taxi_zone_lookup.csv"
OUT = ROOT / "data" / "summaries"

# A wait counts only when pickup comes after the request and within an hour of it.
# 1.3% of trips record a pickup before the request; those are left out of wait times.
MAX_WAIT_SECONDS = 3600

# The dashboard covers the latest twelve months in the cache. Older files may still be there;
# they are left out so the window rolls forward as new months arrive.
MONTHS = 12
files = sorted(RAW_DIR.glob("fhvhv_tripdata_*.parquet"))[-MONTHS:]
if not files:
    raise SystemExit(f"No trip files in {RAW_DIR}. Run pipeline/fetch_raw.py first.")
print(f"Reading {files[0].name} to {files[-1].name} ({len(files)} files)")
RAW = [str(f) for f in files]

con = duckdb.connect()

con.sql(f"""
    CREATE VIEW trips AS
    SELECT
        CASE hvfhs_license_num
            WHEN 'HV0003' THEN 'Uber'
            WHEN 'HV0005' THEN 'Lyft'
            ELSE hvfhs_license_num
        END AS company,
        pickup_datetime,
        PULocationID AS zone_id,
        CASE
            WHEN pickup_datetime >= request_datetime
             AND epoch(pickup_datetime - request_datetime) <= {MAX_WAIT_SECONDS}
            THEN epoch(pickup_datetime - request_datetime) / 60.0
        END AS wait_min
    FROM read_parquet({RAW}, union_by_name = true)
""")

# Each summary has one row per company plus an "All" row, so medians are computed over the
# right set of trips rather than averaged from per-company medians.
WAIT_COLUMNS = """
    count(*) AS trips,
    count(wait_min) AS wait_trips,
    round(median(wait_min), 2) AS wait_median_min,
    round(quantile_cont(wait_min, 0.9), 2) AS wait_p90_min
"""

con.sql(f"""
    COPY (
        SELECT
            strftime(pickup_datetime, '%Y-%m') AS month,
            coalesce(company, 'All') AS company,
            count(DISTINCT pickup_datetime::date) AS days,
            {WAIT_COLUMNS}
        FROM trips
        GROUP BY GROUPING SETS ((month, company), (month))
        ORDER BY month, company
    ) TO '{OUT / "monthly.csv"}' (HEADER)
""")

# Average trips in each weekday and hour slot: total trips divided by how many of that
# weekday fall in the period. Weekday 1 is Monday, 7 is Sunday.
con.sql(f"""
    COPY (
        WITH weekday_counts AS (
            SELECT isodow(d) AS weekday, count(*) AS n_days
            FROM (SELECT DISTINCT pickup_datetime::date AS d FROM trips)
            GROUP BY weekday
        ),
        slots AS (
            SELECT
                coalesce(company, 'All') AS company,
                isodow(pickup_datetime) AS weekday,
                hour(pickup_datetime) AS hour,
                count(*) AS trips
            FROM trips
            GROUP BY GROUPING SETS ((company, weekday, hour), (weekday, hour))
        )
        SELECT company, weekday, hour, round(trips / n_days) AS avg_trips
        FROM slots JOIN weekday_counts USING (weekday)
        ORDER BY company, weekday, hour
    ) TO '{OUT / "heatmap.csv"}' (HEADER)
""")

con.sql(f"""
    COPY (
        WITH by_zone AS (
            SELECT
                coalesce(company, 'All') AS company,
                zone_id,
                {WAIT_COLUMNS}
            FROM trips
            GROUP BY GROUPING SETS ((company, zone_id), (zone_id))
        )
        SELECT b.company, b.zone_id, z.Borough AS borough, z.Zone AS zone,
               b.trips, b.wait_trips, b.wait_median_min, b.wait_p90_min
        FROM by_zone b
        LEFT JOIN read_csv('{ZONES}') z ON z.LocationID = b.zone_id
        ORDER BY b.company, b.trips DESC, b.zone_id
    ) TO '{OUT / "zones.csv"}' (HEADER)
""")

# Check the results before anyone commits them. The site's data loaders run the same checks
# at build time, so a bad file can never reach the live page.
problems = []
monthly = con.sql(f"SELECT * FROM read_csv('{OUT / 'monthly.csv'}')")
checks = con.sql("""
    SELECT count(DISTINCT month), count(*), min(trips), min(days), max(days),
           count(*) FILTER (wait_p90_min < wait_median_min)
    FROM monthly
""").fetchone()
months, rows, min_trips, min_days, max_days, bad_waits = checks
if months != len(files):
    problems.append(f"monthly.csv has {months} months but {len(files)} files were read")
if rows != months * 3:
    problems.append(f"monthly.csv should have All, Uber and Lyft for every month ({rows} rows)")
if min_trips <= 0 or min_days < 28 or max_days > 31 or bad_waits:
    problems.append("monthly.csv has impossible trip counts, day counts or wait times")
slots = con.sql(f"SELECT count(*) FROM read_csv('{OUT / 'heatmap.csv'}')").fetchone()[0]
if slots != 3 * 7 * 24:
    problems.append(f"heatmap.csv should have 504 rows, has {slots}")
if problems:
    raise SystemExit("Summaries failed their checks; do not commit them:\n  " + "\n  ".join(problems))

# Record which TLC files the summaries came from and when TLC published them, so the page can
# say how fresh the data is. Only the files' own dates are used, so re-running the pipeline
# on the same files writes the same file.
def published(parquet):
    sidecar = parquet.with_name(parquet.name + ".headers.json")
    headers = {k.lower(): v for k, v in json.loads(sidecar.read_text()).items()}
    return parsedate_to_datetime(headers["last-modified"]).date().isoformat()

sources = [{"file": f.name, "published": published(f)} for f in files]
(OUT / "meta.json").write_text(json.dumps({
    "first_month": files[0].name[15:22],
    "last_month": files[-1].name[15:22],
    "latest_published": max(s["published"] for s in sources),
    "sources": sources,
}, indent=2) + "\n")

for f in sorted([*OUT.glob("*.csv"), OUT / "meta.json"]):
    print(f"{f.relative_to(ROOT)}: {f.stat().st_size:,} bytes")
