import { lazy, Suspense } from "react";
import { BrowserRouter, Navigate, Route, Routes } from "react-router-dom";
import { ToastProvider } from "./state/ToastProvider";
import { useAuthStore } from "./state/authStore";
import { homePathForRole } from "./features/auth/roleHome";
import ProtectedRoute from "./features/auth/ProtectedRoute";
import DashboardLayout from "./layouts/DashboardLayout";
import { LoadingState } from "./components/EmptyState";
import PublicLayout from "./layouts/PublicLayout";
import ChatbotWidget from "./components/chatbot/ChatbotWidget";
import { SHOW_STATUS_PAGE as SHOW_STATUS } from "./config/env";

// Public pages (no login): loaded on demand so the dashboards bundle stays the same size.
const LandingPage = lazy(() => import("./pages/landing/LandingPage"));
const PublicHelpPage = lazy(() => import("./pages/public-help/PublicHelpPage"));
const LegalPage = lazy(() => import("./pages/legal/LegalPage"));
// Developer status page: only in development builds (or VITE_SHOW_STATUS=true) — config/env.js.
const StatusPage = lazy(() => import("./pages/status/StatusPage"));

import Login from "./pages/Login";
import Register from "./pages/Register";
import NotFound from "./pages/NotFound";
import NotificationsPage from "./pages/shared/NotificationsPage";
import BeneficiaryProfile from "./pages/shared/BeneficiaryProfile";
import Settings from "./pages/shared/Settings";
import PublicProfile from "./pages/PublicProfile";

import RuralDashboard from "./pages/rural/RuralDashboard";
import BookRation from "./pages/rural/BookRation";
import MyToken from "./pages/rural/MyToken";
import BookingHistory from "./pages/rural/BookingHistory";
import MyVerification from "./pages/rural/MyVerification";

import ShopDashboard from "./pages/shop/ShopDashboard";
import Queue from "./pages/shop/Queue";
import ShopInventory from "./pages/shop/Inventory";

// Lazy-loaded: pulls in the QR camera/decoder code, only needed on this one route.
const Scanner = lazy(() => import("./pages/shop/Scanner"));

import GovernmentDashboard from "./pages/government/GovernmentDashboard";
import GovUsers from "./pages/government/Users";
import GovShops from "./pages/government/Shops";
import GovBookings from "./pages/government/Bookings";
import GovInventory from "./pages/government/Inventory";
import Statistics from "./pages/government/Statistics";
import Reports from "./pages/government/Reports";
import Audit from "./pages/government/Audit";
import GovComplaints from "./pages/government/Complaints";
import RuralComplaints from "./pages/rural/Complaints";
import AIIntelligenceCenter from "./pages/government/AIIntelligenceCenter";
import SyntheticData from "./pages/government/SyntheticData";
import AdminDatabase from "./pages/government/AdminDatabase";

// Lazy-loaded: pulls in Leaflet, only needed on the map route.
const GovernmentMap = lazy(() => import("./pages/government/Map"));

import "./styles/global.css";

// Visitors see the public landing page; signed-in users go straight to their dashboard.
function Home() {
  const isAuthenticated = useAuthStore((state) => state.isAuthenticated);
  const user = useAuthStore((state) => state.user);

  if (isAuthenticated && user) {
    return <Navigate to={homePathForRole(user.role)} replace />;
  }
  return <LandingPage />;
}

const publicFallback = <LoadingState text="" />;

export default function App() {
  return (
    <ToastProvider>
      <BrowserRouter>
        <Routes>
          <Route path="/login" element={<Login />} />
          <Route path="/register" element={<Register />} />
          <Route path="/profile/:publicReference" element={<PublicProfile />} />
          <Route element={<PublicLayout />}>
            <Route path="/" element={<Suspense fallback={publicFallback}><Home /></Suspense>} />
            <Route path="/help" element={<Suspense fallback={publicFallback}><PublicHelpPage /></Suspense>} />
            <Route path="/privacy" element={<Suspense fallback={publicFallback}><LegalPage doc="privacy" /></Suspense>} />
            <Route path="/terms" element={<Suspense fallback={publicFallback}><LegalPage doc="terms" /></Suspense>} />
            <Route path="/accessibility" element={<Suspense fallback={publicFallback}><LegalPage doc="accessibility" /></Suspense>} />
          </Route>

          <Route element={<ProtectedRoute roles={["RuralUser", "ShopOwner", "GovernmentOfficial", "Admin"]} />}>
            <Route element={<DashboardLayout />}>
              <Route path="/beneficiary/:id" element={<BeneficiaryProfile />} />
              <Route path="/settings" element={<Settings />} />
            </Route>
          </Route>

          <Route element={<ProtectedRoute roles={["RuralUser"]} />}>
            <Route element={<DashboardLayout />}>
              <Route path="/rural/dashboard" element={<RuralDashboard />} />
              <Route path="/rural/book" element={<BookRation />} />
              <Route path="/rural/token/:id" element={<MyToken />} />
              <Route path="/rural/history" element={<BookingHistory />} />
              <Route path="/rural/verification" element={<MyVerification />} />
              <Route path="/rural/complaints" element={<RuralComplaints />} />
              <Route path="/rural/notifications" element={<NotificationsPage />} />
            </Route>
          </Route>

          <Route element={<ProtectedRoute roles={["ShopOwner"]} />}>
            <Route element={<DashboardLayout />}>
              <Route path="/shop/dashboard" element={<ShopDashboard />} />
              <Route path="/shop/queue" element={<Queue />} />
              <Route
                path="/shop/scanner"
                element={
                  <Suspense fallback={<LoadingState text="Loading scanner..." />}>
                    <Scanner />
                  </Suspense>
                }
              />
              <Route path="/shop/inventory" element={<ShopInventory />} />
              <Route path="/shop/notifications" element={<NotificationsPage />} />
            </Route>
          </Route>

          <Route element={<ProtectedRoute roles={["GovernmentOfficial", "Admin"]} />}>
            <Route element={<DashboardLayout />}>
              <Route path="/gov/dashboard" element={<GovernmentDashboard />} />
              <Route path="/gov/users" element={<GovUsers />} />
              <Route path="/gov/shops" element={<GovShops />} />
              <Route path="/gov/bookings" element={<GovBookings />} />
              <Route path="/gov/inventory" element={<GovInventory />} />
              <Route path="/gov/statistics" element={<Statistics />} />
              <Route path="/gov/reports" element={<Reports />} />
              <Route path="/gov/audit" element={<Audit />} />
              <Route path="/gov/complaints" element={<GovComplaints />} />
              <Route path="/gov/ai" element={<AIIntelligenceCenter />} />
              <Route path="/gov/synthetic-data" element={<SyntheticData />} />
              <Route path="/gov/database" element={<AdminDatabase />} />
              <Route
                path="/gov/map"
                element={
                  <Suspense fallback={<LoadingState text="Loading map..." />}>
                    <GovernmentMap />
                  </Suspense>
                }
              />
              <Route path="/gov/notifications" element={<NotificationsPage />} />
            </Route>
          </Route>

          {SHOW_STATUS && <Route path="/status" element={<Suspense fallback={publicFallback}><StatusPage /></Suspense>} />}

          <Route path="*" element={<NotFound />} />
        </Routes>
        <ChatbotWidget />
      </BrowserRouter>
    </ToastProvider>
  );
}
