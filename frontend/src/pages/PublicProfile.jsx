import { useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import { CheckCircle2, MapPin, ShieldCheck, Store, XCircle } from "lucide-react";
import { getPublicBeneficiaryProfile } from "../services/publicService";
import { LoadingState, ErrorState } from "../components/EmptyState";

export default function PublicProfile() {
  const { publicReference } = useParams();
  const [profile, setProfile] = useState(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);

  const load = () => {
    setLoading(true);
    setError("");
    getPublicBeneficiaryProfile(publicReference)
      .then(setProfile)
      .catch((err) => setError(err.message || "Profile not found."))
      .finally(() => setLoading(false));
  };

  useEffect(load, [publicReference]);

  return (
    <div className="login-page" style={{ gridTemplateColumns: "1fr" }}>
      <div className="login-card-wrap">
        <div className="login-card" style={{ maxWidth: 480 }}>
          <span className="eyebrow blue">PUBLIC VERIFICATION BADGE</span>
          <h2>Smart Ration Beneficiary</h2>
          <p>A minimal, public verification view. No Aadhaar, mobile, address or family details are ever shown here.</p>

          {loading && <LoadingState text="Loading profile..." />}
          {!loading && error && <ErrorState title="Profile not found" text={error} onRetry={load} />}

          {!loading && !error && profile && (
            <>
              <div className="success-circle">
                {profile.verificationBadge === "Verified" ? <CheckCircle2 size={34} /> : <XCircle size={34} />}
              </div>
              <h2 style={{ textAlign: "center" }}>{profile.beneficiaryCode}</h2>
              <div className="summary">
                <div>
                  <span>Verification</span>
                  <b>
                    <ShieldCheck size={13} style={{ verticalAlign: "middle", marginRight: 4 }} />
                    {profile.verificationBadge}
                  </b>
                </div>
                <div>
                  <span>Scheme Eligibility</span>
                  <b>{profile.eligibilityBadge}</b>
                </div>
                <div>
                  <span>Scheme</span>
                  <b>{profile.schemeCode}</b>
                </div>
                <div>
                  <span>Ration Shop</span>
                  <b>
                    <Store size={13} style={{ verticalAlign: "middle", marginRight: 4 }} />
                    {profile.shopCode}
                  </b>
                </div>
                <div>
                  <span>Region</span>
                  <b>
                    <MapPin size={13} style={{ verticalAlign: "middle", marginRight: 4 }} />
                    {profile.region}
                  </b>
                </div>
                <div>
                  <span>Last Collection</span>
                  <b>{profile.lastCollectionMonth || "No collection yet"}</b>
                </div>
              </div>
              <div className="login-trust">
                <ShieldCheck /> Synthetic Demo Data <span /> 🔒 No Personal Data Exposed
              </div>
            </>
          )}
        </div>
      </div>
    </div>
  );
}
