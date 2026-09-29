import { act, renderHook, waitFor } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import QRCode from "qrcode";
import jsQR from "jsqr";
import { centreCrop, viewRegion, wholeFrame, ROI_FRACTION, ROI_SIZE, VIEW_CYCLE, ZOOM_FRACTION } from "../../src/features/qr/qrDecoder";

// A Smart Ration envelope in the real shape (test values only).
const ENVELOPE =
  '{"version":"1.0","project":"SMART_RATION_HSD2C","type":"RATION_TOKEN","reference":"SRQR-10102-673A1AF50F6DADE9",' +
  '"token":"SR-2026-010102","issuedAt":"2026-09-29T07:15:48Z","expiresAt":"2026-09-30T00:00:00Z","signature":"A5279C77071B68A563AFD9090A07A83F"}';

// Render a QR as RGBA pixels (dark on white, `scale` px per module, 4-module quiet zone), optionally
// placed at (ox, oy) on a larger white canvas — i.e. what a camera frame looks like.
function qrPixels(text, { scale = 4, canvasW, canvasH, ox = 0, oy = 0 } = {}) {
  const qr = QRCode.create(text, { errorCorrectionLevel: "M" });
  const n = qr.modules.size;
  const side = (n + 8) * scale;
  const w = canvasW ?? side;
  const h = canvasH ?? side;
  const data = new Uint8ClampedArray(w * h * 4).fill(255);
  for (let y = 0; y < n; y++) {
    for (let x = 0; x < n; x++) {
      if (!qr.modules.get(y, x)) continue;
      for (let dy = 0; dy < scale; dy++) {
        for (let dx = 0; dx < scale; dx++) {
          const px = ox + (x + 4) * scale + dx;
          const py = oy + (y + 4) * scale + dy;
          const i = (py * w + px) * 4;
          data[i] = data[i + 1] = data[i + 2] = 0;
        }
      }
    }
  }
  return { data, width: w, height: h, side };
}

describe("scan region maths", () => {
  it("crops a centred square of the shorter side and caps its size", () => {
    const r = centreCrop(1280, 720);
    expect(r.sw).toBe(Math.round(720 * ROI_FRACTION));
    expect(r.sx).toBe(Math.round((1280 - r.sw) / 2));
    expect(r.sy).toBe(Math.round((720 - r.sh) / 2));
    expect(r.dw).toBe(ROI_SIZE);
  });

  it("never upscales a small frame", () => {
    expect(centreCrop(320, 240).dw).toBe(Math.round(240 * ROI_FRACTION));
    expect(wholeFrame(320, 240)).toMatchObject({ dw: 320, dh: 240 });
  });

  it("downscales the whole frame to the working size", () => {
    expect(wholeFrame(1920, 1080)).toMatchObject({ dw: 960, dh: 540 });
  });

  it("cycles box, zoom, inverse, full; zoom enlarges the centre for a distant QR", () => {
    expect(VIEW_CYCLE).toEqual(["box", "zoom", "inverse", "full"]);
    const zoom = viewRegion("zoom", 1280, 720);
    expect(zoom.sw).toBe(Math.round(720 * ZOOM_FRACTION));
    expect(zoom.dw).toBe(ROI_SIZE);
    expect(zoom.dw).toBeGreaterThan(zoom.sw);
  });
});

describe("local decoding (jsQR, the fallback used on Chrome for Windows)", () => {
  it("decodes a signed Smart Ration envelope exactly", () => {
    const { data, width, height } = qrPixels(ENVELOPE);
    expect(jsQR(data, width, height, { inversionAttempts: "dontInvert" })?.data).toBe(ENVELOPE);
  });

  it("finds the QR inside the centre crop of a 720p frame, fast", () => {
    // The QR placed in the middle of a 1280x720 "frame", as a customer would hold it.
    const probe = qrPixels(ENVELOPE, { scale: 5 });
    const frame = qrPixels(ENVELOPE, { scale: 5, canvasW: 1280, canvasH: 720, ox: Math.round((1280 - probe.side) / 2), oy: Math.round((720 - probe.side) / 2) });
    const r = centreCrop(1280, 720);
    // Crop without scaling (the browser scales with drawImage); jsQR on the cropped square.
    const crop = new Uint8ClampedArray(r.sw * r.sh * 4);
    for (let y = 0; y < r.sh; y++) {
      crop.set(frame.data.subarray(((r.sy + y) * 1280 + r.sx) * 4, ((r.sy + y) * 1280 + r.sx + r.sw) * 4), y * r.sw * 4);
    }
    const started = performance.now();
    const found = jsQR(crop, r.sw, r.sh, { inversionAttempts: "dontInvert" });
    const took = performance.now() - started;
    expect(found?.data).toBe(ENVELOPE);
    expect(took).toBeLessThan(500);
  });

  it("returns nothing for a frame without a QR", () => {
    const blank = new Uint8ClampedArray(200 * 200 * 4).fill(255);
    expect(jsQR(blank, 200, 200)).toBeNull();
  });
});

