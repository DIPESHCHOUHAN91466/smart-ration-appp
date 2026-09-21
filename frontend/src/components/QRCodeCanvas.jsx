import { useEffect, useRef } from "react";
import QRCode from "qrcode";

export default function QRCodeCanvas({ value, size = 190 }) {
  const ref = useRef(null);

  useEffect(() => {
    if (ref.current && value) {
      QRCode.toCanvas(ref.current, value, { width: size, margin: 2, errorCorrectionLevel: "H" });
    }
  }, [value, size]);

  return <canvas ref={ref} aria-label="Ration token QR code" />;
}
