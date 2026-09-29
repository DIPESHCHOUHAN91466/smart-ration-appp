import { useState } from "react";
import { initials } from "../../../features/qr/familyEligibility";
import { useTranslation } from "../../../i18n/useTranslation";

// Passport-style photo (rounded rectangle). Uses the stored photo when there is one; if there is none,
// or it fails to load, a clean initials tile is shown instead — never a broken image or a stock picture.
export default function MemberPhoto({ name, photoUrl }) {
  const { t } = useTranslation();
  const [failed, setFailed] = useState(false);
  if (photoUrl && !failed) {
    return (
      <img className="member-photo" src={photoUrl} alt={`${t("photo_of")} ${name}`} loading="lazy" decoding="async" onError={() => setFailed(true)} />
    );
  }
  return (
    <span className="member-photo initials" role="img" aria-label={`${t("photo_of")} ${name}`}>
      {initials(name)}
    </span>
  );
}
