import { useCallback, useEffect, useRef, useState } from "react";

// Speech-to-text with the browser's own Web Speech API (SpeechRecognition / webkitSpeechRecognition).
// The app only ever receives recognised TEXT: no audio is recorded, stored or sent to our servers.
// (Note: some browsers — e.g. Chrome — run recognition on their vendor's speech service.)

// App language -> recognition language.
export const SPEECH_LANG = { en: "en-IN", hi: "hi-IN", mr: "mr-IN" };

// Error codes surfaced to the UI (mapped to translated messages there).
export const VOICE_ERROR = {
  UNSUPPORTED: "unsupported",
  DENIED: "denied",
  NO_MIC: "no-mic",
  NO_SPEECH: "no-speech",
  NETWORK: "network",
  LANGUAGE: "language",
  FAILED: "failed",
};

// Lifecycle of a voice session, for the UI.
export const VOICE_STATUS = {
  IDLE: "idle",
  REQUESTING_PERMISSION: "requesting_permission", // start() called; waiting for the mic (and permission prompt)
  LISTENING: "listening", // audio is being captured
  PROCESSING: "processing", // stopped; the browser is finishing the last words
  SUCCESS: "success", // ended with recognised text in the input
  ERROR: "error",
  UNSUPPORTED: "unsupported",
};

// Stop on our own after this long, whatever the browser does (a stuck session never keeps the mic open).
export const MAX_SESSION_MS = 60_000;

function recognitionClass() {
  if (typeof window === "undefined") return null;
  return window.SpeechRecognition || window.webkitSpeechRecognition || null;
}

export function mapRecognitionError(code) {
  switch (code) {
    case "not-allowed":
    case "service-not-allowed":
      return VOICE_ERROR.DENIED;
    case "audio-capture":
      return VOICE_ERROR.NO_MIC;
    case "no-speech":
      return VOICE_ERROR.NO_SPEECH;
    case "network":
      return VOICE_ERROR.NETWORK;
    case "language-not-supported":
    case "bad-grammar":
      return VOICE_ERROR.LANGUAGE;
    case "aborted":
      return null; // our own cancel/stop
    default:
      return VOICE_ERROR.FAILED;
  }
}

/**
 * useSpeechRecognition({ lang, onTranscript })
 *   supported        — the browser has speech recognition
 *   isListening      — a session is running
 *   transcript       — text recognised in the current session (final + in-progress)
 *   error            — a VOICE_ERROR code, or null
 *   startListening() / stopListening() (keep the text) / cancelListening() (discard it)
 * `onTranscript(text)` is called with the session's text as it grows (interim results included), so the
 * caller can show it live in its own input. One recognition object per session; everything is released on
 * stop, cancel, language change and unmount.
 */
