import { useEffect, useState } from "react";
import { Store } from "lucide-react";
import PageHeader from "../../components/PageHeader";
import { EmptyState, ErrorState, LoadingState } from "../../components/EmptyState";
import { getShops } from "../../services/shopsService";

export default function Shops() {
  const [shops, setShops] = useState(null);
  const [error, setError] = useState("");

  const load = () => {
    setError("");
    setShops(null);
    getShops()
      .then(setShops)
      .catch((err) => setError(err.message));
  };

  useEffect(load, []);

  return (
    <>
      <PageHeader title="Shop Management" subtitle="Ration shops registered in your jurisdiction." />
      <section className="panel">
        {error && <ErrorState text={error} onRetry={load} />}
        {!error && shops === null && <LoadingState text="Loading shops..." />}
        {!error && shops?.length === 0 && <EmptyState title="No shops found" text="No active ration shops are registered." />}
        {shops?.length > 0 && (
          <div className="table-wrap">
            <table>
              <thead>
                <tr>
                  <th>Shop</th>
                  <th>Code</th>
                  <th>District</th>
                  <th>State</th>
                  <th>Status</th>
                </tr>
              </thead>
              <tbody>
                {shops.map((s) => (
                  <tr key={s.id}>
                    <td>
                      <div className="user-cell">
                        <div className="mini-avatar">
                          <Store size={14} />
                        </div>
                        <b>{s.shopName}</b>
                      </div>
                    </td>
                    <td>
                      <code>{s.shopCode}</code>
                    </td>
                    <td>{s.district}</td>
                    <td>{s.state}</td>
                    <td>
                      <span className={`status ${s.isActive ? "success" : "danger"}`}>{s.isActive ? "Active" : "Inactive"}</span>
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
