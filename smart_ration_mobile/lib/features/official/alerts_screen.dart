import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../app/theme.dart';
import '../../core/network/api_exception.dart';
import '../../l10n/app_localizations.dart';
import '../citizen/citizen_widgets.dart';
import 'official_data.dart';
import 'official_words.dart';

/// Open warnings from the backend's rules (e.g. the same QR scanned many times), most serious first.
/// They point at something worth checking; they never prove wrongdoing, and the screen says so.
class AlertsScreen extends ConsumerWidget {
  const AlertsScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final l = AppLocalizations.of(context);
    final alerts = ref.watch(alertsProvider);
    return Scaffold(
      appBar: AppBar(title: Text(l.alertsTitle)),
      body: RefreshIndicator(
        onRefresh: () => ref.refresh(alertsProvider.future),
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
                  Expanded(child: Text(l.alertsNotice, style: const TextStyle(fontSize: 15, fontWeight: FontWeight.w600))),
                ]),
              ),
            ),
            const SizedBox(height: 12),
            ...alerts.when(
              loading: () => [const SizedBox(height: 60), const Center(child: CircularProgressIndicator())],
              error: (e, _) => [
                Text(e is ApiException ? e.messageIn(l) : l.errorGeneric, textAlign: TextAlign.center),
                TextButton(onPressed: () => ref.invalidate(alertsProvider), child: Text(l.tryAgain)),
              ],
              data: (all) => all.isEmpty
                  ? [Text(l.noAlerts, style: Theme.of(context).textTheme.titleMedium)]
                  : [for (final a in all) _AlertCard(alert: a)],
            ),
          ],
        ),
      ),
    );
  }
}

class _AlertCard extends StatelessWidget {
  const _AlertCard({required this.alert});

  final AlertItem alert;

  @override
  Widget build(BuildContext context) {
    final l = AppLocalizations.of(context);
    return Card(
      margin: const EdgeInsets.only(bottom: 10),
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
          Row(children: [
            Expanded(
              child: Text(alertTypeWord(l, alert.type), style: const TextStyle(fontSize: 17, fontWeight: FontWeight.w700)),
            ),
            StatusPill(text: severityWord(l, alert.severity), tone: severityTone(alert.severity)),
          ]),
          const SizedBox(height: 4),
          if (alert.shopName.isNotEmpty) Text(alert.shopName, style: const TextStyle(color: AppColors.blue, fontWeight: FontWeight.w600)),
          if (alert.detectedAt != null) Text(localMoment(context, alert.detectedAt!), style: const TextStyle(color: AppColors.muted)),
          if (alert.description.isNotEmpty) ...[
            const SizedBox(height: 8),
            // The rule's own words come from the backend in English only.
            if (Localizations.localeOf(context).languageCode != 'en')
              Text(l.alertDetailsInEnglish, style: const TextStyle(color: AppColors.muted, fontSize: 13)),
            Text(alert.description, style: const TextStyle(fontSize: 15)),
          ],
        ]),
      ),
    );
  }
}
