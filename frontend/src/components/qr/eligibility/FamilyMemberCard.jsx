import { useId, useState } from "react";
import { ChevronDown, ChevronUp } from "lucide-react";
import EligibilityBadge from "./EligibilityBadge";
import MemberPhoto from "./MemberPhoto";
import { ELIGIBILITY_TONE, displayAadhaar } from "../../../features/qr/familyEligibility";
import { useTranslation } from "../../../i18n/useTranslation";
import { rationItemLabel, rationItemUnit } from "../../../utils/format";

// One family member: photo, name, relationship, age/gender, masked Aadhaar, ration card, status badges,
// and an expandable details panel (monthly entitlement share). Values the records don't hold are shown
// as "Not recorded", never invented.
export default function FamilyMemberCard({ member, index, rationCardNumber }) {
  const { t } = useTranslation();
  const [open, setOpen] = useState(false);
  const detailsId = useId();
  const aadhaar = displayAadhaar(member.aadhaarMasked);
  const gender = member.gender ? t(`gender_${member.gender}`) : t("not_recorded");
  const tone = ELIGIBILITY_TONE[member.eligibility] ?? "warning";

  return (
    <li className={`member-card ${member.eligibility === "Eligible" ? "" : "not-eligible"}`}>
      <div className="member-main">
        <MemberPhoto name={member.fullName} photoUrl={member.photoUrl} />
        <div className="member-body">
          <div className="member-name-row">
            <b className="member-name">
              <span className="member-index">{index + 1}.</span> {member.fullName}
            </b>
            <EligibilityBadge tone={tone}>{t(`elig_${member.eligibility}`)}</EligibilityBadge>
          </div>
          <div className="member-meta">
            {t(`rel_${member.relationship}`)} · {t("age")} {member.age} · {gender}
          </div>
          <dl className="member-facts">
            <div>
              <dt>{t("aadhaar")}</dt>
              <dd title={aadhaar ? t("masked_for_privacy") : undefined}>{aadhaar ?? t("not_recorded")}</dd>
            </div>
            <div>
              <dt>{t("ration_card")}</dt>
              <dd>{rationCardNumber || t("not_recorded")}</dd>
            </div>
          </dl>
          {member.identityVerified === true && <EligibilityBadge tone="success">{t("identity_verified")}</EligibilityBadge>}
          {member.identityVerified === false && <EligibilityBadge tone="warning">{t("identity")}: {t("not_verified")}</EligibilityBadge>}
        </div>
      </div>

      <button type="button" className="member-toggle" aria-expanded={open} aria-controls={detailsId} onClick={() => setOpen((o) => !o)}>
        {open ? t("hide_details") : t("view_details")} {open ? <ChevronUp size={15} aria-hidden="true" /> : <ChevronDown size={15} aria-hidden="true" />}
      </button>

      {open && (
        <div className="member-details" id={detailsId}>
          <dl className="member-facts">
            <div>
              <dt>{t("relationship")}</dt>
              <dd>{t(`rel_${member.relationship}`)}</dd>
            </div>
            <div>
              <dt>{t("gender")}</dt>
              <dd>{gender}</dd>
            </div>
            <div>
              <dt>{t("eligibility")}</dt>
              <dd>{t(`elig_${member.eligibility}`)}</dd>
            </div>
            <div>
              <dt>{t("identity")}</dt>
              <dd>{member.identityVerified == null ? t("not_recorded") : member.identityVerified ? t("verified") : t("not_verified")}</dd>
            </div>
          </dl>
          <span className="member-share-title">{t("monthly_share")}</span>
          {member.monthlyEntitlement?.length ? (
            <ul className="member-share">
              {member.monthlyEntitlement.map((item) => (
                <li key={item.rationType}>
                  {rationItemLabel(item.rationType)} <b>{item.quantity} {rationItemUnit(item.rationType)}</b>
                </li>
              ))}
            </ul>
          ) : (
            <p className="muted small">{t("no_monthly_share")}</p>
          )}
        </div>
      )}
    </li>
  );
}
