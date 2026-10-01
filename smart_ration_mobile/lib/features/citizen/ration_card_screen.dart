import 'package:flutter/material.dart';

import '../../app/theme.dart';
import '../../l10n/app_localizations.dart';
import 'citizen_data.dart';
import 'citizen_widgets.dart';

/// The ration card and what has been collected on it.
class RationCardScreen extends StatelessWidget {
  const RationCardScreen({super.key});

  @override
  Widget build(BuildContext context) {
    final l = AppLocalizations.of(context);
    return Scaffold(
      appBar: AppBar(title: Text(l.rationCard)),
      body: CitizenDataView(
        builder: (context, data) => [
          Card(
            child: Padding(
              padding: const EdgeInsets.all(18),
              child: Column(children: [
                InfoRow(label: l.cardNumber, value: valueText(data.cardNumber)),
                InfoRow(
                  label: l.cardStatus,
                  value: StatusPill(text: data.cardActive ? l.cardActive : l.cardInactive,
                      tone: data.cardActive ? PillTone.good : PillTone.bad),
                ),
                InfoRow(label: l.cardScheme, value: valueText(data.schemeName)),
                InfoRow(label: l.familySizeLabel, value: valueText(l.memberCount(data.familySize))),
                InfoRow(label: l.familyId, value: valueText(data.familyCode)),
                if (data.shop != null)
                  InfoRow(
                    label: l.assignedShop,
                    value: Column(crossAxisAlignment: CrossAxisAlignment.end, children: [
                      valueText(data.shop!.name),
                      Text([data.shop!.address, data.shop!.district].where((s) => s.isNotEmpty).join(', '),
                          textAlign: TextAlign.end, style: const TextStyle(color: AppColors.muted)),
                    ]),
                  ),
              ]),
            ),
          ),
          const SizedBox(height: 20),
          Text(l.collectionHistory, style: Theme.of(context).textTheme.titleLarge?.copyWith(fontWeight: FontWeight.w700)),
          const SizedBox(height: 10),
          if (data.collections.isEmpty)
            Card(child: Padding(padding: const EdgeInsets.all(18), child: Text(l.noCollections)))
          else
            for (final collection in data.collections) ...[
              _CollectionCard(collection: collection),
              const SizedBox(height: 10),
            ],
        ],
      ),
    );
  }
}

class _CollectionCard extends StatelessWidget {
  const _CollectionCard({required this.collection});

  final Collection collection;

  @override
  Widget build(BuildContext context) {
    final l = AppLocalizations.of(context);
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
          Row(children: [
            const Icon(Icons.event_available, color: AppColors.success),
            const SizedBox(width: 8),
            Expanded(child: Text(collection.collectedAt, style: const TextStyle(fontWeight: FontWeight.w700, fontSize: 16))),
            Text(collection.code, style: const TextStyle(color: AppColors.muted, fontSize: 13)),
          ]),
          if (collection.shopName.isNotEmpty) ...[
            const SizedBox(height: 4),
            Text(collection.shopName, style: const TextStyle(color: AppColors.muted)),
          ],
          const SizedBox(height: 8),
          Wrap(spacing: 8, runSpacing: 6, children: [
            for (final (type, quantity) in collection.items)
              Chip(label: Text('${itemWord(l, type)} ${amount(quantity)} ${unitWord(l, type)}')),
          ]),
        ]),
      ),
    );
  }
}
