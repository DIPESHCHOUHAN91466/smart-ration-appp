import { useEffect, useRef, useState } from "react";
import { NavLink, Outlet, useNavigate } from "react-router-dom";
import {
  Bell, Globe2, Home, LogOut, Menu, Package, QrCode, Search, ClipboardList,
  Ticket, Users, Store, FileText, TrendingUp, ChevronDown, ShieldCheck, MapPin, History,
  Sparkles, Database, Settings as SettingsIcon, User as UserIcon,
} from "lucide-react";
import { useAuthStore } from "../store/authStore";
import { getNotifications } from "../services/notificationsService";
import { useTranslation } from "../i18n/useTranslation";
import { LANGUAGE_OPTIONS } from "../i18n/translations";
import { globalSearch } from "../services/searchService";
import { usePreferencesStore } from "../store/preferencesStore";
import BrandMark from "../components/BrandMark";
import GlobalQrScanner from "../components/qr/GlobalQrScanner";
import { useQrScannerStore } from "../store/qrScannerStore";

// Roles that can verify customer QR codes (POST /api/qr/scan is shop-scoped).
const QR_SCANNER_ROLES = ["ShopOwner"];

const NAV_BY_ROLE = {
  RuralUser: [
    ["/rural/dashboard", "dashboard", Home],
    ["/rural/book", "nav_book_ration", Ticket],
    ["/rural/history", "nav_booking_history", ClipboardList],
    ["/rural/verification", "nav_my_verification", ShieldCheck],
    ["/rural/notifications", "notifications", Bell],
    ["/settings", "nav_settings", SettingsIcon],
  ],
  ShopOwner: [
    ["/shop/dashboard", "dashboard", Home],
    ["/shop/queue", "nav_todays_queue", Users],
    ["/shop/scanner", "nav_qr_verification", QrCode],
    ["/shop/inventory", "nav_inventory", Package],
    ["/shop/notifications", "notifications", Bell],
    ["/settings", "nav_settings", SettingsIcon],
  ],
  GovernmentOfficial: [
    ["/gov/dashboard", "dashboard", Home],
    ["/gov/statistics", "nav_statistics", TrendingUp],
    ["/gov/bookings", "nav_bookings", Ticket],
    ["/gov/shops", "nav_shops", Store],
    ["/gov/users", "nav_beneficiaries", Users],
    ["/gov/inventory", "nav_inventory", Package],
    ["/gov/map", "nav_map", MapPin],
    ["/gov/ai", "nav_ai_center", Sparkles],
    ["/gov/synthetic-data", "nav_synthetic_data", Users],
    ["/gov/database", "nav_database_viewer", Database],
    ["/gov/audit", "nav_audit_log", History],
    ["/gov/reports", "nav_reports", FileText],
    ["/gov/notifications", "notifications", Bell],
    ["/settings", "nav_settings", SettingsIcon],
  ],
};
NAV_BY_ROLE.Admin = NAV_BY_ROLE.GovernmentOfficial;

const ROLE_LABEL_KEY = {
  RuralUser: "role_rural_user",
  ShopOwner: "role_shop_owner",
  GovernmentOfficial: "role_government_official",
  Admin: "role_admin",
};

