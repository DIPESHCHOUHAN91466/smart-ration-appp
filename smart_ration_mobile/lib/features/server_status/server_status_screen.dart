import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../app/routes.dart';
import '../../app/theme.dart';
import '../../core/network/api_exception.dart';
import '../../core/providers.dart';
import '../../l10n/app_localizations.dart';
import 'server_status.dart';

/// Home screen for now: proves the app can reach the backend. Login and the dashboards replace it later.
class ServerStatusScreen extends ConsumerWidget {
  const ServerStatusScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final l = AppLocalizations.of(context);
    final status = ref.watch(serverStatusProvider);
    final env = ref.watch(envProvider);
    final text = Theme.of(context).textTheme;

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
        ],
      ),
      body: RefreshIndicator(
        onRefresh: () => ref.refresh(serverStatusProvider.future),
        child: ListView(
          padding: const EdgeInsets.all(20),
          children: [
            Text(l.poweredBy, style: text.titleMedium?.copyWith(color: AppColors.muted)),
            const SizedBox(height: 20),
            Card(
              child: Padding(
                padding: const EdgeInsets.all(20),
                child: status.when(
                  loading: () => _Checking(label: l.serverChecking),
                  error: (error, _) => _Failed(
                    message: error is ApiException ? error.messageIn(l) : l.errorGeneric,
                    retryLabel: l.tryAgain,
                    onRetry: () => ref.invalidate(serverStatusProvider),
                  ),
                  data: (s) => _Connected(status: s),
                ),
              ),
            ),
            const SizedBox(height: 16),
            Text(l.serverAddress(env.apiBaseUrl, env.environment.name),
                style: text.bodySmall?.copyWith(color: AppColors.muted)),
          ],
        ),
      ),
    );
  }
}

class _Checking extends StatelessWidget {
  const _Checking({required this.label});

  final String label;

  @override
  Widget build(BuildContext context) => Row(children: [
        const SizedBox(width: 28, height: 28, child: CircularProgressIndicator(strokeWidth: 3)),
        const SizedBox(width: 16),
        Expanded(child: Text(label)),
      ]);
}

class _Connected extends StatelessWidget {
  const _Connected({required this.status});

  final ServerStatus status;

  @override
  Widget build(BuildContext context) {
    final l = AppLocalizations.of(context);
    final ok = status.isUsable;
    String word(String value) => switch (value) {
          'healthy' => l.statusHealthy,
          'degraded' => l.statusDegraded,
          'unhealthy' => l.statusUnhealthy,
          _ => l.statusUnknown,
        };

    return Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
      Row(children: [
        Icon(ok ? Icons.check_circle : Icons.error, color: ok ? AppColors.success : AppColors.danger, size: 32),
        const SizedBox(width: 12),
        Expanded(
          child: Text(ok ? l.serverConnected : l.serverNoDatabase, style: Theme.of(context).textTheme.titleLarge),
        ),
      ]),
      const SizedBox(height: 16),
      _Row(label: l.statusOverall, value: word(status.status), good: status.isHealthy, warn: ok && !status.isHealthy),
      _Row(label: l.statusDatabase, value: word(status.database), good: ok),
      _Row(label: l.statusData, value: status.dataMode == 'synthetic' ? l.dataSynthetic : l.dataReal, good: true),
    ]);
  }
}

class _Failed extends StatelessWidget {
  const _Failed({required this.message, required this.retryLabel, required this.onRetry});

  final String message;
  final String retryLabel;
  final VoidCallback onRetry;

  @override
  Widget build(BuildContext context) => Column(crossAxisAlignment: CrossAxisAlignment.stretch, children: [
        Row(children: [
          const Icon(Icons.wifi_off, color: AppColors.danger, size: 32),
          const SizedBox(width: 12),
          Expanded(child: Text(message, style: Theme.of(context).textTheme.titleMedium)),
        ]),
        const SizedBox(height: 16),
        FilledButton.icon(onPressed: onRetry, icon: const Icon(Icons.refresh), label: Text(retryLabel)),
      ]);
}

/// One label/value line with a coloured pill. The pill always has words, so colour is never the only signal.
class _Row extends StatelessWidget {
  const _Row({required this.label, required this.value, required this.good, this.warn = false});

  final String label;
  final String value;
  final bool good;
  final bool warn;

  @override
  Widget build(BuildContext context) {
    final (fg, bg) = good
        ? (AppColors.success, AppColors.successSoft)
        : warn
            ? (AppColors.warning, AppColors.warningSoft)
            : (AppColors.danger, AppColors.dangerSoft);
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 6),
      child: Row(children: [
        Expanded(child: Text(label, style: const TextStyle(color: AppColors.muted, fontSize: 16))),
        const SizedBox(width: 8),
        // Flexible lets a long word wrap instead of overflowing; Align keeps the pill on the right.
        Flexible(
          child: Align(
            alignment: AlignmentDirectional.centerEnd,
            child: Container(
              padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
              decoration: BoxDecoration(color: bg, borderRadius: BorderRadius.circular(99)),
              child: Text(value, style: TextStyle(color: fg, fontWeight: FontWeight.w700, fontSize: 15)),
            ),
          ),
        ),
      ]),
    );
  }
}
