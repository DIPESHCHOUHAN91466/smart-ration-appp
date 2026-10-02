import { useEffect, useRef, useState } from "react";
import PageHeader from "../../components/PageHeader";
import { EmptyState, ErrorState, LoadingState } from "../../components/EmptyState";
import { useTranslation } from "../../i18n/useTranslation";
import {
  AADHAAR_LIKE, COMPLAINT_CATEGORIES, COMPLAINT_ITEMS, COMPLAINT_MAX_LENGTH, COMPLAINT_MIN_LENGTH,
  fileComplaint, getMyComplaints, newRequestKey,
} from "../../services/grievancesService";

const STATUS_TONE = { Submitted: "warning", UnderReview: "warning", Resolved: "success", Rejected: "danger" };

/** Citizen: report a problem (write → review → confirm → reference number) and follow every complaint's status. */
export default function Complaints() {
  const { t } = useTranslation();
  const [rows, setRows] = useState(null);
  const [error, setError] = useState("");
  const [writing, setWriting] = useState(false);

  const load = () => {
    setError("");
    setRows(null);
    getMyComplaints().then(setRows).catch((err) => setError(err.message));
  };
  useEffect(load, []);

  return (
    <>
      <PageHeader
        title={t("gr_title_mine")}
        subtitle={t("gr_subtitle_mine")}
        action={!writing && <button type="button" className="primary-btn" onClick={() => setWriting(true)}>{t("gr_new")}</button>}
      />
      {writing && <NewComplaint onDone={() => { setWriting(false); load(); }} onCancel={() => setWriting(false)} />}
      <section className="panel">
        {error && <ErrorState text={error} onRetry={load} />}
        {!error && rows === null && <LoadingState text={t("gr_loading")} />}
        {!error && rows?.length === 0 && <EmptyState title={t("gr_none_mine")} text="" />}
        {rows?.length > 0 && (
          <div className="table-wrap">
            <table>
              <thead>
                <tr>
                  <th>{t("gr_reference")}</th>
                  <th>{t("gr_filed")}</th>
                  <th>{t("gr_category")}</th>
                  <th>{t("gr_description")}</th>
                  <th>{t("gr_status")}</th>
                </tr>
              </thead>
              <tbody>
                {rows.map((c) => (
                  <tr key={c.id}>
                    <td><code>{c.referenceNumber}</code></td>
                    <td>{c.createdAt?.slice(0, 16).replace("T", " ")}</td>
                    <td>{t(`gr_cat_${c.category}`)}{c.rationType ? ` · ${c.rationType}` : ""}</td>
                    <td style={{ maxWidth: 380 }}>
                      {c.description}
                      {c.resolutionNote && <div className="muted"><b>{t("gr_reply")}:</b> {c.resolutionNote}</div>}
                    </td>
                    <td><span className={`status ${STATUS_TONE[c.status] || "warning"}`}>{t(`gr_status_${c.status}`)}</span></td>
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

function NewComplaint({ onDone, onCancel }) {
  const { t } = useTranslation();
  const requestKey = useRef(newRequestKey());   // reused on every retry: a lost answer never files it twice
  const [category, setCategory] = useState("");
  const [rationType, setRationType] = useState("");
  const [description, setDescription] = useState("");
  const [step, setStep] = useState("write");     // write | review | sent
  const [checked, setChecked] = useState(false);
  const [error, setError] = useState("");
  const [sending, setSending] = useState(false);
  const [reference, setReference] = useState("");

  const privateOk = !AADHAAR_LIKE.test(description);
  const descriptionOk = description.trim().length >= COMPLAINT_MIN_LENGTH;
  const complete = category && descriptionOk && privateOk;

  const send = async () => {
    setSending(true);
    setError("");
    try {
      const filed = await fileComplaint({ category, description, rationType }, requestKey.current);
      setReference(filed.referenceNumber);
      setStep("sent");
    } catch (err) {
      setError(err.message);
    } finally {
      setSending(false);
    }
  };

  if (step === "sent") {
    return (
      <section className="panel" style={{ marginBottom: 18 }}>
        <p role="status" style={{ fontSize: 15 }}>{t("gr_sent")} <code>{reference}</code></p>
        <button type="button" className="primary-btn" onClick={onDone}>{t("gr_title_mine")}</button>
      </section>
    );
  }

  if (step === "review") {
    return (
      <section className="panel form-panel" style={{ marginBottom: 18 }} aria-labelledby="gr-review-title">
        <h2 id="gr-review-title">{t("gr_review")}</h2>
        <p className="muted">{t("gr_review_note")}</p>
        <div className="summary">
          <div><span>{t("gr_category")}</span><b>{t(`gr_cat_${category}`)}</b></div>
          {rationType && <div><span>{t("gr_item")}</span><b>{rationType}</b></div>}
          <div><span>{t("gr_description")}</span><b>{description.trim()}</b></div>
        </div>
        {error && <p role="alert" style={{ color: "var(--red)" }}>{error}</p>}
        <div className="actions">
          <button type="button" className="primary-btn" disabled={sending} onClick={send}>{t("gr_submit")}</button>
          <button type="button" className="secondary-btn" disabled={sending} onClick={() => setStep("write")}>{t("gr_edit")}</button>
        </div>
      </section>
    );
  }

  return (
    <section className="panel form-panel" style={{ marginBottom: 18 }} aria-labelledby="gr-new-title">
      <h2 id="gr-new-title">{t("gr_new")}</h2>
      <form onSubmit={(e) => { e.preventDefault(); setChecked(true); if (complete) setStep("review"); }} noValidate>
        <label htmlFor="gr-category">{t("gr_category")}</label>
        <select id="gr-category" value={category} onChange={(e) => setCategory(e.target.value)} aria-invalid={checked && !category}
          aria-describedby={checked && !category ? "gr-category-error" : undefined} className="small-select" style={{ display: "block", margin: "7px 0 14px" }}>
          <option value="">—</option>
          {COMPLAINT_CATEGORIES.map((c) => <option key={c} value={c}>{t(`gr_cat_${c}`)}</option>)}
        </select>
        {checked && !category && <p id="gr-category-error" role="alert" style={{ color: "var(--red)" }}>{t("gr_choose_category")}</p>}

        <label htmlFor="gr-item">{t("gr_item")}</label>
        <select id="gr-item" value={rationType} onChange={(e) => setRationType(e.target.value)} className="small-select" style={{ display: "block", margin: "7px 0 14px" }}>
          <option value="">{t("gr_item_none")}</option>
          {COMPLAINT_ITEMS.map((i) => <option key={i} value={i}>{i}</option>)}
        </select>

        <label htmlFor="gr-description">{t("gr_description")}</label>
        <textarea id="gr-description" rows={4} maxLength={COMPLAINT_MAX_LENGTH} value={description} placeholder={t("gr_describe_hint")}
          onChange={(e) => setDescription(e.target.value)} aria-describedby="gr-description-help" aria-invalid={!privateOk || (checked && !descriptionOk)} />
        <p id="gr-description-help" className="muted">{t("gr_no_private")}</p>
        {!privateOk && <p role="alert" style={{ color: "var(--red)" }}>{t("gr_no_private")}</p>}
        {privateOk && checked && !descriptionOk && <p role="alert" style={{ color: "var(--red)" }}>{t("gr_describe_short")}</p>}

        <div className="actions">
          <button type="submit" className="primary-btn">{t("gr_review")}</button>
          <button type="button" className="secondary-btn" onClick={onCancel}>{t("gr_cancel")}</button>
        </div>
      </form>
    </section>
  );
}
