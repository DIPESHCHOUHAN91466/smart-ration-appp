import { useEffect, useState } from "react";
import PageHeader from "../../components/PageHeader";
import { EmptyState, ErrorState, LoadingState } from "../../components/EmptyState";
import { useTranslation } from "../../i18n/useTranslation";
import { useToast } from "../../state/toast";
import { AADHAAR_LIKE, getAllComplaints, updateComplaintStatus } from "../../services/grievancesService";

const STATUS_TONE = { Submitted: "warning", UnderReview: "warning", Resolved: "success", Rejected: "danger" };
const STATUSES = ["Submitted", "UnderReview", "Resolved", "Rejected"];

/** Officials: every citizen complaint, newest first. Review one, reply to the citizen, record the outcome. */
export default function Complaints() {
  const { t } = useTranslation();
  const notify = useToast();
  const [status, setStatus] = useState("Submitted");
  const [rows, setRows] = useState(null);
  const [error, setError] = useState("");
  const [open, setOpen] = useState(null);       // id of the complaint being updated
  const [note, setNote] = useState("");
  const [noteError, setNoteError] = useState("");
  const [saving, setSaving] = useState(false);

  const load = () => {
    setError("");
    setRows(null);
    getAllComplaints(status || undefined).then(setRows).catch((err) => setError(err.message));
  };
  useEffect(load, [status]);

  const startUpdate = (complaint) => {
    setOpen(open === complaint.id ? null : complaint.id);
    setNote(complaint.resolutionNote || "");
    setNoteError("");
  };

  const save = async (complaint, next) => {
    if (AADHAAR_LIKE.test(note)) {
      setNoteError(t("gr_no_private"));
      return;
    }
    setSaving(true);
    try {
      await updateComplaintStatus(complaint.id, next, note);
      notify(t("gr_updated"));
      setOpen(null);
      load();
    } catch (err) {
      setNoteError(err.message);
    } finally {
      setSaving(false);
    }
  };

  return (
    <>
      <PageHeader
        title={t("gr_title_gov")}
        subtitle={t("gr_subtitle_gov")}
        action={
          <select className="small-select" aria-label={t("gr_status")} value={status} onChange={(e) => setStatus(e.target.value)}>
            <option value="">{t("gr_filter_all")}</option>
            {STATUSES.map((s) => <option key={s} value={s}>{t(`gr_status_${s}`)}</option>)}
          </select>
        }
      />
      <section className="panel">
        {error && <ErrorState text={error} onRetry={load} />}
        {!error && rows === null && <LoadingState text={t("gr_loading")} />}
        {!error && rows?.length === 0 && <EmptyState title={t("gr_none_gov")} text="" />}
        {rows?.length > 0 && (
          <div className="table-wrap">
            <table>
              <thead>
                <tr>
                  <th>{t("gr_reference")}</th>
                  <th>{t("gr_filed")}</th>
                  <th>{t("gr_category")}</th>
                  <th>{t("gr_shop")}</th>
                  <th>{t("gr_description")}</th>
                  <th>{t("gr_status")}</th>
                  <th><span className="sr-only">{t("gr_action_resolve")}</span></th>
                </tr>
              </thead>
              <tbody>
                {rows.map((c) => (
                  <ComplaintRow key={c.id} c={c} t={t} isOpen={open === c.id} onToggle={() => startUpdate(c)}>
                    {open === c.id && (
                      <tr>
                        <td colSpan={7} className="form-panel">
                          <label className="settings-field-label" htmlFor={`reply-${c.id}`}>{t("gr_reply_label")}</label>
                          <textarea
                            id={`reply-${c.id}`}
                            rows={3}
                            maxLength={500}
                            value={note}
                            onChange={(e) => { setNote(e.target.value); setNoteError(""); }}
                            aria-describedby={`reply-help-${c.id}`}
                          />
                          <p id={`reply-help-${c.id}`} className="muted">{t("gr_no_private")}</p>
                          {noteError && <p role="alert" style={{ color: "var(--red)" }}>{noteError}</p>}
                          <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
                            {c.status === "Submitted" && (
                              <button type="button" className="secondary-btn" disabled={saving} onClick={() => save(c, "UnderReview")}>{t("gr_action_review")}</button>
                            )}
                            <button type="button" className="primary-btn" disabled={saving} onClick={() => save(c, "Resolved")}>{t("gr_action_resolve")}</button>
                            <button type="button" className="secondary-btn" disabled={saving} onClick={() => save(c, "Rejected")}>{t("gr_action_reject")}</button>
                          </div>
                        </td>
                      </tr>
                    )}
                  </ComplaintRow>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </section>
    </>
  );
}

function ComplaintRow({ c, t, isOpen, onToggle, children }) {
  return (
    <>
      <tr>
        <td><code>{c.referenceNumber}</code></td>
        <td>{c.createdAt?.slice(0, 16).replace("T", " ")}</td>
        <td>{t(`gr_cat_${c.category}`)}{c.rationType ? ` · ${c.rationType}` : ""}</td>
        <td>{c.shopName || "—"}</td>
        <td style={{ maxWidth: 360 }}>
          {c.description}
          {c.resolutionNote && <div className="muted">{t("gr_reply")}: {c.resolutionNote}</div>}
        </td>
        <td><span className={`status ${STATUS_TONE[c.status] || "warning"}`}>{t(`gr_status_${c.status}`)}</span></td>
        <td>
          {c.status !== "Resolved" && c.status !== "Rejected" && (
            <button type="button" className="secondary-btn" aria-expanded={isOpen} onClick={onToggle}>{t("gr_action_resolve")}</button>
          )}
        </td>
      </tr>
      {children}
    </>
  );
}
