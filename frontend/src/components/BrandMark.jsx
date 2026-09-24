import hsd2cLogo from "../assets/hsd2c-logo.png";

// The official HSD2C company logo — used exactly as supplied (no recolor,
// redraw or distortion), consistently in the upper-left branding area across
// Login, Register and the dashboard sidebar.
export default function BrandMark({ variant = "" }) {
  return (
    <div className={`brand-mark hsd2c ${variant}`.trim()}>
      <img src={hsd2cLogo} alt="HSD2C - High Speed Device to Cloud Solutions" />
    </div>
  );
}
