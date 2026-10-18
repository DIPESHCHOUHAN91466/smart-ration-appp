import { useCallback, useEffect, useState } from "react";
import { Search } from "lucide-react";
import PageHeader from "../../components/PageHeader";
import StatusBadge from "../../components/StatusBadge";
import { EmptyState, ErrorState, LoadingState } from "../../components/EmptyState";
import { getBookings } from "../../services/rationService";

const STATUS_FILTERS = ["All", "Pending", "Confirmed", "Completed", "Cancelled"];
// The newest bookings matching the filters, filtered and searched on the server: an official's full list grows with
// every booking ever made, so it is never downloaded whole.
export const PAGE_LIMIT = 500;

export default function Bookings() {
  const [bookings, setBookings] = useState(null);
  const [error, setError] = useState("");
  const [search, setSearch] = useState("");
  const [status, setStatus] = useState("All");
  const [query, setQuery] = useState("");

  useEffect(() => {
    const timer = setTimeout(() => setQuery(search.trim()), 300);   // search after a pause in typing
    return () => clearTimeout(timer);
  }, [search]);

  const load = useCallback(() => {
    setError("");
    setBookings(null);
    const params = { limit: PAGE_LIMIT };
    if (status !== "All") params.status = status;
    if (query) params.q = query;
    getBookings(params)
      .then(setBookings)
      .catch((err) => setError(err.message));
  }, [status, query]);

  useEffect(load, [load]);

  const filtered = bookings || [];
  const filtering = status !== "All" || query !== "";

  return (
    <>
      <PageHeader title="All Bookings" subtitle="Ration bookings across every shop in your jurisdiction." />
      <section className="panel">
        <div className="table-toolbar">
          <div>
            <b>
              {filtered.length === PAGE_LIMIT ? `Newest ${PAGE_LIMIT}` : filtered.length} booking(s)
            </b>
            {filtered.length === PAGE_LIMIT && (
              <p className="muted" role="note">
                Showing the newest {PAGE_LIMIT}. Search or choose a status to find older bookings.
              </p>
            )}
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
        {!error && bookings?.length === 0 && !filtering && <EmptyState title="No bookings yet" text="No ration bookings have been made yet." />}
        {!error && bookings?.length === 0 && filtering && <EmptyState title="No matching bookings" text="Try another search or status." />}

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
