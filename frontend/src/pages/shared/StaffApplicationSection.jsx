import { useEffect, useState } from "react";
import { BadgeCheck } from "lucide-react";
import { getShops } from "../../services/shopsService";
import { applyForStaffRole, getMyStaffApplications, withdrawStaffApplication } from "../../services/staffService";
import { useToast } from "../../state/toast";

// "Work as a shop owner or official" card on Settings, citizens only. Applying grants nothing: an administrator checks
// the details outside the app and approves or rejects (POST /api/staff-applications; migration 0009).
export default function StaffApplicationSection() {
  const notify = useToast();
  const [applications, setApplications] = useState([]);
  const [shops, setShops] = useState([]);
  const [form, setForm] = useState({ requestedRole: "ShopOwner", rationShopId: "", office: "", designation: "", proofReference: "" });
  const [errors, setErrors] = useState([]);
  const [busy, setBusy] = useState(false);

  const load = () => getMyStaffApplications().then(setApplications).catch(() => setApplications([]));
  useEffect(() => {
    load();
    getShops().then(setShops).catch(() => setShops([]));
  }, []);

  const pending = applications.find((a) => a.status === "Pending");
  const set = (field) => (e) => setForm((f) => ({ ...f, [field]: e.target.value }));

  const onSubmit = async (e) => {
    e.preventDefault();
    setErrors([]);
    setBusy(true);
    const shopOwner = form.requestedRole === "ShopOwner";
    try {
      await applyForStaffRole({
        requestedRole: form.requestedRole,
        rationShopId: shopOwner && form.rationShopId ? Number(form.rationShopId) : null,
        office: shopOwner ? null : form.office,
        designation: form.designation,
        proofReference: form.proofReference,
      });
      notify("Application sent. An administrator will review it.");
      await load();
    } catch (err) {
      setErrors(err.errors?.length ? err.errors.map((m) => m.replace(/^[A-Za-z]+:\s*/, "")) : [err.message]);
    } finally {
      setBusy(false);
    }
  };

  const withdraw = async (id) => {
    try {
      await withdrawStaffApplication(id);
      await load();
    } catch (err) {
      setErrors([err.message]);
    }
  };

  return (
    <section className="panel">
      <div className="settings-section-title">
        <BadgeCheck size={19} />
        <h2>Work as a shop owner or official</h2>
      </div>
      <p className="muted">
        Apply here. Nothing changes for your account until an administrator has checked your details and approved the
        request. Do not enter Aadhaar numbers.
      </p>

      {applications.length > 0 && (
        <ul aria-label="My applications" style={{ paddingLeft: 18 }}>
          {applications.map((a) => (
            <li key={a.id}>
              {a.requestedRole === "ShopOwner" ? `Shop owner: ${a.rationShopName ?? ""}` : `Official: ${a.office ?? ""}`} —{" "}
              <b>{a.status}</b>
              {a.decisionReason ? ` (${a.decisionReason})` : ""}
              {a.status === "Pending" && (
                <button type="button" className="secondary-btn" style={{ marginLeft: 8 }} onClick={() => withdraw(a.id)}>
                  Withdraw
                </button>
              )}
            </li>
          ))}
        </ul>
      )}

      {!pending && (
        <form onSubmit={onSubmit} aria-label="Staff application">
          <label className="settings-field-label" htmlFor="staff-role">I want to work as</label>
          <select id="staff-role" className="small-select" value={form.requestedRole} onChange={set("requestedRole")}>
            <option value="ShopOwner">Ration shop owner</option>
            <option value="GovernmentOfficial">Government official</option>
          </select>

          {form.requestedRole === "ShopOwner" ? (
            <>
              <label className="settings-field-label" htmlFor="staff-shop">Ration shop</label>
              <select id="staff-shop" className="small-select" value={form.rationShopId} onChange={set("rationShopId")} required>
                <option value="">Choose a shop</option>
                {shops.map((s) => (
                  <option key={s.id} value={s.id}>
                    {s.shopName}
                  </option>
                ))}
              </select>
            </>
          ) : (
            <>
              <label className="settings-field-label" htmlFor="staff-office">District or office</label>
              <input id="staff-office" value={form.office} onChange={set("office")} maxLength={200} required />
            </>
          )}

          <label className="settings-field-label" htmlFor="staff-designation">Designation</label>
          <input id="staff-designation" value={form.designation} onChange={set("designation")} maxLength={120} required />

          <label className="settings-field-label" htmlFor="staff-proof">Licence or employee ID number</label>
          <input id="staff-proof" value={form.proofReference} onChange={set("proofReference")} maxLength={120} required />

          {errors.length > 0 && (
            <ul className="muted" role="alert" style={{ color: "var(--red)", paddingLeft: 18 }}>
              {errors.map((m) => (
                <li key={m}>{m}</li>
              ))}
            </ul>
          )}
          <button type="submit" className="primary-btn" disabled={busy} style={{ marginTop: 10 }}>
            {busy ? "Sending..." : "Send application"}
          </button>
        </form>
      )}
    </section>
  );
}
