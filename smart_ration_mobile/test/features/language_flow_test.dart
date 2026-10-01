import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:smart_ration_mobile/features/language/app_language.dart';

import '../support/fake_backend.dart';
import '../support/test_app.dart';

void main() {
  testWidgets('first launch: splash, then language choice, then sign-in in that language', (tester) async {
    final app = await TestApp.build(FakeBackend((_) => healthyServer));
    await tester.pumpWidget(app.widget);
    await tester.pumpAndSettle();

    // The language screen lists every language in its own script.
    expect(find.text('English'), findsOneWidget);
    expect(find.text('हिंदी'), findsOneWidget);
    expect(find.text('मराठी'), findsOneWidget);

    // Continue does nothing until a language is picked.
    expect(tester.widget<FilledButton>(find.byType(FilledButton)).onPressed, isNull);

    // Picking Hindi switches the screen to Hindi at once.
    await tester.tap(find.text('हिंदी'));
    await tester.pumpAndSettle();
    expect(find.text('अपनी भाषा चुनें'), findsOneWidget);

    await tester.tap(find.text('आगे बढ़ें'));
    await tester.pumpAndSettle();
    expect(find.text('हम आपके पंजीकृत मोबाइल नंबर पर 6 अंकों का कोड भेजेंगे।'), findsOneWidget);
    expect(app.preferences.getString(LanguageController.storageKey), 'hi');
  });

  testWidgets('next launch: the saved language skips the choice', (tester) async {
    final app = await TestApp.build(FakeBackend((_) => healthyServer), savedLanguage: 'mr');
    await tester.pumpWidget(app.widget);
    await tester.pumpAndSettle();

    expect(find.text('आम्ही तुमच्या नोंदणीकृत मोबाइल नंबरवर 6 अंकी कोड पाठवू.'), findsOneWidget);
    expect(find.text('तुमची भाषा निवडा'), findsNothing);
  });

  testWidgets('the language button changes the language and returns to the same screen', (tester) async {
    final app = await TestApp.build(FakeBackend((_) => healthyServer), savedLanguage: 'en');
    await tester.pumpWidget(app.widget);
    await tester.pumpAndSettle();
    expect(find.text('We will send a 6-digit code to your registered mobile number.'), findsOneWidget);

    await tester.tap(find.byTooltip('Language'));
    await tester.pumpAndSettle();
    await tester.tap(find.text('मराठी'));
    await tester.pumpAndSettle();
    await tester.tap(find.text('पुढे चला'));
    await tester.pumpAndSettle();

    expect(find.text('आम्ही तुमच्या नोंदणीकृत मोबाइल नंबरवर 6 अंकी कोड पाठवू.'), findsOneWidget);
    expect(app.preferences.getString(LanguageController.storageKey), 'mr');
  });

  testWidgets('the splash screen shows the logo with a spoken description', (tester) async {
    final app = await TestApp.build(FakeBackend((_) => healthyServer), savedLanguage: 'en');
    await tester.pumpWidget(app.widget);
    await tester.pump();

    expect(find.bySemanticsLabel('Smart Ration AI logo, powered by HSD2C'), findsOneWidget);
    await tester.pumpAndSettle();
  });
}
