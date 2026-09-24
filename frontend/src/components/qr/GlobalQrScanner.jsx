import { lazy, Suspense } from "react";
import { Loader2 } from "lucide-react";
import { useQrScannerStore } from "../../store/qrScannerStore";

// Heavy camera/decoder code is only fetched the first time the scanner opens.
const QrScannerModal = lazy(() => import("./QrScannerModal"));

// Mounted once in DashboardLayout; opened from anywhere via openGlobalQrScanner().
export default function GlobalQrScanner() {
  const isOpen = useQrScannerStore((s) => s.isOpen);
  const close = useQrScannerStore((s) => s.close);

  if (!isOpen) return null;

  return (
    <Suspense
      fallback={
        <div className="qr-modal-backdrop">
          <Loader2 className="qr-spin" size={40} color="#fff" />
        </div>
      }
    >
      <QrScannerModal onClose={close} />
    </Suspense>
  );
}
