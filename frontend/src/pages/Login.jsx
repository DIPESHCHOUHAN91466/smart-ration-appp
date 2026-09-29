import { useState } from "react";
import { useLocation, useNavigate, Link } from "react-router-dom";
import { ArrowRight, Eye, EyeOff, Globe2, ShieldCheck, Sparkles, ScanEye, Landmark, BrainCircuit, Target, QrCode, CheckCircle2 } from "lucide-react";
import { useAuthStore } from "../state/authStore";
import { useToast } from "../state/toast";
import { homePathForRole } from "../features/auth/roleHome";
import { useTranslation } from "../i18n/useTranslation";
import { LANGUAGE_OPTIONS } from "../i18n/translations";
import BrandMark from "../components/BrandMark";
import { DEMO_MODE } from "../config/env";

// Demo accounts are a development/demo aid only: hidden when the build sets VITE_DEMO_MODE=false
// (config/env.js).

const DEMO_ACCOUNTS = [
  { labelKey: "role_rural_user", email: "rural@example.com" },
  { labelKey: "role_shop_owner", email: "shop@example.com" },
  { labelKey: "role_government_official", email: "officer@example.com" },
];

const AI_FLOW_STEPS = [
  { key: "ai_flow_ai", Icon: BrainCircuit },
  { key: "ai_flow_allocation", Icon: Target },
  { key: "ai_flow_token", Icon: QrCode },
  { key: "ai_flow_distribution", Icon: CheckCircle2 },
];

export default function Login() {
  const navigate = useNavigate();
  const location = useLocation();
  const login = useAuthStore((state) => state.login);
  const notify = useToast();
  const { t, language, setLanguage } = useTranslation();

  const [form, setForm] = useState({ email: "", password: "" });
  const [error, setError] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [showPassword, setShowPassword] = useState(false);

  const fillDemo = (email) => setForm({ email, password: "demo123" });

  const onSubmit = async (e) => {
    e.preventDefault();
    setError("");
    setSubmitting(true);
    try {
      const result = await login(form.email.trim(), form.password);
      notify(t("secure_login_successful"));
      const redirectTo = location.state?.from?.pathname || homePathForRole(result.user.role);
      navigate(redirectTo, { replace: true });
    } catch (err) {
      setError(err.message || t("invalid_credentials"));
      notify(err.message || t("invalid_credentials"), "error");
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
            <span className="ai-badge">
              <Sparkles size={15} />
              AI
            </span>{" "}
            {t("login_hero_prefix")} <em>{t("login_hero_suffix")}</em>
          </h1>
          <p>{t("login_hero_tagline")}</p>

          <div className="ai-flow" aria-hidden="true">
            {AI_FLOW_STEPS.map(({ key, Icon }, idx) => (
              <div className="flow-step-wrap" key={key}>
                <div className="step">
                  <Icon />
                  <span>{t(key)}</span>
                </div>
                {idx < AI_FLOW_STEPS.length - 1 && <div className="connector" />}
              </div>
            ))}
          </div>

          <div className="ration-row">
            <div className="ration-chip">
              <div className="icon-wrap">
                <div className="grain-shape rice" />
              </div>
              <small>{t("ration_rice")}</small>
            </div>
            <div className="ration-chip">
              <div className="icon-wrap">
                <div className="grain-shape wheat" />
              </div>
              <small>{t("ration_wheat")}</small>
            </div>
            <div className="ration-chip">
              <div className="icon-wrap">
                <div className="grain-shape dal" />
              </div>
              <small>{t("ration_dal")}</small>
            </div>
            <div className="ration-chip">
              <div className="icon-wrap">
                <div className="grain-shape sugar" />
              </div>
              <small>{t("ration_sugar")}</small>
            </div>
            <div className="ration-chip">
              <div className="icon-wrap">
                <div className="oil-shape" />
              </div>
              <small>{t("ration_label_oil")}</small>
            </div>
          </div>

          <div className="trust-grid">
            <div>
              <ShieldCheck size={16} />
              <span>{t("pill_secure")}</span>
            </div>
            <div>
              <Sparkles size={16} />
              <span>{t("pill_ai_allocation")}</span>
            </div>
            <div>
              <ScanEye size={16} />
              <span>{t("pill_transparent")}</span>
            </div>
            <div>
              <Landmark size={16} />
              <span>{t("pill_governance")}</span>
            </div>
          </div>
        </div>

        <div className="art-footer">
          {t("art_footer_line1")}
          <br />
          <b>{t("art_footer_line2")}</b>
        </div>
      </div>

      <div className="login-card-wrap">
        <div className="language login-lang">
          <Globe2 size={15} />
          <select value={language} onChange={(e) => setLanguage(e.target.value)}>
            {LANGUAGE_OPTIONS.map((opt) => (
              <option key={opt.code} value={opt.code}>{opt.label}</option>
            ))}
          </select>
        </div>
        <form className="login-card" onSubmit={onSubmit}>
          <span className="eyebrow blue">{t("public_service_platform")}</span>
          <h2>{t("login_title")}</h2>
          <p>{t("login_subtitle")}</p>

          <label>
            {t("email")}
            <input type="email" required value={form.email} onChange={(e) => setForm({ ...form, email: e.target.value })} autoComplete="username" />
          </label>
          <label>
            {t("password")}
            <div className="password-field">
              <input
                type={showPassword ? "text" : "password"}
                required
                value={form.password}
                onChange={(e) => setForm({ ...form, password: e.target.value })}
                autoComplete="current-password"
              />
              <button
                type="button"
                className="password-toggle"
                aria-label={showPassword ? t("hide_password") : t("show_password")}
                onClick={() => setShowPassword((v) => !v)}
              >
                {showPassword ? <EyeOff size={16} /> : <Eye size={16} />}
              </button>
            </div>
          </label>

          {error && <p className="muted" style={{ color: "var(--red)" }}>{error}</p>}

          <button className="primary-btn" type="submit" disabled={submitting}>
            {submitting ? (
              <>
                <span className="btn-spinner" /> {t("signing_in")}
              </>
            ) : (
              <>
                {t("login_securely")} <ArrowRight size={17} />
              </>
            )}
          </button>

          {DEMO_MODE && (
            <>
              <div className="or"><span>OR</span></div>
              <div className="demo-box">
                <b>{t("demo_accounts")}:</b><br />
                {DEMO_ACCOUNTS.map((account) => (
                  <button key={account.email} type="button" className="link-btn" style={{ marginTop: 6, marginRight: 12 }} onClick={() => fillDemo(account.email)}>
                    {t(account.labelKey)}
                  </button>
                ))}
              </div>
            </>
          )}

          <p className="muted" style={{ marginTop: 14 }}>
            {t("new_here")} <Link to="/register">{t("create_account_link")}</Link>
          </p>

          <div className="login-trust"><ShieldCheck /> {t("hsd2c_compliant")} <span /> 🔒 {t("data_encrypted")}</div>
        </form>
      </div>
    </div>
  );
}
