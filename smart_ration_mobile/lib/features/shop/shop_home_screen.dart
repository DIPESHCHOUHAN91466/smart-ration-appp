import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../app/routes.dart';
import '../../app/theme.dart';
import '../../core/network/api_exception.dart';
import '../../l10n/app_localizations.dart';
import '../auth/auth_controller.dart';
import 'shop_data.dart';

/// The shop owner's dashboard: today's counts, and the two ways to serve a customer.
class ShopHomeScreen extends ConsumerWidget {
  const ShopHomeScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final l = AppLocalizations.of(context);
    final user = ref.watch(authControllerProvider);
    if (user == null) return const Scaffold(body: SizedBox.shrink());
    final dashboard = ref.watch(shopDashboardProvider);
    final text = Theme.of(context).textTheme;

    // Counts change after every handover, so they are fetched again on return.
    Future<void> open(String route) async {
      await context.push(route);
      ref.invalidate(shopDashboardProvider);
    }

    return Scaffold(
      appBar: AppBar(
        title: Text(l.appTitle),
        actions: [
          IconButton(
            icon: const Icon(Icons.translate),
            tooltip: l.language,
            iconSize: 28,
            onPressed: () => context.push(Routes.changeLanguage),
          ),
          IconButton(
            icon: const Icon(Icons.logout),
            tooltip: l.signOut,
            iconSize: 28,
            onPressed: () => ref.read(authControllerProvider.notifier).signOut(),
          ),
        ],
      ),
      body: RefreshIndicator(
        onRefresh: () => ref.refresh(shopDashboardProvider.future),
        child: ListView(
          padding: const EdgeInsets.all(16),
          children: [
            Text(l.greeting(user.fullName), style: text.headlineSmall?.copyWith(fontWeight: FontWeight.w700)),
            const SizedBox(height: 4),
            Text(l.roleShopOwner, style: const TextStyle(color: AppColors.blue, fontWeight: FontWeight.w600, fontSize: 16)),
            if (dashboard.value case final d?) Text(d.shopName, style: const TextStyle(color: AppColors.muted, fontSize: 16)),
            const SizedBox(height: 16),
            Card(
              child: Padding(
                padding: const EdgeInsets.all(18),
                child: Column(crossAxisAlignment: CrossAxisAlignment.stretch, children: [
                  Text(l.shopTodayTitle, style: text.titleMedium?.copyWith(fontWeight: FontWeight.w700)),
                  const SizedBox(height: 14),
                  ...dashboard.when(
                    loading: () => [const Center(child: CircularProgressIndicator())],
                    error: (e, _) => [
                      Text(e is ApiException ? e.messageIn(l) : l.errorGeneric),
                      TextButton(onPressed: () => ref.invalidate(shopDashboardProvider), child: Text(l.tryAgain)),
                    ],
                    data: (d) => [
                      Row(children: [
                        _Count(label: l.shopTokensToday, value: d.total, color: AppColors.blue),
                        _Count(label: l.shopCollected, value: d.collected, color: AppColors.success),
                        _Count(label: l.shopWaiting, value: d.waiting, color: AppColors.warning),
                        _Count(label: l.shopCancelled, value: d.cancelled, color: AppColors.muted),
                      ]),
                    ],
                  ),
                ]),
              ),
            ),
            const SizedBox(height: 20),
            FilledButton.icon(
              style: FilledButton.styleFrom(minimumSize: const Size.fromHeight(64), textStyle: const TextStyle(fontSize: 18, fontWeight: FontWeight.w700)),
              icon: const Icon(Icons.qr_code_scanner, size: 30),
              label: Text(l.scanCustomerQr),
              onPressed: () => open(Routes.shopScan),
            ),
            const SizedBox(height: 12),
            OutlinedButton.icon(
              icon: const Icon(Icons.sms_outlined),
              label: Text(l.verifyByMobile),
              onPressed: () => open(Routes.shopOtp),
            ),
            const SizedBox(height: 20),
            if ((dashboard.value?.lowStock ?? 0) > 0) ...[
              Card(
                color: AppColors.dangerSoft,
                child: ListTile(
                  leading: const Icon(Icons.warning_amber_rounded, color: AppColors.danger, size: 30),
                  title: Text(l.lowStockBanner(dashboard.value!.lowStock),
                      style: const TextStyle(color: AppColors.danger, fontWeight: FontWeight.w700)),
                  trailing: const Icon(Icons.chevron_right, color: AppColors.danger),
                  onTap: () => open(Routes.shopStock),
                ),
              ),
              const SizedBox(height: 12),
            ],
            Row(children: [
              Expanded(
                child: OutlinedButton.icon(
                  icon: const Icon(Icons.format_list_numbered),
                  label: Text(l.queueButton),
                  onPressed: () => open(Routes.shopQueue),
                ),
              ),
              const SizedBox(width: 12),
              Expanded(
                child: OutlinedButton.icon(
                  icon: const Icon(Icons.inventory_2_outlined),
                  label: Text(l.stockButton),
                  onPressed: () => open(Routes.shopStock),
                ),
              ),
            ]),
            const SizedBox(height: 24),
            OutlinedButton.icon(
              icon: const Icon(Icons.dns_outlined),
              label: Text(l.checkServer),
              onPressed: () => context.push(Routes.serverStatus),
            ),
          ],
        ),
      ),
    );
  }
}

class _Count extends StatelessWidget {
  const _Count({required this.label, required this.value, required this.color});

  final String label;
  final int value;
  final Color color;

  @override
  Widget build(BuildContext context) {
    // Read as one item by screen readers: "Collected 12".
    return Expanded(
      child: MergeSemantics(
        child: Column(children: [
          Text('$value', style: TextStyle(fontSize: 28, fontWeight: FontWeight.w800, color: color)),
          const SizedBox(height: 2),
          Text(label, textAlign: TextAlign.center, style: const TextStyle(color: AppColors.muted, fontSize: 14)),
        ]),
      ),
    );
  }
}
