import { useEffect, useState } from "react";
import { Search } from "lucide-react";
import PageHeader from "../../components/PageHeader";
import StatusBadge from "../../components/StatusBadge";
import { EmptyState, ErrorState, LoadingState } from "../../components/EmptyState";
import { getBookings } from "../../services/rationService";

const STATUS_FILTERS = ["All", "Pending", "Confirmed", "Completed", "Cancelled"];

export default function Bookings() {
  const [bookings, setBookings] = useState(null);
  const [error, setError] = useState("");
  const [search, setSearch] = useState("");
  const [status, setStatus] = useState("All");

  const load = () => {
    setError("");
    setBookings(null);
    getBookings()
      .then((data) => data.sort((a, b) => new Date(b.createdAt) - new Date(a.createdAt)))
      .then(setBookings)
      .catch((err) => setError(err.message));
  };

  useEffect(load, []);

  const filtered = (bookings || []).filter((b) => {
    const matchesStatus = status === "All" || b.status === status;
    const q = search.toLowerCase();
    const matchesSearch = !q || b.tokenNumber.toLowerCase().includes(q) || b.userName.toLowerCase().includes(q) || b.rationShopName.toLowerCase().includes(q);
    return matchesStatus && matchesSearch;
  });

  return (
    <>
      <PageHeader title="All Bookings" subtitle="Ration bookings across every shop in your jurisdiction." />
      <section className="panel">
        <div className="table-toolbar">
          <div>
            <b>{filtered.length} booking(s)</b>
          </div>
          <div style={{ display: "flex", gap: 10 }}>
            <select className="small-select" value={status} onChange={(e) => setStatus(e.target.value)}>
              {STATUS_FILTERS.map((s) => (
                <option key={s} value={s}>
                  {s}
                </option>
              ))}
            </select>
            <div className="top-search" style={{ width: 220 }}>
              <Search size={16} />
              <input placeholder="Search token, user, shop..." value={search} onChange={(e) => setSearch(e.target.value)} />
            </div>
          </div>
        </div>

        {error && <ErrorState text={error} onRetry={load} />}
        {!error && bookings === null && <LoadingState text="Loading bookings..." />}
        {!error && bookings?.length === 0 && <EmptyState title="No bookings yet" text="No ration bookings have been made yet." />}

        {filtered.length > 0 && (
          <div className="table-wrap">
            <table>
              <thead>
                <tr>
                  <th>Token</th>
                  <th>User</th>
                  <th>Shop</th>
                  <th>Date &amp; Slot</th>
                  <th>Status</th>
                </tr>
              </thead>
              <tbody>
                {filtered.map((b) => (
                  <tr key={b.id}>
                    <td>
                      <code>{b.tokenNumber}</code>
                    </td>
                    <td>{b.userName}</td>
                    <td>{b.rationShopName}</td>
                    <td>
                      {b.slotDate.slice(0, 10)} • {b.startTime.slice(0, 5)}
                    </td>
                    <td>
                      <StatusBadge status={b.status} />
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
