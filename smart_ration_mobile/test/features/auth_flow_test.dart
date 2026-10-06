import 'dart:convert';

import 'package:dio/dio.dart';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:smart_ration_mobile/features/auth/auth_controller.dart';
import 'package:smart_ration_mobile/features/citizen/citizen_home_screen.dart';

import '../support/fake_backend.dart';
import '../support/test_app.dart';

Future<TestApp> start(WidgetTester tester, FakeBackend backend, {String language = 'en', bool signedIn = false}) async {
  final app = await TestApp.build(backend, savedLanguage: language, signedInAs: signedIn ? citizen() : null);
  await tester.pumpWidget(app.widget);
  await tester.pumpAndSettle();
  return app;
}

/// Switches to the email & password tab (the sign-in screen opens on mobile & code).
Future<void> useEmail(WidgetTester tester, {String label = 'Email & password'}) async {
  await tester.tap(find.text(label));
  await tester.pumpAndSettle();
}

Future<void> signIn(WidgetTester tester, String email, String password) async {
  if (find.widgetWithText(TextFormField, 'Email').evaluate().isEmpty) await useEmail(tester);
  await tester.enterText(find.widgetWithText(TextFormField, 'Email'), email);
  await tester.enterText(find.widgetWithText(TextFormField, 'Password'), password);
  await tester.ensureVisible(find.widgetWithText(FilledButton, 'Sign in'));   // the form scrolls on small screens
  await tester.pumpAndSettle();
  await tester.tap(find.widgetWithText(FilledButton, 'Sign in'));
  await tester.pumpAndSettle();
}

void main() {
  testWidgets('a citizen signs in and reaches the citizen dashboard', (tester) async {
    final backend = FakeBackend((r) => r.path == '/api/auth/login' ? signedIn() : demoServer(r));
    final app = await start(tester, backend);

    await signIn(tester, '  rural@example.com ', 'secret-pass');

    expect(find.text('Namaste, Asha Devi'), findsOneWidget);
    expect(find.text('Rural User'), findsOneWidget);
    expect(find.byType(CitizenHomeScreen), findsOneWidget);
    // The email is trimmed; the password is sent as typed.
    expect(backend.requests.singleWhere((r) => r.path == '/api/auth/login').data, {'email': 'rural@example.com', 'password': 'secret-pass'});
    // The session is saved so the next launch opens signed in.
    expect(await app.tokens.readRefreshToken(), 'refresh-1');
    expect(jsonDecode((await app.tokens.readUserJson())!)['role'], 'RuralUser');
  });

  testWidgets('a shop owner lands on the shop dashboard with their shop', (tester) async {
    final backend = FakeBackend((r) => r.path == '/api/shop/dashboard'
        ? shopServer(r)
        : signedIn(user: userJson(id: 3, fullName: 'Ramesh Patil', role: 'ShopOwner', rationShopId: 3)));
    await start(tester, backend);

    await signIn(tester, 'shop@example.com', 'secret-pass');

    expect(find.text('Namaste, Ramesh Patil'), findsOneWidget);
    expect(find.text('Shop Owner'), findsOneWidget);
    expect(find.text('Satnavari Ration Shop'), findsOneWidget);
  });

  testWidgets('a wrong password keeps you on the sign-in screen with a plain message', (tester) async {
    final backend = FakeBackend((_) => FakeReply.fail(401, 'Invalid email or password.'));
    final app = await start(tester, backend);

    await signIn(tester, 'rural@example.com', 'wrong');

    expect(find.text('The email or password is not correct.'), findsOneWidget);
    expect(find.byType(CitizenHomeScreen), findsNothing);
    expect(await app.tokens.readRefreshToken(), isNull);
  });

  testWidgets('the wrong-password message is translated', (tester) async {
    final backend = FakeBackend((_) => FakeReply.fail(401, 'Invalid email or password.'));
    await start(tester, backend, language: 'hi');
    await useEmail(tester, label: 'ईमेल और पासवर्ड');

    await tester.enterText(find.widgetWithText(TextFormField, 'ईमेल'), 'rural@example.com');
    await tester.enterText(find.widgetWithText(TextFormField, 'पासवर्ड'), 'wrong');
    await tester.tap(find.widgetWithText(FilledButton, 'साइन इन करें'));
    await tester.pumpAndSettle();

    expect(find.text('ईमेल या पासवर्ड सही नहीं है।'), findsOneWidget);
  });

  testWidgets('empty or invalid fields are caught before anything is sent', (tester) async {
    final backend = FakeBackend((_) => signedIn());
    await start(tester, backend);
    await useEmail(tester);

    await tester.tap(find.widgetWithText(FilledButton, 'Sign in'));
    await tester.pumpAndSettle();
    expect(find.text('Please enter your email.'), findsOneWidget);
    expect(find.text('Please enter your password.'), findsOneWidget);

    await signIn(tester, 'not-an-email', 'x');
    expect(find.text('Please enter a valid email address.'), findsOneWidget);
    expect(backend.requests, isEmpty);
  });

  testWidgets('a saved session opens straight on the dashboard, without signing in again', (tester) async {
    final backend = FakeBackend(demoServer);
    await start(tester, backend, signedIn: true);

    expect(find.text('Namaste, Asha Devi'), findsOneWidget);
    expect(backend.paths, isNot(contains('/api/auth/login')));
  });

  testWidgets('signing out returns to sign-in and cancels the session on the server', (tester) async {
    final backend = FakeBackend((_) => FakeReply.ok(null));
    final app = await start(tester, backend, signedIn: true);

    await tester.tap(find.byTooltip('Sign out'));
    await tester.pumpAndSettle();

    expect(find.text('We will send a 6-digit code to your registered mobile number.'), findsOneWidget);
    expect(await app.tokens.readRefreshToken(), isNull);
    final logout = backend.requests.singleWhere((r) => r.path == '/api/auth/logout');
    expect(logout.data, {'refreshToken': 'saved-refresh'});
  });

  testWidgets('signing out works without internet', (tester) async {
    final backend = FakeBackend((_) => const FakeReply.fails(DioExceptionType.connectionError));
    final app = await start(tester, backend, signedIn: true);

    await tester.tap(find.byTooltip('Sign out'));
    await tester.pumpAndSettle();

    expect(find.widgetWithText(FilledButton, 'Send code'), findsOneWidget);
    expect(await app.tokens.readRefreshToken(), isNull);
  });

  testWidgets('an ended session sends you to sign-in and says why', (tester) async {
    await start(tester, FakeBackend(demoServer), signedIn: true);
    expect(find.byType(CitizenHomeScreen), findsOneWidget);

    containerOf(tester.element(find.byType(CitizenHomeScreen))).read(authControllerProvider.notifier).sessionExpired();
    await tester.pumpAndSettle();

    expect(find.text('Your session has ended. Please sign in again.'), findsOneWidget);
  });
}
