# PracticeOp Lead Sourcing — Project Context

## What this repo is
A re-runnable pipeline that turns raw Google Maps data into a qualified, tiered list of
US criminal defense law firms for cold outreach. PracticeOp sells AI voice intake + ad
attribution to these firms. Founder: Steevo (solo, based in Nigeria, targeting Florida first).

Current market: **Miami-Dade + Broward, Florida**. Later: Palm Beach, Hillsborough (Tampa),
Orange (Orlando), Duval (Jacksonville).

## How to work with me
- Be direct. No filler. If an idea of mine is weak, say why.
- Work in small steps and STOP at each checkpoint for my review. Never skip a checkpoint.
- Before spending money (Apify runs, API calls), state the estimated cost and wait for my go.
- Keep code simple: one script per step + `run_market.py` orchestrator. Python.

## ICP v6 (what qualifies a firm)
Hard gates (all three):
1. Criminal defense is the primary or a MAJOR practice line.
2. Runs paid ads (Google Search, Local Services Ads, Meta). Target is $8K+/mo, but spend is
   NOT visible from data. Record ad PRESENCE only. Never estimate ad spend.
3. 50+ inbound calls/month (confirmed in discovery, not here).

Hard disqualifiers: primarily personal injury · primarily family law · public defender offices.
Do NOT disqualify a firm just because it lists PI or family among other areas; tag it `mixed-practice`.

Descriptors (record, never filter on): attorney count, PMS, other practice lines, billing.
- 1–2 attorneys → tag `small-highspend` (still valid)
- Never filter on attorney count or billing.

## Pipeline
1. **Scrape.** Input is EITHER Apify API runs OR CSV exports I drop into
   `data/<market>/raw/`. Support both. Apify actor: `compass/crawler-google-places`.
   Settings: terms = criminal defense attorney, criminal defense lawyer, DUI attorney,
   drug crime lawyer, criminal lawyer; one county per run; 120 places per term;
   NO paid add-ons; max cost per run $5.
2. **Dedupe + auto-filter.** Dedupe by website root domain (fallback: name + phone).
   Drop names clearly primarily PI / family / divorce / public defender. Save drops to
   `dropped.csv` with a reason. No website → `no_website.csv`.
3. **Ad scan (market level).** Record LSA / Search advertisers per query per market, not per
   firm. If LSA can't be scraped reliably, set `lsa=unknown` and output the Google search
   URLs to `lsa_manual_check.txt` for me.
4. **Crawl + classify.** Homepage + attorneys/team/about pages, max ~5 pages per site, respect
   robots.txt. Keyword-scan HTML for: clio, mycase, practicepanther, lawpay, callrail, ngage,
   apexchat, smith.ai → `tech_stack`. Classify with the cheapest Claude Haiku model via API,
   JSON only: crim_major, practice_areas, mixed_practice, attorney_count, managing_partner,
   spanish_mentioned, confidence. Retry once on bad JSON, else send to manual review.
5. **Contacts.** Build a Florida Bar directory lookup URL per managing partner
   (`bar_lookup_url`). Sunbiz for firm officers. Never scrape LinkedIn or anything behind a login.
   Apollo is NOT in the pipeline yet (being tested manually on 20 firms first).
6. **Tier + export.**
   - Tier A = qualified + (lsa=y OR search_ads=y) + managing partner known
   - Tier B = qualified, weaker signal
   - Hold = ad presence unknown/absent
   Export `data/<market>/leads.csv` and `manual_review.csv`.

## Output schema (leads.csv)
firm, domain, market, phone, address, reviews_count, attorneys, crim_major, mixed_practice,
lsa, search_ads, meta_ads, tech_stack, spanish_mentioned, partner, email, email_status,
bar_lookup_url, tier, tags, confidence

## Checkpoints (stop and show me)
1. After scrape: rows per query, total.
2. After filter: in/out counts + 15 random dropped names.
3. After classify: crim_major split, attorney buckets (1–2 / 3–20 / 20+), 10 low-confidence rows.
4. After tier: counts by tier, attorney bucket, tech marker.

## Hard rules
- NEVER send emails, DMs, connection requests or any outreach.
- NEVER commit secrets. Read `APIFY_TOKEN` and `ANTHROPIC_API_KEY` from env / `.env`.
  `.env` is in `.gitignore`.
- Keep a cost log per run (Apify usage, Anthropic tokens). Warn before any step > $5.
- Budget is tight (~$1,800 total runway). Prefer free options; ask before paid ones.
- Adding a market = adding a block to `markets.yaml`. Nothing else should change.
