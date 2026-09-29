// Local, in-browser QR decoding for the scanner (camera frames and uploaded images).
// Nothing here talks to the server: only the decoded text is sent for verification.
//
// Strategy (fast on every device):
//  1. The browser's native BarcodeDetector when it supports QR (Android, macOS, ChromeOS…).
//  2. Otherwise jsQR in a Web Worker (Chrome on Windows, Firefox, older Safari).
// Each attempt decodes one small view of the current frame, cycling through:
//   box     — the scan-box region with generous tolerance (most QRs are found here, ~20 ms)
//   zoom    — the centre only, enlarged, so a QR held far away still has enough pixels per module
//   inverse — the scan box again, read as light-on-dark (a phone showing the QR in dark mode)
//   full    — the whole frame, for a QR held outside the box

import jsQR from "jsqr";

// Square region around the centre of the frame, as a fraction of the shorter side.
export const ROI_FRACTION = 0.8;
// Working size of the cropped square handed to the decoder (px). QR modules stay ≥ ~3 px wide.
export const ROI_SIZE = 480;
// The "zoom" view: this fraction of the shorter side, scaled to ROI_SIZE (a far-away QR).
export const ZOOM_FRACTION = 0.45;
// Longest side of the whole-frame view (px).
export const FULL_FRAME_SIZE = 960;
// The order in which views are tried, one per frame.
export const VIEW_CYCLE = ["box", "zoom", "inverse", "full"];
// Each view is exactly one jsQR pass, so every frame stays cheap (~15–40 ms in the worker).

/** Pure, for tests: the source/destination rectangle of `view` for a width×height frame. */
export function viewRegion(view, width, height) {
  if (view === "full") return wholeFrame(width, height);
  if (view === "zoom") {
    const r = centreCrop(width, height, ZOOM_FRACTION, ROI_SIZE);
    return { ...r, dw: ROI_SIZE, dh: ROI_SIZE }; // enlarge: more pixels per module for jsQR
  }
  return centreCrop(width, height);
}

/** The centre crop of a width×height frame, scaled to fit `target` px. Pure, for tests. */
export function centreCrop(width, height, fraction = ROI_FRACTION, target = ROI_SIZE) {
  const side = Math.max(1, Math.round(Math.min(width, height) * fraction));
  const sx = Math.round((width - side) / 2);
  const sy = Math.round((height - side) / 2);
  const out = Math.min(side, target);
  return { sx, sy, sw: side, sh: side, dw: out, dh: out };
}

/** The whole frame scaled so its longest side is at most `target` px. Pure, for tests. */
export function wholeFrame(width, height, target = FULL_FRAME_SIZE) {
  const scale = Math.min(1, target / Math.max(width, height));
  return { sx: 0, sy: 0, sw: width, sh: height, dw: Math.max(1, Math.round(width * scale)), dh: Math.max(1, Math.round(height * scale)) };
}

let nativeSupport; // Promise<boolean>, resolved once per page

function nativeQrSupported() {
  if (nativeSupport) return nativeSupport;
  nativeSupport = (async () => {
    try {
      if (typeof window === "undefined" || !("BarcodeDetector" in window)) return false;
      const formats = await window.BarcodeDetector.getSupportedFormats?.();
      return Array.isArray(formats) && formats.includes("qr_code");
    } catch {
      return false;
    }
  })();
  return nativeSupport;
}

function makeCanvas() {
  const canvas = document.createElement("canvas");
  // Tells the browser we read pixels back every frame (keeps the canvas on the CPU: faster getImageData).
  const ctx = canvas.getContext("2d", { willReadFrequently: true, alpha: false });
  return { canvas, ctx };
}

function draw(ctx, canvas, source, r) {
  if (canvas.width !== r.dw) canvas.width = r.dw;
  if (canvas.height !== r.dh) canvas.height = r.dh;
  ctx.drawImage(source, r.sx, r.sy, r.sw, r.sh, 0, 0, r.dw, r.dh);
}

/**
 * A decoder for a live video stream. `decodeFrame(video)` resolves to the QR text or null.
 * Only one frame is ever in flight; call `close()` when the camera stops.
 */
export async function createFrameDecoder() {
  const native = await nativeQrSupported();
  const { canvas, ctx } = makeCanvas();
  let attempt = 0;

  if (native) {
    const detector = new window.BarcodeDetector({ formats: ["qr_code"] });
    return {
      engine: "BarcodeDetector",
      async decodeFrame(video) {
        const w = video.videoWidth;
        const h = video.videoHeight;
        if (!w || !h) return null;
        attempt += 1;
        // The native detector is fast enough for the whole frame; the crop pass helps small QRs.
        const full = attempt % 2 === 0;
        draw(ctx, canvas, video, full ? wholeFrame(w, h, 960) : centreCrop(w, h, ROI_FRACTION, 720));
        const found = await detector.detect(canvas);
        return found[0]?.rawValue || null;
      },
      close() {},
    };
  }

  const worker = new Worker(new URL("./qrDecode.worker.js", import.meta.url), { type: "module" });
  let nextId = 0;
  const pending = new Map();
  worker.onmessage = (e) => {
    const resolve = pending.get(e.data.id);
    pending.delete(e.data.id);
    resolve?.(e.data.text);
  };
  worker.onerror = () => {
    for (const resolve of pending.values()) resolve(null);
    pending.clear();
  };

  return {
    engine: "jsQR (worker)",
    decodeFrame(video) {
      const w = video.videoWidth;
      const h = video.videoHeight;
      if (!w || !h) return Promise.resolve(null);
      const view = VIEW_CYCLE[attempt % VIEW_CYCLE.length];
      attempt += 1;
      const region = viewRegion(view, w, h);
      draw(ctx, canvas, video, region);
      const { data } = ctx.getImageData(0, 0, region.dw, region.dh);
      const id = ++nextId;
      return new Promise((resolve) => {
        pending.set(id, resolve);
        // The pixel buffer is transferred, not copied.
        worker.postMessage(
          { id, width: region.dw, height: region.dh, buffer: data.buffer, invert: view === "inverse" },
          [data.buffer],
        );
      });
    },
    close() {
      worker.terminate();
      for (const resolve of pending.values()) resolve(null);
      pending.clear();
    },
  };
}

/**
 * Decode a QR from an uploaded/captured image file, locally. Resolves to the text; rejects when
 * no QR is found. Tries the native detector, then jsQR at a few sizes (large photos are downscaled
 * first: faster, and phone photos decode better that way).
 */
export async function decodeImageFile(file) {
  const bitmap = await createImageBitmap(file);
  try {
    if (await nativeQrSupported()) {
      const found = await new window.BarcodeDetector({ formats: ["qr_code"] }).detect(bitmap);
      if (found[0]?.rawValue) return found[0].rawValue;
    }
    const { canvas, ctx } = makeCanvas();
    const longest = Math.max(bitmap.width, bitmap.height);
    const sizes = [...new Set([Math.min(longest, 1024), Math.min(longest, 640), Math.min(longest, 1600)])];
    for (const size of sizes) {
      const region = wholeFrame(bitmap.width, bitmap.height, size);
      draw(ctx, canvas, bitmap, region);
      const { data } = ctx.getImageData(0, 0, region.dw, region.dh);
      let code = null;
      try {
        code = jsQR(data, region.dw, region.dh, { inversionAttempts: "attemptBoth" });
      } catch {
        code = null; // jsQR can throw on unusual images; try the next size
      }
      if (code?.data) return code.data;
    }
    throw new Error("No QR code found in the image.");
  } finally {
    bitmap.close?.();
  }
}