export function useSpeechRecognition({ lang = "en-IN", onTranscript } = {}) {
  const Recognition = recognitionClass();
  const supported = Boolean(Recognition);
  const [status, setStatus] = useState(supported ? VOICE_STATUS.IDLE : VOICE_STATUS.UNSUPPORTED);
  const [isListening, setIsListening] = useState(false);
  const [transcript, setTranscript] = useState("");
  const [error, setError] = useState(null);

  const recognitionRef = useRef(null);
  const timerRef = useRef(null);
  const cancelledRef = useRef(false);
  const heardRef = useRef(false);
  const onTranscriptRef = useRef(onTranscript);
  onTranscriptRef.current = onTranscript;

  const release = useCallback(() => {
    clearTimeout(timerRef.current);
    const recognition = recognitionRef.current;
    recognitionRef.current = null;
    if (recognition) {
      recognition.onresult = recognition.onerror = recognition.onend = recognition.onstart = recognition.onaudiostart = null;
    }
    return recognition;
  }, []);

  const stopListening = useCallback(() => {
    const recognition = recognitionRef.current;
    if (!recognition) return;
    setStatus(VOICE_STATUS.PROCESSING);
    try {
      recognition.stop(); // delivers any final result, then onend
    } catch {
      release();
      setIsListening(false);
      setStatus(VOICE_STATUS.IDLE);
    }
  }, [release]);

  const cancelListening = useCallback(() => {
    cancelledRef.current = true;
    const recognition = release();
    try {
      recognition?.abort();
    } catch {
      // already stopped
    }
    setIsListening(false);
    setTranscript("");
    setStatus(VOICE_STATUS.IDLE);
  }, [release]);

  const startListening = useCallback(() => {
    setError(null);
    if (!Recognition) {
      setError(VOICE_ERROR.UNSUPPORTED);
      setStatus(VOICE_STATUS.UNSUPPORTED);
      return;
    }
    if (recognitionRef.current) return; // already listening

    const recognition = new Recognition();
    recognition.lang = lang;
    recognition.continuous = true; // keep listening across short pauses until the user stops
    recognition.interimResults = true; // show words as they are recognised
    recognition.maxAlternatives = 1;
    cancelledRef.current = false;
    heardRef.current = false;
    let finalText = "";

    recognition.onresult = (event) => {
      let interim = "";
      for (let i = event.resultIndex; i < event.results.length; i += 1) {
        const piece = event.results[i][0]?.transcript ?? "";
        if (event.results[i].isFinal) finalText = `${finalText} ${piece}`.trim();
        else interim += piece;
      }
      const text = `${finalText} ${interim}`.replace(/\s+/g, " ").trim();
      if (text) heardRef.current = true;
      setTranscript(text);
      if (!cancelledRef.current) onTranscriptRef.current?.(text);
    };
    let failed = false;
    const markListening = () => {
      if (recognitionRef.current === recognition) setStatus(VOICE_STATUS.LISTENING);
    };
    recognition.onaudiostart = markListening; // the microphone is live (permission granted)
    recognition.onstart = markListening;
    recognition.onerror = (event) => {
      const code = mapRecognitionError(event.error);
      if (code && !cancelledRef.current) {
        failed = true;
        setError(code);
        setStatus(VOICE_STATUS.ERROR);
      }
    };
    recognition.onend = () => {
      release();
      setIsListening(false);
      if (!failed && !cancelledRef.current) setStatus(heardRef.current ? VOICE_STATUS.SUCCESS : VOICE_STATUS.IDLE);
    };

    recognitionRef.current = recognition;
    setStatus(VOICE_STATUS.REQUESTING_PERMISSION); // before start(): onstart may fire synchronously
    try {
      recognition.start(); // the browser asks for microphone permission the first time
      setIsListening(true);
      setTranscript("");
      timerRef.current = setTimeout(() => {
        if (recognitionRef.current === recognition) {
          if (!heardRef.current) setError(VOICE_ERROR.NO_SPEECH);
          stopListening();
        }
      }, MAX_SESSION_MS);
    } catch {
      release();
      setIsListening(false);
      setError(VOICE_ERROR.FAILED);
      setStatus(VOICE_STATUS.ERROR);
    }
  }, [Recognition, lang, release, stopListening]);

  // A language change ends the running session, so the next one uses the new language.
  useEffect(() => {
    if (recognitionRef.current) stopListening();
  }, [lang, stopListening]);

  // Never leave the microphone open after the chat closes.
  useEffect(
    () => () => {
      cancelledRef.current = true;
      const recognition = release();
      try {
        recognition?.abort();
      } catch {
        // already stopped
      }
    },
    [release],
  );

  const clearError = useCallback(() => {
    setError(null);
    setStatus((s) => (s === VOICE_STATUS.ERROR ? VOICE_STATUS.IDLE : s));
  }, []);

  return {
    supported,
    isSupported: supported,
    status,
    isListening,
    transcript,
    error,
    startListening,
    stopListening,
    cancelListening,
    clearError,
  };
}
