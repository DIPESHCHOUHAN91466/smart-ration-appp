import { useCallback, useEffect, useRef, useState } from "react";
import { Html5Qrcode, Html5QrcodeSupportedFormats } from "html5-qrcode";

// Camera states surfaced to the UI.
export const CAMERA_STATE = {
  IDLE: "IDLE",
  STARTING: "STARTING",
  READY: "READY", // camera live, analysing frames
  PAUSED: "PAUSED", // tab hidden — camera released, resumes on return
  ERROR: "ERROR",
};

// Camera error codes (mapped to i18n keys by the UI).
export const CAMERA_ERROR = {
  DENIED: "CAMERA_DENIED",
  NOT_FOUND: "CAMERA_NOT_FOUND",
  IN_USE: "CAMERA_IN_USE",
  INSECURE: "CAMERA_INSECURE",
  UNSUPPORTED: "CAMERA_UNSUPPORTED",
  FAILED: "CAMERA_FAILED",
};

const SCANNER_CONFIG = {
  verbose: false,
  formatsToSupport: [Html5QrcodeSupportedFormats.QR_CODE],
  // Uses the browser's native BarcodeDetector (Chrome/Edge/Android) when
  // present — much cheaper than the JS decoder on every frame.
  experimentalFeatures: { useBarCodeDetectorIfSupported: true },
};

// No qrbox / aspectRatio: the whole frame is analysed and the <video> is
// free to fill its container (the on-screen frame is only a visual guide).
const START_CONFIG = { fps: 10, disableFlip: false };

function classifyCameraError(error) {
  const text = `${error?.name ?? ""} ${error?.message ?? ""} ${typeof error === "string" ? error : ""}`;
  if (/NotAllowedError|PermissionDenied|Permission denied|permission/i.test(text)) return CAMERA_ERROR.DENIED;
  if (/NotFoundError|DevicesNotFound|OverconstrainedError|Requested device not found|no camera/i.test(text)) return CAMERA_ERROR.NOT_FOUND;
  if (/NotReadableError|TrackStartError|Could not start video source|in use/i.test(text)) return CAMERA_ERROR.IN_USE;
  if (/SecurityError|secure context|insecure/i.test(text)) return CAMERA_ERROR.INSECURE;
  return CAMERA_ERROR.FAILED;
}

/**
 * Drives one html5-qrcode instance bound to the element with `elementId`.
 * `onDecode(text)` fires at most once per start(): the first decoded frame
 * locks the scanner and releases the camera, so the same QR can't trigger
 * duplicate verification requests. Call start() again to scan another.
 */
