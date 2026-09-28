-- check: slot_count_drift
-- severity: warning
-- why: BookedCount is a counter kept next to the tokens (booking adds 1, cancelling and rescheduling away
--      subtract 1). It should equal the slot's tokens that are not Cancelled (TokenStatus 4). Drift does
--      not corrupt data but makes a slot look fuller or emptier than it is.
SELECT s.Id AS id, s.BookedCount AS booked, COUNT(t.Id) AS tokens
FROM TimeSlots s
LEFT JOIN Tokens t ON t.TimeSlotId = s.Id AND t.Status <> 4
GROUP BY s.Id, s.BookedCount
HAVING s.BookedCount <> COUNT(t.Id)
ORDER BY s.Id
