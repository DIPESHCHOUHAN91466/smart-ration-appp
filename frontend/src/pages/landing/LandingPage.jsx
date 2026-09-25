import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import {
  ArrowRight, BadgeCheck, Building2, CalendarClock, ChevronDown, Headphones, Landmark, Languages, Lock,
  MessageCircle, PackageCheck, QrCode, Scale, ShieldCheck, Smartphone, Store, UserPlus, Users,
} from "lucide-react";
import QRCodeCanvas from "../../components/QRCodeCanvas";
import { MessageText } from "../../components/chatbot/ChatbotMessage";
import rationMitraLogo from "../../assets/ration-mitra-logo.webp";
import { publicHelpService } from "../../services/chatbotService";
import { openChatbot } from "../../store/chatbotStore";
import { useTranslation } from "../../i18n/useTranslation";

const FAQ_TOPICS = ["how_to_apply", "documents", "eligibility", "token_slots", "qr_verification", "contact_support"];

function Faq() {
  const { t, language } = useTranslation();
  const [items, setItems] = useState([]);
  const [open, setOpen] = useState(null);
  const [answers, setAnswers] = useState({});

  useEffect(() => {
    let alive = true;
    setAnswers({});
    publicHelpService.categories(language)
      .then((cats) => alive && setItems(FAQ_TOPICS.map((id) => cats.find((c) => c.id === id)).filter(Boolean)))
      .catch(() => alive && setItems([]));
    return () => { alive = false; };
  }, [language]);

  const toggle = async (item) => {
    const next = open === item.id ? null : item.id;
    setOpen(next);
    if (next && !answers[item.id]) {
      try {
        const article = await publicHelpService.article(item.primaryArticle, language);
        setAnswers((a) => ({ ...a, [item.id]: article.text }));
      } catch {
        setAnswers((a) => ({ ...a, [item.id]: t("help_error") }));
      }
    }
  };

  if (!items.length) return null;
  return (
    <section className="land-section" aria-labelledby="faq-title">
      <h2 id="faq-title" className="land-h2">{t("land_faq_title")}</h2>
      <div className="faq-list">
        {items.map((item) => (
          <div className={`faq-item ${open === item.id ? "open" : ""}`} key={item.id}>
            <h3>
              <button type="button" aria-expanded={open === item.id} aria-controls={`faq-${item.id}`} onClick={() => toggle(item)}>
                <span>{item.ask}</span>
                <ChevronDown size={18} aria-hidden="true" />
              </button>
            </h3>
            {open === item.id && (
              <div id={`faq-${item.id}`} className="faq-answer" role="region">
                {answers[item.id] ? <MessageText text={answers[item.id]} /> : <p className="muted">{t("land_faq_loading")}</p>}
              </div>
            )}
          </div>
        ))}
      </div>
      <div className="land-center">
        <Link to="/help" className="land-btn outline">{t("land_help_open")} <ArrowRight size={16} aria-hidden="true" /></Link>
      </div>
    </section>
  );
}

