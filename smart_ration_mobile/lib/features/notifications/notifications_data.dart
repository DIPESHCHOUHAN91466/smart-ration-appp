import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../core/network/api_client.dart';
import '../../core/network/api_exception.dart';
import '../../core/providers.dart';

/// The signed-in person's notifications, on the existing backend routes:
///   GET  /api/notifications          mine, newest first
///   POST /api/notifications/read     mark some of mine as read (others' ids are ignored by the backend)

class AppNotification {
  const AppNotification({required this.id, required this.type, required this.title, required this.message, required this.read, this.createdAt});

  final int id;

  /// BookingConfirmed, CollectionCompleted, LowInventory, ... (translated by type in the app).
  final String type;

  /// The backend's own words (English).
  final String title;
  final String message;
  final bool read;

  /// UTC.
  final DateTime? createdAt;

  static AppNotification? tryParse(Object? j) {
    if (j is! Map || j['id'] is! int) return null;
    final at = j['createdAt'];
    return AppNotification(
      id: j['id'] as int,
      type: '${j['type'] ?? ''}',
      title: '${j['title'] ?? ''}',
      message: '${j['message'] ?? ''}',
      read: j['isRead'] == true,
      createdAt: at is String ? DateTime.tryParse(at.endsWith('Z') ? at : '${at}Z') : null,
    );
  }
}

class NotificationsRepository {
  const NotificationsRepository(this._api);

  final ApiClient _api;

  Future<List<AppNotification>> mine() async {
    final data = await _api.get<Object?>('/api/notifications');
    return data is List ? [for (final e in data) ?AppNotification.tryParse(e)] : (throw const ApiException(ApiErrorKind.unknown));
  }

  Future<void> markRead(List<int> ids) => _api.post('/api/notifications/read', body: {'notificationIds': ids});
}

final notificationsRepositoryProvider = Provider<NotificationsRepository>((ref) => NotificationsRepository(ref.watch(apiClientProvider)));

final notificationsProvider =
    FutureProvider.autoDispose<List<AppNotification>>((ref) => ref.watch(notificationsRepositoryProvider).mine());

/// How many are unread (0 while loading or when they can't be fetched).
final unreadCountProvider = Provider.autoDispose<int>(
    (ref) => ref.watch(notificationsProvider).whenOrNull(data: (all) => all.where((n) => !n.read).length) ?? 0);
