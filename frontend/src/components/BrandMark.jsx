import rationMitraLogo from "../assets/ration-mitra-logo.webp";
import hsd2cLogo from "../assets/hsd2c-logo.png";
import hsd2cHeaderLogo from "../assets/hsd2c-logo-header.png";

// The official Ration Mitra logo — the complete supplied artwork (1600×1200, src/assets/ration-mitra-logo.webp),
// used exactly as supplied: never cropped, recoloured, filtered or redrawn. It is always scaled
// proportionally (object-fit: contain, width-driven), so the AI/leaf/hand/cloud mark, "Ration Mitra",
// "AI Powered • For Every Family" and "POWERED BY HSD2C" stay visible at every size. The artwork has a
// white background, so on dark surfaces it sits on a white card instead of being altered.
// variant: "compact" (84×40 header/sidebar logo) | "login" | "hero" (sizes live in global.css, .rm-logo--*; namespaced so a
// variant can never pick up a layout class such as .sidebar).
export const RATION_MITRA_LOGO_ALT = "Ration Mitra — AI Powered, For Every Family. Powered by HSD2C";

export default function BrandMark({ variant = "header" }) {
  return (
    <span className={`rm-logo rm-logo--${variant}`}>
      <img src={rationMitraLogo} alt={RATION_MITRA_LOGO_ALT} width={1600} height={1200} decoding="async" />
    </span>
  );
}

// The HSD2C company logo, used exactly as supplied (no recolour, redraw or distortion).
// variant "header": the tightly framed version, shown on the right of the headers.
export function CompanyMark({ variant = "" }) {
  const header = variant.includes("header");
  return (
    <div className={`brand-mark hsd2c ${variant}`.trim()}>
      <img
        src={header ? hsd2cHeaderLogo : hsd2cLogo}
        alt="HSD2C - High Speed Device to Cloud Solutions"
        width={header ? 157 : 387}
        height={header ? 100 : 290}
        decoding="async"
      />
    </div>
  );
}
