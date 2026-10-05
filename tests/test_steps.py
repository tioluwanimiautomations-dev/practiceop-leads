from lib.common import norm_phone, root_domain
from steps.s1_scrape import county_from_filename
from steps.s2_filter import dedupe, name_verdict


def row(**kw):
    base = dict(name="", website="", phone="", address="", reviews_count="0", county="broward",
                search_term="dui attorney", category="", city="", state="", place_id="", maps_url="",
                rating="", permanently_closed="", temporarily_closed="", source_file="")
    return {**base, **kw}


def test_root_domain():
    assert root_domain("https://www.smithlaw.com/about?utm=x") == "smithlaw.com"
    assert root_domain("smithlaw.co.uk/x") == "smithlaw.co.uk"
    assert root_domain("https://www.facebook.com/smithlaw") == ""
    assert root_domain("") == ""


def test_norm_phone():
    assert norm_phone("+1 (305) 555-0100") == "3055550100"
    assert norm_phone("555") == ""


def test_name_verdict():
    assert name_verdict("Miami Injury Lawyers")[0] == "drop"
    assert name_verdict("Smith Family Law Group") == ("drop", "primarily_family")
    assert name_verdict("Miami-Dade Public Defender")[1] == "public_defender"
    assert name_verdict("Smith Injury & Criminal Defense") == ("keep", "mixed_name")
    assert name_verdict("Garcia Law Firm") == ("keep", "")


def test_dedupe_by_domain_merges_counties():
    rows = [row(name="A Law", website="https://a.com", reviews_count="5", county="broward"),
            row(name="A Law Miami", website="http://www.a.com/x", reviews_count="50", county="miami-dade")]
    kept, dupes = dedupe(rows)
    assert len(kept) == 1 and len(dupes) == 1
    assert kept[0]["name"] == "A Law Miami" and kept[0]["counties"] == "broward|miami-dade"


def test_directory_sites_do_not_merge_distinct_firms():
    rows = [row(name="Firm One", website="https://facebook.com/one", phone="3055550101"),
            row(name="Firm Two", website="https://facebook.com/two", phone="3055550102")]
    kept, _ = dedupe(rows)
    assert len(kept) == 2


def test_county_from_filename():
    c = {"miami-dade": 1, "broward": 1}
    assert county_from_filename("Miami_Dade_dataset.csv", c) == "miami-dade"
    assert county_from_filename("dataset.csv", c) == "unknown"
