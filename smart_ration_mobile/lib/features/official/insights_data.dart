import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../core/network/api_exception.dart';
import '../../core/providers.dart';
import 'official_data.dart' show StockStatus;

/// The officials' AI insights, from one backend route (officials and admins only):
///   GET /api/ai/intelligence-center   rule-based demand trend, stock risk, today's queue and open alerts.
/// The backend also re-runs its alert rules on this call (as the website does). These are rules over real
/// records, not a learned model, and they support decisions; they never act on their own.

class DemandTrend {
  const DemandTrend({required this.rationType, required this.last30, required this.previous30, required this.growthPercent, required this.next30});

  final String rationType;
  final double last30;
  final double previous30;
  final double growthPercent;

  /// The last 30 days carried forward at the same growth.
  final double next30;

  /// Items nobody collected in the last 60 days say nothing about demand.
  bool get hasHistory => last30 > 0 || previous30 > 0;

  static DemandTrend? tryParse(Object? j) {
    if (j is! Map || j['rationType'] is! String) return null;
    return DemandTrend(
      rationType: j['rationType'] as String,
      last30: _num(j['last30DaysKg']),
      previous30: _num(j['previous30DaysKg']),
      growthPercent: _num(j['growthPercent']),
      next30: _num(j['predictedNext30DaysKg']),
    );
  }
}

class StockRisk {
  const StockRisk({
    required this.shopId,
    required this.shopName,
    required this.rationType,
    required this.status,
    required this.available,
    required this.daysUntilReorder,
    required this.explanation,
  });

  final int shopId;
  final String shopName;
  final String rationType;
  final StockStatus status;
  final double available;

  /// Days until it falls to the minimum level at the recent rate; null when nothing was handed out lately.
  final double? daysUntilReorder;

  /// The rule's English explanation.
  final String explanation;

  static StockRisk? tryParse(Object? j) {
    if (j is! Map || j['shopId'] is! int || j['rationType'] is! String) return null;
    final days = j['predictedDaysUntilReorder'];
    return StockRisk(
      shopId: j['shopId'] as int,
      shopName: j['shopName'] is String ? j['shopName'] as String : '',
      rationType: j['rationType'] as String,
      status: switch (j['currentStatus']) {
        'CRITICAL' => StockStatus.critical,
        'LOW' => StockStatus.low,
        _ => StockStatus.normal,
      },
      available: _num(j['availableQuantity']),
      daysUntilReorder: days is num ? days.toDouble() : null,
      explanation: j['explanation'] is String ? j['explanation'] as String : '',
    );
  }
}

class QueueForecast {
  const QueueForecast({required this.shopId, required this.shopName, required this.waiting, required this.waitMinutes});

  final int shopId;
  final String shopName;
  final int waiting;
  final int waitMinutes;

  static QueueForecast? tryParse(Object? j) {
    if (j is! Map || j['shopId'] is! int) return null;
    return QueueForecast(
      shopId: j['shopId'] as int,
      shopName: j['shopName'] is String ? j['shopName'] as String : '',
      waiting: j['pendingInQueue'] is int ? j['pendingInQueue'] as int : 0,
      waitMinutes: _num(j['predictedWaitMinutes']).round(),
    );
  }
}

class Insights {
  const Insights({
    required this.demand,
    required this.stockRisks,
    required this.queues,
    required this.shopsNeedingStock,
    required this.averageWaitMinutes,
    required this.alertsToReview,
    required this.demoData,
  });

  /// Only items with collections in the last 60 days, the fastest-growing first.
  final List<DemandTrend> demand;

  /// Critical first, then low, then normal; soonest to run out first within each.
  final List<StockRisk> stockRisks;

  /// Only shops with someone still to be served today, the longest wait first.
  final List<QueueForecast> queues;
  final int shopsNeedingStock;
  final double averageWaitMinutes;
  final int alertsToReview;

  /// The backend says its figures come from generated demo records.
  final bool demoData;

  static Insights parse(Object? j) {
    if (j is! Map) throw const ApiException(ApiErrorKind.unknown);
    List<T> list<T>(Object? v, T? Function(Object?) parse) => v is List ? [for (final e in v) ?parse(e)] : <T>[];
    const rank = {StockStatus.critical: 0, StockStatus.low: 1, StockStatus.normal: 2};
    return Insights(
      demand: list(j['demandForecast'], DemandTrend.tryParse).where((d) => d.hasHistory).toList()
        ..sort((a, b) => b.growthPercent.compareTo(a.growthPercent)),
      stockRisks: list(j['inventoryRisks'], StockRisk.tryParse)
        ..sort((a, b) {
          final byStatus = rank[a.status]!.compareTo(rank[b.status]!);
          return byStatus != 0 ? byStatus : (a.daysUntilReorder ?? double.infinity).compareTo(b.daysUntilReorder ?? double.infinity);
        }),
      queues: list(j['queuePredictions'], QueueForecast.tryParse).where((q) => q.waiting > 0).toList()
        ..sort((a, b) => b.waitMinutes.compareTo(a.waitMinutes)),
      shopsNeedingStock: j['shopsRequiringAttention'] is int ? j['shopsRequiringAttention'] as int : 0,
      averageWaitMinutes: _num(j['averageQueueWaitMinutes']),
      alertsToReview: j['anomaliesRequiringReview'] is int ? j['anomaliesRequiringReview'] as int : 0,
      demoData: j['isSyntheticData'] == true,
    );
  }
}

final insightsProvider = FutureProvider.autoDispose<Insights>(
    (ref) async => Insights.parse(await ref.watch(apiClientProvider).get<Object?>('/api/ai/intelligence-center')));

double _num(Object? value) => value is num ? value.toDouble() : 0;
