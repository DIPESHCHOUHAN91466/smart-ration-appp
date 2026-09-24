import { useState } from "react";
import { Camera, ShieldCheck } from "lucide-react";
import { useTranslation } from "../../i18n/useTranslation";

// Manual fallback: accepts the SRQR reference printed under the QR, or a
// pasted raw payload. Submits through exactly the same pipeline as a camera scan.
export default function QrManualInput({ onSubmit, onBackToCamera }) {
  const { t } = useTranslation();
  const [value, setValue] = useState("");

  const submit = (e) => {
    e.preventDefault();
    if (value.trim()) onSubmit(value.trim());
  };

  return (
    <form className="qr-manual" onSubmit={submit}>
      <label htmlFor="qr-manual-input">{t("enter_qr_manually")}</label>
      <textarea
        id="qr-manual-input"
        rows={3}
        autoFocus
        placeholder="SRQR-..."
        value={value}
        onChange={(e) => setValue(e.target.value)}
        spellCheck={false}
      />
      <small className="muted">{t("qr_manual_hint")}</small>
      <button type="submit" className="primary-btn wide" disabled={!value.trim()}>
        <ShieldCheck size={16} /> {t("verify")}
      </button>
      <button type="button" className="secondary-btn wide" onClick={onBackToCamera}>
        <Camera size={16} /> {t("open_camera")}
      </button>
    </form>
  );
}
