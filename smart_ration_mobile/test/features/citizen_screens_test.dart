import 'package:dio/dio.dart';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:smart_ration_mobile/features/citizen/citizen_data.dart';
import 'package:smart_ration_mobile/features/citizen/citizen_widgets.dart';

import '../support/fake_backend.dart';
import '../support/test_app.dart';

Future<FakeBackend> openCitizenHome(WidgetTester tester,
    {FakeReply Function(RequestOptions)? handler, String language = 'en'}) async {
  final backend = FakeBackend(handler ?? demoServer);
  final app = await TestApp.build(backend, savedLanguage: language, signedInAs: citizen());
  await tester.pumpWidget(app.widget);
  await tester.pumpAndSettle();
  return backend;
}

/// Scrolls the dashboard to a card's title (lists only build what is near the screen) and taps it.
Future<void> open(WidgetTester tester, String cardTitle) async {
  final title = find.text(cardTitle);
  await tester.scrollUntilVisible(title, 200, scrollable: find.byType(Scrollable).first);
  await tester.pumpAndSettle();
  await tester.tap(title);
  await tester.pumpAndSettle();
}

void main() {
  group('reading the backend answers', () {
    test('all three answers are combined', () {
      final o = parseOverview(citizenProfileJson(), citizenEntitlementJson(), citizenCollectionsJson());
      expect(o.beneficiaryId, 1);
      expect(o.cardNumber, 'PB-DEMO-0001');
      expect(o.members.map((m) => m.fullName), ['Asha Devi', 'Ramesh Devi', 'Meena Devi']);
      expect(o.eligibility, FamilyEligibility.eligible);
      expect(o.isDemoData, isTrue);
      expect(o.shop!.name, 'Satnavari Ration Shop');
      expect(o.entitlement.firstWhere((i) => i.rationType == 'EdibleOil').remaining, 1.5);
      expect(o.collections.single.items.single, ('Rice', 5.0));
    });

    test('some members not eligible -> partially eligible', () {
      final members = [
        {'id': 1, 'fullName': 'A', 'age': 40, 'relationship': 'Head', 'eligibility': 'Eligible'},
        {'id': 2, 'fullName': 'B', 'age': 19, 'relationship': 'Son', 'eligibility': 'VerificationRequired'},
      ];
      final o = parseOverview(citizenProfileJson(members: members), citizenEntitlementJson(), const []);
      expect(o.eligibility, FamilyEligibility.partiallyEligible);
      expect(o.eligibleMembers, 1);
    });

    test('an inactive card -> not eligible, whatever the members', () {
      final o = parseOverview(citizenProfileJson(cardStatus: 'SUSPENDED'), citizenEntitlementJson(), const []);
      expect(o.eligibility, FamilyEligibility.notEligible);
    });

    test('amounts read naturally', () {
      expect([amount(15), amount(1.5), amount(0.75), amount(0)], ['15', '1.5', '0.75', '0']);
    });
  });

  testWidgets('the dashboard shows the card, eligibility and family', (tester) async {
    final backend = await openCitizenHome(tester);

    expect(find.text('Namaste, Asha Devi'), findsOneWidget);
    expect(find.text('Demo data: this is not a real ration card.'), findsOneWidget);
    expect(find.text('PB-DEMO-0001'), findsOneWidget);
    expect(find.text('Satnavari Ration Shop'), findsOneWidget);
    expect(find.text('3 of 3 members eligible'), findsOneWidget);
    expect(find.text('10 kg left of 15 kg'), findsOneWidget);
    // The entitlement and history are fetched together, after the profile.
    expect(backend.paths.first, '/api/beneficiaries/me');
    expect(backend.paths, containsAll(['/api/beneficiaries/1/entitlement', '/api/beneficiaries/1/collections']));
  });

  testWidgets('the family screen lists every member, with Aadhaar masked for the card holder only', (tester) async {
    await openCitizenHome(tester);
    await open(tester, 'Family members');

    expect(find.text('Asha Devi'), findsWidgets);
    expect(find.text('Head of family · Female · 34 years'), findsOneWidget);
    expect(find.text('Spouse · 37 years'), findsOneWidget); // gender not recorded: nothing guessed
    expect(find.text('Daughter · Female · 9 years'), findsOneWidget);
    expect(find.text('XXXX-XXXX-7173 · Aadhaar verified'), findsOneWidget);
    expect(find.textContaining('XXXX'), findsOneWidget);
    expect(find.text('Eligible'), findsNWidgets(3));
  });

  testWidgets('the ration card screen shows the card and the collection history', (tester) async {
    await openCitizenHome(tester);
    await open(tester, 'Ration card');

    expect(find.text('FAM-DEMO-0001'), findsOneWidget);
    expect(find.text('Main road, Nagpur'), findsOneWidget);
    expect(find.text('Collection history'), findsOneWidget);
    expect(find.text('2026-09-29 07:17'), findsOneWidget);
    expect(find.text('Rice 5 kg'), findsOneWidget);
  });

  testWidgets('the eligibility screen explains the status and shows each item', (tester) async {
    await openCitizenHome(tester);
    await open(tester, 'Eligibility');

    expect(find.text('Every member of your family can receive rations this month.'), findsOneWidget);
    expect(find.text("This month's entitlement"), findsOneWidget);
    expect(find.text('Collected: 5 kg'), findsOneWidget);
    await tester.scrollUntilVisible(find.text('1.5 L left of 1.5 L'), 200, scrollable: find.byType(Scrollable).first);
    expect(find.text('1.5 L left of 1.5 L'), findsOneWidget);
  });

  testWidgets('everything is shown in Hindi', (tester) async {
    await openCitizenHome(tester, language: 'hi');

    expect(find.text('नमस्ते, Asha Devi'), findsOneWidget);
    expect(find.text('राशन कार्ड'), findsOneWidget);
    expect(find.text('3 में से 3 सदस्य पात्र'), findsOneWidget);
    expect(find.text('15 किग्रा में से 10 किग्रा बाकी'), findsOneWidget);
  });

  testWidgets('a problem loading shows a plain message and Try again works', (tester) async {
    var failing = true;
    await openCitizenHome(tester, handler: (r) => failing ? const FakeReply.fails(DioExceptionType.connectionError) : demoServer(r));

    expect(find.text('Unable to connect. Please check your internet connection.'), findsOneWidget);
    failing = false;
    await tester.tap(find.text('Try again'));
    await tester.pumpAndSettle();
    expect(find.text('PB-DEMO-0001'), findsOneWidget);
  });

  testWidgets('a citizen without a linked card is told what to do', (tester) async {
    await openCitizenHome(tester,
        handler: (r) => FakeReply.fail(404, 'You do not have a beneficiary profile yet.'));

    expect(find.text('Your ration card is not linked yet. Please contact your ration shop.'), findsOneWidget);
  });
}
