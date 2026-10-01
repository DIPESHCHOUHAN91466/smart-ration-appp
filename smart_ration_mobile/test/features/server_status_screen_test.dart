import 'package:dio/dio.dart';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';

import '../support/fake_backend.dart';
import '../support/test_app.dart';

/// Opens the app signed out (it starts on the sign-in screen) and taps "Check server connection".
Future<void> openServerStatus(WidgetTester tester, FakeBackend backend, {String language = 'en'}) async {
  final app = await TestApp.build(backend, savedLanguage: language);
  await tester.pumpWidget(app.widget);
  await tester.pumpAndSettle();
  // The button is at the bottom of the sign-in form: scroll to it like a user would.
  await tester.scrollUntilVisible(find.byIcon(Icons.dns_outlined), 200, scrollable: find.byType(Scrollable).first);
  await tester.tap(find.byIcon(Icons.dns_outlined));
  await tester.pumpAndSettle();
}

void main() {
  testWidgets('shows the server as connected when it is healthy', (tester) async {
    final backend = FakeBackend((_) => healthyServer);
    await openServerStatus(tester, backend);

    expect(find.text('Server status'), findsOneWidget);
    expect(find.text('Connected to the server'), findsOneWidget);
    expect(find.text('Working'), findsNWidgets(2));
    expect(find.text('Demo data (synthetic)'), findsOneWidget);
    expect(backend.paths, ['/health']);
  });

  testWidgets('a degraded server is still connected', (tester) async {
    final backend =
        FakeBackend((_) => const FakeReply(200, {'status': 'degraded', 'database': 'healthy', 'dataMode': 'synthetic'}));
    await openServerStatus(tester, backend);

    expect(find.text('Connected to the server'), findsOneWidget);
    expect(find.text('Partly working'), findsOneWidget);
  });

  testWidgets('no network shows a plain message and a working retry button', (tester) async {
    var calls = 0;
    final backend = FakeBackend((_) => ++calls == 1 ? const FakeReply.fails(DioExceptionType.connectionError) : healthyServer);
    await openServerStatus(tester, backend);

    expect(find.text('Unable to connect. Please check your internet connection.'), findsOneWidget);
    await tester.tap(find.text('Try again'));
    await tester.pumpAndSettle();
    expect(find.text('Connected to the server'), findsOneWidget);
  });

  testWidgets('errors are shown in the chosen language', (tester) async {
    final backend = FakeBackend((_) => const FakeReply.fails(DioExceptionType.connectionError));
    await openServerStatus(tester, backend, language: 'mr');

    expect(find.text('कनेक्ट होऊ शकले नाही. कृपया तुमचे इंटरनेट कनेक्शन तपासा.'), findsOneWidget);
    expect(find.text('पुन्हा प्रयत्न करा'), findsOneWidget);
  });
}
