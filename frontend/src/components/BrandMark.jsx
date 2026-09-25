import emblem from "../assets/ration-mitra-emblem.png";
import hsd2cLogo from "../assets/hsd2c-logo.png";

// Logo 1 — the Ration Mitra emblem: a pixel crop (not a redraw) of the supplied logo
// src/assets/ration-mitra-logo.webp, on its own black background. Shown at the top of every
// header (public site, login, register, dashboard sidebar) next to the product name. The chatbot
// uses the same emblem, smaller (Logo 2, ChatbotAvatar). Decorative: the name is always next to it.
export default function BrandMark({ variant = "" }) {
  return (
    <div className={`brand-mark emblem ${variant}`.trim()}>
      <img src={emblem} alt="" aria-hidden="true" width={44} height={44} />
    </div>
  );
}

// The official HSD2C company logo — used exactly as supplied (no recolor, redraw or distortion),
// in the footer ("Powered by HSD2C").
export function CompanyMark({ variant = "" }) {
  return (
    <div className={`brand-mark hsd2c ${variant}`.trim()}>
      <img src={hsd2cLogo} alt="HSD2C - High Speed Device to Cloud Solutions" />
    </div>
  );
}
