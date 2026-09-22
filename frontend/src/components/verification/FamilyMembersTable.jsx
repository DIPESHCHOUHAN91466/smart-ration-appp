const ELIGIBILITY_TONE = {
  Eligible: "success",
  NotEligible: "danger",
  Pending: "warning",
  VerificationRequired: "warning",
};

export default function FamilyMembersTable({ family }) {
  if (!family) return null;

  return (
    <section className="panel">
      <div className="panel-title">
        <div>
          <span className="eyebrow blue">FAMILY DETAILS</span>
          <h2>{family.familyCode}</h2>
        </div>
        <span className="muted">
          {family.eligibleMemberCount} of {family.familySize} eligible
        </span>
      </div>
      <div className="table-wrap">
        <table>
          <thead>
            <tr>
              <th>Name</th>
              <th>Age</th>
              <th>Relationship</th>
              <th>Eligibility</th>
            </tr>
          </thead>
          <tbody>
            {family.members.map((m) => (
              <tr key={m.id}>
                <td>
                  <div className="user-cell">
                    <div className="mini-avatar">{m.fullName[0]}</div>
                    <b>{m.fullName}</b>
                  </div>
                </td>
                <td>{m.age}</td>
                <td>{m.relationship}</td>
                <td>
                  <span className={`status ${ELIGIBILITY_TONE[m.eligibility] || "warning"}`}>{m.eligibility}</span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </section>
  );
}
