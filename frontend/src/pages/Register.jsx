import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { ArrowRight, ShieldCheck } from "lucide-react";
import { useAuthStore } from "../state/authStore";
import { useToast } from "../state/toast";
import { homePathForRole } from "../features/auth/roleHome";
import { useTranslation } from "../i18n/useTranslation";
import BrandMark from "../components/BrandMark";

export default function Register() {
  const navigate = useNavigate();
  const register = useAuthStore((state) => state.register);
  const notify = useToast();
  const { t } = useTranslation();

  const [form, setForm] = useState({ fullName: "", email: "", mobileNumber: "", password: "", confirmPassword: "" });
  const [errors, setErrors] = useState([]);
  const [submitting, setSubmitting] = useState(false);

  const update = (field) => (e) => setForm({ ...form, [field]: e.target.value });

  const onSubmit = async (e) => {
    e.preventDefault();
    setErrors([]);

    if (form.password !== form.confirmPassword) {
      setErrors([t("passwords_mismatch")]);
      return;
    }

    setSubmitting(true);
    try {
      const result = await register({
        fullName: form.fullName.trim(),
        email: form.email.trim(),
        mobileNumber: form.mobileNumber.trim(),
        password: form.password,
      });
      notify(t("registration_success"));
      navigate(homePathForRole(result.user.role), { replace: true });
    } catch (err) {
      setErrors(err.errors?.length ? err.errors : [err.message || t("registration_failed")]);
      notify(err.message || t("registration_failed"), "error");
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="login-page">
      <div className="login-art">
        <div className="login-brand">
          <BrandMark variant="login" />
        </div>
        <div className="art-content">
          <span className="eyebrow">{t("login_eyebrow")}</span>
          <h1>
            {t("register_join_prefix")} <em>{t("register_join_role")}</em>
          </h1>
          <p>{t("register_tagline")}</p>
        </div>
      </div>

      <div className="login-card-wrap">
        <form className="login-card" onSubmit={onSubmit}>
          <span className="eyebrow blue">{t("public_service_platform")}</span>
          <h2>{t("register_heading")}</h2>
          <p>{t("register_subtitle")}</p>

          <label>
            {t("full_name")}
            <input required value={form.fullName} onChange={update("fullName")} />
          </label>
          <label>
            {t("email")}
            <input type="email" required value={form.email} onChange={update("email")} autoComplete="username" />
          </label>
          <label>
            {t("mobile_number")}
            <input required value={form.mobileNumber} onChange={update("mobileNumber")} placeholder="9000000001" />
          </label>
          <label>
            {t("password")}
            <input
              type="password"
              required
              minLength={8}
              value={form.password}
              onChange={update("password")}
              autoComplete="new-password"
            />
          </label>
          <label>
            {t("confirm_password")}
            <input
              type="password"
              required
              minLength={8}
              value={form.confirmPassword}
              onChange={update("confirmPassword")}
              autoComplete="new-password"
            />
          </label>

          {errors.length > 0 && (
            <ul className="muted" style={{ color: "var(--red)", paddingLeft: 18 }}>
              {errors.map((message) => (
                <li key={message}>{message}</li>
              ))}
            </ul>
          )}

          <button className="primary-btn" type="submit" disabled={submitting}>
            {submitting ? t("creating_account") : t("create_account")} <ArrowRight size={17} />
          </button>

          <p className="muted" style={{ marginTop: 14 }}>
            {t("already_registered")} <Link to="/login">{t("sign_in")}</Link>
          </p>

          <div className="login-trust">
            <ShieldCheck /> {t("hsd2c_compliant")} <span /> 🔒 {t("data_encrypted")}
          </div>
        </form>
      </div>
    </div>
  );
}
