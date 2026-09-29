import rationMitraLogo from "../../assets/ration-mitra-logo.webp";

// The assistant's avatar: the SAME official Ration Mitra logo asset as the header (not a separate icon),
// shown complete (object-fit: contain, never cropped or stretched) inside a round white badge, so the logo's
// own white background blends in instead of showing as a rectangle. `size` is the badge diameter; the logo
// fills ~84% of it (a 48px badge holds a 40px logo box).
export default function ChatbotAvatar({ size = 36, className = "" }) {
  return (
    <span className={`chatbot-avatar ${className}`.trim()} style={{ width: size, height: size }} aria-hidden="true">
      <img src={rationMitraLogo} alt="" width={1600} height={1200} decoding="async" draggable="false" />
    </span>
  );
}
