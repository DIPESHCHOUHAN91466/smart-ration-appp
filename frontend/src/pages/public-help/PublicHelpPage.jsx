import { useCallback, useEffect, useState } from "react";
import { useSearchParams } from "react-router-dom";
import {
  AlertTriangle, ArrowLeft, BadgeCheck, CalendarClock, ChevronRight, CreditCard, FileText, Files, Headphones,
  Info, Landmark, MapPin, MessageCircle, QrCode, Scale, Search, ShieldAlert, ShoppingBag, X,
} from "lucide-react";
import { Link } from "react-router-dom";
import { MessageText } from "../../components/chatbot/ChatbotMessage";
import { publicHelpService } from "../../services/chatbotService";
import { openChatbot } from "../../store/chatbotStore";
import { useTranslation } from "../../i18n/useTranslation";

const ICONS = {
  card: CreditCard, check: BadgeCheck, form: FileText, file: Files, clock: CalendarClock, qr: QrCode,
  bag: ShoppingBag, scheme: Landmark, shield: Scale, map: MapPin, info: Info, phone: Headphones,
};

function useHelpData(language) {
  const [categories, setCategories] = useState(null);
  const [error, setError] = useState(false);
  const load = useCallback(() => {
    setError(false);
    publicHelpService.categories(language).then(setCategories).catch(() => setError(true));
  }, [language]);
  useEffect(load, [load]);
  return { categories, error, reload: load };
}

function Article({ id, language, onBack, onOpen }) {
  const { t } = useTranslation();
  const [article, setArticle] = useState(null);
  const [error, setError] = useState(false);

  useEffect(() => {
    let alive = true;
    setArticle(null);
    setError(false);
    publicHelpService.article(id, language).then((a) => alive && setArticle(a)).catch(() => alive && setError(true));
    return () => { alive = false; };
  }, [id, language]);

  return (
    <article className="help-article" aria-live="polite">
      <button type="button" className="help-back" onClick={onBack}><ArrowLeft size={16} aria-hidden="true" /> {t("help_back")}</button>
      {error && <p className="help-error" role="alert"><AlertTriangle size={16} aria-hidden="true" /> {t("help_error")}</p>}
      {!article && !error && <div className="help-skeleton" aria-label={t("help_loading")}><span /><span /><span /></div>}
      {article && (
        <>
          <h2>{article.title}</h2>
          <div className="help-article-body"><MessageText text={article.text} /></div>
          {article.links?.filter((l) => l.path?.startsWith("/") && !l.path.startsWith("//")).map((l) => (
            <Link key={l.path} to={l.path} className="land-btn primary small">{l.label} <ChevronRight size={15} aria-hidden="true" /></Link>
          ))}
          {article.related?.length > 0 && (
            <div className="help-related">
              <h3>{t("help_related")}</h3>
              {article.related.map((r) => <button type="button" key={r.id} onClick={() => onOpen(r.id)}>{r.title}</button>)}
            </div>
          )}
        </>
      )}
    </article>
  );
}

