import 'dart:async';

import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:smart_ration_mobile/app/routes.dart';
import 'package:smart_ration_mobile/features/booking/book_ration_screen.dart';
import 'package:smart_ration_mobile/features/help/help_chat_screen.dart';
import 'package:smart_ration_mobile/features/help/help_data.dart';
import 'package:smart_ration_mobile/features/help/voice.dart';

import '../support/fake_backend.dart';
import '../support/fake_help.dart';
import '../support/test_app.dart';

/// A microphone the test speaks into.
class FakeVoice implements VoiceInput {
  FakeVoice({this.available = true});

  final bool available;
  String? language;
  void Function(String, bool)? _onWords;
  void Function()? _onStopped;

  @override
  Future<bool> start({required String language, required void Function(String, bool) onWords, required void Function() onStopped}) async {
    if (!available) return false;
    this.language = language;
    _onWords = onWords;
    _onStopped = onStopped;
    return true;
  }

  void hear(String words, {bool done = false}) {
    _onWords?.call(words, done);
    if (done) stop();
  }

  @override
  Future<void> stop() async {
    final stopped = _onStopped;
    _onStopped = null;
    stopped?.call();
  }
}

/// A speaker that "reads" until the test says it has finished.
class FakeSpeaker implements Speaker {
  FakeSpeaker({this.hasVoice = true});

  final bool hasVoice;
  final spoken = <(String, String)>[];
  Completer<void>? _reading;

  @override
  Future<bool> speak(String text, String language) async {
    if (!hasVoice) return false;
    spoken.add((text, language));
    _reading = Completer<void>();
    await _reading!.future;
    return true;
  }

  void finish() {
    if (_reading != null && !_reading!.isCompleted) _reading!.complete();
  }

  @override
  Future<void> stop() async => finish();
}

/// Opens the app as the demo citizen and taps Help.
Future<FakeBackend> openHelp(WidgetTester tester, {String language = 'en', VoiceInput? voice, Speaker? speaker}) async {
  tester.view.physicalSize = const Size(1080, 3200);
  tester.view.devicePixelRatio = 2.0;
  addTearDown(tester.view.reset);
  final backend = FakeBackend(helpOrDemo);
  final app = await TestApp.build(backend, savedLanguage: language, signedInAs: citizen(), overrides: [
    voiceInputProvider.overrideWithValue(voice ?? FakeVoice()),
    speakerProvider.overrideWithValue(speaker ?? FakeSpeaker()),
  ]);
  await tester.pumpWidget(app.widget);
  await tester.pumpAndSettle();
  await tester.tap(find.byTooltip(language == 'mr' ? 'मदत' : 'Help'));
  await tester.pumpAndSettle();
  return backend;
}

Iterable<Object?> asked(FakeBackend b) => b.requests.where((r) => r.path == '/api/chatbot/message').map((r) => r.data);

