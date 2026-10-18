"""GET /api/ration/bookings: optional server-side filter, search and paging (2026-10-18, PERF-01).

An official's unfiltered list is every booking ever made (locally 9,660 rows, 4.9 MB, about 2 s per request), and the
staff screens filtered it in the browser. The filters must not change the default answer, nor widen anyone's scope.
"""

from __future__ import annotations

from ration_world import TEST_PASSWORD, book


def _ravi(env) -> dict:
    r = env["client"].post("/api/auth/register", json={"fullName": "Ravi Kale", "email": "ravi@example.com",
                                                       "mobileNumber": "9000000002", "password": TEST_PASSWORD})
    assert r.status_code == 200, r.text
    return {"Authorization": f"Bearer {r.json()['data']['accessToken']}"}


def _two_bookings(env) -> tuple[dict, dict, dict]:
    asha = book(env).json()["data"]
    ravi_headers = _ravi(env)
    ravi = env["client"].post("/api/ration/bookings", headers=ravi_headers, json={
        "rationShopId": 1, "timeSlotId": 1, "items": [{"rationType": "Rice", "quantity": 1}]}).json()["data"]
    return asha, ravi, ravi_headers


def _ids(env, headers, **params) -> list[int]:
    r = env["client"].get("/api/ration/bookings", headers=headers, params=params)
    assert r.status_code == 200, r.text
    return [b["id"] for b in r.json()["data"]]


def test_without_parameters_the_answer_is_unchanged(env):
    asha, ravi, _ = _two_bookings(env)
    assert _ids(env, env["official"]) == [ravi["id"], asha["id"]]          # everything in scope, newest first
    assert _ids(env, env["shop"]) == [ravi["id"], asha["id"]]
    assert _ids(env, env["citizen"]) == [asha["id"]]


def test_limit_and_offset_page_newest_first(env):
    asha, ravi, _ = _two_bookings(env)
    assert _ids(env, env["official"], limit=1) == [ravi["id"]]
    assert _ids(env, env["official"], limit=1, offset=1) == [asha["id"]]
    assert _ids(env, env["official"], limit=1, offset=5) == []
    assert _ids(env, env["official"], limit=999_999) == [ravi["id"], asha["id"]]   # capped, not an error
    assert _ids(env, env["official"], limit=0) == [ravi["id"]]                     # at least one row
    assert _ids(env, env["official"], limit=5, offset=-3) == [ravi["id"], asha["id"]]


def test_status_filter(env):
    asha, ravi, ravi_headers = _two_bookings(env)
    assert env["client"].delete(f"/api/ration/bookings/{ravi['id']}", headers=ravi_headers).status_code == 200
    assert _ids(env, env["official"], status="Cancelled") == [ravi["id"]]
    assert _ids(env, env["official"], status="confirmed") == [asha["id"]]          # case-insensitive, like the UI
    assert _ids(env, env["official"], status="All") == [ravi["id"], asha["id"]]
    r = env["client"].get("/api/ration/bookings", headers=env["official"], params={"status": "Lost"})
    assert r.status_code == 400 and r.json()["errorCode"] == "INVALID_STATUS"


def test_search_by_person_shop_or_token_number(env):
    asha, ravi, _ = _two_bookings(env)
    assert _ids(env, env["official"], q="ravi") == [ravi["id"]]
    assert _ids(env, env["official"], q="SATNAVARI") == [ravi["id"], asha["id"]]
    assert _ids(env, env["official"], q=asha["tokenNumber"][-4:]) == [asha["id"]]
    assert _ids(env, env["official"], q="%") == []                                 # a literal %, not a wildcard
    assert _ids(env, env["official"], q="   ") == [ravi["id"], asha["id"]]        # blank: no filter


def test_search_never_widens_the_callers_scope(env):
    asha, ravi, _ = _two_bookings(env)
    assert _ids(env, env["citizen"], q="ravi") == []                               # another citizen's booking
    assert _ids(env, env["citizen"], q="satnavari", limit=50) == [asha["id"]]
    assert _ids(env, env["other_shop"], q="asha") == []                            # another shop's booking
