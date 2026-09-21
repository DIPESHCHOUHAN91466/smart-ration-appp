import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { ArrowLeft, ArrowRight, CheckCircle2, Clock3, Store } from "lucide-react";
import PageHeader from "../../components/PageHeader";
import { ErrorState, LoadingState } from "../../components/EmptyState";
import { getShops } from "../../services/shopsService";
import { getSlots } from "../../services/slotsService";
import { getRationItems, createBooking } from "../../services/rationService";
import { useToast } from "../../context/ToastContext";

function today() {
  return new Date().toISOString().slice(0, 10);
}

export default function BookRation() {
  const navigate = useNavigate();
  const notify = useToast();

  const [step, setStep] = useState(1);

  const [shops, setShops] = useState(null);
  const [shopsError, setShopsError] = useState("");
  const [shopId, setShopId] = useState(null);

  const [date, setDate] = useState(today());
  const [slots, setSlots] = useState(null);
  const [slotsError, setSlotsError] = useState("");
  const [timeSlotId, setTimeSlotId] = useState(null);

  const [catalog, setCatalog] = useState(null);
  const [catalogError, setCatalogError] = useState("");
  const [selections, setSelections] = useState({});

  const [submitting, setSubmitting] = useState(false);
  const [submitError, setSubmitError] = useState("");

  useEffect(() => {
    getShops().then(setShops).catch((err) => setShopsError(err.message));
  }, []);

  useEffect(() => {
    if (!shopId || step !== 2) return;
    setSlots(null);
    setSlotsError("");
    getSlots(shopId, date)
      .then(setSlots)
      .catch((err) => setSlotsError(err.message));
  }, [shopId, date, step]);

  useEffect(() => {
    if (step !== 3) return;
    getRationItems()
      .then((items) => {
        setCatalog(items);
        setSelections(
          Object.fromEntries(items.map((item) => [item.rationType, { checked: true, quantity: item.standardQuotaPerBooking }])),
        );
      })
      .catch((err) => setCatalogError(err.message));
  }, [step]);

  const selectedShop = shops?.find((s) => s.id === shopId);
  const selectedSlot = slots?.find((s) => s.id === timeSlotId);

  const toggleItem = (rationType) =>
    setSelections((prev) => ({ ...prev, [rationType]: { ...prev[rationType], checked: !prev[rationType].checked } }));

  const setQuantity = (rationType, quantity) =>
    setSelections((prev) => ({ ...prev, [rationType]: { ...prev[rationType], quantity } }));

  const submit = async () => {
    setSubmitError("");
    const items = Object.entries(selections)
      .filter(([, v]) => v.checked && Number(v.quantity) > 0)
      .map(([rationType, v]) => ({ rationType, quantity: Number(v.quantity) }));

    if (items.length === 0) {
      setSubmitError("Select at least one ration item.");
      return;
    }

    setSubmitting(true);
    try {
      const token = await createBooking({ rationShopId: shopId, timeSlotId, items });
      notify("Token and QR generated successfully");
      navigate(`/rural/token/${token.id}`, { replace: true });
    } catch (err) {
      setSubmitError(err.errors?.join(" ") || err.message || "Could not create booking.");
      notify(err.message || "Booking failed", "error");
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <>
      <PageHeader title="Book Ration" subtitle="Select a shop, a 5-minute collection slot, and your ration items." />
      <div className="stepper">
        {["Select Shop & Slot", "Select Slot", "Select Items", "Confirm"].map((label, i) => (
          <div key={label} className={step === i + 1 ? "current" : step > i + 1 ? "done" : ""}>
            <span>{step > i + 1 ? "✓" : i + 1}</span>
            {label}
          </div>
        ))}
      </div>

      {step === 1 && (
        <section className="panel form-panel">
          <h2>Choose your ration shop</h2>
          {shopsError && <ErrorState text={shopsError} />}
          {!shopsError && shops === null && <LoadingState text="Loading shops..." />}
          {shops && (
            <div className="item-grid">
              {shops.map((shop) => (
                <button
                  key={shop.id}
                  className={`item-card ${shopId === shop.id ? "chosen" : ""}`}
                  onClick={() => setShopId(shop.id)}
                >
                  <Store className="item-icon" size={26} />
                  <div>
                    <b>{shop.shopName}</b>
                    <span>
                      {shop.address}, {shop.district}
                    </span>
                  </div>
                  {shopId === shop.id && <CheckCircle2 className="check" />}
                </button>
              ))}
            </div>
          )}
          <button className="primary-btn wide" disabled={!shopId} onClick={() => setStep(2)}>
            Continue to Time Slot <ArrowRight />
          </button>
        </section>
      )}

      {step === 2 && (
        <section className="panel form-panel">
          <h2>Choose collection slot</h2>
          <div className="form-grid">
            <label>
              Ration Shop
              <input value={selectedShop?.shopName || ""} disabled />
            </label>
            <label>
              Date
              <input type="date" min={today()} value={date} onChange={(e) => setDate(e.target.value)} />
            </label>
          </div>

          {slotsError && <ErrorState text={slotsError} />}
          {!slotsError && slots === null && <LoadingState text="Loading slots..." />}
          {slots && slots.length === 0 && <ErrorState title="No slots" text="No slots configured for this date." />}

          {slots && slots.length > 0 && (
            <div className="slot-grid">
              {slots.map((slot) => (
                <button
                  key={slot.id}
                  className={timeSlotId === slot.id ? "slot selected" : "slot"}
                  disabled={slot.status === "Full"}
                  onClick={() => setTimeSlotId(slot.id)}
                  style={slot.status === "Full" ? { opacity: 0.45, cursor: "not-allowed" } : undefined}
                >
                  <Clock3 size={15} />
                  {slot.startTime.slice(0, 5)}
                  <small style={{ color: slot.status === "Full" ? "var(--red)" : slot.status === "Limited" ? "var(--orange)" : "var(--green)" }}>
                    {slot.status} ({slot.capacity - slot.bookedCount} left)
                  </small>
                </button>
              ))}
            </div>
          )}

          <div className="actions">
            <button className="secondary-btn" onClick={() => setStep(1)}>
              <ArrowLeft /> Back
            </button>
            <button className="primary-btn" disabled={!timeSlotId} onClick={() => setStep(3)}>
              Continue to Items <ArrowRight />
            </button>
          </div>
        </section>
      )}

      {step === 3 && (
        <section className="panel form-panel">
          <h2>Select ration items</h2>
          <p className="muted">Choose the items you want to collect and the quantity, up to your standard quota.</p>

          {catalogError && <ErrorState text={catalogError} />}
          {!catalogError && catalog === null && <LoadingState text="Loading ration items..." />}

          {catalog && (
            <div className="item-grid">
              {catalog.map((item) => {
                const selection = selections[item.rationType] || { checked: false, quantity: 0 };
                return (
                  <div key={item.rationType} className={`item-card ${selection.checked ? "chosen" : ""}`} style={{ cursor: "default" }}>
                    <span className="item-icon">🌾</span>
                    <div style={{ flex: 1 }}>
                      <label style={{ display: "flex", alignItems: "center", gap: 8, cursor: "pointer" }}>
                        <input type="checkbox" checked={selection.checked} onChange={() => toggleItem(item.rationType)} style={{ width: "auto" }} />
                        <b>
                          {item.name} <small>({item.vernacularName})</small>
                        </b>
                      </label>
                      <span>Quota: {item.standardQuotaPerBooking} {item.unit}</span>
                      {selection.checked && (
                        <input
                          type="number"
                          min={0.1}
                          max={item.standardQuotaPerBooking}
                          step={0.1}
                          value={selection.quantity}
                          onChange={(e) => setQuantity(item.rationType, e.target.value)}
                          style={{ marginTop: 8 }}
                        />
                      )}
                    </div>
                  </div>
                );
              })}
            </div>
          )}

          <div className="actions">
            <button className="secondary-btn" onClick={() => setStep(2)}>
              <ArrowLeft /> Back
            </button>
            <button className="primary-btn" onClick={() => setStep(4)}>
              Review Booking <ArrowRight />
            </button>
          </div>
        </section>
      )}

      {step === 4 && (
        <section className="panel confirmation">
          <div className="success-circle">
            <CheckCircle2 size={42} />
          </div>
          <h2>Review &amp; Confirm</h2>
          <p className="muted">Your token will be generated after confirmation.</p>
          <div className="summary">
            <div>
              <span>Shop</span>
              <b>{selectedShop?.shopName}</b>
            </div>
            <div>
              <span>Date &amp; Time</span>
              <b>
                {date} • {selectedSlot?.startTime.slice(0, 5)}
              </b>
            </div>
            <div>
              <span>Items</span>
              <b>
                {Object.entries(selections)
                  .filter(([, v]) => v.checked)
                  .map(([type, v]) => `${type} ${v.quantity}`)
                  .join(" • ")}
              </b>
            </div>
          </div>

          {submitError && (
            <p className="muted" style={{ color: "var(--red)" }}>
              {submitError}
            </p>
          )}

          <div className="actions">
            <button className="secondary-btn" onClick={() => setStep(3)}>
              <ArrowLeft /> Change
            </button>
            <button className="primary-btn" onClick={submit} disabled={submitting}>
              <CheckCircle2 /> {submitting ? "Confirming..." : "Confirm & Generate Token"}
            </button>
          </div>
        </section>
      )}
    </>
  );
}
