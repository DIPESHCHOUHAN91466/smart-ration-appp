// The shops' clock: Asia/Kolkata, the same business clock as the server (backend app/utils/time.py). Slot dates and
// opening hours are Indian wall-clock values, so "today" and "has this slot started" must not depend on the zone the
// browser happens to be set to. The server re-checks every booking; this only keeps the screen honest.

export const BUSINESS_TIME_ZONE = "Asia/Kolkata";

const FORMAT = new Intl.DateTimeFormat("en-GB", {
  timeZone: BUSINESS_TIME_ZONE,
  year: "numeric",
  month: "2-digit",
  day: "2-digit",
  hour: "2-digit",
  minute: "2-digit",
  second: "2-digit",
  hourCycle: "h23",
});

/** "YYYY-MM-DDTHH:MM:SS" on the business clock (sortable as text). */
export function businessNow(now = new Date()) {
  const p = Object.fromEntries(FORMAT.formatToParts(now).map((part) => [part.type, part.value]));
  return `${p.year}-${p.month}-${p.day}T${p.hour}:${p.minute}:${p.second}`;
}

/** Today's date on the business clock, "YYYY-MM-DD" (the value an <input type="date"> uses). */
export function businessToday(now = new Date()) {
  return businessNow(now).slice(0, 10);
}

/** The business date `n` days before today, "YYYY-MM-DD" (report ranges are Indian calendar days). */
export function businessDaysAgo(n, now = new Date()) {
  const [year, month, day] = businessToday(now).split("-").map(Number);
  return new Date(Date.UTC(year, month - 1, day - n)).toISOString().slice(0, 10);   // date arithmetic only, no zone
}

/** The 1st of next month on the business clock, as a Date for display (entitlements renew then). */
export function businessNextMonthStart(now = new Date()) {
  const [year, month] = businessToday(now).split("-").map(Number);
  return new Date(year, month, 1);   // month is 1-based here, so this is the next month's 1st
}

/** A slot whose start (its date + start time, business clock) is now or past has started and can't be booked —
 * the server's rule (slot_has_started) and the Android app's (Slot.hasStarted). */
export function slotHasStarted(slot, now = new Date()) {
  const date = String(slot.slotDate).slice(0, 10);
  const start = String(slot.startTime).slice(0, 8).padEnd(8, ":00").slice(0, 8);
  return `${date}T${start}` <= businessNow(now);
}