export function useQrScanner({ elementId, onDecode }) {
  const [state, setState] = useState(CAMERA_STATE.IDLE);
  const [error, setError] = useState(null);
  const [cameras, setCameras] = useState([]);
  const [torchSupported, setTorchSupported] = useState(false);
  const [torchOn, setTorchOn] = useState(false);

  const scannerRef = useRef(null);
  const lockedRef = useRef(false);
  const cameraIndexRef = useRef(-1); // -1 = "rear camera via facingMode"
  const wantRunningRef = useRef(false);
  const queueRef = useRef(Promise.resolve());
  const camerasRef = useRef([]);
  const onDecodeRef = useRef(onDecode);
  onDecodeRef.current = onDecode;

  // html5-qrcode throws if start/stop overlap, so every transition is queued.
  const enqueue = useCallback((task) => {
    queueRef.current = queueRef.current.then(task, task);
    return queueRef.current;
  }, []);

  const releaseCamera = useCallback(async () => {
    const scanner = scannerRef.current;
    scannerRef.current = null;
    setTorchSupported(false);
    setTorchOn(false);
    if (!scanner) return;
    try {
      if (scanner.isScanning) await scanner.stop();
      scanner.clear();
    } catch {
      // Already stopped / element gone — nothing left to release.
    }
  }, []);

  const startInternal = useCallback(async () => {
    await releaseCamera();

    if (typeof window !== "undefined" && window.isSecureContext === false) {
      setError(CAMERA_ERROR.INSECURE);
      setState(CAMERA_STATE.ERROR);
      return;
    }
    if (!navigator.mediaDevices?.getUserMedia) {
      setError(CAMERA_ERROR.UNSUPPORTED);
      setState(CAMERA_STATE.ERROR);
      return;
    }
    if (!document.getElementById(elementId)) return;

    setError(null);
    setState(CAMERA_STATE.STARTING);
    lockedRef.current = false;

    const scanner = new Html5Qrcode(elementId, SCANNER_CONFIG);
    scannerRef.current = scanner;

    const onSuccess = (decodedText) => {
      if (lockedRef.current) return;
      lockedRef.current = true;
      wantRunningRef.current = false;
      enqueue(async () => {
        await releaseCamera();
        setState(CAMERA_STATE.IDLE);
      });
      onDecodeRef.current?.(decodedText);
    };

    const knownCameras = camerasRef.current;
    const primary =
      cameraIndexRef.current >= 0 && knownCameras[cameraIndexRef.current]
        ? { deviceId: { exact: knownCameras[cameraIndexRef.current].id } }
        : { facingMode: "environment" };

    try {
      try {
        await scanner.start(primary, START_CONFIG, onSuccess, () => {});
      } catch (err) {
        // Laptops/desktops often have no "environment" camera: fall back to
        // any camera rather than failing outright.
        const code = classifyCameraError(err);
        if (code !== CAMERA_ERROR.NOT_FOUND || !primary.facingMode) throw err;
        await scanner.start({ facingMode: "user" }, START_CONFIG, onSuccess, () => {});
      }
    } catch (err) {
      if (scannerRef.current === scanner) scannerRef.current = null;
      try {
        scanner.clear();
      } catch {
        // ignore
      }
      setError(classifyCameraError(err));
      setState(CAMERA_STATE.ERROR);
      return;
    }

    // Closed or tab hidden while the camera was starting up.
    if (!wantRunningRef.current || scannerRef.current !== scanner) {
      await releaseCamera();
      return;
    }

    setState(CAMERA_STATE.READY);

    try {
      const torch = scanner.getRunningTrackCameraCapabilities().torchFeature();
      setTorchSupported(torch.isSupported());
    } catch {
      setTorchSupported(false);
    }

    // Labels/ids are only available after permission is granted.
    if (knownCameras.length === 0) {
      Html5Qrcode.getCameras()
        .then((list) => {
          camerasRef.current = list || [];
          setCameras(camerasRef.current);
        })
        .catch(() => {});
    }
  }, [elementId, enqueue, releaseCamera]);

  const start = useCallback(() => {
    wantRunningRef.current = true;
    return enqueue(startInternal);
  }, [enqueue, startInternal]);

  const stop = useCallback(() => {
    wantRunningRef.current = false;
    return enqueue(async () => {
      await releaseCamera();
      setState(CAMERA_STATE.IDLE);
    });
  }, [enqueue, releaseCamera]);

  const switchCamera = useCallback(() => {
    const list = camerasRef.current;
    if (list.length < 2) return Promise.resolve();
    if (cameraIndexRef.current < 0) {
      // Started on the rear camera via facingMode: switch to a front one first.
      const front = list.findIndex((c) => /front|user|facetime/i.test(c.label));
      cameraIndexRef.current = front >= 0 ? front : 1;
    } else {
      cameraIndexRef.current = (cameraIndexRef.current + 1) % list.length;
    }
    return start();
  }, [start]);

  const toggleTorch = useCallback(async () => {
    const scanner = scannerRef.current;
    if (!scanner || !torchSupported) return;
    try {
      const torch = scanner.getRunningTrackCameraCapabilities().torchFeature();
      await torch.apply(!torchOn);
      setTorchOn(!torchOn);
    } catch {
      setTorchSupported(false);
    }
  }, [torchOn, torchSupported]);

  // Decode a QR from an uploaded/captured image — no live camera needed.
  const scanImageFile = useCallback(
    async (file, fileElementId) => {
      const reader = new Html5Qrcode(fileElementId, SCANNER_CONFIG);
      try {
        return await reader.scanFile(file, false);
      } finally {
        try {
          reader.clear();
        } catch {
          // ignore
        }
      }
    },
    [],
  );

  // Release the camera when the tab is hidden, resume when it's back.
  useEffect(() => {
    const onVisibility = () => {
      if (document.hidden) {
        if (scannerRef.current) {
          enqueue(async () => {
            await releaseCamera();
            setState(CAMERA_STATE.PAUSED);
          });
        }
      } else if (wantRunningRef.current) {
        enqueue(startInternal);
      }
    };
    document.addEventListener("visibilitychange", onVisibility);
    return () => document.removeEventListener("visibilitychange", onVisibility);
  }, [enqueue, releaseCamera, startInternal]);

  // Never leave the camera (and its LED) on after unmount.
  useEffect(
    () => () => {
      wantRunningRef.current = false;
      enqueue(releaseCamera);
    },
    [enqueue, releaseCamera],
  );

  return {
    state,
    error,
    cameras,
    canSwitchCamera: cameras.length > 1,
    torchSupported,
    torchOn,
    start,
    stop,
    switchCamera,
    toggleTorch,
    scanImageFile,
  };
}
