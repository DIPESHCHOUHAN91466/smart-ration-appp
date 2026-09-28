-- check: collections_with_open_tokens
-- severity: error
-- why: completing a collection sets its token to Completed (TokenStatus 3) in the same transaction; any
--      other status lets the same token be scanned and collected again.
SELECT c.Id AS id, c.TokenId AS token_id, t.Status AS token_status
FROM RationCollections c
JOIN Tokens t ON t.Id = c.TokenId
WHERE t.Status <> 3
ORDER BY c.Id
