import 'dart:convert';

import 'package:flutter_secure_storage/flutter_secure_storage.dart';

/// Copies of backend answers kept on the phone so the most important screens (the citizen's token
/// and its QR) still work without internet. Stored encrypted (Android Keystore), keyed by the
/// signed-in user, and wiped on sign-out.
abstract class OfflineStore {
  Future<String?> read(String key);
  Future<void> write(String key, String value);
  Future<void> clearAll();
}

class SecureOfflineStore implements OfflineStore {
  SecureOfflineStore([FlutterSecureStorage? storage]) : _storage = storage ?? const FlutterSecureStorage();

  final FlutterSecureStorage _storage;
  static const _prefix = 'offline.';

  @override
  Future<String?> read(String key) => _storage.read(key: '$_prefix$key');

  @override
  Future<void> write(String key, String value) => _storage.write(key: '$_prefix$key', value: value);

  @override
  Future<void> clearAll() async {
    final all = await _storage.readAll();
    for (final key in all.keys.where((k) => k.startsWith(_prefix))) {
      await _storage.delete(key: key);
    }
  }
}

/// In memory only. Used by tests.
class MemoryOfflineStore implements OfflineStore {
  final Map<String, String> values = {};

  @override
  Future<String?> read(String key) async => values[key];

  @override
  Future<void> write(String key, String value) async => values[key] = value;

  @override
  Future<void> clearAll() async => values.clear();
}

/// A saved backend answer and when it was saved.
class SavedCopy {
  const SavedCopy(this.data, this.savedAt);

  final Object? data;
  final DateTime savedAt;

  String encode() => jsonEncode({'savedAt': savedAt.toUtc().toIso8601String(), 'data': data});

  static SavedCopy? decode(String? text) {
    if (text == null) return null;
    try {
      final j = jsonDecode(text);
      final at = j is Map ? DateTime.tryParse('${j['savedAt']}') : null;
      return at == null ? null : SavedCopy(j['data'], at.toLocal());
    } on FormatException {
      return null;
    }
  }
}
