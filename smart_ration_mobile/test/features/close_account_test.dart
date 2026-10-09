import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';

import '../support/fake_backend.dart';
import '../support/test_app.dart';
import 'account_test.dart' show FakeSaver, openAccount, scrollTo;

const wrongPassword = FakeReply(400, {
  'success': false,
  'message': 'One or more validation errors occurred.',
  'data': null,
  'errors': ['CurrentPassword: The password is incorrect.'],
});

void main() {
  testWidgets('a citizen closes their account with the password and is signed out', (tester) async {
    var attempts = 0;
    final backend = FakeBackend((r) {
      if (r.path != '/api/users/me/close') return demoServer(r);
      attempts++;
      return attempts == 1 ? wrongPassword : FakeReply.ok(null);
    });
    await openAccount(tester, backend, FakeSaver());

    await scrollTo(tester, find.widgetWithText(OutlinedButton, 'Close my account'));
    await tester.tap(find.widgetWithText(OutlinedButton, 'Close my account'));
    await tester.pumpAndSettle();
    final confirm = find.widgetWithText(FilledButton, 'Close my account permanently');

    await scrollTo(tester, confirm);
    await tester.tap(confirm);
    await tester.pumpAndSettle();
    expect(find.text('Please enter your password.'), findsOneWidget);
    expect(backend.requests.where((r) => r.path == '/api/users/me/close'), isEmpty);

    await tester.enterText(find.widgetWithText(TextFormField, 'Current password'), 'not-it');
    await tester.tap(confirm);
    await tester.pumpAndSettle();
    expect(backend.requests.where((r) => r.path == '/api/users/me/close'), hasLength(1));
    expect(find.text('My account'), findsOneWidget, reason: 'a wrong password keeps the person signed in');

    await tester.enterText(find.widgetWithText(TextFormField, 'Current password'), 'the-right-password');
    await tester.tap(confirm);
    await tester.pumpAndSettle();
    final sent = backend.requests.where((r) => r.path == '/api/users/me/close').last;
    expect(sent.data, {'currentPassword': 'the-right-password'});
    expect(find.text('Sign in'), findsWidgets);
  });

  testWidgets('shop owners do not see the card: the office closes staff accounts', (tester) async {
    await openAccount(tester, FakeBackend(shopServer), FakeSaver(), user: shopOwner());
    expect(find.text('Close my account'), findsNothing);
  });
}
