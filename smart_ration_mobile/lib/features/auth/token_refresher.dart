import 'package:dio/dio.dart';

import '../../core/network/api_exception.dart';
import '../../core/storage/token_storage.dart';
import 'session.dart';

/// Swaps the refresh token for a new access token when the old one has expired (after 15 minutes).
///
/// The backend's refresh tokens work only ONCE. If several requests fail at the same moment they
/// all wait for the same single refresh, otherwise the second refresh would be rejected and the
/// user signed out for no reason.
class TokenRefresher {
  TokenRefresher({required this.dio, required this.storage, required this.onSessionExpired});

  /// A plain client without the sign-in interceptors, so a failed refresh can't loop.
  final Dio dio;
  final TokenStorage storage;

  /// Called when the server says the session is over (refresh token expired or revoked).
  final void Function() onSessionExpired;

  Future<String?>? _running;

  /// The new access token, or null when the session is over.
  /// Throws [ApiException] for network problems: being offline must never sign anyone out.
  Future<String?> refresh() => _running ??= _refresh().whenComplete(() => _running = null);

  Future<String?> _refresh() async {
    final refreshToken = await storage.readRefreshToken();
    if (refreshToken == null) return _expired();
    try {
      final response = await dio.post<Object?>('/api/auth/refresh', data: {'refreshToken': refreshToken});
      final body = response.data;
      final result = AuthResult.tryParse(body is Map ? body['data'] : null);
      if (result == null) return await _expired();
      await result.saveTo(storage);
      return result.accessToken;
    } on DioException catch (e) {
      final status = e.response?.statusCode;
      if (status == 400 || status == 401) return await _expired();
      throw ApiException.fromDio(e);
    }
  }

  Future<String?> _expired() async {
    await storage.clear();
    onSessionExpired();
    return null;
  }
}
