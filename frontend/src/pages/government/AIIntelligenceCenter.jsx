import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { AlertTriangle, Package, Sparkles, TrendingUp, Users } from "lucide-react";
import PageHeader from "../../components/PageHeader";
import { EmptyState, ErrorState, LoadingState } from "../../components/EmptyState";
import { getIntelligenceCenter } from "../../services/aiService";
import PythonAnalyticsPanel from "../../components/ai/PythonAnalyticsPanel";

const RISK_TONE = { NORMAL: "success", LOW: "warning", CRITICAL: "danger" };
const SEVERITY_TONE = { Low: "warning", Medium: "warning", High: "danger" };

export default function AIIntelligenceCenter() {
  const navigate = useNavigate();
  const [data, setData] = useState(null);
  const [error, setError] = useState("");

  const load = () => {
    setError("");
    setData(null);
    getIntelligenceCenter()
      .then(setData)
      .catch((err) => setError(err.message));
  };

  useEffect(load, []);

  return (
    <>
      <PageHeader title="AI Intelligence Center" subtitle="Rule-based demand, inventory-risk, queue and anomaly analysis computed live from real distribution data." />

      <div className="info-callout" style={{ marginBottom: 18 }}>
        <Sparkles size={16} />
        <p>
          Decision support only — computed from synthetic demo data. No alert here autonomously denies benefits, cancels
          entitlement, or declares fraud. A human must review and authorize any action.
        </p>
      </div>

      {error && <ErrorState text={error} onRetry={load} />}
      {!error && data === null && <LoadingState text="Running AI analysis..." />}

      {data && (
        <>
          <div className="stats-grid">
            <div className="stat-card orange">
              <div className="stat-top">
                <span>Shops Requiring Attention</span>
                <Package size={19} />
              </div>
              <strong>{data.shopsRequiringAttention}</strong>
              <small>Low or critical inventory</small>
            </div>
            <div className="stat-card blue">
              <div className="stat-top">
                <span>Average Queue Wait</span>
                <Users size={19} />
              </div>
              <strong>{data.averageQueueWaitMinutes.toFixed(1)} min</strong>
              <small>Across all shops</small>
            </div>
            <div className="stat-card cyan">
              <div className="stat-top">
                <span>Anomalies Requiring Review</span>
                <AlertTriangle size={19} />
              </div>
              <strong>{data.anomaliesRequiringReview}</strong>
              <small>Open alerts</small>
            </div>
            <div className="stat-card green">
              <div className="stat-top">
                <span>Data Source</span>
                <Sparkles size={19} />
              </div>
              <strong style={{ fontSize: 15 }}>{data.isSyntheticData ? "Synthetic Demo" : "Live"}</strong>
              <small>Decision support only</small>
            </div>
          </div>

          <section className="panel" style={{ marginBottom: 18 }}>
            <div className="panel-title">
              <div>
                <span className="eyebrow blue">DEMAND FORECAST</span>
                <h2>Trailing 30-day trend by commodity</h2>
              </div>
            </div>
            {data.demandForecast.length === 0 ? (
              <EmptyState title="No demand data yet" text="Not enough collection history to forecast demand." />
            ) : (
              <div className="table-wrap">
                <table>
                  <thead>
                    <tr>
                      <th>Commodity</th>
                      <th>Last 30 Days</th>
                      <th>Previous 30 Days</th>
                      <th>Growth</th>
                      <th>Predicted Next 30 Days</th>
                    </tr>
                  </thead>
                  <tbody>
                    {data.demandForecast.map((f) => (
                      <tr key={f.rationType}>
                        <td>{f.rationType}</td>
                        <td>{f.last30DaysKg} kg</td>
                        <td>{f.previous30DaysKg} kg</td>
                        <td style={{ color: f.growthPercent >= 0 ? "var(--green)" : "var(--red)" }}>
                          <TrendingUp size={13} style={{ verticalAlign: "middle", marginRight: 4 }} />
                          {f.growthPercent.toFixed(1)}%
                        </td>
                        <td>
                          <b>{f.predictedNext30DaysKg} kg</b>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </section>

          <section className="panel" style={{ marginBottom: 18 }}>
            <div className="panel-title">
              <div>
                <span className="eyebrow blue">INVENTORY RISK</span>
                <h2>Per shop, per commodity</h2>
              </div>
            </div>
            {data.inventoryRisks.length === 0 ? (
              <EmptyState title="No inventory data" text="No shops have inventory records yet." />
            ) : (
              <div className="table-wrap">
                <table>
                  <thead>
                    <tr>
                      <th>Shop</th>
                      <th>Item</th>
                      <th>Status</th>
                      <th>Available</th>
                      <th>Avg Daily Use</th>
                      <th>Reorder ETA</th>
                      <th>Explanation</th>
                    </tr>
                  </thead>
                  <tbody>
                    {data.inventoryRisks.map((r, idx) => (
                      <tr key={`${r.shopId}-${r.rationType}-${idx}`}>
                        <td>{r.shopName}</td>
                        <td>{r.rationType}</td>
                        <td>
                          <span className={`status ${RISK_TONE[r.currentStatus] || "warning"}`}>{r.currentStatus}</span>
                        </td>
                        <td>{r.availableQuantity} kg</td>
                        <td>{r.averageDailyConsumption.toFixed ? r.averageDailyConsumption.toFixed(1) : r.averageDailyConsumption} kg</td>
                        <td>{formatReorderEta(r.predictedDaysUntilReorder)}</td>
                        <td className="muted" style={{ fontSize: 10 }}>{r.explanation}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </section>

          <section className="panel" style={{ marginBottom: 18 }}>
            <div className="panel-title">
              <div>
                <span className="eyebrow blue">QUEUE PREDICTION</span>
                <h2>Estimated wait by shop</h2>
              </div>
            </div>
            {data.queuePredictions.length === 0 ? (
              <EmptyState title="No queue data" text="No shops have a pending queue right now." />
            ) : (
              data.queuePredictions.map((q) => (
                <div className="shop-row" key={q.shopId}>
                  <div className="shop-avatar">
                    <Users size={18} />
                  </div>
                  <div className="grow">
                    <b>{q.shopName}</b>
                    <small>{q.explanation}</small>
                  </div>
                  <strong>{q.predictedWaitMinutes} min</strong>
                </div>
              ))
            )}
          </section>

          <section className="panel">
            <div className="panel-title">
              <div>
                <span className="eyebrow blue">RECENT ANOMALIES</span>
                <h2>{data.recentAnomalies.length} alert(s)</h2>
              </div>
            </div>
            {data.recentAnomalies.length === 0 ? (
              <EmptyState title="No anomalies detected" text="No unusual patterns found in the last scan." />
            ) : (
              data.recentAnomalies.map((a) => (
                <div
                  className="complaint"
                  key={a.id}
                  style={{ cursor: a.beneficiaryId ? "pointer" : "default" }}
                  onClick={() => a.beneficiaryId && navigate(`/beneficiary/${a.beneficiaryId}`)}
                >
                  <AlertTriangle size={18} color={a.severity === "High" ? "var(--red)" : "var(--orange)"} />
                  <div>
                    <b>{a.alertType}</b>
                    <small>
                      {a.description} • {a.createdAt}
                    </small>
                  </div>
                  <span className={`status ${SEVERITY_TONE[a.severity] || "warning"}`}>{a.severity}</span>
                </div>
              ))
            )}
          </section>
        </>
      )}

      <PythonAnalyticsPanel />
    </>
  );
}

function formatReorderEta(days) {
  if (days === null || days === undefined) return "—";
  if (days < 0) {
    return <span style={{ color: "var(--red)" }}>Reorder overdue ({Math.abs(days).toFixed(0)}d)</span>;
  }
  return `${days.toFixed(0)} day(s)`;
}
