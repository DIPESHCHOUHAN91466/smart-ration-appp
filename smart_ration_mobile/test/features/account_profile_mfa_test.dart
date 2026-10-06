import 'dart:convert';

import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:qr_flutter/qr_flutter.dart';
import 'package:smart_ration_mobile/features/auth/session.dart';

import '../support/fake_backend.dart';
import '../support/test_app.dart';
import 'account_test.dart' show FakeSaver, openAccount;

SessionUser official() => SessionUser.tryParse(userJson(id: 4, fullName: 'District Government Officer', role: 'GovernmentOfficial'))!;

Map<String, Object?> profileJson({String fullName = 'Asha Devi', String mobile = '9800000007', String role = 'RuralUser', int id = 7}) =>
    {...userJson(id: id, fullName: fullName, role: role), 'mobileNumber': mobile};

FakeReply mfa({required bool enabled, bool available = true}) => FakeReply.ok({'enabled': enabled, 'available': available});

const wrongCode = FakeReply(400, {
  'success': false,
  'message': 'One or more validation errors occurred.',
  'data': null,
  'errors': ['Code: The code is wrong or has expired. Use the current code from your authenticator app.'],
});

Future<void> fill(WidgetTester tester, String label, String value) async {
  final field = find.widgetWithText(TextFormField, label);
  await tester.ensureVisible(field);
  await tester.enterText(field, value);
}

Future<void> tapButton(WidgetTester tester, String text) async {
  final button = find.ancestor(of: find.text(text), matching: find.bySubtype<ButtonStyleButton>());
  await tester.ensureVisible(button);
  await tester.pumpAndSettle();
  await tester.tap(button);
  await tester.pumpAndSettle();
}

