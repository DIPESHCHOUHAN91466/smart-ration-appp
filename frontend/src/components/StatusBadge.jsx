const STATUS_TONE = {
  Confirmed: "success",
  Completed: "success",
  Pending: "warning",
  Cancelled: "danger",
  NoShow: "danger",
  Available: "success",
  Limited: "warning",
  Full: "danger",
};

export default function StatusBadge({ status }) {
  const tone = STATUS_TONE[status] || "warning";
  return <span className={`status ${tone}`}>{status}</span>;
}
