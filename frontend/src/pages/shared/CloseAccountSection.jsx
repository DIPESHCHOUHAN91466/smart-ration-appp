import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { UserX } from "lucide-react";
import apiClient from "../../api/client";
import { useAuthStore } from "../../state/authStore";
import { useTranslation } from "../../i18n/useTranslation";
import { useToast } from "../../state/toast";

// "Close my account" card on Settings, citizens only (POST /users/me/close; Google Play account-deletion rule).
// The account is switched off at once and every session ends; the privacy policy says when records are erased.
export default function CloseAccountSection() {
  const { t } = useTranslation();
  const notify = useToast();
  const navigate = useNavigate();
  const clearSession = useAuthStore((state) => state.clearSession);
  const [open, setOpen] = useState(false);
  const [password, setPassword] = useState("");
  const [errors, setErrors] = useState([]);
  const [busy, setBusy] = useState(false);

  const onSubmit = async (e) => {
    e.preventDefault();
    setErrors([]);
    setBusy(true);
    try {
      await apiClient.post("/users/me/close", { currentPassword: password });
      clearSession();
      notify(t("close_account_done"));
      navigate("/login", { replace: true });
    } catch (err) {
      setErrors(err.errors?.length ? err.errors.map((m) => m.replace(/^[A-Za-z]+:\s*/, "")) : [err.message]);
      setBusy(false);
    }
  };

  return (
    <section className="panel">
      <div className="settings-section-title">
        <UserX size={19} style={{ color: "var(--red)" }} />
        <h2>{t("close_account_title")}</h2>
      </div>
      <p className="muted">{t("close_account_intro")}</p>
      {!open ? (
        <button className="secondary-btn" type="button" style={{ color: "var(--red)" }} onClick={() => setOpen(true)}>
          {t("close_account_title")}
        </button>
      ) : (
        <form className="form-grid" onSubmit={onSubmit}>
          <label style={{ gridColumn: "1 / -1" }}>
            {t("current_password")}
            <input type="password" required maxLength={100} autoComplete="current-password"
              value={password} onChange={(e) => setPassword(e.target.value)} />
          </label>
          {errors.length > 0 && (
            <ul className="muted" role="alert" style={{ gridColumn: "1 / -1", color: "var(--red)", paddingLeft: 18, margin: 0 }}>
              {errors.map((message) => <li key={message}>{message}</li>)}
            </ul>
          )}
          <div className="actions" style={{ gridColumn: "1 / -1", marginTop: 0 }}>
            <button className="primary-btn" type="submit" disabled={busy}
              style={{ background: "var(--red)", boxShadow: "none" }}>
              {busy ? t("close_account_closing") : t("close_account_confirm")}
            </button>
            <button className="secondary-btn" type="button" disabled={busy} onClick={() => setOpen(false)}>
              {t("cancel")}
            </button>
          </div>
        </form>
      )}
    </section>
  );
}
