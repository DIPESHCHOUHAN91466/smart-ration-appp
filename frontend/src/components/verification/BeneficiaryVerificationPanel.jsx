import { CheckCircle2, Clock3, MapPin, ShieldCheck, User, XCircle } from "lucide-react";
import { Link } from "react-router-dom";
import VerificationStatusCard from "./VerificationStatusCard";
import FamilyMembersTable from "./FamilyMembersTable";
import EntitlementTable from "./EntitlementTable";
import VerificationSummaryBanner from "./VerificationSummaryBanner";

export default function BeneficiaryVerificationPanel({ verification, onConfirm, onCancel, confirming }) {
  const { beneficiary, family, aadhaarVerification, passbookVerification, mobileVerification, booking, entitlement, verificationSummary, previousCollections } = verification;

  const ready = verificationSummary.overallStatus === "READY_FOR_RATION_COLLECTION";
  const todayTotal = entitlement.items.reduce((sum, i) => sum + i.todayAllocation, 0);

  return (
    <>
      <div className="demo-box" style={{ marginBottom: 18 }}>
        <b>SYNTHETIC / DEMO VERIFICATION MODE</b> — Aadhaar, passbook and family data shown here are synthetic demo
        records, not real government verification.
      </div>

      <section className="panel" style={{ marginBottom: 18 }}>
        <div className="panel-title">
          <div>
            <span className="eyebrow blue">QR VERIFICATION</span>
            <h2>Token: {booking.tokenNumber}</h2>
          </div>
          <span className={`status ${booking.status === "Confirmed" ? "success" : "danger"}`}>{booking.status}</span>
        </div>
        <div className="actions" style={{ marginBottom: 14 }}>
          <Link className="secondary-btn" to={`/beneficiary/${beneficiary.id}`}>
            <User size={16} /> View Full 360° Profile
          </Link>
        </div>
        <div className="booking-meta">
          <div>
            <Clock3 />
            <b>{booking.bookingTime}</b>
            <small>{booking.collectionDate}</small>
          </div>
          <div>
            <MapPin />
            <b>{booking.shopName}</b>
            <small>{booking.shopCode}</small>
          </div>
          <div>
            <ShieldCheck />
            <b>{beneficiary.fullName}</b>
            <small>
              {beneficiary.beneficiaryCode} • {beneficiary.mobileMasked}
            </small>
          </div>
        </div>
      </section>

      <div className="item-grid" style={{ gridTemplateColumns: "repeat(4,1fr)", marginBottom: 18 }}>
        <VerificationStatusCard
          title="AADHAAR VERIFICATION"
          status={aadhaarVerification.status}
          rows={[
            { label: "Masked Aadhaar", value: aadhaarVerification.aadhaarMasked },
            { label: "Mode", value: aadhaarVerification.verificationMode.replace("_", " ") },
          ]}
        />
        <VerificationStatusCard
          title="PASSBOOK VERIFICATION"
          status={passbookVerification.verificationStatus}
          rows={[
            { label: "Passbook ID", value: passbookVerification.passbookNumber },
            { label: "Status", value: passbookVerification.status },
          ]}
        />
        <VerificationStatusCard
          title="MOBILE VERIFICATION"
          status={mobileVerification.status}
          rows={[{ label: "Mobile", value: mobileVerification.mobileMasked }]}
        />
        <VerificationStatusCard
          title="TOKEN VERIFICATION"
          status={booking.status === "Confirmed" ? "Valid" : booking.status}
          statusLabel={booking.status === "Confirmed" ? "VALID" : booking.status}
          rows={[{ label: "Token", value: booking.tokenNumber }]}
        />
      </div>

      <div style={{ marginBottom: 18 }}>
        <VerificationSummaryBanner summary={verificationSummary} />
      </div>

      <div style={{ marginBottom: 18 }}>
        <FamilyMembersTable family={family} />
      </div>

      <div style={{ marginBottom: 18 }}>
        <EntitlementTable entitlement={entitlement} />
      </div>

      {previousCollections.length > 0 && (
        <section className="panel" style={{ marginBottom: 18 }}>
          <div className="panel-title">
            <div>
              <span className="eyebrow blue">AUDIT TIMELINE</span>
              <h2>Previous Collections</h2>
            </div>
          </div>
          {previousCollections.map((c) => (
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
      )}

      <section className="panel confirmation">
        <h2>Ration Issuance Summary</h2>
        <div className="summary">
          <div>
            <span>Beneficiary</span>
            <b>{beneficiary.fullName}</b>
          </div>
          <div>
            <span>Family Members</span>
            <b>{family.familySize}</b>
          </div>
          <div>
            <span>Scheme</span>
            <b>{entitlement.schemeCode}</b>
          </div>
          <div>
            <span>Today's Allocation</span>
            <b>{entitlement.items.filter((i) => i.todayAllocation > 0).map((i) => `${i.rationType} ${i.todayAllocation}kg`).join(" • ") || "None"}</b>
          </div>
          <div>
            <span>Total</span>
            <b>{todayTotal} kg</b>
          </div>
        </div>
        <div className="actions">
          <button className="secondary-btn" onClick={onCancel}>
            <XCircle /> Cancel
          </button>
          <button className="primary-btn" onClick={onConfirm} disabled={!ready || confirming}>
            <CheckCircle2 /> {confirming ? "Confirming..." : "Confirm Ration Collection"}
          </button>
        </div>
      </section>
    </>
  );
}
