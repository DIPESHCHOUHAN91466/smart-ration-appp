import { useCallback, useEffect, useRef, useState } from "react";
import { createFrameDecoder, decodeImageFile } from "../features/qr/qrDecoder";
import { qrClear, qrLog, qrLogValue, qrMark } from "../features/qr/qrTiming";

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

// Upper bound on the wait between decode attempts when frame callbacks are not firing.
const FRAME_FALLBACK_MS = 50;

// 720p is plenty for a QR held near the camera and keeps every frame cheap to process; `ideal`
// (never `exact`) so devices that can't do it still start, and laptops without a rear camera
// simply get their only camera instead of an error.
export function videoConstraints(deviceId) {
  return {
    ...(deviceId ? { deviceId: { exact: deviceId } } : { facingMode: { ideal: "environment" } }),
    width: { ideal: 1280 },
    height: { ideal: 720 },
    frameRate: { ideal: 30 },
  };
}

export function classifyCameraError(error) {
  const text = `${error?.name ?? ""} ${error?.message ?? ""} ${typeof error === "string" ? error : ""}`;
  if (/NotAllowedError|PermissionDenied|Permission denied|permission/i.test(text)) return CAMERA_ERROR.DENIED;
  if (/NotFoundError|DevicesNotFound|OverconstrainedError|Requested device not found|no camera/i.test(text)) return CAMERA_ERROR.NOT_FOUND;
  if (/NotReadableError|TrackStartError|AbortError|Could not start video source|in use/i.test(text)) return CAMERA_ERROR.IN_USE;
  if (/SecurityError|secure context|insecure/i.test(text)) return CAMERA_ERROR.INSECURE;
  return CAMERA_ERROR.FAILED;
}

/**
 * Live QR scanning on a <video> element (attach `videoRef`). Frames are decoded locally
 * (native BarcodeDetector, else jsQR in a worker) back-to-back: the next frame is taken as soon
 * as the previous decode finishes — no fixed polling interval, never more than one in flight.
 *
 * `onDecode(text)` fires at most once per start(): the first decoded frame locks the scanner and
 * stops the camera, so the same QR can't trigger duplicate verification requests. Call start()
 * again (a new session) to scan another.
 */
