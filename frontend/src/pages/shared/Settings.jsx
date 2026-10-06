import { useRef, useState } from "react";
import { Accessibility, Database, Globe2, Palette, ShieldCheck, SlidersHorizontal, User } from "lucide-react";
import PageHeader from "../../components/PageHeader";
import ToggleSetting from "../../components/ToggleSetting";
import { useAuthStore } from "../../state/authStore";
import { useTranslation } from "../../i18n/useTranslation";
import { LANGUAGE_OPTIONS } from "../../i18n/translations";
import { useLanguageStore } from "../../i18n/useTranslation";
import { usePreferencesStore } from "../../state/preferencesStore";
import { useToast } from "../../state/toast";
import ProfileSection from "./ProfileSection";
import PasswordSection from "./PasswordSection";
import MfaSection from "./MfaSection";
import DataExportSection from "./DataExportSection";

const ROLE_LABEL_KEY = {
  RuralUser: "role_rural_user",
  ShopOwner: "role_shop_owner",
  GovernmentOfficial: "role_government_official",
  Admin: "role_admin",
};

export default function Settings() {
  const { t, language } = useTranslation();
  const setLanguage = useLanguageStore((s) => s.setLanguage);
  const user = useAuthStore((s) => s.user);
  const notify = useToast();
  const prefs = usePreferencesStore();
  const fileInputRef = useRef(null);

  const [pendingLanguage, setPendingLanguage] = useState(language);
  const [confirmReset, setConfirmReset] = useState(false);

  const applyLanguage = () => {
    setLanguage(pendingLanguage);
    notify(t("settings_saved"));
  };

  const downloadBackup = () => {
    const payload = {
      language,
      density: prefs.density,
      sidebar: prefs.sidebar,
      fontSize: prefs.fontSize,
      highContrast: prefs.highContrast,
      reduceAnimations: prefs.reduceAnimations,
      showSearch: prefs.showSearch,
      showNotifications: prefs.showNotifications,
      showProfile: prefs.showProfile,
      showBreadcrumbs: prefs.showBreadcrumbs,
      showStatus: prefs.showStatus,
      showAvailability: prefs.showAvailability,
      showHelp: prefs.showHelp,
    };
    const blob = new Blob([JSON.stringify(payload, null, 2)], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = "smart-ration-preferences.json";
    a.click();
    URL.revokeObjectURL(url);
    notify(t("settings_backup_success"));
  };

  const restoreBackup = (e) => {
    const file = e.target.files?.[0];
    e.target.value = "";
    if (!file) return;

    const reader = new FileReader();
    reader.onload = () => {
      try {
        const data = JSON.parse(reader.result);
        const validLanguage = LANGUAGE_OPTIONS.some((o) => o.code === data.language);
        const validEnum = (value, allowed) => allowed.includes(value);

        if (typeof data !== "object" || data === null) throw new Error("invalid");

        if (validLanguage) setLanguage(data.language);

        const next = {};
        if (validEnum(data.density, ["compact", "comfortable", "full"])) next.density = data.density;
        if (validEnum(data.sidebar, ["expanded", "collapsed"])) next.sidebar = data.sidebar;
        if (validEnum(data.fontSize, ["small", "medium", "large"])) next.fontSize = data.fontSize;
        for (const key of ["highContrast", "reduceAnimations", "showSearch", "showNotifications", "showProfile", "showBreadcrumbs", "showStatus", "showAvailability", "showHelp"]) {
          if (typeof data[key] === "boolean") next[key] = data[key];
        }

        if (Object.keys(next).length === 0 && !validLanguage) {
          throw new Error("invalid");
        }

        prefs.setMany(next);
        notify(t("settings_restore_success"));
      } catch {
        notify(t("settings_restore_invalid"), "error");
      }
    };
    reader.readAsText(file);
  };

  const resetPreferences = () => {
    prefs.resetAll();
    setLanguage("en");
    setPendingLanguage("en");
    setConfirmReset(false);
    notify(t("settings_reset_success"));
  };

  return (
    <>
      <PageHeader title={t("settings_title")} subtitle={t("settings_subtitle")} />

      <div className="settings-grid">
        <ProfileSection />
        <PasswordSection />
        {user && user.role !== "RuralUser" && <MfaSection />}
        <DataExportSection />

        {/* Language */}
        <section className="panel">
          <div className="settings-section-title">
            <Globe2 size={19} />
            <h2>{t("settings_section_language")}</h2>
          </div>
          <div className="option-row">
            {LANGUAGE_OPTIONS.map((opt) => (
              <button key={opt.code} className={pendingLanguage === opt.code ? "selected" : ""} onClick={() => setPendingLanguage(opt.code)}>
                {opt.label}
              </button>
            ))}
          </div>
          <button className="primary-btn" onClick={applyLanguage} disabled={pendingLanguage === language}>
            {t("settings_apply_language")}
          </button>
        </section>

        {/* Appearance */}
        <section className="panel">
          <div className="settings-section-title">
            <Palette size={19} />
            <h2>{t("settings_section_appearance")}</h2>
          </div>

          <span className="settings-field-label">{t("settings_display_density")}</span>
          <div className="option-row">
            {[
              ["compact", "settings_compact_mode"],
              ["comfortable", "settings_comfortable_mode"],
              ["full", "settings_full_display_mode"],
            ].map(([value, key]) => (
              <button key={value} className={prefs.density === value ? "selected" : ""} onClick={() => prefs.setPreference("density", value)}>
                {t(key)}
              </button>
            ))}
          </div>

          <span className="settings-field-label">{t("settings_sidebar_mode")}</span>
          <div className="option-row">
            {[
              ["expanded", "settings_sidebar_expanded"],
              ["collapsed", "settings_sidebar_collapsed"],
            ].map(([value, key]) => (
              <button key={value} className={prefs.sidebar === value ? "selected" : ""} onClick={() => prefs.setPreference("sidebar", value)}>
                {t(key)}
              </button>
            ))}
          </div>

          <span className="settings-field-label">{t("settings_font_size")}</span>
          <div className="option-row">
            {[
              ["small", "settings_font_small"],
              ["medium", "settings_font_medium"],
              ["large", "settings_font_large"],
            ].map(([value, key]) => (
              <button key={value} className={prefs.fontSize === value ? "selected" : ""} onClick={() => prefs.setPreference("fontSize", value)}>
                {t(key)}
              </button>
            ))}
          </div>

          <ToggleSetting label={t("settings_reduce_animations")} checked={prefs.reduceAnimations} onChange={(v) => prefs.setPreference("reduceAnimations", v)} />
          <ToggleSetting label={t("settings_high_contrast")} checked={prefs.highContrast} onChange={(v) => prefs.setPreference("highContrast", v)} />
        </section>

        {/* Display */}
        <section className="panel">
          <div className="settings-section-title">
            <SlidersHorizontal size={19} />
            <h2>{t("settings_section_display")}</h2>
          </div>
          <ToggleSetting label={t("settings_show_search")} checked={prefs.showSearch} onChange={(v) => prefs.setPreference("showSearch", v)} />
          <ToggleSetting label={t("settings_show_notifications")} checked={prefs.showNotifications} onChange={(v) => prefs.setPreference("showNotifications", v)} />
          <ToggleSetting label={t("settings_show_profile")} checked={prefs.showProfile} onChange={(v) => prefs.setPreference("showProfile", v)} />
          <ToggleSetting label={t("settings_show_breadcrumbs")} checked={prefs.showBreadcrumbs} onChange={(v) => prefs.setPreference("showBreadcrumbs", v)} />
          <ToggleSetting label={t("settings_show_status")} checked={prefs.showStatus} onChange={(v) => prefs.setPreference("showStatus", v)} />
          <ToggleSetting label={t("settings_show_availability")} checked={prefs.showAvailability} onChange={(v) => prefs.setPreference("showAvailability", v)} />
          <ToggleSetting label={t("settings_show_help")} checked={prefs.showHelp} onChange={(v) => prefs.setPreference("showHelp", v)} />
        </section>

        {/* Accessibility (mirrors the appearance controls that matter for accessibility) */}
        <section className="panel">
          <div className="settings-section-title">
            <Accessibility size={19} />
            <h2>{t("settings_section_accessibility")}</h2>
          </div>
          <ToggleSetting label={t("settings_high_contrast")} checked={prefs.highContrast} onChange={(v) => prefs.setPreference("highContrast", v)} />
          <ToggleSetting label={t("settings_reduce_animations")} checked={prefs.reduceAnimations} onChange={(v) => prefs.setPreference("reduceAnimations", v)} />
          <span className="settings-field-label" style={{ marginTop: 14 }}>{t("settings_font_size")}</span>
          <div className="option-row">
            {[
              ["small", "settings_font_small"],
              ["medium", "settings_font_medium"],
              ["large", "settings_font_large"],
            ].map(([value, key]) => (
              <button key={value} className={prefs.fontSize === value ? "selected" : ""} onClick={() => prefs.setPreference("fontSize", value)}>
                {t(key)}
              </button>
            ))}
          </div>
        </section>

        {/* User Role */}
        <section className="panel">
          <div className="settings-section-title">
            <User size={19} />
            <h2>{t("settings_section_role")}</h2>
          </div>
          <span className="settings-field-label">{t("settings_current_role")}</span>
          <p style={{ fontSize: 14, fontWeight: 700, marginTop: 0 }}>{t(ROLE_LABEL_KEY[user?.role]) || user?.role}</p>
          <div className="info-callout">
            <ShieldCheck size={16} />
            <p>{t("settings_role_note")}</p>
          </div>
        </section>

        {/* Preferences & Data */}
        <section className="panel">
          <div className="settings-section-title">
            <Database size={19} />
            <h2>{t("settings_section_preferences")}</h2>
          </div>

          <div className="toggle-row" style={{ alignItems: "flex-start" }}>
            <div>
              <b>{t("settings_backup")}</b>
              <small>{t("settings_backup_desc")}</small>
            </div>
            <button className="secondary-btn" onClick={downloadBackup}>
              {t("settings_backup")}
            </button>
          </div>

          <div className="toggle-row" style={{ alignItems: "flex-start" }}>
            <div>
              <b>{t("settings_restore")}</b>
              <small>{t("settings_restore_desc")}</small>
            </div>
            <button className="secondary-btn" onClick={() => fileInputRef.current?.click()}>
              {t("settings_choose_file")}
            </button>
            <input ref={fileInputRef} type="file" accept="application/json" style={{ display: "none" }} onChange={restoreBackup} />
          </div>

          <div className="toggle-row">
            <div>
              <b>{t("settings_reset")}</b>
            </div>
            <button className="secondary-btn" style={{ color: "var(--red)" }} onClick={() => setConfirmReset(true)}>
              {t("settings_reset")}
            </button>
          </div>
        </section>
      </div>

      {confirmReset && (
        <div className="modal-backdrop" onClick={() => setConfirmReset(false)}>
          <div className="modal" onClick={(e) => e.stopPropagation()}>
            <h2>{t("settings_reset_confirm_title")}</h2>
            <p className="muted">{t("settings_reset_confirm_message")}</p>
            <div className="actions" style={{ justifyContent: "center", marginTop: 20 }}>
              <button className="secondary-btn" onClick={() => setConfirmReset(false)}>
                {t("cancel")}
              </button>
              <button className="primary-btn" style={{ background: "var(--red)" }} onClick={resetPreferences}>
                {t("settings_reset")}
              </button>
            </div>
          </div>
        </div>
      )}
    </>
  );
}

