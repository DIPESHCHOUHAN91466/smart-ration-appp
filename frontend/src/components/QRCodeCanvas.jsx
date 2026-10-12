import { useEffect, useRef } from "react";
import QRCode from "qrcode";

export default function QRCodeCanvas({ value, size = 190, errorCorrectionLevel = "H", label = "Ration token QR code" }) {
  const ref = useRef(null);

  useEffect(() => {
    if (ref.current && value) {
      // margin 4 = the standard white quiet zone: cameras find the code faster with it.
      QRCode.toCanvas(ref.current, value, { width: size, margin: 4, errorCorrectionLevel });
    }
  }, [value, size, errorCorrectionLevel]);

  // Shrinks with a narrow screen instead of overflowing it.
  return <canvas ref={ref} role="img" aria-label={label} style={{ maxWidth: "100%", height: "auto" }} />;
}
