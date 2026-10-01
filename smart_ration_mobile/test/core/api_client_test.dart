import 'package:dio/dio.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:smart_ration_mobile/core/network/api_client.dart';
import 'package:smart_ration_mobile/core/network/api_exception.dart';
import 'package:smart_ration_mobile/core/storage/token_storage.dart';

import '../support/fake_backend.dart';

ApiClient clientFor(FakeBackend backend, {TokenStorage? tokens}) =>
    ApiClient.create(baseUrl: 'http://test.local', tokens: tokens ?? MemoryTokenStorage(), adapter: backend);

void main() {
  group('ApiClient', () {
    test('returns only the data part of the backend envelope', () async {
      final backend = FakeBackend((_) => const FakeReply(200, {
            'success': true,
            'message': 'Success',
            'data': {'id': 7, 'shopName': 'Fair Price Shop 12'},
            'errors': null,
          }));
      final data = await clientFor(backend).get<Map<String, dynamic>>('/api/shops/7');
      expect(data, {'id': 7, 'shopName': 'Fair Price Shop 12'});
      expect(backend.requests.single.uri.toString(), 'http://test.local/api/shops/7');
    });

    test('sends the saved sign-in token', () async {
      final tokens = MemoryTokenStorage();
      await tokens.saveTokens(accessToken: 'abc.def.ghi', refreshToken: 'r');
      final backend = FakeBackend((_) => const FakeReply(200, {'success': true, 'data': null}));
      await clientFor(backend, tokens: tokens).get<void>('/api/ration/bookings');
      expect(backend.requests.single.headers['Authorization'], 'Bearer abc.def.ghi');
    });

    test('sends no Authorization header when signed out', () async {
      final backend = FakeBackend((_) => const FakeReply(200, {'success': true, 'data': null}));
      await clientFor(backend).get<void>('/api/shops');
      expect(backend.requests.single.headers.containsKey('Authorization'), isFalse);
    });

    test('a rejected booking keeps the backend message and code', () async {
      final backend = FakeBackend((_) => const FakeReply(409, {
            'success': false,
            'message': 'This time slot is full. Please choose another slot.',
            'data': null,
            'errors': null,
            'errorCode': 'SLOT_FULL',
          }));
      final error = await clientFor(backend).post<void>('/api/ration/bookings', body: {}).then<Object?>(
            (_) => null,
            onError: (Object e) => e,
          );
      expect(error, isA<ApiException>());
      final e = error! as ApiException;
      expect(e.kind, ApiErrorKind.conflict);
      expect(e.userMessage, 'This time slot is full. Please choose another slot.');
      expect(e.errorCode, 'SLOT_FULL');
    });

    test('getJson returns accepted error bodies such as 503 from /health', () async {
      final backend = FakeBackend((_) => const FakeReply(503, {'status': 'unhealthy', 'database': 'unhealthy'}));
      final body = await clientFor(backend).getJson('/health', acceptedStatuses: {503});
      expect(body['status'], 'unhealthy');
    });

    test('no network becomes a friendly message', () async {
      final backend = FakeBackend((_) => const FakeReply.fails(DioExceptionType.connectionError));
      await expectLater(
        clientFor(backend).get<void>('/api/shops'),
        throwsA(isA<ApiException>()
            .having((e) => e.kind, 'kind', ApiErrorKind.noConnection)
            .having((e) => e.userMessage, 'message', 'Unable to connect. Please check your internet connection.')),
      );
    });
  });
}
