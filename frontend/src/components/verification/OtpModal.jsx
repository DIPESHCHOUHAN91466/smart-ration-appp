import { useState } from "react";
import { X, Smartphone } from "lucide-react";
import { requestOtp, verifyOtp } from "../../services/verificationService";

export default function OtpModal({ onClose, onVerified }) {
  const [step, setStep] = useState("mobile"); // mobile | otp
  const [mobileNumber, setMobileNumber] = useState("");
  const [otpVerificationId, setOtpVerificationId] = useState(null);
  const [maskedMobile, setMaskedMobile] = useState("");
  const [demoOtp, setDemoOtp] = useState(null);
  const [code, setCode] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const handleRequestOtp = async (e) => {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      const result = await requestOtp(mobileNumber.trim());
      setOtpVerificationId(result.otpVerificationId);
      setMaskedMobile(result.mobileMasked);
      setDemoOtp(result.demoOtpValue);
      setStep("otp");
    } catch (err) {
      setError(err.message || "Could not send OTP.");
    } finally {
      setLoading(false);
    }
  };

  const handleVerifyOtp = async (e) => {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      const result = await verifyOtp(otpVerificationId, code.trim());
      onVerified(result);
    } catch (err) {
      setError(err.message || "OTP verification failed.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="modal-backdrop">
      <div className="modal">
        <button className="modal-close" onClick={onClose}>
          <X />
        </button>
        <span className="eyebrow blue">IDENTITY RECOVERY — NOT AADHAAR VERIFICATION</span>
        <h2>Mobile OTP Verification</h2>
        <p className="muted">
          Use this only when the QR code can't be scanned. It verifies the beneficiary's registered mobile number —
          it does not perform Aadhaar verification.
        </p>

        {step === "mobile" && (
          <form onSubmit={handleRequestOtp}>
            <label style={{ textAlign: "left", display: "block", margin: "16px 0" }}>
              Beneficiary's registered mobile number
              <input
                required
                value={mobileNumber}
                onChange={(e) => setMobileNumber(e.target.value)}
                placeholder="9876543210"
              />
            </label>
            {error && <p style={{ color: "var(--red)", fontSize: 12 }}>{error}</p>}
            <button className="primary-btn wide" type="submit" disabled={loading}>
              <Smartphone size={16} /> {loading ? "Sending..." : "Request OTP"}
            </button>
          </form>
        )}

        {step === "otp" && (
          <form onSubmit={handleVerifyOtp}>
            <p className="muted">OTP sent to {maskedMobile}</p>
            {demoOtp && (
              <div className="demo-box" style={{ textAlign: "left" }}>
                <b>Demo mode:</b> OTP is <b>{demoOtp}</b> (shown only because DEMO_OTP_ENABLED=true)
              </div>
            )}
            <label style={{ textAlign: "left", display: "block", margin: "16px 0" }}>
              Enter 6-digit OTP
              <input
                required
                maxLength={6}
                value={code}
                onChange={(e) => setCode(e.target.value.replace(/\D/g, ""))}
                placeholder="123456"
              />
            </label>
            {error && <p style={{ color: "var(--red)", fontSize: 12 }}>{error}</p>}
            <button className="primary-btn wide" type="submit" disabled={loading || code.length !== 6}>
              {loading ? "Verifying..." : "Verify OTP"}
            </button>
            <button type="button" className="secondary-btn wide" onClick={() => setStep("mobile")}>
              Use a different number
            </button>
          </form>
        )}
      </div>
    </div>
  );
}
