import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../app/routes.dart';
import '../../app/theme.dart';
import '../../core/network/api_exception.dart';
import '../../l10n/app_localizations.dart';
import '../assistant/assistant_sheet.dart';
import '../auth/auth_controller.dart';
import '../auth/session.dart';
import '../citizen/citizen_widgets.dart';
import '../notifications/notifications_screen.dart';
import 'official_data.dart';

/// The government official's (and admin's) dashboard: today's totals across every shop, the last
/// 30 days, and the way into the shops, the open alerts, citizens' complaints (alerts and complaints
/// can be updated on their own screens) and the read-only records (bookings, stock, reports, audit, users).
class OfficialHomeScreen extends ConsumerWidget {
  const OfficialHomeScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final l = AppLocalizations.of(context);
    final user = ref.watch(authControllerProvider);
    if (user == null) return const Scaffold(body: SizedBox.shrink());
    final overview = ref.watch(officialOverviewProvider);
    final period = ref.watch(periodStatsProvider);
    final alerts = ref.watch(alertsProvider);
    final text = Theme.of(context).textTheme;

    Future<OfficialOverview> refresh() {
      ref.invalidate(periodStatsProvider);
      ref.invalidate(alertsProvider);
      return ref.refresh(officialOverviewProvider.future);
    }

