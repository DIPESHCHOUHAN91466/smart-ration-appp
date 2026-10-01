import 'package:flutter/material.dart';

import '../../app/theme.dart';
import '../../l10n/app_localizations.dart';
import 'citizen_data.dart';
import 'citizen_home_screen.dart';
import 'citizen_widgets.dart';

/// Every member of the family with age, relationship and eligibility. Aadhaar is only ever shown
/// masked (XXXX-XXXX-1234), and only for the card holder, the one person whose Aadhaar is on record.
class FamilyScreen extends StatelessWidget {
  const FamilyScreen({super.key});

  @override
  Widget build(BuildContext context) {
    final l = AppLocalizations.of(context);
    return Scaffold(
      appBar: AppBar(title: Text(l.familyMembers)),
      body: CitizenDataView(
        builder: (context, data) => [
          Card(
            child: Padding(
              padding: const EdgeInsets.all(18),
              child: Column(children: [
                InfoRow(label: l.familyId, value: valueText(data.familyCode)),
                InfoRow(label: l.familySizeLabel, value: valueText(l.memberCount(data.familySize))),
                InfoRow(
                  label: l.eligibilityTitle,
                  value: StatusPill(text: l.eligibleMembersOf(data.eligibleMembers, data.familySize), tone: eligibilityTone(data.eligibility)),
                ),
              ]),
            ),
          ),
          const SizedBox(height: 12),
          for (final member in data.members) ...[
            _MemberCard(member: member, overview: data),
            const SizedBox(height: 10),
          ],
        ],
      ),
    );
  }
}

class _MemberCard extends StatelessWidget {
  const _MemberCard({required this.member, required this.overview});

  final FamilyMember member;
  final CitizenOverview overview;

  @override
  Widget build(BuildContext context) {
    final l = AppLocalizations.of(context);
    final (word, tone) = switch (member.eligibility) {
      'Eligible' => (l.memberEligible, PillTone.good),
      'NotEligible' => (l.memberNotEligible, PillTone.bad),
      'Pending' => (l.memberPending, PillTone.warn),
      _ => (l.memberVerificationRequired, PillTone.warn),
    };
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Row(crossAxisAlignment: CrossAxisAlignment.start, children: [
          Initials(name: member.fullName, radius: 26),
          const SizedBox(width: 14),
          Expanded(
            child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
              Text(member.fullName, style: Theme.of(context).textTheme.titleMedium?.copyWith(fontWeight: FontWeight.w700)),
              const SizedBox(height: 2),
              Text('${relationshipWord(l, member.relationship)} · ${l.ageYears(member.age)}',
                  style: const TextStyle(color: AppColors.muted, fontSize: 15)),
              if (member.isHead && overview.aadhaarMasked.isNotEmpty) ...[
                const SizedBox(height: 6),
                Row(children: [
                  Icon(overview.aadhaarVerified ? Icons.verified_user_outlined : Icons.gpp_maybe_outlined,
                      size: 18, color: overview.aadhaarVerified ? AppColors.success : AppColors.warning),
                  const SizedBox(width: 6),
                  Flexible(
                    child: Text('${overview.aadhaarMasked} · ${overview.aadhaarVerified ? l.aadhaarVerified : l.aadhaarNotVerified}',
                        style: const TextStyle(fontSize: 14)),
                  ),
                ]),
              ],
              const SizedBox(height: 8),
              StatusPill(text: word, tone: tone),
            ]),
          ),
        ]),
      ),
    );
  }
}