export function useQrScanner({ onDecode }) {
  const [state, setState] = useState(CAMERA_STATE.IDLE);
  const [error, setError] = useState(null);
  const [cameras, setCameras] = useState([]);
  const [torchSupported, setTorchSupported] = useState(false);
  const [torchOn, setTorchOn] = useState(false);

  const videoRef = useRef(null);
  const streamRef = useRef(null);
  const decoderRef = useRef(null); // Promise of the decoder, created once and reused across sessions
  const sessionRef = useRef(0); // bumped by every start/stop: stale async work checks it and bails out
  const lockedRef = useRef(false);
  const wantRunningRef = useRef(false);
  const deviceIdRef = useRef(null); // null = "rear camera via facingMode"
  const camerasRef = useRef([]);
  const onDecodeRef = useRef(onDecode);
  onDecodeRef.current = onDecode;

  const releaseCamera = useCallback(() => {
    const stream = streamRef.current;
    streamRef.current = null;
    stream?.getTracks().forEach((track) => track.stop());
    if (videoRef.current) videoRef.current.srcObject = null;
    setTorchSupported(false);
    setTorchOn(false);
  }, []);

  const getDecoder = useCallback(() => {
    if (!decoderRef.current) {
      decoderRef.current = createFrameDecoder().catch((err) => {
        decoderRef.current = null;
        throw err;
      });
    }
    return decoderRef.current;
  }, []);

  const scanLoop = useCallback((session, decoder) => {
    const video = videoRef.current;
    let firstAttempt = true;
    const next = () => {
      if (session !== sessionRef.current || lockedRef.current || !videoRef.current) return;
      // Decode on the next *new* camera frame where supported (else the next paint) — or after
      // FRAME_FALLBACK_MS, whichever comes first: browsers stop painting a window that is covered
      // by another one (while still reporting it "visible"), and then frame callbacks never fire.
      let done = false;
      const run = () => {
        if (done) return;
        done = true;
        clearTimeout(timer);
        tick();
      };
      const timer = setTimeout(run, FRAME_FALLBACK_MS);
      if (video.requestVideoFrameCallback) video.requestVideoFrameCallback(run);
      else requestAnimationFrame(run);
    };
    const tick = async () => {
      if (session !== sessionRef.current || lockedRef.current) return;
      let text = null;
      if (video.readyState >= 2) {
        if (firstAttempt) {
          firstAttempt = false;
          qrMark("scanStart");
        }
        try {
          text = await decoder.decodeFrame(video);
        } catch {
          text = null; // one bad frame never stops the scanner
        }
      }
      if (text && session === sessionRef.current && !lockedRef.current) {
        lockedRef.current = true; // scanner locked: exactly one verification per session
        wantRunningRef.current = false;
        sessionRef.current += 1;
        qrMark("detected");
        qrLog("Detected (from first frame)", "scanStart", "detected");
        releaseCamera();
        setState(CAMERA_STATE.IDLE);
        onDecodeRef.current?.(text);
        return;
      }
      next();
    };
    next();
  }, [releaseCamera]);

  const start = useCallback(async () => {
    wantRunningRef.current = true;
    const session = ++sessionRef.current;
    lockedRef.current = false;
    releaseCamera();

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

    setError(null);
    setState(CAMERA_STATE.STARTING);
    qrClear("scanStart", "detected");
    qrMark("cameraRequested");

    let stream;
    let decoder;
    try {
      // Camera and decoder start together, not one after the other.
      [stream, decoder] = await Promise.all([
        navigator.mediaDevices.getUserMedia({ video: videoConstraints(deviceIdRef.current), audio: false }),
        getDecoder(),
      ]);
    } catch (err) {
      if (session !== sessionRef.current) return;
      setError(classifyCameraError(err));
      setState(CAMERA_STATE.ERROR);
      return;
    }

    // Closed, restarted or tab hidden while the camera was starting.
    if (session !== sessionRef.current || !wantRunningRef.current || !videoRef.current) {
      stream.getTracks().forEach((track) => track.stop());
      return;
    }

    streamRef.current = stream;
    const video = videoRef.current;
    video.srcObject = stream;
    try {
      await video.play();
    } catch {
      // Autoplay of a muted inline video is allowed everywhere we support; frames still arrive.
    }
    if (session !== sessionRef.current) return;

    const [track] = stream.getVideoTracks();
    const caps = track?.getCapabilities?.() ?? {};
    if (Array.isArray(caps.focusMode) && caps.focusMode.includes("continuous")) {
      track.applyConstraints({ advanced: [{ focusMode: "continuous" }] }).catch(() => {});
    }
    setTorchSupported(Boolean(caps.torch));

    qrMark("cameraReady");
    qrLog("Camera started", "cameraRequested", "cameraReady");
    const settings = track?.getSettings?.() ?? {};
    qrLogValue("Camera", `${settings.width ?? "?"}x${settings.height ?? "?"} @ ${Math.round(settings.frameRate ?? 0) || "?"}fps, decoder ${decoder.engine}`);
    setState(CAMERA_STATE.READY);

    // Labels/ids are only available after permission is granted.
    if (camerasRef.current.length === 0 && navigator.mediaDevices.enumerateDevices) {
      navigator.mediaDevices
        .enumerateDevices()
        .then((devices) => {
          camerasRef.current = devices.filter((d) => d.kind === "videoinput").map((d) => ({ id: d.deviceId, label: d.label }));
          setCameras(camerasRef.current);
        })
        .catch(() => {});
    }

    scanLoop(session, decoder);
  }, [getDecoder, releaseCamera, scanLoop]);

  const stop = useCallback(() => {
    wantRunningRef.current = false;
    sessionRef.current += 1;
    releaseCamera();
    setState(CAMERA_STATE.IDLE);
  }, [releaseCamera]);

  const switchCamera = useCallback(() => {
    const list = camerasRef.current;
    if (list.length < 2) return Promise.resolve();
    const current = streamRef.current?.getVideoTracks()[0]?.getSettings?.().deviceId ?? deviceIdRef.current;
    const index = list.findIndex((c) => c.id === current);
    deviceIdRef.current = list[(index + 1) % list.length].id;
    return start();
  }, [start]);

  const toggleTorch = useCallback(async () => {
    const track = streamRef.current?.getVideoTracks()[0];
    if (!track || !torchSupported) return;
    try {
      await track.applyConstraints({ advanced: [{ torch: !torchOn }] });
      setTorchOn(!torchOn);
    } catch {
      setTorchSupported(false);
    }
  }, [torchOn, torchSupported]);

  // Decode a QR from an uploaded/captured image — locally, no live camera or server upload.
  const scanImageFile = useCallback((file) => decodeImageFile(file), []);

  // Release the camera when the tab is hidden, resume when it's back.
  useEffect(() => {
    const onVisibility = () => {
      if (document.hidden) {
        if (streamRef.current) {
          sessionRef.current += 1;
          releaseCamera();
          setState(CAMERA_STATE.PAUSED);
        }
      } else if (wantRunningRef.current) {
        start();
      }
    };
    document.addEventListener("visibilitychange", onVisibility);
    return () => document.removeEventListener("visibilitychange", onVisibility);
  }, [releaseCamera, start]);

  // Never leave the camera (and its LED) or the decoder worker running after unmount.
  useEffect(
    () => () => {
      wantRunningRef.current = false;
      sessionRef.current += 1;
      releaseCamera();
      decoderRef.current?.then((d) => d.close()).catch(() => {});
      decoderRef.current = null;
    },
    [releaseCamera],
  );

  return {
    videoRef,
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
