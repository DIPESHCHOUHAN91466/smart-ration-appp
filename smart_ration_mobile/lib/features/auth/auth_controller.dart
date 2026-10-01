import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../core/network/api_client.dart';
import '../../core/network/api_exception.dart';
import '../../core/providers.dart';
import '../../core/storage/token_storage.dart';
import 'session.dart';

/// Talks to the backend's /api/auth routes.
class AuthRepository {
  const AuthRepository(this._api);

  final ApiClient _api;

  Future<AuthResult> login(String email, String password) async {
    final data = await _api.post<Object?>('/api/auth/login', body: {'email': email.trim(), 'password': password});
    return AuthResult.tryParse(data) ?? (throw const ApiException(ApiErrorKind.unknown));
  }

  /// Tells the backend to cancel the refresh token, so a copied token can't be used later.
  Future<void> logout(String refreshToken) => _api.post<Object?>('/api/auth/logout', body: {'refreshToken': refreshToken});
}

final authRepositoryProvider = Provider<AuthRepository>((ref) => AuthRepository(ref.watch(apiClientProvider)));

/// The session found on the phone at start-up (set in main.dart; null = signed out).
final restoredSessionProvider = Provider<SessionUser?>((ref) => null);

/// Who is signed in right now, or null. Screens and the router watch this.
class AuthController extends Notifier<SessionUser?> {
  TokenStorage get _storage => ref.read(tokenStorageProvider);

  @override
  SessionUser? build() => ref.read(restoredSessionProvider);

  /// Throws [ApiException] when the backend refuses (wrong password, too many attempts, offline…).
  Future<void> signIn(String email, String password) async {
    final result = await ref.read(authRepositoryProvider).login(email, password);
    await result.saveTo(_storage);
    ref.read(sessionExpiredNoticeProvider.notifier).set(false);
    state = result.user;
  }

  /// Signs out on this phone at once, then asks the backend to cancel the session.
  /// Being offline doesn't stop the user from signing out.
  Future<void> signOut() async {
    final refreshToken = await _storage.readRefreshToken();
    await _storage.clear();
    state = null;
    if (refreshToken != null) {
      try {
        await ref.read(authRepositoryProvider).logout(refreshToken);
      } on ApiException {
        // Best effort: the token still expires on its own after 7 days.
      }
    }
  }

  /// Called when the backend rejects the refresh token (expired after 7 days, or revoked).
  void sessionExpired() {
    if (state == null) return;
    ref.read(sessionExpiredNoticeProvider.notifier).set(true);
    state = null;
  }
}

final authControllerProvider = NotifierProvider<AuthController, SessionUser?>(AuthController.new);

/// True after the app signed someone out because their session ended, so the sign-in screen can
/// explain why they are there.
class SessionExpiredNotice extends Notifier<bool> {
  @override
  bool build() => false;

  void set(bool value) => state = value;
}

final sessionExpiredNoticeProvider = NotifierProvider<SessionExpiredNotice, bool>(SessionExpiredNotice.new);
