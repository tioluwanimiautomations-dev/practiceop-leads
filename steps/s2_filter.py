"""Step 2: dedupe + auto-filter scraped.csv.

Outputs (data/<market>/): filtered.csv, dropped.csv, no_website.csv
Bias is toward KEEPING: only names that are clearly PI / family / divorce / public defender
are dropped, and never if the name also signals criminal defense (tagged name_flag=mixed).
"""
import random
import re
from collections import Counter

from lib.common import (is_directory_url, market_dir, norm_name, norm_phone, read_csv,
                        root_domain, write_csv)

PI_RE = re.compile(r"\b(injur\w*|accident\w*|wrongful death|slip (and|&) fall|truck(ing)?|"
                   r"malpractice|workers'? ?comp\w*|car crash|crash)\b", re.I)
FAMILY_RE = re.compile(r"\b(family law|family (law )?(attorneys?|lawyers?|firm)|divorce\w*|"
                       r"custody|child support|adoption|matrimonial)\b", re.I)
PD_RE = re.compile(r"\bpublic defender\w*|\boffice of the (regional )?counsel\b", re.I)
CRIM_RE = re.compile(r"\b(criminal|defense|defence|dui|dwi|felony|misdemeanor|drug)\b", re.I)
CATEGORY_PI_RE = re.compile(r"personal injury|divorce|family law|accident", re.I)

DROPPED_FIELDS = ["name", "reason", "county", "website", "phone", "category", "search_term", "detail"]
OUT_FIELDS = ["firm_key", "name", "domain", "website", "phone", "address", "city", "state", "county",
              "counties", "reviews_count", "rating", "category", "search_terms", "place_id",
              "maps_url", "name_flag", "category_flag", "dup_count"]


def name_verdict(name):
    """-> ('drop', reason) | ('keep', flag)"""
    for label, rx in (("public_defender", PD_RE), ("primarily_pi", PI_RE), ("primarily_family", FAMILY_RE)):
        m = rx.search(name)
        if m:
            if label != "public_defender" and CRIM_RE.search(name):
                return "keep", "mixed_name"
            return "drop", label
    return "keep", ""


def firm_key(r):
    """root domain > name+phone > name+address. Directory/social URLs never count as a domain."""
    dom = root_domain(r["website"])
    if dom:
        return dom, "domain"
    n, p = norm_name(r["name"]), norm_phone(r["phone"])
    if p:
        return f"{n}|{p}", "name_phone"
    return f"{n}|{norm_name(r['address'])}", "name_addr"


def _reviews(r):
    try:
        return int(float(r["reviews_count"] or 0))
    except ValueError:
        return 0


def dedupe(rows):
    """Merge rows sharing a firm key. Keeps the highest-review row; unions counties/terms."""
    groups = {}
    for r in rows:
        key, _ = firm_key(r)
        groups.setdefault(key, []).append(r)
    kept, dupes = [], []
    for key, grp in groups.items():
        grp.sort(key=_reviews, reverse=True)
        best = dict(grp[0])
        best["firm_key"] = key
        best["domain"] = root_domain(best["website"])
        best["counties"] = "|".join(sorted({g["county"] for g in grp}))
        best["search_terms"] = "|".join(sorted({g["search_term"] for g in grp if g["search_term"]}))
        best["dup_count"] = len(grp)
        kept.append(best)
        for g in grp[1:]:
            dupes.append({**g, "reason": "duplicate", "detail": f"dup of {best['name']} ({key})"})
    return kept, dupes


def run(market, seed=None, **_):
    d = market_dir(market["name"])
    rows = read_csv(d / "scraped.csv")
    state = market["state"]

    dropped, live = [], []
    for r in rows:
        reason = detail = ""
        if r["permanently_closed"].lower() == "true":
            reason = "permanently_closed"
        elif r["state"] and r["state"].upper() not in (state, "FLORIDA"):
            reason, detail = "out_of_state", r["state"]
        else:
            verdict, val = name_verdict(r["name"])
            if verdict == "drop":
                reason = val
        if reason:
            dropped.append({**r, "reason": reason, "detail": detail})
            continue
        r["name_flag"] = name_verdict(r["name"])[1]
        r["category_flag"] = "pi_family_category" if CATEGORY_PI_RE.search(r["category"]) else ""
        live.append(r)

    has_site, no_site = [], []
    for r in live:
        (no_site if not r["website"] or is_directory_url(r["website"]) else has_site).append(r)
    for r in no_site:
        r["website"] = "" if is_directory_url(r["website"]) else r["website"]

    kept, dupes1 = dedupe(has_site)
    nosite_kept, dupes2 = dedupe(no_site)
    dropped += dupes1 + dupes2

    write_csv(d / "filtered.csv", kept, OUT_FIELDS)
    write_csv(d / "no_website.csv", nosite_kept, OUT_FIELDS)
    write_csv(d / "dropped.csv", dropped, DROPPED_FIELDS)

    rng = random.Random(seed)
    non_dupe = [x for x in dropped if x["reason"] != "duplicate"]
    sample = rng.sample(non_dupe, min(15, len(non_dupe)))

    print("\n=== CHECKPOINT 2: dedupe + filter ===")
    print(f"IN:  {len(rows)} scraped rows")
    print(f"OUT: {len(kept)} firms with website -> filtered.csv")
    print(f"     {len(nosite_kept)} firms without a usable website -> no_website.csv")
    print(f"     {len(dropped)} dropped -> dropped.csv")
    print("\nDropped by reason:")
    for reason, n in Counter(x["reason"] for x in dropped).most_common():
        print(f"  {reason:22s} {n:5d}")
    print(f"\n{len(sample)} random dropped names (excluding duplicates):")
    for x in sample:
        print(f"  [{x['reason']}] {x['name']}")
    mixed = sum(1 for r in kept + nosite_kept if r["name_flag"] == "mixed_name")
    cat = sum(1 for r in kept + nosite_kept if r["category_flag"])
    multi = sum(1 for r in kept if "|" in r["counties"])
    print(f"\nKept but worth a look: {mixed} mixed-name (PI/family word + criminal word), "
          f"{cat} with a PI/family Google category (classifier will decide in step 4)")
    print(f"Firms present in both counties (merged): {multi}")
    return kept
