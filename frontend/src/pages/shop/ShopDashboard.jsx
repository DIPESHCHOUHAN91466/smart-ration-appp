import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { CheckCircle2, Clock3, Package, QrCode, Ticket, XCircle } from "lucide-react";
import PageHeader from "../../components/PageHeader";
import { ErrorState, LoadingState } from "../../components/EmptyState";
import { getShopDashboard } from "../../services/shopService";
import { openGlobalQrScanner } from "../../store/qrScannerStore";

export default function ShopDashboard() {
  const navigate = useNavigate();
  const [dashboard, setDashboard] = useState(null);
  const [error, setError] = useState("");

  const load = () => {
    setError("");
    setDashboard(null);
    getShopDashboard()
      .then(setDashboard)
      .catch((err) => setError(err.message));
  };

  useEffect(load, []);

  if (error) return <ErrorState text={error} onRetry={load} />;
  if (!dashboard) return <LoadingState text="Loading dashboard..." />;

  const lowStock = dashboard.inventory.filter((i) => i.isLowStock);

  return (
    <>
      <PageHeader title={dashboard.shopName} subtitle="Monitor today's queue and complete ration distribution." />

      <div className="stats-grid">
        <button className="stat-card blue" onClick={() => navigate("/shop/queue")}>
          <div className="stat-top">
            <span>Today's Tokens</span>
            <Ticket size={19} />
          </div>
          <strong>{dashboard.todayTotalTokens}</strong>
          <small>Total bookings today</small>
        </button>
        <button className="stat-card green" onClick={() => navigate("/shop/queue")}>
          <div className="stat-top">
            <span>Completed</span>
            <CheckCircle2 size={19} />
          </div>
          <strong>{dashboard.todayCompleted}</strong>
          <small>Collections done</small>
        </button>
        <button className="stat-card orange" onClick={() => navigate("/shop/queue")}>
          <div className="stat-top">
            <span>Pending</span>
            <Clock3 size={19} />
          </div>
          <strong>{dashboard.todayPending}</strong>
          <small>Awaiting collection</small>
        </button>
        <button className="stat-card cyan" onClick={() => navigate("/shop/inventory")}>
          <div className="stat-top">
            <span>Cancelled Today</span>
            <XCircle size={19} />
          </div>
          <strong>{dashboard.todayCancelled}</strong>
          <small>Bookings cancelled</small>
        </button>
      </div>

      <div className="grid-2">
        <section className="panel">
          <div className="panel-title">
            <div>
              <span className="eyebrow blue">FAST VERIFICATION</span>
              <h2>QR Verification</h2>
            </div>
          </div>
          <div className="scanner-card">
            <div className="scanner-icon">
              <QrCode size={40} />
            </div>
            <h3>Verify a customer token</h3>
            <p>Scan or enter the customer's QR reference to verify their booking.</p>
            <button className="primary-btn" onClick={openGlobalQrScanner} aria-label="Open QR Scanner">
              <QrCode /> Open QR Scanner
            </button>
          </div>
        </section>

        <section className="panel">
          <div className="panel-title">
            <div>
              <span className="eyebrow blue">STOCK HEALTH</span>
              <h2>Inventory</h2>
            </div>
          </div>
          {lowStock.length > 0 ? (
            lowStock.map((item) => (
              <div className="shop-row" key={item.id}>
                <div className="shop-avatar">
                  <Package size={18} />
                </div>
                <div className="grow">
                  <b>{item.rationType}</b>
                  <small>Low stock — {item.availableQuantity} remaining (min {item.minimumStockLevel})</small>
                </div>
                <strong style={{ color: "var(--red)" }}>Low</strong>
              </div>
            ))
          ) : (
            dashboard.inventory.map((item) => (
              <div className="shop-row" key={item.id}>
                <div className="shop-avatar">
                  <Package size={18} />
                </div>
                <div className="grow">
                  <b>{item.rationType}</b>
                  <small>{item.availableQuantity} available</small>
                </div>
                <strong style={{ color: "var(--green)" }}>Healthy</strong>
              </div>
            ))
          )}
        </section>
      </div>
    </>
  );
}
