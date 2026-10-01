import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:qr_flutter/qr_flutter.dart';

import '../../app/routes.dart';
import '../../app/theme.dart';
import '../../core/network/api_exception.dart';
import '../../l10n/app_localizations.dart';
import '../citizen/citizen_data.dart';
import '../citizen/citizen_widgets.dart';
import 'booking_data.dart';
import 'booking_widgets.dart';

/// One token: number, time, items and, while it can still be collected, the signed QR code.
class TokenScreen extends ConsumerWidget {
  const TokenScreen({super.key, required this.tokenId});

  final int tokenId;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final l = AppLocalizations.of(context);
    final token = ref.watch(tokenProvider(tokenId));
    return Scaffold(
      appBar: AppBar(title: Text(l.myToken)),
      body: RefreshIndicator(
        onRefresh: () {
          ref.invalidate(qrPayloadProvider(tokenId));
          return ref.refresh(tokenProvider(tokenId).future);
        },
        child: ListView(
          padding: const EdgeInsets.all(16),
          children: token.when(
            loading: () => [const SizedBox(height: 80), const Center(child: CircularProgressIndicator())],
            error: (e, _) => [
              const SizedBox(height: 40),
              Text(e is ApiException ? e.messageIn(l) : l.errorGeneric,
                  textAlign: TextAlign.center, style: Theme.of(context).textTheme.titleMedium),
              const SizedBox(height: 16),
              FilledButton.icon(
                  onPressed: () => ref.invalidate(tokenProvider(tokenId)), icon: const Icon(Icons.refresh), label: Text(l.tryAgain)),
            ],
            data: (t) => _content(context, ref, t),
          ),
        ),
      ),
    );
  }

  List<Widget> _content(BuildContext context, WidgetRef ref, RationToken t) {
    final l = AppLocalizations.of(context);
    final state = t.stateOn(DateTime.now());
    return [
      Card(
        child: Padding(
          padding: const EdgeInsets.all(18),
          child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
            Row(children: [
              Expanded(child: Text(l.tokenNumber, style: const TextStyle(color: AppColors.muted, fontSize: 15))),
              StatusPill(text: tokenStateWord(l, state), tone: tokenStateTone(state)),
            ]),
            const SizedBox(height: 4),
            SelectableText(t.number,
                style: const TextStyle(fontSize: 30, fontWeight: FontWeight.w800, color: AppColors.blue, letterSpacing: 1)),
            const SizedBox(height: 12),
            InfoRow(label: l.collectionDate, value: valueText(longDate(context, t.date))),
            InfoRow(label: l.collectionTime, value: valueText('${timeLabel(context, t.start)} – ${timeLabel(context, t.end)}')),
            InfoRow(label: l.assignedShop, value: valueText(t.shopName)),
            const SizedBox(height: 8),
            Text(l.tokenItems, style: const TextStyle(color: AppColors.muted, fontSize: 15)),
            const SizedBox(height: 6),
            Wrap(spacing: 8, runSpacing: 6, children: [
              for (final (type, q) in t.items) Chip(label: Text('${itemWord(l, type)} ${amount(q)} ${unitWord(l, type)}')),
            ]),
          ]),
        ),
      ),
      if (state == TokenState.booked) ...[
        const SizedBox(height: 12),
        _QrCard(token: t),
        const SizedBox(height: 16),
        OutlinedButton.icon(
          style: OutlinedButton.styleFrom(foregroundColor: AppColors.danger, side: const BorderSide(color: AppColors.danger)),
          icon: const Icon(Icons.event_busy),
          label: Text(l.cancelBooking),
          onPressed: () => _cancel(context, ref, t),
        ),
      ],
      const SizedBox(height: 24),
    ];
  }

  Future<void> _cancel(BuildContext context, WidgetRef ref, RationToken t) async {
    final l = AppLocalizations.of(context);
    final messenger = ScaffoldMessenger.of(context);
    final yes = await showDialog<bool>(
      context: context,
      builder: (dialog) => AlertDialog(
        title: Text(l.cancelConfirmTitle),
        content: Text(l.cancelConfirmBody),
        actions: [
          TextButton(onPressed: () => Navigator.pop(dialog, false), child: Text(l.keepBooking)),
          FilledButton(
            style: FilledButton.styleFrom(backgroundColor: AppColors.danger),
            onPressed: () => Navigator.pop(dialog, true),
            child: Text(l.cancelBooking),
          ),
        ],
      ),
    );
    if (yes != true) return;
    try {
      await ref.read(bookingRepositoryProvider).cancel(t.id);
      ref.invalidate(tokenProvider(t.id));
      ref.invalidate(myTokensProvider);
      ref.invalidate(citizenOverviewProvider);
      messenger.showSnackBar(SnackBar(content: Text(l.bookingCancelled)));
    } on ApiException catch (e) {
      messenger.showSnackBar(SnackBar(content: Text(e.messageIn(l))));
    }
  }
}

