import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';

import '../support/fake_backend.dart';
import 'auth_flow_test.dart' show signIn, start;

FakeReply challenge() => FakeReply.ok({'mfaRequired': true, 'mfaToken': 'pending-1', 'mfaExpiresInSeconds': 300});

Map<String, Object?> official() => userJson(id: 7, fullName: 'Officer Kale', role: 'GovernmentOfficial');

Future<void> enterCode(WidgetTester tester, String code) async {
  await tester.enterText(find.widgetWithText(TextFormField, 'Code from the authenticator app'), code);
  await tester.tap(find.widgetWithText(FilledButton, 'Sign in'));
  await tester.pumpAndSettle();
}

void main() {
  testWidgets('staff with two-factor sign-in enter the app code after the password', (tester) async {
    final backend = FakeBackend((r) => switch (r.path) {
          '/api/auth/login' => challenge(),
          '/api/auth/mfa/verify' => signedIn(user: official()),
          _ => officialServer(r),
        });
    final app = await start(tester, backend);

    await signIn(tester, 'officer@example.com', 'secret-pass');
    expect(find.textContaining('Two-factor sign-in is on'), findsOneWidget);
    expect(await app.tokens.readRefreshToken(), isNull);           // no session from the password alone

    await enterCode(tester, '123456');
    expect(backend.requests.singleWhere((r) => r.path == '/api/auth/mfa/verify').data, {'mfaToken': 'pending-1', 'code': '123456'});
    expect(await app.tokens.readRefreshToken(), 'refresh-1');
    expect(find.text('Namaste, Officer Kale'), findsOneWidget);
  });

  testWidgets('a wrong code keeps the code step with a plain message', (tester) async {
    final backend = FakeBackend((r) => r.path == '/api/auth/login'
        ? challenge()
        : FakeReply(401, {'success': false, 'message': 'x', 'data': null, 'errors': null, 'errorCode': 'MFA_CODE_INVALID'}));
    final app = await start(tester, backend);
    await signIn(tester, 'officer@example.com', 'secret-pass');

    await enterCode(tester, '000000');
    expect(find.text('The code is wrong or has expired. Use the current code from your authenticator app.'), findsOneWidget);
    expect(find.widgetWithText(TextFormField, 'Code from the authenticator app'), findsOneWidget);
    expect(await app.tokens.readRefreshToken(), isNull);
  });

  testWidgets('an expired pending sign-in starts again from the password', (tester) async {
    final backend = FakeBackend((r) => r.path == '/api/auth/login'
        ? challenge()
        : FakeReply(401, {'success': false, 'message': 'x', 'data': null, 'errors': null, 'errorCode': 'MFA_PENDING_INVALID'}));
    await start(tester, backend);
    await signIn(tester, 'officer@example.com', 'secret-pass');

    await enterCode(tester, '123456');
    expect(find.text('The sign-in took too long. Please enter your email and password again.'), findsOneWidget);
    expect(find.widgetWithText(TextFormField, 'Password'), findsOneWidget);
  });

  testWidgets('"Start again" returns to email and password', (tester) async {
    await start(tester, FakeBackend((_) => challenge()));
    await signIn(tester, 'officer@example.com', 'secret-pass');
    await tester.ensureVisible(find.text('Start again'));
    await tester.pumpAndSettle();
    await tester.tap(find.text('Start again'));
    await tester.pumpAndSettle();
    expect(find.widgetWithText(TextFormField, 'Email'), findsOneWidget);
  });

  testWidgets('the code step is translated', (tester) async {
    await start(tester, FakeBackend((_) => challenge()), language: 'hi');
    await tester.tap(find.text('ईमेल और पासवर्ड'));
    await tester.pumpAndSettle();
    await tester.enterText(find.widgetWithText(TextFormField, 'ईमेल'), 'officer@example.com');
    await tester.enterText(find.widgetWithText(TextFormField, 'पासवर्ड'), 'secret-pass');
    await tester.tap(find.byType(FilledButton).first);
    await tester.pumpAndSettle();
    expect(find.textContaining('दो-चरणीय साइन इन चालू है'), findsOneWidget);
  });
}
