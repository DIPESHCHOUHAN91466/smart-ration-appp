import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';

import '../support/fake_backend.dart';
import 'auth_flow_test.dart' show start, useEmail;

const _strong = 'Kite-River-Lamp-42';

FakeReply resetSent() => FakeReply.ok({'mobileMasked': '******0001', 'expiresInSeconds': 300, 'resendAfterSeconds': 30, 'demoOtpValue': null});

Future<void> tapText(WidgetTester tester, String text) async {
  await tester.ensureVisible(find.text(text).last);
  await tester.pumpAndSettle();
  await tester.tap(find.text(text).last);
  await tester.pumpAndSettle();
}

Future<void> fill(WidgetTester tester, String label, String value) =>
    tester.enterText(find.widgetWithText(TextFormField, label), value);

Future<void> openReset(WidgetTester tester) async {
  await useEmail(tester);
  await tapText(tester, 'Forgot password?');
  expect(find.text('Reset your password'), findsWidgets);
}

void main() {
  setUp(() {
    final view = TestWidgetsFlutterBinding.instance.platformDispatcher.views.first;
    view.physicalSize = const Size(1080, 3000);
    view.devicePixelRatio = 3;
  });
  tearDown(() => TestWidgetsFlutterBinding.instance.platformDispatcher.views.first.reset());

  testWidgets('a forgotten password is reset with the code sent to the mobile', (tester) async {
    final backend = FakeBackend((r) => switch (r.path) {
          '/api/auth/password/reset/request' => resetSent(),
          '/api/auth/password/reset/confirm' => FakeReply.ok(null),
          _ => demoServer(r),
        });
    await start(tester, backend);
    await openReset(tester);

    await fill(tester, 'Mobile number', '+91 90000 00001');
    await tapText(tester, 'Send code');
    expect(backend.requests.singleWhere((r) => r.path == '/api/auth/password/reset/request').data, {'mobileNumber': '9000000001'});
    expect(find.textContaining('a 6-digit code has been sent'), findsOneWidget);

    await fill(tester, '6-digit code', '123456');
    await fill(tester, 'New password', _strong);
    await fill(tester, 'Confirm new password', _strong);
    await tapText(tester, 'Set new password');

    expect(backend.requests.singleWhere((r) => r.path == '/api/auth/password/reset/confirm').data,
        {'mobileNumber': '9000000001', 'otp': '123456', 'newPassword': _strong});
    expect(find.text('Password changed. Please sign in with the new password.'), findsOneWidget);
    expect(find.text('Reset your password'), findsNothing);   // back on the sign-in screen
  });

  testWidgets('short and mismatched new passwords are caught before sending', (tester) async {
    final backend = FakeBackend((r) => r.path == '/api/auth/password/reset/request' ? resetSent() : demoServer(r));
    await start(tester, backend);
    await openReset(tester);
    await fill(tester, 'Mobile number', '9000000001');
    await tapText(tester, 'Send code');

    await fill(tester, '6-digit code', '123456');
    await fill(tester, 'New password', 'short');
    await fill(tester, 'Confirm new password', 'different');
    await tapText(tester, 'Set new password');
    expect(find.text('Use at least 12 characters.'), findsOneWidget);
    expect(find.text('The passwords do not match.'), findsOneWidget);
    expect(backend.requests.where((r) => r.path == '/api/auth/password/reset/confirm'), isEmpty);
  });

  testWidgets("the server's reason for refusing a new password is shown", (tester) async {
    final backend = FakeBackend((r) => switch (r.path) {
          '/api/auth/password/reset/request' => resetSent(),
          '/api/auth/password/reset/confirm' => const FakeReply(400, {
              'success': false, 'message': 'One or more validation errors occurred.', 'data': null,
              'errors': ['NewPassword: This password is too common. Choose a less predictable one.'],
            }),
          _ => demoServer(r),
        });
    await start(tester, backend);
    await openReset(tester);
    await fill(tester, 'Mobile number', '9000000001');
    await tapText(tester, 'Send code');
    await fill(tester, '6-digit code', '123456');
    await fill(tester, 'New password', 'password1234!');
    await fill(tester, 'Confirm new password', 'password1234!');
    await tapText(tester, 'Set new password');
    expect(find.text('This password is too common. Choose a less predictable one.'), findsOneWidget);
  });

  testWidgets('a signed-in citizen changes the password and keeps the new session', (tester) async {
    final backend = FakeBackend((r) => r.path == '/api/auth/password/change'
        ? signedIn(access: 'access-2', refresh: 'refresh-2')
        : demoServer(r));
    final app = await start(tester, backend, signedIn: true);

    await tester.tap(find.byTooltip('Change password'));
    await tester.pumpAndSettle();
    await fill(tester, 'Current password', 'old-secret');
    await fill(tester, 'New password', _strong);
    await fill(tester, 'Confirm new password', _strong);
    await tester.ensureVisible(find.widgetWithText(FilledButton, 'Change password'));
    await tester.tap(find.widgetWithText(FilledButton, 'Change password'));
    await tester.pumpAndSettle();

    expect(backend.requests.singleWhere((r) => r.path == '/api/auth/password/change').data,
        {'currentPassword': 'old-secret', 'newPassword': _strong});
    expect(await app.tokens.readRefreshToken(), 'refresh-2');
    expect(find.text('Password changed. Other devices have been signed out.'), findsOneWidget);
  });

  testWidgets('the reset screen is translated', (tester) async {
    await start(tester, FakeBackend(demoServer), language: 'mr');
    await useEmail(tester, label: 'ईमेल व पासवर्ड');
    await tapText(tester, 'पासवर्ड विसरलात?');
    expect(find.text('आपला पासवर्ड रीसेट करा'), findsWidgets);
  });
}
