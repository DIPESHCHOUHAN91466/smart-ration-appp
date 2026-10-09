import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:smart_ration_mobile/app/env.dart';

import '../support/fake_backend.dart';
import '../support/test_app.dart';
import 'auth_flow_test.dart' show useEmail;
import 'register_test.dart' show openRegister;

EditableText box(WidgetTester tester, String label) =>
    tester.widget<EditableText>(find.descendant(of: find.widgetWithText(TextFormField, label), matching: find.byType(EditableText)));

bool obscured(WidgetTester tester, String label) =>
    tester.widget<EditableText>(find.descendant(of: find.widgetWithText(TextFormField, label), matching: find.byType(EditableText))).obscureText;

Future<void> openLogin(WidgetTester tester, Env env) async {
  tester.view.physicalSize = const Size(1080, 3200);
  tester.view.devicePixelRatio = 2.0;
  addTearDown(tester.view.reset);
  final app = await TestApp.build(FakeBackend(demoServer), savedLanguage: 'en', env: env);
  await tester.pumpWidget(app.widget);
  await tester.pumpAndSettle();
  await useEmail(tester);
}

void main() {
  testWidgets('every password box on the registration screen has a show/hide button', (tester) async {
    await openRegister(tester);
    await tester.enterText(find.widgetWithText(TextFormField, 'Password'), 'river lamp mango seven');
    expect(obscured(tester, 'Password'), isTrue);
    expect(obscured(tester, 'Confirm password'), isTrue);

    await tester.tap(find.descendant(of: find.widgetWithText(TextFormField, 'Password'), matching: find.byTooltip('Show password')));
    await tester.pump();
    expect(obscured(tester, 'Password'), isFalse);
    expect(obscured(tester, 'Confirm password'), isTrue, reason: 'each box has its own button');

    await tester.tap(find.descendant(of: find.widgetWithText(TextFormField, 'Password'), matching: find.byTooltip('Hide password')));
    await tester.pump();
    expect(obscured(tester, 'Password'), isTrue);
  });

  testWidgets('a public demo build offers the three roles and fills in email and password', (tester) async {
    await openLogin(tester, Env.parse(environment: 'production', apiBaseUrl: 'https://demo.example.org', demoPassword: 'Demo-pass-123', release: true));
    expect(find.text('Try a demo account'), findsOneWidget);
    expect(find.textContaining('Demo password: Demo-pass-123'), findsOneWidget);

    await tester.ensureVisible(find.widgetWithText(ActionChip, 'Shop Owner'));
    await tester.tap(find.widgetWithText(ActionChip, 'Shop Owner'));
    await tester.pump();
    expect(box(tester, 'Email').controller.text, 'shop@example.com');
    expect(box(tester, 'Password').controller.text, 'Demo-pass-123');
    expect(find.widgetWithText(ActionChip, 'Rural User'), findsOneWidget);
    expect(find.widgetWithText(ActionChip, 'Government Official'), findsOneWidget);
  });

  testWidgets('a normal release build shows no demo accounts and contains no password', (tester) async {
    await openLogin(tester, Env.parse(environment: 'production', apiBaseUrl: 'https://demo.example.org', release: true));
    expect(find.byType(ActionChip), findsNothing);
    expect(find.textContaining('Demo password'), findsNothing);
  });

  testWidgets('a development build fills in the email only', (tester) async {
    await openLogin(tester, Env.parse(environment: 'development', apiBaseUrl: 'http://test.local'));
    await tester.ensureVisible(find.widgetWithText(ActionChip, 'Rural User'));
    await tester.tap(find.widgetWithText(ActionChip, 'Rural User'));
    await tester.pump();
    expect(box(tester, 'Email').controller.text, 'rural@example.com');
    expect(box(tester, 'Password').controller.text, isEmpty);
    expect(find.textContaining('Demo password:'), findsNothing);
  });
}
