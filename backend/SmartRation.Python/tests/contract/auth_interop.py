"""Live auth interoperability between the C# API and the Python backend.

Registers two throwaway test accounts (one per backend) and proves:
  * a BCrypt user logging in via Python gets upgraded to Argon2 and can
    still log in via C#;
  * a Python-registered (Argon2) user can log in via C# and C# can read
    the beneficiary Python provisioned;
  * access and refresh tokens from either backend work on the other;
  * error responses are identical.
Usage (both servers running): .venv\\Scripts\\python tests\\contract\\auth_interop.py
"""

from __future__ import annotations

import os
import random
import sys
import time

import httpx
import pymysql

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from app.core.config import Settings  # noqa: E402
from app.core.security import decode_access_token  # noqa: E402

CS = "http://localhost:5188/api"
PY = "http://127.0.0.1:8000/api"
settings = Settings()
results: list[tuple[bool, str]] = []


def check(ok: bool, label: str) -> None:
    results.append((ok, label))
    print(f"{'OK  ' if ok else 'FAIL'} {label}")


def stored_hash(email: str) -> str:
    url = httpx.URL(settings.database_url.replace("mysql+pymysql", "mysql"))
    conn = pymysql.connect(host=url.host, port=url.port or 3306, user=url.username, password=url.password, database=url.path.lstrip("/"))
    with conn.cursor() as cur:
        cur.execute("SELECT PasswordHash FROM Users WHERE Email=%s", (email,))
        return cur.fetchone()[0]


def post(base, path, **kw):
    return httpx.post(f"{base}{path}", timeout=30, **kw)


def main() -> int:
    stamp = f"{int(time.time())}{random.randint(100, 999)}"
    pw = "Interop-Pass-123"

    # --- 1. BCrypt user (registered via C#) -> login via Python -> Argon2 -> login via C#
    cs_email = f"interop.cs.{stamp}@example.com"
    r = post(CS, "/auth/register", json={"fullName": "Interop CS User", "email": cs_email, "mobileNumber": f"8{stamp[-9:]}", "password": pw})
    check(r.status_code == 200, "C# register (BCrypt)")
    check(stored_hash(cs_email).startswith("$2"), "  stored hash is BCrypt")
    r = post(PY, "/auth/login", json={"email": cs_email, "password": pw})
    check(r.status_code == 200, "Python login of BCrypt user")
    py_tokens = r.json()["data"]
    check(stored_hash(cs_email).startswith("$argon2id$"), "  hash upgraded to Argon2id")
    r = post(CS, "/auth/login", json={"email": cs_email, "password": pw})
    check(r.status_code == 200, "C# login AFTER the Argon2 upgrade (rollback safety)")
    cs_tokens = r.json()["data"]

    # --- 2. Tokens across backends
    r = httpx.get(f"{CS}/users/profile", headers={"Authorization": f"Bearer {py_tokens['accessToken']}"}, timeout=30)
    check(r.status_code == 200 and r.json()["data"]["email"] == cs_email, "Python-issued access token accepted by C#")
    c = decode_access_token(cs_tokens["accessToken"], settings)
    check(c["sub"] == str(cs_tokens["user"]["id"]), "C#-issued access token validated by Python")
    r = post(PY, "/auth/refresh", json={"refreshToken": cs_tokens["refreshToken"]})
    check(r.status_code == 200, "C#-issued refresh token rotated by Python")
    rotated = r.json()["data"]["refreshToken"]
    r = post(CS, "/auth/refresh", json={"refreshToken": rotated})
    check(r.status_code == 200, "Python-issued refresh token rotated by C#")
    r = post(CS, "/auth/refresh", json={"refreshToken": cs_tokens["refreshToken"]})
    check(r.status_code == 401, "reused (rotated) refresh token rejected by C#")
    r = post(PY, "/auth/logout", json={"refreshToken": py_tokens["refreshToken"]})
    check(r.status_code == 200, "Python logout")
    check(post(CS, "/auth/refresh", json={"refreshToken": py_tokens["refreshToken"]}).status_code == 401, "  C# refuses the logged-out token")

    # --- 3. Python-registered user works on C#, including provisioned beneficiary data
    py_email = f"interop.py.{stamp}@example.com"
    r = post(PY, "/auth/register", json={"fullName": "Interop Py User", "email": py_email, "mobileNumber": f"7{stamp[-9:]}", "password": pw})
    check(r.status_code == 200 and r.json()["data"]["user"]["role"] == "RuralUser", "Python register")
    check(stored_hash(py_email).startswith("$argon2id$"), "  stored hash is Argon2id")
    r = post(CS, "/auth/login", json={"email": py_email, "password": pw})
    check(r.status_code == 200, "C# login of Python-registered user")
    token = r.json()["data"]["accessToken"]
    me = httpx.get(f"{CS}/beneficiaries/me", headers={"Authorization": f"Bearer {token}"}, timeout=30)
    b = me.json().get("data") or {}
    check(me.status_code == 200 and str(b.get("beneficiary", {}).get("beneficiaryCode", b.get("beneficiaryCode", ""))).startswith("BEN-DEMO-"),
          "C# reads the beneficiary Python provisioned")

    # --- 4. Identical error responses
    cases = [
        ("/auth/login", {"email": "nobody@example.com", "password": "wrong"}),
        ("/auth/login", {}),
        ("/auth/login", {"email": "not-an-email", "password": ""}),
        ("/auth/register", {"fullName": "A", "email": "x", "mobileNumber": "abc", "password": "short"}),
        ("/auth/register", {"fullName": "Dup", "email": cs_email, "mobileNumber": "9000012345", "password": pw}),
        ("/auth/refresh", {"refreshToken": "bogus"}),
        ("/auth/logout", {"refreshToken": "bogus"}),
    ]
    for path, body in cases:
        a, p = post(CS, path, json=body), post(PY, path, json=body)
        ja, jp = a.json(), p.json()
        if ja.get("errors") and jp.get("errors"):
            ja["errors"], jp["errors"] = sorted(ja["errors"]), sorted(jp["errors"])
        check(a.status_code == p.status_code and ja == jp, f"same response {a.status_code}/{p.status_code} for {path} {list(body)}")

    failed = sum(not ok for ok, _ in results)
    print(f"\n{len(results) - failed}/{len(results)} checks passed. Test accounts: {cs_email}, {py_email}")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
