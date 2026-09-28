// Formatting shared by pages and components, always in the user's interface language (en / hi / mr).
// Pure functions: no React, no state — unit-tested in tests/unit/format.test.js.

const LOCALES = { en: "en-IN", hi: "hi-IN", mr: "mr-IN" };

/** The Intl locale for an interface language; anything unknown falls back to Indian English. */
export function localeFor(language) {
  return LOCALES[language] ?? "en-IN";
}

// The backends send UTC timestamps; some without a zone suffix ("2026-09-28T10:05:03").
function parseUtc(value) {
  if (value instanceof Date) return value;
  if (typeof value !== "string" || !value) return null;
  const hasZone = /(Z|[+-]\d{2}:?\d{2})$/.test(value);
  const date = new Date(hasZone || !value.includes("T") ? value : `${value}Z`);
  return Number.isNaN(date.getTime()) ? null : date;
}

/** "2026-09-28" (a calendar date, no time zone) -> "28 September 2026" in the user's language. */
export function formatDate(isoDate, language) {
  const date = new Date(`${isoDate}T00:00:00`);
  if (Number.isNaN(date.getTime())) return isoDate;
  return date.toLocaleDateString(localeFor(language), { day: "numeric", month: "long", year: "numeric" });
}

/** A UTC timestamp -> local date and time ("28 Sept 2026, 3:35 pm"); "—" when missing or invalid. */
export function formatDateTime(value, language) {
  const date = parseUtc(value);
  if (!date) return "—";
  return date.toLocaleString(localeFor(language), { dateStyle: "medium", timeStyle: "short" });
}

/** "EdibleOil" -> "Edible Oil" (C# enum names as sent by the API). */
export function rationItemLabel(rationType) {
  return String(rationType).replace(/([a-z])([A-Z])/g, "$1 $2");
}

/** Oil is measured in litres, every other ration item in kilograms. */
export function rationItemUnit(rationType) {
  return rationType === "EdibleOil" ? "L" : "kg";
}
