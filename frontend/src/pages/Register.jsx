import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { ArrowRight, ShieldCheck } from "lucide-react";
import { useAuthStore } from "../store/authStore";
import { useToast } from "../context/ToastContext";
import { homePathForRole } from "../routes/roleHome";

export default function Register() {
  const navigate = useNavigate();
  const register = useAuthStore((state) => state.register);
  const notify = useToast();

  const [form, setForm] = useState({ fullName: "", email: "", mobileNumber: "", password: "", confirmPassword: "" });
  const [errors, setErrors] = useState([]);
  const [submitting, setSubmitting] = useState(false);

  const update = (field) => (e) => setForm({ ...form, [field]: e.target.value });

  const onSubmit = async (e) => {
    e.preventDefault();
    setErrors([]);

    if (form.password !== form.confirmPassword) {
      setErrors(["Passwords do not match."]);
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
      notify("Account created — welcome to Smart Ration");
      navigate(homePathForRole(result.user.role), { replace: true });
    } catch (err) {
      setErrors(err.errors?.length ? err.errors : [err.message || "Registration failed."]);
      notify(err.message || "Registration failed", "error");
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
            Join as a <em>Rural User</em>
          </h1>
          <p>Register to book your ration collection slot, generate a token and track your history online.</p>
        </div>
      </div>

      <div className="login-card-wrap">
        <form className="login-card" onSubmit={onSubmit}>
          <span className="eyebrow blue">PUBLIC SERVICE PLATFORM</span>
          <h2>Create your account</h2>
          <p>Self-registration creates a Rural User account. Shop and government accounts are provisioned by administrators.</p>

          <label>
            Full name
            <input required value={form.fullName} onChange={update("fullName")} />
          </label>
          <label>
            Email
            <input type="email" required value={form.email} onChange={update("email")} autoComplete="username" />
          </label>
          <label>
            Mobile number
            <input required value={form.mobileNumber} onChange={update("mobileNumber")} placeholder="9876543210" />
          </label>
          <label>
            Password
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
            Confirm password
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
            {submitting ? "Creating account..." : "Create account"} <ArrowRight size={17} />
          </button>

          <p className="muted" style={{ marginTop: 14 }}>
            Already registered? <Link to="/login">Sign in</Link>
          </p>

          <div className="login-trust">
            <ShieldCheck /> HSD2C Compliant <span /> 🔒 Data Encrypted
          </div>
        </form>
      </div>
    </div>
  );
}