    return Scaffold(
      floatingActionButton: const AiButton(screen: 'official_home'),
      appBar: AppBar(
        title: Text(l.appTitle),
        actions: [
          const NotificationsBell(),
          IconButton(
            icon: const Icon(Icons.help_outline),
            tooltip: l.helpButton,
            iconSize: 28,
            onPressed: () => context.push(Routes.help),
          ),
          IconButton(icon: const Icon(Icons.translate), tooltip: l.language, iconSize: 28, onPressed: () => context.push(Routes.changeLanguage)),
          IconButton(
            icon: const Icon(Icons.password),
            tooltip: l.changePasswordTitle,
            iconSize: 28,
            onPressed: () => context.push(Routes.changePassword),
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
        onRefresh: refresh,
        child: ListView(
          padding: const EdgeInsets.all(16),
          children: [
            Text(l.greeting(user.fullName), style: text.headlineSmall?.copyWith(fontWeight: FontWeight.w700)),
            const SizedBox(height: 4),
            Text(user.role == AppRole.admin ? l.roleAdmin : l.roleOfficial,
                style: const TextStyle(color: AppColors.blue, fontWeight: FontWeight.w600, fontSize: 16)),
            const SizedBox(height: 16),
            _Panel(
              title: l.officialTodayTitle,
              child: overview.when(
                loading: () => const Center(child: CircularProgressIndicator()),
                error: (e, _) => _Retry(error: e, onRetry: () => ref.invalidate(officialOverviewProvider)),
                data: (o) => Column(children: [
                  Row(children: [
                    _Tile(label: l.statBookings, value: '${o.bookingsToday}', color: AppColors.blue),
                    _Tile(label: l.shopCollected, value: '${o.collectedToday}', color: AppColors.success),
                    _Tile(label: l.shopWaiting, value: '${o.waitingToday}', color: AppColors.warning),
                  ]),
                  const SizedBox(height: 14),
                  Row(children: [
                    _Tile(label: l.statHandedOutToday, value: '${amount(o.handedOutTodayKg)} ${l.unitKg}', color: AppColors.ink),
                    _Tile(label: l.statShops, value: '${o.shops}', color: AppColors.ink),
                    _Tile(label: l.statBeneficiaries, value: '${o.beneficiaries}', color: AppColors.ink),
                  ]),
                ]),
              ),
            ),
            const SizedBox(height: 12),
            _Panel(
              title: l.periodTitle,
              child: period.when(
                loading: () => const Center(child: CircularProgressIndicator()),
                error: (e, _) => _Retry(error: e, onRetry: () => ref.invalidate(periodStatsProvider)),
                data: (p) => Column(crossAxisAlignment: CrossAxisAlignment.stretch, children: [
                  Row(children: [
                    _Tile(label: l.statTokensBooked, value: '${p.tokens}', color: AppColors.blue),
                    _Tile(label: l.shopCollected, value: '${p.collected}', color: AppColors.success),
                    _Tile(label: l.shopCancelled, value: '${p.cancelled}', color: AppColors.muted),
                  ]),
                  const SizedBox(height: 14),
                  Text(l.collectionRateLabel, style: const TextStyle(color: AppColors.muted)),
                  const SizedBox(height: 6),
                  // The bar is decoration; the sentence below says the same in words.
                  ExcludeSemantics(
                    child: ClipRRect(
                      borderRadius: BorderRadius.circular(8),
                      child: LinearProgressIndicator(
                        value: (p.collectionRate / 100).clamp(0, 1),
                        minHeight: 12,
                        color: AppColors.success,
                        backgroundColor: AppColors.successSoft,
                      ),
                    ),
                  ),
                  const SizedBox(height: 6),
                  Text(l.collectionRateValue(amount(p.collectionRate)), style: const TextStyle(fontSize: 16, fontWeight: FontWeight.w600)),
                ]),
              ),
            ),
            const SizedBox(height: 12),
            if ((overview.value?.lowStockAlerts ?? 0) > 0)
              Card(
                color: AppColors.warningSoft,
                child: ListTile(
                  leading: const Icon(Icons.inventory_2_outlined, color: AppColors.warning, size: 28),
                  title: Text(l.statLowStockAlerts, style: const TextStyle(fontWeight: FontWeight.w700)),
                  trailing: Text('${overview.value!.lowStockAlerts}',
                      style: const TextStyle(fontSize: 22, fontWeight: FontWeight.w800, color: AppColors.warning)),
                  onTap: () => context.push(Routes.officialShops),
                ),
              ),
            const SizedBox(height: 12),
            FilledButton.icon(
              style: FilledButton.styleFrom(minimumSize: const Size.fromHeight(60)),
              icon: const Icon(Icons.storefront, size: 28),
              label: Text(l.statShops),
              onPressed: () => context.push(Routes.officialShops),
            ),
            const SizedBox(height: 12),
            OutlinedButton.icon(
              icon: const Icon(Icons.notification_important_outlined),
              label: Text(alerts.value == null ? l.alertsTitle : l.alertsButton(alerts.value!.length)),
              onPressed: () => context.push(Routes.officialAlerts),
            ),
            const SizedBox(height: 12),
            OutlinedButton.icon(
              icon: const Icon(Icons.insights),
              label: Text(l.aiCenterTitle),
              onPressed: () => context.push(Routes.officialInsights),
            ),
            const SizedBox(height: 12),
            OutlinedButton.icon(
              icon: const Icon(Icons.report_problem_outlined),
              label: Text(l.officialComplaintsTitle),
              onPressed: () => context.push(Routes.officialComplaints),
            ),
            const SizedBox(height: 12),
            _Panel(
              title: l.recordsTitle,
              child: Column(children: [
                for (final (icon, label, route) in [
                  (Icons.confirmation_number_outlined, l.allBookingsTitle, Routes.officialBookings),
                  (Icons.inventory_2_outlined, l.stockAllShopsTitle, Routes.officialStock),
                  (Icons.description_outlined, l.reportsTitle, Routes.officialReports),
                  (Icons.fact_check_outlined, l.auditTitle, Routes.officialAudit),
                  (Icons.people_outline, l.usersTitle, Routes.officialUsers),
                ])
                  ListTile(
                    contentPadding: EdgeInsets.zero,
                    minTileHeight: 56,
                    leading: Icon(icon, color: AppColors.blue, size: 28),
                    title: Text(label, style: const TextStyle(fontSize: 16, fontWeight: FontWeight.w600)),
                    trailing: const Icon(Icons.chevron_right),
                    onTap: () => context.push(route),
                  ),
              ]),
            ),
            const SizedBox(height: 24),
            OutlinedButton.icon(
              icon: const Icon(Icons.dns_outlined),
              label: Text(l.checkServer),
              onPressed: () => context.push(Routes.serverStatus),
            ),
            const SizedBox(height: 88),
          ],
        ),
      ),
    );
  }
}

class _Panel extends StatelessWidget {
  const _Panel({required this.title, required this.child});

  final String title;
  final Widget child;

  @override
  Widget build(BuildContext context) => Card(
        child: Padding(
          padding: const EdgeInsets.all(18),
          child: Column(crossAxisAlignment: CrossAxisAlignment.stretch, children: [
            Semantics(
              header: true,
              child: Text(title, style: Theme.of(context).textTheme.titleMedium?.copyWith(fontWeight: FontWeight.w700)),
            ),
            const SizedBox(height: 14),
            child,
          ]),
        ),
      );
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

class _Retry extends StatelessWidget {
  const _Retry({required this.error, required this.onRetry});

  final Object error;
  final VoidCallback onRetry;

  @override
  Widget build(BuildContext context) {
    final l = AppLocalizations.of(context);
    return Column(children: [
      Text(error is ApiException ? (error as ApiException).messageIn(l) : l.errorGeneric, textAlign: TextAlign.center),
      TextButton(onPressed: onRetry, child: Text(l.tryAgain)),
    ]);
  }
}
