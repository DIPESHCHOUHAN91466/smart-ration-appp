import 'package:dio/dio.dart';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:smart_ration_mobile/app/routes.dart';
import 'package:smart_ration_mobile/features/assistant/assistant_data.dart';
import 'package:smart_ration_mobile/features/auth/session.dart';
import 'package:smart_ration_mobile/features/citizen/family_screen.dart';
import 'package:smart_ration_mobile/features/grievance/my_complaints_screen.dart';
import 'package:smart_ration_mobile/features/help/help_chat_screen.dart';
import 'package:smart_ration_mobile/features/help/voice.dart';
import 'package:smart_ration_mobile/features/shop/scanner_screen.dart';
import 'package:smart_ration_mobile/features/shop/stock_screen.dart';

import '../support/fake_backend.dart';
import '../support/fake_grievance.dart';
import '../support/fake_help.dart';
import '../support/test_app.dart';
import 'help_test.dart' show FakeSpeaker, FakeVoice;
import 'shop_test.dart' show fakeCamera, tapText;

/// What the fake assistant answers for each sentence (the real one's shapes); anything else: a help fallback.
final _understood = <String, Map<String, Object?>>{
  'मुझे शिकायत करनी है कि इस महीने मुझे गेहूं कम मिला।': {
    'action': 'fill_form', 'intent': 'fill_form', 'form': 'grievance', 'language': 'hi', 'understoodBy': 'rules', 'missing': [],
    'fields': {'category': 'LessRation', 'rationType': 'Wheat', 'description': 'मुझे शिकायत करनी है कि इस महीने मुझे गेहूं कम मिला।'},
  },
  'show my family': {'action': 'navigate', 'intent': 'navigate', 'target': 'family', 'language': 'en', 'understoodBy': 'rules'},
  'show stock': {'action': 'navigate', 'intent': 'navigate', 'target': 'stock', 'language': 'en', 'understoodBy': 'rules'},
  'When will I get my ration?': {
    'action': 'answer', 'intent': 'collection_time', 'language': 'en', 'understoodBy': 'rules',
    'reply': {'kind': 'personal', 'language': 'en', 'text': 'Your upcoming bookings:\n• SR-2026-000501 — 03-10-2026 10:30–10:35',
        'links': [{'path': '/rural/token/501', 'label': 'Show my token'}], 'suggestions': [], 'related': []},
  },
  'switch to marathi': {'action': 'change_language', 'intent': 'change_language', 'target': 'mr', 'language': 'en', 'understoodBy': 'rules'},
  'read this page': {'action': 'read_screen', 'intent': 'read_screen', 'language': 'en', 'understoodBy': 'rules'},
};

FakeReply Function(RequestOptions) assistantServer({FakeReply Function(RequestOptions)? fallback}) {
  final complaints = complaintServer(fallback: fallback);
  return (r) {
    if (r.path == '/api/assistant/understand') {
      final text = (r.data as Map)['text'];
      return FakeReply.ok(_understood[text] ??
          {'action': 'answer', 'intent': 'ask', 'language': 'en', 'understoodBy': 'rules',
              'reply': {'kind': 'fallback', 'language': 'en', 'text': "I'm not able to verify that information.", 'links': [], 'suggestions': [], 'related': []}});
    }
    return complaints(r);
  };
}

Future<FakeBackend> openAssistant(WidgetTester tester,
    {String language = 'en', SessionUser? user, FakeVoice? voice, FakeSpeaker? speaker, FakeReply Function(RequestOptions)? server}) async {
  tester.view.physicalSize = const Size(1080, 3600);
  tester.view.devicePixelRatio = 2.0;
  addTearDown(tester.view.reset);
  final backend = FakeBackend(server ?? assistantServer());
  final app = await TestApp.build(backend, savedLanguage: language, signedInAs: user ?? citizen(), overrides: [
    voiceInputProvider.overrideWithValue(voice ?? FakeVoice()),
    speakerProvider.overrideWithValue(speaker ?? FakeSpeaker()),
    cameraViewProvider.overrideWithValue(fakeCamera),
  ]);
  await tester.pumpWidget(app.widget);
  await tester.pumpAndSettle();
  await tester.tap(find.byIcon(Icons.auto_awesome)); // the AI button
  await tester.pumpAndSettle();
  return backend;
}

Future<void> say(WidgetTester tester, String text) async {
  await tester.enterText(find.byType(TextField).last, text);
  await tester.tap(find.byIcon(Icons.send).last);
  await tester.pumpAndSettle();
}

List<Object?> understood(FakeBackend b) => b.requests.where((r) => r.path == '/api/assistant/understand').map((r) => r.data).toList();

