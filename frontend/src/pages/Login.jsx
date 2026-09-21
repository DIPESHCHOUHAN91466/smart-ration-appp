import { useState } from "react";
import { useLocation, useNavigate, Link } from "react-router-dom";
import { ArrowRight, Globe2, ShieldCheck } from "lucide-react";
import { useAuthStore } from "../store/authStore";
import { useToast } from "../context/ToastContext";
import { homePathForRole } from "../routes/roleHome";

const DEMO_ACCOUNTS = [
  { label: "Rural User", email: "rural@example.com" },
  { label: "Shop Owner", email: "shop@example.com" },
  { label: "Government Official", email: "officer@example.com" },
];

export default function Login() {
  const navigate = useNavigate();
  const location = useLocation();
  const login = useAuthStore((state) => state.login);
  const notify = useToast();

  const [form, setForm] = useState({ email: "", password: "" });
  const [error, setError] = useState("");
  const [submitting, setSubmitting] = useState(false);

  const fillDemo = (email) => setForm({ email, password: "demo123" });

  const onSubmit = async (e) => {
    e.preventDefault();
    setError("");
    setSubmitting(true);
    try {
      const result = await login(form.email.trim(), form.password);
      notify("Secure login successful");
      const redirectTo = location.state?.from?.pathname || homePathForRole(result.user.role);
      navigate(redirectTo, { replace: true });
    } catch (err) {
      setError(err.message || "Login failed. Please check your credentials.");
      notify(err.message || "Login failed", "error");
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="login-page">
      <div className="login-art">
        <div className="login-brand">
          <div className="brand-mark light">SR</div>
          <div>
            <b>Smart Ration</b>
            <small>HSD2C Distribution Platform</small>
          </div>
        </div>
        <div className="art-content">
          <span className="eyebrow">DIGITAL INDIA • SECURE • TRANSPARENT</span>
          <h1>
            Smart Ration <em>Distribution</em>
          </h1>
          <p>Technology-driven ration distribution for a healthier and stronger community.</p>
          <div className="feature-pills">
            <span>🛡 Secure Access</span>
            <span>👥 Fair Distribution</span>
            <span>📊 Better Governance</span>
          </div>
          <div className="grain-illustration">
            <div className="sack"></div>
            <div className="bowl b1"></div>
            <div className="bowl b2"></div>
            <div className="bowl b3"></div>
          </div>
        </div>
        <div className="art-footer">
          Ensuring Food Security
          <br />
          <b>for Every Family</b>
        </div>
      </div>

      <div className="login-card-wrap">
        <div className="language login-lang">
          <Globe2 size={15} />
          <select defaultValue="English">
            <option>English</option>
            <option>मराठी</option>
            <option>हिन्दी</option>
          </select>
        </div>
        <form className="login-card" onSubmit={onSubmit}>
          <span className="eyebrow blue">PUBLIC SERVICE PLATFORM</span>
          <h2>Smart Ration Distribution</h2>
          <p>Secure role-based access for rural users, ration shops and government officials.</p>

          <label>
            Email
            <input
              type="email"
              required
              value={form.email}
              onChange={(e) => setForm({ ...form, email: e.target.value })}
              autoComplete="username"
            />
          </label>
          <label>
            Password
            <input
              type="password"
              required
              value={form.password}
              onChange={(e) => setForm({ ...form, password: e.target.value })}
              autoComplete="current-password"
            />
          </label>

          {error && (
            <p className="muted" style={{ color: "var(--red)" }}>
              {error}
            </p>
          )}

          <button className="primary-btn" type="submit" disabled={submitting}>
            {submitting ? "Signing in..." : "Login securely"} <ArrowRight size={17} />
          </button>

          <div className="or">
            <span>OR</span>
          </div>

          <div className="demo-box">
            <b>Demo Accounts (password: demo123):</b>
            <br />
            {DEMO_ACCOUNTS.map((account) => (
              <button
                key={account.email}
                type="button"
                className="link-btn"
                style={{ marginTop: 6, marginRight: 12 }}
                onClick={() => fillDemo(account.email)}
              >
                {account.label}
              </button>
            ))}
          </div>

          <p className="muted" style={{ marginTop: 14 }}>
            New here? <Link to="/register">Create a rural user account</Link>
          </p>

          <div className="login-trust">
            <ShieldCheck /> HSD2C Compliant <span /> 🔒 Data Encrypted
          </div>
        </form>
      </div>
    </div>
  );
}
