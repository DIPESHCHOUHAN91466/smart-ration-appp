import { useEffect, useState } from "react";
import { Check, Package, Pencil, X } from "lucide-react";
import PageHeader from "../../components/PageHeader";
import { EmptyState, ErrorState, LoadingState } from "../../components/EmptyState";
import { getInventory, updateInventory } from "../../services/inventoryService";
import { useToast } from "../../state/toast";

export default function ShopInventory() {
  const [items, setItems] = useState(null);
  const [error, setError] = useState("");
  const [editingId, setEditingId] = useState(null);
  const [draft, setDraft] = useState({ availableQuantity: 0, minimumStockLevel: 0 });
  const [saving, setSaving] = useState(false);
  const notify = useToast();

  const load = () => {
    setError("");
    setItems(null);
    getInventory()
      .then(setItems)
      .catch((err) => setError(err.message));
  };

  useEffect(load, []);

  const startEdit = (item) => {
    setEditingId(item.id);
    setDraft({ availableQuantity: item.availableQuantity, minimumStockLevel: item.minimumStockLevel });
  };

  const save = async (id) => {
    setSaving(true);
    try {
      const updated = await updateInventory(id, {
        availableQuantity: Number(draft.availableQuantity),
        minimumStockLevel: Number(draft.minimumStockLevel),
      });
      setItems((prev) => prev.map((i) => (i.id === id ? updated : i)));
      notify("Inventory updated");
      setEditingId(null);
    } catch (err) {
      notify(err.message || "Could not update inventory", "error");
    } finally {
      setSaving(false);
    }
  };

  return (
    <>
      <PageHeader title="Inventory" subtitle="Track stock against pre-selected customer ration requirements." />

      {error && <ErrorState text={error} onRetry={load} />}
      {!error && items === null && <LoadingState text="Loading inventory..." />}
      {!error && items?.length === 0 && <EmptyState title="No inventory records" text="No inventory has been configured for your shop yet." />}

      {items?.length > 0 && (
        <>
          <div className="stats-grid">
            {items.map((item) => (
              <div className={`stat-card ${item.isLowStock ? "orange" : "blue"}`} key={item.id}>
                <div className="stat-top">
                  <span>{item.rationType}</span>
                  <Package size={19} />
                </div>
                <strong>{item.availableQuantity} kg</strong>
                <small>{item.isLowStock ? "Low stock" : "Available stock"}</small>
              </div>
            ))}
          </div>

          <section className="panel">
            <h2>Commodity inventory</h2>
            <div className="table-wrap">
              <table>
                <thead>
                  <tr>
                    <th>Commodity</th>
                    <th>Available</th>
                    <th>Allocated (lifetime)</th>
                    <th>Minimum threshold</th>
                    <th>Status</th>
                    <th></th>
                  </tr>
                </thead>
                <tbody>
                  {items.map((item) => {
                    const editing = editingId === item.id;
                    return (
                      <tr key={item.id}>
                        <td>{item.rationType}</td>
                        <td>
                          {editing ? (
                            <input
                              type="number"
                              min={0}
                              step={0.1}
                              value={draft.availableQuantity}
                              onChange={(e) => setDraft({ ...draft, availableQuantity: e.target.value })}
                              style={{ width: 100 }}
                            />
                          ) : (
                            `${item.availableQuantity} kg`
                          )}
                        </td>
                        <td>{item.allocatedQuantity} kg</td>
                        <td>
                          {editing ? (
                            <input
                              type="number"
                              min={0}
                              step={0.1}
                              value={draft.minimumStockLevel}
                              onChange={(e) => setDraft({ ...draft, minimumStockLevel: e.target.value })}
                              style={{ width: 100 }}
                            />
                          ) : (
                            `${item.minimumStockLevel} kg`
                          )}
                        </td>
                        <td>
                          <span className={`status ${item.isLowStock ? "warning" : "success"}`}>
                            {item.isLowStock ? "Low" : "Healthy"}
                          </span>
                        </td>
                        <td>
                          {editing ? (
                            <div style={{ display: "flex", gap: 6 }}>
                              <button className="icon-btn" onClick={() => save(item.id)} disabled={saving}>
                                <Check size={15} />
                              </button>
                              <button className="icon-btn" onClick={() => setEditingId(null)}>
                                <X size={15} />
                              </button>
                            </div>
                          ) : (
                            <button className="icon-btn" onClick={() => startEdit(item)}>
                              <Pencil size={15} />
                            </button>
                          )}
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          </section>
        </>
      )}
    </>
  );
}
