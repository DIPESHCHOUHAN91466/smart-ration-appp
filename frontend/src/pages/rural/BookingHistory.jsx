import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { ArrowRight, XCircle } from "lucide-react";
import PageHeader from "../../components/PageHeader";
import StatusBadge from "../../components/StatusBadge";
import { EmptyState, ErrorState, LoadingState } from "../../components/EmptyState";
import { getBookings, cancelBooking } from "../../services/rationService";
import { useToast } from "../../state/toast";

export default function BookingHistory() {
  const [bookings, setBookings] = useState(null);
  const [error, setError] = useState("");
  const notify = useToast();

  const load = () => {
    setError("");
    setBookings(null);
    getBookings()
      .then((data) => data.sort((a, b) => new Date(b.createdAt) - new Date(a.createdAt)))
      .then(setBookings)
      .catch((err) => setError(err.message));
  };

  useEffect(load, []);

  const onCancel = async (id) => {
    if (!window.confirm("Cancel this booking?")) return;
    try {
      await cancelBooking(id);
      notify("Booking cancelled");
      load();
    } catch (err) {
      notify(err.message || "Could not cancel booking", "error");
    }
  };

  return (
    <>
      <PageHeader title="Booking History" subtitle="Your previous and upcoming ration token records." />
      <section className="panel">
        {error && <ErrorState text={error} onRetry={load} />}
        {!error && bookings === null && <LoadingState text="Loading history..." />}
        {!error && bookings?.length === 0 && <EmptyState title="No bookings yet" text="Book your first ration collection slot to see it here." />}
        {bookings?.length > 0 && (
          <div className="table-wrap">
            <table>
              <thead>
                <tr>
                  <th>Token</th>
                  <th>Shop</th>
                  <th>Date &amp; Slot</th>
                  <th>Items</th>
                  <th>Status</th>
                  <th></th>
                </tr>
              </thead>
              <tbody>
                {bookings.map((b) => (
                  <tr key={b.id}>
                    <td>
                      <code>{b.tokenNumber}</code>
                    </td>
                    <td>{b.rationShopName}</td>
                    <td>
                      {b.slotDate.slice(0, 10)} • {b.startTime.slice(0, 5)}
                    </td>
                    <td>{b.items.map((i) => i.rationType).join(", ")}</td>
                    <td>
                      <StatusBadge status={b.status} />
                    </td>
                    <td style={{ display: "flex", gap: 6 }}>
                      <Link className="icon-btn" to={`/rural/token/${b.id}`}>
                        <ArrowRight size={16} />
                      </Link>
                      {(b.status === "Pending" || b.status === "Confirmed") && (
                        <button className="icon-btn" onClick={() => onCancel(b.id)} title="Cancel">
                          <XCircle size={16} color="var(--red)" />
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
