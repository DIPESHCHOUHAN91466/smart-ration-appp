import 'package:dio/dio.dart';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:smart_ration_mobile/features/auth/auth_controller.dart';
import 'package:smart_ration_mobile/features/citizen/citizen_home_screen.dart';

import '../support/fake_backend.dart';
import '../support/test_app.dart';

FakeReply codeSent({String? demo = '123456'}) => FakeReply.ok(
    {'mobileMasked': '******0001', 'expiresInSeconds': 300, 'resendAfterSeconds': 30, 'demoOtpValue': demo});

/// The backend: sends a code, and accepts only 123456.
FakeReply otpBackend(RequestOptions r) => switch (r.path) {
      '/api/auth/otp/request' => codeSent(),
      '/api/auth/otp/verify' => (r.data as Map)['otp'] == '123456'
          ? signedIn()
          : FakeReply.fail(401, 'The code is wrong or has expired.'),
      _ => demoServer(r),
    };

Future<TestApp> start(WidgetTester tester, FakeBackend backend, {String language = 'en'}) async {
  final app = await TestApp.build(backend, savedLanguage: language);
  await tester.pumpWidget(app.widget);
  await tester.pumpAndSettle();
  return app;
}

Future<void> askForCode(WidgetTester tester, String mobile) async {
  await tester.enterText(find.widgetWithText(TextFormField, 'Mobile number'), mobile);
  await tester.tap(find.widgetWithText(FilledButton, 'Send code'));
  await tester.pumpAndSettle();
}

Future<void> enterCode(WidgetTester tester, String code) async {
  await tester.enterText(find.widgetWithText(TextFormField, '6-digit code'), code);
  await tester.tap(find.widgetWithText(FilledButton, 'Sign in'));
  await tester.pump();
  await tester.pump(const Duration(milliseconds: 100));
}

void main() {
  test('mobile numbers are cleaned the same way as on the backend', () {
    for (final input in ['9000000001', '90000 00001', '+91 9000000001', '+91-90000-00001', '09000000001', '919000000001']) {
      expect(normalizeMobile(input), '9000000001', reason: input);
    }
    for (final input in ['12345', '1234567890', '5000000001', '90000000011', '', 'abcdefghij']) {
      expect(normalizeMobile(input), isNull, reason: input);
    }
  });

  testWidgets('a citizen signs in with their mobile number and the texted code', (tester) async {
    final backend = FakeBackend(otpBackend);
    final app = await start(tester, backend);

    await askForCode(tester, '+91 90000 00001');
    expect(find.text("If ******0001 is registered, a code has been sent to it and to the account's email."), findsOneWidget);
    expect(find.text('Development demo code: 123456'), findsOneWidget);
    expect(backend.requests.last.data, {'mobileNumber': '9000000001'});

    await enterCode(tester, '123456');
    await tester.pumpAndSettle();

    expect(find.byType(CitizenHomeScreen), findsOneWidget);
    expect(find.text('Namaste, Asha Devi'), findsOneWidget);
    expect(backend.requests.singleWhere((r) => r.path == '/api/auth/otp/verify').data, {'mobileNumber': '9000000001', 'otp': '123456'});
    expect(await app.tokens.readRefreshToken(), 'refresh-1');
  });

  testWidgets('a wrong code shows a plain message and keeps the code screen', (tester) async {
    await start(tester, FakeBackend(otpBackend));
    await askForCode(tester, '9000000001');

    await enterCode(tester, '000000');
    await tester.pumpAndSettle();

    expect(find.text('The code is wrong or has expired. Please try again or ask for a new code.'), findsOneWidget);
    expect(find.byType(CitizenHomeScreen), findsNothing);
  });

  testWidgets('a wrong code message is translated', (tester) async {
    await start(tester, FakeBackend(otpBackend), language: 'mr');
    await tester.enterText(find.widgetWithText(TextFormField, 'मोबाइल नंबर'), '9000000001');
    await tester.tap(find.widgetWithText(FilledButton, 'कोड पाठवा'));
    await tester.pumpAndSettle();
    await tester.enterText(find.widgetWithText(TextFormField, '6 अंकी कोड'), '000000');
    await tester.tap(find.widgetWithText(FilledButton, 'साइन इन करा'));
    await tester.pumpAndSettle();

    expect(find.text('कोड चुकीचा आहे किंवा त्याची मुदत संपली आहे. कृपया पुन्हा प्रयत्न करा किंवा नवीन कोड मागवा.'), findsOneWidget);
  });

  testWidgets('an invalid number or code is caught before anything is sent', (tester) async {
    final backend = FakeBackend(otpBackend);
    await start(tester, backend);

    await askForCode(tester, '12345');
    expect(find.text('Please enter a 10-digit mobile number.'), findsOneWidget);
    expect(backend.requests, isEmpty);

    await askForCode(tester, '9000000001');
    await tester.enterText(find.widgetWithText(TextFormField, '6-digit code'), '12');
    await tester.tap(find.widgetWithText(FilledButton, 'Sign in'));
    await tester.pumpAndSettle();
    expect(find.text('Please enter the 6-digit code.'), findsOneWidget);
    expect(backend.paths.where((p) => p == '/api/auth/otp/verify'), isEmpty);
  });

  testWidgets('a new code can be asked for only after the wait, and the number can be changed', (tester) async {
    final backend = FakeBackend(otpBackend);
    await start(tester, backend);
    await askForCode(tester, '9000000001');

    expect(find.text('Send a new code in 30 s'), findsOneWidget);
    expect(tester.widget<TextButton>(find.widgetWithText(TextButton, 'Send a new code in 30 s')).onPressed, isNull);

    await tester.pump(const Duration(seconds: 31));
    await tester.tap(find.text('Send a new code'));
    await tester.pumpAndSettle();
    expect(backend.paths.where((p) => p == '/api/auth/otp/request').length, 2);

    await tester.tap(find.text('Change number'));
    await tester.pumpAndSettle();
    expect(find.widgetWithText(TextFormField, 'Mobile number'), findsOneWidget);
    await tester.pump(const Duration(seconds: 31)); // let the resend timer end
  });

  testWidgets('if the SMS cannot be sent, the app suggests email and password', (tester) async {
    final backend = FakeBackend((_) => const FakeReply(503, {
          'success': false,
          'message': 'Could not send the code right now.',
          'data': null,
          'errors': null,
          'errorCode': 'SMS_UNAVAILABLE',
        }));
    await start(tester, backend);
    await askForCode(tester, '9000000001');

    expect(find.text('The code could not be sent right now. Please try again, or sign in with email and password.'),
        findsOneWidget);
  });

  testWidgets('the demo code is never shown when the server does not send one', (tester) async {
    await start(tester, FakeBackend((_) => codeSent(demo: null)));
    await askForCode(tester, '9000000001');

    expect(find.textContaining('demo code'), findsNothing);
    await tester.pump(const Duration(seconds: 31));
  });

  testWidgets('staff are told to use email and password', (tester) async {
    await start(tester, FakeBackend(otpBackend));
    expect(find.text('Ration shop owners and officials sign in with email and password.'), findsOneWidget);
  });
}
