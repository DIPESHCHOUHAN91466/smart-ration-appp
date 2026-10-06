import 'package:dio/dio.dart';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:smart_ration_mobile/app/routes.dart';
import 'package:smart_ration_mobile/features/official/records_data.dart';

import '../support/fake_backend.dart';
import 'official_test.dart' show openOfficial;

Map<String, Object?> bookingJson(int id, String number, String user, String shop, String status, String day) => {
      'id': id, 'tokenNumber': number, 'userName': user, 'rationShopName': shop, 'status': status, 'slotDate': '${day}T00:00:00',
      'startTime': '10:00:00', 'endTime': '10:30:00', 'items': const [], 'qrCodeValue': 'SRQR-$id',
    };

Map<String, Object?> stockJson(int id, int shop, String type, num available, num minimum) => {
      'id': id, 'rationShopId': shop, 'rationType': type, 'availableQuantity': available, 'allocatedQuantity': 0,
      'minimumStockLevel': minimum, 'isLowStock': available <= minimum, 'updatedAt': '2026-10-01T00:00:00',
    };

/// The officials' record routes, shaped like the real backend answers.
FakeReply recordsServer(RequestOptions r) => switch (r.path) {
      '/api/ration/bookings' => FakeReply.ok([
          bookingJson(3, 'SR-2026-000003', 'Asha Devi', 'Satnavari Ration Shop', 'Completed', '2026-10-01'),
          bookingJson(2, 'SR-2026-000002', 'Ramesh Patil', 'Hingna Ration Shop', 'Cancelled', '2026-10-01'),
          bookingJson(1, 'SR-2026-000001', 'Sunita Rao', 'Satnavari Ration Shop', 'Confirmed', '2099-01-01'),
        ]),
      '/api/inventory' => FakeReply.ok([
          stockJson(10, 2, 'Rice', 400, 100),
          stockJson(11, 1, 'Sugar', 5, 20), // low, at shop 1
          stockJson(12, 1, 'Wheat', 480, 100),
        ]),
      '/api/admin/reports' => FakeReply.ok([
          for (final (name, count) in [
            ('Daily Collection Report', 120),
            ('Token Generation Report', 160),
            ('QR Verification Report', 118),
            ('Cancelled Bookings Report', 9),
          ])
            {'reportName': name, 'description': 'English text', 'recordCount': count, 'exportAvailable': false},
        ]),
      '/api/audit/verification' => FakeReply.ok([
          {'id': 9, 'action': 'OtpFailed', 'verificationMethod': 'OTP', 'status': 'FAILED', 'reason': 'OTP_INVALID',
              'tokenNumber': 'SR-2026-000003', 'beneficiaryId': 41, 'timestamp': '2026-10-01 10:11:05'},
          {'id': 8, 'action': 'CollectionConfirmed', 'verificationMethod': 'QR', 'status': 'SUCCESS', 'reason': null,
              'tokenNumber': 'SR-2026-000002', 'beneficiaryId': 40, 'timestamp': '2026-10-01 09:00:00'},
        ]),
      '/api/admin/users' => FakeReply.ok([
          {'id': 7, 'fullName': 'Asha Devi', 'email': 'asha@example.com', 'mobileNumber': '9876543210', 'role': 'RuralUser'},
          {'id': 3, 'fullName': 'Satnavari Shop Owner', 'email': 'shop@example.com', 'mobileNumber': '9123456789', 'role': 'ShopOwner'},
        ]),
      _ => officialServer(r),
    };

List<RequestOptions> calls(FakeBackend b, String path) => b.requests.where((r) => r.path == path).toList();

