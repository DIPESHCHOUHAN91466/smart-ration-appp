import apiClient, { unwrap } from "./api";

export function getRationItems() {
  return unwrap(apiClient.get("/ration/items"));
}

export function createBooking(payload) {
  return unwrap(apiClient.post("/ration/bookings", payload));
}

export function getBookings() {
  return unwrap(apiClient.get("/ration/bookings"));
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
