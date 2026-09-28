import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { ArrowLeft, ArrowRight, CheckCircle2, Clock3, Store } from "lucide-react";
import PageHeader from "../../components/PageHeader";
import { ErrorState, LoadingState } from "../../components/EmptyState";
import RationItemCard from "../../components/RationItemCard";
import { getShops } from "../../services/shopsService";
import { getSlots } from "../../services/slotsService";
import { getRationItems, createBooking } from "../../services/rationService";
import { useToast } from "../../state/toast";
import { useTranslation } from "../../i18n/useTranslation";
import { usePreferencesStore } from "../../state/preferencesStore";

function today() {
  return new Date().toISOString().slice(0, 10);
}

export default function BookRation() {
  const navigate = useNavigate();
  const notify = useToast();
  const { t } = useTranslation();
  const showAvailability = usePreferencesStore((s) => s.showAvailability);

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
    if (step !== 3 || !shopId) return;
    getRationItems(shopId)
      .then((items) => {
        setCatalog(items);
        setSelections(
          Object.fromEntries(
            items.map((item) => {
              const eligible = item.eligibleQuantity ?? item.standardQuotaPerBooking;
              const cap = item.availableQuantity != null ? Math.min(eligible, item.availableQuantity) : eligible;
              const initialQty = Math.min(item.standardQuotaPerBooking, cap);
              return [item.rationType, { checked: cap > 0, quantity: cap > 0 ? initialQty : 0 }];
            }),
          ),
        );
      })
      .catch((err) => setCatalogError(err.message));
  }, [step, shopId]);

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
      setSubmitError(t("select_at_least_one_item"));
      return;
    }

    setSubmitting(true);
    try {
      const token = await createBooking({ rationShopId: shopId, timeSlotId, items });
      notify(t("token_qr_generated"));
      navigate(`/rural/token/${token.id}`, { replace: true });
    } catch (err) {
      setSubmitError(err.errors?.join(" ") || err.message || t("could_not_create_booking"));
      notify(err.message || t("booking_failed"), "error");
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <>
      <PageHeader title={t("book_ration_title")} subtitle={t("book_ration_subtitle")} />
      <div className="stepper">
        {[t("step_select_shop"), t("step_select_slot"), t("step_select_items"), t("step_confirm")].map((label, i) => (
          <div key={label} className={step === i + 1 ? "current" : step > i + 1 ? "done" : ""}>
            <span>{step > i + 1 ? "✓" : i + 1}</span>
            {label}
          </div>
        ))}
      </div>

      {step === 1 && (
        <section className="panel form-panel">
          <h2>{t("choose_shop_heading")}</h2>
          {shopsError && <ErrorState text={shopsError} />}
          {!shopsError && shops === null && <LoadingState text={t("loading")} />}
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
            {t("continue_to_slot")} <ArrowRight />
          </button>
        </section>
      )}

      {step === 2 && (
        <section className="panel form-panel">
          <h2>{t("choose_slot_heading")}</h2>
          <div className="form-grid">
            <label>
              {t("ration_shop_label")}
              <input value={selectedShop?.shopName || ""} disabled />
            </label>
            <label>
              {t("date_label")}
              <input type="date" min={today()} value={date} onChange={(e) => setDate(e.target.value)} />
            </label>
          </div>

          {slotsError && <ErrorState text={slotsError} />}
          {!slotsError && slots === null && <LoadingState text={t("loading")} />}
          {slots && slots.length === 0 && <ErrorState title={t("no_slots_title")} text={t("no_slots_text")} />}

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
                  {showAvailability && (
                    <small style={{ color: slot.status === "Full" ? "var(--red)" : slot.status === "Limited" ? "var(--orange)" : "var(--green)" }}>
                      {slot.status} ({slot.capacity - slot.bookedCount} left)
                    </small>
                  )}
                </button>
              ))}
            </div>
          )}

          <div className="actions">
            <button className="secondary-btn" onClick={() => setStep(1)}>
              <ArrowLeft /> {t("back")}
            </button>
            <button className="primary-btn" disabled={!timeSlotId} onClick={() => setStep(3)}>
              {t("continue_to_items")} <ArrowRight />
            </button>
          </div>
        </section>
      )}

      {step === 3 && (
        <section className="panel form-panel">
          <h2>{t("select_items_heading")}</h2>
          <p className="muted">{t("select_items_subtitle")}</p>

          {catalogError && <ErrorState text={catalogError} />}
          {!catalogError && catalog === null && <LoadingState text={t("loading")} />}

          {catalog && (
            <div className="item-grid">
              {catalog.map((item) => {
                const selection = selections[item.rationType] || { checked: false, quantity: 0 };
                return (
                  <RationItemCard
                    key={item.rationType}
                    item={item}
                    selected={selection.checked}
                    quantity={selection.quantity}
                    onToggle={() => toggleItem(item.rationType)}
                    onQuantityChange={(qty) => setQuantity(item.rationType, qty)}
                  />
                );
              })}
            </div>
          )}

          <div className="actions">
            <button className="secondary-btn" onClick={() => setStep(2)}>
              <ArrowLeft /> {t("back")}
            </button>
            <button className="primary-btn" onClick={() => setStep(4)}>
              {t("review_confirm_heading")} <ArrowRight />
            </button>
          </div>
        </section>
      )}

      {step === 4 && (
        <section className="panel confirmation">
          <div className="success-circle">
            <CheckCircle2 size={42} />
          </div>
          <h2>{t("review_confirm_heading")}</h2>
          <p className="muted">{t("review_confirm_subtitle")}</p>
          <div className="summary">
            <div>
              <span>{t("shop_label")}</span>
              <b>{selectedShop?.shopName}</b>
            </div>
            <div>
              <span>{t("date_time_label")}</span>
              <b>
                {date} • {selectedSlot?.startTime.slice(0, 5)}
              </b>
            </div>
            <div>
              <span>{t("items_label")}</span>
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
              <ArrowLeft /> {t("change")}
            </button>
            <button className="primary-btn" onClick={submit} disabled={submitting}>
              <CheckCircle2 /> {submitting ? t("confirming") : t("confirm_generate_token")}
            </button>
          </div>
        </section>
      )}
    </>
  );
}