class _QrCard extends ConsumerWidget {
  const _QrCard({required this.token});

  final RationToken token;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final l = AppLocalizations.of(context);
    final payload = ref.watch(qrPayloadProvider(token.id));
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(18),
        child: Column(children: [
          Text(l.showQrAtShop, textAlign: TextAlign.center, style: Theme.of(context).textTheme.titleMedium),
          const SizedBox(height: 12),
          payload.when(
            loading: () => const SizedBox(height: 260, child: Center(child: CircularProgressIndicator())),
            error: (e, _) => Column(children: [
              Text(e is ApiException ? e.messageIn(l) : l.errorGeneric, textAlign: TextAlign.center),
              TextButton(onPressed: () => ref.invalidate(qrPayloadProvider(token.id)), child: Text(l.tryAgain)),
            ]),
            // Its own labelled image for screen readers ("QR code for token SR-…"), not merged into nearby text.
            data: (text) => Semantics(
              container: true,
              image: true,
              label: l.qrCodeLabel(token.number),
              child: ExcludeSemantics(
                child: Container(
                  color: Colors.white, // a white quiet zone around the code, so every scanner can read it
                  padding: const EdgeInsets.all(12),
                  child: QrImageView(
                    data: text,
                    size: 260,
                    backgroundColor: Colors.white,
                    errorCorrectionLevel: QrErrorCorrectLevel.M,
                  ),
                ),
              ),
            ),
          ),
          const SizedBox(height: 12),
          Text(l.qrManualCode, textAlign: TextAlign.center, style: const TextStyle(color: AppColors.muted)),
          const SizedBox(height: 4),
          SelectableText(token.reference,
              textAlign: TextAlign.center, style: const TextStyle(fontWeight: FontWeight.w700, fontSize: 16, letterSpacing: 0.5)),
          IconButton(
            tooltip: MaterialLocalizations.of(context).copyButtonLabel,
            icon: const Icon(Icons.copy),
            onPressed: () => Clipboard.setData(ClipboardData(text: token.reference)),
          ),
          Row(mainAxisAlignment: MainAxisAlignment.center, children: [
            const Icon(Icons.lock_outline, size: 18, color: AppColors.muted),
            const SizedBox(width: 6),
            Flexible(child: Text(l.qrNoPersonalData, style: const TextStyle(color: AppColors.muted))),
          ]),
        ]),
      ),
    );
  }
}

/// All my tokens: the ones still to collect first, then the rest, newest first.
class TokensScreen extends ConsumerWidget {
  const TokensScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final l = AppLocalizations.of(context);
    final tokens = ref.watch(myTokensProvider);
    final now = DateTime.now();
    return Scaffold(
      appBar: AppBar(title: Text(l.myTokens)),
      body: RefreshIndicator(
        onRefresh: () => ref.refresh(myTokensProvider.future),
        child: ListView(
          padding: const EdgeInsets.all(16),
          children: tokens.when(
            loading: () => [const SizedBox(height: 80), const Center(child: CircularProgressIndicator())],
            error: (e, _) => [
              Text(e is ApiException ? e.messageIn(l) : l.errorGeneric, textAlign: TextAlign.center),
              TextButton(onPressed: () => ref.invalidate(myTokensProvider), child: Text(l.tryAgain)),
            ],
            data: (all) {
              if (all.isEmpty) return [Text(l.noTokens, style: Theme.of(context).textTheme.titleMedium)];
              final ordered = [
                ...all.where((t) => t.stateOn(now) == TokenState.booked),
                ...all.where((t) => t.stateOn(now) != TokenState.booked),
              ];
              return [
                for (final t in ordered)
                  Card(
                    margin: const EdgeInsets.only(bottom: 10),
                    child: ListTile(
                      contentPadding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
                      title: Text(t.number, style: const TextStyle(fontWeight: FontWeight.w700, fontSize: 17)),
                      subtitle: Text('${dayLabel(context, t.date)} · ${timeLabel(context, t.start)}\n${t.shopName}'),
                      isThreeLine: true,
                      trailing: StatusPill(text: tokenStateWord(l, t.stateOn(now)), tone: tokenStateTone(t.stateOn(now))),
                      onTap: () => context.push(Routes.citizenToken(t.id)),
                    ),
                  ),
              ];
            },
          ),
        ),
      ),
    );
  }
}
