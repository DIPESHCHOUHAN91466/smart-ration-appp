import 'package:flutter_secure_storage/flutter_secure_storage.dart';

/// Where the sign-in session is kept between app launches: the two tokens and a short summary of
/// the signed-in user (name, role), so the app can open signed in even without internet.
abstract class TokenStorage {
  Future<String?> readAccessToken();
  Future<String?> readRefreshToken();
  Future<String?> readUserJson();
  Future<void> saveSession({required String accessToken, required String refreshToken, required String userJson});
  Future<void> clear();
}

/// The real storage: Android's encrypted Keystore, which other apps cannot read.
class SecureTokenStorage implements TokenStorage {
  SecureTokenStorage([FlutterSecureStorage? storage]) : _storage = storage ?? const FlutterSecureStorage();

  final FlutterSecureStorage _storage;
  static const _accessKey = 'access_token';
  static const _refreshKey = 'refresh_token';
  static const _userKey = 'session_user';

  @override
  Future<String?> readAccessToken() => _storage.read(key: _accessKey);

  @override
  Future<String?> readRefreshToken() => _storage.read(key: _refreshKey);

  @override
  Future<String?> readUserJson() => _storage.read(key: _userKey);

  @override
  Future<void> saveSession({required String accessToken, required String refreshToken, required String userJson}) async {
    await _storage.write(key: _accessKey, value: accessToken);
    await _storage.write(key: _refreshKey, value: refreshToken);
    await _storage.write(key: _userKey, value: userJson);
  }

  @override
  Future<void> clear() async {
    await _storage.delete(key: _accessKey);
    await _storage.delete(key: _refreshKey);
    await _storage.delete(key: _userKey);
  }
}

/// Keeps the session in memory only. Used by tests.
class MemoryTokenStorage implements TokenStorage {
  String? _access;
  String? _refresh;
  String? _user;

  @override
  Future<String?> readAccessToken() async => _access;

  @override
  Future<String?> readRefreshToken() async => _refresh;

  @override
  Future<String?> readUserJson() async => _user;

  @override
  Future<void> saveSession({required String accessToken, required String refreshToken, required String userJson}) async {
    _access = accessToken;
    _refresh = refreshToken;
    _user = userJson;
  }

  @override
  Future<void> clear() async {
    _access = null;
    _refresh = null;
    _user = null;
  }
}
