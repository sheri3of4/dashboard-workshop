"""Build the operations summaries from the raw trip files.

Reads every row in data/raw/ with DuckDB and writes small CSV files to data/summaries/.
The dashboard reads only those summaries, never the raw rows.

Run it from the project root:

    uv run python pipeline/build_summaries.py
"""

from pathlib import Path

import duckdb

ROOT = Path(__file__).resolve().parent.parent
RAW = ROOT / "data" / "raw" / "fhvhv_tripdata_*.parquet"
ZONES = ROOT / "data" / "reference" / "taxi_zone_lookup.csv"
OUT = ROOT / "data" / "summaries"

# A wait counts only when pickup comes after the request and within an hour of it.
# 1.3% of trips record a pickup before the request; those are left out of wait times.
MAX_WAIT_SECONDS = 3600

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
    FROM read_parquet('{RAW}', union_by_name = true)
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
        ORDER BY b.company, b.trips DESC
    ) TO '{OUT / "zones.csv"}' (HEADER)
""")

for f in sorted(OUT.glob("*.csv")):
    print(f"{f.relative_to(ROOT)}: {f.stat().st_size:,} bytes")
