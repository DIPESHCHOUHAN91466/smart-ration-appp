import { useEffect, useMemo, useState } from "react";
import { MapContainer, TileLayer, Marker, Popup, CircleMarker } from "react-leaflet";
import "leaflet/dist/leaflet.css";
import L from "leaflet";
import { AlertTriangle, Package, Store, Users } from "lucide-react";
import PageHeader from "../../components/PageHeader";
import { ErrorState, LoadingState } from "../../components/EmptyState";
import { getShopMarkers, getMapAnalytics } from "../../services/mapService";

const STATUS_COLOR = { Normal: "#16a34a", Low: "#f59e0b", Critical: "#dc2626" };

function shopIcon(status) {
  const color = STATUS_COLOR[status] || "#2563eb";
  return L.divIcon({
    className: "",
    html: `<div style="width:18px;height:18px;border-radius:50%;background:${color};border:3px solid white;box-shadow:0 2px 6px rgba(0,0,0,.4)"></div>`,
    iconSize: [18, 18],
    iconAnchor: [9, 9],
  });
}

const HEATMAP_OPTIONS = [
  { value: "none", label: "No overlay" },
  { value: "BeneficiaryDensityHeatmap", label: "Beneficiary Density" },
  { value: "DemandHeatmap", label: "Booking Demand" },
  { value: "CollectionActivityHeatmap", label: "Collection Activity" },
  { value: "InventoryShortageHeatmap", label: "Inventory Shortage" },
];

