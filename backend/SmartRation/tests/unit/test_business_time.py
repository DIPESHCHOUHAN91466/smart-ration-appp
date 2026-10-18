"""The shops' clock (2026-10-17, DEF-03): the IANA Asia/Kolkata zone (UTC+05:30, no daylight saving). Pure functions, fixed instants."""

from __future__ import annotations

from datetime import UTC, datetime, time, timedelta
from pathlib import Path

import pytest

from app.utils.time import (
    BUSINESS_TIMEZONE,
    business_day_utc,
    business_month_utc,
    business_now,
    business_to_utc,
    business_today,
    slot_has_started,
)

D = datetime(2026, 10, 17)   # a calendar date; times below are naive UTC instants unless named IST


@pytest.mark.parametrize(("utc", "ist"), [
    (datetime(2026, 10, 16, 18, 29), datetime(2026, 10, 16, 23, 59)),   # last minute of the previous IST day
    (datetime(2026, 10, 16, 18, 30), datetime(2026, 10, 17, 0, 0)),     # IST midnight while UTC is still the 16th
    (datetime(2026, 10, 16, 23, 59), datetime(2026, 10, 17, 5, 29)),    # 05:29 IST: UTC and IST dates differ
    (datetime(2026, 10, 17, 0, 0), datetime(2026, 10, 17, 5, 30)),      # 05:30 IST: both dates agree again
    (datetime(2026, 12, 31, 18, 30), datetime(2027, 1, 1, 0, 0)),       # year boundary
])
def test_utc_instants_map_to_ist_wall_clock(utc, ist):
    assert business_now(utc) == ist
    assert business_today(utc) == ist.replace(hour=0, minute=0)


def test_the_business_zone_is_the_iana_asia_kolkata_zone_at_plus_05_30_all_year():
    assert str(BUSINESS_TIMEZONE) == "Asia/Kolkata"            # from the tz database (tzdata is pinned), never a guess
    for day in range(0, 366):                                  # no daylight saving on any day of the year
        instant = datetime(2026, 1, 1, tzinfo=UTC) + timedelta(days=day)
        assert instant.astimezone(BUSINESS_TIMEZONE).utcoffset() == timedelta(hours=5, minutes=30)


def test_the_tzdata_requirement_is_pinned_for_slim_images():
    requirements = (Path(__file__).resolve().parents[2] / "requirements.txt").read_text(encoding="utf-8")
    assert any(line.startswith("tzdata==") for line in requirements.splitlines())


def test_an_ist_day_and_month_as_utc_bounds():
    assert business_to_utc(datetime(2026, 10, 17, 0, 0)) == datetime(2026, 10, 16, 18, 30)
    assert business_day_utc(datetime(2026, 10, 17, 14, 0)) == (datetime(2026, 10, 16, 18, 30), datetime(2026, 10, 17, 18, 30))
    # 01:30 IST on 1 November is still 31 October in UTC: the window is November's (IST)
    assert business_month_utc(datetime(2026, 10, 31, 20, 0)) == (datetime(2026, 10, 31, 18, 30), datetime(2026, 11, 30, 18, 30))
    # last minute of October in IST: still October's window
    assert business_month_utc(datetime(2026, 10, 31, 18, 29)) == (datetime(2026, 9, 30, 18, 30), datetime(2026, 10, 31, 18, 30))
    # year boundary
    assert business_month_utc(datetime(2026, 12, 31, 18, 30)) == (datetime(2026, 12, 31, 18, 30), datetime(2027, 1, 31, 18, 30))
    # February in a non-leap year
    assert business_month_utc(datetime(2027, 2, 10)) == (datetime(2027, 1, 31, 18, 30), datetime(2027, 2, 28, 18, 30))


@pytest.mark.parametrize(("now_ist", "started"), [
    (datetime(2026, 10, 17, 8, 59, 59), False),   # one second before the 09:00 slot: still bookable
    (datetime(2026, 10, 17, 9, 0), True),         # exactly at the start: started (same rule as the Android app)
    (datetime(2026, 10, 17, 9, 1), True),         # later the same IST day
    (datetime(2026, 10, 18, 0, 1), True),         # next day
    (datetime(2026, 10, 16, 23, 59), False),      # the day before
])
def test_a_09_00_slot_starts_at_09_00_ist(now_ist, started):
    now_utc = now_ist - timedelta(hours=5, minutes=30)
    assert slot_has_started(D, time(9), now_utc) is started


def test_yesterdays_slot_has_started_even_while_the_utc_date_is_still_yesterday():
    now_utc = datetime(2026, 10, 16, 20, 0)   # 01:30 IST on the 17th; UTC date is the 16th
    assert slot_has_started(D - timedelta(days=1), time(16, 55), now_utc)          # yesterday's last slot
    assert not slot_has_started(D, time(9), now_utc)                               # today's first slot
