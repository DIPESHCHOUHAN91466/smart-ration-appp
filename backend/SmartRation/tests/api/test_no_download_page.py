"""Regression (2026-10-17, SEC-01): an uncommitted /download page once served sign-in credentials, a fixed OTP, a
tunnel address and a third-party QR image from the API. No route may serve that page or an APK; /download is just a
client route of the website now. The legitimate download — a citizen's own data export — stays sign-in only."""

from __future__ import annotations

import pytest

UNSAFE_MARKERS = ("password", "otp", "trycloudflare", "api.qrserver.com", "credentials")
APK_TYPE = "application/vnd.android.package-archive"


def _api_paths(client) -> set[str]:
    return set(client.app.openapi()["paths"])   # every API route, including those of included routers


@pytest.mark.parametrize("path", ["/download", "/download/apk"])
def test_no_api_route_serves_a_download_page_or_apk(make_client, path):
    client = make_client(legacy_api_url="")
    assert not any(p == "/download" or p.startswith("/download/") for p in _api_paths(client))
    r = client.get(path)
    assert r.status_code == 404
    assert r.headers.get("content-type", "") != APK_TYPE


@pytest.mark.parametrize("path", ["/download", "/download/apk"])
def test_with_the_website_built_in_download_is_only_the_app_shell(tmp_path, make_client, path):
    dist = tmp_path / "dist"
    dist.mkdir()
    (dist / "index.html").write_text("<!doctype html><title>Ration Mitra</title>", encoding="utf-8")
    client = make_client(legacy_api_url="", frontend_dist_dir=str(dist))
    r = client.get(path)
    assert r.status_code == 200 and r.text == "<!doctype html><title>Ration Mitra</title>"   # the SPA, nothing else
    assert r.headers["content-type"].startswith("text/html")
    assert not any(marker in r.text.lower() for marker in UNSAFE_MARKERS)


def test_the_legitimate_data_export_download_still_exists_and_needs_sign_in(make_client):
    client = make_client(legacy_api_url="")
    for path in ("/api/users/me/export", "/api/v1/users/me/export"):
        assert client.get(path).status_code == 401, path   # 401, not 404: the route exists and requires sign-in
