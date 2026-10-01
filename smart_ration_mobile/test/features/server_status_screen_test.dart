import 'package:dio/dio.dart';
import 'package:flutter_test/flutter_test.dart';

import '../support/fake_backend.dart';
import '../support/test_app.dart';

void main() {
  testWidgets('shows the server as connected when it is healthy', (tester) async {
    final backend = FakeBackend((_) => healthyServer);
    final (app, _) = await buildTestApp(backend, savedLanguage: 'en');
    await tester.pumpWidget(app);
    await tester.pumpAndSettle();

    expect(find.text('Smart Ration AI'), findsOneWidget);
    expect(find.text('Powered by HSD2C'), findsOneWidget);
    expect(find.text('Connected to the server'), findsOneWidget);
    expect(find.text('Working'), findsNWidgets(2));
    expect(find.text('Demo data (synthetic)'), findsOneWidget);
    expect(backend.requests.single.path, '/health');
  });

  testWidgets('a degraded server is still connected', (tester) async {
    final backend =
        FakeBackend((_) => const FakeReply(200, {'status': 'degraded', 'database': 'healthy', 'dataMode': 'synthetic'}));
    final (app, _) = await buildTestApp(backend, savedLanguage: 'en');
    await tester.pumpWidget(app);
    await tester.pumpAndSettle();

    expect(find.text('Connected to the server'), findsOneWidget);
    expect(find.text('Partly working'), findsOneWidget);
  });

  testWidgets('no network shows a plain message and a working retry button', (tester) async {
    var calls = 0;
    final backend = FakeBackend((_) => ++calls == 1 ? const FakeReply.fails(DioExceptionType.connectionError) : healthyServer);
    final (app, _) = await buildTestApp(backend, savedLanguage: 'en');
    await tester.pumpWidget(app);
    await tester.pumpAndSettle();

    expect(find.text('Unable to connect. Please check your internet connection.'), findsOneWidget);
    await tester.tap(find.text('Try again'));
    await tester.pumpAndSettle();
    expect(find.text('Connected to the server'), findsOneWidget);
  });

  testWidgets('errors are shown in the chosen language', (tester) async {
    final backend = FakeBackend((_) => const FakeReply.fails(DioExceptionType.connectionError));
    final (app, _) = await buildTestApp(backend, savedLanguage: 'mr');
    await tester.pumpWidget(app);
    await tester.pumpAndSettle();

    expect(find.text('कनेक्ट होऊ शकले नाही. कृपया तुमचे इंटरनेट कनेक्शन तपासा.'), findsOneWidget);
    expect(find.text('पुन्हा प्रयत्न करा'), findsOneWidget);
  });
}
