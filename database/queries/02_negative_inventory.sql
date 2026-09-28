-- check: negative_inventory
-- severity: error
-- why: stock moves through the inventory ledger, which never takes a quantity below zero; a negative
--      available or allocated quantity means stock was edited directly or a ledger step was lost.
SELECT Id AS id, RationShopId AS shop_id, RationType AS ration_type, AvailableQuantity AS available, AllocatedQuantity AS allocated
FROM Inventory
WHERE AvailableQuantity < 0 OR AllocatedQuantity < 0
ORDER BY Id
