import 'package:dio/dio.dart';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:smart_ration_mobile/app/routes.dart';

import '../support/test_app.dart';

import '../support/fake_backend.dart';
import 'booking_test.dart' show hm, openAt, scrollTo;

const shopsJson = [
  {'id': 1, 'shopName': 'Satnavari Ration Shop', 'address': 'Main Road, Satnavari', 'district': 'Nagpur'},
  {'id': 3, 'shopName': 'Wadi Ration Shop', 'address': 'Main Road, Wadi', 'district': 'Nagpur'},
];

FakeReply withShops(RequestOptions r) => r.path == '/api/shops' ? FakeReply.ok(shopsJson) : demoServer(r);

void main() {
  testWidgets('like the website, the citizen can choose another shop before booking', (tester) async {
    final backend = await openAt(tester, Routes.citizenBook, handler: withShops);
    expect(find.text('Choose your ration shop'), findsOneWidget);
    expect(find.text('Satnavari Ration Shop'), findsOneWidget, reason: "the family's own shop is chosen first");

    await tester.tap(find.byType(DropdownButtonFormField<int>));
    await tester.pumpAndSettle();
    await tester.tap(find.text('Wadi Ration Shop').last);
    await tester.pumpAndSettle();
    expect(find.text('Main Road, Wadi, Nagpur'), findsOneWidget);

    await tester.tap(find.text('Tomorrow'));
    await tester.pumpAndSettle();
    await tester.tap(find.text(hm('11:50 PM')));
    await tester.pumpAndSettle();
    expect(backend.requests.where((r) => r.path == '/api/slots').last.queryParameters['shopId'], 3);

    await scrollTo(tester, find.text('Book and get token'));
    await tester.tap(find.text('Book and get token'));
    await tester.pumpAndSettle();
    final post = backend.requests.singleWhere((r) => r.method == 'POST' && r.path == '/api/ration/bookings');
    expect((post.data as Map)['rationShopId'], 3);
  });

  testWidgets('without the shop list (offline) the family shop can still be booked', (tester) async {
    await openAt(tester, Routes.citizenBook,
        handler: (r) => r.path == '/api/shops' ? const FakeReply(503, {'success': false, 'message': 'down'}) : demoServer(r));
    expect(find.text('Choose your ration shop'), findsOneWidget);
    expect(find.text('Book and get token'), findsOneWidget);
  });

  testWidgets('Book ration is on the home screen also when a booking already exists', (tester) async {
    tester.view.physicalSize = const Size(1080, 3200);
    tester.view.devicePixelRatio = 2.0;
    addTearDown(tester.view.reset);
    final app = await TestApp.build(FakeBackend(withShops), savedLanguage: 'en', signedInAs: citizen());
    await tester.pumpWidget(app.widget);
    await tester.pumpAndSettle();
    expect(find.text('Show QR code'), findsOneWidget, reason: 'the demo citizen already has a token');
    for (final label in ['Book ration', 'Booking history', 'My verification', 'My complaints', 'Notifications', 'My account']) {
      expect(find.text(label), findsWidgets, reason: label);
    }
    await tester.tap(find.text('Book ration').first);
    await tester.pumpAndSettle();
    expect(find.text('Choose your ration shop'), findsOneWidget);
  });
}
