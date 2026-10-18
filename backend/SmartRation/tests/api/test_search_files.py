"""robots.txt and sitemap.xml are real files, not the app shell (2026-10-18, SEO-01).

Before: /robots.txt and /sitemap.xml fell through to the single-page-app fallback and were answered with index.html
(text/html), so search engines got no robots rules and an invalid sitemap. Now frontend/public/ holds both files, the
build copies them to dist/, and the backend serves them as files. The test uses the real files from frontend/public.
"""

from __future__ import annotations

import re
import shutil
import xml.etree.ElementTree as ET

import pytest
from py_testkit import REPO_ROOT

PUBLIC = REPO_ROOT / "frontend" / "public"
PRIVATE_PREFIXES = ["/api/", "/profile/", "/beneficiary/", "/rural", "/shop", "/gov", "/settings"]
PUBLIC_PAGES = {"/", "/help", "/privacy", "/terms", "/accessibility"}


@pytest.fixture
def site(tmp_path, make_client):
    dist = tmp_path / "dist"
    dist.mkdir()
    (dist / "index.html").write_text("<!doctype html><title>Ration Mitra</title>", encoding="utf-8")
    for name in ("robots.txt", "sitemap.xml"):
        shutil.copy(PUBLIC / name, dist / name)
    return make_client(frontend_dist_dir=str(dist))


def test_robots_txt_is_served_as_text_not_as_the_app(site):
    r = site.get("/robots.txt")
    assert r.status_code == 200 and r.headers["content-type"].startswith("text/plain")
    assert "<html" not in r.text.lower() and "User-agent: *" in r.text


def test_sitemap_is_served_as_xml_not_as_the_app(site):
    r = site.get("/sitemap.xml")
    assert r.status_code == 200 and "xml" in r.headers["content-type"]
    ET.fromstring(r.content)   # well-formed


def test_robots_keeps_signed_in_areas_and_personal_pages_out_of_search():
    rules = [line.split(":", 1)[1].strip() for line in (PUBLIC / "robots.txt").read_text(encoding="utf-8").splitlines()
             if line.lower().startswith("disallow:")]
    for prefix in PRIVATE_PREFIXES:
        assert prefix in rules, prefix


def test_the_sitemap_lists_only_public_pages_on_the_robots_sitemap_host():
    ns = {"s": "http://www.sitemaps.org/schemas/sitemap/0.9"}
    locs = [e.text for e in ET.parse(PUBLIC / "sitemap.xml").getroot().findall("s:url/s:loc", ns)]
    sitemap_line = re.search(r"^Sitemap:\s*(\S+)", (PUBLIC / "robots.txt").read_text(encoding="utf-8"), re.M).group(1)
    host = sitemap_line.rsplit("/sitemap.xml", 1)[0]
    assert sitemap_line.startswith("https://") and all(loc.startswith(host + "/") for loc in locs)
    assert {loc[len(host):] for loc in locs} == PUBLIC_PAGES
    assert not any(loc[len(host):].startswith(tuple(PRIVATE_PREFIXES)) for loc in locs)
