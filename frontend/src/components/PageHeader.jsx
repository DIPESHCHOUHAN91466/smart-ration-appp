import { usePreferencesStore } from "../state/preferencesStore";

export default function PageHeader({ title, subtitle, action }) {
  const showBreadcrumbs = usePreferencesStore((s) => s.showBreadcrumbs);
  const showHelp = usePreferencesStore((s) => s.showHelp);

  return (
    <div className="page-header">
      <div>
        {showBreadcrumbs && <div className="eyebrow blue">SMART RATION • HSD2C</div>}
        <h1>{title}</h1>
        {subtitle && showHelp && <p>{subtitle}</p>}
      </div>
      {action}
    </div>
  );
}
