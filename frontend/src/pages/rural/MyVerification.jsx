import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { User } from "lucide-react";
import PageHeader from "../../components/PageHeader";
import { ErrorState, LoadingState } from "../../components/EmptyState";
import VerificationStatusCard from "../../components/verification/VerificationStatusCard";
import FamilyMembersTable from "../../components/verification/FamilyMembersTable";
import EntitlementTable from "../../components/verification/EntitlementTable";
import { getMyProfile, getEntitlement } from "../../services/beneficiariesService";
import { useTranslation } from "../../i18n/useTranslation";

export default function MyVerification() {
  const { t } = useTranslation();
  const [profile, setProfile] = useState(null);
  const [entitlement, setEntitlement] = useState(null);
  const [error, setError] = useState("");

  const load = () => {
    setError("");
    setProfile(null);
    getMyProfile()
      .then(async (p) => {
        setProfile(p);
        const e = await getEntitlement(p.beneficiary.id);
        setEntitlement(e);
      })
      .catch((err) => setError(err.message));
  };

  useEffect(load, []);

  if (error) return <ErrorState text={error} onRetry={load} />;
  if (!profile) return <LoadingState text="Loading your verification profile..." />;

  return (
    <>
      <PageHeader
        title="My Verification"
        subtitle="Your Aadhaar, passbook, mobile verification and ration entitlement status."
        action={
          <Link className="secondary-btn" to={`/beneficiary/${profile.beneficiary.id}`}>
            <User size={16} /> View Full 360° Profile
          </Link>
        }
      />

      <div className="demo-box" style={{ marginBottom: 18 }}>
        <b>SYNTHETIC / DEMO VERIFICATION MODE</b> — this is demo verification data, not real Aadhaar/government
        verification.
      </div>

      <div className="item-grid" style={{ gridTemplateColumns: "repeat(3,1fr)", marginBottom: 18 }}>
        <VerificationStatusCard
          title="AADHAAR VERIFICATION"
          status={profile.aadhaarVerification.status}
          rows={[
            { label: "Masked Aadhaar", value: profile.aadhaarVerification.aadhaarMasked },
            { label: "Mode", value: profile.aadhaarVerification.verificationMode.replace("_", " ") },
          ]}
        />
        <VerificationStatusCard
          title="PASSBOOK VERIFICATION"
          status={profile.passbookVerification.verificationStatus}
          rows={[
            { label: "Passbook ID", value: profile.passbookVerification.passbookNumber },
            { label: "Status", value: profile.passbookVerification.status },
          ]}
        />
        <VerificationStatusCard
          title="MOBILE VERIFICATION"
          status={profile.mobileVerification.status}
          rows={[{ label: "Mobile", value: profile.mobileVerification.mobileMasked }]}
        />
      </div>

      {/* After a number change the new number starts unverified; a code sent to it fixes that (no office visit). */}
      {profile.mobileVerification.status !== "Verified" && (
        <p className="info-callout" role="note" style={{ marginTop: 0, marginBottom: 18 }}>{t("mobile_reverify_hint")}</p>
      )}

      <div style={{ marginBottom: 18 }}>
        <FamilyMembersTable family={profile.family} />
      </div>

      {entitlement && <EntitlementTable entitlement={entitlement} />}
    </>
  );
}
