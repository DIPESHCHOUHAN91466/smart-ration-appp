import { useEffect, useRef, useState } from "react";
import { AlertCircle, QrCode, Smartphone } from "lucide-react";
import { Html5Qrcode } from "html5-qrcode";
import PageHeader from "../../components/PageHeader";
import BeneficiaryVerificationPanel from "../../components/verification/BeneficiaryVerificationPanel";
import OtpModal from "../../components/verification/OtpModal";
import CollectionReceipt from "../../components/verification/CollectionReceipt";
import { verifyByQr } from "../../services/verificationService";
import { confirmCollection } from "../../services/collectionService";
import { useToast } from "../../context/ToastContext";

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
  const [cameraActive, setCameraActive] = useState(false);
  const [cameraError, setCameraError] = useState("");
  const scannerRef = useRef(null);
  const notify = useToast();

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
    try {
      const result = await verifyByQr(value);
      setVerification(result);
      setVerificationMethod("QR");
    } catch (err) {
      setVerifyError({ message: err.message, code: value });
    } finally {
      setVerifying(false);
    }
  };

  const stopCamera = async () => {
    if (scannerRef.current) {
      try {
        await scannerRef.current.stop();
        await scannerRef.current.clear();
      } catch {
        // already stopped
      }
      scannerRef.current = null;
    }
    setCameraActive(false);
  };

  const startCamera = async () => {
    setCameraError("");
    try {
      const scanner = new Html5Qrcode("qr-reader");
      scannerRef.current = scanner;
      setCameraActive(true);
      await scanner.start(
        { facingMode: "environment" },
        { fps: 10, qrbox: 220 },
        (decodedText) => {
          setManualValue(decodedText);
          stopCamera();
          runVerify(decodedText);
        },
        () => {},
      );
    } catch {
      setCameraError("Could not access the camera. Use manual entry or Mobile OTP instead.");
      setCameraActive(false);
    }
  };

  useEffect(() => {
    return () => {
      stopCamera();
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

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
            {cameraActive ? (
              <div id="qr-reader" style={{ width: "100%", height: "100%" }} />
            ) : (
              <>
                <QrCode size={48} />
                <p>Camera scanner</p>
                <small>Point the camera at the QR code</small>
              </>
            )}
          </div>

          {!cameraActive ? (
            <button className="primary-btn wide" onClick={startCamera}>
              <QrCode /> Start Camera Scanner
            </button>
          ) : (
            <button className="secondary-btn wide" onClick={stopCamera}>
              Stop Camera
            </button>
          )}
          {cameraError && (
            <p className="muted" style={{ color: "var(--red)" }}>
              {cameraError}
            </p>
          )}

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
