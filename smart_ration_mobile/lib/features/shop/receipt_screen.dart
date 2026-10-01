import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:intl/intl.dart';

import '../../app/routes.dart';
import '../../app/theme.dart';
import '../../l10n/app_localizations.dart';
import '../citizen/citizen_widgets.dart';
import 'shop_data.dart';

/// Proof that the ration was handed over, with the backend's collection ID.
class ReceiptScreen extends ConsumerStatefulWidget {
  const ReceiptScreen({super.key, required this.receipt});

  final Receipt? receipt;

  @override
  ConsumerState<ReceiptScreen> createState() => _ReceiptScreenState();
}

class _ReceiptScreenState extends ConsumerState<ReceiptScreen> {
  @override
  void initState() {
    super.initState();
    // Today's counts on the dashboard are now out of date.
    Future.microtask(() => ref.invalidate(shopDashboardProvider));
  }

  @override
  Widget build(BuildContext context) {
    final l = AppLocalizations.of(context);
    final r = widget.receipt;
    return Scaffold(
      appBar: AppBar(title: Text(l.receiptTitle), automaticallyImplyLeading: false),
      body: r == null
          ? Center(child: Text(l.nothingToCheck))
          : ListView(
              padding: const EdgeInsets.all(16),
              children: [
                const Icon(Icons.check_circle, color: AppColors.success, size: 72),
                const SizedBox(height: 8),
                Semantics(
                  liveRegion: true,
                  child: Text(l.receiptTitle,
                      textAlign: TextAlign.center, style: const TextStyle(fontSize: 24, fontWeight: FontWeight.w800, color: AppColors.success)),
                ),
                const SizedBox(height: 4),
                Text(l.receiptSaved, textAlign: TextAlign.center, style: const TextStyle(fontSize: 16, color: AppColors.muted)),
                const SizedBox(height: 16),
                Card(
                  child: Padding(
                    padding: const EdgeInsets.all(18),
                    child: Column(crossAxisAlignment: CrossAxisAlignment.stretch, children: [
                      Text(l.receiptCollectionId, style: const TextStyle(color: AppColors.muted, fontSize: 15)),
                      SelectableText(r.collectionCode,
                          style: const TextStyle(fontSize: 26, fontWeight: FontWeight.w800, color: AppColors.blue, letterSpacing: 0.5)),
                      const SizedBox(height: 10),
                      InfoRow(label: l.tokenNumber, value: valueText(r.tokenNumber)),
                      InfoRow(label: l.customer, value: valueText(r.customerName)),
                      InfoRow(label: l.collectionTime, value: valueText(collectedAtLabel(context, r.collectedAt))),
                      const Divider(height: 24),
                      for (final (type, quantity) in r.items)
                        Padding(
                          padding: const EdgeInsets.symmetric(vertical: 4),
                          child: Row(children: [
                            Icon(itemIcon(type), color: AppColors.muted, size: 22),
                            const SizedBox(width: 10),
                            Expanded(child: Text(itemWord(l, type), style: const TextStyle(fontSize: 16))),
                            Text('${amount(quantity)} ${unitWord(l, type)}', style: const TextStyle(fontSize: 16, fontWeight: FontWeight.w700)),
                          ]),
                        ),
                    ]),
                  ),
                ),
                const SizedBox(height: 20),
                FilledButton.icon(
                  style: FilledButton.styleFrom(minimumSize: const Size.fromHeight(60), textStyle: const TextStyle(fontSize: 18, fontWeight: FontWeight.w700)),
                  icon: const Icon(Icons.qr_code_scanner, size: 28),
                  label: Text(l.scanNextCustomer),
                  onPressed: () => context.go(Routes.shopScan),
                ),
                const SizedBox(height: 10),
                OutlinedButton.icon(
                  icon: const Icon(Icons.home_outlined),
                  label: Text(l.backToDashboard),
                  onPressed: () => context.go(Routes.shopHome),
                ),
              ],
            ),
    );
  }
}

/// The backend writes the time in UTC ("2026-10-01 04:37"); shown on the phone's clock.
String collectedAtLabel(BuildContext context, String utcText) {
  final parsed = DateTime.tryParse('${utcText.replaceFirst(' ', 'T')}Z');
  if (parsed == null) return utcText;
  final local = parsed.toLocal();
  final locale = Localizations.localeOf(context).toLanguageTag();
  return '${DateFormat.yMMMd(locale).format(local)}, ${DateFormat.jm(locale).format(local)}';
}
