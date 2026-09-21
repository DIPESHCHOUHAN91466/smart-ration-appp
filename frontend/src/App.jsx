import { lazy, Suspense } from "react";
import { BrowserRouter, Navigate, Route, Routes } from "react-router-dom";
import { ToastProvider } from "./context/ToastContext";
import { useAuthStore } from "./store/authStore";
import { homePathForRole } from "./routes/roleHome";
import ProtectedRoute from "./routes/ProtectedRoute";
import DashboardLayout from "./layouts/DashboardLayout";
import { LoadingState } from "./components/EmptyState";

import Login from "./pages/Login";
import Register from "./pages/Register";
import NotFound from "./pages/NotFound";
import NotificationsPage from "./pages/shared/NotificationsPage";

import RuralDashboard from "./pages/rural/RuralDashboard";
import BookRation from "./pages/rural/BookRation";
import MyToken from "./pages/rural/MyToken";
import BookingHistory from "./pages/rural/BookingHistory";

import ShopDashboard from "./pages/shop/ShopDashboard";
import Queue from "./pages/shop/Queue";
import ShopInventory from "./pages/shop/Inventory";

// Lazy-loaded: pulls in the (large) html5-qrcode camera library, only needed on this one route.
const Scanner = lazy(() => import("./pages/shop/Scanner"));

import GovernmentDashboard from "./pages/government/GovernmentDashboard";
import GovUsers from "./pages/government/Users";
import GovShops from "./pages/government/Shops";
import GovBookings from "./pages/government/Bookings";
import GovInventory from "./pages/government/Inventory";
import Statistics from "./pages/government/Statistics";
import Reports from "./pages/government/Reports";

import "./styles.css";

function HomeRedirect() {
  const isAuthenticated = useAuthStore((state) => state.isAuthenticated);
  const user = useAuthStore((state) => state.user);

  if (!isAuthenticated || !user) {
    return <Navigate to="/login" replace />;
  }
  return <Navigate to={homePathForRole(user.role)} replace />;
}

export default function App() {
  return (
    <ToastProvider>
      <BrowserRouter>
        <Routes>
          <Route path="/login" element={<Login />} />
          <Route path="/register" element={<Register />} />
          <Route path="/" element={<HomeRedirect />} />

          <Route element={<ProtectedRoute roles={["RuralUser"]} />}>
            <Route element={<DashboardLayout />}>
              <Route path="/rural/dashboard" element={<RuralDashboard />} />
              <Route path="/rural/book" element={<BookRation />} />
              <Route path="/rural/token/:id" element={<MyToken />} />
              <Route path="/rural/history" element={<BookingHistory />} />
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
              <Route path="/gov/notifications" element={<NotificationsPage />} />
            </Route>
          </Route>

          <Route path="*" element={<NotFound />} />
        </Routes>
      </BrowserRouter>
    </ToastProvider>
  );
}
