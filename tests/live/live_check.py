"""Live system check of a running Smart Ration deployment (local stack or Render), through its real HTTP API.

    python tests/live/live_check.py --base-url https://<your-link>
    python tests/live/live_check.py --base-url http://127.0.0.1:8000 --readme-accounts    # local stack, README demo accounts

Covers: transport and headers, health/readiness/database TLS, error hygiene, sign-in (valid, invalid, injection), the
citizen journey (ration card, entitlement, items, slot, booking, token, signed QR, AI assistant), the shop counter (QR
verify, tampered/foreign QR, collection, repeat refused, stock decremented), the official views, the complaint
lifecycle, role and cross-citizen isolation, sign-out, and response times.

Secrets: the demo password comes from SMOKE_DEMO_PASSWORD (environment, or backend/SmartRation/.env, which is
git-ignored) or, with --readme-accounts, from the README's local demo table. Passwords and tokens are never printed.

Writes (synthetic demo data only): one booking that is then collected, one complaint that is then resolved, and one
throwaway citizen account ("Live Check ...") used to prove a citizen cannot see another citizen's data.
Sign-in is rate limited (10 per minute per address) and one run signs in about 8 times: leave a minute between runs.
Exit code 0 only if every check passed.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import secrets
import sys
import time
import urllib.error
import urllib.request
from datetime import date, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SEED_ACCOUNTS = {"RuralUser": "rural@example.com", "ShopOwner": "shop@example.com", "GovernmentOfficial": "officer@example.com"}

results: list[tuple[str, bool, str]] = []
timings: list[tuple[str, float]] = []


def check(label: str, ok: bool, detail: str = "") -> bool:
    results.append((label, bool(ok), detail))
    print(("PASS " if ok else "FAIL ") + label + (f"  [{detail}]" if detail else ""), flush=True)
    return bool(ok)


class Api:
    def __init__(self, base: str):
        self.base = base.rstrip("/")

    def call(self, method: str, path: str, body=None, token: str | None = None, headers: dict | None = None, raw: bytes | None = None):
        data = raw if raw is not None else (json.dumps(body).encode() if body is not None else None)
        req = urllib.request.Request(self.base + path, method=method, data=data)
        req.add_header("Content-Type", "application/json")
        if token:
            req.add_header("Authorization", "Bearer " + token)
        for k, v in (headers or {}).items():
            req.add_header(k, v)
        started = time.perf_counter()
        try:
            with urllib.request.urlopen(req, timeout=90) as r:
                status, hdrs, text = r.status, {k.lower(): v for k, v in r.headers.items()}, r.read().decode("utf-8", "replace")
        except urllib.error.HTTPError as e:
            status, hdrs, text = e.code, {k.lower(): v for k, v in e.headers.items()}, e.read().decode("utf-8", "replace")
        timings.append((f"{method} {re.sub(r'/[0-9]+', '/{id}', path.split('?')[0])}", (time.perf_counter() - started) * 1000))
        try:
            payload = json.loads(text) if text else None
        except ValueError:
            payload = None
        return status, payload, hdrs, text


def demo_password(readme: bool, role: str) -> tuple[str, str]:
    if readme:
        row = next(line for line in (ROOT / "README.md").read_text(encoding="utf-8").splitlines() if f"`{role}`" in line)
        email, password = re.findall(r"`([^`]*)`", row)[:2]
        return email, password
    password = os.environ.get("SMOKE_DEMO_PASSWORD")
    if not password:
        env_file = ROOT / "backend" / "SmartRation" / ".env"
        if env_file.exists():
            for line in env_file.read_text(encoding="utf-8").splitlines():
                if line.startswith("SMOKE_DEMO_PASSWORD="):
                    password = line.split("=", 1)[1].strip()
    if not password:
        sys.exit("Set SMOKE_DEMO_PASSWORD (environment or backend/SmartRation/.env) to the deployment's SEED_DEMO_PASSWORD.")
    return SEED_ACCOUNTS[role], password


def no_leak(text: str) -> bool:
    lowered = text.lower()
    return not any(marker in lowered for marker in ("traceback", "sqlalchemy", "pymysql", 'file "/', "mysql+pymysql://"))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-url", required=True)
    parser.add_argument("--readme-accounts", action="store_true", help="local stack: use the README's demo accounts")
    args = parser.parse_args()
    api = Api(args.base_url)
    https = api.base.startswith("https://")

    # ------------------------------------------------------------------ transport, health, hygiene
    status, _, hdrs, page = api.call("GET", "/")
    check("website loads", status == 200 and '<div id="root">' in page, str(status))
    if https:
        check("HSTS header", hdrs.get("strict-transport-security", "").startswith("max-age="), hdrs.get("strict-transport-security", "missing"))
        try:
            plain = urllib.request.urlopen(urllib.request.Request("http://" + api.base[len("https://"):] + "/health/live"), timeout=60)
            check("plain HTTP ends on HTTPS", plain.geturl().startswith("https://"), plain.geturl())
        except urllib.error.URLError as e:
            check("plain HTTP ends on HTTPS", False, type(e).__name__)
    check("security headers", hdrs.get("x-content-type-options") == "nosniff" and hdrs.get("x-frame-options") == "DENY")
    s, live, _, _ = api.call("GET", "/health/live")
    check("liveness", s == 200)
    s, ready, _, _ = api.call("GET", "/ready")
    check("readiness: database, migrations, legacy API disabled", s == 200 and ready["ready"] is True
          and ready["checks"]["legacyApi"] == "disabled", json.dumps(ready.get("checks")) if ready else str(s))
    s, db, _, _ = api.call("GET", "/health/db")
    enc = (db or {}).get("encryption", "missing")
    check("database healthy, schema at head", s == 200 and db["status"] == "healthy" and db["migrations"] == "ok", f"{(db or {}).get('latencyMs')} ms")
    if https:
        check("database link is encrypted (TLS)", enc.startswith("TLS"), enc)
    s, body, _, text = api.call("GET", "/api/definitely-not-a-route")
    check("unknown API route: clean 404, no internals", s == 404 and no_leak(text))
    s, body, _, text = api.call("POST", "/api/auth/login", raw=b"{not json")
    check("malformed JSON: 4xx, no internals", 400 <= s < 500 and no_leak(text), str(s))
    s, body, _, text = api.call("POST", "/api/auth/login", {"email": "' OR '1'='1' -- ", "password": "x' OR '1'='1"})
    check("SQL-injection-shaped sign-in refused cleanly", s in (400, 401) and no_leak(text), str(s))

    # ------------------------------------------------------------------ sign-in
    sessions = {}
    for role in SEED_ACCOUNTS:
        email, password = demo_password(args.readme_accounts, role)
        s, body, _, _ = api.call("POST", "/api/auth/login", {"email": email, "password": password})
        ok = s == 200 and body["data"]["user"]["role"] == role
        check(f"sign-in: {role}", ok, str(s))
        if ok:
            sessions[role] = body["data"]
        if role == "RuralUser":
            s, _, _, text = api.call("POST", "/api/auth/login", {"email": email, "password": password + "-wrong"})
            check("wrong password refused (401), no detail leaked", s == 401 and no_leak(text) and password not in text, str(s))
    if len(sessions) < 3:
        return summary()
    citizen, shop, official = (sessions[r]["accessToken"] for r in ("RuralUser", "ShopOwner", "GovernmentOfficial"))
    s, _, _, _ = api.call("GET", "/api/beneficiaries/me")
    check("no token: 401", s == 401, str(s))
    s, _, _, _ = api.call("GET", "/api/beneficiaries/me", token="not-a-real-token")
    check("forged token: 401", s == 401, str(s))

    # ------------------------------------------------------------------ citizen journey
    s, me, _, _ = api.call("GET", "/api/beneficiaries/me", token=citizen)
    ok = check("citizen: ration card, family, verification", s == 200 and me["data"]["beneficiary"] and me["data"]["rationShop"], str(s))
    if not ok:
        return summary()
    beneficiary, shop_id = me["data"]["beneficiary"]["id"], me["data"]["rationShop"]["id"]
    s, ent, _, _ = api.call("GET", f"/api/beneficiaries/{beneficiary}/entitlement", token=citizen)
    check("citizen: entitlement", s == 200 and ent["data"], str(s))
    s, items, _, _ = api.call("GET", f"/api/ration/items?shopId={shop_id}", token=citizen)
    check("citizen: ration items for the shop", s == 200 and len(items["data"]) > 0, f"{len(items['data']) if s == 200 else s} items")
    slot = None
    for offset in (0, 1, 2):
        day = (date.today() + timedelta(days=offset)).isoformat()
        s, slots, _, _ = api.call("GET", f"/api/slots?shopId={shop_id}&date={day}", token=citizen)
        free = [x for x in (slots or {}).get("data") or [] if x.get("availableCapacity", x.get("capacity", 1) - x.get("bookedCount", 0)) > 0]
        if free:
            slot = free[-1]
            break
    if not check("citizen: a free 5-minute slot", slot is not None):
        return summary()
    item = next((i for i in items["data"] if (i.get("rationType") == "Rice")), items["data"][0])
    s, booking, _, text = api.call("POST", "/api/ration/bookings", {"rationShopId": shop_id, "timeSlotId": slot["id"],
                                                                     "items": [{"rationType": item["rationType"], "quantity": 1}]}, citizen)
    if not check("citizen: booking creates a token", s == 200 and booking["data"]["tokenNumber"], (booking or {}).get("message", str(s))):
        return summary()
    token_id, token_number = booking["data"]["id"], booking["data"]["tokenNumber"]
    s, _, _, _ = api.call("GET", f"/api/tokens/{token_id}", token=citizen)
    check("citizen: token details", s == 200)
    s, qr, _, _ = api.call("GET", f"/api/qr/payload/{token_id}", token=citizen)
    check("citizen: signed QR payload", s == 200 and qr["data"], str(s))
    s, ai, _, _ = api.call("POST", "/api/assistant/understand", {"text": "When can I collect my ration?", "language": "en"}, citizen)
    check("AI assistant answers from the citizen's real bookings", s == 200 and token_number in ai["data"]["reply"]["text"])

    # ------------------------------------------------------------------ shop counter
    s, dash, _, _ = api.call("GET", "/api/shop/dashboard", token=shop)
    check("shop: dashboard", s == 200)
    s, stock_before, _, _ = api.call("GET", "/api/inventory", token=shop)
    line = next((x for x in stock_before["data"] if x["rationType"] == item["rationType"]), None)
    s, scan, _, _ = api.call("POST", "/api/qr/scan", {"qrData": qr["data"]}, shop)
    sd = (scan or {}).get("data") or {}
    check("shop: QR verified, ready to collect", s == 200 and sd.get("verified") is True, sd.get("status", str(s)))
    # A well-formed QR whose token number was changed: only the signature can catch it.
    forged = token_number[:-1] + ("0" if token_number[-1] != "0" else "1")
    text_qr = qr["data"] if isinstance(qr["data"], str) else json.dumps(qr["data"])
    s, bad, _, _ = api.call("POST", "/api/qr/scan", {"qrData": text_qr.replace(token_number, forged)}, shop)
    check("shop: QR with a changed token number refused by its signature", s == 200 and (bad["data"] or {}).get("status") == "INVALID_SIGNATURE",
          ((bad or {}).get("data") or {}).get("status", str(s)))
    s, _, _, _ = api.call("POST", "/api/qr/scan", {"qrData": qr["data"]}, citizen)
    check("citizen cannot use the shop scanner (403)", s == 403, str(s))
    key = secrets.token_hex(16)
    s1, receipt, _, _ = api.call("POST", "/api/ration/collection/confirm", {"tokenId": token_id, "verificationMethod": "QR"}, shop, {"Idempotency-Key": key})
    s2, again, _, _ = api.call("POST", "/api/ration/collection/confirm", {"tokenId": token_id, "verificationMethod": "QR"}, shop, {"Idempotency-Key": key})
    code = ((receipt or {}).get("data") or {}).get("collectionCode", "")
    check("shop: collection confirmed with a receipt", s1 == 200 and code, code or str(s1))
    check("shop: retried confirmation returns the same receipt", s2 == 200 and again["data"]["collectionCode"] == code)
    s, rescan, _, _ = api.call("POST", "/api/qr/scan", {"qrData": qr["data"]}, shop)
    check("shop: the collected QR is refused", s == 200 and rescan["data"]["verified"] is False, rescan["data"].get("status"))
    if line:
        s, stock_after, _, _ = api.call("GET", "/api/inventory", token=shop)
        after = next(x for x in stock_after["data"] if x["id"] == line["id"])
        check("shop: stock went down by the quantity handed out", round(line["availableQuantity"] - after["availableQuantity"], 3) == 1,
              f"{line['availableQuantity']} -> {after['availableQuantity']}")

    # ------------------------------------------------------------------ official
    for path in ("/api/admin/dashboard", "/api/admin/statistics", "/api/shops/map", "/api/ai/alerts/active"):
        s, _, _, _ = api.call("GET", path, token=official)
        check(f"official: {path}", s == 200, str(s))
    s, _, _, _ = api.call("GET", "/api/admin/dashboard", token=citizen)
    check("citizen cannot open the official dashboard (403)", s == 403, str(s))

    # ------------------------------------------------------------------ complaints
    said = "I want to complain, this month I got less wheat than my card shows."
    s, u, _, _ = api.call("POST", "/api/assistant/understand", {"text": said, "language": "en"}, citizen)
    fields = ((u or {}).get("data") or {}).get("fields", {})
    check("AI pre-fills the complaint from what was said", s == 200 and fields.get("category") == "LessRation" and fields.get("rationType") == "Wheat")
    form = {"category": "LessRation", "rationType": "Wheat", "description": said + " (live check)", "source": "ASSISTANT"}
    s, empty, _, _ = api.call("POST", "/api/grievances", {**form, "description": " "}, citizen, {"Idempotency-Key": secrets.token_hex(16)})
    check("empty complaint refused (400)", s == 400, str(s))
    key = secrets.token_hex(16)
    s1, g1, _, _ = api.call("POST", "/api/grievances", form, citizen, {"Idempotency-Key": key})
    s2, g2, _, _ = api.call("POST", "/api/grievances", form, citizen, {"Idempotency-Key": key})
    ref = ((g1 or {}).get("data") or {}).get("referenceNumber", "")
    check("complaint filed with a reference number", s1 == 200 and re.fullmatch(r"GRV-\d{4}-\d{6}", ref or "") is not None, ref or str(s1))
    check("duplicate submission files it once", s2 == 200 and g2["data"]["referenceNumber"] == ref)
    gid = g1["data"]["id"]
    s, listed, _, _ = api.call("GET", "/api/grievances?status=Submitted", token=official)
    check("official sees the new complaint", s == 200 and any(x["id"] == gid for x in listed["data"]))
    s, _, _, _ = api.call("GET", "/api/grievances", token=citizen)
    check("citizen cannot list everyone's complaints (403)", s == 403, str(s))
    s, _, _, _ = api.call("POST", f"/api/grievances/{gid}/status", {"status": "UnderReview"}, official)
    check("official: under review", s == 200, str(s))
    reply = "Live check: the shop has been asked to give the missing wheat."
    s, _, _, _ = api.call("POST", f"/api/grievances/{gid}/status", {"status": "Resolved", "note": reply}, official)
    check("official: resolved with a response", s == 200, str(s))
    s, mine, _, _ = api.call("GET", "/api/grievances/mine", token=citizen)
    mine_g = next((x for x in mine["data"] if x["id"] == gid), {})
    check("citizen sees the resolved status and the official's response", mine_g.get("status") == "Resolved" and mine_g.get("resolutionNote") == reply)
    s, notes, _, _ = api.call("GET", "/api/notifications", token=citizen)
    check("citizen notified of filing and resolution", s == 200 and sum(ref in n["message"] for n in notes["data"]) >= 2)

    # ------------------------------------------------------------------ cross-citizen isolation (throwaway account)
    stamp = int(time.time())
    other_pw = secrets.token_urlsafe(18)
    s, reg, _, _ = api.call("POST", "/api/auth/register", {"fullName": f"Live Check {stamp}", "email": f"live-check-{stamp}@example.com",
                                                          "mobileNumber": f"9{stamp % 10**9:09d}", "password": other_pw})
    if check("throwaway citizen registered (synthetic card)", s == 200, (reg or {}).get("message", str(s))):
        other = reg["data"]["accessToken"]
        s, _, _, _ = api.call("GET", f"/api/ration/bookings/{token_id}", token=other)
        check("another citizen cannot open this citizen's booking", s in (403, 404), str(s))
        s, _, _, _ = api.call("GET", f"/api/qr/payload/{token_id}", token=other)
        check("another citizen cannot get this citizen's QR", s in (403, 404), str(s))
        s, theirs, _, _ = api.call("GET", "/api/grievances/mine", token=other)
        check("another citizen does not see this citizen's complaint", s == 200 and all(x["id"] != gid for x in theirs["data"]))

    # ------------------------------------------------------------------ sign-out
    refresh = sessions["RuralUser"]["refreshToken"]
    s, _, _, _ = api.call("POST", "/api/auth/logout", {"refreshToken": refresh}, citizen)
    check("sign-out", s == 200, str(s))
    s, _, _, _ = api.call("POST", "/api/auth/refresh", {"refreshToken": refresh})
    check("signed-out session cannot be refreshed (401)", s == 401, str(s))
    email, password = demo_password(args.readme_accounts, "RuralUser")
    s, _, _, _ = api.call("POST", "/api/auth/login", {"email": email, "password": password})
    check("sign in again", s == 200, str(s))
    return summary()


def summary() -> int:
    by_route: dict[str, list[float]] = {}
    for route, ms in timings:
        by_route.setdefault(route, []).append(ms)
    slow = sorted(((max(v), r) for r, v in by_route.items()), reverse=True)[:6]
    print("\nslowest calls (max ms): " + ", ".join(f"{r} {m:.0f}" for m, r in slow))
    failed = [r for r in results if not r[1]]
    print(f"\n{len(results) - len(failed)} passed, {len(failed)} failed")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
