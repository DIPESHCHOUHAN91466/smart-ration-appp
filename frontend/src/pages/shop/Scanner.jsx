import { useEffect, useRef, useState } from "react";
import { AlertCircle, CheckCircle2, QrCode } from "lucide-react";
import { Html5Qrcode } from "html5-qrcode";
import PageHeader from "../../components/PageHeader";
import { EmptyState } from "../../components/EmptyState";
import { verifyQr } from "../../services/qrService";
import { completeCollection } from "../../services/shopService";
import { useToast } from "../../context/ToastContext";

export default function Scanner() {
  const [manualValue, setManualValue] = useState("");
  const [result, setResult] = useState(null);
  const [verifying, setVerifying] = useState(false);
  const [completing, setCompleting] = useState(false);
  const [cameraActive, setCameraActive] = useState(false);
  const [cameraError, setCameraError] = useState("");
  const scannerRef = useRef(null);
  const notify = useToast();

  const verify = async (value) => {
    if (!value) return;
    setVerifying(true);
    setResult(null);
    try {
      const token = await verifyQr(value);
      setResult(token);
    } catch (err) {
      setResult({ error: true, message: err.message, code: value });
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
        // scanner may already be stopped
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
          verify(decodedText);
        },
        () => {
          // per-frame scan miss — ignore, this fires continuously while scanning
        },
      );
    } catch {
      setCameraError("Could not access the camera. Use manual entry instead.");
      setCameraActive(false);
    }
  };

  useEffect(() => {
    return () => {
      stopCamera();
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const onComplete = async () => {
    setCompleting(true);
    try {
      await completeCollection(result.id);
      notify(`Collection completed for ${result.tokenNumber}`);
      setResult((r) => ({ ...r, status: "Completed" }));
    } catch (err) {
      notify(err.message || "Could not complete collection", "error");
    } finally {
      setCompleting(false);
    }
  };

  return (
    <section className="scanner-page">
      <PageHeader title="QR Verification" subtitle="Scan the customer's Smart Ration token or enter its reference manually." />
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
          <button className="secondary-btn wide" disabled={!manualValue || verifying} onClick={() => verify(manualValue)}>
            {verifying ? "Verifying..." : "Verify manually"}
          </button>
        </section>

        <section className="panel">
          {!result && <EmptyState title="Ready to verify" text="Scan a QR code or enter its reference to display customer and ration details here." />}

          {result?.error && (
            <div className="result error">
              <AlertCircle size={48} />
              <h2>QR verification failed</h2>
              <p>{result.message}</p>
              <code>{result.code}</code>
            </div>
          )}

          {result && !result.error && (
            <div className="result success-result">
              <div className="success-circle">
                <CheckCircle2 size={42} />
              </div>
              <h2>Customer Verified</h2>
              <p>Token and booking are valid for this shop.</p>
              <div className="summary">
                <div>
                  <span>Customer</span>
                  <b>{result.userName}</b>
                </div>
                <div>
                  <span>Token</span>
                  <b>{result.tokenNumber}</b>
                </div>
                <div>
                  <span>Arrival</span>
                  <b>{result.startTime.slice(0, 5)}</b>
                </div>
                <div>
                  <span>Ration</span>
                  <b>{result.items.map((i) => `${i.rationType} ${i.quantity}`).join(" • ")}</b>
                </div>
              </div>
              {result.status !== "Completed" ? (
                <button className="primary-btn wide" onClick={onComplete} disabled={completing}>
                  <CheckCircle2 /> {completing ? "Completing..." : "Mark Collection Complete"}
                </button>
              ) : (
                <p className="muted" style={{ color: "var(--green)" }}>
                  Collection already completed for this token.
                </p>
              )}
            </div>
          )}
        </section>
      </div>
    </section>
  );
}
