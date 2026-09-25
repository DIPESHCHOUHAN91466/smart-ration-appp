import emblem from "../../assets/ration-mitra-emblem.png";

// Logo 2 — the Ration Mitra emblem (same crop as the header's Logo 1), small and round, so the
// assistant is visibly the "Ration Mitra AI Assistant".
export default function ChatbotAvatar({ size = 36, className = "" }) {
  return <img className={`chatbot-avatar ${className}`.trim()} src={emblem} width={size} height={size} alt="" aria-hidden="true" />;
}
