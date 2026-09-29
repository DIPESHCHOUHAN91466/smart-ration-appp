// Pure helpers for the eligibility screen. Eligibility itself is decided by the server; these only
// count and total what the server returned, for display.
import { rationItemUnit } from "../../utils/format";

// Badge tone for the server's member eligibility value.
export const ELIGIBILITY_TONE = { Eligible: "success", NotEligible: "error", Pending: "warning", VerificationRequired: "warning" };

/** { total, eligible, allEligible } from the verification's family block (members are the source). */
export function familyCounts(family) {
  const members = family?.members ?? [];
  const total = members.length || family?.familySize || 0;
  const eligible = members.length ? members.filter((m) => m.eligibility === "Eligible").length : family?.eligibleMemberCount ?? 0;
  return { total, eligible, allEligible: total > 0 && eligible === total };
}

/** Totals per unit (kg and L are never added together), e.g. { kg: 10, L: 0.5 }. Zero quantities skipped. */
export function unitTotals(items, quantityKey) {
  const totals = {};
  for (const item of items ?? []) {
    const quantity = Number(item[quantityKey]) || 0;
    if (quantity <= 0) continue;
    const unit = rationItemUnit(item.rationType);
    totals[unit] = Math.round(((totals[unit] ?? 0) + quantity) * 1000) / 1000;
  }
  return totals;
}

/** Up to two initials for the photo fallback: "Rahul Patil" -> "RP". */
export function initials(name) {
  const parts = String(name ?? "").trim().split(/\s+/).filter(Boolean);
  if (parts.length === 0) return "?";
  return (parts[0][0] + (parts.length > 1 ? parts[parts.length - 1][0] : "")).toUpperCase();
}

/** "XXXX-XXXX-1234" -> "XXXX XXXX 1234". Only a masked value is ever shown; anything else is refused. */
export function displayAadhaar(masked) {
  if (!masked || !/^X{4}-X{4}-\d{4}$/.test(masked)) return null;
  return masked.replaceAll("-", " ");
}
