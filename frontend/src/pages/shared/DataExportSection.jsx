import { useState } from "react";
import { Download } from "lucide-react";
import apiClient from "../../api/client";
import { useTranslation } from "../../i18n/useTranslation";
import { useToast } from "../../state/toast";

// "Download my data" card on Settings (DPDP Act 2023): everything the system holds about the signed-in person,
// as one JSON file (GET /users/me/export). The file is made in the browser; nothing is stored or cached.
export default function DataExportSection() {
  const { t } = useTranslation();
  const notify = useToast();
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");

  const download = async () => {
    setBusy(true);
    setError("");
    try {
      const response = await apiClient.get("/users/me/export");
      const blob = new Blob([JSON.stringify(response.data.data, null, 2)], { type: "application/json" });
      const url = URL.createObjectURL(blob);
      const link = document.createElement("a");
      link.href = url;
      link.download = `smart-ration-my-data-${new Date().toISOString().slice(0, 10)}.json`;
      document.body.appendChild(link);
      link.click();
      link.remove();
      URL.revokeObjectURL(url);
      notify(t("export_done"));
    } catch (err) {
      setError(err.message || t("export_failed"));
    } finally {
      setBusy(false);
    }
  };

  return (
    <section className="panel">
      <div className="settings-section-title">
        <Download size={19} />
        <h2>{t("settings_section_export")}</h2>
      </div>
      <p className="muted">{t("export_intro")}</p>
      {error && <p role="alert" style={{ color: "var(--red)" }}>{error}</p>}
      <button className="secondary-btn" type="button" onClick={download} disabled={busy}>
        {busy ? t("export_preparing") : t("export_download")}
      </button>
    </section>
  );
}
