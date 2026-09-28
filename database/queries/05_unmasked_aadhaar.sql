-- check: unmasked_aadhaar
-- severity: error
-- why: privacy rule — only the masked form XXXX-XXXX-1234 may ever be stored. Anything else may be a
--      full Aadhaar number and must be removed and reported, not "fixed" silently.
-- The value itself is never selected, so running this check cannot leak it.
SELECT Id AS id, BeneficiaryId AS beneficiary_id
FROM AadhaarVerifications
WHERE AadhaarMasked IS NOT NULL
  AND (LENGTH(AadhaarMasked) <> 14 OR AadhaarMasked NOT LIKE 'XXXX-XXXX-____')
ORDER BY Id
