import { useEffect, useState } from "react";
import PageHeader from "../../components/PageHeader";
import { EmptyState, ErrorState, LoadingState } from "../../components/EmptyState";
import { getInventory } from "../../services/inventoryService";
import { getShops } from "../../services/shopsService";

export default function GovernmentInventory() {
  const [inventory, setInventory] = useState(null);
  const [shops, setShops] = useState({});
  const [error, setError] = useState("");

  const load = () => {
    setError("");
    setInventory(null);
    Promise.all([getInventory(), getShops()])
      .then(([inventoryData, shopsData]) => {
        setShops(Object.fromEntries(shopsData.map((s) => [s.id, s.shopName])));
        setInventory(inventoryData);
      })
      .catch((err) => setError(err.message));
  };

  useEffect(load, []);

  return (
    <>
      <PageHeader title="Inventory Overview" subtitle="Stock levels across every ration shop." />
      <section className="panel">
        {error && <ErrorState text={error} onRetry={load} />}
        {!error && inventory === null && <LoadingState text="Loading inventory..." />}
        {!error && inventory?.length === 0 && <EmptyState title="No inventory records" text="No inventory has been configured yet." />}
        {inventory?.length > 0 && (
          <div className="table-wrap">
            <table>
              <thead>
                <tr>
                  <th>Shop</th>
                  <th>Commodity</th>
                  <th>Available</th>
                  <th>Allocated</th>
                  <th>Minimum</th>
                  <th>Status</th>
                </tr>
              </thead>
              <tbody>
                {inventory.map((item) => (
                  <tr key={item.id}>
                    <td>{shops[item.rationShopId] || `Shop #${item.rationShopId}`}</td>
                    <td>{item.rationType}</td>
                    <td>{item.availableQuantity} kg</td>
                    <td>{item.allocatedQuantity} kg</td>
                    <td>{item.minimumStockLevel} kg</td>
                    <td>
                      <span className={`status ${item.isLowStock ? "warning" : "success"}`}>{item.isLowStock ? "Low" : "Healthy"}</span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </section>
    </>
  );
}