export default function LandingPage() {
  const { t } = useTranslation();

  const steps = [
    { icon: UserPlus, title: "land_step1_title", text: "land_step1_text" },
    { icon: CalendarClock, title: "land_step2_title", text: "land_step2_text" },
    { icon: QrCode, title: "land_step3_title", text: "land_step3_text" },
    { icon: PackageCheck, title: "land_step4_title", text: "land_step4_text" },
  ];
  const services = [
    { icon: Users, title: "land_service_citizen_title", text: "land_service_citizen_text" },
    { icon: Store, title: "land_service_shop_title", text: "land_service_shop_text" },
    { icon: Landmark, title: "land_service_gov_title", text: "land_service_gov_text" },
  ];
  const benefits = [
    { icon: CalendarClock, title: "land_benefit1_title", text: "land_benefit1_text" },
    { icon: Scale, title: "land_benefit2_title", text: "land_benefit2_text" },
    { icon: Lock, title: "land_benefit3_title", text: "land_benefit3_text" },
    { icon: Languages, title: "land_benefit4_title", text: "land_benefit4_text" },
  ];
  const contacts = [
    { icon: Store, title: "land_contact_shop_title", text: "land_contact_shop_text" },
    { icon: Building2, title: "land_contact_office_title", text: "land_contact_office_text" },
    { icon: Headphones, title: "land_contact_helpline_title", text: "land_contact_helpline_text" },
  ];

  return (
    <div className="landing">
      {/* ---------------------------------------------------------------- hero */}
      <section className="land-hero">
        <div className="land-hero-inner">
          <div className="land-hero-copy">
            <span className="land-badge"><ShieldCheck size={15} aria-hidden="true" /> {t("land_badge")}</span>
            <h1>{t("land_title")}</h1>
            <p className="land-lead">{t("land_subtitle")}</p>
            <div className="land-actions">
              <Link to="/register" className="land-btn primary">{t("land_cta_start")} <ArrowRight size={17} aria-hidden="true" /></Link>
              <Link to="/help" className="land-btn ghost">{t("land_cta_help")}</Link>
            </div>
            <ul className="land-stats">
              <li><CalendarClock size={16} aria-hidden="true" /> {t("land_stat_slots")}</li>
              <li><QrCode size={16} aria-hidden="true" /> {t("land_stat_verify")}</li>
              <li><Languages size={16} aria-hidden="true" /> {t("land_stat_langs")}</li>
              <li><PackageCheck size={16} aria-hidden="true" /> {t("land_stat_stock")}</li>
            </ul>
          </div>

          <div className="land-hero-visual" aria-hidden="true">
            <div className="token-card">
              <div className="token-top">
                <span>{t("app_name")}</span>
                <BadgeCheck size={18} />
              </div>
              <div className="token-qr"><QRCodeCanvas value="SMART-RATION-SAMPLE-TOKEN" size={148} errorCorrectionLevel="M" /></div>
              <div className="token-meta">
                <b>TKN-SAMPLE</b>
                <span>10:05 – 10:10</span>
              </div>
              <div className="token-items">
                <span>Rice · 10 kg</span><span>Wheat · 6 kg</span><span>Sugar · 2 kg</span>
              </div>
            </div>
            <div className="float-chip one"><ShieldCheck size={15} /> QR ✓</div>
            <div className="float-chip two"><Smartphone size={15} /> OTP</div>
          </div>
        </div>
      </section>

      {/* ---------------------------------------------------------------- how it works */}
      <section className="land-section" aria-labelledby="how-title">
        <h2 id="how-title" className="land-h2">{t("land_how_title")}</h2>
        <p className="land-sub">{t("land_how_sub")}</p>
        <ol className="land-steps">
          {steps.map((s, i) => (
            <li key={s.title} className="land-card step">
              <span className="step-num" aria-hidden="true">{i + 1}</span>
              <s.icon size={26} className="land-icon" aria-hidden="true" />
              <h3>{t(s.title)}</h3>
              <p>{t(s.text)}</p>
            </li>
          ))}
        </ol>
      </section>

      {/* ---------------------------------------------------------------- services */}
      <section className="land-section tinted" aria-labelledby="services-title">
        <h2 id="services-title" className="land-h2">{t("land_services_title")}</h2>
        <div className="land-grid three">
          {services.map((s) => (
            <article key={s.title} className="land-card service">
              <span className="land-icon-tile"><s.icon size={24} aria-hidden="true" /></span>
              <h3>{t(s.title)}</h3>
              <p>{t(s.text)}</p>
            </article>
          ))}
        </div>
      </section>

      {/* ---------------------------------------------------------------- benefits + QR */}
      <section className="land-section" aria-labelledby="benefits-title">
        <h2 id="benefits-title" className="land-h2">{t("land_benefits_title")}</h2>
        <div className="land-grid four">
          {benefits.map((b) => (
            <article key={b.title} className="land-card benefit">
              <b.icon size={22} className="land-icon" aria-hidden="true" />
              <h3>{t(b.title)}</h3>
              <p>{t(b.text)}</p>
            </article>
          ))}
        </div>

        <div className="land-qr">
          <div className="land-qr-icon"><QrCode size={46} aria-hidden="true" /></div>
          <div>
            <h3>{t("land_qr_title")}</h3>
            <p>{t("land_qr_text")}</p>
            <ul>
              <li><BadgeCheck size={16} aria-hidden="true" /> {t("land_qr_point1")}</li>
              <li><BadgeCheck size={16} aria-hidden="true" /> {t("land_qr_point2")}</li>
              <li><BadgeCheck size={16} aria-hidden="true" /> {t("land_qr_point3")}</li>
            </ul>
          </div>
        </div>
      </section>

      {/* ---------------------------------------------------------------- public help / assistant */}
      <section className="land-help" aria-labelledby="assist-title">
        <div className="land-help-inner">
          <img src={rationMitraLogo} alt="Ration Mitra — AI powered, for every family. Powered by HSD2C" className="land-help-logo" width={168} height={168} />
          <div>
            <h2 id="assist-title">{t("land_help_title")}</h2>
            <p>{t("land_help_text")}</p>
            <div className="land-actions">
              <button type="button" className="land-btn primary light" onClick={() => openChatbot()}>
                <MessageCircle size={17} aria-hidden="true" /> {t("land_help_chat")}
              </button>
              <Link to="/help" className="land-btn ghost light">{t("land_help_open")}</Link>
            </div>
          </div>
        </div>
      </section>

      <Faq />

      {/* ---------------------------------------------------------------- contact */}
      <section className="land-section tinted" aria-labelledby="contact-title">
        <h2 id="contact-title" className="land-h2">{t("land_contact_title")}</h2>
        <div className="land-grid three">
          {contacts.map((c) => (
            <article key={c.title} className="land-card contact">
              <span className="land-icon-tile"><c.icon size={22} aria-hidden="true" /></span>
              <h3>{t(c.title)}</h3>
              <p>{t(c.text)}</p>
            </article>
          ))}
        </div>
      </section>
    </div>
  );
}
