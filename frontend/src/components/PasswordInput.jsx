import { useState } from "react";
import { Eye, EyeOff } from "lucide-react";
import { useTranslation } from "../i18n/useTranslation";

// The backend's rule for a NEW password (app/security/password_policy.py: MIN_LENGTH / MAX_LENGTH).
export const PASSWORD_MIN_LENGTH = 8;
export const PASSWORD_MAX_LENGTH = 100;

// A password box with the eye button that shows / hides what was typed (same look as the Login page).
export default function PasswordInput({ isNew = true, ...props }) {
  const { t } = useTranslation();
  const [visible, setVisible] = useState(false);
  const limits = isNew ? { minLength: PASSWORD_MIN_LENGTH, maxLength: PASSWORD_MAX_LENGTH } : {};
  return (
    <div className="password-field">
      <input autoComplete={isNew ? "new-password" : "current-password"} {...limits} {...props} type={visible ? "text" : "password"} />
      <button
        type="button"
        className="password-toggle"
        aria-label={visible ? t("hide_password") : t("show_password")}
        aria-pressed={visible}
        onClick={() => setVisible((v) => !v)}
      >
        {visible ? <EyeOff size={16} /> : <Eye size={16} />}
      </button>
    </div>
  );
}
