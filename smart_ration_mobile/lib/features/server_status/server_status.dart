import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../core/network/api_client.dart';
import '../../core/providers.dart';

/// What the backend's `GET /health` reports.
class ServerStatus {
  const ServerStatus({required this.status, required this.database, required this.dataMode});

  /// `healthy`, `degraded` (works, but an optional part such as the AI service is down) or `unhealthy`.
  final String status;

  /// `healthy` or `unhealthy`.
  final String database;

  /// `synthetic` (demo data) or `real`.
  final String dataMode;

  bool get isHealthy => status == 'healthy';
  bool get isUsable => database == 'healthy';

  factory ServerStatus.fromJson(Map<String, dynamic> json) => ServerStatus(
        status: json['status'] as String? ?? 'unknown',
        database: json['database'] as String? ?? 'unknown',
        dataMode: json['dataMode'] as String? ?? 'unknown',
      );
}

class ServerStatusRepository {
  const ServerStatusRepository(this._api);

  final ApiClient _api;

  /// 503 still carries a status body (the database is down), so it is read rather than treated as a failure.
  Future<ServerStatus> fetch() async => ServerStatus.fromJson(await _api.getJson('/health', acceptedStatuses: {503}));
}

final serverStatusRepositoryProvider =
    Provider<ServerStatusRepository>((ref) => ServerStatusRepository(ref.watch(apiClientProvider)));

final serverStatusProvider =
    FutureProvider.autoDispose<ServerStatus>((ref) => ref.watch(serverStatusRepositoryProvider).fetch());
