import 'package:dio/dio.dart';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:qr_flutter/qr_flutter.dart';
import 'package:smart_ration_mobile/app/router.dart';
import 'package:smart_ration_mobile/app/routes.dart';
import 'package:smart_ration_mobile/features/booking/booking_data.dart';
import 'package:smart_ration_mobile/features/citizen/citizen_home_screen.dart';

import '../support/fake_backend.dart';
import '../support/test_app.dart';

/// Times are written with a narrow no-break space before AM/PM (Unicode CLDR), e.g. "10:05 AM".
String hm(String text) => text.replaceAll(' AM', ' AM').replaceAll(' PM', ' PM');

/// Opens the app as the signed-in demo citizen on a tall phone screen, then goes to [path].
Future<FakeBackend> openAt(WidgetTester tester, String path, {FakeReply Function(RequestOptions)? handler}) async {
  tester.view.physicalSize = const Size(1080, 3200);
  tester.view.devicePixelRatio = 2.0;
  addTearDown(tester.view.reset);
  final backend = FakeBackend(handler ?? demoServer);
  final app = await TestApp.build(backend, savedLanguage: 'en', signedInAs: citizen());
  await tester.pumpWidget(app.widget);
  await tester.pumpAndSettle();
  containerOf(tester.element(find.byType(CitizenHomeScreen))).read(routerProvider).push(path);
  await tester.pumpAndSettle();
  return backend;
}

Future<void> scrollTo(WidgetTester tester, Finder finder) async {
  await tester.scrollUntilVisible(finder, 200, scrollable: find.byType(Scrollable).first);
  await tester.pumpAndSettle();
}

