import 'dart:io';

import 'package:dio/dio.dart';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:smart_ration_mobile/app/router.dart';
import 'package:smart_ration_mobile/app/routes.dart';
import 'package:smart_ration_mobile/features/auth/register_screen.dart';
import 'package:smart_ration_mobile/features/citizen/citizen_home_screen.dart';
import 'package:smart_ration_mobile/features/legal/privacy_screen.dart';
import 'package:smart_ration_mobile/features/legal/privacy_text.dart';

import '../support/fake_backend.dart';
import '../support/test_app.dart';
import 'auth_flow_test.dart' show start;

/// Signed out, on the registration screen (from the sign-in screen's link).
Future<FakeBackend> openRegister(WidgetTester tester, {FakeReply Function(RequestOptions)? register, String language = 'en'}) async {
  tester.view.physicalSize = const Size(1080, 3200);
  tester.view.devicePixelRatio = 2.0;
  addTearDown(tester.view.reset);
  final backend = FakeBackend((r) => r.path == '/api/auth/register' ? (register ?? (_) => signedIn())(r) : demoServer(r));
  await start(tester, backend, language: language);
  await tester.ensureVisible(find.byIcon(Icons.person_add_alt_1_outlined));
  await tester.tap(find.byIcon(Icons.person_add_alt_1_outlined));
  await tester.pumpAndSettle();
  return backend;
}

Future<void> fill(WidgetTester tester, {String password = 'river lamp mango seven', String? confirm}) async {
  await tester.enterText(find.widgetWithText(TextFormField, 'Full name'), '  Asha Devi ');
  await tester.enterText(find.widgetWithText(TextFormField, 'Email'), ' asha@example.com ');
  await tester.enterText(find.widgetWithText(TextFormField, 'Mobile number'), '+91 98765 43210');
  await tester.enterText(find.widgetWithText(TextFormField, 'Password'), password);
  await tester.enterText(find.widgetWithText(TextFormField, 'Confirm password'), confirm ?? password);
}

Future<void> submit(WidgetTester tester) async {
  await tester.ensureVisible(find.widgetWithText(FilledButton, 'Create account'));
  await tester.pumpAndSettle();
  await tester.tap(find.widgetWithText(FilledButton, 'Create account'));
  await tester.pumpAndSettle();
}

List<RequestOptions> registrations(FakeBackend b) => b.requests.where((r) => r.path == '/api/auth/register').toList();

void main() {
  testWidgets('a new citizen registers with consent, is signed in and reaches their dashboard', (tester) async {
    final backend = await openRegister(tester);
    expect(find.byType(RegisterScreen), findsOneWidget);
    expect(find.textContaining('Shop owners and officials get their accounts from the office.'), findsOneWidget);

    await fill(tester);
    await tester.tap(find.byType(Checkbox));
    await submit(tester);

    expect(registrations(backend).single.data, {
      'fullName': 'Asha Devi',
      'email': 'asha@example.com',
      'mobileNumber': '9876543210',
      'password': 'river lamp mango seven',
      'consentToPrivacyPolicy': true,
    });
    expect(find.byType(CitizenHomeScreen), findsOneWidget);
    expect(find.text('Welcome! Your account is ready.'), findsOneWidget);
  });

  testWidgets('without the consent tick nothing is sent', (tester) async {
    final backend = await openRegister(tester);
    await fill(tester);
    await submit(tester);

    expect(find.text('Please read the privacy policy and tick the box to continue.'), findsOneWidget);
    expect(registrations(backend), isEmpty);
  });

  testWidgets('the form checks name, email, mobile, password length and that both passwords match', (tester) async {
    final backend = await openRegister(tester);
    await tester.tap(find.byType(Checkbox));
    await tester.enterText(find.widgetWithText(TextFormField, 'Email'), 'not-an-email');
    await tester.enterText(find.widgetWithText(TextFormField, 'Mobile number'), '12345');
    await tester.enterText(find.widgetWithText(TextFormField, 'Password'), 'short');
    await tester.enterText(find.widgetWithText(TextFormField, 'Confirm password'), 'other');
    await submit(tester);

    expect(find.text('Please enter your full name.'), findsOneWidget);
    expect(find.text('Please enter a valid email address.'), findsOneWidget);
    expect(find.text('Please enter a 10-digit mobile number.'), findsOneWidget);
    expect(find.text('Use at least 12 characters.'), findsOneWidget);
    expect(find.text('The passwords do not match.'), findsOneWidget);
    expect(registrations(backend), isEmpty);
  });

  testWidgets('an existing account and a refused password are explained', (tester) async {
    var answer = const FakeReply(409, {'success': false, 'message': 'An account with this email already exists.', 'data': null, 'errors': null});
    await openRegister(tester, register: (_) => answer);
    await fill(tester);
    await tester.tap(find.byType(Checkbox));
    await submit(tester);
    expect(find.textContaining('already exists. Sign in instead, or reset your password.'), findsOneWidget);

    answer = const FakeReply(400, {
      'success': false, 'message': 'Validation failed', 'data': null, 'errors': ['Password: This password is too common.'],
    });
    await submit(tester);
    expect(find.text('This password is too common.'), findsOneWidget);
    expect(find.byType(RegisterScreen), findsOneWidget);
  });

  testWidgets('"Read the privacy policy" opens it in the app language', (tester) async {
    await openRegister(tester, language: 'hi');
    await tester.ensureVisible(find.byIcon(Icons.privacy_tip_outlined));
    await tester.tap(find.byIcon(Icons.privacy_tip_outlined));
    await tester.pumpAndSettle();

    expect(find.byType(PrivacyScreen), findsOneWidget);
    expect(find.text(privacyPolicy['hi']!.title), findsWidgets);
    expect(find.text(privacyPolicy['hi']!.sections.first.heading), findsOneWidget);
  });

  test('registration and the privacy policy are open without signing in; signed in they lead home', () {
    expect(redirectFor(null, Routes.register), isNull);
    expect(redirectFor(null, Routes.privacy), isNull);
    expect(redirectFor(citizen(), Routes.register), Routes.citizenHome);
    expect(redirectFor(citizen(), Routes.privacy), isNull);
  });

  test("the app's privacy policy is the website's, word for word (run tool/gen_privacy_policy.mjs after a change)", () {
    final web = File('../frontend/src/pages/legal/legalContent.js').readAsStringSync();
    // The website writes each string as a JSON-style "..." literal.
    String literal(String s) => '"${s.replaceAll(r'\', r'\\').replaceAll('"', r'\"')}"';
    for (final MapEntry(key: lang, value: policy) in privacyPolicy.entries) {
      final start = web.indexOf('privacy: {', web.indexOf('  $lang: {'));
      final block = web.substring(start, web.indexOf('terms: {', start));
      expect(block, contains(literal(policy.title)), reason: '$lang title');
      // Every section on the website is in the app...
      final webSections = RegExp(r'^\s*\["', multiLine: true).allMatches(block).length;
      expect(policy.sections.length, webSections, reason: '$lang section count');
      // ...with the same heading and paragraphs.
      for (final section in policy.sections) {
        expect(block, contains(literal(section.heading)), reason: '$lang ${section.heading}');
        for (final p in section.paragraphs) {
          expect(block, contains(literal(p)), reason: '$lang paragraph changed on the website: $p');
        }
      }
    }
  });
}
