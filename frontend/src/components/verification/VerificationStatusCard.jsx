import { CheckCircle2, Clock3, XCircle, AlertTriangle } from "lucide-react";

const ICONS = {
  Verified: CheckCircle2,
  Valid: CheckCircle2,
  Pending: Clock3,
  NotVerified: AlertTriangle,
  Failed: XCircle,
  Expired: XCircle,
  Cancelled: XCircle,
  Completed: CheckCircle2,
};

const TONE = {
  Verified: "success",
  Valid: "success",
  Pending: "warning",
  NotVerified: "warning",
  Failed: "danger",
  Expired: "danger",
  Cancelled: "danger",
  Completed: "success",
};

export default function VerificationStatusCard({ title, status, statusLabel, rows }) {
  const Icon = ICONS[status] || Clock3;
  const tone = TONE[status] || "warning";

  return (
    <div className="panel" style={{ padding: 18 }}>
      <div className="panel-title" style={{ marginBottom: 10 }}>
        <div>
          <span className="eyebrow blue">{title}</span>
        </div>
        <span className={`status ${tone}`}>
          <Icon size={13} style={{ marginRight: 4 }} />
          {statusLabel || status}
        </span>
      </div>
      <div className="detail-list">
        {rows.map((row) => (
          <div key={row.label} style={{ padding: "8px 0" }}>
            <span style={{ fontSize: 10, color: "var(--muted)" }}>{row.label}</span>
            <b style={{ display: "block", fontSize: 12, marginTop: 2 }}>{row.value}</b>
          </div>
        ))}
      </div>
    </div>
  );
}
