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

  /// Throws [MfaRequired] for a staff account with two-factor sign-in: the password was right, and the
  /// code from the authenticator app finishes the sign-in ([verifyMfa]).
  Future<AuthResult> login(String email, String password) async {
    final data = await _api.post<Object?>('/api/auth/login', body: {'email': email.trim(), 'password': password});
    if (data is Map && data['mfaRequired'] == true && data['mfaToken'] is String) throw MfaRequired(data['mfaToken'] as String);
    return AuthResult.tryParse(data) ?? (throw const ApiException(ApiErrorKind.unknown));
  }

  /// Second sign-in step for two-factor accounts: the pending sign-in (5 minutes) and the app's 6-digit code.
  Future<AuthResult> verifyMfa(String mfaToken, String code) async {
    final data = await _api.post<Object?>('/api/auth/mfa/verify', body: {'mfaToken': mfaToken, 'code': code});
    return AuthResult.tryParse(data) ?? (throw const ApiException(ApiErrorKind.unknown));
  }

  /// Asks the backend to text a sign-in code. The answer is the same whether or not the number is
  /// registered (the backend never reveals which numbers have accounts).
  Future<OtpSent> requestOtp(String mobile) async {
    final data = await _api.post<Object?>('/api/auth/otp/request', body: {'mobileNumber': mobile});
    return OtpSent.tryParse(data) ?? (throw const ApiException(ApiErrorKind.unknown));
  }

  Future<AuthResult> verifyOtp(String mobile, String code) async {
    final data = await _api.post<Object?>('/api/auth/otp/verify', body: {'mobileNumber': mobile, 'otp': code});
    return AuthResult.tryParse(data) ?? (throw const ApiException(ApiErrorKind.unknown));
  }

  /// Texts a password-reset code to the account's registered mobile (any role). Same answer whether or not the
  /// number is registered.
  Future<OtpSent> requestPasswordReset(String mobile) async {
    final data = await _api.post<Object?>('/api/auth/password/reset/request', body: {'mobileNumber': mobile});
    return OtpSent.tryParse(data) ?? (throw const ApiException(ApiErrorKind.unknown));
  }

  /// Sets the new password with the code; every session of the account ends.
  Future<void> confirmPasswordReset(String mobile, String code, String newPassword) => _api.post<Object?>(
      '/api/auth/password/reset/confirm', body: {'mobileNumber': mobile, 'otp': code, 'newPassword': newPassword});

  /// Changes the password while signed in; the answer is the new session for this phone.
  Future<AuthResult> changePassword(String current, String newPassword) async {
    final data = await _api.post<Object?>('/api/auth/password/change',
        body: {'currentPassword': current, 'newPassword': newPassword});
    return AuthResult.tryParse(data) ?? (throw const ApiException(ApiErrorKind.unknown));
  }

  /// Tells the backend to cancel the refresh token, so a copied token can't be used later.
  Future<void> logout(String refreshToken) => _api.post<Object?>('/api/auth/logout', body: {'refreshToken': refreshToken});
}

/// The password was right, but the account uses two-factor sign-in: no session yet. [token] is the pending
/// sign-in for [AuthRepository.verifyMfa]; it is not an access token and is never saved.
class MfaRequired implements Exception {
  const MfaRequired(this.token);

  final String token;
}

/// What `/api/auth/otp/request` answers.
class OtpSent {
  const OtpSent({required this.mobileMasked, required this.resendAfterSeconds, this.demoCode});

  final String mobileMasked;
  final int resendAfterSeconds;

  /// Only sent by a development server in demo mode; always null in production.
  final String? demoCode;

  static OtpSent? tryParse(Object? data) {
    if (data is! Map || data['mobileMasked'] is! String) return null;
    final wait = data['resendAfterSeconds'];
    final demo = data['demoOtpValue'];
    return OtpSent(
      mobileMasked: data['mobileMasked'] as String,
      resendAfterSeconds: wait is int ? wait : 30,
      demoCode: demo is String && demo.isNotEmpty ? demo : null,
    );
  }
}

/// '98765 43210', '+91 98765-43210', '098765 43210' -> '9876543210'; null if it is not a 10-digit
/// Indian mobile number. The backend applies the same rule.
String? normalizeMobile(String input) {
  var digits = input.replaceAll(RegExp(r'[\s\-()]'), '');
  if (digits.startsWith('+91')) {
    digits = digits.substring(3);
  } else if (digits.length == 12 && digits.startsWith('91')) {
    digits = digits.substring(2);
  } else if (digits.length == 11 && digits.startsWith('0')) {
    digits = digits.substring(1);
  }
  return RegExp(r'^[6-9]\d{9}$').hasMatch(digits) ? digits : null;
}

final authRepositoryProvider = Provider<AuthRepository>((ref) => AuthRepository(ref.watch(apiClientProvider)));

/// The session found on the phone at start-up (set in main.dart; null = signed out).
final restoredSessionProvider = Provider<SessionUser?>((ref) => null);

/// Who is signed in right now, or null. Screens and the router watch this.
class AuthController extends Notifier<SessionUser?> {
  TokenStorage get _storage => ref.read(tokenStorageProvider);

  @override
  SessionUser? build() => ref.read(restoredSessionProvider);

  /// Throws [ApiException] when the backend refuses (wrong password, too many attempts, offline…), and
  /// [MfaRequired] when the account needs the two-factor code.
  Future<void> signIn(String email, String password) async =>
      _start(await ref.read(authRepositoryProvider).login(email, password));

  /// Second step for staff with two-factor sign-in, after [signIn] threw [MfaRequired].
  Future<void> signInWithMfa(String mfaToken, String code) async =>
      _start(await ref.read(authRepositoryProvider).verifyMfa(mfaToken, code));

  /// Every other device is signed out by the backend; this phone continues with the new session.
  Future<void> changePassword(String current, String newPassword) async =>
      _start(await ref.read(authRepositoryProvider).changePassword(current, newPassword));

  /// Sign-in with the code texted to a citizen's mobile. Throws [ApiException] like [signIn].
  Future<void> signInWithOtp(String mobile, String code) async =>
      _start(await ref.read(authRepositoryProvider).verifyOtp(mobile, code));

  /// The person changed their name or mobile number: the saved session shows the new details too.
  Future<void> profileUpdated(SessionUser user) async {
    final access = await _storage.readAccessToken();
    final refresh = await _storage.readRefreshToken();
    if (state == null || user.id != state!.id || access == null || refresh == null) return;
    await AuthResult(accessToken: access, refreshToken: refresh, user: user).saveTo(_storage);
    state = user;
  }

  Future<void> _start(AuthResult result) async {
    await result.saveTo(_storage);
    ref.read(sessionExpiredNoticeProvider.notifier).set(false);
    state = result.user;
  }

  /// Signs out on this phone at once, then asks the backend to cancel the session.
  /// Being offline doesn't stop the user from signing out.
  Future<void> signOut() async {
    final refreshToken = await _storage.readRefreshToken();
    await _storage.clear();
    await ref.read(offlineStoreProvider).clearAll(); // saved tokens and QR codes go too
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
    ref.read(offlineStoreProvider).clearAll().ignore(); // saved tokens and QR codes go too
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
