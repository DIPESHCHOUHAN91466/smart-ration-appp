import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:smart_ration_mobile/app/router.dart';
import 'package:smart_ration_mobile/app/routes.dart';
import 'package:smart_ration_mobile/features/booking/book_ration_screen.dart';
import 'package:smart_ration_mobile/features/help/help_chat_screen.dart';
import 'package:smart_ration_mobile/features/help/help_topics_screen.dart';

import '../support/fake_backend.dart';
import '../support/test_app.dart';
import 'help_test.dart' show FakeSpeaker, openHelp;

Future<FakeBackend> openTopics(WidgetTester tester, {String language = 'en', FakeSpeaker? speaker}) async {
  final backend = await openHelp(tester, language: language, speaker: speaker);
  await tester.tap(find.byTooltip(language == 'en' ? 'Help topics' : 'मदत विषय'));
  await tester.pumpAndSettle();
  return backend;
}

void main() {
  testWidgets('the help chat leads to the topics; sections open to their articles, in my language', (tester) async {
    final backend = await openTopics(tester);

    expect(find.byType(HelpTopicsScreen), findsOneWidget);
    expect(backend.requests.singleWhere((r) => r.path == '/api/public-help/categories').queryParameters, {'language': 'en'});
    expect(find.text('Booking and tokens (en)'), findsOneWidget);
    expect(find.textContaining('2 articles'), findsOneWidget);
    expect(find.textContaining('1 article'), findsWidgets);
    expect(find.text('How to book a slot'), findsNothing); // closed

    await tester.tap(find.text('Booking and tokens (en)'));
    await tester.pumpAndSettle();
    await tester.tap(find.text('How to book a slot'));
    await tester.pumpAndSettle();
    expect(find.byType(HelpArticleScreen), findsOneWidget);
    expect(find.textContaining('2. Pick a time'), findsOneWidget);
  });

  testWidgets('Marathi: the sections are asked for in Marathi', (tester) async {
    final backend = await openTopics(tester, language: 'mr');
    expect(backend.requests.singleWhere((r) => r.path == '/api/public-help/categories').queryParameters, {'language': 'mr'});
    expect(find.text('Booking and tokens (mr)'), findsOneWidget);
  });

  testWidgets('search: hits open the article; no hits point to the assistant', (tester) async {
    final backend = await openTopics(tester);

    await tester.enterText(find.byType(TextField), '  book  ');
    await tester.testTextInput.receiveAction(TextInputAction.search);
    await tester.pumpAndSettle();
    expect(backend.requests.last.queryParameters, {'q': 'book', 'language': 'en'});
    expect(find.text('Results for “book”'), findsOneWidget);
    expect(find.text('Open Book Ration.'), findsOneWidget);
    expect(find.text('Booking and tokens (en)'), findsNothing);

    await tester.enterText(find.byType(TextField), 'xyz');
    await tester.testTextInput.receiveAction(TextInputAction.search);
    await tester.pumpAndSettle();
    expect(find.text('Nothing found. Try other words or ask the assistant.'), findsOneWidget);
    await tester.tap(find.text('Ask the assistant'));
    await tester.pumpAndSettle();
    expect(find.byType(HelpChatScreen), findsWidgets);
  });

  testWidgets('clearing the search shows the sections again', (tester) async {
    await openTopics(tester);
    await tester.enterText(find.byType(TextField), 'book');
    await tester.testTextInput.receiveAction(TextInputAction.search);
    await tester.pumpAndSettle();
    await tester.tap(find.byIcon(Icons.close));
    await tester.pumpAndSettle();
    expect(find.text('Booking and tokens (en)'), findsOneWidget);
  });

  testWidgets('an article: read aloud without emoji, a button into the app, related articles', (tester) async {
    final speaker = FakeSpeaker();
    await openTopics(tester, speaker: speaker);
    containerOf(tester.element(find.byType(HelpTopicsScreen))).read(routerProvider).push(Routes.helpArticle('how-to-book'));
    await tester.pumpAndSettle();

    expect(find.text('How to book a slot'), findsOneWidget);
    await tester.tap(find.text('Read aloud'));
    await tester.pump();
    expect(speaker.spoken.single.$1, isNot(contains('📅')));
    expect(speaker.spoken.single.$1, startsWith('How to book a slot. 1. Open Book Ration'));
    expect(speaker.spoken.single.$2, 'en');
    speaker.finish();
    await tester.pumpAndSettle();

    expect(find.text('Cancel a booking'), findsOneWidget);
    await tester.tap(find.text('Book a slot'));
    await tester.pumpAndSettle();
    expect(find.byType(BookRationScreen), findsOneWidget);
  });

  testWidgets('an article that does not exist says so and offers to try again', (tester) async {
    await openTopics(tester);
    containerOf(tester.element(find.byType(HelpTopicsScreen))).read(routerProvider).push(Routes.helpArticle('nope'));
    await tester.pumpAndSettle();
    expect(find.text('Try again'), findsOneWidget);
  });

  test('help topics and every article are open without signing in', () {
    expect(redirectFor(null, Routes.helpTopics), isNull);
    expect(redirectFor(null, Routes.helpArticle('how-to-book')), isNull);
    expect(redirectFor(null, '/help/topicsX'), Routes.login);
  });
}
