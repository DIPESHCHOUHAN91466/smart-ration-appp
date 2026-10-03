"""The built frontend served by the API (FRONTEND_DIST_DIR), and bare-host service URLs."""

from __future__ import annotations

import pytest
from py_testkit import make_settings


@pytest.fixture
def site(tmp_path, make_client):
    dist = tmp_path / "dist"
    (dist / "assets").mkdir(parents=True)
    (dist / "index.html").write_text("<!doctype html><title>Ration Mitra</title>", encoding="utf-8")
    (dist / "assets" / "app-123.js").write_text("console.log(1)", encoding="utf-8")
    (dist / "favicon.png").write_bytes(b"\x89PNG")
    (tmp_path / "secret.txt").write_text("outside the build", encoding="utf-8")
    return make_client(frontend_dist_dir=str(dist))


def test_the_app_is_served_on_every_client_route(site):
    for path in ("/", "/help", "/rural/dashboard", "/gov/users/42"):
        r = site.get(path)
        assert r.status_code == 200 and "Ration Mitra" in r.text, path
        assert r.headers["cache-control"] == "no-store" and r.headers["x-frame-options"] == "DENY"


def test_pages_carry_a_strict_content_security_policy_and_allow_the_voice_and_camera_features(site):
    headers = site.get("/rural/dashboard").headers
    csp = dict(part.strip().split(" ", 1) for part in headers["content-security-policy"].split(";"))
    assert csp["script-src"] == "'self'"                         # no inline or third-party script
    assert csp["object-src"] == "'none'" and csp["frame-ancestors"] == "'none'" and csp["base-uri"] == "'self'"
    assert csp["connect-src"] == "'self'"                        # API calls only to this site
    assert csp["font-src"] == "'self' data:" and "googleapis" not in headers["content-security-policy"]   # fonts self-hosted
    assert "https://*.tile.openstreetmap.org" in csp["img-src"]
    permissions = headers["permissions-policy"]
    assert "camera=(self)" in permissions and "microphone=(self)" in permissions   # QR scanner and chatbot voice input
    assert "content-security-policy" not in site.get("/docs").headers               # Swagger's CDN assets keep working


def test_built_files_are_served_with_caching(site):
    r = site.get("/assets/app-123.js")
    assert r.status_code == 200 and r.text == "console.log(1)"
    assert "immutable" in r.headers["cache-control"]
    assert site.get("/favicon.png").content == b"\x89PNG"


def test_api_health_and_docs_are_never_answered_with_the_app(site):
    assert site.get("/health").json()["status"] in ("healthy", "degraded")
    assert site.get("/docs").status_code == 200 and "swagger" in site.get("/docs").text.lower()
    r = site.get("/api/does-not-exist")
    assert r.status_code in (404, 502, 503) and "Ration Mitra" not in r.text


def test_files_outside_the_build_cannot_be_read(site):
    for path in ("/../secret.txt", "/%2e%2e/secret.txt", "/assets/../../secret.txt"):
        assert "outside the build" not in site.get(path).text


def test_without_the_setting_nothing_is_served(make_client):
    assert make_client().get("/rural/dashboard").status_code == 404


def test_missing_build_fails_at_startup(tmp_path, make_client):
    with pytest.raises(RuntimeError, match="index.html"):
        make_client(frontend_dist_dir=str(tmp_path / "nothing-here"))


def test_bare_host_names_get_https(tmp_path):
    settings = make_settings(tmp_path, legacy_api_url="smart-ration-core.onrender.com", ai_service_url="")
    assert settings.legacy_api_url == "https://smart-ration-core.onrender.com"
    assert settings.ai_service_url == ""
    assert make_settings(tmp_path, legacy_api_url="http://localhost:5188").legacy_api_url == "http://localhost:5188"


def test_website_files_are_compressed_but_api_responses_are_not(tmp_path, make_client):
    dist = tmp_path / "dist"
    (dist / "assets").mkdir(parents=True)
    (dist / "index.html").write_text("<!doctype html><title>Ration Mitra</title>" + "<p>x</p>" * 300, encoding="utf-8")
    (dist / "assets" / "app-9.js").write_text("console.log('ration');" * 200, encoding="utf-8")
    (dist / "assets" / "tiny-1.js").write_text("1", encoding="utf-8")
    site = make_client(frontend_dist_dir=str(dist))
    gz = {"Accept-Encoding": "gzip, br"}

    r = site.get("/assets/app-9.js", headers=gz)
    assert r.headers["content-encoding"] == "gzip" and "Accept-Encoding" in r.headers["vary"]
    assert r.text == "console.log('ration');" * 200                      # the client decompresses it correctly
    assert "immutable" in r.headers["cache-control"]
    page = site.get("/rural/dashboard", headers=gz)
    assert page.headers["content-encoding"] == "gzip" and "content-security-policy" in page.headers
    assert "content-encoding" not in site.get("/assets/tiny-1.js", headers=gz).headers          # too small to bother
    assert "content-encoding" not in site.get("/assets/app-9.js", headers={"Accept-Encoding": "identity"}).headers
    assert "content-encoding" not in site.get("/health", headers=gz).headers                    # API: never (BREACH)
