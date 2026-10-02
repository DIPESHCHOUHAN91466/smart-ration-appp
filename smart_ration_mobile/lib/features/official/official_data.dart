import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../core/network/api_client.dart';
import '../../core/network/api_exception.dart';
import '../../core/providers.dart';
import '../shop/shop_data.dart';

/// The government official's view, on existing read-only backend routes (officials and admins only):
///   GET /api/admin/dashboard        today's totals across all shops
///   GET /api/admin/statistics       the last 30 days: tokens, collections, collection rate, per shop
///   GET /api/shops/map              every shop with today's activity and stock status
///   GET /api/shops/{id}/location    one shop: owner, place and stock lines
///   GET /api/ai/alerts/active       open rule-based warnings (decision support, not proof of fraud)
///   POST /api/ai/alerts/{id}/resolve  mark one under review, resolved or dismissed (officials only)

class OfficialOverview {
  const OfficialOverview({
    required this.beneficiaries,
    required this.shops,
    required this.bookingsToday,
    required this.collectedToday,
    required this.waitingToday,
    required this.handedOutTodayKg,
    required this.lowStockAlerts,
  });

  final int beneficiaries;
  final int shops;
  final int bookingsToday;
  final int collectedToday;
  final int waitingToday;
  final double handedOutTodayKg;
  final int lowStockAlerts;

  static OfficialOverview parse(Object? j) {
    if (j is! Map) throw const ApiException(ApiErrorKind.unknown);
    return OfficialOverview(
      beneficiaries: _int(j['totalBeneficiaries']),
      shops: _int(j['totalShops']),
      bookingsToday: _int(j['todayBookings']),
      collectedToday: _int(j['todayCollections']),
      waitingToday: _int(j['pendingCollections']),
      handedOutTodayKg: _num(j['rationDistributedTodayKg']),
      lowStockAlerts: _int(j['lowStockAlerts']),
    );
  }
}

class PeriodStats {
  const PeriodStats({required this.tokens, required this.collected, required this.cancelled, required this.collectionRate});

  final int tokens;
  final int collected;
  final int cancelled;

  /// Percent of booked tokens that were collected (the backend's figure).
  final double collectionRate;

  static PeriodStats parse(Object? j) {
    if (j is! Map) throw const ApiException(ApiErrorKind.unknown);
    return PeriodStats(
      tokens: _int(j['tokensGenerated']),
      collected: _int(j['collectionsCompleted']),
      cancelled: _int(j['collectionsCancelled']),
      collectionRate: _num(j['collectionEfficiencyPercent']),
    );
  }
}

/// A shop's stock as the backend rates it: Critical, Low or Normal.
enum StockStatus { critical, low, normal }

StockStatus _stockStatus(Object? v) => switch (v) {
      'Critical' => StockStatus.critical,
      'Low' => StockStatus.low,
      _ => StockStatus.normal,
    };

class ShopSummary {
  const ShopSummary({
    required this.id,
    required this.name,
    required this.village,
    required this.district,
    required this.stock,
    required this.bookedToday,
    required this.collectedToday,
  });

  final int id;
  final String name;
  final String village;
  final String district;
  final StockStatus stock;
  final int bookedToday;
  final int collectedToday;

  static ShopSummary? tryParse(Object? j) {
    if (j is! Map || j['id'] is! int) return null;
    return ShopSummary(
      id: j['id'] as int,
      name: _text(j['shopName']),
      village: _text(j['village']),
      district: _text(j['district']),
      stock: _stockStatus(j['inventoryStatus']),
      bookedToday: _int(j['todayBookings']),
      collectedToday: _int(j['completedCollections']),
    );
  }
}

class ShopDetail {
  const ShopDetail({required this.id, required this.name, required this.code, required this.owner, required this.place, required this.stock});

  final int id;
  final String name;
  final String code;
  final String owner;

  /// "Satnavari, Nagpur, Maharashtra"
  final String place;
  final List<StockLine> stock;

  static ShopDetail parse(Object? j) {
    if (j is! Map || j['id'] is! int) throw const ApiException(ApiErrorKind.unknown);
    return ShopDetail(
      id: j['id'] as int,
      name: _text(j['shopName']),
      code: _text(j['shopCode']),
      owner: _text(j['operatorName']),
      place: [j['village'], j['district'], j['state']].whereType<String>().where((s) => s.isNotEmpty).join(', '),
      stock: [for (final i in (j['inventory'] as List? ?? const [])) ?StockLine.tryParse(i)],
    );
  }
}