void main() {
  test('assistant links open the matching app screen; unknown ones are dropped', () {
    expect(appRouteForHelpLink('/rural/book'), Routes.citizenBook);
    expect(appRouteForHelpLink('/rural/token/42'), Routes.citizenToken(42));
    expect(appRouteForHelpLink('/rural/verification'), Routes.citizenCard);
    expect(appRouteForHelpLink('/login'), Routes.login);
    expect(appRouteForHelpLink('/admin/users'), isNull);
  });

  test('read-aloud text has no emoji or bullets', () {
    expect(speakable('Namaste! 👋\n\n• Ration card\n• Eligibility'), 'Namaste! \n Ration card\n Eligibility');
  });

  testWidgets('welcome, a quick topic, then a related article', (tester) async {
    final backend = await openHelp(tester);

    expect(find.byType(HelpChatScreen), findsOneWidget);
    expect(backend.requests.singleWhere((r) => r.path == '/api/chatbot/welcome').queryParameters, {'language': 'en'});
    expect(find.textContaining('I am Ration Mitra (en).'), findsOneWidget);
    expect(find.textContaining("Don't type Aadhaar numbers, OTPs or passwords."), findsOneWidget);

    await tester.tap(find.widgetWithText(ActionChip, 'Documents'));
    await tester.pumpAndSettle();
    expect(asked(backend).single, {'language': 'en', 'topic': 'documents'});
    expect(find.text('Documents usually required'), findsOneWidget);

    await tester.tap(find.widgetWithText(ActionChip, 'Who is eligible'));
    await tester.pumpAndSettle();
    expect(asked(backend).last, {'language': 'en', 'articleId': 'eligibility'});
    // Quick topics are offered only under the latest answer.
    expect(find.widgetWithText(ActionChip, 'Documents'), findsNothing);
  });

  testWidgets('a typed question; the answer links into the app, and unknown links are hidden', (tester) async {
    final backend = await openHelp(tester);

    await tester.enterText(find.byType(TextField), '  my booking  ');
    await tester.tap(find.byTooltip('Send'));
    await tester.pumpAndSettle();
    expect(asked(backend).single, {'language': 'en', 'message': 'my booking'});
    expect(find.text('my booking'), findsOneWidget);
    expect(find.text('Unknown page'), findsNothing);

    await tester.tap(find.text('Book a slot'));
    await tester.pumpAndSettle();
    expect(find.byType(BookRationScreen), findsOneWidget);
  });

  testWidgets('in Marathi the assistant is asked in Marathi', (tester) async {
    final backend = await openHelp(tester, language: 'mr');
    expect(backend.requests.singleWhere((r) => r.path == '/api/chatbot/welcome').queryParameters, {'language': 'mr'});
    await tester.enterText(find.byType(TextField), 'रेशन कार्ड');
    await tester.tap(find.byTooltip('पाठवा'));
    await tester.pumpAndSettle();
    expect(asked(backend).single, {'language': 'mr', 'message': 'रेशन कार्ड'});
  });

  testWidgets('asking by voice: words appear as spoken, and a finished sentence is sent', (tester) async {
    final voice = FakeVoice();
    final backend = await openHelp(tester, voice: voice);

    await tester.tap(find.byTooltip('Ask by voice'));
    await tester.pumpAndSettle();
    expect(voice.language, 'en');
    expect(find.text('Listening… speak now'), findsOneWidget);

    voice.hear('what doc');
    await tester.pumpAndSettle();
    expect(find.text('what doc'), findsOneWidget);
    expect(asked(backend), isEmpty);

    voice.hear('what documents do I need', done: true);
    await tester.pumpAndSettle();
    expect(asked(backend).single, {'language': 'en', 'message': 'what documents do I need'});
    expect(find.text('Listening… speak now'), findsNothing);
  });

  testWidgets('silence: says nothing was heard, and sends nothing', (tester) async {
    final voice = FakeVoice();
    final backend = await openHelp(tester, voice: voice);
    await tester.tap(find.byTooltip('Ask by voice'));
    await tester.pumpAndSettle();

    await voice.stop(); // the recogniser gives up: no speech detected
    await tester.pumpAndSettle();
    expect(find.text("I didn't hear anything. Tap the mic and try again."), findsOneWidget);
    expect(asked(backend), isEmpty);
  });

  testWidgets('no microphone: a plain message instead of voice', (tester) async {
    await openHelp(tester, voice: FakeVoice(available: false));
    await tester.tap(find.byTooltip('Ask by voice'));
    await tester.pumpAndSettle();
    expect(find.text('Voice input is not available. Allow the microphone in Settings, or type your question.'), findsOneWidget);
  });

  testWidgets('an answer is read aloud in the app language, and the button resets when it ends', (tester) async {
    final speaker = FakeSpeaker();
    await openHelp(tester, speaker: speaker);

    await tester.tap(find.text('Read aloud'));
    await tester.pump();
    expect(speaker.spoken.single.$2, 'en');
    expect(speaker.spoken.single.$1, contains('I am Ration Mitra'));
    expect(find.text('Stop reading'), findsOneWidget);

    speaker.finish();
    await tester.pumpAndSettle();
    expect(find.text('Read aloud'), findsOneWidget);
  });

  testWidgets('no voice for the language: says how to add one', (tester) async {
    await openHelp(tester, speaker: FakeSpeaker(hasVoice: false));
    await tester.tap(find.text('Read aloud'));
    await tester.pumpAndSettle();
    expect(find.textContaining('This phone has no voice for this language.'), findsOneWidget);
  });

  testWidgets('help is open to everyone, from the sign-in screen', (tester) async {
    final app = await TestApp.build(FakeBackend(helpOrDemo), savedLanguage: 'en',
        overrides: [voiceInputProvider.overrideWithValue(FakeVoice()), speakerProvider.overrideWithValue(FakeSpeaker())]);
    await tester.pumpWidget(app.widget);
    await tester.pumpAndSettle();
    await tester.tap(find.byTooltip('Help'));
    await tester.pumpAndSettle();
    expect(find.byType(HelpChatScreen), findsOneWidget);
    expect(find.textContaining('I am Ration Mitra'), findsOneWidget);
  });
}
