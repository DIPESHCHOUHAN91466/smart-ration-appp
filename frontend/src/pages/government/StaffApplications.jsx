import { useCallback, useEffect, useState } from "react";
import PageHeader from "../../components/PageHeader";
import { EmptyState, ErrorState, LoadingState } from "../../components/EmptyState";
import {
  approveStaffApplication,
  getStaffApplications,
  rejectStaffApplication,
} from "../../services/staffService";
import { useToast } from "../../state/toast";

const STATUSES = ["Pending", "Approved", "Rejected", "Withdrawn", "All"];

// Admin only (the API answers 403 to everyone else). Approving grants the requested role; every decision needs a
// written reason and is audited. Check the licence / employee ID outside the app before deciding.
export default function StaffApplications() {
  const notify = useToast();
  const [status, setStatus] = useState("Pending");
  const [rows, setRows] = useState(null);
  const [error, setError] = useState("");
  const [reasons, setReasons] = useState({});
  const [busy, setBusy] = useState(null);

  const load = useCallback(() => {
    setError("");
    setRows(null);
    getStaffApplications(status).then(setRows).catch((err) => setError(err.message));
  }, [status]);

  useEffect(load, [load]);

  const decide = async (id, approve) => {
    const reason = (reasons[id] || "").trim();
    if (reason.length < 5) {
      notify("Write a reason of at least 5 characters first.");
      return;
    }
    setBusy(id);
    try {
      await (approve ? approveStaffApplication(id, reason) : rejectStaffApplication(id, reason));
      notify(approve ? "Approved: the role is granted." : "Rejected.");
      load();
    } catch (err) {
      notify(err.message);
    } finally {
      setBusy(null);
    }
  };

  return (
    <>
      <PageHeader title="Staff applications" subtitle="People asking to work as a ration shop owner or a government official." />
      <section className="panel">
        <div className="table-toolbar">
          <b>{rows ? rows.length : 0} application(s)</b>
          <select className="small-select" aria-label="Status" value={status} onChange={(e) => setStatus(e.target.value)}>
            {STATUSES.map((s) => (
              <option key={s} value={s}>
                {s}
              </option>
            ))}
          </select>
        </div>

        {error && <ErrorState text={error} onRetry={load} />}
        {!error && rows === null && <LoadingState text="Loading applications..." />}
        {!error && rows?.length === 0 && <EmptyState title="Nothing to review" text="No applications with this status." />}

        {rows?.length > 0 && (
          <div className="table-wrap">
            <table>
              <thead>
                <tr>
                  <th>Applicant</th>
                  <th>Requested</th>
                  <th>Designation</th>
                  <th>Licence / ID</th>
                  <th>Status</th>
                  <th>Decision</th>
                </tr>
              </thead>
              <tbody>
                {rows.map((a) => (
                  <tr key={a.id}>
                    <td>{a.applicantName}</td>
                    <td>{a.requestedRole === "ShopOwner" ? `Shop owner: ${a.rationShopName ?? ""}` : `Official: ${a.office ?? ""}`}</td>
                    <td>{a.designation}</td>
                    <td>
                      <code>{a.proofReference}</code>
                    </td>
                    <td>{a.status}</td>
                    <td>
                      {a.status === "Pending" ? (
                        <div style={{ display: "flex", gap: 6, flexWrap: "wrap" }}>
                          <input
                            aria-label={`Reason for application ${a.id}`}
                            placeholder="Reason (required)"
                            value={reasons[a.id] || ""}
                            onChange={(e) => setReasons((r) => ({ ...r, [a.id]: e.target.value }))}
                            maxLength={500}
                          />
                          <button type="button" className="primary-btn" disabled={busy === a.id} onClick={() => decide(a.id, true)}>
                            Approve
                          </button>
                          <button type="button" className="secondary-btn" disabled={busy === a.id} onClick={() => decide(a.id, false)}>
                            Reject
                          </button>
                        </div>
                      ) : (
                        a.decisionReason || "—"
                      )}
                    </td>
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
