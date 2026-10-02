import 'package:dio/dio.dart';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:smart_ration_mobile/app/router.dart';
import 'package:smart_ration_mobile/app/routes.dart';
import 'package:smart_ration_mobile/features/auth/session.dart';
import 'package:smart_ration_mobile/features/official/official_data.dart';
import 'package:smart_ration_mobile/features/official/official_home_screen.dart';

import '../support/fake_backend.dart';
import '../support/test_app.dart';

SessionUser official() =>
    SessionUser.tryParse(userJson(id: 4, fullName: 'District Government Officer', role: 'GovernmentOfficial'))!;

Future<FakeBackend> openOfficial(WidgetTester tester,
    {String? path, String language = 'en', FakeReply Function(RequestOptions)? server}) async {
  tester.view.physicalSize = const Size(1080, 3600);
  tester.view.devicePixelRatio = 2.0;
  addTearDown(tester.view.reset);
  final backend = FakeBackend(server ?? officialServer);
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

  group('updating an alert', () {
    /// The official views plus a working update route: resolved or dismissed alerts leave the open
    /// list, an alert under review stays with its note.
    FakeReply Function(RequestOptions) liveAlerts({FakeReply? updateReply}) {
      final status = <int, String>{40: 'Open', 47: 'UnderReview'};
      final notes = <int, String>{47: 'Called the shop owner.'};
      return (r) {
        final m = RegExp(r'^/api/ai/alerts/(\d+)/resolve$').firstMatch(r.path);
        if (m != null && r.method == 'POST') {
          if (updateReply != null) return updateReply;
          final id = int.parse(m.group(1)!);
          final body = r.data as Map;
          status[id] = body['Status'] as String;
          notes[id] = (body['Note'] as String?) ?? '';
          return FakeReply.ok({'id': id, 'status': status[id]});
        }
        if (r.path == '/api/ai/alerts/active') {
          return FakeReply.ok({
            'sync': {'available': false},
            'items': [
              for (final (id, type, severity) in [(47, 'RepeatedQrScan', 'MEDIUM'), (40, 'DuplicateCollectionAttempt', 'HIGH')])
                if (status[id] == 'Open' || status[id] == 'UnderReview')
                  {...alertJson(id, type, severity), 'status': status[id], 'resolutionNote': notes[id]},
            ],
          });
        }
        return officialServer(r);
      };
    }

    Finder updateButtonOf(String alertTitle) =>
        find.descendant(of: find.ancestor(of: find.text(alertTitle), matching: find.byType(Card)), matching: find.text('Update'));

    List<RequestOptions> updates(FakeBackend b) => b.requests.where((r) => r.path.endsWith('/resolve')).toList();

    testWidgets('resolving an alert sends the decision and note, and it leaves the list', (tester) async {
      final backend = await openOfficial(tester, path: Routes.officialAlerts, server: liveAlerts());

      await tester.tap(updateButtonOf('Repeated collection attempts'));
      await tester.pumpAndSettle();
      expect(find.text('Update this alert'), findsOneWidget);
      expect(find.text('Do not write Aadhaar numbers, OTPs or passwords.'), findsOneWidget);

      await tester.tap(find.text('Resolved'));
      await tester.enterText(find.widgetWithText(TextField, 'Note (optional)'), '  Visited the shop; extra bag returned.  ');
      await tester.tap(find.text('Save'));
      await tester.pumpAndSettle();

      final sent = updates(backend).single;
      expect(sent.path, '/api/ai/alerts/40/resolve');
      expect(sent.data, {'Status': 'Resolved', 'Note': 'Visited the shop; extra bag returned.'});
      expect(find.text('Alert updated'), findsOneWidget);
      expect(find.text('Repeated collection attempts'), findsNothing);
      expect(find.text('Same QR scanned many times'), findsOneWidget);
    });

    testWidgets('an alert under review shows that and its note; the form starts at "Resolved" with the note kept', (tester) async {
      final backend = await openOfficial(tester, path: Routes.officialAlerts, server: liveAlerts());

      expect(find.text('Under review'), findsOneWidget);
      expect(find.text("Official's note"), findsOneWidget);
      expect(find.text('Called the shop owner.'), findsOneWidget);

      await tester.tap(updateButtonOf('Same QR scanned many times'));
      await tester.pumpAndSettle();
      final selected = tester.widget<RadioGroup<AlertDecision>>(find.byType(RadioGroup<AlertDecision>));
      expect(selected.groupValue, AlertDecision.resolved);

      await tester.tap(find.text('Not a problem'));
      await tester.tap(find.text('Save'));
      await tester.pumpAndSettle();
      expect(updates(backend).single.data, {'Status': 'Dismissed', 'Note': 'Called the shop owner.'});
      expect(find.text('Same QR scanned many times'), findsNothing);
    });

    testWidgets('a note that looks like an Aadhaar number is not sent', (tester) async {
      final backend = await openOfficial(tester, path: Routes.officialAlerts, server: liveAlerts());

      await tester.tap(updateButtonOf('Repeated collection attempts'));
      await tester.pumpAndSettle();
      await tester.enterText(find.widgetWithText(TextField, 'Note (optional)'), 'Card holder 1234 5678 9012');
      await tester.tap(find.text('Save'));
      await tester.pumpAndSettle();

      expect(updates(backend), isEmpty);
      expect(find.text('Update this alert'), findsOneWidget); // still open, showing the warning as an error
      expect(find.text('Do not write Aadhaar numbers, OTPs or passwords.'), findsOneWidget);
    });

    testWidgets("the backend's refusal is shown and the form stays open", (tester) async {
      await openOfficial(tester,
          path: Routes.officialAlerts,
          server: liveAlerts(updateReply: FakeReply.fail(403, 'Only government officials can resolve alerts.')));

      await tester.tap(updateButtonOf('Repeated collection attempts'));
      await tester.pumpAndSettle();
      await tester.tap(find.text('Save'));
      await tester.pumpAndSettle();

      expect(find.text('Only government officials can resolve alerts.'), findsOneWidget);
      expect(find.text('Update this alert'), findsOneWidget);
      expect(find.text('Alert updated'), findsNothing);
    });
  });

  testWidgets('in Marathi the alert kinds are translated and the English rule text is labelled', (tester) async {
    await openOfficial(tester, path: Routes.officialAlerts, language: 'mr');

    expect(find.text('वारंवार रेशन घेण्याचा प्रयत्न'), findsOneWidget);
    expect(find.text('प्रणालीकडील तपशील (इंग्रजीत):'), findsNWidgets(2));
  });
}
