import EligibilityBadge from "./EligibilityBadge";
import { familyCounts } from "../../../features/qr/familyEligibility";
import { useTranslation } from "../../../i18n/useTranslation";
import { formatDate } from "../../../utils/format";

// Who, which token, which ration card: the prominent token plus the customer / booking facts.
export default function CustomerSummary({ verification, ready }) {
  const { t, language } = useTranslation();
  const { beneficiary, booking, entitlement, passbookVerification: card, verificationSummary: summary } = verification;
  const { total, eligible, allEligible } = familyCounts(verification.family);

  return (
    <section className="elig-card" aria-labelledby="customer-summary-title">
      <span className="eyebrow blue" id="customer-summary-title">{t("customer_verification")}</span>

      <div className="elig-token">
        <div>
          <span className="elig-token-label">{t("token")}</span>
          <strong className="elig-token-number">{booking.tokenNumber}</strong>
        </div>
        <EligibilityBadge tone={ready ? "success" : "warning"}>{ready ? t("ready_for_collection") : t("step_blocked")}</EligibilityBadge>
      </div>

      <dl className="elig-facts">
        <div className="span-2">
          <dt>{t("customer")}</dt>
          <dd className="elig-customer">{beneficiary.fullName}</dd>
        </div>
        <div>
          <dt>{t("ration_card")}</dt>
          <dd>
            {card?.passbookNumber ?? t("not_recorded")}
            {card?.verificationStatus === "Verified" && <EligibilityBadge tone="success">{t("ration_card_valid")}</EligibilityBadge>}
          </dd>
        </div>
        <div>
          <dt>{t("scheme")}</dt>
          <dd>{entitlement?.schemeCode ?? "—"}</dd>
        </div>
        <div>
          <dt>{t("ration_shop")}</dt>
          <dd>{booking.shopName}</dd>
        </div>
        <div>
          <dt>{t("collection_slot")}</dt>
          <dd>
            {formatDate(booking.collectionDate, language)} · {booking.bookingTime}
          </dd>
        </div>
        <div>
          <dt>{t("family_members")}</dt>
          <dd>
            {allEligible ? `${total} · ${t("all_eligible")}` : `${eligible} / ${total} ${t("members_eligible")}`}
          </dd>
        </div>
        <div>
          <dt>{t("mobile")}</dt>
          <dd>{beneficiary.mobileMasked}</dd>
        </div>
      </dl>

      <div className="elig-badge-row" aria-label={t("verification_steps")}>
        <EligibilityBadge tone="success">{t("qr_verified")}</EligibilityBadge>
        <EligibilityBadge tone={summary?.aadhaarVerified ? "success" : "warning"}>
          {summary?.aadhaarVerified ? t("identity_verified") : `${t("identity")}: ${t("not_verified")}`}
        </EligibilityBadge>
        <EligibilityBadge tone={summary?.familyEligible ? "success" : "error"}>
          {summary?.familyEligible ? t("elig_Eligible") : t("elig_NotEligible")}
        </EligibilityBadge>
      </div>
    </section>
  );
}
