import { useEffect } from "react";
import { useTranslation } from "../../i18n/useTranslation";
import { LEGAL_REVIEWED, legalContent } from "./legalContent";

/** One policy page (privacy | terms | accessibility) in the reader's language. */
export default function LegalPage({ doc }) {
  const { t, language } = useTranslation();
  const content = (legalContent[language] || legalContent.en)[doc];

  useEffect(() => {
    document.title = `${content.title} · ${t("app_name")}`;
  }, [content.title, t]);

  return (
    <article className="legal-page" lang={language} aria-labelledby="legal-title">
      <h1 id="legal-title">{content.title}</h1>
      <p className="legal-updated">{t("legal_last_updated")}: {LEGAL_REVIEWED}</p>
      {content.sections.map(([heading, paragraphs]) => (
        <section key={heading}>
          <h2>{heading}</h2>
          {paragraphs.length > 2 ? (
            <ul>{paragraphs.map((p) => <li key={p}>{p}</li>)}</ul>
          ) : (
            paragraphs.map((p) => <p key={p}>{p}</p>)
          )}
        </section>
      ))}
    </article>
  );
}
