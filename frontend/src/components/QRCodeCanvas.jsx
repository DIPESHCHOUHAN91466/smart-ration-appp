import { useEffect, useRef } from "react";
import QRCode from "qrcode";

export default function QRCodeCanvas({ value, size = 190, errorCorrectionLevel = "H" }) {
  const ref = useRef(null);

  useEffect(() => {
    if (ref.current && value) {
      QRCode.toCanvas(ref.current, value, { width: size, margin: 2, errorCorrectionLevel });
    }
  }, [value, size, errorCorrectionLevel]);

  return <canvas ref={ref} aria-label="Ration token QR code" />;
}
