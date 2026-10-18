import apiClient, { unwrap } from "../api/client";

export function getRationItems(shopId) {
  return unwrap(apiClient.get("/ration/items", { params: shopId ? { shopId } : {} }));
}

export function createBooking(payload) {
  return unwrap(apiClient.post("/ration/bookings", payload));
}

/** My / my shop's / all bookings, newest first. Optional `{ status, q, limit, offset }` filter and page on the server. */
export function getBookings(params) {
  return unwrap(apiClient.get("/ration/bookings", params ? { params } : undefined));
}

export function getBooking(id) {
  return unwrap(apiClient.get(`/ration/bookings/${id}`));
}

export function rescheduleBooking(id, timeSlotId) {
  return unwrap(apiClient.put(`/ration/bookings/${id}`, { timeSlotId }));
}

export function cancelBooking(id) {
  return unwrap(apiClient.delete(`/ration/bookings/${id}`));
}
