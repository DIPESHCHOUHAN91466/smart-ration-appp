import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../app/routes.dart';
import '../../app/theme.dart';
import '../../core/network/api_exception.dart';
import '../../l10n/app_localizations.dart';
import '../citizen/citizen_widgets.dart';
import 'insights_data.dart';
import 'official_data.dart' show StockStatus;
import 'official_words.dart';

/// The website's AI Intelligence Center for the phone: three headline numbers, the demand trend per item,
/// the stock that will run out first and today's expected waits. Open alerts are handled on the alerts screen.
class InsightsScreen extends ConsumerStatefulWidget {
  const InsightsScreen({super.key});

  @override
  ConsumerState<InsightsScreen> createState() => _InsightsScreenState();
}

class _InsightsScreenState extends ConsumerState<InsightsScreen> {
  /// Normal stock lines are hidden until asked for; the list is for what needs attention.
  bool _allStock = false;

  @override
  Widget build(BuildContext context) {
    final l = AppLocalizations.of(context);
    final insights = ref.watch(insightsProvider);
    return Scaffold(
      appBar: AppBar(title: Text(l.aiCenterTitle)),
      body: RefreshIndicator(
        onRefresh: () => ref.refresh(insightsProvider.future),
        child: ListView(
          padding: const EdgeInsets.all(16),
          children: [
            Card(
              color: AppColors.warningSoft,
              child: Padding(
                padding: const EdgeInsets.all(14),
                child: Row(children: [
                  const Icon(Icons.info_outline, color: AppColors.warning),
                  const SizedBox(width: 10),
                  Expanded(child: Text(l.aiCenterNotice, style: const TextStyle(fontSize: 15, fontWeight: FontWeight.w600))),
                ]),
              ),
            ),
            const SizedBox(height: 12),
            ...insights.when(
              loading: () => [const SizedBox(height: 60), const Center(child: CircularProgressIndicator())],
              error: (e, _) => [
                Text(e is ApiException ? e.messageIn(l) : l.errorGeneric, textAlign: TextAlign.center),
                TextButton(onPressed: () => ref.invalidate(insightsProvider), child: Text(l.tryAgain)),
              ],
              data: (i) => _content(context, l, i),
            ),
          ],
        ),
      ),
    );
  }

  List<Widget> _content(BuildContext context, AppLocalizations l, Insights i) {
    final risks = _allStock ? i.stockRisks : i.stockRisks.where((r) => r.status != StockStatus.normal).toList();
    return [
      if (i.demoData) ...[
        Text(l.aiDemoData, style: const TextStyle(color: AppColors.muted)),
        const SizedBox(height: 8),
      ],
      Card(
        child: Padding(
          padding: const EdgeInsets.symmetric(vertical: 16, horizontal: 8),
          child: Row(children: [
            _Tile(label: l.aiShopsAttention, value: '${i.shopsNeedingStock}', color: AppColors.warning),
            _Tile(label: l.aiAverageWait, value: l.minutesShort(amount(i.averageWaitMinutes)), color: AppColors.blue),
            _Tile(label: l.aiAlertsToReview, value: '${i.alertsToReview}', color: AppColors.danger),
          ]),
        ),
      ),
      if (i.alertsToReview > 0) ...[
        const SizedBox(height: 8),
        OutlinedButton.icon(
          icon: const Icon(Icons.notification_important_outlined),
          label: Text(l.alertsButton(i.alertsToReview)),
          onPressed: () => context.push(Routes.officialAlerts),
        ),
      ],
      const SizedBox(height: 12),
      SectionCard(
        title: l.aiDemandTitle,
        icon: Icons.trending_up,
        child: i.demand.isEmpty
            ? Text(l.aiNoDemand)
            : Column(children: [for (final d in i.demand) _DemandRow(trend: d)]),
      ),
      const SizedBox(height: 12),
      SectionCard(
        title: l.aiStockRiskTitle,
        icon: Icons.inventory_2_outlined,
        child: Column(crossAxisAlignment: CrossAxisAlignment.stretch, children: [
          if (risks.isEmpty) Text(l.noLowStock),
          for (final r in risks) _RiskRow(risk: r),
          if (!_allStock && risks.length < i.stockRisks.length)
            TextButton(onPressed: () => setState(() => _allStock = true), child: Text(l.aiShowAllStock)),
        ]),
      ),
      const SizedBox(height: 12),
      SectionCard(
        title: l.aiQueueTitle,
        icon: Icons.groups_outlined,
        child: i.queues.isEmpty
            ? Text(l.aiNoQueue)
            : Column(children: [
                for (final q in i.queues)
                  MergeSemantics(
                    child: ListTile(
                      contentPadding: EdgeInsets.zero,
                      title: Text(q.shopName, style: const TextStyle(fontWeight: FontWeight.w600)),
                      subtitle: Text(l.aiQueueLine(q.waiting)),
                      trailing: Text(l.minutesShort('${q.waitMinutes}'),
                          style: const TextStyle(fontSize: 17, fontWeight: FontWeight.w800, color: AppColors.ink)),
                      onTap: () => context.push(Routes.officialShop(q.shopId)),
                    ),
                  ),
              ]),
      ),
      const SizedBox(height: 24),
    ];
  }
}