export default function PublicHelpPage() {
  const { t, language } = useTranslation();
  const [params, setParams] = useSearchParams();
  const { categories, error, reload } = useHelpData(language);
  const [query, setQuery] = useState(params.get("q") || "");
  const [results, setResults] = useState(null);
  const [openCategory, setOpenCategory] = useState(null);
  const articleId = params.get("article");
  const searched = params.get("q");

  useEffect(() => {
    if (!searched) { setResults(null); return; }
    let alive = true;
    publicHelpService.search(searched, language).then((r) => alive && setResults(r)).catch(() => alive && setResults([]));
    return () => { alive = false; };
  }, [searched, language]);

  const openArticle = (id) => { setParams({ article: id }); window.scrollTo({ top: 0, behavior: "smooth" }); };
  const back = () => setParams(searched ? { q: searched } : {});
  const submit = (e) => {
    e.preventDefault();
    const q = query.trim();
    setParams(q ? { q } : {});
  };

  return (
    <div className="help-page">
      <section className="help-hero">
        <h1>{t("help_title")}</h1>
        <p>{t("help_subtitle")}</p>
        <form className="help-search" role="search" onSubmit={submit}>
          <label htmlFor="help-q" className="sr-only">{t("help_search_label")}</label>
          <Search size={18} aria-hidden="true" />
          <input id="help-q" type="search" value={query} maxLength={100} placeholder={t("help_search_placeholder")} onChange={(e) => setQuery(e.target.value)} />
          {query && (
            <button type="button" className="help-clear" aria-label={t("help_clear_search")} onClick={() => { setQuery(""); setParams({}); }}>
              <X size={16} aria-hidden="true" />
            </button>
          )}
          <button type="submit" className="land-btn primary small">{t("help_search_btn")}</button>
        </form>
        <p className="help-privacy"><ShieldAlert size={15} aria-hidden="true" /> {t("help_privacy_note")}</p>
      </section>

      <div className="help-body">
        {articleId ? (
          <Article id={articleId} language={language} onBack={back} onOpen={openArticle} />
        ) : searched ? (
          <section aria-live="polite">
            <h2 className="help-results-title">{t("help_results_for")} “{searched}”</h2>
            {results === null && <div className="help-skeleton"><span /><span /></div>}
            {results?.length === 0 && (
              <div className="help-empty">
                <p>{t("help_no_results")}</p>
                <button type="button" className="land-btn primary small" onClick={() => openChatbot(searched)}>
                  <MessageCircle size={16} aria-hidden="true" /> {t("help_ask_assistant")}
                </button>
              </div>
            )}
            <ul className="help-results">
              {results?.map((r) => (
                <li key={r.id}>
                  <button type="button" onClick={() => openArticle(r.id)}>
                    <strong>{r.title}</strong>
                    <span>{r.excerpt}</span>
                    <ChevronRight size={18} aria-hidden="true" />
                  </button>
                </li>
              ))}
            </ul>
          </section>
        ) : (
          <>
            {error && (
              <div className="help-error" role="alert">
                <AlertTriangle size={16} aria-hidden="true" /> {t("help_error")}
                <button type="button" className="chat-retry" onClick={reload}>{t("help_retry")}</button>
              </div>
            )}
            {!categories && !error && <div className="help-grid">{Array.from({ length: 6 }, (_, i) => <div key={i} className="help-card skeleton" />)}</div>}
            {categories && (
              <div className="help-grid">
                {categories.map((c) => {
                  const Icon = ICONS[c.icon] || Info;
                  const isOpen = openCategory === c.id;
                  return (
                    <section key={c.id} className={`help-card ${isOpen ? "open" : ""}`}>
                      <button type="button" className="help-card-head" aria-expanded={isOpen} aria-controls={`help-${c.id}`} onClick={() => setOpenCategory(isOpen ? null : c.id)}>
                        <span className="land-icon-tile"><Icon size={22} aria-hidden="true" /></span>
                        <span className="help-card-text">
                          <strong>{c.title}</strong>
                          <small>{c.description}</small>
                        </span>
                        <span className="help-count">{c.articles.length} {t(c.articles.length === 1 ? "help_topic_one" : "help_topics_count")}</span>
                      </button>
                      {isOpen && (
                        <ul id={`help-${c.id}`} className="help-card-articles">
                          {c.articles.map((a) => (
                            <li key={a.id}><button type="button" onClick={() => openArticle(a.id)}>{a.title} <ChevronRight size={15} aria-hidden="true" /></button></li>
                          ))}
                        </ul>
                      )}
                    </section>
                  );
                })}
              </div>
            )}
            <div className="help-assist">
              <MessageCircle size={22} aria-hidden="true" />
              <p>{t("land_help_text")}</p>
              <button type="button" className="land-btn primary small" onClick={() => openChatbot()}>{t("help_ask_assistant")}</button>
            </div>
          </>
        )}
      </div>
    </div>
  );
}
