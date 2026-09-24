// Reusable on/off control for Settings — used wherever a preference is a
// plain boolean. Fully keyboard-operable (role="switch", Enter/Space).
export default function ToggleSetting({ label, description, checked, onChange }) {
  const toggle = () => onChange(!checked);

  return (
    <div className="toggle-row">
      <div>
        <b>{label}</b>
        {description && <small>{description}</small>}
      </div>
      <span
        className={`toggle-switch ${checked ? "on" : ""}`}
        onClick={toggle}
        role="switch"
        aria-checked={checked}
        aria-label={label}
        tabIndex={0}
        onKeyDown={(e) => {
          if (e.key === "Enter" || e.key === " ") {
            e.preventDefault();
            toggle();
          }
        }}
      >
        <span className="toggle-knob" />
      </span>
    </div>
  );
}
