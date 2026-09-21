import { useEffect, useState } from "react";
import { CheckCircle2, Search } from "lucide-react";
import PageHeader from "../../components/PageHeader";
import StatusBadge from "../../components/StatusBadge";
import { EmptyState, ErrorState, LoadingState } from "../../components/EmptyState";
import { getShopQueue, completeCollection } from "../../services/shopService";
import { useToast } from "../../context/ToastContext";

export default function Queue() {
  const [tokens, setTokens] = useState(null);
  const [error, setError] = useState("");
  const [search, setSearch] = useState("");
  const [completingId, setCompletingId] = useState(null);
  const notify = useToast();

  const load = () => {
    setError("");
    setTokens(null);
    getShopQueue()
      .then(setTokens)
      .catch((err) => setError(err.message));
  };

  useEffect(load, []);

  const onComplete = async (token) => {
    setCompletingId(token.id);
    try {
      await completeCollection(token.id);
      notify(`Collection completed for ${token.tokenNumber}`);
      load();
    } catch (err) {
      notify(err.message || "Could not complete collection", "error");
    } finally {
      setCompletingId(null);
    }
  };

  const filtered = (tokens || []).filter((t) => {
    const q = search.toLowerCase();
    return !q || t.tokenNumber.toLowerCase().includes(q) || t.userName.toLowerCase().includes(q);
  });

  return (
    <>
      <PageHeader title="Today's Queue" subtitle="Live customer arrivals and pre-selected ration requirements." />
      <section className="panel">
        <div className="table-toolbar">
          <div>
            <b>{filtered.length} customer(s)</b>
            <span className="muted"> • Today's queue</span>
          </div>
          <div className="top-search" style={{ width: 260 }}>
            <Search size={16} />
            <input placeholder="Search by name or token..." value={search} onChange={(e) => setSearch(e.target.value)} />
          </div>
        </div>

        {error && <ErrorState text={error} onRetry={load} />}
        {!error && tokens === null && <LoadingState text="Loading queue..." />}
        {!error && tokens?.length === 0 && <EmptyState title="No bookings today" text="No customers are booked for today at your shop." />}

        {filtered.length > 0 && (
          <div className="table-wrap">
            <table>
              <thead>
                <tr>
                  <th>User</th>
                  <th>Token</th>
                  <th>Arrival</th>
                  <th>Ration</th>
                  <th>Status</th>
                  <th></th>
                </tr>
              </thead>
              <tbody>
                {filtered.map((t) => (
                  <tr key={t.id}>
                    <td>
                      <div className="user-cell">
                        <div className="mini-avatar">{t.userName[0]}</div>
                        <b>{t.userName}</b>
                      </div>
                    </td>
                    <td>
                      <code>{t.tokenNumber}</code>
                    </td>
                    <td>{t.startTime.slice(0, 5)}</td>
                    <td>{t.items.map((i) => `${i.rationType} ${i.quantity}`).join(", ")}</td>
                    <td>
                      <StatusBadge status={t.status} />
                    </td>
                    <td>
                      {t.status === "Confirmed" && (
                        <button className="secondary-btn" onClick={() => onComplete(t)} disabled={completingId === t.id}>
                          <CheckCircle2 size={14} /> {completingId === t.id ? "..." : "Complete"}
                        </button>
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
