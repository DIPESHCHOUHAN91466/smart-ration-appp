import { Link } from "react-router-dom";
import { AlertCircle, ArrowRight, Lock, RotateCcw } from "lucide-react";
import ChatbotAvatar from "./ChatbotAvatar";
import { useTranslation } from "../../i18n/useTranslation";

// Replies are plain text from the knowledge base. Render them as paragraphs and lists —
// never as HTML — so nothing in a message can become markup.
const BULLET = /^[•\-*]\s+/;
const NUMBERED = /^\d+[.)]\s+/;

export function toBlocks(text) {
  const blocks = [];
  for (const raw of (text || "").split("\n")) {
    const line = raw.trim();
    if (!line) {
      blocks.push({ type: "gap" });
      continue;
    }
    const type = BULLET.test(line) ? "ul" : NUMBERED.test(line) ? "ol" : "p";
    const content = line.replace(type === "ul" ? BULLET : type === "ol" ? NUMBERED : "", "");
    const last = blocks[blocks.length - 1];
    if (type !== "p" && last?.type === type) last.items.push(content);
    else blocks.push(type === "p" ? { type, text: content } : { type, items: [content] });
  }
  // One gap between blocks at most, none at the start or end.
  const compact = blocks.filter((b, i) => b.type !== "gap" || blocks[i - 1]?.type !== "gap");
  while (compact[0]?.type === "gap") compact.shift();
  while (compact[compact.length - 1]?.type === "gap") compact.pop();
  return compact;
}

const isInternal = (path) => typeof path === "string" && path.startsWith("/") && !path.startsWith("//");

export function MessageText({ text }) {
  return toBlocks(text).map((block, i) => {
    if (block.type === "gap") return <div className="chat-gap" key={i} />;
    if (block.type === "ul") return <ul key={i}>{block.items.map((item, j) => <li key={j}>{item}</li>)}</ul>;
    if (block.type === "ol") return <ol key={i}>{block.items.map((item, j) => <li key={j}>{item}</li>)}</ol>;
    return <p key={i}>{block.text}</p>;
  });
}

export default function ChatbotMessage({ message, onChoose, onRetry, onNavigate, highlight }) {
  const { t } = useTranslation();

  if (message.role === "user") {
    return (
      <div className={`chat-row user ${highlight ? "match" : ""}`}>
        <span className="sr-only">{t("chat_you")}: </span>
        <div className="chat-bubble user">{message.text}</div>
      </div>
    );
  }

  if (message.error) {
    return (
      <div className="chat-row bot">
        <ChatbotAvatar size={28} />
        <div className="chat-bubble bot error" role="alert">
          <AlertCircle size={16} aria-hidden="true" />
          <span>{t(message.error === "rate_limited" ? "chat_rate_limited" : "chat_error")}</span>
          <button type="button" className="chat-retry" onClick={onRetry}>
            <RotateCcw size={14} aria-hidden="true" /> {t("chat_retry")}
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className={`chat-row bot ${highlight ? "match" : ""}`}>
      <ChatbotAvatar size={28} />
      <div className={`chat-bubble bot kind-${message.kind || "answer"}`}>
        <span className="sr-only">{t("chat_assistant")}: </span>
        {message.title && message.kind === "answer" && <strong className="chat-answer-title">{message.title}</strong>}
        {message.requiresLogin && <Lock size={15} className="chat-lock" aria-hidden="true" />}
        <MessageText text={message.text} />

        {message.links?.filter((l) => isInternal(l.path)).length > 0 && (
          <div className="chat-links">
            {message.links.filter((l) => isInternal(l.path)).map((link) => (
              <Link key={link.path} to={link.path} className="chat-link" onClick={onNavigate}>
                {link.label} <ArrowRight size={14} aria-hidden="true" />
              </Link>
            ))}
          </div>
        )}

        {message.related?.length > 0 && (
          <div className="chat-related">
            <span>{t("chat_related")}</span>
            {message.related.map((r) => (
              <button type="button" key={r.id} onClick={() => onChoose({ label: r.title, articleId: r.id })}>{r.title}</button>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
