import { useEffect, useState } from "react";
import PageHeader from "../../components/PageHeader";
import { EmptyState, ErrorState, LoadingState } from "../../components/EmptyState";
import { getDatabaseTableRows, getDatabaseTables } from "../../services/adminDatabaseService";

const PAGE_SIZE = 20;

const TABLE_LABELS = {
  beneficiaries: "Beneficiaries",
  familyMembers: "Family Members",
  tokens: "Tokens",
  collections: "Ration Collections",
  inventory: "Inventory",
  aiInsights: "AI Insights",
  auditLogs: "Audit Logs",
};

// Columns to render per table — keeps the viewer generic across very
// different row shapes without a giant per-table component tree.
const TABLE_COLUMNS = {
  beneficiaries: [
    ["beneficiaryCode", "Code"], ["fullName", "Name"], ["gender", "Gender"], ["village", "Village"],
    ["district", "District"], ["schemeCode", "Scheme"], ["shopName", "Shop"], ["familySize", "Family"],
    ["aadhaarStatus", "Aadhaar"], ["passbookStatus", "Passbook"], ["isActive", "Active"], ["isBlocked", "Blocked"],
  ],
  familyMembers: [
    ["familyCode", "Family"], ["fullName", "Name"], ["age", "Age"], ["relationship", "Relationship"], ["eligibility", "Eligibility"],
  ],
  tokens: [
    ["tokenNumber", "Token"], ["beneficiaryCode", "Beneficiary"], ["shopName", "Shop"], ["slotDate", "Slot Date"], ["status", "Status"], ["qrCodeValue", "QR Value"],
  ],
  collections: [
    ["collectionCode", "Collection"], ["beneficiaryCode", "Beneficiary"], ["shopName", "Shop"], ["collectedAt", "Collected At"], ["totalQuantityKg", "Total (kg)"],
  ],
  inventory: [
    ["shopName", "Shop"], ["rationType", "Item"], ["available", "Available"], ["allocated", "Allocated"], ["minimumStockLevel", "Min Stock"],
  ],
  aiInsights: [
    ["entityType", "Entity"], ["entityId", "Entity ID"], ["insightType", "Type"], ["riskLevel", "Risk"], ["score", "Score"], ["explanation", "Explanation"], ["createdAt", "Created At"],
  ],
  auditLogs: [
    ["verificationReference", "Reference"], ["action", "Action"], ["verificationMethod", "Method"], ["tokenNumber", "Token"], ["status", "Status"], ["reason", "Reason"], ["timestamp", "Timestamp"],
  ],
};

export default function AdminDatabase() {
  const [tables, setTables] = useState([]);
  const [activeTable, setActiveTable] = useState(null);
  const [search, setSearch] = useState("");
  const [page, setPage] = useState(1);
  const [result, setResult] = useState(null);
  const [error, setError] = useState("");

  useEffect(() => {
    getDatabaseTables()
      .then((names) => {
        setTables(names);
        setActiveTable(names[0]);
      })
      .catch((err) => setError(err.message));
  }, []);

  useEffect(() => {
    if (!activeTable) return;
    setError("");
    setResult(null);
    getDatabaseTableRows(activeTable, { search: search || undefined, page, pageSize: PAGE_SIZE })
      .then(setResult)
      .catch((err) => setError(err.message));
  }, [activeTable, search, page]);

  const totalPages = result ? Math.max(1, Math.ceil(result.totalCount / PAGE_SIZE)) : 1;
  const columns = TABLE_COLUMNS[activeTable] || [];

  return (
    <>
      <PageHeader title="Database Viewer" subtitle="Read-only inspection of the underlying tables. Government / Admin access only." />

      <div className="demo-box" style={{ marginBottom: 18 }}>
        <b>READ-ONLY</b> — this viewer never writes to the database. All data shown is the synthetic demo dataset.
      </div>

      <div className="role-tabs" style={{ flexWrap: "wrap" }}>
        {tables.map((tbl) => (
          <button
            key={tbl}
            className={activeTable === tbl ? "selected" : ""}
            onClick={() => {
              setActiveTable(tbl);
              setPage(1);
              setSearch("");
            }}
          >
            {TABLE_LABELS[tbl] || tbl}
          </button>
        ))}
      </div>

      <section className="panel" style={{ marginTop: 18 }}>
        {["beneficiaries", "familyMembers", "tokens", "collections"].includes(activeTable) && (
          <label style={{ display: "block", marginBottom: 16 }}>
            Search
            <input
              placeholder="Search this table..."
              value={search}
              onChange={(e) => {
                setPage(1);
                setSearch(e.target.value);
              }}
            />
          </label>
        )}

        {error && <ErrorState text={error} onRetry={() => setActiveTable(activeTable)} />}
        {!error && result === null && <LoadingState text="Loading table..." />}
        {!error && result?.items.length === 0 && <EmptyState title="No rows found" text="This table has no matching rows." />}
        {result?.items.length > 0 && (
          <>
            <div className="table-wrap">
              <table>
                <thead>
                  <tr>
                    {columns.map(([key, label]) => (
                      <th key={key}>{label}</th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {result.items.map((row, idx) => (
                    <tr key={row.id ?? idx}>
                      {columns.map(([key]) => (
                        <td key={key}>{formatCell(row[key])}</td>
                      ))}
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

function formatCell(value) {
  if (value === null || value === undefined) return "—";
  if (typeof value === "boolean") return value ? "Yes" : "No";
  return String(value);
}
