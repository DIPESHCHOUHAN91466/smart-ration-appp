import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:smart_ration_mobile/features/language/app_language.dart';

import '../support/fake_backend.dart';
import '../support/test_app.dart';

void main() {
  testWidgets('first launch: splash, then language choice, then home in that language', (tester) async {
    final (app, preferences) = await buildTestApp(FakeBackend((_) => healthyServer));
    await tester.pumpWidget(app);
    await tester.pumpAndSettle();

    // The language screen lists every language in its own script.
    expect(find.text('English'), findsOneWidget);
    expect(find.text('हिंदी'), findsOneWidget);
    expect(find.text('मराठी'), findsOneWidget);

    // Continue does nothing until a language is picked.
    final continueButton = find.byType(FilledButton);
    expect(tester.widget<FilledButton>(continueButton).onPressed, isNull);

    // Picking Hindi switches the screen to Hindi at once.
    await tester.tap(find.text('हिंदी'));
    await tester.pumpAndSettle();
    expect(find.text('अपनी भाषा चुनें'), findsOneWidget);

    await tester.tap(find.text('आगे बढ़ें'));
    await tester.pumpAndSettle();
    expect(find.text('सर्वर से जुड़ गए'), findsOneWidget);
    expect(find.text('स्मार्ट राशन AI'), findsOneWidget);
    expect(preferences.getString(LanguageController.storageKey), 'hi');
  });

  testWidgets('next launch: the saved language skips the choice', (tester) async {
    final (app, _) = await buildTestApp(FakeBackend((_) => healthyServer), savedLanguage: 'mr');
    await tester.pumpWidget(app);
    await tester.pumpAndSettle();

    expect(find.text('सर्व्हरशी जोडले गेले'), findsOneWidget);
    expect(find.text('तुमची भाषा निवडा'), findsNothing);
  });

  testWidgets('the language button changes the language and returns home', (tester) async {
    final (app, preferences) = await buildTestApp(FakeBackend((_) => healthyServer), savedLanguage: 'en');
    await tester.pumpWidget(app);
    await tester.pumpAndSettle();
    expect(find.text('Connected to the server'), findsOneWidget);

    await tester.tap(find.byTooltip('Language'));
    await tester.pumpAndSettle();
    await tester.tap(find.text('मराठी'));
    await tester.pumpAndSettle();
    await tester.tap(find.text('पुढे चला'));
    await tester.pumpAndSettle();

    expect(find.text('सर्व्हरशी जोडले गेले'), findsOneWidget);
    expect(preferences.getString(LanguageController.storageKey), 'mr');
  });

  testWidgets('the splash screen shows the logo with a spoken description', (tester) async {
    final (app, _) = await buildTestApp(FakeBackend((_) => healthyServer), savedLanguage: 'en');
    await tester.pumpWidget(app);
    await tester.pump();

    expect(find.bySemanticsLabel('Smart Ration AI logo, powered by HSD2C'), findsOneWidget);
    await tester.pumpAndSettle();
  });
}
