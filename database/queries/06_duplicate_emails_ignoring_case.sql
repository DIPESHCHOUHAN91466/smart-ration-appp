-- check: duplicate_emails_ignoring_case
-- severity: error
-- why: both backends lower-case e-mail addresses before storing and looking them up, so two accounts that
--      differ only in case mean one of them can never sign in (and would bypass the unique index).
SELECT MIN(Id) AS id, COUNT(*) AS accounts
FROM Users
GROUP BY LOWER(Email)
HAVING COUNT(*) > 1
ORDER BY MIN(Id)
