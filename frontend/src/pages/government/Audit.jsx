import { useEffect, useState } from "react";
import { useTranslation } from "../../i18n/useTranslation";
import PageHeader from "../../components/PageHeader";
import { EmptyState, ErrorState, LoadingState } from "../../components/EmptyState";
import { getVerificationAudit } from "../../services/auditService";

const STATUS_TONE = { SUCCESS: "success", BLOCKED: "warning", FAILED: "danger" };

export default function Audit() {
  const { t } = useTranslation();
  const [logs, setLogs] = useState(null);
  const [error, setError] = useState("");
  const [statusFilter, setStatusFilter] = useState("");

  const load = () => {
    setError("");
    setLogs(null);
    getVerificationAudit({ status: statusFilter || undefined })
      .then(setLogs)
      .catch((err) => setError(err.message));
  };

  useEffect(load, [statusFilter]);

  return (
    <>
      <PageHeader
        title="Verification Audit Trail"
        subtitle="Every QR scan, OTP request and collection decision across all shops."
        action={
          <select className="small-select" aria-label={t("a11y_filter_status")} value={statusFilter} onChange={(e) => setStatusFilter(e.target.value)}>
            <option value="">All statuses</option>
            <option value="SUCCESS">Success</option>
            <option value="BLOCKED">Blocked</option>
            <option value="FAILED">Failed</option>
          </select>
        }
      />
      <section className="panel">
        {error && <ErrorState text={error} onRetry={load} />}
        {!error && logs === null && <LoadingState text="Loading audit trail..." />}
        {!error && logs?.length === 0 && <EmptyState title="No audit entries" text="No verification activity recorded yet." />}
        {logs?.length > 0 && (
          <div className="table-wrap">
            <table>
              <thead>
                <tr>
                  <th>Time</th>
                  <th>Action</th>
                  <th>Method</th>
                  <th>Token</th>
                  <th>Beneficiary</th>
                  <th>Status</th>
                  <th>Reason</th>
                </tr>
              </thead>
              <tbody>
                {logs.map((l) => (
                  <tr key={l.id}>
                    <td>{l.timestamp}</td>
                    <td>{l.action}</td>
                    <td>{l.verificationMethod}</td>
                    <td>{l.tokenNumber ? <code>{l.tokenNumber}</code> : "—"}</td>
                    <td>{l.beneficiaryId ? `#${l.beneficiaryId}` : "—"}</td>
                    <td>
                      <span className={`status ${STATUS_TONE[l.status] || "warning"}`}>{l.status}</span>
                    </td>
                    <td>{l.reason || "—"}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </section>
    </>
  );
}
