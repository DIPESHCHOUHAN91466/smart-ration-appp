import { AlertTriangle, CheckCircle2 } from "lucide-react";

export default function VerificationSummaryBanner({ summary }) {
  if (!summary) return null;
  const ready = summary.overallStatus === "READY_FOR_RATION_COLLECTION";

  const checks = [
    ["Aadhaar Verified", summary.aadhaarVerified],
    ["Passbook Verified", summary.passbookVerified],
    ["Mobile Verified", summary.mobileVerified],
    ["Token Valid", summary.tokenValid],
    ["Family Eligible", summary.familyEligible],
    ["Entitlement Available", summary.entitlementAvailable],
  ];

  return (
    <div className={`info-callout ${ready ? "" : ""}`} style={{ background: ready ? "#e8f8ee" : "#feecec", color: ready ? "var(--green)" : "var(--red)", flexDirection: "column", alignItems: "flex-start" }}>
      <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
        {ready ? <CheckCircle2 /> : <AlertTriangle />}
        <b style={{ fontSize: 14 }}>{ready ? "READY FOR RATION COLLECTION" : "COLLECTION BLOCKED"}</b>
      </div>
      {!ready && summary.blockedReason && <p style={{ margin: "6px 0 0", color: "#8a2020" }}>Reason: {summary.blockedReason}</p>}
      <div style={{ display: "flex", flexWrap: "wrap", gap: "8px 18px", marginTop: 12 }}>
        {checks.map(([label, ok]) => (
          <span key={label} style={{ fontSize: 11, color: ok ? "var(--green)" : "#8a2020", display: "flex", alignItems: "center", gap: 4 }}>
            {ok ? "✓" : "✗"} {label}
          </span>
        ))}
      </div>
    </div>
  );
}
