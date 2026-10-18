import { describe, it, expect } from "vitest";
import { businessDaysAgo, businessNextMonthStart, businessNow, businessToday, slotHasStarted } from "../../src/utils/businessTime";

// Instants are given in UTC ("Z"); the expectations are Asia/Kolkata wall-clock values (UTC+05:30).
const at = (iso) => new Date(iso);

describe("utils/businessTime", () => {
  it("uses the Indian date, which runs ahead of UTC until 05:30", () => {
    expect(businessToday(at("2026-10-16T18:29:00Z"))).toBe("2026-10-16");   // 23:59 IST
    expect(businessToday(at("2026-10-16T18:30:00Z"))).toBe("2026-10-17");   // 00:00 IST, UTC still the 16th
    expect(businessToday(at("2026-10-16T23:59:00Z"))).toBe("2026-10-17");   // 05:29 IST
    expect(businessToday(at("2026-10-17T00:00:00Z"))).toBe("2026-10-17");   // 05:30 IST
    expect(businessNow(at("2026-12-31T18:30:00Z"))).toBe("2027-01-01T00:00:00");   // year boundary
  });

  it("renews on the 1st of the next Indian month", () => {
    const d = businessNextMonthStart(at("2026-10-31T20:00:00Z"));          // 1 Nov 01:30 IST
    expect([d.getFullYear(), d.getMonth() + 1, d.getDate()]).toEqual([2026, 12, 1]);
    const e = businessNextMonthStart(at("2026-12-15T06:00:00Z"));
    expect([e.getFullYear(), e.getMonth() + 1, e.getDate()]).toEqual([2027, 1, 1]);
  });

  it("a slot has started from its start time on (same rule as the server and the Android app)", () => {
    const slot = { slotDate: "2026-10-17T00:00:00", startTime: "09:00:00" };
    expect(slotHasStarted(slot, at("2026-10-17T03:29:59Z"))).toBe(false);   // 08:59:59 IST
    expect(slotHasStarted(slot, at("2026-10-17T03:30:00Z"))).toBe(true);    // exactly 09:00 IST
    expect(slotHasStarted(slot, at("2026-10-17T07:30:00Z"))).toBe(true);    // 13:00 IST
    expect(slotHasStarted({ ...slot, startTime: "09:00" }, at("2026-10-17T03:00:00Z"))).toBe(false);   // HH:MM form
  });

  it("yesterday's slots have started even while the UTC date is still yesterday", () => {
    const yesterday = { slotDate: "2026-10-16T00:00:00", startTime: "16:55:00" };
    const today = { slotDate: "2026-10-17T00:00:00", startTime: "09:00:00" };
    const now = at("2026-10-16T20:00:00Z");                                  // 01:30 IST on the 17th
    expect(slotHasStarted(yesterday, now)).toBe(true);
    expect(slotHasStarted(today, now)).toBe(false);
  });
});

describe("utils/businessTime report ranges", () => {
  it("counts days back from the Indian date, across month and year ends", () => {
    const now = at("2026-10-31T19:00:00Z");                                   // 1 Nov 00:30 IST, UTC still 31 Oct
    expect(businessDaysAgo(0, now)).toBe("2026-11-01");                         // officials can pick today
    expect(businessDaysAgo(29, now)).toBe("2026-10-03");
    expect(businessDaysAgo(1, at("2027-01-01T00:00:00Z"))).toBe("2026-12-31");
  });
});
