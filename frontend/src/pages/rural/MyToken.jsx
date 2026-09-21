import { useEffect, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { Clock3, Download, MapPin, Package, ShieldCheck, Smartphone, XCircle } from "lucide-react";
import PageHeader from "../../components/PageHeader";
import QRCodeCanvas from "../../components/QRCodeCanvas";
import StatusBadge from "../../components/StatusBadge";
import { ErrorState, LoadingState } from "../../components/EmptyState";
import { getToken } from "../../services/tokensService";
import { cancelBooking } from "../../services/rationService";
import { useToast } from "../../context/ToastContext";

export default function MyToken() {
  const { id } = useParams();
  const navigate = useNavigate();
  const notify = useToast();

  const [token, setToken] = useState(null);
  const [error, setError] = useState("");
  const [cancelling, setCancelling] = useState(false);

  const load = () => {
    setError("");
    setToken(null);
    getToken(id)
      .then(setToken)
      .catch((err) => setError(err.message));
  };

  useEffect(load, [id]);

  const onCancel = async () => {
    if (!window.confirm("Cancel this booking? This cannot be undone.")) return;
    setCancelling(true);
    try {
      await cancelBooking(id);
      notify("Booking cancelled");
      navigate("/rural/history", { replace: true });
    } catch (err) {
      notify(err.message || "Could not cancel booking", "error");
    } finally {
      setCancelling(false);
    }
  };

  if (error) return <ErrorState text={error} onRetry={load} />;
  if (!token) return <LoadingState text="Loading your token..." />;

  const canCancel = token.status === "Pending" || token.status === "Confirmed";

  return (
    <>
      <PageHeader
        title="My Token & QR"
        subtitle="Keep this QR code ready when you arrive at your ration shop."
        action={<StatusBadge status={token.status} />}
      />
      <div className="token-layout">
        <section className="panel token-card">
          <span className="eyebrow blue">YOUR TOKEN NUMBER</span>
          <div className="token-number">{token.tokenNumber}</div>
          <div className="qr-preview">
            <QRCodeCanvas value={token.qrCodeValue} />
          </div>
          <b className="qr-ref">{token.qrCodeValue}</b>
          <button className="secondary-btn wide" onClick={() => window.print()}>
            <Download /> Print / Save
          </button>
          {canCancel && (
            <button className="secondary-btn wide" style={{ color: "var(--red)" }} onClick={onCancel} disabled={cancelling}>
              <XCircle /> {cancelling ? "Cancelling..." : "Cancel Booking"}
            </button>
          )}
        </section>
        <section className="panel">
          <span className="eyebrow blue">BOOKING DETAILS</span>
          <h2>Collection appointment</h2>
          <div className="detail-list">
            <div>
              <Clock3 />
              <span>
                Date &amp; Time
                <b>
                  {token.slotDate.slice(0, 10)} • {token.startTime.slice(0, 5)} - {token.endTime.slice(0, 5)}
                </b>
              </span>
            </div>
            <div>
              <MapPin />
              <span>
                Ration Shop
                <b>{token.rationShopName}</b>
              </span>
            </div>
            <div>
              <Package />
              <span>
                Pre-selected items
                <b>{token.items.map((i) => `${i.rationType} (${i.quantity})`).join(" • ")}</b>
              </span>
            </div>
            <div>
              <Smartphone />
              <span>
                Status
                <b>{token.status}{token.collectedAt ? ` • collected ${new Date(token.collectedAt).toLocaleString()}` : ""}</b>
              </span>
            </div>
          </div>
          <div className="info-callout">
            <ShieldCheck />
            <div>
              <b>Secure verification</b>
              <p>Your QR contains a non-sensitive, signed reference only. Identity and booking validation happen on the server.</p>
            </div>
          </div>
        </section>
      </div>
    </>
  );
}
