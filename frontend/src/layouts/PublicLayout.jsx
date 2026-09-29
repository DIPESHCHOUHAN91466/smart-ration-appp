import { useEffect, useState } from "react";
import { Link, NavLink, Outlet, useLocation } from "react-router-dom";
import { ArrowRight, Menu, X } from "lucide-react";
import BrandMark, { CompanyMark } from "../components/BrandMark";
import LanguageSwitcher from "../components/LanguageSwitcher";
import { useTranslation } from "../i18n/useTranslation";
import "../pages/landing/public.css";

// Header + footer for the pages anyone can open without logging in (landing, Public Help).
export default function PublicLayout() {
  const { t, language } = useTranslation();
  const [menuOpen, setMenuOpen] = useState(false);
  const location = useLocation();

  useEffect(() => setMenuOpen(false), [location.pathname, location.search]);
  useEffect(() => {
    document.documentElement.lang = language;
  }, [language]);

  const nav = (
    <>
      <NavLink to="/" end className="pub-nav-link">{t("nav_home")}</NavLink>
      <NavLink to="/help" className="pub-nav-link">{t("nav_public_help")}</NavLink>
      <NavLink to="/login" className="pub-nav-link">{t("nav_login")}</NavLink>
    </>
  );

  return (
    <div className="pub-shell">
      <a href="#main" className="skip-link">{t("skip_to_content")}</a>
      <header className="pub-header">
        <div className="pub-header-inner">
          <Link to="/" className="pub-brand" aria-label={`${t("app_name")} — ${t("nav_home")}`}>
            <BrandMark variant="header" />
          </Link>
          <nav className="pub-nav" aria-label="Main">{nav}</nav>
          <div className="pub-header-actions">
            <CompanyMark variant="header" />
            <LanguageSwitcher />
            <Link to="/register" className="pub-cta">{t("nav_get_started")} <ArrowRight size={16} aria-hidden="true" /></Link>
            <button
              type="button"
              className="pub-menu-btn"
              aria-expanded={menuOpen}
              aria-controls="pub-mobile-nav"
              aria-label={menuOpen ? t("nav_close_menu") : t("nav_menu")}
              onClick={() => setMenuOpen((o) => !o)}
            >
              {menuOpen ? <X size={20} /> : <Menu size={20} />}
            </button>
          </div>
        </div>
        {menuOpen && (
          <nav id="pub-mobile-nav" className="pub-mobile-nav" aria-label="Mobile">
            {nav}
            <Link to="/register" className="pub-cta">{t("nav_get_started")}</Link>
          </nav>
        )}
      </header>

      <main id="main" tabIndex={-1}>
        <Outlet />
      </main>

      <footer className="pub-footer">
        <div className="pub-footer-inner">
          <div>
            <div className="pub-brand footer">
              <CompanyMark variant="light" />
              <span className="pub-brand-text">
                <strong>{t("app_name")} HSD2C</strong>
                <small>{t("powered_by")}</small>
              </span>
            </div>
            <p className="pub-demo-note">{t("land_demo_notice")}</p>
          </div>
          <nav aria-label={t("footer_links")} className="pub-footer-links">
            <Link to="/help">{t("nav_public_help")}</Link>
            <Link to="/login">{t("nav_login")}</Link>
            <Link to="/register">{t("nav_get_started")}</Link>
          </nav>
        </div>
        <p className="pub-copy">© {new Date().getFullYear()} HSD2C · {t("footer_rights")}</p>
      </footer>
    </div>
  );
}