class _DemandRow extends StatelessWidget {
  const _DemandRow({required this.trend});

  final DemandTrend trend;

  @override
  Widget build(BuildContext context) {
    final l = AppLocalizations.of(context);
    final d = trend;
    final unit = unitWord(l, d.rationType);
    final up = d.growthPercent >= 0;
    final growth = '${up ? '+' : '−'}${amount(double.parse(d.growthPercent.abs().toStringAsFixed(1)))}%';
    return MergeSemantics(
      child: Padding(
        padding: const EdgeInsets.symmetric(vertical: 6),
        child: Row(children: [
          Icon(itemIcon(d.rationType), color: AppColors.muted, size: 24),
          const SizedBox(width: 10),
          Expanded(
            child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
              Text(itemWord(l, d.rationType), style: const TextStyle(fontSize: 16, fontWeight: FontWeight.w600)),
              Text(l.aiDemandLine('${amount(d.last30)} $unit', '${amount(d.previous30)} $unit'),
                  style: const TextStyle(color: AppColors.muted)),
            ]),
          ),
          const SizedBox(width: 8),
          Column(crossAxisAlignment: CrossAxisAlignment.end, children: [
            Text(l.aiDemandExpected, style: const TextStyle(color: AppColors.muted, fontSize: 13)),
            Text('${amount(d.next30)} $unit', style: const TextStyle(fontSize: 16, fontWeight: FontWeight.w800)),
            // Colour and arrow repeat the sign, so the trend is not shown by colour alone.
            Row(mainAxisSize: MainAxisSize.min, children: [
              Icon(up ? Icons.arrow_upward : Icons.arrow_downward, size: 16, color: up ? AppColors.success : AppColors.danger),
              Text(growth, style: TextStyle(fontWeight: FontWeight.w700, color: up ? AppColors.success : AppColors.danger)),
            ]),
          ]),
        ]),
      ),
    );
  }
}

class _RiskRow extends StatelessWidget {
  const _RiskRow({required this.risk});

  final StockRisk risk;

  @override
  Widget build(BuildContext context) {
    final l = AppLocalizations.of(context);
    final r = risk;
    final days = r.daysUntilReorder;
    final when = days == null ? l.aiNoRecentUse : (days <= 0 ? l.aiReorderNow : l.aiDaysLeft(days.ceil()));
    return InkWell(
      onTap: () => context.push(Routes.officialShop(r.shopId)),
      child: Padding(
        padding: const EdgeInsets.symmetric(vertical: 8),
        child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
          Row(children: [
            Icon(itemIcon(r.rationType), color: AppColors.muted, size: 24),
            const SizedBox(width: 10),
            Expanded(
              child: Text('${itemWord(l, r.rationType)} · ${r.shopName}', style: const TextStyle(fontSize: 16, fontWeight: FontWeight.w600)),
            ),
          ]),
          const SizedBox(height: 4),
          Wrap(spacing: 8, runSpacing: 4, crossAxisAlignment: WrapCrossAlignment.center, children: [
            StatusPill(text: stockStatusWord(l, r.status), tone: stockStatusTone(r.status)),
            Text('${l.stockAvailable}: ${amount(r.available)} ${unitWord(l, r.rationType)}'),
          ]),
          const SizedBox(height: 2),
          Text(when, style: TextStyle(fontWeight: FontWeight.w700, color: days != null && days <= 7 ? AppColors.danger : AppColors.ink)),
        ]),
      ),
    );
  }
}

class _Tile extends StatelessWidget {
  const _Tile({required this.label, required this.value, required this.color});

  final String label;
  final String value;
  final Color color;

  @override
  Widget build(BuildContext context) => Expanded(
        child: MergeSemantics(
          child: Column(children: [
            FittedBox(child: Text(value, style: TextStyle(fontSize: 24, fontWeight: FontWeight.w800, color: color))),
            const SizedBox(height: 2),
            Text(label, textAlign: TextAlign.center, style: const TextStyle(color: AppColors.muted, fontSize: 13)),
          ]),
        ),
      );
}
