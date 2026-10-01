import 'package:dio/dio.dart';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:smart_ration_mobile/app/router.dart';
import 'package:smart_ration_mobile/app/routes.dart';
import 'package:smart_ration_mobile/features/shop/scanner_screen.dart';
import 'package:smart_ration_mobile/features/shop/shop_data.dart';
import 'package:smart_ration_mobile/features/shop/shop_home_screen.dart';

import '../support/fake_backend.dart';
import '../support/test_app.dart';

const readyCode = 'SRQR-501-ABCDEF0123456789';
const usedCode = 'SRQR-777-ABCDEF0123456789';
const forgedCode = 'SRQR-999-0000000000000000';

/// Stands in for the camera: one button per QR code "held up" to it.
Widget fakeCamera(BuildContext context, ValueChanged<String> onCode) => ListView(children: [
      for (final code in [readyCode, usedCode, forgedCode]) TextButton(onPressed: () => onCode(code), child: Text('camera sees $code')),
    ]);

/// Opens the app as the signed-in demo shop owner on a tall screen, then goes to [path].
Future<FakeBackend> openShop(WidgetTester tester, {String? path, FakeReply Function(RequestOptions)? handler}) async {
  tester.view.physicalSize = const Size(1080, 3600);
  tester.view.devicePixelRatio = 2.0;
  addTearDown(tester.view.reset);
  final backend = FakeBackend(handler ?? shopServer);
  final app = await TestApp.build(backend, savedLanguage: 'en', signedInAs: shopOwner(),
      overrides: [cameraViewProvider.overrideWithValue(fakeCamera)]);
  await tester.pumpWidget(app.widget);
  await tester.pumpAndSettle();
  if (path != null) {
    containerOf(tester.element(find.byType(ShopHomeScreen))).read(routerProvider).push(path);
    await tester.pumpAndSettle();
  }
  return backend;
}

Future<void> tapText(WidgetTester tester, String text) async {
  await tester.ensureVisible(find.text(text).last);
  await tester.tap(find.text(text).last);
  await tester.pumpAndSettle();
}

Iterable<RequestOptions> confirms(FakeBackend b) => b.requests.where((r) => r.path == '/api/ration/collection/confirm');

