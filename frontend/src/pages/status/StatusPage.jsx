import { useCallback, useEffect, useState } from "react";
import { Activity, CheckCircle2, CircleAlert, CircleSlash, RefreshCw, XCircle } from "lucide-react";
import { API_BASE_URL } from "../../services/apiBase";
import "./status.css";

// Developer status page (/status): live health of every component, read from the Python API's
// /health and /ready and the C# API's /api/health (through the proxy). Only routed in development
// builds or when VITE_SHOW_STATUS=true — see App.jsx. English only: it's a developer tool.
const API_BASE = API_BASE_URL.replace(/\/api(\/v1)?\/?$/, "");

const ICON = { healthy: CheckCircle2, ok: CheckCircle2, synthetic: CircleAlert, disabled: CircleSlash };

async function fetchJson(url) {
  const started = performance.now();
  try {
    const response = await fetch(url, { headers: { Accept: "application/json" } });
    const body = await response.json().catch(() => null);
    return { status: response.status, body, ms: Math.round(performance.now() - started) };
  } catch {
    return { status: 0, body: null, ms: Math.round(performance.now() - started) };
  }
}

function Row({ name, value, detail }) {
  const state = String(value ?? "unreachable");
  const Icon = ICON[state] || (state.startsWith("ok") ? CheckCircle2 : XCircle);
  const tone = ["healthy", "ok"].includes(state) ? "good" : state === "disabled" ? "muted" : state === "synthetic" ? "info" : "bad";
  return (
    <tr>
      <th scope="row">{name}</th>
      <td><span className={`status-pill ${tone}`}><Icon size={15} aria-hidden="true" /> {state}</span></td>
      <td className="status-detail">{detail}</td>
    </tr>
  );
}

export default function StatusPage() {
  const [data, setData] = useState(null);
  const [checkedAt, setCheckedAt] = useState(null);

  const refresh = useCallback(async () => {
    const [health, ready, legacy] = await Promise.all([
      fetchJson(`${API_BASE}/health`),
      fetchJson(`${API_BASE}/ready`),
      fetchJson(`${API_BASE}/api/health`),
    ]);
    setData({ health, ready, legacy });
    setCheckedAt(new Date());
  }, []);

  useEffect(() => {
    refresh();
    const id = setInterval(refresh, 15000);
    return () => clearInterval(id);
  }, [refresh]);

  const h = data?.health.body;
  const r = data?.ready.body;
  return (
    <main className="status-page">
      <header>
        <h1><Activity size={24} aria-hidden="true" /> System status</h1>
        <p>Developer view of every Smart Ration component. Refreshes every 15 seconds.</p>
        <button type="button" className="status-refresh" onClick={refresh}><RefreshCw size={15} aria-hidden="true" /> Refresh</button>
      </header>
      {!data ? <p>Checking…</p> : (
        <table className="status-table">
          <caption className="sr-only">Component health</caption>
          <thead><tr><th scope="col">Component</th><th scope="col">State</th><th scope="col">Detail</th></tr></thead>
          <tbody>
            <Row name="Python API (:8000)" value={data.health.status ? h?.status ?? "unhealthy" : "unreachable"} detail={`${API_BASE}/health · ${data.health.ms} ms`} />
            <Row name="MySQL database" value={h?.database} detail="SELECT 1 from the Python API" />
            <Row name="Schema migrations" value={r?.checks?.migrations} detail="Alembic head vs. database" />
            <Row name="C# API (:5188)" value={h?.legacyApi} detail={`via proxy: /api/health → HTTP ${data.legacy.status || "—"}`} />
            <Row name="AI service (:8001)" value={h?.aiService} detail="analytics / forecasts" />
            <Row name="Chatbot" value={h?.chatbot} detail="knowledge base loaded, provider available" />
            <Row name="Data mode" value={h?.dataMode} detail={h?.dataMode === "synthetic" ? "demo data — not real citizens" : ""} />
            <Row name="Ready for traffic" value={r ? (r.ready ? "ok" : "failing") : undefined} detail="/ready" />
          </tbody>
        </table>
      )}
      {checkedAt && <p className="status-time">Last checked {checkedAt.toLocaleTimeString()}</p>}
    </main>
  );
}
