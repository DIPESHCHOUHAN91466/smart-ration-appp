import { useEffect, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import {
  ArrowLeft, CheckCircle2, Clock3, MapPin, Phone, QrCode, ShieldAlert, ShieldCheck, Sparkles, User, XCircle,
} from "lucide-react";
import PageHeader from "../../components/PageHeader";
import { LoadingState, ErrorState } from "../../components/EmptyState";
import FamilyMembersTable from "../../components/verification/FamilyMembersTable";
import EntitlementTable from "../../components/verification/EntitlementTable";
import VerificationStatusCard from "../../components/verification/VerificationStatusCard";
import { getFullProfile } from "../../services/beneficiariesService";

const TABS = [
  { key: "overview", label: "Overview" },
  { key: "family", label: "Family & Ration Card" },
  { key: "entitlement", label: "Entitlement" },
  { key: "verification", label: "Verification" },
  { key: "qr", label: "QR & Collection History" },
  { key: "ai", label: "AI Insights & Audit" },
];

const RISK_TONE = { Low: "success", Medium: "warning", High: "danger" };

export default function BeneficiaryProfile() {
  const { id } = useParams();
  const navigate = useNavigate();
  const [profile, setProfile] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [tab, setTab] = useState("overview");

  const load = () => {
    setLoading(true);
    setError(null);
    getFullProfile(id)
      .then(setProfile)
      .catch((err) => setError(err.message || "Could not load beneficiary profile."))
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [id]);

  if (loading) return <LoadingState text="Loading beneficiary profile..." />;
  if (error) return <ErrorState text={error} onRetry={load} />;
  if (!profile) return null;

  const { profile: p, family, rationCard, aadhaarVerification, passbookVerification, mobileVerification, entitlement, currentQr, collectionHistory, verificationHistory, qrScanHistory, aiInsight } = profile;

  return (
    <>
      <PageHeader
        title={p.fullName}
        subtitle={`${p.beneficiaryCode} • ${p.village}, ${p.district}, ${p.state}`}
        action={
          <button className="secondary-btn" onClick={() => navigate(-1)}>
            <ArrowLeft size={16} /> Back
          </button>
        }
      />

      <div className="demo-box" style={{ marginBottom: 18 }}>
        <b>SYNTHETIC / DEMO DATA</b> — every field on this profile (demographics, Aadhaar, passbook, AI insight) is
        synthetic demo data, not a real government record.
      </div>

      <section className="panel" style={{ marginBottom: 18, display: "flex", gap: 18, alignItems: "center" }}>
        <div className="avatar" style={{ width: 64, height: 64, fontSize: 22 }}>
          {p.profilePhotoUrl ? <img src={p.profilePhotoUrl} alt={p.fullName} style={{ width: "100%", height: "100%", borderRadius: "50%" }} /> : (p.fullName || "?")[0].toUpperCase()}
        </div>
        <div className="grow">
          <div style={{ display: "flex", gap: 10, alignItems: "center", marginBottom: 4 }}>
            <b style={{ fontSize: 16 }}>{p.fullName}</b>
            <span className={`status ${p.isBlocked ? "danger" : p.isActive ? "success" : "warning"}`}>
              {p.isBlocked ? "BLOCKED" : p.isActive ? "ACTIVE" : "INACTIVE"}
            </span>
          </div>
          <small className="muted">
            {p.gender} • DOB {p.dateOfBirth || "—"} • Registered {p.registrationDate}
          </small>
        </div>
        <div className="booking-meta" style={{ gridTemplateColumns: "repeat(3,1fr)", flex: "0 0 auto", minWidth: 380 }}>
          <div>
            <Phone />
            <b>{p.mobileMasked}</b>
            <small>Masked mobile</small>
          </div>
          <div>
            <Clock3 />
            <b>{p.lastCollectionDate || "None yet"}</b>
            <small>Last collection</small>
          </div>
          <div>
            <MapPin />
            <b>{p.nextCollectionDate || "Not scheduled"}</b>
            <small>Next collection</small>
          </div>
        </div>
      </section>

      <div className="stepper" style={{ marginBottom: 20 }}>
        {TABS.map((t) => (
          <button key={t.key} className={tab === t.key ? "current" : ""} onClick={() => setTab(t.key)} style={{ border: 0, background: "none" }}>
            {t.label}
          </button>
        ))}
      </div>

      {tab === "overview" && (
        <div className="item-grid" style={{ gridTemplateColumns: "repeat(3,1fr)" }}>
          <VerificationStatusCard
            title="AADHAAR VERIFICATION"
            status={aadhaarVerification.status}
            rows={[
              { label: "Masked Aadhaar", value: aadhaarVerification.aadhaarMasked },
              { label: "Mode", value: aadhaarVerification.verificationMode?.replace("_", " ") },
            ]}
          />
          <VerificationStatusCard
            title="PASSBOOK VERIFICATION"
            status={passbookVerification.verificationStatus}
            rows={[
              { label: "Passbook No.", value: passbookVerification.passbookNumber },
              { label: "Card Status", value: passbookVerification.status },
            ]}
          />
          <VerificationStatusCard
            title="MOBILE VERIFICATION"
            status={mobileVerification.status}
            rows={[{ label: "Mobile", value: mobileVerification.mobileMasked }]}
          />
        </div>
      )}

      {tab === "family" && (
        <>
          <section className="panel" style={{ marginBottom: 18 }}>
            <div className="panel-title">
              <div>
                <span className="eyebrow blue">RATION CARD</span>
                <h2>{rationCard.rationCardNumber || "Not issued"}</h2>
              </div>
              <span className={`status ${rationCard.status === "ACTIVE" ? "success" : "warning"}`}>{rationCard.status}</span>
            </div>
            <div className="booking-meta">
              <div>
                <ShieldCheck />
                <b>{rationCard.schemeName}</b>
                <small>{rationCard.schemeCode}</small>
              </div>
              <div>
                <User />
                <b>{rationCard.familySize}</b>
                <small>Family size</small>
              </div>
            </div>
          </section>
          <FamilyMembersTable family={family} />
        </>
      )}

      {tab === "entitlement" && <EntitlementTable entitlement={entitlement} />}

      {tab === "verification" && (
        <div className="item-grid" style={{ gridTemplateColumns: "repeat(3,1fr)" }}>
          <VerificationStatusCard
            title="AADHAAR VERIFICATION"
            status={aadhaarVerification.status}
            rows={[
              { label: "Masked Aadhaar", value: aadhaarVerification.aadhaarMasked },
              { label: "Verified On", value: aadhaarVerification.verificationDate || "—" },
              { label: "Source", value: aadhaarVerification.verificationSource },
              { label: "Mode", value: aadhaarVerification.verificationMode?.replace("_", " ") },
            ]}
          />
          <VerificationStatusCard
            title="PASSBOOK VERIFICATION"
            status={passbookVerification.verificationStatus}
            rows={[
              { label: "Passbook No.", value: passbookVerification.passbookNumber },
              { label: "Last Updated", value: passbookVerification.lastUpdated || "—" },
              { label: "Source", value: passbookVerification.verificationSource },
            ]}
          />
          <VerificationStatusCard
            title="MOBILE VERIFICATION"
            status={mobileVerification.status}
            rows={[
              { label: "Mobile", value: mobileVerification.mobileMasked },
              { label: "Verified At", value: mobileVerification.verifiedAt || "—" },
            ]}
          />
        </div>
      )}

      {tab === "qr" && (
        <>
          <section className="panel" style={{ marginBottom: 18 }}>
            <div className="panel-title">
              <div>
                <span className="eyebrow blue">CURRENT QR TOKEN</span>
                <h2>{currentQr?.tokenNumber || "No active booking"}</h2>
              </div>
              {currentQr && <span className="status success">{currentQr.status}</span>}
            </div>
            {currentQr ? (
              <div className="booking-meta">
                <div>
                  <QrCode />
                  <b>{currentQr.qrCodeValue}</b>
                  <small>QR reference</small>
                </div>
                <div>
                  <Clock3 />
                  <b>{currentQr.collectionDate}</b>
                  <small>{currentQr.bookingTime}</small>
                </div>
                <div>
                  <MapPin />
                  <b>{currentQr.shopName}</b>
                  <small>Ration shop</small>
                </div>
              </div>
            ) : (
              <p className="muted">This beneficiary has no upcoming confirmed booking.</p>
            )}
          </section>

          <section className="panel" style={{ marginBottom: 18 }}>
            <div className="panel-title">
              <div>
                <span className="eyebrow blue">COLLECTION HISTORY</span>
                <h2>{collectionHistory.length} record(s)</h2>
              </div>
            </div>
            {collectionHistory.length === 0 && <p className="muted">No ration collected yet.</p>}
            {collectionHistory.map((c) => (
              <div className="complaint" key={c.collectionCode}>
                <CheckCircle2 size={18} color="var(--green)" />
                <div>
                  <b>{c.collectionCode}</b>
                  <small>
                    {c.collectedAt} • {c.shopName} • {c.items.map((i) => `${i.rationType} ${i.quantity}kg`).join(", ")}
                  </small>
                </div>
              </div>
            ))}
          </section>

          <section className="panel">
            <div className="panel-title">
              <div>
                <span className="eyebrow blue">QR SCAN HISTORY</span>
                <h2>{qrScanHistory.length} scan(s)</h2>
              </div>
            </div>
            {qrScanHistory.length === 0 && <p className="muted">No QR scans recorded yet.</p>}
            {qrScanHistory.map((l) => (
              <div className="complaint" key={l.id}>
                <QrCode size={18} color="var(--blue)" />
                <div>
                  <b>{l.verificationReference}</b>
                  <small>
                    {l.timestamp} • {l.status} {l.reason ? `— ${l.reason}` : ""}
                  </small>
                </div>
              </div>
            ))}
          </section>
        </>
      )}

      {tab === "ai" && (
        <>
          <section className="panel" style={{ marginBottom: 18 }}>
            <div className="panel-title">
              <div>
                <span className="eyebrow blue">AI RISK INSIGHT</span>
                <h2>
                  <Sparkles size={16} style={{ verticalAlign: "middle", marginRight: 6 }} />
                  {aiInsight.riskLevel} Risk
                </h2>
              </div>
              <span className={`status ${RISK_TONE[aiInsight.riskLevel] || "warning"}`}>{aiInsight.riskLevel}</span>
            </div>
            <p className="muted">{aiInsight.explanation}</p>
            <ul style={{ marginTop: 10, paddingLeft: 18, fontSize: 12, color: "var(--muted)" }}>
              {aiInsight.reasons.map((r) => (
                <li key={r}>{r}</li>
              ))}
            </ul>
            <div className="info-callout">
              <ShieldAlert size={16} />
              <p>Decision support only — synthetic demo data. A human must review and authorize any action.</p>
            </div>
          </section>

          <section className="panel">
            <div className="panel-title">
              <div>
                <span className="eyebrow blue">AUDIT TRAIL</span>
                <h2>{verificationHistory.length} event(s)</h2>
              </div>
            </div>
            {verificationHistory.length === 0 && <p className="muted">No audit events recorded yet.</p>}
            {verificationHistory.map((l) => (
              <div className="complaint" key={l.id}>
                {l.status === "BLOCKED" ? <XCircle size={18} color="var(--red)" /> : <CheckCircle2 size={18} color="var(--green)" />}
                <div>
                  <b>
                    {l.action} • {l.verificationMethod}
                  </b>
                  <small>
                    {l.timestamp} • {l.status} {l.reason ? `— ${l.reason}` : ""}
                  </small>
                </div>
              </div>
            ))}
          </section>
        </>
      )}
    </>
  );
}
