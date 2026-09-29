import { AlertTriangle, CheckCircle2, Circle, XCircle } from "lucide-react";

const ICONS = { success: CheckCircle2, warning: AlertTriangle, error: XCircle, info: Circle, muted: Circle };

// Status badge: colour AND icon AND text, so status never depends on colour alone.
export default function EligibilityBadge({ tone = "success", children }) {
  const Icon = ICONS[tone] ?? Circle;
  return (
    <span className={`elig-badge ${tone}`}>
      <Icon size={13} aria-hidden="true" />
      {children}
    </span>
  );
}
