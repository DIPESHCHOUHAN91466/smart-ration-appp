import { useEffect, useState } from "react";
import { useLocation, useNavigate } from "react-router-dom";
import { AlertCircle, QrCode, Smartphone } from "lucide-react";
import PageHeader from "../../components/PageHeader";
import BeneficiaryVerificationPanel from "../../components/verification/BeneficiaryVerificationPanel";
import OtpModal from "../../components/verification/OtpModal";
import CollectionReceipt from "../../components/verification/CollectionReceipt";
import { scanQr } from "../../services/qrService";
import { precheckQr } from "../../features/qr/qrValidation";
import { QR_STATUS_META } from "../../features/qr/qrContract";
import { confirmCollection } from "../../services/collectionService";
import { openGlobalQrScanner } from "../../state/qrScannerStore";
import { useTranslation } from "../../i18n/useTranslation";
import { useToast } from "../../state/toast";

const VERIFYING_STEPS = [
  "Token verified",
  "Beneficiary verified",
  "Aadhaar status checked",
  "Passbook status checked",
  "Family eligibility checked",
  "Entitlement calculated",
];

export default function Scanner() {
  const [manualValue, setManualValue] = useState("");
  const [verifying, setVerifying] = useState(false);
  const [verifyError, setVerifyError] = useState(null);
  const [verification, setVerification] = useState(null);
  const [verificationMethod, setVerificationMethod] = useState("QR");
  const [receipt, setReceipt] = useState(null);
  const [confirming, setConfirming] = useState(false);
  const [showOtpModal, setShowOtpModal] = useState(false);
  const notify = useToast();
  const { t } = useTranslation();
  const location = useLocation();
  const navigate = useNavigate();

  // Arriving from the global scanner's "Continue Distribution": show the
  // verification it already fetched, then clear the history state so a
  // refresh doesn't resurrect a stale result.
  useEffect(() => {
    const incoming = location.state?.verification;
    if (!incoming) return;
    setVerification(incoming);
    setVerificationMethod("QR");
    setVerifyError(null);
    setReceipt(null);
    setManualValue(location.state.qrValue || "");
    navigate(location.pathname, { replace: true, state: null });
  }, [location.key]); // eslint-disable-line react-hooks/exhaustive-deps

  const reset = () => {
    setVerification(null);
    setVerifyError(null);
    setReceipt(null);
    setManualValue("");
  };

  const runVerify = async (value) => {
    setVerifyError(null);
    setVerification(null);
    setVerifying(true);
    const check = precheckQr(value);
    if (!check.ok) {
      setVerifyError({ message: t(QR_STATUS_META[check.status].descKey), code: value });
      setVerifying(false);
      return;
    }
    try {
      // Same pipeline as the camera scanner (signed envelope or SRQR reference).
      const result = await scanQr(check.value);
      if (result.verification) {
        setVerification(result.verification);
        setVerificationMethod("QR");
      } else {
        setVerifyError({ message: result.message, code: value });
      }
    } catch (err) {
      setVerifyError({ message: err.message, code: value });
    } finally {
      setVerifying(false);
    }
  };

  const onOtpVerified = (result) => {
    setShowOtpModal(false);
    setVerification(result);
    setVerificationMethod("OTP");
    setVerifyError(null);
  };

  const onConfirm = async () => {
    setConfirming(true);
    try {
      const result = await confirmCollection(verification.booking.tokenId, verificationMethod);
      setReceipt(result);
      notify(`Collection confirmed: ${result.collectionCode}`);
    } catch (err) {
      notify(err.message || "Could not confirm collection", "error");
      // Re-fetch so the blocked-reason banner reflects the latest state.
      if (verificationMethod === "QR" && manualValue) {
        runVerify(manualValue);
      }
    } finally {
      setConfirming(false);
    }
  };

  if (receipt) {
    return (
      <>
        <PageHeader title="Beneficiary Verification" subtitle="Ration issuance receipt." />
        <CollectionReceipt receipt={receipt} onDone={reset} />
      </>
    );
  }

  if (verification) {
    return (
      <>
        <PageHeader title="Beneficiary Verification" subtitle="Review verification and entitlement before issuing ration." />
        <BeneficiaryVerificationPanel verification={verification} onConfirm={onConfirm} onCancel={reset} confirming={confirming} />
      </>
    );
  }

  return (
    <section className="scanner-page">
      <PageHeader title="Scan Beneficiary QR" subtitle="Scan the beneficiary's Smart Ration token or enter its reference manually." />
      <div className="scanner-layout">
        <section className="panel">
          <div className="scanner-frame">
            <QrCode size={48} />
            <p>{t("scan_customer_qr")}</p>
            <small>{t("align_qr")}</small>
          </div>

          <button className="primary-btn wide" onClick={openGlobalQrScanner} aria-label={t("open_qr_scanner")}>
            <QrCode /> {t("open_camera")}
          </button>

          <div className="or">
            <span>OR</span>
          </div>
          <label>
            Enter QR reference
            <input placeholder="SRQR-..." value={manualValue} onChange={(e) => setManualValue(e.target.value)} />
          </label>
          <button className="secondary-btn wide" disabled={!manualValue || verifying} onClick={() => runVerify(manualValue)}>
            {verifying ? "Verifying..." : "Verify manually"}
          </button>

          <div className="or">
            <span>OR</span>
          </div>
          <button className="secondary-btn wide" onClick={() => setShowOtpModal(true)}>
            <Smartphone size={16} /> Can't Scan QR? Use Mobile OTP
          </button>
        </section>

        <section className="panel">
          {verifying && (
            <div className="result">
              <div className="success-circle">
                <QrCode size={30} />
              </div>
              <h2>Verifying beneficiary...</h2>
              <ul style={{ textAlign: "left", listStyle: "none", padding: 0, marginTop: 18 }}>
                {VERIFYING_STEPS.map((step) => (
                  <li key={step} style={{ padding: "6px 0", fontSize: 12, color: "var(--muted)" }}>
                    ⏳ {step}
                  </li>
                ))}
              </ul>
            </div>
          )}

          {!verifying && verifyError && (
            <div className="result error">
              <AlertCircle size={48} />
              <h2>QR verification failed</h2>
              <p>{verifyError.message}</p>
              <code>{verifyError.code}</code>
            </div>
          )}

          {!verifying && !verifyError && (
            <div className="empty">
              <QrCode size={42} />
              <h2>Ready to verify</h2>
              <p>Scan a QR code, enter its reference, or use Mobile OTP to display beneficiary and entitlement details here.</p>
            </div>
          )}
        </section>
      </div>

      {showOtpModal && <OtpModal onClose={() => setShowOtpModal(false)} onVerified={onOtpVerified} />}
    </section>
  );
}