void main() {
  group('rules', () {
    final day = DateTime(2026, 10, 3);

    test('a slot that has begun can no longer be booked', () {
      final slot = Slot.tryParse({'id': 1, 'slotDate': '2026-10-03T00:00:00', 'startTime': '10:05:00', 'endTime': '10:10:00',
          'capacity': 2, 'bookedCount': 0, 'status': 'Available'})!;
      expect(slot.hasStarted(DateTime(2026, 10, 3, 10, 4)), isFalse);
      expect(slot.hasStarted(DateTime(2026, 10, 3, 10, 5)), isTrue);
      expect(slot.hasStarted(DateTime(2026, 10, 2, 23, 0)), isFalse);
    });

    test('a slot with no places left is full', () {
      final full = Slot.tryParse({'id': 1, 'slotDate': '2026-10-03', 'startTime': '10:05:00', 'endTime': '10:10:00',
          'capacity': 2, 'bookedCount': 2, 'status': 'Available'})!;
      expect(full.isFull, isTrue);
      expect(full.placesLeft, 0);
    });

    test('an item can be asked for up to the smallest of: per visit, left this month, in stock', () {
      BookableItem item(num perVisit, num? left, num? stock) => BookableItem.tryParse(
          {'rationType': 'Rice', 'standardQuotaPerBooking': perVisit, 'eligibleQuantity': left, 'availableQuantity': stock})!;
      expect(item(5, 15, 100).maxQuantity, 5);
      expect(item(5, 3, 100).maxQuantity, 3);
      expect(item(5, 15, 2).maxQuantity, 2);
      expect(item(5, 0, 100).maxQuantity, 0);
    });

    test('token states: booked, collected, cancelled, and missed when the day has passed', () {
      RationToken token(String status, int offset) =>
          RationToken.tryParse({...tokenJson(status: status), 'slotDate': day.add(Duration(days: offset)).toIso8601String().substring(0, 10)})!;
      expect(token('Confirmed', 0).stateOn(day), TokenState.booked);
      expect(token('Confirmed', -1).stateOn(day), TokenState.missed);
      expect(token('NoShow', 0).stateOn(day), TokenState.missed);
      expect(token('Completed', -5).stateOn(day), TokenState.collected);
      expect(token('Cancelled', 2).stateOn(day), TokenState.cancelled);
    });

    test('the next token is the earliest one still to collect', () {
      RationToken token(int id, int offset, String start, {String status = 'Confirmed'}) => RationToken.tryParse({
            ...tokenJson(id: id, status: status),
            'slotDate': day.add(Duration(days: offset)).toIso8601String().substring(0, 10),
            'startTime': start,
          })!;
      final next = nextToken([
        token(1, 3, '09:00:00'),
        token(2, 1, '11:00:00'),
        token(3, 1, '10:00:00'),
        token(4, -1, '08:00:00'),
        token(5, 0, '09:00:00', status: 'Cancelled'),
      ], day);
      expect(next!.id, 3);
      expect(nextToken([token(4, -1, '08:00:00')], day), isNull);
    });
  });

  testWidgets('the dashboard shows the next token with a Show QR button', (tester) async {
    tester.view.physicalSize = const Size(1080, 3200);
    tester.view.devicePixelRatio = 2.0;
    addTearDown(tester.view.reset);
    final app = await TestApp.build(FakeBackend(demoServer), savedLanguage: 'en', signedInAs: citizen());
    await tester.pumpWidget(app.widget);
    await tester.pumpAndSettle();

    expect(find.text('Your next collection'), findsOneWidget);
    expect(find.text('SR-2026-000501'), findsOneWidget);
    expect(find.text(hm('Tomorrow · 10:05 AM – 10:10 AM')), findsOneWidget);
    expect(find.text('Show QR code'), findsOneWidget);
  });

  testWidgets('booking: day, time, items, then the new token with its QR', (tester) async {
    final backend = await openAt(tester, Routes.citizenBook);

    await tester.tap(find.text('Tomorrow'));
    await tester.pumpAndSettle();
    expect(find.text('1 left'), findsOneWidget); // 23:50
    expect(find.text('Full'), findsOneWidget); // 23:55
    await tester.tap(find.text(hm('11:50 PM')));
    await tester.pumpAndSettle();

    // Each item starts at its maximum: rice 5 (per visit), wheat 3 (left this month), salt 0.75.
    expect(find.text('5 kg'), findsOneWidget);
    expect(find.text('3 kg'), findsOneWidget);
    expect(find.text('0.75 kg'), findsOneWidget);
    // Salt can't go above what is left this month.
    await scrollTo(tester, find.byTooltip('More Salt'));
    expect(tester.widget<IconButton>(find.widgetWithIcon(IconButton, Icons.add).last).onPressed, isNull);
    await tester.tap(find.byTooltip('Less Salt'));
    await tester.pumpAndSettle();
    expect(find.text('0.5 kg'), findsOneWidget);

    await scrollTo(tester, find.text('Book and get token'));
    await tester.tap(find.text('Book and get token'));
    await tester.pumpAndSettle();

    final post = backend.requests.singleWhere((r) => r.method == 'POST' && r.path == '/api/ration/bookings');
    expect(post.data, {
      'rationShopId': 1,
      'timeSlotId': 77,
      'items': [
        {'rationType': 'Rice', 'quantity': 5.0},
        {'rationType': 'Wheat', 'quantity': 3.0},
        {'rationType': 'Salt', 'quantity': 0.5},
      ],
    });
    expect(find.text('SR-2026-000502'), findsOneWidget);
    expect(find.byType(QrImageView), findsOneWidget);
    expect(find.text('Your token is ready.'), findsOneWidget);
  });

  testWidgets('a full slot cannot be chosen, and nothing is sent without a time', (tester) async {
    final backend = await openAt(tester, Routes.citizenBook);
    await tester.tap(find.text('Tomorrow'));
    await tester.pumpAndSettle();

    await tester.tap(find.text(hm('11:55 PM'))); // full
    await tester.pumpAndSettle();
    await scrollTo(tester, find.text('Book and get token'));
    await tester.tap(find.text('Book and get token'));
    await tester.pumpAndSettle();

    expect(find.text('Please choose a time.'), findsOneWidget);
    expect(backend.requests.where((r) => r.method == 'POST'), isEmpty);
  });

  testWidgets('the backend refusing a booking is shown plainly', (tester) async {
    await openAt(tester, Routes.citizenBook,
        handler: (r) => r.method == 'POST' && r.path == '/api/ration/bookings'
            ? FakeReply.fail(409, 'This time slot is full. Please choose another slot.')
            : demoServer(r));
    await tester.tap(find.text('Tomorrow'));
    await tester.pumpAndSettle();
    await tester.tap(find.text(hm('11:50 PM')));
    await tester.pumpAndSettle();
    await scrollTo(tester, find.text('Book and get token'));
    await tester.tap(find.text('Book and get token'));
    await tester.pumpAndSettle();

    expect(find.text('This time slot is full. Please choose another slot.'), findsOneWidget);
  });

  testWidgets('the token screen shows the QR, the typed code, and can cancel after confirming', (tester) async {
    final backend = await openAt(tester, Routes.citizenToken(501));

    expect(find.text('SR-2026-000501'), findsOneWidget);
    expect(find.byType(QrImageView), findsOneWidget);
    expect(find.bySemanticsLabel('QR code for token SR-2026-000501'), findsOneWidget);
    expect(find.text('SRQR-501-ABCDEF0123456789'), findsOneWidget);
    expect(find.text('The QR code holds no personal details.'), findsOneWidget);

    await scrollTo(tester, find.text('Cancel booking'));
    await tester.tap(find.text('Cancel booking'));
    await tester.pumpAndSettle();
    expect(find.text('Cancel this booking?'), findsOneWidget);
    await tester.tap(find.text('Keep it'));
    await tester.pumpAndSettle();
    expect(backend.requests.where((r) => r.method == 'DELETE'), isEmpty);

    await tester.tap(find.text('Cancel booking'));
    await tester.pumpAndSettle();
    await tester.tap(find.widgetWithText(FilledButton, 'Cancel booking'));
    await tester.pumpAndSettle();
    expect(backend.requests.where((r) => r.method == 'DELETE').single.path, '/api/ration/bookings/501');
    expect(find.text('Booking cancelled.'), findsOneWidget);
  });

  testWidgets('a token whose day has passed shows Missed and no QR', (tester) async {
    await openAt(tester, Routes.citizenToken(501),
        handler: (r) => r.path == '/api/tokens/501' ? FakeReply.ok(tokenJson(dayOffset: -2)) : demoServer(r));

    expect(find.text('Missed'), findsOneWidget);
    expect(find.byType(QrImageView), findsNothing);
    expect(find.text('Cancel booking'), findsNothing);
  });

  testWidgets('my tokens lists every token with its state', (tester) async {
    await openAt(tester, Routes.citizenTokens,
        handler: (r) => r.method == 'GET' && r.path == '/api/ration/bookings'
            ? FakeReply.ok([tokenJson(), tokenJson(id: 400, number: 'SR-2026-000400', status: 'Completed', dayOffset: -10)])
            : demoServer(r));

    expect(find.text('SR-2026-000501'), findsOneWidget);
    expect(find.text('Booked'), findsOneWidget);
    expect(find.text('SR-2026-000400'), findsOneWidget);
    expect(find.text('Collected'), findsOneWidget);
  });
}
