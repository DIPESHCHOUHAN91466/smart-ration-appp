export default function EntitlementTable({ entitlement }) {
  if (!entitlement) return null;

  return (
    <section className="panel">
      <div className="panel-title">
        <div>
          <span className="eyebrow blue">RATION ENTITLEMENT</span>
          <h2>
            {entitlement.schemeName} ({entitlement.schemeCode})
          </h2>
        </div>
        <span className="muted">{entitlement.eligibleMemberCount} eligible members</span>
      </div>
      <div className="table-wrap">
        <table>
          <thead>
            <tr>
              <th>Commodity</th>
              <th>Monthly Entitlement</th>
              <th>Already Collected</th>
              <th>Remaining</th>
              <th>Today's Allocation</th>
            </tr>
          </thead>
          <tbody>
            {entitlement.items.map((item) => (
              <tr key={item.rationType}>
                <td>{item.rationType}</td>
                <td>{item.monthlyEntitlement} kg</td>
                <td>{item.alreadyCollected} kg</td>
                <td>{item.remaining} kg</td>
                <td>
                  <b style={{ color: item.todayAllocation > 0 ? "var(--green)" : "var(--red)" }}>{item.todayAllocation} kg</b>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </section>
  );
}
