import { unitTotals, familyCounts } from "../../../features/qr/familyEligibility";
import { useTranslation } from "../../../i18n/useTranslation";
import { rationItemLabel, rationItemUnit } from "../../../utils/format";

// What may be issued at this collection (the server's today-allocation), with per-unit totals:
// kilograms and litres are totalled separately, never added together.
export default function RationEntitlement({ verification }) {
  const { t } = useTranslation();
  const items = (verification.entitlement?.items ?? []).filter((i) => i.todayAllocation > 0);
  const totals = unitTotals(items, "todayAllocation");
  const { eligible } = familyCounts(verification.family);
  if (items.length === 0) return null;

  return (
    <section className="elig-card" aria-labelledby="ration-entitlement-title">
      <span className="eyebrow blue" id="ration-entitlement-title">{t("ration_entitlement")}</span>
      <table className="elig-table">
        <thead>
          <tr>
            <th scope="col">{t("item")}</th>
            <th scope="col" className="num">{t("eligible_quantity")}</th>
          </tr>
        </thead>
        <tbody>
          {items.map((item) => (
            <tr key={item.rationType}>
              <td>{rationItemLabel(item.rationType)}</td>
              <td className="num">
                <b>{item.todayAllocation}</b> {rationItemUnit(item.rationType)}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
      <div className="elig-totals" aria-label={t("total_this_collection")}>
        <span className="elig-totals-title">{t("total_this_collection")}</span>
        <div>
          <span>{t("eligible_members")}</span>
          <b>{eligible}</b>
        </div>
        <div>
          <span>{t("ration_items")}</span>
          <b>{items.length}</b>
        </div>
        {totals.kg != null && (
          <div>
            <span>{t("dry_goods")}</span>
            <b>{totals.kg} kg</b>
          </div>
        )}
        {totals.L != null && (
          <div>
            <span>{t("liquids")}</span>
            <b>{totals.L} L</b>
          </div>
        )}
      </div>
    </section>
  );
}
