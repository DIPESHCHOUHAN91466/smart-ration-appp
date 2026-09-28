-- check: shop_owners_without_shop
-- severity: warning
-- why: a shop owner (Role 2) acts on the shop in their token's rationShopId claim; without a shop the
--      account can sign in but every shop screen is empty or refused.
SELECT Id AS id
FROM Users
WHERE Role = 2 AND RationShopId IS NULL
ORDER BY Id
