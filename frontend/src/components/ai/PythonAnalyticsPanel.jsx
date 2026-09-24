import { useCallback, useEffect, useState } from "react";
import { Activity, AlertTriangle, Brain, CheckCircle2, Clock3, RefreshCcw, ShieldAlert, Store, TrendingUp } from "lucide-react";
import {
  getActiveAlerts,
  getAnalyticsForecast,
  getAnalyticsRisk,
  getAnalyticsShops,
  getSystemHealth,
  resolveAlert,
  syncAlerts,
} from "../../services/aiService";
import { useAuthStore } from "../../store/authStore";
import { useToast } from "../../context/ToastContext";
import { useTranslation } from "../../i18n/useTranslation";

const TONE = {
  HIGH: "success", MEDIUM: "warning", LOW: "danger",
  OK: "success", WATCH: "warning", INVESTIGATE: "danger",
  HEALTHY: "success", DEGRADED: "warning", UNHEALTHY: "danger",
  SUFFICIENT: "success", ANOMALOUS: "warning", INSUFFICIENT: "danger",
};
const SEVERITY_TONE = { INFO: "success", LOW: "warning", MEDIUM: "warning", HIGH: "danger", CRITICAL: "danger" };
const RISK_TONE = { LOW: "success", MEDIUM: "warning", HIGH: "danger", CRITICAL: "danger" };

function formatTime(iso, language) {
  if (!iso) return "—";
  const d = new Date(iso.endsWith("Z") ? iso : `${iso}Z`);
  return d.toLocaleString({ hi: "hi-IN", mr: "mr-IN" }[language] ?? "en-IN", { dateStyle: "medium", timeStyle: "short" });
}

