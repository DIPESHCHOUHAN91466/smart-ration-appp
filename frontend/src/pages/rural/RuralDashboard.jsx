import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import {
  Ticket, QrCode, ClipboardList, Clock3, Package, MapPin, ArrowRight, Bell,
} from "lucide-react";
import PageHeader from "../../components/PageHeader";
import { EmptyState, ErrorState, LoadingState } from "../../components/EmptyState";
import { getBookings } from "../../services/rationService";

const ACTIVE_STATUSES = ["Pending", "Confirmed"];

export default function RuralDashboard() {
  const navigate = useNavigate();
  const [bookings, setBookings] = useState(null);
  const [error, setError] = useState("");

  const load = () => {
    setError("");
    setBookings(null);
    getBookings()
      .then(setBookings)
      .catch((err) => setError(err.message));
  };

  useEffect(load, []);

  if (error) return <ErrorState text={error} onRetry={load} />;
  if (bookings === null) return <LoadingState text="Loading your dashboard..." />;

  const activeBooking = bookings
    .filter((b) => ACTIVE_STATUSES.includes(b.status))
    .sort((a, b) => new Date(a.slotDate + "T" + a.startTime) - new Date(b.slotDate + "T" + b.startTime))[0];

  const completedCount = bookings.filter((b) => b.status === "Completed").length;

  return (
    <>
      <PageHeader title="Welcome back" subtitle="Manage your ration booking, token and collection details." />

      <div className="stats-grid">
        <button className="stat-card blue" onClick={() => navigate(activeBooking ? `/rural/token/${activeBooking.id}` : "/rural/book")}>
          <div className="stat-top">
            <span>Current Token</span>
            <Ticket size={19} />
          </div>
          <strong>{activeBooking ? activeBooking.tokenNumber : "None"}</strong>
          <small>{activeBooking ? activeBooking.status : "Book a slot to get started"}</small>
          <ArrowRight className="stat-arrow" size={17} />
        </button>
        <button className="stat-card cyan" onClick={() => navigate(activeBooking ? `/rural/token/${activeBooking.id}` : "/rural/book")}>
          <div className="stat-top">
            <span>Next Collection</span>
            <Clock3 size={19} />
          </div>
          <strong>{activeBooking ? activeBooking.slotDate.slice(0, 10) : "—"}</strong>
          <small>{activeBooking ? activeBooking.startTime.slice(0, 5) : "No upcoming slot"}</small>
          <ArrowRight className="stat-arrow" size={17} />
        </button>
        <button className="stat-card green" onClick={() => navigate("/rural/history")}>
          <div className="stat-top">
            <span>Collections Completed</span>
            <Package size={19} />
          </div>
          <strong>{completedCount}</strong>
          <small>Lifetime collections</small>
          <ArrowRight className="stat-arrow" size={17} />
        </button>
        <button className="stat-card orange" onClick={() => navigate(activeBooking ? `/rural/token/${activeBooking.id}` : "/rural/book")}>
          <div className="stat-top">
            <span>Shop</span>
            <MapPin size={19} />
          </div>
          <strong>{activeBooking ? activeBooking.rationShopName : "—"}</strong>
          <small>{activeBooking ? "Your collection shop" : "Select a shop when booking"}</small>
          <ArrowRight className="stat-arrow" size={17} />
        </button>
      </div>

      <div className="grid-2">
        <section className="panel hero-panel">
          <div className="panel-title">
            <div>
              <span className="eyebrow blue">YOUR ACTIVE BOOKING</span>
              <h2>Ration Collection Token</h2>
            </div>
            {activeBooking && <span className="status success">● {activeBooking.status}</span>}
          </div>

          {!activeBooking ? (
            <EmptyState title="No active booking" text="Book a ration collection slot to generate your token and QR code." />
          ) : (
            <>
              <div className="token-big">{activeBooking.tokenNumber}</div>
              <div className="booking-meta">
                <div>
                  <Clock3 />
                  <b>{activeBooking.startTime.slice(0, 5)}</b>
                  <small>{activeBooking.slotDate.slice(0, 10)}</small>
                </div>
                <div>
                  <MapPin />
                  <b>{activeBooking.rationShopName}</b>
                  <small>Ration shop</small>
                </div>
                <div>
                  <Package />
                  <b>{activeBooking.items.length} item(s)</b>
                  <small>{activeBooking.items.map((i) => i.rationType).join(" • ")}</small>
                </div>
              </div>
              <div className="actions">
                <button className="primary-btn" onClick={() => navigate(`/rural/token/${activeBooking.id}`)}>
                  <QrCode /> View QR
                </button>
                <button className="secondary-btn" onClick={() => navigate("/rural/history")}>
                  <ClipboardList /> History
                </button>
              </div>
            </>
          )}
        </section>

        <section className="panel">
          <div className="panel-title">
            <div>
              <span className="eyebrow blue">QUICK ACTIONS</span>
              <h2>What would you like to do?</h2>
            </div>
          </div>
          <div className="quick-grid">
            <button onClick={() => navigate("/rural/book")}>
              <Ticket />
              <b>Book Ration</b>
              <small>Select items, shop and slot</small>
            </button>
            <button onClick={() => navigate(activeBooking ? `/rural/token/${activeBooking.id}` : "/rural/book")}>
              <QrCode />
              <b>Show QR Code</b>
              <small>Verify at the shop</small>
            </button>
            <button onClick={() => navigate("/rural/history")}>
              <ClipboardList />
              <b>Booking History</b>
              <small>View previous visits</small>
            </button>
            <button onClick={() => navigate("/rural/notifications")}>
              <Bell />
              <b>Notifications</b>
              <small>Booking &amp; collection updates</small>
            </button>
          </div>
        </section>
      </div>
    </>
  );
}