void main() {
  testWidgets('the dashboard lists the five records', (tester) async {
    await openOfficial(tester, server: recordsServer);

    expect(find.text('Records'), findsOneWidget);
    for (final title in ['All bookings', 'Stock in all shops', 'Reports', 'Verification record', 'People and staff']) {
      expect(find.text(title), findsOneWidget);
    }
    await tester.tap(find.text('Reports'));
    await tester.pumpAndSettle();
    expect(find.text('Collections completed'), findsOneWidget);
  });

  testWidgets('bookings: newest first as sent, filter by state and search by name, token or shop', (tester) async {
    await openOfficial(tester, path: Routes.officialBookings, server: recordsServer);

    expect(find.text('3 bookings'), findsOneWidget);
    double y(String text) => tester.getTopLeft(find.text(text)).dy;
    expect(y('SR-2026-000003'), lessThan(y('SR-2026-000001')));

    await tester.tap(find.widgetWithText(ChoiceChip, 'Collected'));
    await tester.pumpAndSettle();
    expect(find.text('1 bookings'), findsOneWidget);
    expect(find.text('Asha Devi'), findsOneWidget);

    await tester.tap(find.widgetWithText(ChoiceChip, 'All'));
    await tester.enterText(find.byType(TextField), 'hingna');
    await tester.pumpAndSettle();
    expect(find.text('Ramesh Patil'), findsOneWidget);
    expect(find.text('Asha Devi'), findsNothing);

    await tester.enterText(find.byType(TextField), 'nobody');
    await tester.pumpAndSettle();
    expect(find.text('No bookings here.'), findsOneWidget);
  });

  testWidgets('stock: shops with low stock first, named from the shops list; "low only" hides the rest', (tester) async {
    await openOfficial(tester, path: Routes.officialStock, server: recordsServer);

    double y(String text) => tester.getTopLeft(find.text(text)).dy;
    final low = find.text('Low');
    expect(low, findsOneWidget);
    expect(find.text('Rice'), findsOneWidget);
    // The shop holding the low sugar comes first.
    expect(y('Sugar'), lessThan(y('Rice')));

    await tester.tap(find.widgetWithText(ChoiceChip, 'Low stock only'));
    await tester.pumpAndSettle();
    expect(find.text('Sugar'), findsOneWidget);
    expect(find.text('Wheat'), findsNothing);
    expect(find.text('Rice'), findsNothing);
  });

  testWidgets('reports: the last 30 days by default, counts translated by name', (tester) async {
    final backend = await openOfficial(tester, path: Routes.officialReports, server: recordsServer);

    final q = calls(backend, '/api/admin/reports').single.queryParameters;
    final from = DateTime.parse(q['fromDate'] as String);
    final to = DateTime.parse(q['toDate'] as String);
    expect(to.difference(from).inDays, 29);
    final now = DateTime.now();
    expect(to, DateTime(now.year, now.month, now.day));

    expect(find.text('Tokens booked'), findsOneWidget);
    expect(find.text('160'), findsOneWidget);
    expect(find.text('Bookings cancelled'), findsOneWidget);
    expect(find.text('File download is not available yet.'), findsOneWidget);
  });

  testWidgets('verification record: actions in words, outcome filter sent to the backend', (tester) async {
    final backend = await openOfficial(tester, path: Routes.officialAudit, server: recordsServer);

    expect(find.text('OTP wrong'), findsOneWidget);
    expect(find.text('Ration handed over'), findsOneWidget);
    expect(find.text('OTP_INVALID'), findsOneWidget);
    expect(calls(backend, '/api/audit/verification').single.queryParameters, isEmpty);

    await tester.tap(find.widgetWithText(ChoiceChip, 'Failed'));
    await tester.pumpAndSettle();
    expect(calls(backend, '/api/audit/verification').last.queryParameters, {'status': 'FAILED'});
  });

  testWidgets('people: contact details masked; role filter sent; name search on the phone', (tester) async {
    final backend = await openOfficial(tester, path: Routes.officialUsers, server: recordsServer);

    expect(find.text('••••••3210'), findsOneWidget);
    expect(find.text('a•••@example.com'), findsOneWidget);
    expect(find.text('9876543210'), findsNothing);
    expect(find.text('asha@example.com'), findsNothing);

    await tester.tap(find.widgetWithText(ChoiceChip, 'Shop Owner'));
    await tester.pumpAndSettle();
    expect(calls(backend, '/api/admin/users').last.queryParameters, {'role': 'ShopOwner'});

    await tester.tap(find.widgetWithText(ChoiceChip, 'All'));
    await tester.pumpAndSettle();
    await tester.enterText(find.byType(TextField), 'asha');
    await tester.pumpAndSettle();
    expect(find.text('Asha Devi'), findsOneWidget);
    expect(find.text('Satnavari Shop Owner'), findsNothing);
  });

  test('masking keeps only the last four characters', () {
    expect(maskTail('9876543210'), '••••••3210');
    expect(maskTail('123'), '••••');
    expect(maskTail(''), '');
    expect(const Account(id: 1, name: 'x', role: null, email: 'not-an-email', mobile: '').maskedEmail, '••••••••mail');
  });
}
