import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { AlertCircle, CheckCircle2, Clock3, Package, Store, Users } from "lucide-react";
import PageHeader from "../../components/PageHeader";
import { ErrorState, LoadingState } from "../../components/EmptyState";
import { getGovernmentDashboard } from "../../services/adminService";

export default function GovernmentDashboard() {
  const navigate = useNavigate();
  const [dashboard, setDashboard] = useState(null);
  const [error, setError] = useState("");

  const load = () => {
    setError("");
    setDashboard(null);
    getGovernmentDashboard()
      .then(setDashboard)
      .catch((err) => setError(err.message));
  };

  useEffect(load, []);

  if (error) return <ErrorState text={error} onRetry={load} />;
  if (!dashboard) return <LoadingState text="Loading dashboard..." />;

  return (
    <>
      <PageHeader title="Good afternoon" subtitle="Monitor ration distribution performance across your jurisdiction." />

      <div className="stats-grid">
        <button className="stat-card blue" onClick={() => navigate("/gov/users")}>
          <div className="stat-top">
            <span>Beneficiaries Served</span>
            <Users size={19} />
          </div>
          <strong>{dashboard.totalBeneficiaries}</strong>
          <small>Registered rural users</small>
        </button>
        <button className="stat-card cyan" onClick={() => navigate("/gov/shops")}>
          <div className="stat-top">
            <span>Active Shops</span>
            <Store size={19} />
          </div>
          <strong>{dashboard.totalShops}</strong>
          <small>Ration shops</small>
        </button>
        <button className="stat-card green" onClick={() => navigate("/gov/bookings")}>
          <div className="stat-top">
            <span>Today's Collections</span>
            <CheckCircle2 size={19} />
          </div>
          <strong>{dashboard.todayCollections}</strong>
          <small>of {dashboard.todayBookings} bookings</small>
        </button>
        <button className="stat-card orange" onClick={() => navigate("/gov/bookings")}>
          <div className="stat-top">
            <span>Pending Collections</span>
            <Clock3 size={19} />
          </div>
          <strong>{dashboard.pendingCollections}</strong>
          <small>Awaiting pickup today</small>
        </button>
      </div>

      <div className="grid-2">
        <section className="panel">
          <div className="panel-title">
            <div>
              <span className="eyebrow blue">TODAY</span>
              <h2>Ration Distributed</h2>
            </div>
          </div>
          <div className="token-big">{dashboard.rationDistributedTodayKg} kg</div>
          <p className="muted">Total quantity collected across all shops today.</p>
        </section>
        <section className="panel">
          <div className="panel-title">
            <div>
              <span className="eyebrow blue">ALERTS</span>
              <h2>Inventory Status</h2>
            </div>
          </div>
          {dashboard.lowStockAlerts > 0 ? (
            <div className="shop-row">
              <div className="shop-avatar">
                <AlertCircle size={18} color="var(--orange)" />
              </div>
              <div className="grow">
                <b>{dashboard.lowStockAlerts} commodity record(s) low on stock</b>
                <small>Across all shops</small>
              </div>
              <button className="link-btn" onClick={() => navigate("/gov/inventory")}>
                View
              </button>
            </div>
          ) : (
            <div className="shop-row">
              <div className="shop-avatar">
                <Package size={18} color="var(--green)" />
              </div>
              <div className="grow">
                <b>All shops adequately stocked</b>
                <small>No low-stock alerts</small>
              </div>
            </div>
          )}
        </section>
      </div>
    </>
  );
}
