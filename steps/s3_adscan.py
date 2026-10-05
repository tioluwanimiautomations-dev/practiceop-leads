"""Step 3: market-level ad scan (LSA / Search advertisers per query per location).

No scraping of Google: SERPs/LSA are bot-hostile and against ToS, so this step sets lsa/search_ads
to 'unknown' and writes the search URLs for a manual check. Fill ad_scan.csv by hand; re-running
never overwrites values you entered.

Outputs (data/<market>/): ad_scan.csv (editable), lsa_manual_check.txt (URL checklist)
"""
from urllib.parse import quote_plus

from lib.common import market_dir, read_csv, write_csv

FIELDS = ["location", "query", "url", "lsa", "search_ads", "advertisers_seen"]
FILLED = ("lsa", "search_ads", "advertisers_seen")


def run(market, **_):
    d = market_dir(market["name"])
    path = d / "ad_scan.csv"
    existing = {(r["location"], r["query"]): r for r in read_csv(path)} if path.exists() else {}

    rows = []
    for location in market["ad_locations"].values():
        for term in market["search_terms"]:
            q = f"{term} {location}"
            row = {"location": location, "query": term,
                   "url": "https://www.google.com/search?q=" + quote_plus(q),
                   "lsa": "unknown", "search_ads": "unknown", "advertisers_seen": ""}
            old = existing.get((location, term))
            if old:
                row.update({k: old[k] for k in FILLED if old.get(k)})
            rows.append(row)
    write_csv(path, rows, FIELDS)

    lines = [
        f"Manual ad check: {market['name']}",
        "Use a clean/incognito window; Google shows different ads by location and device.",
        "For each URL record in ad_scan.csv: lsa (y/n), search_ads (y/n), advertisers_seen",
        "(firm names in the Google Guaranteed / LSA block and sponsored results, separated by ';').",
        "Presence only. Do not estimate spend.", "",
    ]
    lines += [f"[ ] {r['location']} | {r['query']}\n    {r['url']}" for r in rows]
    (d / "lsa_manual_check.txt").write_text("\n".join(lines) + "\n")

    done = sum(1 for r in rows if r["lsa"] != "unknown" or r["search_ads"] != "unknown")
    print("\n=== STEP 3: ad scan ===")
    print(f"{len(rows)} market-level queries ({done} already filled in) -> ad_scan.csv")
    print(f"Manual checklist -> data/{market['name']}/lsa_manual_check.txt")
    print("lsa / search_ads = 'unknown' until you fill them in.")
    return rows
