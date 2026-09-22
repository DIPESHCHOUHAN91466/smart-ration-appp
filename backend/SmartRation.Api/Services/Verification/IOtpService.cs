using SmartRation.Api.Models;

namespace SmartRation.Api.Services.Verification;

public interface IOtpService
{
    // Generates and "sends" an OTP for the given beneficiary. Development:
    // SyntheticOtpService (config-driven fixed/demo code). Production:
    // an AuthorizedSmsOtpService would dispatch a real SMS here instead.
    Task<OtpVerification> RequestOtpAsync(int beneficiaryId, int requestedByUserId);

    Task<OtpVerification> VerifyOtpAsync(int otpVerificationId, string code);
}
