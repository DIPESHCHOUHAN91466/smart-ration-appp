import { useTranslation } from "../../../i18n/useTranslation";

// Compact verification timeline, driven by the server's verification summary (not decoration: a step
// the server did not pass is shown as not passed).
export default function VerificationSteps({ summary, ready }) {
  const { t } = useTranslation();
  const steps = [
    ["step_qr_scanned", true],
    ["step_customer_identified", true],
    ["step_ration_card_verified", Boolean(summary?.passbookVerified)],
    ["step_family_checked", Boolean(summary?.familyEligible)],
    ["step_entitlement_calculated", Boolean(summary?.entitlementAvailable)],
  ];
  return (
    <section className="elig-card" aria-labelledby="verification-steps-title">
      <span className="eyebrow blue" id="verification-steps-title">{t("verification_steps")}</span>
      <ol className="elig-steps">
        {steps.map(([key, done]) => (
          <li key={key} className={done ? "done" : "failed"}>
            <span className="elig-step-dot" aria-hidden="true">{done ? "✓" : "✕"}</span>
            {t(key)}
            <span className="sr-only">: {done ? t("verified") : t("not_verified")}</span>
          </li>
        ))}
        <li className={ready ? "current" : "failed"}>
          <span className="elig-step-dot" aria-hidden="true">{ready ? "●" : "✕"}</span>
          {ready ? t("step_ready") : t("step_blocked")}
        </li>
      </ol>
    </section>
  );
}
