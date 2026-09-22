namespace SmartRation.Api.Common;

// Centralized masking so sensitive-looking values are never assembled
// inconsistently across services, logs, or DTOs.
public static class MaskingUtil
{
    public static string MaskMobile(string mobile)
    {
        if (string.IsNullOrEmpty(mobile) || mobile.Length < 4)
        {
            return "****";
        }

        var lastFour = mobile[^4..];
        return $"{new string('*', 6)}{lastFour}";
    }

    // Formats a synthetic 12-digit demo Aadhaar-shaped reference as
    // XXXX-XXXX-#### — never a real Aadhaar number.
    public static string MaskSyntheticAadhaar(string lastFourDigits)
    {
        return $"XXXX-XXXX-{lastFourDigits}";
    }
}
