import apiClient, { unwrap } from "../api/client";

// Citizens' complaints (the backend's "grievances"). Citizens file and follow their own; officials review all.
// Every write carries an Idempotency-Key so a retried request is recorded once.

export const COMPLAINT_CATEGORIES = [
  "LessRation", "PoorQuality", "ShopClosed", "Overcharged", "TokenProblem", "VerificationProblem", "StaffBehaviour", "Other",
];
export const COMPLAINT_ITEMS = ["Rice", "Wheat", "Sugar", "Pulses", "EdibleOil", "Salt"];
export const COMPLAINT_MIN_LENGTH = 10;
export const COMPLAINT_MAX_LENGTH = 1000;

/** Twelve digits with optional spaces or dashes: looks like an Aadhaar number, which must never be written here. */
export const AADHAAR_LIKE = /(?<!\d)\d{4}[\s-]?\d{4}[\s-]?\d{4}(?!\d)/;

export function newRequestKey() {
  const bytes = new Uint8Array(16);
  crypto.getRandomValues(bytes);
  return Array.from(bytes, (b) => b.toString(16).padStart(2, "0")).join("");
}

export function getMyComplaints() {
  return unwrap(apiClient.get("/grievances/mine"));
}

export function fileComplaint({ category, description, rationType }, requestKey) {
  return unwrap(apiClient.post("/grievances", { category, description: description.trim(), rationType: rationType || undefined, source: "APP" },
    { headers: { "Idempotency-Key": requestKey } }));
}

export function getAllComplaints(status) {
  return unwrap(apiClient.get("/grievances", { params: status ? { status } : {} }));
}

export function updateComplaintStatus(id, status, note) {
  return unwrap(apiClient.post(`/grievances/${id}/status`, { status, note: note?.trim() || undefined }));
}
