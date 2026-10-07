"""Bring the local trip cache up to date with TLC's published files.

Reads TLC's trip record page, takes the latest twelve months of high volume for-hire files,
and downloads only the months that are missing from data/raw/ or that TLC has re-uploaded
since they were cached. Files already in the cache and unchanged are never downloaded again.

TLC's file server blocks clients that make many or parallel requests, so this asks for one
file at a time with a pause in between.

Run it from the project root:

    uv run python pipeline/fetch_raw.py            # check and download
    uv run python pipeline/fetch_raw.py --check    # only report what would change
"""

import json
import re
import sys
import time
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RAW = ROOT / "data" / "raw"
PAGE = "https://www.nyc.gov/site/tlc/about/tlc-trip-record-data.page"
FILE_LINK = re.compile(r"https://[^\"']+/trip-data/fhvhv_tripdata_(\d{4}-\d{2})\.parquet")
MONTHS = 12
PAUSE_SECONDS = 2
USER_AGENT = "dashboard-workshop data refresh (one file at a time)"


def request(url, method="GET"):
    return urllib.request.urlopen(
        urllib.request.Request(url, method=method, headers={"User-Agent": USER_AGENT}),
        timeout=60,
    )


def published_months():
    """The months TLC lists on its page, newest last, with each file's URL."""
    with request(PAGE) as response:
        html = response.read().decode("utf-8", errors="replace")
    links = {m.group(1): m.group(0) for m in FILE_LINK.finditer(html)}
    return sorted(links.items())


def cached_headers(path):
    """The headers saved when a file was downloaded, with lowercase names."""
    sidecar = path.with_name(path.name + ".headers.json")
    if not sidecar.exists():
        return None
    return {k.lower(): v for k, v in json.loads(sidecar.read_text()).items()}


def same_file(saved, current):
    keys = ("etag", "last-modified", "content-length")
    return all(saved.get(k) == current.get(k) for k in keys)


def download(url, path):
    """Download to a temporary name, check the size, then move it into place."""
    partial = path.with_name(path.name + ".partial")
    with request(url) as response, open(partial, "wb") as out:
        headers = {k.lower(): v for k, v in response.headers.items()}
        while chunk := response.read(1 << 20):
            out.write(chunk)
    expected = int(headers.get("content-length", -1))
    if expected != partial.stat().st_size:
        partial.unlink()
        raise RuntimeError(f"{path.name}: expected {expected:,} bytes, got a different size")
    partial.replace(path)
    path.with_name(path.name + ".headers.json").write_text(json.dumps(headers, indent=2) + "\n")


def main():
    check_only = "--check" in sys.argv
    window = published_months()[-MONTHS:]
    if not window:
        sys.exit(f"No trip files found on {PAGE}. The page layout may have changed.")
    print(f"TLC lists {window[0][0]} to {window[-1][0]}; keeping the latest {len(window)} months.")

    changed = 0
    for i, (month, url) in enumerate(window):
        path = RAW / f"fhvhv_tripdata_{month}.parquet"
        if i:
            time.sleep(PAUSE_SECONDS)
        with request(url, method="HEAD") as response:
            current = {k.lower(): v for k, v in response.headers.items()}
        saved = cached_headers(path)

        if path.exists() and saved and same_file(saved, current):
            print(f"  {month}: up to date")
            continue

        reason = "new month" if not path.exists() else "re-uploaded by TLC"
        size = int(current.get("content-length", 0)) / 1e6
        changed += 1
        if check_only:
            print(f"  {month}: {reason}, would download {size:,.0f} MB")
            continue
        print(f"  {month}: {reason}, downloading {size:,.0f} MB ...", flush=True)
        download(url, path)
        print(f"  {month}: done")

    if changed == 0:
        print("Nothing to download. The cache matches TLC.")
    elif check_only:
        print(f"{changed} file(s) would be downloaded. Run without --check to fetch them.")


if __name__ == "__main__":
    main()
