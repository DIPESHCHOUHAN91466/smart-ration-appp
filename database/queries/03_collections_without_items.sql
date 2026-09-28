-- check: collections_without_items
-- severity: error
-- why: RationCollectionService writes a collection and its items in one transaction; a collection with
--      no items records a hand-over of nothing and cannot be reconciled with the stock ledger.
SELECT c.Id AS id, c.TokenId AS token_id, c.RationShopId AS shop_id
FROM RationCollections c
WHERE NOT EXISTS (SELECT 1 FROM RationCollectionItems i WHERE i.RationCollectionId = c.Id)
ORDER BY c.Id
