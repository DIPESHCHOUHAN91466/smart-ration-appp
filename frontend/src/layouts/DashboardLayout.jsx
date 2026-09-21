import { useEffect, useState } from "react";
import { NavLink, Outlet, useNavigate } from "react-router-dom";
import {
  Bell, Globe2, Home, LogOut, Menu, Package, QrCode, Search, ClipboardList,
  Ticket, Users, Store, FileText, TrendingUp, ChevronDown,
} from "lucide-react";
import { useAuthStore } from "../store/authStore";
import { getNotifications } from "../services/notificationsService";

const NAV_BY_ROLE = {
  RuralUser: [
    ["/rural/dashboard", "Dashboard", Home],
    ["/rural/book", "Book Ration", Ticket],
    ["/rural/history", "Booking History", ClipboardList],
    ["/rural/notifications", "Notifications", Bell],
  ],
  ShopOwner: [
    ["/shop/dashboard", "Dashboard", Home],
    ["/shop/queue", "Today's Queue", Users],
    ["/shop/scanner", "QR Verification", QrCode],
    ["/shop/inventory", "Inventory", Package],
    ["/shop/notifications", "Notifications", Bell],
  ],
  GovernmentOfficial: [
    ["/gov/dashboard", "Dashboard", Home],
    ["/gov/statistics", "Statistics", TrendingUp],
    ["/gov/bookings", "Bookings", Ticket],
    ["/gov/shops", "Shops", Store],
    ["/gov/users", "Beneficiaries", Users],
    ["/gov/inventory", "Inventory", Package],
    ["/gov/reports", "Reports", FileText],
    ["/gov/notifications", "Notifications", Bell],
  ],
};
NAV_BY_ROLE.Admin = NAV_BY_ROLE.GovernmentOfficial;

const ROLE_LABEL = {
  RuralUser: "Rural User",
  ShopOwner: "Shop Owner",
  GovernmentOfficial: "Government Official",
  Admin: "Administrator",
};

export default function DashboardLayout() {
  const navigate = useNavigate();
  const user = useAuthStore((state) => state.user);
  const logout = useAuthStore((state) => state.logout);
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const [unreadCount, setUnreadCount] = useState(0);

  const nav = NAV_BY_ROLE[user?.role] || [];

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

  const handleLogout = async () => {
    await logout();
    navigate("/login", { replace: true });
  };

  return (
    <div className="app-shell">
      <aside className={`sidebar ${sidebarOpen ? "open" : "closed"}`}>
        <div className="brand">
          <div className="brand-mark">SR</div>
          <div>
            <strong>Smart Ration</strong>
            <span>HSD2C Distribution Platform</span>
          </div>
        </div>
        <div className="nav-section">MAIN MENU</div>
        {nav.map(([path, label, Icon]) => (
          <NavLink key={path} to={path} className={({ isActive }) => `nav-item ${isActive ? "active" : ""}`}>
            <Icon size={19} />
            <span>{label}</span>
          </NavLink>
        ))}
        <div className="sidebar-bottom">
          <div className="offline">
            <span className="online-dot"></span> System Online
          </div>
          <button className="nav-item" onClick={handleLogout}>
            <LogOut size={19} />
            <span>Sign out</span>
          </button>
        </div>
      </aside>

      <main className={`main ${sidebarOpen ? "with-sidebar" : ""}`}>
        <header className="topbar">
          <button className="icon-btn mobile-menu" onClick={() => setSidebarOpen((open) => !open)}>
            <Menu />
          </button>
          <div className="top-search">
            <Search size={17} />
            <input placeholder="Search dashboard..." disabled />
          </div>
          <div className="top-actions">
            <button className="icon-btn" onClick={() => navigate(`${basePathForRole(user?.role)}/notifications`)}>
              <Bell size={19} />
              {unreadCount > 0 && <i></i>}
            </button>
            <div className="language">
              <Globe2 size={16} />
              <select defaultValue="English">
                <option>English</option>
                <option>मराठी</option>
                <option>हिन्दी</option>
              </select>
            </div>
            <div className="profile">
              <div className="avatar">{(user?.fullName || "?")[0].toUpperCase()}</div>
              <div>
                <strong>{ROLE_LABEL[user?.role] || user?.role}</strong>
                <small>{user?.email}</small>
              </div>
              <ChevronDown size={15} />
            </div>
          </div>
        </header>

        <div className="page-content">
          <Outlet />
        </div>
      </main>
    </div>
  );
}

function basePathForRole(role) {
  if (role === "RuralUser") return "/rural";
  if (role === "ShopOwner") return "/shop";
  return "/gov";
}