void main() {
  setUp(() {
    final view = TestWidgetsFlutterBinding.instance.platformDispatcher.views.first;
    view.physicalSize = const Size(1080, 3000);
    view.devicePixelRatio = 3;
  });
  tearDown(() => TestWidgetsFlutterBinding.instance.platformDispatcher.views.first.reset());

  testWidgets('the profile shows the email read-only and saves a new name and mobile number', (tester) async {
    var saved = profileJson();
    final backend = FakeBackend((r) => switch ((r.method, r.path)) {
          ('GET', '/api/users/profile') => FakeReply.ok(saved),
          ('PUT', '/api/users/profile') => FakeReply.ok(saved = profileJson(fullName: 'Asha Devi Patil', mobile: '9811111111')),
          _ => demoServer(r),
        });
    final app = await openAccount(tester, backend, FakeSaver());

    expect(find.text('asha@example.com'), findsOneWidget);
    expect(find.widgetWithText(TextFormField, 'Current password'), findsNothing);
    await fill(tester, 'Full name', '  Asha Devi Patil ');
    await fill(tester, 'Mobile number', '+91 98111 11111');
    await tester.pumpAndSettle();
    // A new number needs the password: sign-in codes and password resets go to it.
    await tapButton(tester, 'Save');
    expect(find.text('Please enter your password.'), findsOneWidget);
    expect(backend.requests.where((r) => r.method == 'PUT'), isEmpty);

    await fill(tester, 'Current password', 'my-password');
    await tapButton(tester, 'Save');

    expect(backend.requests.singleWhere((r) => r.method == 'PUT').data,
        {'fullName': 'Asha Devi Patil', 'mobileNumber': '9811111111', 'currentPassword': 'my-password'});
    expect(find.widgetWithText(TextFormField, 'Current password'), findsNothing);   // saved: the field goes away
    expect(find.text('Profile saved'), findsOneWidget);
    // The phone's saved session shows the new name too, so the next launch greets the person correctly.
    final savedUser = jsonDecode((await app.tokens.readUserJson())!) as Map;
    expect(savedUser['fullName'], 'Asha Devi Patil');
    expect(savedUser['mobileNumber'], '9811111111');
    expect(await app.tokens.readRefreshToken(), 'saved-refresh');   // still the same session
  });

  testWidgets('a bad name or number is caught before sending, and a number in use is explained', (tester) async {
    final backend = FakeBackend((r) => switch ((r.method, r.path)) {
          ('GET', '/api/users/profile') => FakeReply.ok(profileJson()),
          ('PUT', '/api/users/profile') => const FakeReply(409, {
              'success': false, 'message': 'Another account already uses this mobile number.', 'data': null, 'errors': null}),
          _ => demoServer(r),
        });
    await openAccount(tester, backend, FakeSaver());

    await fill(tester, 'Full name', 'A');
    await fill(tester, 'Mobile number', '12345');
    await tapButton(tester, 'Save');
    expect(find.text('Please enter your full name.'), findsOneWidget);
    expect(backend.requests.where((r) => r.method == 'PUT'), isEmpty);

    await fill(tester, 'Full name', 'Asha Devi');
    await fill(tester, 'Mobile number', '9822222222');
    await tester.pumpAndSettle();
    await fill(tester, 'Current password', 'my-password');
    await tapButton(tester, 'Save');
    expect(find.text('Another account already uses this mobile number.'), findsOneWidget);
    expect(find.text('Profile saved'), findsNothing);
  });

  testWidgets('a name change alone sends no password; a wrong password is explained in Hindi', (tester) async {
    final backend = FakeBackend((r) => switch ((r.method, r.path)) {
          ('GET', '/api/users/profile') => FakeReply.ok(profileJson()),
          ('PUT', '/api/users/profile') when (r.data as Map).containsKey('currentPassword') => const FakeReply(400, {
              'success': false, 'message': 'One or more validation errors occurred.', 'data': null,
              'errors': ['CurrentPassword: The password is incorrect.']}),
          ('PUT', '/api/users/profile') => FakeReply.ok(profileJson(fullName: 'आशा देवी')),
          _ => demoServer(r),
        });
    await openAccount(tester, backend, FakeSaver(), language: 'hi');

    await fill(tester, 'पूरा नाम', 'आशा देवी');
    await tapButton(tester, 'सहेजें');
    expect(backend.requests.singleWhere((r) => r.method == 'PUT').data, {'fullName': 'आशा देवी', 'mobileNumber': '9800000007'});

    await fill(tester, 'मोबाइल नंबर', '9822222222');
    await tester.pumpAndSettle();
    await fill(tester, 'वर्तमान पासवर्ड', 'wrong');
    await tapButton(tester, 'सहेजें');
    expect(find.text('पासवर्ड गलत है।'), findsOneWidget);
  });

  testWidgets('a citizen sees whether Aadhaar, ration card and mobile are verified; no two-factor card', (tester) async {
    final backend = FakeBackend((r) => switch (r.path) {
          '/api/users/profile' => FakeReply.ok(profileJson()),
          '/api/beneficiaries/me' => FakeReply.ok({
              ...citizenProfileJson(),
              'mobileVerification': {'mobileMasked': '******0007', 'status': 'Pending'},
            }),
          _ => demoServer(r),
        });
    await openAccount(tester, backend, FakeSaver());

    expect(find.text('My verification'), findsOneWidget);
    expect(find.text('XXXX-XXXX-7173'), findsOneWidget);   // only ever the masked Aadhaar
    expect(find.text('PB-DEMO-0001'), findsOneWidget);
    expect(find.text('Verified'), findsNWidgets(2));
    expect(find.text('Pending'), findsOneWidget);
    expect(find.text('Demo data: this is not a real ration card.'), findsOneWidget);
    expect(find.text('Two-factor sign-in'), findsNothing);
    expect(backend.paths, isNot(contains('/api/auth/mfa/status')));
  });

  testWidgets('a shop owner turns on two-factor sign-in: password, QR and key, then a code', (tester) async {
    var enabled = false;
    final backend = FakeBackend((r) => switch ((r.method, r.path)) {
          ('GET', '/api/users/profile') => FakeReply.ok(profileJson(id: 3, role: 'ShopOwner')),
          ('GET', '/api/auth/mfa/status') => mfa(enabled: enabled),
          ('POST', '/api/auth/mfa/setup') => FakeReply.ok({
              'secret': 'JBSWY3DPEHPK3PXP',
              'otpauthUri': 'otpauth://totp/SmartRation:shop%40example.com?secret=JBSWY3DPEHPK3PXP&issuer=SmartRation',
              'issuer': 'SmartRation',
            }),
          ('POST', '/api/auth/mfa/enable') => r.data['code'] == '111111' ? wrongCode : (() {
              enabled = true;
              return mfa(enabled: true);
            })(),
          _ => demoServer(r),
        });
    await openAccount(tester, backend, FakeSaver(), user: shopOwner());

    expect(find.text('Two-factor sign-in'), findsOneWidget);
    expect(find.text('My verification'), findsNothing);
    await tapButton(tester, 'Set up two-factor sign-in');
    expect(find.text('Please enter your password.'), findsOneWidget);   // nothing sent without the password
    expect(backend.paths, isNot(contains('/api/auth/mfa/setup')));

    await fill(tester, 'Current password', 'my-password');
    await tapButton(tester, 'Set up two-factor sign-in');
    expect(backend.requests.singleWhere((r) => r.path == '/api/auth/mfa/setup').data, {'password': 'my-password'});
    expect(find.byType(QrImageView), findsOneWidget);
    expect(find.text('JBSWY3DPEHPK3PXP'), findsOneWidget);

    await fill(tester, '6-digit code', '111111');
    await tapButton(tester, 'Turn on');
    expect(find.text('The code is wrong or has expired. Use the current code from your authenticator app.'), findsOneWidget);
    expect(find.byType(QrImageView), findsOneWidget);   // still setting up

    await fill(tester, '6-digit code', '123456');
    await tapButton(tester, 'Turn on');
    expect(find.text('Two-factor sign-in is on.'), findsWidgets);
    expect(find.text('Turn off two-factor sign-in'), findsOneWidget);
    expect(find.byType(QrImageView), findsNothing);
  });

  testWidgets('an official turns two-factor sign-in off with the password and a code', (tester) async {
    var enabled = true;
    final backend = FakeBackend((r) => switch ((r.method, r.path)) {
          ('GET', '/api/users/profile') => FakeReply.ok(profileJson(id: 4, role: 'GovernmentOfficial')),
          ('GET', '/api/auth/mfa/status') => mfa(enabled: enabled),
          ('POST', '/api/auth/mfa/disable') => (() {
              enabled = false;
              return mfa(enabled: false);
            })(),
          _ => demoServer(r),
        });
    await openAccount(tester, backend, FakeSaver(), user: official());

    await fill(tester, 'Current password', 'my-password');
    await fill(tester, '6-digit code', '654321');
    await tapButton(tester, 'Turn off two-factor sign-in');

    expect(backend.requests.singleWhere((r) => r.path == '/api/auth/mfa/disable').data, {'password': 'my-password', 'code': '654321'});
    expect(find.text('Two-factor sign-in is off.'), findsOneWidget);
    expect(find.text('Set up two-factor sign-in'), findsOneWidget);
  });

  testWidgets('staff on a server without two-factor sign-in do not see the card', (tester) async {
    final backend = FakeBackend((r) => switch (r.path) {
          '/api/users/profile' => FakeReply.ok(profileJson(id: 3, role: 'ShopOwner')),
          '/api/auth/mfa/status' => mfa(enabled: false, available: false),
          _ => demoServer(r),
        });
    await openAccount(tester, backend, FakeSaver(), user: shopOwner());
    expect(find.text('Two-factor sign-in'), findsNothing);
    expect(find.text('My profile'), findsOneWidget);
  });
}