export default function GovernmentMap() {
  const [markers, setMarkers] = useState(null);
  const [analytics, setAnalytics] = useState(null);
  const [error, setError] = useState("");
  const [filters, setFilters] = useState({ state: "", district: "", taluka: "", village: "", inventoryStatus: "" });
  const [heatmapLayer, setHeatmapLayer] = useState("none");
  const [selectedShop, setSelectedShop] = useState(null);

  const load = () => {
    setError("");
    Promise.all([getShopMarkers(filters), getMapAnalytics()])
      .then(([m, a]) => {
        setMarkers(m);
        setAnalytics(a);
      })
      .catch((err) => setError(err.message));
  };

  // eslint-disable-next-line react-hooks/exhaustive-deps
  useEffect(load, [filters.state, filters.district, filters.taluka, filters.village, filters.inventoryStatus]);

  const filterOptions = useMemo(() => {
    if (!markers) return { states: [], districts: [], talukas: [], villages: [] };
    return {
      states: [...new Set(markers.map((m) => m.state))],
      districts: [...new Set(markers.map((m) => m.district))],
      talukas: [...new Set(markers.map((m) => m.taluka).filter(Boolean))],
      villages: [...new Set(markers.map((m) => m.village).filter(Boolean))],
    };
  }, [markers]);

  const heatmapPoints = analytics && heatmapLayer !== "none" ? analytics[heatmapLayer.charAt(0).toLowerCase() + heatmapLayer.slice(1)] : [];

  return (
    <>
      <PageHeader title="Smart Ration Map" subtitle="Live shop, inventory and verification overview across your jurisdiction." />

      <div className="demo-box" style={{ marginBottom: 18 }}>
        <b>DEMO MAP DATA</b> — shop coordinates are synthetic demo locations. Heatmap layers are weighted by real
        (seeded) counts at the shop level only — this system never plots individual beneficiary addresses.
      </div>

      {error && <ErrorState text={error} onRetry={load} />}

      {analytics && (
        <div className="stats-grid">
          <div className="stat-card blue">
            <div className="stat-top">
              <span>Total / Active Shops</span>
              <Store size={19} />
            </div>
            <strong>
              {analytics.totalShops} / {analytics.activeShops}
            </strong>
          </div>
          <div className="stat-card orange">
            <div className="stat-top">
              <span>Low / Critical Inventory</span>
              <AlertTriangle size={19} />
            </div>
            <strong>
              {analytics.lowInventoryShops} / {analytics.criticalInventoryShops}
            </strong>
          </div>
          <div className="stat-card cyan">
            <div className="stat-top">
              <span>Beneficiaries / Eligible</span>
              <Users size={19} />
            </div>
            <strong>
              {analytics.totalBeneficiaries} / {analytics.eligibleBeneficiaries}
            </strong>
          </div>
          <div className="stat-card green">
            <div className="stat-top">
              <span>Today's Collections / Pending</span>
              <Package size={19} />
            </div>
            <strong>
              {analytics.todayCollections} / {analytics.pendingCollections}
            </strong>
          </div>
        </div>
      )}

      <section className="panel" style={{ marginBottom: 18 }}>
        <div className="form-grid" style={{ gridTemplateColumns: "repeat(5,1fr)" }}>
          <label>
            State
            <select value={filters.state} onChange={(e) => setFilters({ ...filters, state: e.target.value })}>
              <option value="">All</option>
              {filterOptions.states.map((s) => <option key={s} value={s}>{s}</option>)}
            </select>
          </label>
          <label>
            District
            <select value={filters.district} onChange={(e) => setFilters({ ...filters, district: e.target.value })}>
              <option value="">All</option>
              {filterOptions.districts.map((s) => <option key={s} value={s}>{s}</option>)}
            </select>
          </label>
          <label>
            Taluka
            <select value={filters.taluka} onChange={(e) => setFilters({ ...filters, taluka: e.target.value })}>
              <option value="">All</option>
              {filterOptions.talukas.map((s) => <option key={s} value={s}>{s}</option>)}
            </select>
          </label>
          <label>
            Inventory Status
            <select value={filters.inventoryStatus} onChange={(e) => setFilters({ ...filters, inventoryStatus: e.target.value })}>
              <option value="">All</option>
              <option value="Normal">Normal</option>
              <option value="Low">Low</option>
              <option value="Critical">Critical</option>
            </select>
          </label>
          <label>
            Heatmap Overlay
            <select value={heatmapLayer} onChange={(e) => setHeatmapLayer(e.target.value)}>
              {HEATMAP_OPTIONS.map((o) => <option key={o.value} value={o.value}>{o.label}</option>)}
            </select>
          </label>
        </div>
      </section>

      {!markers && !error && <LoadingState text="Loading map..." />}

      {markers && (
        <div className="grid-2" style={{ gridTemplateColumns: "1.4fr .6fr" }}>
          <section className="panel" style={{ padding: 0, overflow: "hidden" }}>
            <MapContainer center={[21.19, 79.1]} zoom={9} style={{ height: 520, width: "100%" }}>
              <TileLayer
                attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
                url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
              />
              {markers.map((m) => (
                <Marker key={m.id} position={[m.latitude, m.longitude]} icon={shopIcon(m.inventoryStatus)} eventHandlers={{ click: () => setSelectedShop(m) }}>
                  <Popup>
                    <b>{m.shopName}</b>
                    <br />
                    {m.village}, {m.district}
                    <br />
                    Inventory: {m.inventoryStatus}
                    <br />
                    Today: {m.todayBookings} bookings, {m.completedCollections} completed
                  </Popup>
                </Marker>
              ))}
              {heatmapPoints.map((p, idx) => (
                <CircleMarker
                  key={idx}
                  center={[p.lat, p.lng]}
                  radius={Math.min(30, 6 + p.intensity)}
                  pathOptions={{ color: "#2563eb", fillColor: "#2563eb", fillOpacity: 0.25, weight: 1 }}
                />
              ))}
            </MapContainer>
          </section>

          <section className="panel">
            <div className="panel-title">
              <div>
                <span className="eyebrow blue">SHOP DETAILS</span>
                <h2>{selectedShop ? selectedShop.shopName : "Select a shop"}</h2>
              </div>
            </div>
            {!selectedShop && <p className="muted">Click a marker on the map to see shop details.</p>}
            {selectedShop && (
              <div className="detail-list">
                <div>
                  <span>Shop Code</span>
                  <b>{selectedShop.shopCode}</b>
                </div>
                <div>
                  <span>Location</span>
                  <b>
                    {selectedShop.village}, {selectedShop.taluka}, {selectedShop.district}
                  </b>
                </div>
                <div>
                  <span>Inventory Status</span>
                  <b style={{ color: STATUS_COLOR[selectedShop.inventoryStatus] }}>{selectedShop.inventoryStatus}</b>
                </div>
                <div>
                  <span>Today's Bookings</span>
                  <b>{selectedShop.todayBookings}</b>
                </div>
                <div>
                  <span>Completed / Pending Collections</span>
                  <b>
                    {selectedShop.completedCollections} / {selectedShop.pendingCollections}
                  </b>
                </div>
                <div>
                  <span>Eligible Beneficiaries</span>
                  <b>{selectedShop.eligibleBeneficiaries}</b>
                </div>
                <div>
                  <span>Verification Issues</span>
                  <b style={{ color: selectedShop.verificationIssues > 0 ? "var(--orange)" : "var(--green)" }}>{selectedShop.verificationIssues}</b>
                </div>
              </div>
            )}
          </section>
        </div>
      )}
    </>
  );
}