// ---------------------------------------------------------------- the camera hook

vi.mock("../../src/features/qr/qrDecoder", async (original) => {
  const actual = await original();
  return {
    ...actual,
    createFrameDecoder: vi.fn(async () => ({ engine: "test", decodeFrame: vi.fn(async () => ENVELOPE), close: vi.fn() })),
  };
});

describe("useQrScanner", () => {
  let track;
  beforeEach(() => {
    track = { stop: vi.fn(), getCapabilities: () => ({}), getSettings: () => ({ width: 1280, height: 720, frameRate: 30 }) };
    const stream = { getTracks: () => [track], getVideoTracks: () => [track] };
    vi.stubGlobal("navigator", {
      ...navigator,
      mediaDevices: { getUserMedia: vi.fn(async () => stream), enumerateDevices: vi.fn(async () => []) },
    });
    vi.stubGlobal("requestAnimationFrame", (cb) => setTimeout(cb, 0));
  });
  afterEach(() => vi.unstubAllGlobals());

  async function startScanner(onDecode) {
    const { useQrScanner, CAMERA_STATE } = await import("../../src/hooks/useQrScanner");
    const hook = renderHook(() => useQrScanner({ onDecode }));
    const video = document.createElement("video");
    Object.defineProperty(video, "readyState", { value: 4 });
    video.play = vi.fn(async () => {});
    hook.result.current.videoRef.current = video;
    await act(async () => {
      await hook.result.current.start();
    });
    return { hook, CAMERA_STATE };
  }

  it("asks for a 720p rear camera and decodes exactly once, then releases the camera", async () => {
    const onDecode = vi.fn();
    const { hook, CAMERA_STATE } = await startScanner(onDecode);
    await waitFor(() => expect(onDecode).toHaveBeenCalledTimes(1));
    expect(onDecode).toHaveBeenCalledWith(ENVELOPE);
    const constraints = navigator.mediaDevices.getUserMedia.mock.calls[0][0].video;
    expect(constraints).toMatchObject({ facingMode: { ideal: "environment" }, width: { ideal: 1280 }, height: { ideal: 720 } });
    // The same QR stays in view, but the scanner is locked: no second verification request.
    await new Promise((r) => setTimeout(r, 50));
    expect(onDecode).toHaveBeenCalledTimes(1);
    expect(track.stop).toHaveBeenCalled();
    expect(hook.result.current.state).toBe(CAMERA_STATE.IDLE);
  });

  it("a new session (reopened scanner) can scan the next customer", async () => {
    const onDecode = vi.fn();
    const { hook } = await startScanner(onDecode);
    await waitFor(() => expect(onDecode).toHaveBeenCalledTimes(1));
    await act(async () => {
      await hook.result.current.start();
    });
    await waitFor(() => expect(onDecode).toHaveBeenCalledTimes(2));
  });

  it("maps a denied permission to a clear error without retrying", async () => {
    navigator.mediaDevices.getUserMedia = vi.fn(async () => {
      throw Object.assign(new Error("Permission denied"), { name: "NotAllowedError" });
    });
    const onDecode = vi.fn();
    const { hook, CAMERA_STATE } = await startScanner(onDecode);
    expect(hook.result.current.state).toBe(CAMERA_STATE.ERROR);
    expect(hook.result.current.error).toBe("CAMERA_DENIED");
    expect(navigator.mediaDevices.getUserMedia).toHaveBeenCalledTimes(1);
    expect(onDecode).not.toHaveBeenCalled();
  });

  it("classifies the other camera failures", async () => {
    const { classifyCameraError } = await import("../../src/hooks/useQrScanner");
    expect(classifyCameraError({ name: "NotFoundError" })).toBe("CAMERA_NOT_FOUND");
    expect(classifyCameraError({ name: "NotReadableError" })).toBe("CAMERA_IN_USE");
    expect(classifyCameraError({ name: "SecurityError" })).toBe("CAMERA_INSECURE");
  });
});
