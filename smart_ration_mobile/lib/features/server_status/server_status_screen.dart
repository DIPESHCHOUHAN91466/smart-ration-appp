import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../app/theme.dart';
import '../../core/network/api_exception.dart';
import '../../core/providers.dart';
import 'server_status.dart';

// TODO(M3): every sentence on this screen moves into the English / Hindi / Marathi translation files.

/// First screen for now: proves the app can reach the backend. Later milestones put the splash,
/// language choice and login in front of it.
class ServerStatusScreen extends ConsumerWidget {
  const ServerStatusScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final status = ref.watch(serverStatusProvider);
    final env = ref.watch(envProvider);
    final text = Theme.of(context).textTheme;

    return Scaffold(
      appBar: AppBar(title: const Text('Smart Ration AI')),
      body: RefreshIndicator(
        onRefresh: () => ref.refresh(serverStatusProvider.future),
        child: ListView(
          padding: const EdgeInsets.all(20),
          children: [
            Text('Powered by HSD2C', style: text.titleMedium?.copyWith(color: AppColors.muted)),
            const SizedBox(height: 20),
            Card(
              child: Padding(
                padding: const EdgeInsets.all(20),
                child: status.when(
                  loading: () => const _Checking(),
                  error: (error, _) => _Failed(
                    message: error is ApiException ? error.userMessage : 'Something went wrong. Please try again.',
                    onRetry: () => ref.invalidate(serverStatusProvider),
                  ),
                  data: (s) => _Connected(status: s),
                ),
              ),
            ),
            const SizedBox(height: 16),
            Text('Server: ${env.apiBaseUrl}  ·  ${env.environment.name}',
                style: text.bodySmall?.copyWith(color: AppColors.muted)),
          ],
        ),
      ),
    );
  }
}

class _Checking extends StatelessWidget {
  const _Checking();

  @override
  Widget build(BuildContext context) => const Row(children: [
        SizedBox(width: 28, height: 28, child: CircularProgressIndicator(strokeWidth: 3)),
        SizedBox(width: 16),
        Expanded(child: Text('Checking the connection to the server…')),
      ]);
}

class _Connected extends StatelessWidget {
  const _Connected({required this.status});

  final ServerStatus status;

  @override
  Widget build(BuildContext context) {
    final ok = status.isUsable;
    return Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
      Row(children: [
        Icon(ok ? Icons.check_circle : Icons.error, color: ok ? AppColors.success : AppColors.danger, size: 32),
        const SizedBox(width: 12),
        Expanded(
          child: Text(ok ? 'Connected to the server' : 'The server cannot reach its database',
              style: Theme.of(context).textTheme.titleLarge),
        ),
      ]),
      const SizedBox(height: 16),
      _Row(label: 'Overall', value: status.status, good: status.isHealthy, warn: ok && !status.isHealthy),
      _Row(label: 'Database', value: status.database, good: ok),
      _Row(label: 'Data', value: status.dataMode == 'synthetic' ? 'Demo data (synthetic)' : status.dataMode, good: true),
    ]);
  }
}

class _Failed extends StatelessWidget {
  const _Failed({required this.message, required this.onRetry});

  final String message;
  final VoidCallback onRetry;

  @override
  Widget build(BuildContext context) => Column(crossAxisAlignment: CrossAxisAlignment.stretch, children: [
        Row(children: [
          const Icon(Icons.wifi_off, color: AppColors.danger, size: 32),
          const SizedBox(width: 12),
          Expanded(child: Text(message, style: Theme.of(context).textTheme.titleMedium)),
        ]),
        const SizedBox(height: 16),
        FilledButton.icon(onPressed: onRetry, icon: const Icon(Icons.refresh), label: const Text('Try again')),
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
        Container(
          padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
          decoration: BoxDecoration(color: bg, borderRadius: BorderRadius.circular(99)),
          child: Text(value, style: TextStyle(color: fg, fontWeight: FontWeight.w700, fontSize: 15)),
        ),
      ]),
    );
  }
}
