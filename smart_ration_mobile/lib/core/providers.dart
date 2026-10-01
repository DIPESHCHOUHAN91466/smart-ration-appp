import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../app/env.dart';
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

final apiClientProvider = Provider<ApiClient>((ref) {
  final env = ref.watch(envProvider);
  return ApiClient.create(
    baseUrl: env.apiBaseUrl,
    tokens: ref.watch(tokenStorageProvider),
    logRequests: env.isDevelopment,
  );
});
