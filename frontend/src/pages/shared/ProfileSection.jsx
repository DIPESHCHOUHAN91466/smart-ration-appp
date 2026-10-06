import { useEffect, useState } from "react";
import { UserRound } from "lucide-react";
import { getProfile, updateProfile } from "../../services/usersService";
import { useAuthStore } from "../../state/authStore";
import { useTranslation } from "../../i18n/useTranslation";
import { useToast } from "../../state/toast";

// "My profile" card on the Settings page: the signed-in user edits their own name and mobile
// number (GET/PUT /api/v1/users/profile). The email is the sign-in name and stays read-only.
const FULL_ROW = { gridColumn: "1 / -1" };

export default function ProfileSection() {
  const { t } = useTranslation();
  const notify = useToast();
  const [profile, setProfile] = useState(null);
  const [form, setForm] = useState({ fullName: "", mobileNumber: "" });
  const [loadFailed, setLoadFailed] = useState(false);
  const [saving, setSaving] = useState(false);
  const [errors, setErrors] = useState([]);

  useEffect(() => {
    let active = true;
    getProfile()
      .then((data) => {
        if (!active) return;
        setProfile(data);
        setForm({ fullName: data.fullName, mobileNumber: data.mobileNumber });
      })
      .catch(() => active && setLoadFailed(true));
    return () => {
      active = false;
    };
  }, []);

  const update = (field) => (e) => setForm({ ...form, [field]: e.target.value });
  const payload = { fullName: form.fullName.trim(), mobileNumber: form.mobileNumber.trim() };
  const unchanged = profile && payload.fullName === profile.fullName && payload.mobileNumber === profile.mobileNumber;
  // Sign-in codes and password resets go to the mobile number, so a new number needs the password (the API asks too).
  const mobileChanged = profile && payload.mobileNumber !== profile.mobileNumber;

  const onSubmit = async (e) => {
    e.preventDefault();
    setErrors([]);
    setSaving(true);
    try {
      const saved = await updateProfile(mobileChanged ? { ...payload, currentPassword: form.currentPassword || "" } : payload);
      setProfile(saved);
      setForm({ fullName: saved.fullName, mobileNumber: saved.mobileNumber });
      // Keep the header's name and avatar in step with what was saved.
      const { user, updateUser } = useAuthStore.getState();
      if (user) updateUser({ ...user, fullName: saved.fullName });
      notify(t("profile_saved"));
    } catch (err) {
      setErrors(err.errors?.length ? err.errors : [err.message || t("profile_save_failed")]);
      notify(err.message || t("profile_save_failed"), "error");
    } finally {
      setSaving(false);
    }
  };

  return (
    <section className="panel">
      <div className="settings-section-title">
        <UserRound size={19} />
        <h2>{t("settings_section_profile")}</h2>
      </div>

      {loadFailed ? (
        <p className="muted" role="alert">{t("profile_load_failed")}</p>
      ) : !profile ? (
        <p className="muted">{t("loading")}</p>
      ) : (
        <form className="form-grid" onSubmit={onSubmit}>
          <label style={FULL_ROW}>
            {t("email")}
            <input value={profile.email} readOnly aria-describedby="profile-email-note" />
            <small id="profile-email-note" className="muted" style={{ fontWeight: 400 }}>{t("profile_email_note")}</small>
          </label>
          <label>
            {t("full_name")}
            <input required minLength={2} maxLength={150} autoComplete="name" value={form.fullName} onChange={update("fullName")} />
          </label>
          <label>
            {t("mobile_number")}
            <input required type="tel" inputMode="tel" maxLength={20} autoComplete="tel" value={form.mobileNumber} onChange={update("mobileNumber")} />
          </label>
          {mobileChanged && (
            <label style={FULL_ROW}>
              {t("current_password")}
              <input type="password" required maxLength={100} autoComplete="current-password" value={form.currentPassword || ""}
                onChange={update("currentPassword")} aria-describedby="profile-password-note" />
              <small id="profile-password-note" className="muted" style={{ fontWeight: 400 }}>{t("profile_mobile_password_note")}</small>
            </label>
          )}
          {errors.length > 0 && (
            <ul className="muted" role="alert" style={{ ...FULL_ROW, color: "var(--red)", paddingLeft: 18, margin: 0 }}>
              {errors.map((message) => (
                <li key={message}>{message}</li>
              ))}
            </ul>
          )}
          <button className="primary-btn" type="submit" disabled={saving || unchanged} style={{ ...FULL_ROW, justifySelf: "start" }}>
            {saving ? t("profile_saving") : t("save")}
          </button>
        </form>
      )}
    </section>
  );
}
