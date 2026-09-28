-- check: overbooked_time_slots
-- severity: error
-- why: BookingService refuses a booking when BookedCount >= Capacity and never lets the count go below 0,
--      so a slot outside 0..Capacity means the counter was changed outside the application.
SELECT Id AS id, RationShopId AS shop_id, Capacity AS capacity, BookedCount AS booked
FROM TimeSlots
WHERE BookedCount > Capacity OR BookedCount < 0
ORDER BY Id
