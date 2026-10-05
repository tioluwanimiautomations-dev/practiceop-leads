"""Step 1: load Apify CSV exports from data/<market>/raw/ -> scraped.csv (normalized).

CSV mode only for now. Apify API mode comes later.
"""
from collections import Counter

from lib.common import market_dir, read_csv, write_csv

# normalized field -> candidate column names in the Apify export (first non-empty wins)
COLUMN_MAP = {
    "name": ["title", "name"],
    "website": ["website", "webSite", "url_website"],
    "phone": ["phone", "phoneUnformatted"],
    "address": ["address"],
    "city": ["city"],
    "state": ["state"],
    "reviews_count": ["reviewsCount", "reviews_count"],
    "rating": ["totalScore", "rating"],
    "category": ["categoryName", "category"],
    "search_term": ["searchString", "search_term"],
    "place_id": ["placeId", "place_id"],
    "maps_url": ["url", "maps_url"],
    "permanently_closed": ["permanentlyClosed"],
    "temporarily_closed": ["temporarilyClosed"],
}
FIELDS = ["county", "source_file"] + list(COLUMN_MAP)


def county_from_filename(fname, counties):
    f = fname.lower().replace("_", "-")
    hits = [slug for slug in counties if slug in f]
    return hits[0] if len(hits) == 1 else "unknown"


def normalize(row, county, source_file):
    out = {"county": county, "source_file": source_file}
    for field, candidates in COLUMN_MAP.items():
        out[field] = next((row[c].strip() for c in candidates if row.get(c, "").strip()), "")
    return out


def run(market, **_):
    raw_dir = market_dir(market["name"]) / "raw"
    files = sorted(raw_dir.glob("*.csv"))
    if not files:
        raise SystemExit(f"No CSVs in {raw_dir}. Drop Apify exports there "
                         f"(filename must contain a county slug: {', '.join(market['counties'])}).")

    rows, per_file = [], {}
    for f in files:
        county = county_from_filename(f.name, market["counties"])
        if county == "unknown":
            print(f"WARNING: {f.name}: can't tell county from filename; tagged 'unknown'")
        raw = read_csv(f)
        if raw and not any(c in raw[0] for c in COLUMN_MAP["name"]):
            raise SystemExit(f"{f.name}: no 'title'/'name' column. Is this an Apify Google Maps export?")
        per_file[f.name] = (county, len(raw))
        rows += [normalize(r, county, f.name) for r in raw]

    write_csv(market_dir(market["name"]) / "scraped.csv", rows, FIELDS)

    print("\n=== CHECKPOINT 1: scrape ===")
    print("Files:")
    for name, (county, n) in per_file.items():
        print(f"  {name:50s} {county:12s} {n:5d} rows")
    print("\nRows per query:")
    by_term = Counter(r["search_term"] or "(blank)" for r in rows)
    for term, n in sorted(by_term.items(), key=lambda x: -x[1]):
        print(f"  {term:35s} {n:5d}")
    print("\nRows per county:")
    for c, n in Counter(r["county"] for r in rows).items():
        print(f"  {c:35s} {n:5d}")
    cap = market["max_places_per_term"]
    over = [(t, n) for t, n in by_term.items() if n > cap * len(market["counties"])]
    if over:
        print(f"\nNOTE: terms above {cap}/term/county cap: {over}")
    print(f"\nTOTAL: {len(rows)} rows -> data/{market['name']}/scraped.csv")
    return rows
