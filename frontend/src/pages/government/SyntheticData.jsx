import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import PageHeader from "../../components/PageHeader";
import { EmptyState, ErrorState, LoadingState } from "../../components/EmptyState";
import { getSyntheticBeneficiaries } from "../../services/syntheticDataService";

const AADHAAR_FILTERS = ["", "NotVerified", "Pending", "Verified", "Failed", "Expired"];
const PASSBOOK_FILTERS = ["", "NotVerified", "Pending", "Verified", "Failed"];
const PAGE_SIZE = 20;

export default function SyntheticData() {
  const navigate = useNavigate();
  const [search, setSearch] = useState("");
  const [aadhaarStatus, setAadhaarStatus] = useState("");
  const [passbookStatus, setPassbookStatus] = useState("");
  const [page, setPage] = useState(1);
  const [result, setResult] = useState(null);
  const [error, setError] = useState("");

  const load = () => {
    setError("");
    getSyntheticBeneficiaries({
      search: search || undefined,
      aadhaarStatus: aadhaarStatus || undefined,
      passbookStatus: passbookStatus || undefined,
      page,
      pageSize: PAGE_SIZE,
    })
      .then(setResult)
      .catch((err) => setError(err.message));
  };

  useEffect(() => {
    const timer = setTimeout(load, 300);
    return () => clearTimeout(timer);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [search, aadhaarStatus, passbookStatus, page]);

  const totalPages = result ? Math.max(1, Math.ceil(result.totalCount / PAGE_SIZE)) : 1;

  return (
    <>
      <PageHeader title="Synthetic Data Management" subtitle="Search and inspect the seeded synthetic beneficiary dataset. Never exposed to rural users or shop owners." />

      <div className="demo-box" style={{ marginBottom: 18 }}>
        <b>SYNTHETIC / DEMO DATA</b> — every row here is a generated demo record, not a real government beneficiary.
      </div>

      <section className="panel" style={{ marginBottom: 18 }}>
        <div className="form-grid" style={{ gridTemplateColumns: "2fr 1fr 1fr" }}>
          <label>
            Search
            <input
              placeholder="Name or beneficiary code..."
              value={search}
              onChange={(e) => {
                setPage(1);
                setSearch(e.target.value);
              }}
            />
          </label>
          <label>
            Aadhaar status
            <select
              value={aadhaarStatus}
              onChange={(e) => {
                setPage(1);
                setAadhaarStatus(e.target.value);
              }}
            >
              {AADHAAR_FILTERS.map((f) => (
                <option key={f} value={f}>
                  {f || "All"}
                </option>
              ))}
            </select>
          </label>
          <label>
            Passbook status
            <select
              value={passbookStatus}
              onChange={(e) => {
                setPage(1);
                setPassbookStatus(e.target.value);
              }}
            >
              {PASSBOOK_FILTERS.map((f) => (
                <option key={f} value={f}>
                  {f || "All"}
                </option>
              ))}
            </select>
          </label>
        </div>
      </section>

      <section className="panel">
        {error && <ErrorState text={error} onRetry={load} />}
        {!error && result === null && <LoadingState text="Loading synthetic dataset..." />}
        {!error && result?.items.length === 0 && <EmptyState title="No records found" text="No beneficiaries match this filter." />}
        {result?.items.length > 0 && (
          <>
            <div className="table-wrap">
              <table>
                <thead>
                  <tr>
                    <th>Beneficiary</th>
                    <th>Village / District</th>
                    <th>Scheme</th>
                    <th>Shop</th>
                    <th>Family</th>
                    <th>Aadhaar</th>
                    <th>Passbook</th>
                    <th>Status</th>
                  </tr>
                </thead>
                <tbody>
                  {result.items.map((b) => (
                    <tr key={b.id} style={{ cursor: "pointer" }} onClick={() => navigate(`/beneficiary/${b.id}`)}>
                      <td>
                        <div className="user-cell">
                          <div className="mini-avatar">{b.fullName[0]}</div>
                          <div>
                            <b>{b.fullName}</b>
                            <div className="muted" style={{ fontSize: 10 }}>{b.beneficiaryCode}</div>
                          </div>
                        </div>
                      </td>
                      <td>{b.village}, {b.district}</td>
                      <td>{b.schemeCode}</td>
                      <td>{b.shopName}</td>
                      <td>{b.familySize}</td>
                      <td>
                        <span className={`status ${b.aadhaarStatus === "Verified" ? "success" : b.aadhaarStatus === "Failed" ? "danger" : "warning"}`}>{b.aadhaarStatus}</span>
                      </td>
                      <td>
                        <span className={`status ${b.passbookStatus === "Verified" ? "success" : b.passbookStatus === "Failed" ? "danger" : "warning"}`}>{b.passbookStatus}</span>
                      </td>
                      <td>
                        <span className={`status ${b.isBlocked ? "danger" : b.isActive ? "success" : "warning"}`}>{b.isBlocked ? "Blocked" : b.isActive ? "Active" : "Inactive"}</span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            <div className="table-toolbar" style={{ marginTop: 14 }}>
              <span className="muted">
                Page {result.page} of {totalPages} • {result.totalCount} total
              </span>
              <div className="actions">
                <button className="secondary-btn" disabled={page <= 1} onClick={() => setPage((p) => p - 1)}>
                  Previous
                </button>
                <button className="secondary-btn" disabled={page >= totalPages} onClick={() => setPage((p) => p + 1)}>
                  Next
                </button>
              </div>
            </div>
          </>
        )}
      </section>
    </>
  );
}