export default function DashboardLayout() {
  const navigate = useNavigate();
  const user = useAuthStore((state) => state.user);
  const logout = useAuthStore((state) => state.logout);
  const { t, language, setLanguage } = useTranslation();

  const density = usePreferencesStore((s) => s.density);
  const fontSize = usePreferencesStore((s) => s.fontSize);
  const highContrast = usePreferencesStore((s) => s.highContrast);
  const reduceAnimations = usePreferencesStore((s) => s.reduceAnimations);
  const sidebarPref = usePreferencesStore((s) => s.sidebar);
  const setPreference = usePreferencesStore((s) => s.setPreference);
  const showSearch = usePreferencesStore((s) => s.showSearch);
  const showNotifications = usePreferencesStore((s) => s.showNotifications);
  const showProfile = usePreferencesStore((s) => s.showProfile);
  const showStatus = usePreferencesStore((s) => s.showStatus);

  // On phone-width screens the sidebar is a drawer and must start closed
  // regardless of the desktop "expanded/collapsed" preference — otherwise
  // it (and the content's margin-left reserved for it) would cover or push
  // around the page on a small screen before the user ever touches it.
  const [sidebarOpen, setSidebarOpen] = useState(
    () => typeof window !== "undefined" && window.innerWidth > 760 && sidebarPref !== "collapsed",
  );
  const [unreadCount, setUnreadCount] = useState(0);
  const [profileMenuOpen, setProfileMenuOpen] = useState(false);
  const profileRef = useRef(null);

  const [searchTerm, setSearchTerm] = useState("");
  const [searchResults, setSearchResults] = useState([]);
  const [searchOpen, setSearchOpen] = useState(false);
  const [searching, setSearching] = useState(false);
  const searchBoxRef = useRef(null);
  const debounceRef = useRef(null);

  const nav = NAV_BY_ROLE[user?.role] || [];
  const canScanQr = QR_SCANNER_ROLES.includes(user?.role);
  const openQrScanner = useQrScannerStore((s) => s.open);

  const toggleSidebar = () => {
    setSidebarOpen((open) => {
      const next = !open;
      setPreference("sidebar", next ? "expanded" : "collapsed");
      return next;
    });
  };

  useEffect(() => {
    let cancelled = false;
    getNotifications()
      .then((items) => {
        if (!cancelled) setUnreadCount((items || []).filter((n) => !n.isRead).length);
      })
      .catch(() => {});
    return () => {
      cancelled = true;
    };
  }, []);

  useEffect(() => {
    function onClickOutside(e) {
      if (searchBoxRef.current && !searchBoxRef.current.contains(e.target)) {
        setSearchOpen(false);
      }
      if (profileRef.current && !profileRef.current.contains(e.target)) {
        setProfileMenuOpen(false);
      }
    }
    document.addEventListener("mousedown", onClickOutside);
    return () => document.removeEventListener("mousedown", onClickOutside);
  }, []);

  const onSearchChange = (value) => {
    setSearchTerm(value);
    clearTimeout(debounceRef.current);
    if (value.trim().length < 2) {
      setSearchResults([]);
      setSearchOpen(false);
      return;
    }
    debounceRef.current = setTimeout(async () => {
      setSearching(true);
      try {
        const results = await globalSearch(value.trim());
        setSearchResults(results || []);
        setSearchOpen(true);
      } catch {
        setSearchResults([]);
      } finally {
        setSearching(false);
      }
    }, 300);
  };

  const goToResult = (result) => {
    setSearchOpen(false);
    setSearchTerm("");
    navigate(result.path);
  };

  const handleLogout = async () => {
    await logout();
    navigate("/login", { replace: true });
  };

  const shellClassName = [
    "app-shell",
    `density-${density}`,
    `font-${fontSize}`,
    highContrast ? "high-contrast" : "",
    reduceAnimations ? "reduce-motion" : "",
  ]
    .filter(Boolean)
    .join(" ");

  return (
    <div className={shellClassName}>
      <aside className={`sidebar ${sidebarOpen ? "open" : "closed"}`}>
        <div className="brand">
          <BrandMark />
          <div>
            <strong>{t("brand_name")}</strong>
            <span>{t("app_subtitle")}</span>
          </div>
        </div>
        <div className="nav-section">{t("nav_section_main")}</div>
        {nav.map(([path, labelKey, Icon]) => (
          <NavLink key={path} to={path} className={({ isActive }) => `nav-item ${isActive ? "active" : ""}`}>
            <Icon size={19} />
            <span>{t(labelKey)}</span>
          </NavLink>
        ))}
        <div className="sidebar-bottom">
          {showStatus && (
            <div className="offline">
              <span className="online-dot"></span> {t("system_online")}
            </div>
          )}
          <button className="nav-item" onClick={handleLogout}>
            <LogOut size={19} />
            <span>{t("sign_out")}</span>
          </button>
          <div className="offline powered-by">{t("powered_by")}</div>
        </div>
      </aside>

      <main className={`main ${sidebarOpen ? "with-sidebar" : ""}`}>
        <header className="topbar">
          <button className="icon-btn mobile-menu" onClick={toggleSidebar}>
            <Menu />
          </button>
          {showSearch && (
            <div className="top-search" ref={searchBoxRef} style={{ position: "relative" }}>
              <Search size={17} />
              <input
                placeholder={t("search_placeholder")}
                value={searchTerm}
                onChange={(e) => onSearchChange(e.target.value)}
                onFocus={() => searchResults.length > 0 && setSearchOpen(true)}
              />
              {searchOpen && (
                <div className="search-dropdown">
                  {searching && <div className="search-dropdown-item muted">{t("loading")}</div>}
                  {!searching && searchResults.length === 0 && (
                    <div className="search-dropdown-item muted">{t("no_results")}</div>
                  )}
                  {!searching &&
                    searchResults.map((r, idx) => (
                      <button key={`${r.type}-${idx}`} type="button" className="search-dropdown-item" onClick={() => goToResult(r)}>
                        <span className="search-result-type">{r.type}</span>
                        <span>
                          <b>{r.title}</b>
                          <small>{r.subtitle}</small>
                        </span>
                      </button>
                    ))}
                </div>
              )}
            </div>
          )}
          <div className="top-actions">
            {canScanQr && (
              <button type="button" className="primary-btn scan-qr-btn" onClick={openQrScanner} aria-label={t("open_qr_scanner")}>
                <QrCode size={17} />
                <span>{t("scan_qr")}</span>
              </button>
            )}
            {showNotifications && (
              <button className="icon-btn" onClick={() => navigate(`${basePathForRole(user?.role)}/notifications`)}>
                <Bell size={19} />
                {unreadCount > 0 && <i></i>}
              </button>
            )}
            <div className="language">
              <Globe2 size={16} />
              <select value={language} onChange={(e) => setLanguage(e.target.value)}>
                {LANGUAGE_OPTIONS.map((opt) => (
                  <option key={opt.code} value={opt.code}>
                    {opt.label}
                  </option>
                ))}
              </select>
            </div>
            {showProfile && (
              <div className="profile" ref={profileRef} style={{ position: "relative", cursor: "pointer" }} onClick={() => setProfileMenuOpen((v) => !v)}>
                <div className="avatar">{(user?.fullName || "?")[0].toUpperCase()}</div>
                <div>
                  <strong>{t(ROLE_LABEL_KEY[user?.role]) || user?.role}</strong>
                  <small>{user?.email}</small>
                </div>
                <ChevronDown size={15} />
                {profileMenuOpen && (
                  <div className="search-dropdown" style={{ top: "calc(100% + 8px)", right: 0, left: "auto", minWidth: 200 }}>
                    {user?.role === "RuralUser" && (
                      <button type="button" className="search-dropdown-item" onClick={() => navigate("/rural/verification")}>
                        <UserIcon size={15} />
                        <span>{t("nav_my_verification")}</span>
                      </button>
                    )}
                    <button type="button" className="search-dropdown-item" onClick={() => navigate("/settings")}>
                      <SettingsIcon size={15} />
                      <span>{t("nav_settings")}</span>
                    </button>
                    <button type="button" className="search-dropdown-item" onClick={handleLogout}>
                      <LogOut size={15} />
                      <span>{t("sign_out")}</span>
                    </button>
                  </div>
                )}
              </div>
            )}
          </div>
        </header>

        <div className="page-content">
          <Outlet />
        </div>
      </main>

      {canScanQr && (
        <>
          <button type="button" className="scan-qr-fab" onClick={openQrScanner} aria-label={t("open_qr_scanner")}>
            <QrCode size={24} />
          </button>
          <GlobalQrScanner />
        </>
      )}
    </div>
  );
}

function basePathForRole(role) {
  if (role === "RuralUser") return "/rural";
  if (role === "ShopOwner") return "/shop";
  return "/gov";
}
