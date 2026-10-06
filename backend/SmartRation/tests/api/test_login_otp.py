"""/api/auth/otp/request + /verify — citizens sign in with a code sent to their registered mobile."""

from __future__ import annotations

from datetime import timedelta

from sqlalchemy import select

from app.database.connection import get_session_factory
from app.database.enums import OtpStatus
from app.database.models import AuditLog, Beneficiary, OtpVerification, User
from app.services import login_otp_service
from app.utils.time import utc_now

CITIZEN = "9000000001"  # registered Rural User in the shared ration world (tests/ration_world.py)


def session():
    return get_session_factory()()


def request_code(c, mobile=CITIZEN):
    return c.post("/api/auth/otp/request", json={"mobileNumber": mobile})


def verify(c, otp="123456", mobile=CITIZEN):
    return c.post("/api/auth/otp/verify", json={"mobileNumber": mobile, "otp": otp})


def login_codes():
    with session() as db:
        return db.scalars(select(OtpVerification).order_by(OtpVerification.Id)).all()


def test_citizen_signs_in_with_the_code(env):
    c = env["client"]
    r = request_code(c)
    assert r.status_code == 200, r.text
    sent = r.json()["data"]
    assert sent == {"mobileMasked": "******0001", "expiresInSeconds": 300, "resendAfterSeconds": 30, "demoOtpValue": "123456"}

    r = verify(c)
    assert r.status_code == 200, r.text
    data = r.json()["data"]
    assert data["user"]["role"] == "RuralUser" and data["user"]["mobileNumber"] == CITIZEN
    assert data["accessToken"] and data["refreshToken"]
    # The session works like a password session: the profile opens and the refresh token rotates.
    assert c.get("/api/users/profile", headers={"Authorization": f"Bearer {data['accessToken']}"}).status_code == 200
    assert c.post("/api/auth/refresh", json={"refreshToken": data["refreshToken"]}).status_code == 200
    # The code can't be used twice.
    assert verify(c).status_code == 401


def test_only_a_hash_of_the_code_is_stored(env):
    request_code(env["client"])
    (code,) = login_codes()
    assert code.OtpHash != "123456" and len(code.OtpHash) == 64
    with session() as db:
        user = db.scalar(select(User).where(User.MobileNumber == CITIZEN))
    assert code.RequestedByUserId == user.Id  # requested by the citizen themself


def test_formats_of_the_same_number_are_accepted(env):
    c = env["client"]
    for mobile in ["90000 00001", "+91 9000000001", "+91-90000-00001", "09000000001", "919000000001"]:
        assert login_otp_service.normalize_mobile(mobile) == CITIZEN
    assert request_code(c, "+91 90000 00001").json()["data"]["mobileMasked"] == "******0001"


def test_invalid_numbers_are_rejected_with_a_clear_message(env):
    for mobile in ["12345", "1234567890", "abcdefghij", "", "90000000011"]:
        r = request_code(env["client"], mobile)
        assert r.status_code == 400, mobile
    assert "Enter a 10-digit mobile number." in " ".join(request_code(env["client"], "12345").json()["errors"])


def test_unregistered_and_staff_numbers_get_the_same_answer_and_no_code(env):
    c = env["client"]
    citizen = request_code(c).json()
    for mobile in ["9876543210", "9000000051", "9000000061"]:  # nobody, a shop owner, an official
        other = request_code(c, mobile).json()
        assert other["message"] == citizen["message"]
        assert set(other["data"]) == set(citizen["data"])
    assert len(login_codes()) == 1  # only the citizen's
    # (OTP calls are limited to 6 a minute per address, so one sign-in attempt is enough here.)
    assert verify(c, mobile="9000000051").status_code == 401


def test_wrong_codes_and_the_three_try_limit(env):
    c = env["client"]
    request_code(c)
    for _ in range(3):
        r = verify(c, "000000")
        assert r.status_code == 401 and r.json()["errorCode"] == "OTP_INVALID"
    # After three wrong tries even the right code is refused: a new code is needed.
    assert verify(c).status_code == 401
    assert login_codes()[0].Status == OtpStatus.Failed


def test_an_expired_code_is_refused(env):
    c = env["client"]
    request_code(c)
    with session() as db:
        code = db.scalar(select(OtpVerification))
        code.ExpiresAt -= timedelta(minutes=10)
        db.commit()
    r = verify(c)
    assert r.status_code == 401 and r.json()["message"] == login_otp_service.INVALID_CODE


def test_asking_again_too_soon_keeps_the_first_code(env):
    c = env["client"]
    request_code(c)
    request_code(c)
    assert len(login_codes()) == 1
    assert verify(c).status_code == 200


