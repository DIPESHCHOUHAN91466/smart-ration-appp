import { useEffect, useState } from "react";
import { useTranslation } from "../../i18n/useTranslation";
import { Store, TrendingUp } from "lucide-react";
import PageHeader from "../../components/PageHeader";
import { EmptyState, ErrorState, LoadingState } from "../../components/EmptyState";
import { getStatistics } from "../../services/adminService";

function daysAgo(n) {
  const d = new Date();
  d.setDate(d.getDate() - n);
  return d.toISOString().slice(0, 10);
}

export default function Statistics() {
  const { t } = useTranslation();
  const [fromDate, setFromDate] = useState(daysAgo(29));
  const [toDate, setToDate] = useState(daysAgo(0));
  const [stats, setStats] = useState(null);
  const [error, setError] = useState("");

  const load = () => {
    setError("");
    setStats(null);
    getStatistics(fromDate, toDate)
      .then(setStats)
      .catch((err) => setError(err.message));
  };

  useEffect(load, [fromDate, toDate]);

  return (
    <>
      <PageHeader
        title="Government Analytics"
        subtitle="Aggregated distribution intelligence across the jurisdiction."
        action={
          <div style={{ display: "flex", gap: 10 }}>
            <input type="date" aria-label={t("a11y_from_date")} value={fromDate} onChange={(e) => setFromDate(e.target.value)} max={toDate} />
            <input type="date" aria-label={t("a11y_to_date")} value={toDate} onChange={(e) => setToDate(e.target.value)} min={fromDate} max={daysAgo(0)} />
          </div>
        }
      />

      {error && <ErrorState text={error} onRetry={load} />}
      {!error && stats === null && <LoadingState text="Loading statistics..." />}

      {stats && (
        <>
          <div className="stats-grid">
            <div className="stat-card blue">
              <div className="stat-top">
                <span>Tokens Generated</span>
                <TrendingUp size={19} />
              </div>
              <strong>{stats.tokensGenerated}</strong>
              <small>
                {stats.fromDate.slice(0, 10)} to {stats.toDate.slice(0, 10)}
              </small>
            </div>
            <div className="stat-card green">
              <div className="stat-top">
                <span>Collections Completed</span>
                <TrendingUp size={19} />
              </div>
              <strong>{stats.collectionsCompleted}</strong>
              <small>In selected range</small>
            </div>
            <div className="stat-card orange">
              <div className="stat-top">
                <span>Collections Cancelled</span>
                <TrendingUp size={19} />
              </div>
              <strong>{stats.collectionsCancelled}</strong>
              <small>In selected range</small>
            </div>
            <div className="stat-card cyan">
              <div className="stat-top">
                <span>Collection Efficiency</span>
                <TrendingUp size={19} />
              </div>
              <strong>{stats.collectionEfficiencyPercent}%</strong>
              <small>Completed vs generated</small>
            </div>
          </div>

          <section className="panel">
            <div className="panel-title">
              <div>
                <span className="eyebrow blue">SHOP PERFORMANCE</span>
                <h2>Efficiency by Shop</h2>
              </div>
            </div>
            {stats.shopPerformance.length === 0 ? (
              <EmptyState title="No activity" text="No bookings were made at any shop in this date range." />
            ) : (
              stats.shopPerformance.map((s) => (
                <div className="shop-row" key={s.shopId}>
                  <div className="shop-avatar">
                    <Store size={18} />
                  </div>
                  <div className="grow">
                    <b>{s.shopName}</b>
                    <small>
                      {s.completedTokens} of {s.totalTokens} completed
                    </small>
                  </div>
                  <strong>{s.efficiencyPercent}%</strong>
                </div>
              ))
            )}
          </section>
        </>
      )}
    </>
  );
}
