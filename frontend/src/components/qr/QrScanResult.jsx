import { AlertTriangle, ArrowRight, CheckCircle2, Keyboard, RefreshCcw, ScanLine, XCircle } from "lucide-react";
import { QR_STATUS, QR_STATUS_META } from "../../qr/qrContract";
import { useTranslation } from "../../i18n/useTranslation";

const TONE_ICON = { success: CheckCircle2, warning: AlertTriangle, error: XCircle };

// "EdibleOil" -> "Edible Oil"; oil is measured in litres, everything else in kg.
const itemLabel = (rationType) => rationType.replace(/([a-z])([A-Z])/g, "$1 $2");
const itemUnit = (rationType) => (rationType === "EdibleOil" ? "L" : "kg");

function formatDate(isoDate, language) {
  const date = new Date(`${isoDate}T00:00:00`);
  if (Number.isNaN(date.getTime())) return isoDate;
  const locale = { hi: "hi-IN", mr: "mr-IN" }[language] ?? "en-IN";
  return date.toLocaleDateString(locale, { day: "numeric", month: "long", year: "numeric" });
}

// Verification outcome. Shows only non-sensitive booking data (masked
// mobile, no Aadhaar) — the full profile stays on the distribution screen.
export default function QrScanResult({ result, onContinue, onScanAgain, onManual, onRetry }) {
  const { t, language } = useTranslation();
  const meta = QR_STATUS_META[result.status] ?? QR_STATUS_META[QR_STATUS.INVALID_FORMAT];
  const Icon = TONE_ICON[meta.tone];
  const v = result.verification;
  const booking = v?.booking;
  const allocations = (v?.entitlement?.items ?? []).filter((i) => i.todayAllocation > 0);

  // Server-provided reason for eligibility blocks (e.g. "Aadhaar verification is pending.").
  const description = meta.descKey ? t(meta.descKey) : result.message;

  return (
    <div className={`qr-result tone-${meta.tone}`}>
      <div className="qr-result-head" role="status" aria-live="assertive">
        <div className="qr-result-icon">
          <Icon size={34} />
        </div>
        <h2>{t(meta.titleKey)}</h2>
        <p>{description}</p>
      </div>

      {booking && (
        <section className="qr-result-card" aria-label={t("customer_verification")}>
          <span className="eyebrow blue">{t("customer_verification")}</span>
          <dl className="qr-result-grid">
            <div>
              <dt>{t("token_number")}</dt>
              <dd className="qr-token">{booking.tokenNumber}</dd>
            </div>
            <div>
              <dt>{t("customer")}</dt>
              <dd>{v.beneficiary.fullName}</dd>
            </div>
            <div>
              <dt>{t("ration_shop")}</dt>
              <dd>{booking.shopName}</dd>
            </div>
            <div>
              <dt>{t("collection_slot")}</dt>
              <dd>{booking.bookingTime}</dd>
            </div>
            <div>
              <dt>{t("date")}</dt>
              <dd>{formatDate(booking.collectionDate, language)}</dd>
            </div>
            <div>
              <dt>{t("scheme")}</dt>
              <dd>{v.entitlement?.schemeCode ?? "—"}</dd>
            </div>
            <div>
              <dt>{t("family_members")}</dt>
              <dd>{v.family?.familySize ?? "—"}</dd>
            </div>
            <div>
              <dt>{t("mobile")}</dt>
              <dd>{v.beneficiary.mobileMasked}</dd>
            </div>
          </dl>

          {result.status === QR_STATUS.VERIFIED && allocations.length > 0 && (
            <>
              <span className="eyebrow blue">{t("ration_entitlement")}</span>
              <ul className="qr-entitlement">
                {allocations.map((item) => (
                  <li key={item.rationType}>
                    <span>{itemLabel(item.rationType)}</span>
                    <b>
                      {item.todayAllocation} {itemUnit(item.rationType)}
                    </b>
                  </li>
                ))}
              </ul>
            </>
          )}
        </section>
      )}

      <div className="qr-result-actions">
        {result.status === QR_STATUS.VERIFIED && (
          <button type="button" className="primary-btn wide" onClick={onContinue} autoFocus>
            {t("continue_distribution")} <ArrowRight size={16} />
          </button>
        )}
        {result.status === QR_STATUS.NETWORK_ERROR && (
          <button type="button" className="primary-btn wide" onClick={onRetry} autoFocus>
            <RefreshCcw size={16} /> {t("try_again")}
          </button>
        )}
        {result.status !== QR_STATUS.VERIFIED && booking && (
          <button type="button" className="secondary-btn wide" onClick={onContinue}>
            {t("view_full_details")} <ArrowRight size={16} />
          </button>
        )}
        <button
          type="button"
          className={result.status === QR_STATUS.VERIFIED || result.status === QR_STATUS.NETWORK_ERROR ? "secondary-btn wide" : "primary-btn wide"}
          onClick={onScanAgain}
          autoFocus={result.status !== QR_STATUS.VERIFIED && result.status !== QR_STATUS.NETWORK_ERROR}
        >
          <ScanLine size={16} /> {result.status === QR_STATUS.VERIFIED ? t("scan_another_qr") : t("scan_again")}
        </button>
        {result.status !== QR_STATUS.VERIFIED && (
          <button type="button" className="secondary-btn wide" onClick={onManual}>
            <Keyboard size={16} /> {t("enter_qr_manually")}
          </button>
        )}
      </div>
    </div>
  );
}