def test_a_new_code_replaces_the_old_one(env):
    c = env["client"]
    request_code(c)
    with session() as db:
        first = db.scalar(select(OtpVerification))
        first.CreatedAt -= timedelta(minutes=1)  # past the 30-second wait
        db.commit()
    request_code(c)
    first, second = login_codes()
    assert first.Status == OtpStatus.Expired and second.Status == OtpStatus.Pending


def test_a_shop_counter_code_cannot_sign_the_citizen_in(env):
    c = env["client"]
    r = c.post("/api/verification/otp/request", headers=env["shop"], json={"mobileNumber": CITIZEN})
    assert r.status_code == 200, r.text
    assert verify(c).status_code == 401  # same demo code, but it belongs to the counter


def test_a_deactivated_citizen_gets_no_code(env):
    with session() as db:
        db.scalar(select(User).where(User.MobileNumber == CITIZEN)).IsActive = False
        db.commit()
    assert request_code(env["client"]).status_code == 200
    assert login_codes() == []


def test_attempts_are_audited_with_masked_numbers(env):
    c = env["client"]
    request_code(c)
    verify(c, "000000")
    verify(c)
    with session() as db:
        rows = db.scalars(select(AuditLog).order_by(AuditLog.Id)).all()
    actions = [(a.Action, a.Result) for a in rows if a.Action.startswith("LOGIN")]
    assert ("LOGIN_OTP_REQUESTED", "SUCCESS") in actions or any(a == "LOGIN_OTP_REQUESTED" for a, _ in actions)
    assert ("LOGIN_FAILED", "FAILED") in actions
    assert any(a == "LOGIN" for a, _ in actions)
    text = " ".join(f"{a.Details}" for a in rows)
    assert CITIZEN not in text and "******0001" in text


def test_requests_are_rate_limited(env):
    c = env["client"]
    codes = [request_code(c, "9876543210").status_code for _ in range(8)]
    assert 429 in codes


# ---------------------------------------------------------------- lockout and SMS cap (N6)


def _citizen_id() -> int:
    with session() as db:
        return db.scalar(select(User.Id).where(User.MobileNumber == CITIZEN))


def _add_failures(n: int) -> None:
    with session() as db:
        for _ in range(n):
            db.add(AuditLog(UserId=_citizen_id(), Action="LOGIN_FAILED", EntityName="User", Result="FAILED", CreatedAt=utc_now()))
        db.commit()


def test_a_locked_account_gets_no_code_and_even_the_right_code_is_refused_without_saying_why(env):
    c = env["client"]
    request_code(c)                                       # a valid code exists ...
    _add_failures(5)                                      # ... then five failed sign-ins (password or OTP) lock the account
    r = verify(c)
    assert r.status_code == 401 and r.json()["errorCode"] == "OTP_INVALID"     # same answer as a wrong code
    assert r.json()["message"] == login_otp_service.INVALID_CODE
    with session() as db:
        code = db.scalar(select(OtpVerification))
        code.CreatedAt -= timedelta(minutes=1)            # past the resend wait
        db.commit()
    assert request_code(c).status_code == 200             # same answer as always ...
    assert len(login_codes()) == 1                        # ... but no new code and no SMS
    with session() as db:
        results = {(a.Action, a.Result) for a in db.scalars(select(AuditLog))}
    assert ("LOGIN_LOCKED", "BLOCKED") in results and ("LOGIN_OTP_REQUESTED", "BLOCKED") in results


def test_at_most_ten_sign_in_codes_per_number_per_day(env):
    c = env["client"]
    with session() as db:
        user = db.scalar(select(User).where(User.MobileNumber == CITIZEN))
        ben = db.scalar(select(Beneficiary).where(Beneficiary.UserId == user.Id))
        for i in range(10):                               # ten codes earlier today, all used up
            t = utc_now() - timedelta(hours=1, minutes=i)
            db.add(OtpVerification(BeneficiaryId=ben.Id, RequestedByUserId=user.Id, OtpHash="0" * 64, AttemptCount=0,
                                   MaxAttempts=3, Status=int(OtpStatus.Verified), CreatedAt=t, ExpiresAt=t + timedelta(minutes=5)))
        db.commit()
    assert request_code(c).status_code == 200 and len(login_codes()) == 10     # the 11th is not created or sent
    with session() as db:                                 # a day later the number can get codes again
        for code in db.scalars(select(OtpVerification)):
            code.CreatedAt -= timedelta(days=1)
        db.commit()
    request_code(c)
    assert len(login_codes()) == 11
