// Development-only timing for the QR scanner ("[QR] Camera started: 320ms" …).
// Logs durations only — never the QR text or any customer data. Silent in production builds.

const marks = {};

export function qrMark(name) {
  marks[name] = performance.now();
}

export function qrClear(...names) {
  for (const name of names) delete marks[name];
}

export function qrLog(label, fromMark, toMark) {
  if (!import.meta.env.DEV) return;
  const from = marks[fromMark];
  const to = toMark ? marks[toMark] : performance.now();
  if (from === undefined || to === undefined) return;
  console.info(`[QR] ${label}: ${Math.round(to - from)}ms`);
}

export function qrLogValue(label, value) {
  if (!import.meta.env.DEV || value === undefined || value === null) return;
  console.info(`[QR] ${label}: ${value}`);
}
