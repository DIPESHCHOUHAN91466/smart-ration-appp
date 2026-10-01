import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:smart_ration_mobile/app/router.dart';
import 'package:smart_ration_mobile/app/routes.dart';
import 'package:smart_ration_mobile/features/auth/session.dart';
import 'package:smart_ration_mobile/features/official/official_home_screen.dart';

import '../support/fake_backend.dart';
import '../support/test_app.dart';

SessionUser official() =>
    SessionUser.tryParse(userJson(id: 4, fullName: 'District Government Officer', role: 'GovernmentOfficial'))!;

Future<FakeBackend> openOfficial(WidgetTester tester, {String? path, String language = 'en'}) async {
  tester.view.physicalSize = const Size(1080, 3600);
  tester.view.devicePixelRatio = 2.0;
  addTearDown(tester.view.reset);
  final backend = FakeBackend(officialServer);
  final app = await TestApp.build(backend, savedLanguage: language, signedInAs: official());
  await tester.pumpWidget(app.widget);
  await tester.pumpAndSettle();
  if (path != null) {
    containerOf(tester.element(find.byType(OfficialHomeScreen))).read(routerProvider).push(path);
    await tester.pumpAndSettle();
  }
  return backend;
}

void main() {
  testWidgets("the official's dashboard: today, the last 30 days, low stock and alerts", (tester) async {
    await openOfficial(tester);

    expect(find.text('Namaste, District Government Officer'), findsOneWidget);
    expect(find.text('Government Official'), findsOneWidget);
    expect(find.text('Today across all shops'), findsOneWidget);
    expect(find.text('14'), findsOneWidget); // bookings today
    expect(find.text('114.75 kg'), findsOneWidget);
    expect(find.text('257'), findsOneWidget);
    expect(find.text('Last 30 days'), findsOneWidget);
    expect(find.text('453'), findsOneWidget);
    expect(find.text('77% of booked tokens were collected'), findsOneWidget);
    expect(find.text('Low-stock items'), findsOneWidget);
    expect(find.text('Alerts (2)'), findsOneWidget);
  });

  testWidgets('shops: worst stock first, filter by status, then one shop with its stock', (tester) async {
    await openOfficial(tester, path: Routes.officialShops);

    double y(String text) => tester.getTopLeft(find.text(text)).dy;
    expect(y('Satnavari Ration Shop'), lessThan(y('Hingna Ration Shop'))); // critical before low
    expect(y('Hingna Ration Shop'), lessThan(y('Butibori Ration Shop'))); // low before normal
    expect(find.textContaining('Today: 2 booked · 1 collected'), findsOneWidget);

    await tester.tap(find.widgetWithText(ChoiceChip, 'Critical'));
    await tester.pumpAndSettle();
    expect(find.text('Satnavari Ration Shop'), findsOneWidget);
    expect(find.text('Butibori Ration Shop'), findsNothing);

    await tester.tap(find.text('Satnavari Ration Shop'));
    await tester.pumpAndSettle();
    expect(find.text('SR-SATNAVARI-001'), findsOneWidget);
    expect(find.text('Satnavari Shop Owner'), findsOneWidget);
    expect(find.text('Satnavari, Nagpur, Maharashtra'), findsOneWidget);
    expect(find.text('3.5 kg'), findsOneWidget); // salt, low
    expect(find.text('480 kg'), findsOneWidget);
  });

  testWidgets('alerts: most serious first, with the "not proof of fraud" notice', (tester) async {
    await openOfficial(tester, path: Routes.officialAlerts);

    expect(find.text('These are warnings to review, not proof of fraud. Check before acting.'), findsOneWidget);
    double y(String text) => tester.getTopLeft(find.text(text)).dy;
    expect(y('Repeated collection attempts'), lessThan(y('Same QR scanned many times'))); // HIGH before MEDIUM
    expect(find.text('High'), findsOneWidget);
    expect(find.text('Rule text 40 from the backend.'), findsOneWidget);
    expect(find.text('Details from the system (English):'), findsNothing);
  });

  testWidgets('in Marathi the alert kinds are translated and the English rule text is labelled', (tester) async {
    await openOfficial(tester, path: Routes.officialAlerts, language: 'mr');

    expect(find.text('वारंवार रेशन घेण्याचा प्रयत्न'), findsOneWidget);
    expect(find.text('प्रणालीकडील तपशील (इंग्रजीत):'), findsNWidgets(2));
  });
}
