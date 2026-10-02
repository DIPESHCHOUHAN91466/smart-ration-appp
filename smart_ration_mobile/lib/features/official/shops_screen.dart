import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../app/routes.dart';
import '../../app/theme.dart';
import '../../core/network/api_exception.dart';
import '../../l10n/app_localizations.dart';
import '../citizen/citizen_widgets.dart';
import 'official_data.dart';
import 'official_words.dart';

/// Every shop, the ones with the worst stock first, filterable by stock status.
class ShopsScreen extends ConsumerStatefulWidget {
  const ShopsScreen({super.key});

  @override
  ConsumerState<ShopsScreen> createState() => _ShopsScreenState();
}

class _ShopsScreenState extends ConsumerState<ShopsScreen> {
  /// null = all shops.
  StockStatus? _only;

  @override
  Widget build(BuildContext context) {
    final l = AppLocalizations.of(context);
    final shops = ref.watch(shopsProvider);
    return Scaffold(
      appBar: AppBar(title: Text(l.statShops)),
      body: RefreshIndicator(
        onRefresh: () => ref.refresh(shopsProvider.future),
        child: ListView(
          padding: const EdgeInsets.all(16),
          children: [
            Wrap(spacing: 8, runSpacing: 8, children: [
              for (final option in <StockStatus?>[null, ...StockStatus.values])
                ChoiceChip(
                  label: Text(option == null ? l.filterAll : stockStatusWord(l, option)),
                  selected: _only == option,
                  onSelected: (_) => setState(() => _only = option),
                ),
            ]),
            const SizedBox(height: 12),
            ...shops.when(
              loading: () => [const SizedBox(height: 60), const Center(child: CircularProgressIndicator())],
              error: (e, _) => [
                Text(e is ApiException ? e.messageIn(l) : l.errorGeneric, textAlign: TextAlign.center),
                TextButton(onPressed: () => ref.invalidate(shopsProvider), child: Text(l.tryAgain)),
              ],
              data: (all) {
                final shown = all.where((s) => _only == null || s.stock == _only).toList()
                  ..sort((a, b) {
                    final byStock = a.stock.index.compareTo(b.stock.index); // critical, low, normal
                    return byStock != 0 ? byStock : a.name.compareTo(b.name);
                  });
                if (shown.isEmpty) return [Text(l.noShops, style: Theme.of(context).textTheme.titleMedium)];
                return [
                  for (final s in shown)
                    Card(
                      margin: const EdgeInsets.only(bottom: 10),
                      child: ListTile(
                        contentPadding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
                        title: Text(s.name, style: const TextStyle(fontWeight: FontWeight.w700, fontSize: 17)),
                        subtitle: Text('${[s.village, s.district].where((p) => p.isNotEmpty).join(', ')}\n'
                            '${l.shopTodayLine(s.bookedToday, s.collectedToday)}'),
                        isThreeLine: true,
                        trailing: StatusPill(text: stockStatusWord(l, s.stock), tone: stockStatusTone(s.stock)),
                        onTap: () => context.push(Routes.officialShop(s.id)),
                      ),
                    ),
                ];
              },
            ),
          ],
        ),
      ),
    );
  }
}

/// One shop: who runs it, where it is, and its stock (read-only for officials here).
class ShopDetailScreen extends ConsumerWidget {
  const ShopDetailScreen({super.key, required this.shopId});

  final int shopId;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final l = AppLocalizations.of(context);
    final detail = ref.watch(shopDetailProvider(shopId));
    return Scaffold(
      appBar: AppBar(title: Text(detail.value?.name ?? l.statShops)),
      body: RefreshIndicator(
        onRefresh: () => ref.refresh(shopDetailProvider(shopId).future),
        child: ListView(
          padding: const EdgeInsets.all(16),
          children: detail.when(
            loading: () => [const SizedBox(height: 80), const Center(child: CircularProgressIndicator())],
            error: (e, _) => [
              Text(e is ApiException ? e.messageIn(l) : l.errorGeneric, textAlign: TextAlign.center),
              TextButton(onPressed: () => ref.invalidate(shopDetailProvider(shopId)), child: Text(l.tryAgain)),
            ],
            data: (d) => [
              SectionCard(
                title: d.name,
                icon: Icons.storefront,
                child: Column(children: [
                  InfoRow(label: l.shopCodeLabel, value: valueText(d.code)),
                  InfoRow(label: l.shopOwnerLabel, value: valueText(d.owner)),
                  InfoRow(label: l.shopPlaceLabel, value: valueText(d.place)),
                ]),
              ),
              const SizedBox(height: 12),
              SectionCard(
                title: l.stockButton,
                icon: Icons.inventory_2_outlined,
                child: d.stock.isEmpty
                    ? Text(l.noStockLines)
                    : Column(children: [
                        for (final s in [...d.stock.where((s) => s.low), ...d.stock.where((s) => !s.low)])
                          Padding(
                            padding: const EdgeInsets.symmetric(vertical: 6),
                            child: Row(children: [
                              Icon(itemIcon(s.rationType), color: AppColors.muted, size: 24),
                              const SizedBox(width: 10),
                              Expanded(
                                child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                                  Text(itemWord(l, s.rationType), style: const TextStyle(fontSize: 16, fontWeight: FontWeight.w600)),
                                  Text('${l.stockMinimum}: ${amount(s.minimum)} ${unitWord(l, s.rationType)}',
                                      style: const TextStyle(color: AppColors.muted)),
                                ]),
                              ),
                              const SizedBox(width: 8),
                              // Quantity above its label, so the row fits small phones with large text.
                              Column(crossAxisAlignment: CrossAxisAlignment.end, children: [
                                Text('${amount(s.available)} ${unitWord(l, s.rationType)}',
                                    style: TextStyle(fontSize: 16, fontWeight: FontWeight.w800, color: s.low ? AppColors.danger : AppColors.ink)),
                                const SizedBox(height: 4),
                                StatusPill(text: s.low ? l.stockLow : l.stockOk, tone: s.low ? PillTone.bad : PillTone.good),
                              ]),
                            ]),
                          ),
                      ]),
              ),
            ],
          ),
        ),
      ),
    );
  }
}
