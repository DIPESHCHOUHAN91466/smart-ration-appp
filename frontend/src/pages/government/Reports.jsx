import { useEffect, useState } from "react";
import { Download, FileText } from "lucide-react";
import PageHeader from "../../components/PageHeader";
import { ErrorState, LoadingState } from "../../components/EmptyState";
import { getReports } from "../../services/adminService";

function daysAgo(n) {
  const d = new Date();
  d.setDate(d.getDate() - n);
  return d.toISOString().slice(0, 10);
}

export default function Reports() {
  const [fromDate, setFromDate] = useState(daysAgo(29));
  const [toDate, setToDate] = useState(daysAgo(0));
  const [reports, setReports] = useState(null);
  const [error, setError] = useState("");

  const load = () => {
    setError("");
    setReports(null);
    getReports(fromDate, toDate)
      .then(setReports)
      .catch((err) => setError(err.message));
  };

  useEffect(load, [fromDate, toDate]);

  return (
    <>
      <PageHeader
        title="Government Reports"
        subtitle="Live record counts for the selected date range."
        action={
          <div style={{ display: "flex", gap: 10 }}>
            <input type="date" value={fromDate} onChange={(e) => setFromDate(e.target.value)} max={toDate} />
            <input type="date" value={toDate} onChange={(e) => setToDate(e.target.value)} min={fromDate} max={daysAgo(0)} />
          </div>
        }
      />

      {error && <ErrorState text={error} onRetry={load} />}
      {!error && reports === null && <LoadingState text="Loading reports..." />}

      {reports && (
        <div className="report-grid">
          {reports.map((r) => (
            <div className="report-card" key={r.reportName}>
              <FileText />
              <div>
                <b>{r.reportName}</b>
                <small>{r.description}</small>
                <small>{r.recordCount} record(s) in range</small>
              </div>
              <span title={r.exportAvailable ? "Download" : "File export not implemented yet"}>
                <Download size={17} style={{ opacity: r.exportAvailable ? 1 : 0.35 }} />
              </span>
            </div>
          ))}
        </div>
      )}
    </>
  );
}
