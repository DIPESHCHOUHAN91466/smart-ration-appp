namespace SmartRation.Api.Services;

// Verifies both password-hash formats in use during the Python migration:
//   * BCrypt ($2a$/$2b$...) — created by this C# API.
//   * Argon2id ($argon2id$...) — the Python backend upgrades a user's hash to
//     Argon2 after a successful login there.
// Accepting both keeps every account usable from either backend, so the
// C# API remains a working rollback target. This API still creates BCrypt hashes.
public static class PasswordHashes
{
    public static bool Verify(string password, string storedHash)
    {
        if (string.IsNullOrEmpty(storedHash))
        {
            return false;
        }

        if (storedHash.StartsWith("$argon2", StringComparison.Ordinal))
        {
            try
            {
                return Isopoh.Cryptography.Argon2.Argon2.Verify(storedHash, password);
            }
            catch (Exception)
            {
                return false; // malformed hash: never an unhandled 500 on login
            }
        }

        try
        {
            return BCrypt.Net.BCrypt.Verify(password, storedHash);
        }
        catch (BCrypt.Net.SaltParseException)
        {
            return false;
        }
    }
}
