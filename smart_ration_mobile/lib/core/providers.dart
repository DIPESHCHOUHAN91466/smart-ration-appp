import 'package:dio/dio.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../app/env.dart';
import '../features/auth/auth_controller.dart';
import '../features/auth/token_refresher.dart';
import 'network/api_client.dart';
import 'storage/token_storage.dart';

/// Shared building blocks. A "provider" hands the same object to every screen that asks for it,
/// and lets tests swap in fakes.

/// Riverpod would otherwise retry a failed request up to 10 times (about 40 seconds) in the background.
/// The app shows the problem at once with a "Try again" button instead, and never resends a request
/// the backend has rejected (such as a full time slot).
Duration? noAutomaticRetry(int retryCount, Object error) => null;

/// Set once in main.dart from the build settings.
final envProvider = Provider<Env>((ref) => throw UnimplementedError('envProvider is set in main.dart'));

final tokenStorageProvider = Provider<TokenStorage>((ref) => SecureTokenStorage());

/// Tests replace this to answer requests without a real server.
final httpAdapterProvider = Provider<HttpClientAdapter?>((ref) => null);

final tokenRefresherProvider = Provider<TokenRefresher>((ref) => TokenRefresher(
      dio: ApiClient.createDio(ref.watch(envProvider).apiBaseUrl, adapter: ref.watch(httpAdapterProvider)),
      storage: ref.watch(tokenStorageProvider),
      // Read only when it happens, so the client and the sign-in state don't depend on each other at start-up.
      onSessionExpired: () => ref.read(authControllerProvider.notifier).sessionExpired(),
    ));

final apiClientProvider = Provider<ApiClient>((ref) {
  final env = ref.watch(envProvider);
  return ApiClient.create(
    baseUrl: env.apiBaseUrl,
    tokens: ref.watch(tokenStorageProvider),
    refreshAccessToken: ref.watch(tokenRefresherProvider).refresh,
    logRequests: env.isDevelopment,
    adapter: ref.watch(httpAdapterProvider),
  );
});
