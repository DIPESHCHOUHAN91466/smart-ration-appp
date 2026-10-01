import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../app/routes.dart';
import '../../app/theme.dart';
import '../../core/network/api_exception.dart';
import '../../l10n/app_localizations.dart';
import '../booking/booking_widgets.dart';
import '../citizen/citizen_widgets.dart';
import 'shop_data.dart';

/// Today's tokens at my shop: who is still to come (in time order), then who is done.
///
/// There is deliberately no "mark collected" button here: a customer is served only after their QR
/// or a code on their mobile proves the token is theirs (the scanner and OTP screens).
class QueueScreen extends ConsumerWidget {
  const QueueScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final l = AppLocalizations.of(context);
    final queue = ref.watch(shopQueueProvider);
    return Scaffold(
      appBar: AppBar(title: Text(l.queueButton)),
      body: RefreshIndicator(
        onRefresh: () => ref.refresh(shopQueueProvider.future),
        child: ListView(
          padding: const EdgeInsets.all(16),
          children: queue.when(
            loading: () => [const SizedBox(height: 80), const Center(child: CircularProgressIndicator())],
            error: (e, _) => [
              Text(e is ApiException ? e.messageIn(l) : l.errorGeneric, textAlign: TextAlign.center),
              TextButton(onPressed: () => ref.invalidate(shopQueueProvider), child: Text(l.tryAgain)),
            ],
            data: (all) {
              if (all.isEmpty) return [Text(l.queueEmpty, style: Theme.of(context).textTheme.titleMedium)];
              final waiting = all.where((e) => e.waiting).toList();
              final done = all.where((e) => !e.waiting).toList();
              return [
                _Header(l.queueWaitingHeader(waiting.length)),
                for (final e in waiting) _QueueTile(entry: e),
                if (done.isNotEmpty) ...[
                  const SizedBox(height: 12),
                  _Header(l.queueDoneHeader(done.length)),
                  for (final e in done) _QueueTile(entry: e),
                ],
              ];
            },
          ),
        ),
      ),
    );
  }
}

class _Header extends StatelessWidget {
  const _Header(this.text);

  final String text;

  @override
  Widget build(BuildContext context) => Padding(
        padding: const EdgeInsets.only(bottom: 8),
        child: Semantics(
          header: true,
          child: Text(text, style: Theme.of(context).textTheme.titleMedium?.copyWith(fontWeight: FontWeight.w700)),
        ),
      );
}

class _QueueTile extends ConsumerWidget {
  const _QueueTile({required this.entry});

  final QueueEntry entry;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final l = AppLocalizations.of(context);
    final t = entry.token;
    final state = t.stateOn(DateTime.now());
    final (word, tone) = entry.waiting ? (l.shopWaiting, PillTone.warn) : (tokenStateWord(l, state), tokenStateTone(state));
    return Card(
      margin: const EdgeInsets.only(bottom: 10),
      child: ListTile(
        contentPadding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
        leading: Text(timeLabel(context, t.start), style: const TextStyle(fontSize: 16, fontWeight: FontWeight.w700, color: AppColors.blue)),
        title: Text(entry.customerName.isEmpty ? t.number : entry.customerName,
            style: const TextStyle(fontWeight: FontWeight.w700, fontSize: 17)),
        subtitle: Text('${t.number}\n${t.items.map((i) => '${itemWord(l, i.$1)} ${amount(i.$2)} ${unitWord(l, i.$1)}').join(' · ')}'),
        isThreeLine: true,
        trailing: StatusPill(text: word, tone: tone),
        onTap: entry.waiting ? () => _serve(context, ref) : null,
      ),
    );
  }

  /// A waiting customer: the two checked ways to serve them.
  Future<void> _serve(BuildContext context, WidgetRef ref) async {
    final l = AppLocalizations.of(context);
    final route = await showModalBottomSheet<String>(
      context: context,
      showDragHandle: true,
      builder: (sheet) => SafeArea(
        child: Padding(
          padding: const EdgeInsets.fromLTRB(20, 0, 20, 20),
          child: Column(mainAxisSize: MainAxisSize.min, crossAxisAlignment: CrossAxisAlignment.stretch, children: [
            Text(entry.customerName, style: const TextStyle(fontSize: 20, fontWeight: FontWeight.w700)),
            Text('${entry.token.number} · ${timeLabel(context, entry.token.start)}', style: const TextStyle(color: AppColors.muted)),
            const SizedBox(height: 12),
            Text(l.queueServeHint, style: const TextStyle(fontSize: 16)),
            const SizedBox(height: 16),
            FilledButton.icon(
              icon: const Icon(Icons.qr_code_scanner),
              label: Text(l.scanCustomerQr),
              onPressed: () => Navigator.pop(sheet, Routes.shopScan),
            ),
            const SizedBox(height: 10),
            OutlinedButton.icon(
              icon: const Icon(Icons.sms_outlined),
              label: Text(l.verifyByMobile),
              onPressed: () => Navigator.pop(sheet, Routes.shopOtp),
            ),
          ]),
        ),
      ),
    );
    if (route == null || !context.mounted) return;
    await context.push(route);
    ref.invalidate(shopQueueProvider);
  }
}
