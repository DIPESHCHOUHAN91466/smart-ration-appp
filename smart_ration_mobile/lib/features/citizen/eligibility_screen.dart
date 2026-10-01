import 'package:flutter/material.dart';

import '../../app/theme.dart';
import '../../l10n/app_localizations.dart';
import 'citizen_data.dart';
import 'citizen_widgets.dart';

/// Is the family eligible, and how much can it still collect this month. Every number is the backend's.
class EligibilityScreen extends StatelessWidget {
  const EligibilityScreen({super.key});

  @override
  Widget build(BuildContext context) {
    final l = AppLocalizations.of(context);
    final text = Theme.of(context).textTheme;
    return Scaffold(
      appBar: AppBar(title: Text(l.eligibilityTitle)),
      body: CitizenDataView(
        builder: (context, data) => [
          Card(
            child: Padding(
              padding: const EdgeInsets.all(18),
              child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                StatusPill(text: eligibilityWord(l, data.eligibility), tone: eligibilityTone(data.eligibility)),
                const SizedBox(height: 12),
                Text(
                  switch (data.eligibility) {
                    FamilyEligibility.eligible => l.eligibilityExplainEligible,
                    FamilyEligibility.partiallyEligible => l.eligibilityExplainPartial,
                    FamilyEligibility.notEligible => l.eligibilityExplainNot,
                  },
                  style: text.bodyLarge,
                ),
                const SizedBox(height: 12),
                InfoRow(label: l.cardScheme, value: valueText(data.schemeName)),
                InfoRow(label: l.familySizeLabel, value: valueText(l.memberCount(data.familySize))),
                InfoRow(label: l.eligibilityTitle, value: valueText(l.eligibleMembersOf(data.eligibleMembers, data.familySize))),
              ]),
            ),
          ),
          const SizedBox(height: 20),
          Text(l.monthlyEntitlement, style: text.titleLarge?.copyWith(fontWeight: FontWeight.w700)),
          const SizedBox(height: 10),
          for (final item in data.entitlement) ...[
            _EntitlementCard(item: item),
            const SizedBox(height: 10),
          ],
        ],
      ),
    );
  }
}

class _EntitlementCard extends StatelessWidget {
  const _EntitlementCard({required this.item});

  final EntitlementItem item;

  @override
  Widget build(BuildContext context) {
    final l = AppLocalizations.of(context);
    final unit = unitWord(l, item.rationType);
    final used = item.monthly <= 0 ? 0.0 : (item.collected / item.monthly).clamp(0.0, 1.0);
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
          Row(children: [
            Icon(itemIcon(item.rationType), color: AppColors.blue),
            const SizedBox(width: 10),
            Expanded(child: Text(itemWord(l, item.rationType), style: const TextStyle(fontSize: 18, fontWeight: FontWeight.w700))),
          ]),
          const SizedBox(height: 8),
          Text(l.remainingOf(amount(item.remaining), amount(item.monthly), unit),
              style: const TextStyle(fontSize: 16, fontWeight: FontWeight.w600)),
          const SizedBox(height: 8),
          // How much of the month's quota is already collected.
          ClipRRect(
            borderRadius: BorderRadius.circular(99),
            child: LinearProgressIndicator(
              value: used,
              minHeight: 10,
              backgroundColor: const Color(0xFFE8EEF5),
              color: item.remaining <= 0 ? AppColors.muted : AppColors.blue,
              // Screen readers announce the item and the percentage; the sentence below gives the amount.
              semanticsLabel: itemWord(l, item.rationType),
            ),
          ),
          const SizedBox(height: 6),
          Text(l.collectedAmount(amount(item.collected), unit), style: const TextStyle(color: AppColors.muted)),
        ]),
      ),
    );
  }
}