void main() {
  test('screen names from the assistant map to this app, only where the role has the screen', () {
    expect(routeForAssistantScreen('my_tokens', AppRole.ruralUser), Routes.citizenTokens);
    expect(routeForAssistantScreen('home', AppRole.shopOwner), Routes.shopHome);
    expect(routeForAssistantScreen('alerts', AppRole.governmentOfficial), Routes.officialAlerts);
    expect(routeForAssistantScreen('admin_users', AppRole.admin), isNull);
  });

  testWidgets('flagship: a spoken Hindi complaint opens the filled form at review; confirming files it and reads the number', (tester) async {
    final voice = FakeVoice();
    final speaker = FakeSpeaker();
    final backend = await openAssistant(tester, language: 'hi', voice: voice, speaker: speaker);
    expect(find.text('मैं आपकी कैसे मदद करूं?'), findsOneWidget);

    await tester.tap(find.byIcon(Icons.mic));
    await tester.pumpAndSettle();
    voice.hear('मुझे शिकायत करनी है कि इस महीने मुझे गेहूं कम मिला।', done: true);
    await tester.pumpAndSettle();

    expect(understood(backend).single, {'text': 'मुझे शिकायत करनी है कि इस महीने मुझे गेहूं कम मिला।', 'language': 'hi', 'screen': 'home'});
    // Straight to review: nothing is sent yet.
    expect(find.text('जमा करने से पहले कृपया अपनी जानकारी जाँच लें।'), findsOneWidget);
    expect(find.text('राशन कम मिला'), findsOneWidget);
    expect(backend.requests.where((r) => r.path == '/api/grievances'), isEmpty);

    await tapText(tester, 'पुष्टि करें और भेजें');
    expect((backend.requests.singleWhere((r) => r.path == '/api/grievances').data as Map)['source'], 'ASSISTANT');
    expect(find.text('GRV-2026-000001'), findsOneWidget);
    expect(speaker.spoken.single.$1, contains('आपकी शिकायत सफलतापूर्वक दर्ज हो गई है।'));
    speaker.finish();
    await tester.pumpAndSettle();
  });

  testWidgets('asking for a screen opens it', (tester) async {
    await openAssistant(tester);
    await say(tester, 'show my family');
    expect(find.byType(FamilyScreen), findsOneWidget);
  });

  testWidgets('an answer from the real bookings is shown, can be read aloud, and its link opens the token', (tester) async {
    final speaker = FakeSpeaker();
    await openAssistant(tester, speaker: speaker);
    await say(tester, 'When will I get my ration?');

    expect(find.textContaining('SR-2026-000501 — 03-10-2026 10:30–10:35'), findsOneWidget);
    await tester.tap(find.text('Read aloud'));
    await tester.pumpAndSettle();
    expect(speaker.spoken.single.$1, startsWith('Your upcoming bookings:'));
    speaker.finish();
    await tester.pumpAndSettle();

    await tester.tap(find.text('Show my token'));
    await tester.pumpAndSettle();
    expect(find.text('SR-2026-000501'), findsWidgets);
  });

  testWidgets('"read this page" reads the home screen: the next token, day, time and shop', (tester) async {
    final speaker = FakeSpeaker();
    await openAssistant(tester, speaker: speaker);
    await say(tester, 'read this page');

    final (text, language) = speaker.spoken.single;
    expect(language, 'en');
    expect(text, allOf(startsWith('Your next ration collection: token SR-2026-000501, '), contains('Satnavari')));
    expect(find.text(text), findsOneWidget); // also shown
    speaker.finish();
    await tester.pumpAndSettle();
  });

  testWidgets('changing the language by voice switches the whole app', (tester) async {
    await openAssistant(tester);
    await say(tester, 'switch to marathi');
    expect(find.text('भाषा बदलली.'), findsOneWidget);
    expect(find.text('मी तुमची कशी मदत करू?'), findsOneWidget);
  });

  testWidgets('something it cannot verify gets the honest fallback, not a guess', (tester) async {
    await openAssistant(tester);
    await say(tester, 'What will the price of wheat be next year?');
    expect(find.text("I'm not able to verify that information."), findsOneWidget);
  });

  testWidgets('quick actions open common screens in one tap', (tester) async {
    await openAssistant(tester);
    await tester.tap(find.widgetWithText(ActionChip, 'My complaints'));
    await tester.pumpAndSettle();
    expect(find.byType(MyComplaintsScreen), findsOneWidget);
  });

  testWidgets("a problem reaching the assistant is said plainly and the sheet stays open", (tester) async {
    await openAssistant(tester,
        server: (r) => r.path == '/api/assistant/understand' ? const FakeReply.fails(DioExceptionType.connectionError) : demoServer(r));
    await say(tester, 'show my family');
    expect(find.byType(FamilyScreen), findsNothing);
    expect(find.text('How can I help you?'), findsOneWidget);
    expect(find.byType(Card), findsWidgets);
  });

  testWidgets("a shop owner's AI button has the shop's quick actions and opens its screens", (tester) async {
    await openAssistant(tester, user: shopOwner(), server: assistantServer(fallback: shopServer));
    expect(find.widgetWithText(ActionChip, 'Stock'), findsOneWidget);
    expect(find.widgetWithText(ActionChip, 'My complaints'), findsNothing);
    await say(tester, 'show stock');
    expect(find.byType(StockScreen), findsOneWidget);

    await tester.pageBack();
    await tester.pumpAndSettle();
    await tester.tap(find.byIcon(Icons.auto_awesome));
    await tester.pumpAndSettle();
    await tester.tap(find.widgetWithText(ActionChip, "Scan customer's QR"));
    await tester.pumpAndSettle();
    expect(find.byType(ScannerScreen), findsOneWidget);
  });

  testWidgets('the sign-in screen offers the help assistant', (tester) async {
    tester.view.physicalSize = const Size(1080, 3600);
    tester.view.devicePixelRatio = 2.0;
    addTearDown(tester.view.reset);
    final app = await TestApp.build(FakeBackend(helpOrDemo), savedLanguage: 'en');
    await tester.pumpWidget(app.widget);
    await tester.pumpAndSettle();
    await tapText(tester, 'Need help signing in? Ask AI');
    expect(find.byType(HelpChatScreen), findsOneWidget);
  });
}
