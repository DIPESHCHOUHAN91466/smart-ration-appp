import { useEffect, useState } from "react";
import { ShieldCheck } from "lucide-react";
import apiClient from "../../api/client";
import QRCodeCanvas from "../../components/QRCodeCanvas";
import { useTranslation } from "../../i18n/useTranslation";
import { useToast } from "../../state/toast";

// "Two-factor sign-in" card on Settings for shop owners, officials and admins (opt-in TOTP,
// /auth/mfa/status|setup|enable|disable). Once on, every password sign-in also asks for the app's 6-digit code.
const FULL_ROW = { gridColumn: "1 / -1" };

export default function MfaSection() {
  const { t } = useTranslation();
  const notify = useToast();
  const [status, setStatus] = useState(null);
  const [setup, setSetup] = useState(null);           // { secret, otpauthUri } while setting up
  const [password, setPassword] = useState("");
  const [code, setCode] = useState("");
  const [errors, setErrors] = useState([]);
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    let active = true;
    apiClient.get("/auth/mfa/status")
      .then((r) => active && setStatus(r.data.data))
      .catch(() => active && setStatus({ enabled: false, available: false }));
    return () => {
      active = false;
    };
  }, []);

  const run = async (action) => {
    setErrors([]);
    setBusy(true);
    try {
      await action();
    } catch (err) {
      setErrors(err.errors?.length ? err.errors : [err.message || t("mfa_failed")]);
    } finally {
      setBusy(false);
    }
  };

  const start = (e) => {
    e.preventDefault();
    run(async () => {
      const r = await apiClient.post("/auth/mfa/setup", { password });
      setSetup(r.data.data);
      setPassword("");
    });
  };

  const confirm = (e) => {
    e.preventDefault();
    run(async () => {
      const r = await apiClient.post("/auth/mfa/enable", { code: code.trim() });
      setStatus(r.data.data);
      setSetup(null);
      setCode("");
      notify(t("mfa_enabled_toast"));
    });
  };

  const turnOff = (e) => {
    e.preventDefault();
    run(async () => {
      const r = await apiClient.post("/auth/mfa/disable", { password, code: code.trim() });
      setStatus(r.data.data);
      setPassword("");
      setCode("");
      notify(t("mfa_disabled_toast"));
    });
  };

  const errorList = errors.length > 0 && (
    <ul className="muted" role="alert" style={{ ...FULL_ROW, color: "var(--red)", paddingLeft: 18, margin: 0 }}>
      {errors.map((message) => <li key={message}>{message}</li>)}
    </ul>
  );
  const passwordField = (
    <label style={FULL_ROW}>
      {t("current_password")}
      <input type="password" required maxLength={100} autoComplete="current-password" value={password}
        onChange={(e) => setPassword(e.target.value)} />
    </label>
  );
  const codeField = (
    <label style={FULL_ROW}>
      {t("mfa_code")}
      <input required inputMode="numeric" pattern="[0-9]{6}" minLength={6} maxLength={6} autoComplete="one-time-code"
        value={code} onChange={(e) => setCode(e.target.value)} />
    </label>
  );

  return (
    <section className="panel">
      <div className="settings-section-title">
        <ShieldCheck size={19} />
        <h2>{t("settings_section_mfa")}</h2>
      </div>

      {!status ? (
        <p className="muted">{t("loading")}</p>
      ) : !status.available && !status.enabled ? (
        <p className="muted">{t("mfa_unavailable")}</p>
      ) : status.enabled ? (
        <form className="form-grid" onSubmit={turnOff}>
          <p role="status" style={FULL_ROW}><b>{t("mfa_is_on")}</b> {t("mfa_off_hint")}</p>
          {passwordField}
          {codeField}
          {errorList}
          <button className="secondary-btn" type="submit" disabled={busy} style={{ ...FULL_ROW, justifySelf: "start" }}>
            {t("mfa_turn_off")}
          </button>
        </form>
      ) : setup ? (
        <form className="form-grid" onSubmit={confirm}>
          <p style={FULL_ROW}>{t("mfa_scan")}</p>
          <div style={FULL_ROW}>
            <QRCodeCanvas value={setup.otpauthUri} size={180} errorCorrectionLevel="M" label={t("mfa_qr_label")} />
            <p className="muted" style={{ marginTop: 6 }}>
              {t("mfa_manual_key")}: <code style={{ wordBreak: "break-all" }}>{setup.secret}</code>
            </p>
          </div>
          {codeField}
          {errorList}
          <button className="primary-btn" type="submit" disabled={busy} style={{ ...FULL_ROW, justifySelf: "start" }}>
            {t("mfa_turn_on")}
          </button>
        </form>
      ) : (
        <form className="form-grid" onSubmit={start}>
          <p style={FULL_ROW}>{t("mfa_intro")}</p>
          {passwordField}
          {errorList}
          <button className="primary-btn" type="submit" disabled={busy} style={{ ...FULL_ROW, justifySelf: "start" }}>
            {t("mfa_set_up")}
          </button>
        </form>
      )}
    </section>
  );
}
