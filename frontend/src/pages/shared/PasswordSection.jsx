import { useState } from "react";
import { KeyRound } from "lucide-react";
import { useAuthStore } from "../../state/authStore";
import { useTranslation } from "../../i18n/useTranslation";
import { useToast } from "../../state/toast";

// "Change password" card on the Settings page (POST /auth/password/change). The backend signs out every
// other device; this one keeps working with the new tokens it returns.
const FULL_ROW = { gridColumn: "1 / -1" };
const EMPTY = { currentPassword: "", newPassword: "", confirmPassword: "" };

export default function PasswordSection() {
  const { t } = useTranslation();
  const notify = useToast();
  const changePassword = useAuthStore((state) => state.changePassword);
  const [form, setForm] = useState(EMPTY);
  const [errors, setErrors] = useState([]);
  const [saving, setSaving] = useState(false);

  const update = (field) => (e) => setForm({ ...form, [field]: e.target.value });

  const onSubmit = async (e) => {
    e.preventDefault();
    setErrors([]);
    if (form.newPassword !== form.confirmPassword) {
      setErrors([t("passwords_mismatch")]);
      return;
    }
    setSaving(true);
    try {
      await changePassword(form.currentPassword, form.newPassword);
      setForm(EMPTY);
      notify(t("password_changed"));
    } catch (err) {
      setErrors(err.errors?.length ? err.errors : [err.message || t("password_change_failed")]);
    } finally {
      setSaving(false);
    }
  };

  return (
    <section className="panel">
      <div className="settings-section-title">
        <KeyRound size={19} />
        <h2>{t("settings_section_password")}</h2>
      </div>
      <form className="form-grid" onSubmit={onSubmit}>
        <label style={FULL_ROW}>
          {t("current_password")}
          <input type="password" required maxLength={100} autoComplete="current-password"
            value={form.currentPassword} onChange={update("currentPassword")} />
        </label>
        <label>
          {t("new_password")}
          <input type="password" required minLength={12} maxLength={100} autoComplete="new-password"
            value={form.newPassword} onChange={update("newPassword")} aria-describedby="change-password-help" />
        </label>
        <label>
          {t("confirm_password")}
          <input type="password" required minLength={12} maxLength={100} autoComplete="new-password"
            value={form.confirmPassword} onChange={update("confirmPassword")} />
        </label>
        <p id="change-password-help" className="muted" style={{ ...FULL_ROW, margin: 0 }}>
          {t("password_rules")} {t("password_change_signs_out")}
        </p>
        {errors.length > 0 && (
          <ul className="muted" role="alert" style={{ ...FULL_ROW, color: "var(--red)", paddingLeft: 18, margin: 0 }}>
            {errors.map((message) => (
              <li key={message}>{message}</li>
            ))}
          </ul>
        )}
        <button className="primary-btn" type="submit" disabled={saving} style={{ ...FULL_ROW, justifySelf: "start" }}>
          {saving ? t("profile_saving") : t("change_password")}
        </button>
      </form>
    </section>
  );
}
