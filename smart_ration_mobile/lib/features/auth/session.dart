import 'dart:convert';

import '../../core/storage/token_storage.dart';

/// The four roles the backend knows. The backend decides the role; the app only reads it.
enum AppRole {
  ruralUser('RuralUser'),
  shopOwner('ShopOwner'),
  governmentOfficial('GovernmentOfficial'),
  admin('Admin');

  const AppRole(this.apiName);

  /// The exact word the backend sends, e.g. "ShopOwner".
  final String apiName;

  static AppRole? fromApi(Object? value) => AppRole.values.where((r) => r.apiName == value).firstOrNull;
}

/// Who is signed in, as reported by the backend at sign-in.
class SessionUser {
  const SessionUser({
    required this.id,
    required this.fullName,
    required this.email,
    required this.mobileNumber,
    required this.role,
    this.rationShopId,
  });

  final int id;
  final String fullName;
  final String email;
  final String mobileNumber;
  final AppRole role;

  /// Set for shop owners only: the one shop they may serve.
  final int? rationShopId;

  /// Returns null when the data is incomplete or the role is unknown, so a damaged or outdated
  /// saved session is treated as "signed out" instead of crashing.
  static SessionUser? tryParse(Object? json) {
    if (json is! Map) return null;
    final id = json['id'];
    final role = AppRole.fromApi(json['role']);
    if (id is! int || role == null) return null;
    final shop = json['rationShopId'];
    return SessionUser(
      id: id,
      fullName: json['fullName'] is String ? json['fullName'] as String : '',
      email: json['email'] is String ? json['email'] as String : '',
      mobileNumber: json['mobileNumber'] is String ? json['mobileNumber'] as String : '',
      role: role,
      rationShopId: shop is int ? shop : null,
    );
  }

  Map<String, Object?> toJson() => {
        'id': id,
        'fullName': fullName,
        'email': email,
        'mobileNumber': mobileNumber,
        'role': role.apiName,
        'rationShopId': rationShopId,
      };
}

/// What `/api/auth/login` and `/api/auth/refresh` return inside `data`.
class AuthResult {
  const AuthResult({required this.accessToken, required this.refreshToken, required this.user});

  final String accessToken;
  final String refreshToken;
  final SessionUser user;

  static AuthResult? tryParse(Object? data) {
    if (data is! Map) return null;
    final access = data['accessToken'];
    final refresh = data['refreshToken'];
    final user = SessionUser.tryParse(data['user']);
    if (access is! String || refresh is! String || user == null) return null;
    return AuthResult(accessToken: access, refreshToken: refresh, user: user);
  }

  Future<void> saveTo(TokenStorage storage) =>
      storage.saveSession(accessToken: accessToken, refreshToken: refreshToken, userJson: jsonEncode(user.toJson()));
}

/// Reads a saved session at app start. Anything incomplete is wiped and counts as signed out.
Future<SessionUser?> restoreSession(TokenStorage storage) async {
  try {
    final refresh = await storage.readRefreshToken();
    final userJson = await storage.readUserJson();
    if (refresh == null || userJson == null) return null;
    final user = SessionUser.tryParse(jsonDecode(userJson));
    if (user == null) await storage.clear();
    return user;
  } on Object {
    // Unreadable storage (e.g. after the phone's lock settings changed): start signed out.
    await storage.clear();
    return null;
  }
}
