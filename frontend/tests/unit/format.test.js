import { describe, it, expect } from "vitest";
import { formatDate, formatDateTime, localeFor, rationItemLabel, rationItemUnit } from "../../src/utils/format";

describe("utils/format", () => {
  it("maps interface languages to Indian locales", () => {
    expect(localeFor("en")).toBe("en-IN");
    expect(localeFor("hi")).toBe("hi-IN");
    expect(localeFor("mr")).toBe("mr-IN");
    expect(localeFor("fr")).toBe("en-IN");
    expect(localeFor(undefined)).toBe("en-IN");
  });

  it("formats calendar dates without shifting the day", () => {
    expect(formatDate("2026-09-28", "en")).toContain("28");
    expect(formatDate("2026-09-28", "en")).toContain("2026");
    expect(formatDate("not-a-date", "en")).toBe("not-a-date");
  });

  it("treats zone-less API timestamps as UTC (regression: C# sends DateTime without 'Z')", () => {
    // Same instant written three ways must format identically.
    const zoneless = formatDateTime("2026-09-28T10:05:00", "en");
    expect(formatDateTime("2026-09-28T10:05:00Z", "en")).toBe(zoneless);
    expect(formatDateTime("2026-09-28T15:35:00+05:30", "en")).toBe(zoneless);
  });

  it("shows a dash for missing or broken timestamps", () => {
    expect(formatDateTime(null, "en")).toBe("—");
    expect(formatDateTime("", "hi")).toBe("—");
    expect(formatDateTime("garbage", "mr")).toBe("—");
  });

  it("uses the interface language", () => {
    const hindi = formatDateTime("2026-09-28T10:05:00Z", "hi");
    expect(hindi).not.toBe(formatDateTime("2026-09-28T10:05:00Z", "en"));
  });

  it("labels ration items and their units", () => {
    expect(rationItemLabel("EdibleOil")).toBe("Edible Oil");
    expect(rationItemLabel("Rice")).toBe("Rice");
    expect(rationItemUnit("EdibleOil")).toBe("L");
    expect(rationItemUnit("Wheat")).toBe("kg");
  });
});
