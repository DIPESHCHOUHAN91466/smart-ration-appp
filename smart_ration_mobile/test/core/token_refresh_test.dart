import 'package:dio/dio.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:smart_ration_mobile/core/network/api_client.dart';
import 'package:smart_ration_mobile/core/network/api_exception.dart';
import 'package:smart_ration_mobile/core/storage/token_storage.dart';
import 'package:smart_ration_mobile/features/auth/token_refresher.dart';

import '../support/fake_backend.dart';

/// An API client wired like the app's, with a fake backend. [expired] counts sign-outs.
class Harness {
  Harness(FakeReply Function(RequestOptions) handler, {Duration delay = Duration.zero})
      : backend = FakeBackend(handler, delay: delay) {
    refresher = TokenRefresher(
      dio: ApiClient.createDio('http://test.local', adapter: backend),
      storage: tokens,
      onSessionExpired: () => expired++,
    );
    api = ApiClient.create(
        baseUrl: 'http://test.local', tokens: tokens, refreshAccessToken: refresher.refresh, adapter: backend);
  }

  final FakeBackend backend;
  final tokens = MemoryTokenStorage();
  late final TokenRefresher refresher;
  late final ApiClient api;
  int expired = 0;

  Future<void> signedInWith(String access) => tokens.saveSession(accessToken: access, refreshToken: 'old-refresh', userJson: '{}');

  int get refreshCalls => backend.paths.where((p) => p == '/api/auth/refresh').length;
}

/// Accepts only the token `fresh-access`; anything else is "expired" (401).
FakeReply backendWithNewTokens(RequestOptions r) {
  if (r.path == '/api/auth/refresh') return signedIn(access: 'fresh-access', refresh: 'new-refresh');
  return r.headers['Authorization'] == 'Bearer fresh-access'
      ? FakeReply.ok({'ok': true})
      : FakeReply.fail(401, 'Authentication required.');
}

void main() {
  test('an expired access token is refreshed once and the request is retried', () async {
    final h = Harness(backendWithNewTokens);
    await h.signedInWith('stale-access');

    expect(await h.api.get<Map<String, dynamic>>('/api/ration/bookings'), {'ok': true});
    expect(h.backend.paths, ['/api/ration/bookings', '/api/auth/refresh', '/api/ration/bookings']);
    expect(h.backend.requests[1].data, {'refreshToken': 'old-refresh'});
    expect(await h.tokens.readAccessToken(), 'fresh-access');
    expect(await h.tokens.readRefreshToken(), 'new-refresh');
    expect(h.expired, 0);
  });

  test('requests that fail together share ONE refresh (refresh tokens work only once)', () async {
    final h = Harness(backendWithNewTokens, delay: const Duration(milliseconds: 20));
    await h.signedInWith('stale-access');

    final results = await Future.wait([
      h.api.get<Map<String, dynamic>>('/api/shops'),
      h.api.get<Map<String, dynamic>>('/api/ration/items'),
      h.api.get<Map<String, dynamic>>('/api/notifications'),
    ]);

    expect(results, everyElement({'ok': true}));
    expect(h.refreshCalls, 1);
  });

  test('a rejected refresh token ends the session', () async {
    final h = Harness((r) => FakeReply.fail(401, 'Authentication required.'));
    await h.signedInWith('stale-access');

    await expectLater(
      h.api.get<Object?>('/api/ration/bookings'),
      throwsA(isA<ApiException>().having((e) => e.kind, 'kind', ApiErrorKind.unauthorized)),
    );
    expect(h.expired, 1);
    expect(await h.tokens.readRefreshToken(), isNull);
  });

  test('no internet during a refresh does NOT sign anyone out', () async {
    final h = Harness((r) => r.path == '/api/auth/refresh'
        ? const FakeReply.fails(DioExceptionType.connectionError)
        : FakeReply.fail(401, 'Authentication required.'));
    await h.signedInWith('stale-access');

    await expectLater(
      h.api.get<Object?>('/api/ration/bookings'),
      throwsA(isA<ApiException>().having((e) => e.kind, 'kind', ApiErrorKind.noConnection)),
    );
    expect(h.expired, 0);
    expect(await h.tokens.readRefreshToken(), 'old-refresh');
  });

  test('a request that still fails after one refresh is not retried again', () async {
    final h = Harness((r) => r.path == '/api/auth/refresh'
        ? signedIn(access: 'still-rejected')
        : FakeReply.fail(401, 'Authentication required.'));
    await h.signedInWith('stale-access');

    await expectLater(h.api.get<Object?>('/api/ration/bookings'), throwsA(isA<ApiException>()));
    expect(h.backend.paths, ['/api/ration/bookings', '/api/auth/refresh', '/api/ration/bookings']);
  });

  test('a wrong password on sign-in never triggers a refresh', () async {
    final h = Harness((r) => FakeReply.fail(401, 'Invalid email or password.'));

    await expectLater(h.api.post<Object?>('/api/auth/login', body: {}), throwsA(isA<ApiException>()));
    expect(h.refreshCalls, 0);
    expect(h.expired, 0);
  });
}