void main() {
  test('each handover gets its own random 32-character request key', () {
    final a = newRequestKey();
    expect(a, matches(RegExp(r'^[0-9a-f]{32}$')));
    expect(newRequestKey(), isNot(a));
  });

  testWidgets("the dashboard shows today's counts and both ways to serve a customer", (tester) async {
    await openShop(tester);

    expect(find.text('Satnavari Ration Shop'), findsOneWidget);
    expect(find.text('12'), findsOneWidget);
    expect(find.text('5'), findsOneWidget);
    expect(find.text('6'), findsOneWidget);
    expect(find.text('Waiting'), findsOneWidget);
    expect(find.text("Scan customer's QR"), findsOneWidget);
    expect(find.text('No QR? Verify with mobile code'), findsOneWidget);
  });

  testWidgets('scan, check, confirm after asking, then the receipt', (tester) async {
    final backend = await openShop(tester, path: Routes.shopScan);

    await tapText(tester, 'camera sees $readyCode');
    expect(backend.requests.singleWhere((r) => r.path == '/api/qr/scan').data, {'qrData': readyCode});

    // The backend's verdict, the customer and every check.
    expect(find.text('Ready to collect'), findsOneWidget);
    expect(find.text('Asha Devi'), findsOneWidget);
    expect(find.text('SR-2026-000501'), findsOneWidget);
    expect(find.text('Identified by QR code'), findsOneWidget);
    expect(find.bySemanticsLabel('Aadhaar verified: Yes'), findsOneWidget);
    // What to hand over comes from the token itself.
    expect(find.text('5 kg'), findsOneWidget);
    expect(find.text('0.5 L'), findsOneWidget);

    // Nothing is recorded until the shopkeeper says the items were handed over.
    await tapText(tester, 'Hand over and confirm');
    expect(find.text('Confirm handover?'), findsOneWidget);
    await tapText(tester, 'Not yet');
    expect(confirms(backend), isEmpty);

    await tapText(tester, 'Hand over and confirm');
    await tapText(tester, 'Yes, handed over');
    final confirm = confirms(backend).single;
    expect(confirm.data, {'tokenId': 501, 'verificationMethod': 'QR'});
    expect(confirm.headers['Idempotency-Key'], matches(RegExp(r'^[0-9a-f]{32}$')));

    expect(find.text('Ration handed over'), findsWidgets);
    expect(find.text('COL-DEMO-000042'), findsOneWidget);

    // Next customer: straight back to the scanner, with the dashboard behind it.
    await tapText(tester, 'Scan next customer');
    expect(find.text('camera sees $readyCode'), findsOneWidget);
    await tester.pageBack();
    await tester.pumpAndSettle();
    expect(find.byType(ShopHomeScreen), findsOneWidget);
  });

  testWidgets('a retry after a lost connection reuses the same request key', (tester) async {
    var attempts = 0;
    final backend = await openShop(tester, path: Routes.shopScan, handler: (r) {
      if (r.path == '/api/ration/collection/confirm' && attempts++ == 0) return const FakeReply.fails(DioExceptionType.connectionError);
      return shopServer(r);
    });
    await tapText(tester, 'camera sees $readyCode');
    await tapText(tester, 'Hand over and confirm');
    await tapText(tester, 'Yes, handed over');
    expect(find.textContaining('Unable to connect'), findsOneWidget);

    await tapText(tester, 'Hand over and confirm');
    await tapText(tester, 'Yes, handed over');
    final keys = confirms(backend).map((r) => r.headers['Idempotency-Key']).toList();
    expect(keys, hasLength(2));
    expect(keys[0], keys[1]);
    expect(find.text('COL-DEMO-000042'), findsOneWidget);
  });

  testWidgets('a forged QR is refused on the scanner, and is not sent again until "Scan again"', (tester) async {
    final backend = await openShop(tester, path: Routes.shopScan);
    int scans() => backend.requests.where((r) => r.path == '/api/qr/scan').length;

    await tapText(tester, 'camera sees $forgedCode');
    expect(find.text('Cannot accept this token'), findsOneWidget);
    expect(find.text('This QR code is not genuine. Do not hand over ration.'), findsOneWidget);

    // The camera keeps seeing the same code many times a second; it is not re-sent.
    await tapText(tester, 'camera sees $forgedCode');
    expect(scans(), 1);

    await tapText(tester, 'Scan again');
    await tapText(tester, 'camera sees $forgedCode');
    expect(scans(), 2);
  });

  testWidgets('an already-collected token shows why, translated, and no hand-over button', (tester) async {
    await openShop(tester, path: Routes.shopScan);
    await tapText(tester, 'camera sees $usedCode');

    expect(find.text('Do not hand over ration'), findsOneWidget);
    expect(find.text('This token has already been used to collect ration.'), findsOneWidget);
    expect(find.bySemanticsLabel('Token valid for collection: No'), findsOneWidget);
    expect(find.text('Hand over and confirm'), findsNothing);
  });

  testWidgets('a typed code is checked for the SRQR- start, then sent in capitals', (tester) async {
    final backend = await openShop(tester, path: Routes.shopScan);

    await tester.enterText(find.byType(TextField), 'hello');
    await tapText(tester, 'Check');
    expect(find.text('Please type the code that starts with SRQR-.'), findsOneWidget);
    expect(backend.requests.where((r) => r.path == '/api/qr/scan'), isEmpty);

    await tester.enterText(find.byType(TextField), 'srqr-501-abcdef0123456789');
    await tapText(tester, 'Check');
    expect(backend.requests.singleWhere((r) => r.path == '/api/qr/scan').data, {'qrData': readyCode});
    expect(find.text('Ready to collect'), findsOneWidget);
  });

  testWidgets('not enough stock: a plain message, and nothing was issued', (tester) async {
    await openShop(tester, path: Routes.shopScan,
        handler: (r) => r.path == '/api/ration/collection/confirm'
            ? const FakeReply(409, {
                'success': false,
                'message': 'Insufficient Rice stock to complete this collection.',
                'errorCode': 'INSUFFICIENT_STOCK',
              })
            : shopServer(r));
    await tapText(tester, 'camera sees $readyCode');
    await tapText(tester, 'Hand over and confirm');
    await tapText(tester, 'Yes, handed over');

    expect(find.text('Not enough stock for this token. Nothing was handed over or deducted.'), findsOneWidget);
    expect(find.text('Ready to collect'), findsOneWidget);
  });

  testWidgets('no QR: code to the mobile, a wrong code, the right code, then the check by OTP', (tester) async {
    final backend = await openShop(tester, path: Routes.shopOtp);

    await tester.enterText(find.byType(TextField), '98000');
    await tapText(tester, 'Send code');
    expect(find.text('Please enter a 10-digit mobile number.'), findsOneWidget);

    await tester.enterText(find.byType(TextField), '9800000007');
    await tapText(tester, 'Send code');
    expect(backend.requests.singleWhere((r) => r.path == '/api/verification/otp/request').data, {'mobileNumber': '9800000007'});
    expect(find.text('Ask the customer for the code sent to ******0007. It is valid for 5 minutes.'), findsOneWidget);
    expect(find.text('Development demo code: 123456'), findsOneWidget);

    await tester.enterText(find.byType(TextField), '111111');
    await tapText(tester, 'Verify code');
    expect(find.text('The code is wrong or has expired. Please try again or ask for a new code.'), findsOneWidget);

    await tester.enterText(find.byType(TextField), '123456');
    await tapText(tester, 'Verify code');
    expect(find.text('Identified by mobile code'), findsOneWidget);

    await tapText(tester, 'Hand over and confirm');
    await tapText(tester, 'Yes, handed over');
    expect(confirms(backend).single.data, {'tokenId': 501, 'verificationMethod': 'OTP'});
  });
}