// Forecasts, persisted alerts, risk scores and shop monitoring from the Python
// AI service, in the user's language. Every figure carries its basis and
// limitations; when the service is down the panel says so instead of showing
// stale or made-up numbers. Nothing here acts on a finding automatically.
export default function PythonAnalyticsPanel() {
  const { t, language } = useTranslation();
  const notify = useToast();
  const role = useAuthStore((s) => s.user?.role);
  const canResolve = role === "GovernmentOfficial" || role === "Admin";

  const [horizon, setHorizon] = useState(30);
  const [health, setHealth] = useState(null);
  const [forecast, setForecast] = useState(null);
  const [alerts, setAlerts] = useState(null);
  const [risk, setRisk] = useState(null);
  const [shops, setShops] = useState(null);
  const [busyAlert, setBusyAlert] = useState(null);

  const failed = { available: false, error: true };

  const loadAlerts = useCallback(() => {
    setAlerts(null);
    getActiveAlerts()
      .then(setAlerts)
      .catch(() => setAlerts({ error: true }));
  }, []);

  useEffect(() => {
    let cancelled = false;
    const guard = (setter) => (value) => !cancelled && setter(value);
    getSystemHealth().then(guard(setHealth)).catch(() => guard(setHealth)({ system: "UNHEALTHY" }));
    getAnalyticsRisk({ limit: 10, lang: language }).then(guard(setRisk)).catch(() => guard(setRisk)(failed));
    getAnalyticsShops({ lang: language }).then(guard(setShops)).catch(() => guard(setShops)(failed));
    loadAlerts();
    return () => {
      cancelled = true;
    };
  }, [language]); // eslint-disable-line react-hooks/exhaustive-deps

  useEffect(() => {
    let cancelled = false;
    setForecast(null);
    getAnalyticsForecast({ horizonDays: horizon, lang: language })
      .then((r) => !cancelled && setForecast(r))
      .catch(() => !cancelled && setForecast(failed));
    return () => {
      cancelled = true;
    };
  }, [horizon, language]); // eslint-disable-line react-hooks/exhaustive-deps

  const act = async (alert, status) => {
    const note = status === "UnderReview" ? "" : window.prompt(t("ai_resolution_note")) ?? null;
    if (note === null) return;
    setBusyAlert(alert.id);
    try {
      await resolveAlert(alert.id, status, note || undefined);
      notify(t("ai_alert_updated"));
      loadAlerts();
    } catch (err) {
      notify(err.message || t("ai_connection_problem"), "error");
    } finally {
      setBusyAlert(null);
    }
  };

  const refresh = async () => {
    try {
      await syncAlerts();
    } catch {
      // the list below shows the unavailable state
    }
    loadAlerts();
  };

  return (
    <section className="panel" style={{ marginTop: 18 }}>
      <div className="panel-title">
        <div>
          <span className="eyebrow blue">{t("ai_python_eyebrow")}</span>
          <h2>
            <Brain size={17} style={{ verticalAlign: "-3px", marginRight: 6 }} />
            {t("ai_python_title")}
          </h2>
        </div>
        {health && (
          <span className={`status ${TONE[health.system] || "warning"}`} title={`DB: ${health.database} • AI: ${health.ai}`}>
            <Activity size={12} style={{ marginRight: 4 }} />
            {health.system} • AI {health.ai}
          </span>
        )}
      </div>

      {/* ---------------- Alerts ---------------- */}
      <div className="ai-subhead-row">
        <h3 className="ai-subhead">
          <AlertTriangle size={15} /> {t("ai_alerts_title")}
        </h3>
        <span className="muted ai-last-run">
          <Clock3 size={12} /> {t("ai_last_analysis")}: {formatTime(alerts?.sync?.lastAnalysisAt, language)}
          {canResolve && (
            <button type="button" className="link-btn" onClick={refresh}>
              <RefreshCcw size={12} /> {t("ai_refresh")}
            </button>
          )}
        </span>
      </div>
      {!alerts && <p className="muted">{t("loading")}</p>}
      {alerts?.error && <Unavailable />}
      {alerts && !alerts.error && (
        <>
          {alerts.sync && !alerts.sync.available && !alerts.sync.skipped && (
            <p className="muted">
              <b>{t("ai_unavailable")}</b> {t("ai_alerts_stale")}
            </p>
          )}
          {alerts.items.length === 0 ? (
            <p className="muted">
              <CheckCircle2 size={14} style={{ verticalAlign: "-2px", color: "var(--green)" }} /> {t("ai_no_alerts")}
            </p>
          ) : (
            <div className="ai-alert-list">
              {alerts.items.slice(0, 25).map((a) => (
                <article className="ai-alert" key={a.id}>
                  <div className="ai-alert-head">
                    <span className={`status ${SEVERITY_TONE[a.severity] || "warning"}`}>{a.severity}</span>
                    <b>{a.title}</b>
                    {a.score != null && <span className="muted">score {Math.round(a.score)}</span>}
                    <span className="muted ai-alert-meta">
                      {a.shopName || t("ai_system_wide")} • {a.source === "PYTHON_AI" ? "Python AI" : t("ai_rules")} • {a.status}
                    </span>
                  </div>
                  <p>{a.description}</p>
                  {a.recommendedAction && (
                    <p className="ai-alert-action">
                      <b>{t("ai_recommended_action")}:</b> {a.recommendedAction}
                    </p>
                  )}
                  <div className="ai-alert-foot">
                    <small className="muted">
                      {t("ai_detected")} {formatTime(a.detectedAt, language)}
                      {a.lastSeenAt && ` • ${t("ai_last_seen")} ${formatTime(a.lastSeenAt, language)}`}
                    </small>
                    {canResolve && (
                      <span className="ai-alert-buttons">
                        {a.status === "Open" && (
                          <button type="button" className="secondary-btn" disabled={busyAlert === a.id} onClick={() => act(a, "UnderReview")}>
                            {t("ai_mark_review")}
                          </button>
                        )}
                        <button type="button" className="secondary-btn" disabled={busyAlert === a.id} onClick={() => act(a, "Resolved")}>
                          {t("ai_resolve")}
                        </button>
                        <button type="button" className="secondary-btn" disabled={busyAlert === a.id} onClick={() => act(a, "Dismissed")}>
                          {t("ai_dismiss")}
                        </button>
                      </span>
                    )}
                  </div>
                </article>
              ))}
            </div>
          )}
          <p className="muted ai-disclaimer">{t("ai_alert_disclaimer")}</p>
        </>
      )}

      {/* ---------------- Forecast ---------------- */}
      <div className="ai-subhead-row">
        <h3 className="ai-subhead">
          <TrendingUp size={15} /> {t("ai_forecast_title")}
        </h3>
        <span className="option-row" style={{ margin: 0 }}>
          {[7, 30].map((h) => (
            <button key={h} type="button" className={horizon === h ? "selected" : ""} onClick={() => setHorizon(h)}>
              {h} {t("ai_days")}
            </button>
          ))}
        </span>
      </div>
      <Section result={forecast}>
        {(data) => (
          <div className="table-wrap">
            <table>
              <thead>
                <tr>
                  <th>{t("ai_item")}</th>
                  <th>{t("ai_forecast")}</th>
                  <th>{t("ai_range")}</th>
                  <th>{t("ai_confidence")}</th>
                  <th>{t("ai_data")}</th>
                  <th>{t("ai_basis")}</th>
                </tr>
              </thead>
              <tbody>
                {data.items.map((i) => (
                  <tr key={i.ration_type}>
                    <td>{i.ration_type}</td>
                    <td>{i.data_sufficient ? <b>{i.forecast} {i.unit}</b> : "—"}</td>
                    <td>{i.data_sufficient ? `${i.range_low}–${i.range_high} ${i.unit}` : "—"}</td>
                    <td>{i.data_sufficient ? <span className={`status ${TONE[i.confidence]}`}>{i.confidence}</span> : "—"}</td>
                    <td>
                      <span className={`status ${TONE[i.data_quality]}`}>{i.data_sufficient ? i.data_quality : t("ai_insufficient")}</span>
                      <small className="muted" style={{ display: "block", marginTop: 3 }}>
                        {i.data_points}/{i.minimum_required} {t("ai_days")}
                      </small>
                    </td>
                    <td className="muted">
                      {i.explanation.text}
                      {i.limitations?.filter((l) => l.code !== "FORECAST_INSUFFICIENT_DATA").map((l) => (
                        <small key={l.code} style={{ display: "block", marginTop: 3 }}>
                          • {l.text}
                        </small>
                      ))}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </Section>

      {/* ---------------- Risk ---------------- */}
      <h3 className="ai-subhead">
        <ShieldAlert size={15} /> {t("ai_risk_title")}
      </h3>
      <Section result={risk}>
        {(data) => (
          <>
            <p className="muted" style={{ marginTop: 0 }}>
              {data.disclaimer.text} ({t("ai_flagged_of").replace("{flagged}", data.flagged).replace("{evaluated}", data.evaluated)})
            </p>
            {data.items.length === 0 ? (
              <p className="muted">{t("ai_no_risk")}</p>
            ) : (
              data.items.map((b) => (
                <div className="complaint" key={b.beneficiary_id}>
                  <span className={`status ${RISK_TONE[b.risk_level]}`}>{b.risk_score}</span>
                  <div>
                    <b>
                      {b.beneficiary_code} • {b.risk_level}
                    </b>
                    <small>{b.reasons.map((r) => `${r.text} (+${r.points})`).join(" • ")}</small>
                  </div>
                </div>
              ))
            )}
          </>
        )}
      </Section>

      {/* ---------------- Shops ---------------- */}
      <h3 className="ai-subhead">
        <Store size={15} /> {t("ai_shop_monitoring")}
      </h3>
      <Section result={shops}>
        {(data) => (
          <div className="table-wrap">
            <table>
              <thead>
                <tr>
                  <th>{t("ai_shop")}</th>
                  <th>{t("ai_status")}</th>
                  <th>{t("ai_failed_verifications")}</th>
                  <th>{t("ai_no_shows")}</th>
                  <th>{t("ai_findings")}</th>
                </tr>
              </thead>
              <tbody>
                {data.shops.map((s) => (
                  <tr key={s.shop_id}>
                    <td>{s.shop_name}</td>
                    <td>
                      <span className={`status ${TONE[s.status]}`}>{s.status}</span>
                    </td>
                    <td>
                      {s.failed_verifications}/{s.verifications}
                    </td>
                    <td>{s.no_show_tokens}</td>
                    <td className="muted">{s.findings.length ? s.findings.map((f) => f.text).join(" • ") : "—"}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </Section>
    </section>
  );
}

function Unavailable({ fallback }) {
  const { t } = useTranslation();
  return (
    <div className="info-callout" style={{ marginTop: 0 }}>
      <Activity size={16} />
      <p>
        <b>{t("ai_unavailable")}</b> {fallback ? t("ai_fallback_note") : t("ai_core_unaffected")}
      </p>
    </div>
  );
}

function Section({ result, children }) {
  const { t } = useTranslation();
  if (!result) return <p className="muted">{t("loading")}</p>;
  if (result.available && result.data) return children(result.data);
  return <Unavailable fallback={result.source === "fallback"} />;
}
