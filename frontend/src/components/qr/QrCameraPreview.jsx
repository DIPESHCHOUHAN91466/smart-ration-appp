import { useEffect, useRef } from "react";
import { CameraOff, FlashlightOff, Flashlight, ImageUp, Keyboard, Loader2, RefreshCcw, SwitchCamera } from "lucide-react";
import { CAMERA_ERROR, CAMERA_STATE, useQrScanner } from "../../hooks/useQrScanner";
import { useTranslation } from "../../i18n/useTranslation";

const CAMERA_ELEMENT_ID = "global-qr-camera";
const FILE_ELEMENT_ID = "global-qr-file-reader";

const CAMERA_ERROR_KEYS = {
  [CAMERA_ERROR.DENIED]: ["camera_permission_required", "camera_permission_desc"],
  [CAMERA_ERROR.NOT_FOUND]: ["camera_unavailable", "camera_not_found_desc"],
  [CAMERA_ERROR.IN_USE]: ["camera_unavailable", "camera_in_use_desc"],
  [CAMERA_ERROR.INSECURE]: ["camera_unavailable", "camera_insecure_desc"],
  [CAMERA_ERROR.UNSUPPORTED]: ["camera_unavailable", "camera_unsupported_desc"],
  [CAMERA_ERROR.FAILED]: ["camera_unavailable", "camera_failed_desc"],
};

// Live camera viewport + controls. Starts the camera as soon as it mounts
// (i.e. the moment "Scan QR" is clicked) and releases it on unmount.
export default function QrCameraPreview({ onDecode, onManual, onImageError }) {
  const { t } = useTranslation();
  const fileInputRef = useRef(null);
  const camera = useQrScanner({ elementId: CAMERA_ELEMENT_ID, onDecode });
  const { start, stop } = camera;

  useEffect(() => {
    start();
    return () => {
      stop();
    };
  }, [start, stop]);

  const onFileChosen = async (e) => {
    const file = e.target.files?.[0];
    e.target.value = "";
    if (!file) return;
    await stop();
    try {
      const text = await camera.scanImageFile(file, FILE_ELEMENT_ID);
      onDecode(text);
    } catch {
      onImageError();
    }
  };

  const errorKeys = camera.error ? CAMERA_ERROR_KEYS[camera.error] : null;
  const statusText =
    camera.state === CAMERA_STATE.STARTING
      ? t("camera_starting")
      : camera.state === CAMERA_STATE.READY
        ? t("ready_to_scan")
        : camera.state === CAMERA_STATE.PAUSED
          ? t("camera_paused")
          : "";

  return (
    <div className="qr-camera">
      <div className="qr-camera-viewport">
        {/* html5-qrcode injects the <video> here. */}
        <div id={CAMERA_ELEMENT_ID} className="qr-camera-feed" />

        {camera.state === CAMERA_STATE.READY && (
          <div className="qr-camera-overlay" aria-hidden="true">
            <div className="qr-scan-frame">
              <span className="qr-corner tl" />
              <span className="qr-corner tr" />
              <span className="qr-corner bl" />
              <span className="qr-corner br" />
              <span className="qr-scan-line" />
            </div>
          </div>
        )}

        {camera.state === CAMERA_STATE.STARTING && (
          <div className="qr-camera-message">
            <Loader2 className="qr-spin" size={34} />
            <b>{t("camera_starting")}</b>
          </div>
        )}

        {camera.state === CAMERA_STATE.PAUSED && (
          <div className="qr-camera-message">
            <CameraOff size={34} />
            <b>{t("camera_paused")}</b>
            <button type="button" className="primary-btn" onClick={start}>
              <RefreshCcw size={16} /> {t("try_again")}
            </button>
          </div>
        )}

        {camera.state === CAMERA_STATE.ERROR && errorKeys && (
          <div className="qr-camera-message" role="alert">
            <CameraOff size={38} />
            <b>{t(errorKeys[0])}</b>
            <p>{t(errorKeys[1])}</p>
            <div className="qr-camera-message-actions">
              <button type="button" className="primary-btn" onClick={start}>
                <RefreshCcw size={16} /> {t("try_again")}
              </button>
              <button type="button" className="secondary-btn" onClick={onManual}>
                <Keyboard size={16} /> {t("enter_qr_manually")}
              </button>
            </div>
          </div>
        )}
      </div>

      <p className="qr-camera-status" role="status" aria-live="polite">
        {camera.state === CAMERA_STATE.READY ? t("align_qr") : statusText}
      </p>

      <div className="qr-camera-controls">
        {camera.torchSupported && (
          <button
            type="button"
            className={`qr-control ${camera.torchOn ? "on" : ""}`}
            onClick={camera.toggleTorch}
            aria-pressed={camera.torchOn}
            aria-label={t("flash")}
          >
            {camera.torchOn ? <Flashlight size={20} /> : <FlashlightOff size={20} />}
            <span>{t("flash")}</span>
          </button>
        )}
        {camera.canSwitchCamera && (
          <button type="button" className="qr-control" onClick={camera.switchCamera} aria-label={t("switch_camera")}>
            <SwitchCamera size={20} />
            <span>{t("switch_camera")}</span>
          </button>
        )}
        <button type="button" className="qr-control" onClick={() => fileInputRef.current?.click()} aria-label={t("upload_qr_image")}>
          <ImageUp size={20} />
          <span>{t("upload_qr_image")}</span>
        </button>
        <button type="button" className="qr-control" onClick={onManual} aria-label={t("enter_qr_manually")}>
          <Keyboard size={20} />
          <span>{t("enter_qr_manually")}</span>
        </button>
      </div>

      <input ref={fileInputRef} type="file" accept="image/*" hidden onChange={onFileChosen} />
      <div id={FILE_ELEMENT_ID} hidden />
    </div>
  );
}
