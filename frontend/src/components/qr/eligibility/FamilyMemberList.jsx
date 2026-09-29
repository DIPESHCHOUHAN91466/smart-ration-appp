import { RefreshCcw, Users } from "lucide-react";
import EligibilityBadge from "./EligibilityBadge";
import FamilyMemberCard from "./FamilyMemberCard";
import { familyCounts } from "../../../features/qr/familyEligibility";
import { useTranslation } from "../../../i18n/useTranslation";

// "Family Members Eligible for Collection": dynamic x / y count and one card per member.
export default function FamilyMemberList({ family, rationCardNumber, onRetry }) {
  const { t } = useTranslation();
  const members = family?.members ?? [];
  const { total, eligible, allEligible } = familyCounts(family);

  return (
    <section className="elig-card" aria-labelledby="family-members-title">
      <div className="elig-card-head">
        <div>
          <span className="eyebrow blue">{t("family_members")}</span>
          <h3 id="family-members-title">{t("family_members_eligible_title")}</h3>
          <p className="muted small">
            {total} {t("family_registered_under_card")}
            {family?.familyCode ? ` · ${family.familyCode}` : ""}
          </p>
        </div>
        <EligibilityBadge tone={allEligible ? "success" : eligible > 0 ? "warning" : "error"}>
          {allEligible ? `${total} ${t("members")} · ${t("all_eligible")}` : `${eligible} / ${total} ${t("members_eligible")}`}
        </EligibilityBadge>
      </div>

      {members.length === 0 ? (
        <div className="elig-empty" role="status">
          <Users size={22} aria-hidden="true" />
          <p>{t("no_family_records")}</p>
          {onRetry && (
            <button type="button" className="secondary-btn" onClick={onRetry}>
              <RefreshCcw size={15} /> {t("retry_verification")}
            </button>
          )}
        </div>
      ) : (
        <ul className="member-grid">
          {members.map((member, index) => (
            <FamilyMemberCard key={member.id} member={member} index={index} rationCardNumber={rationCardNumber} />
          ))}
        </ul>
      )}
    </section>
  );
}