class AlertItem {
  const AlertItem({
    required this.id,
    required this.type,
    required this.severity,
    required this.shopName,
    required this.description,
    required this.detectedAt,
    this.underReview = false,
    this.note = '',
  });

  final int id;

  /// e.g. RepeatedQrScan, LOW_STOCK (translated where known).
  final String type;

  /// HIGH, MEDIUM or LOW.
  final String severity;
  final String shopName;

  /// The rule's own explanation (English, written by the backend).
  final String description;

  /// UTC, as the backend stores it.
  final DateTime? detectedAt;

  /// An official has started checking it (otherwise it is still Open).
  final bool underReview;

  /// What the official wrote when updating it.
  final String note;

  static AlertItem? tryParse(Object? j) {
    if (j is! Map || j['id'] is! int) return null;
    final at = j['detectedAt'];
    return AlertItem(
      id: j['id'] as int,
      type: _text(j['alertType']),
      severity: _text(j['severity']).toUpperCase(),
      shopName: _text(j['shopName']),
      description: _text(j['description']),
      detectedAt: at is String ? DateTime.tryParse(at.endsWith('Z') ? at : '${at}Z') : null,
      underReview: j['status'] == 'UnderReview',
      note: _text(j['resolutionNote']),
    );
  }
}

/// What an official decides about an alert. Resolved and dismissed alerts leave the open list.
enum AlertDecision {
  underReview('UnderReview'),
  resolved('Resolved'),
  dismissed('Dismissed');

  const AlertDecision(this.wire);

  /// The backend's name for it.
  final String wire;
}

/// Twelve digits, with or without spaces or dashes: looks like an Aadhaar number, which must never
/// be written in a note.
final aadhaarLikePattern = RegExp(r'(?<!\d)\d{4}[\s-]?\d{4}[\s-]?\d{4}(?!\d)');

class OfficialRepository {
  const OfficialRepository(this._api);

  final ApiClient _api;

  Future<OfficialOverview> overview() async => OfficialOverview.parse(await _api.get<Object?>('/api/admin/dashboard'));

  /// The backend's default period: the last 30 days.
  Future<PeriodStats> last30Days() async => PeriodStats.parse(await _api.get<Object?>('/api/admin/statistics'));

  Future<List<ShopSummary>> shops() async {
    final data = await _api.get<Object?>('/api/shops/map');
    return data is List ? [for (final e in data) ?ShopSummary.tryParse(e)] : (throw const ApiException(ApiErrorKind.unknown));
  }

  Future<ShopDetail> shop(int id) async => ShopDetail.parse(await _api.get<Object?>('/api/shops/$id/location'));

  /// Open alerts, most serious first.
  Future<List<AlertItem>> alerts() async {
    final data = await _api.get<Object?>('/api/ai/alerts/active');
    final items = data is Map ? data['items'] : null;
    if (items is! List) throw const ApiException(ApiErrorKind.unknown);
    const rank = {'HIGH': 0, 'MEDIUM': 1, 'LOW': 2};
    return [for (final e in items) ?AlertItem.tryParse(e)]
      ..sort((a, b) => (rank[a.severity] ?? 3).compareTo(rank[b.severity] ?? 3));
  }

  /// Records the official's decision. The backend checks the caller really is an official, and
  /// saying the same thing twice (e.g. a retry) changes nothing further.
  Future<void> updateAlert(int id, AlertDecision decision, {String note = ''}) async {
    await _api.post<Object?>('/api/ai/alerts/$id/resolve', body: {
      'Status': decision.wire,
      if (note.trim().isNotEmpty) 'Note': note.trim(),
    });
  }
}

final officialRepositoryProvider = Provider<OfficialRepository>((ref) => OfficialRepository(ref.watch(apiClientProvider)));

final officialOverviewProvider = FutureProvider.autoDispose<OfficialOverview>((ref) => ref.watch(officialRepositoryProvider).overview());

final periodStatsProvider = FutureProvider.autoDispose<PeriodStats>((ref) => ref.watch(officialRepositoryProvider).last30Days());

final shopsProvider = FutureProvider.autoDispose<List<ShopSummary>>((ref) => ref.watch(officialRepositoryProvider).shops());

final shopDetailProvider = FutureProvider.autoDispose.family<ShopDetail, int>((ref, id) => ref.watch(officialRepositoryProvider).shop(id));

final alertsProvider = FutureProvider.autoDispose<List<AlertItem>>((ref) => ref.watch(officialRepositoryProvider).alerts());

String _text(Object? value) => value is String ? value : '';
int _int(Object? value) => value is int ? value : 0;
double _num(Object? value) => value is num ? value.toDouble() : 0;
