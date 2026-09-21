import { useEffect, useState } from "react";
import PageHeader from "../../components/PageHeader";
import { EmptyState, ErrorState, LoadingState } from "../../components/EmptyState";
import { getUsers } from "../../services/adminService";

const ROLE_FILTERS = [
  { value: "", label: "All roles" },
  { value: "RuralUser", label: "Rural Users" },
  { value: "ShopOwner", label: "Shop Owners" },
  { value: "GovernmentOfficial", label: "Government Officials" },
];

export default function Users() {
  const [users, setUsers] = useState(null);
  const [error, setError] = useState("");
  const [role, setRole] = useState("");

  const load = (r) => {
    setError("");
    setUsers(null);
    getUsers(r || undefined)
      .then(setUsers)
      .catch((err) => setError(err.message));
  };

  useEffect(() => load(role), [role]);

  return (
    <>
      <PageHeader
        title="Beneficiaries & Staff"
        subtitle="Search and review registered users across all roles."
        action={
          <select className="small-select" value={role} onChange={(e) => setRole(e.target.value)}>
            {ROLE_FILTERS.map((f) => (
              <option key={f.value} value={f.value}>
                {f.label}
              </option>
            ))}
          </select>
        }
      />
      <section className="panel">
        {error && <ErrorState text={error} onRetry={() => load(role)} />}
        {!error && users === null && <LoadingState text="Loading users..." />}
        {!error && users?.length === 0 && <EmptyState title="No users found" text="No users match this filter." />}
        {users?.length > 0 && (
          <div className="table-wrap">
            <table>
              <thead>
                <tr>
                  <th>Name</th>
                  <th>Email</th>
                  <th>Mobile</th>
                  <th>Role</th>
                </tr>
              </thead>
              <tbody>
                {users.map((u) => (
                  <tr key={u.id}>
                    <td>
                      <div className="user-cell">
                        <div className="mini-avatar">{u.fullName[0]}</div>
                        <b>{u.fullName}</b>
                      </div>
                    </td>
                    <td>{u.email}</td>
                    <td>{u.mobileNumber}</td>
                    <td>
                      <span className="status success">{u.role}</span>
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
