import { useCallback, useEffect, useRef, useState } from "react";
import { useNavigate } from "react-router-dom";
import { ArrowLeft, Loader2, X } from "lucide-react";
import QrCameraPreview from "./QrCameraPreview";
import QrManualInput from "./QrManualInput";
import QrScanResult from "./QrScanResult";
import { precheckQr } from "../../features/qr/qrValidation";
import { scanQr } from "../../services/qrService";
import { QR_STATUS } from "../../features/qr/qrContract";
import { useTranslation } from "../../i18n/useTranslation";
import { qrLog, qrMark } from "../../features/qr/qrTiming";

const VIEW = { CAMERA: "camera", MANUAL: "manual", VERIFYING: "verifying", RESULT: "result" };

// Full-screen (mobile) / large modal (desktop) scanner. Lazy-loaded by
// GlobalQrScanner so the QR decoder is only downloaded when first opened.
export default function QrScannerModal({ onClose }) {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const [view, setView] = useState(VIEW.CAMERA);
  const [result, setResult] = useState(null);
  const inFlightRef = useRef(false);
  const lastValueRef = useRef("");
  const closeBtnRef = useRef(null);

  // One verification at a time: a second decode while a request is pending is dropped.
  const verify = useCallback(async (rawText) => {
    if (inFlightRef.current) return;

    const check = precheckQr(rawText);
    if (!check.ok) {
      setResult({ status: check.status, verified: false });
      setView(VIEW.RESULT);
      return;
    }

    inFlightRef.current = true;
    lastValueRef.current = check.value;
    setView(VIEW.VERIFYING);
    qrMark("apiStart");
    try {
      const response = await scanQr(check.value);
      qrMark("apiEnd");
      qrLog("API round trip", "apiStart", "apiEnd");
      qrLog("Total (first camera frame -> result)", "scanStart", "apiEnd");
      setResult(response);
    } catch (err) {
      // 401 is handled globally (refresh / redirect to login); everything
      // else that isn't a structured scan result is a transport problem.
      setResult({ status: QR_STATUS.NETWORK_ERROR, verified: false, message: err.message });
    } finally {
      inFlightRef.current = false;
      setView(VIEW.RESULT);
    }
  }, []);

  const scanAgain = () => {
    setResult(null);
    setView(VIEW.CAMERA);
  };

  const continueToDistribution = () => {
    navigate("/shop/scanner", { state: { verification: result.verification, qrValue: lastValueRef.current } });
    onClose();
  };

  useEffect(() => {
    closeBtnRef.current?.focus();
    const onKey = (e) => {
      if (e.key === "Escape") onClose();
    };
    document.addEventListener("keydown", onKey);
    const previousOverflow = document.body.style.overflow;
    document.body.style.overflow = "hidden";
    return () => {
      document.removeEventListener("keydown", onKey);
      document.body.style.overflow = previousOverflow;
    };
  }, [onClose]);

  const showBack = view === VIEW.MANUAL || view === VIEW.RESULT;

  return (
    <div className="qr-modal-backdrop" onMouseDown={(e) => e.target === e.currentTarget && onClose()}>
      <div className="qr-modal" role="dialog" aria-modal="true" aria-labelledby="qr-modal-title">
        <header className="qr-modal-header">
          {showBack ? (
            <button type="button" className="qr-header-btn" onClick={scanAgain} aria-label={t("back")}>
              <ArrowLeft size={20} />
            </button>
          ) : (
            <span className="qr-header-spacer" />
          )}
          <h2 id="qr-modal-title">
            {view === VIEW.RESULT && result?.status === QR_STATUS.VERIFIED ? t("elig_title") : t("scan_customer_qr")}
          </h2>
          <button ref={closeBtnRef} type="button" className="qr-header-btn" onClick={onClose} aria-label={t("close_scanner")}>
            <X size={20} />
          </button>
        </header>

        <div className="qr-modal-body">
          {view === VIEW.CAMERA && (
            <QrCameraPreview
              onDecode={verify}
              onManual={() => setView(VIEW.MANUAL)}
              onImageError={() => {
                setResult({ status: QR_STATUS.INVALID_FORMAT, verified: false });
                setView(VIEW.RESULT);
              }}
            />
          )}

          {view === VIEW.MANUAL && <QrManualInput onSubmit={verify} onBackToCamera={scanAgain} />}

          {view === VIEW.VERIFYING && (
            <div className="qr-verifying" role="status" aria-live="polite">
              <Loader2 className="qr-spin" size={42} />
              <b>{t("verifying_customer")}</b>
              <small className="qr-verifying-step">✓ {t("qr_detected")}</small>
              <small className="muted">{t("verifying_checks")}</small>
            </div>
          )}

          {view === VIEW.RESULT && result && (
            <QrScanResult
              result={result}
              onContinue={continueToDistribution}
              onScanAgain={scanAgain}
              onManual={() => setView(VIEW.MANUAL)}
              onRetry={() => verify(lastValueRef.current)}
            />
          )}
        </div>
      </div>
    </div>
  );
}
