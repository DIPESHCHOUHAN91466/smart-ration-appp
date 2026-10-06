import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { ArrowRight } from "lucide-react";
import apiClient from "../api/client";
import { useToast } from "../state/toast";
import { useTranslation } from "../i18n/useTranslation";
import BrandMark from "../components/BrandMark";

// Forgotten password: a one-time code goes to the account's registered mobile, then a new password is set
// (POST /auth/password/reset/request, /confirm). The answer never says whether a number is registered.
export default function ForgotPassword() {
  const navigate = useNavigate();
  const notify = useToast();
  const { t } = useTranslation();

  const [step, setStep] = useState("mobile");
  const [form, setForm] = useState({ mobileNumber: "", otp: "", password: "", confirmPassword: "" });
  const [sentTo, setSentTo] = useState(null);
  const [demoCode, setDemoCode] = useState(null);
  const [errors, setErrors] = useState([]);
  const [submitting, setSubmitting] = useState(false);

  const update = (field) => (e) => setForm({ ...form, [field]: e.target.value });

  const fail = (err, fallback) => {
    setErrors(err.errors?.length ? err.errors : [err.message || t(fallback)]);
  };

  const requestCode = async (e) => {
    e.preventDefault();
    setErrors([]);
    setSubmitting(true);
    try {
      const response = await apiClient.post("/auth/password/reset/request", { mobileNumber: form.mobileNumber.trim() });
      const data = response.data.data;
      setSentTo(data.mobileMasked);
      setDemoCode(data.demoOtpValue || null);
      setStep("code");
    } catch (err) {
      fail(err, "reset_failed");
    } finally {
      setSubmitting(false);
    }
  };

  const confirm = async (e) => {
    e.preventDefault();
    setErrors([]);
    if (form.password !== form.confirmPassword) {
      setErrors([t("passwords_mismatch")]);
      return;
    }
    setSubmitting(true);
    try {
      await apiClient.post("/auth/password/reset/confirm", {
        mobileNumber: form.mobileNumber.trim(),
        otp: form.otp.trim(),
        newPassword: form.password,
      });
      notify(t("reset_done"));
      navigate("/login", { replace: true });
    } catch (err) {
      fail(err, "reset_failed");
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
          <h1>{t("reset_heading")}</h1>
          <p>{t("reset_tagline")}</p>
        </div>
      </div>

      <div className="login-card-wrap">
        <form className="login-card" onSubmit={step === "mobile" ? requestCode : confirm}>
          <span className="eyebrow blue">{t("public_service_platform")}</span>
          <h2>{t("reset_heading")}</h2>

          {step === "mobile" ? (
            <>
              <p>{t("reset_mobile_intro")}</p>
              <label>
                {t("mobile_number")}
                <input required type="tel" inputMode="tel" maxLength={20} autoComplete="tel"
                  value={form.mobileNumber} onChange={update("mobileNumber")} placeholder="9000000001" />
              </label>
            </>
          ) : (
            <>
              <p role="status">{t("reset_code_sent").replace("{mobile}", sentTo || "")}</p>
              {demoCode && <p className="muted">{t("reset_demo_code")}: <b>{demoCode}</b></p>}
              <label>
                {t("reset_code")}
                <input required inputMode="numeric" pattern="[0-9]{6}" minLength={6} maxLength={6} autoComplete="one-time-code"
                  value={form.otp} onChange={update("otp")} />
              </label>
              <label>
                {t("new_password")}
                <input type="password" required minLength={12} maxLength={100} autoComplete="new-password"
                  value={form.password} onChange={update("password")} aria-describedby="reset-password-help" />
              </label>
              <p id="reset-password-help" className="muted" style={{ marginTop: -6 }}>{t("password_rules")}</p>
              <label>
                {t("confirm_password")}
                <input type="password" required minLength={12} maxLength={100} autoComplete="new-password"
                  value={form.confirmPassword} onChange={update("confirmPassword")} />
              </label>
            </>
          )}

          {errors.length > 0 && (
            <ul className="muted" role="alert" style={{ color: "var(--red)", paddingLeft: 18 }}>
              {errors.map((message) => (
                <li key={message}>{message}</li>
              ))}
            </ul>
          )}

          <button className="primary-btn" type="submit" disabled={submitting}>
            {step === "mobile" ? t("reset_send_code") : t("reset_set_password")} <ArrowRight size={17} />
          </button>

          <p className="muted" style={{ marginTop: 14 }}>
            <Link to="/login" style={{ textDecoration: "underline" }}>{t("reset_back_to_sign_in")}</Link>
          </p>
        </form>
      </div>
    </div>
  );
}
