import 'dart:async';

import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_tts/flutter_tts.dart';
import 'package:speech_to_text/speech_to_text.dart';

/// Turns speech into text, in the app's language. Android's speech service does the recognition
/// (usually Google's, which may send the audio over the internet); nothing is recorded by the app.
abstract class VoiceInput {
  /// Starts listening. [onWords] receives the words so far, with done=true at the end; [onStopped] is
  /// called once listening ends for any reason. Returns false when voice input is not available
  /// (no permission, no speech service, or no microphone).
  Future<bool> start({required String language, required void Function(String words, bool done) onWords, required void Function() onStopped});

  Future<void> stop();
}

/// Reads text aloud in the app's language with the phone's text-to-speech voice.
abstract class Speaker {
  /// Completes when the reading has finished or was stopped. Returns false when the phone has no
  /// voice for [language].
  Future<bool> speak(String text, String language);

  Future<void> stop();
}

/// en / hi / mr as Indian locales for the speech services.
String speechLocale(String language, {String separator = '-'}) => switch (language) {
      'hi' => 'hi${separator}IN',
      'mr' => 'mr${separator}IN',
      _ => 'en${separator}IN',
    };

/// Text as it should be spoken: no emoji, bullets or extra blank lines.
String speakable(String text) => text
    .replaceAll(RegExp(r'[\u{1F000}-\u{1FAFF}\u{2600}-\u{27BF}\u{FE0F}]', unicode: true), '')
    .replaceAll('•', '')
    .replaceAll(RegExp(r'\n\s*\n+'), '\n')
    .trim();

class DeviceVoiceInput implements VoiceInput {
  final _speech = SpeechToText();
  bool? _ready;
  void Function()? _onStopped;

  @override
  Future<bool> start({required String language, required void Function(String words, bool done) onWords, required void Function() onStopped}) async {
    _ready ??= await _speech.initialize(
      onStatus: (status) {
        if (status == SpeechToText.doneStatus || status == SpeechToText.notListeningStatus) _finish();
      },
      onError: (_) => _finish(),
    );
    if (_ready != true) return false;
    _onStopped = onStopped;
    await _speech.listen(
      onResult: (r) => onWords(r.recognizedWords, r.finalResult),
      listenOptions: SpeechListenOptions(
        localeId: speechLocale(language, separator: '_'),
        partialResults: true,
        cancelOnError: true,
        listenMode: ListenMode.confirmation,
        pauseFor: const Duration(seconds: 3),
        listenFor: const Duration(seconds: 30),
      ),
    );
    return true;
  }

  void _finish() {
    final stopped = _onStopped;
    _onStopped = null;
    stopped?.call();
  }

  @override
  Future<void> stop() async {
    await _speech.stop();
    _finish();
  }
}

class DeviceSpeaker implements Speaker {
  final _tts = FlutterTts();
  bool _setUp = false;

  @override
  Future<bool> speak(String text, String language) async {
    final locale = speechLocale(language);
    // "Available" only means the engine supports the language; its voice may still be missing
    // (seen with Marathi on Google's engine), so the voice must also be installed on the phone.
    if (await _tts.isLanguageAvailable(locale) != true || await _tts.isLanguageInstalled(locale) != true) return false;
    if (!_setUp) {
      await _tts.awaitSpeakCompletion(true); // speak() then returns only when the reading ends
      _setUp = true;
    }
    await _tts.stop();
    await _tts.setLanguage(locale);

    // Safety net: if the engine never starts (or reports an error), give up instead of waiting forever.
    final started = Completer<bool>();
    _tts.setStartHandler(() {
      if (!started.isCompleted) started.complete(true);
    });
    _tts.setErrorHandler((_) {
      if (!started.isCompleted) started.complete(false);
    });
    final reading = _tts.speak(speakable(text));
    if (!await started.future.timeout(const Duration(seconds: 5), onTimeout: () => false)) {
      await _tts.stop();
      return false;
    }
    await reading;
    return true;
  }

  @override
  Future<void> stop() async => _tts.stop();
}

final voiceInputProvider = Provider<VoiceInput>((ref) => DeviceVoiceInput());

final speakerProvider = Provider<Speaker>((ref) {
  final speaker = DeviceSpeaker();
  ref.onDispose(speaker.stop);
  return speaker;
});
