import 'package:dio/dio.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:smart_ration_mobile/app/app.dart';
import 'package:smart_ration_mobile/app/env.dart';
import 'package:smart_ration_mobile/core/network/api_client.dart';
import 'package:smart_ration_mobile/core/providers.dart';
import 'package:smart_ration_mobile/core/storage/token_storage.dart';

import '../support/fake_backend.dart';

Widget appWith(FakeBackend backend) => ProviderScope(
      retry: noAutomaticRetry,
      overrides: [
        envProvider.overrideWithValue(Env.parse(environment: 'development', apiBaseUrl: '')),
        apiClientProvider.overrideWithValue(
            ApiClient.create(baseUrl: 'http://test.local', tokens: MemoryTokenStorage(), adapter: backend)),
      ],
      child: const SmartRationApp(),
    );

void main() {
  testWidgets('shows the server as connected when it is healthy', (tester) async {
    final backend = FakeBackend((_) => const FakeReply(200, {
          'status': 'healthy',
          'database': 'healthy',
          'dataMode': 'synthetic',
        }));
    await tester.pumpWidget(appWith(backend));
    await tester.pumpAndSettle();

    expect(find.text('Smart Ration AI'), findsOneWidget);
    expect(find.text('Powered by HSD2C'), findsOneWidget);
    expect(find.text('Connected to the server'), findsOneWidget);
    expect(find.text('healthy'), findsNWidgets(2));
    expect(find.text('Demo data (synthetic)'), findsOneWidget);
    expect(backend.requests.single.path, '/health');
  });

  testWidgets('a degraded server is still connected', (tester) async {
    final backend =
        FakeBackend((_) => const FakeReply(200, {'status': 'degraded', 'database': 'healthy', 'dataMode': 'synthetic'}));
    await tester.pumpWidget(appWith(backend));
    await tester.pumpAndSettle();

    expect(find.text('Connected to the server'), findsOneWidget);
    expect(find.text('degraded'), findsOneWidget);
  });

  testWidgets('no network shows a plain message and a working retry button', (tester) async {
    var calls = 0;
    final backend = FakeBackend((_) {
      calls++;
      return calls == 1
          ? const FakeReply.fails(DioExceptionType.connectionError)
          : const FakeReply(200, {'status': 'healthy', 'database': 'healthy', 'dataMode': 'synthetic'});
    });
    await tester.pumpWidget(appWith(backend));
    await tester.pumpAndSettle();

    expect(find.text('Unable to connect. Please check your internet connection.'), findsOneWidget);
    await tester.tap(find.text('Try again'));
    await tester.pumpAndSettle();
    expect(find.text('Connected to the server'), findsOneWidget);
  });
}
