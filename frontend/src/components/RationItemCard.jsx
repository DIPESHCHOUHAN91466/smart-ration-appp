import { Minus, Plus } from "lucide-react";
import { useTranslation } from "../i18n/useTranslation";

const RATION_ICONS = { Rice: "🌾", Wheat: "🌿", Sugar: "🍬", Pulses: "🫘", EdibleOil: "🛢️", Salt: "🧂" };
const RATION_NAME_KEY = { Rice: "ration_rice", Wheat: "ration_wheat", Sugar: "ration_sugar", Pulses: "ration_pulses", EdibleOil: "ration_oil", Salt: "ration_salt" };

// Reusable ration-item selection card: icon + localized name, real Available
// (shop inventory) / Eligible (entitlement-derived) quantities, and a +/-
// stepper that cannot go negative or past whichever cap (eligibility or
// inventory) is lower — no free-text quantity input, so an invalid quantity
// is simply not reachable rather than caught after the fact.
export default function RationItemCard({ item, selected, quantity, onToggle, onQuantityChange }) {
  const { t } = useTranslation();
  const icon = RATION_ICONS[item.rationType] || "🌾";
  const nameKey = RATION_NAME_KEY[item.rationType];
  const localizedName = nameKey ? t(nameKey) : item.name;
  const eligible = item.eligibleQuantity ?? item.standardQuotaPerBooking;
  const available = item.availableQuantity;
  const maxQty = available != null ? Math.min(eligible, available) : eligible;
  const exhausted = maxQty <= 0;

  const step = (delta) => {
    const next = Math.round((Number(quantity) + delta) * 10) / 10;
    if (next < 0 || next > maxQty) return;
    onQuantityChange(next);
  };

  return (
    <div className={`item-card ration-card ${selected ? "chosen" : ""}`} style={{ cursor: "default" }}>
      <span className="item-icon">{icon}</span>
      <div style={{ flex: 1 }}>
        <label style={{ display: "flex", alignItems: "center", gap: 8, cursor: exhausted ? "not-allowed" : "pointer" }}>
          <input type="checkbox" checked={selected} onChange={onToggle} disabled={exhausted} style={{ width: "auto" }} />
          <b>
            {item.name} <small>({localizedName})</small>
          </b>
        </label>
        <div className="ration-meta">
          <span>
            {t("qty_available")}: {available != null ? `${available} ${item.unit}` : "—"}
          </span>
          <span>
            {t("qty_eligible")}: {eligible} {item.unit}
          </span>
        </div>

        {exhausted && (
          <small className="muted" style={{ color: "var(--red)" }}>
            {available != null && available <= 0 ? t("validation_qty_exceeds_inventory") : t("no_entitlement")}
          </small>
        )}

        {selected && !exhausted && (
          <div className="qty-stepper">
            <button type="button" onClick={() => step(-0.5)} disabled={quantity <= 0} aria-label={t("validation_qty_negative")}>
              <Minus size={14} />
            </button>
            <span>
              {quantity} {item.unit}
            </span>
            <button type="button" onClick={() => step(0.5)} disabled={quantity >= maxQty} aria-label={t("qty_selected")}>
              <Plus size={14} />
            </button>
          </div>
        )}
      </div>
    </div>
  );
}
