import { useState } from "react";
import { AlertTriangle, ArrowRight, CheckCircle2, Keyboard, RefreshCcw, ScanLine, XCircle } from "lucide-react";
import { QR_STATUS, QR_STATUS_META } from "../../features/qr/qrContract";
import { useTranslation } from "../../i18n/useTranslation";
import CustomerSummary from "./eligibility/CustomerSummary";
import FamilyMemberList from "./eligibility/FamilyMemberList";
import RationEntitlement from "./eligibility/RationEntitlement";
import VerificationSteps from "./eligibility/VerificationSteps";

const TONE_ICON = { success: CheckCircle2, warning: AlertTriangle, error: XCircle };

// Verification outcome. Everything shown comes from the server's verification (the source of truth for
// identity, eligibility, entitlement and collection status); Aadhaar is only ever the masked last 4.
// Layout, most important first: status -> token/customer/ration card -> family -> what was verified ->
// what may be issued -> actions.
export default function QrScanResult({ result, onContinue, onScanAgain, onManual, onRetry }) {
  const { t, language } = useTranslation();
  const [verifiedAt] = useState(() => new Date());
  const meta = QR_STATUS_META[result.status] ?? QR_STATUS_META[QR_STATUS.INVALID_FORMAT];
  const Icon = TONE_ICON[meta.tone];
  const v = result.verification;
  const booking = v?.booking;
  const ready = result.status === QR_STATUS.VERIFIED;

  // Server-provided reason for eligibility blocks (e.g. "Aadhaar verification is pending.").
  const description = meta.descKey ? t(meta.descKey) : result.message;
  const time = verifiedAt.toLocaleTimeString(language === "en" ? "en-IN" : `${language}-IN`, { hour: "2-digit", minute: "2-digit" });

  return (
    <div className={`qr-result tone-${meta.tone} ${booking ? "rich" : ""}`}>
      <div className="qr-result-head" role="status" aria-live="assertive">
        <div className="qr-result-icon">
          <Icon size={34} />
        </div>
        {ready ? (
          <>
            <h2>{t("customer_verified")}</h2>
            <p>{t("eligible_for_ration_collection")}</p>
            <p className="qr-result-time">
              {t("qr_verified")} · {t("verified_at")} {time}
            </p>
          </>
        ) : (
          <>
            <h2>{t(meta.titleKey)}</h2>
            <p>{description}</p>
          </>
        )}
      </div>

      {booking && (
        <div className="elig-layout">
          <div className="elig-col">
            <CustomerSummary verification={v} ready={ready} />
            <VerificationSteps summary={v.verificationSummary} ready={ready} />
          </div>
          <div className="elig-col">
            <FamilyMemberList family={v.family} rationCardNumber={v.passbookVerification?.passbookNumber} onRetry={onRetry} />
            {ready && <RationEntitlement verification={v} />}
          </div>
        </div>
      )}

      <div className="qr-result-actions">
        {ready && (
          <button type="button" className="primary-btn wide elig-continue" onClick={onContinue} autoFocus>
            {t("continue_distribution")} <ArrowRight size={18} />
          </button>
        )}
        {result.status === QR_STATUS.NETWORK_ERROR && (
          <button type="button" className="primary-btn wide" onClick={onRetry} autoFocus>
            <RefreshCcw size={16} /> {t("try_again")}
          </button>
        )}
        {!ready && booking && (
          <button type="button" className="secondary-btn wide" onClick={onContinue}>
            {t("view_full_details")} <ArrowRight size={16} />
          </button>
        )}
        <button
          type="button"
          className={ready || result.status === QR_STATUS.NETWORK_ERROR ? "secondary-btn wide" : "primary-btn wide"}
          onClick={onScanAgain}
          autoFocus={!ready && result.status !== QR_STATUS.NETWORK_ERROR}
        >
          <ScanLine size={16} /> {ready ? t("scan_another_qr") : t("scan_again")}
        </button>
        {!ready && (
          <button type="button" className="secondary-btn wide" onClick={onManual}>
            <Keyboard size={16} /> {t("enter_qr_manually")}
          </button>
        )}
      </div>
    </div>
  );
}
