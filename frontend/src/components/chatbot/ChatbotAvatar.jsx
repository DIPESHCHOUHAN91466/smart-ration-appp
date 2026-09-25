import avatar from "../../assets/chatbot/chatbot-avatar.svg";

export default function ChatbotAvatar({ size = 36, className = "" }) {
  return <img className={`chatbot-avatar ${className}`.trim()} src={avatar} width={size} height={size} alt="" aria-hidden="true" />;
}
