// Decodes QR codes off the main thread so the camera preview never stutters.
// Receives a small, already-cropped RGBA frame; returns the decoded text or null.
import jsQR from "jsqr";

// Light-on-dark codes (a phone showing the QR in dark mode): flip the pixels and read normally.
// Not jsQR's own "onlyInvert" mode, which crashes in jsQR 1.4.0's locator on such frames.
function invertInPlace(pixels) {
  for (let i = 0; i < pixels.length; i += 4) {
    pixels[i] = 255 - pixels[i];
    pixels[i + 1] = 255 - pixels[i + 1];
    pixels[i + 2] = 255 - pixels[i + 2];
  }
}

self.onmessage = (event) => {
  const { id, width, height, buffer, invert } = event.data;
  let text = null;
  try {
    const pixels = new Uint8ClampedArray(buffer);
    if (invert) invertInPlace(pixels);
    const code = jsQR(pixels, width, height, { inversionAttempts: "dontInvert" });
    text = code?.data || null;
  } catch {
    text = null; // jsQR can throw on unusual frames: that frame is just "no QR"
  }
  self.postMessage({ id, text });
};
