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
import 'shop_words.dart';

/// The backend's verdict on one customer: who they are, every check, what to hand over, and, only
/// when the backend says READY, the button that records the handover.
class CustomerCheckScreen extends ConsumerStatefulWidget {
  const CustomerCheckScreen({super.key, required this.check});

  /// Null when the screen was opened without a scan (e.g. after the app was restarted).
  final CustomerCheck? check;

  @override
  ConsumerState<CustomerCheckScreen> createState() => _CustomerCheckScreenState();
}

class _CustomerCheckScreenState extends ConsumerState<CustomerCheckScreen> {
  /// Chosen once for this handover and reused on every retry (see ShopRepository.confirm).
  final _requestKey = newRequestKey();
  bool _saving = false;
  String? _error;

  Future<void> _handOver(CustomerCheck check) async {
    final l = AppLocalizations.of(context);
    final yes = await showDialog<bool>(
      context: context,
      builder: (dialog) => AlertDialog(
        title: Text(l.handOverConfirmTitle),
        content: Text(l.handOverConfirmBody(check.name)),
        actions: [
          TextButton(onPressed: () => Navigator.pop(dialog, false), child: Text(l.notYet)),
          FilledButton(onPressed: () => Navigator.pop(dialog, true), child: Text(l.yesHandedOver)),
        ],
      ),
    );
    if (yes != true || !mounted) return;
    setState(() {
      _saving = true;
      _error = null;
    });
    try {
      final receipt = await ref.read(shopRepositoryProvider).confirm(check, _requestKey);
      if (mounted) context.pushReplacement(Routes.shopReceipt, extra: receipt);
    } on ApiException catch (e) {
      if (mounted) setState(() => _error = handoverErrorIn(l, e));
    } finally {
      if (mounted) setState(() => _saving = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final l = AppLocalizations.of(context);
    final check = widget.check;
    return Scaffold(
      appBar: AppBar(title: Text(l.checkTitle)),
      body: check == null
          ? Center(child: Padding(padding: const EdgeInsets.all(24), child: Text(l.nothingToCheck, textAlign: TextAlign.center)))
          : ListView(
              padding: const EdgeInsets.all(16),
              children: [
                _Verdict(check: check),
                const SizedBox(height: 12),
                _CustomerCard(check: check),
                const SizedBox(height: 12),
                _ChecksCard(check: check),
                const SizedBox(height: 12),
                _ItemsCard(tokenId: check.tokenId),
                const SizedBox(height: 16),
                if (_error != null) ...[
                  Semantics(
                    liveRegion: true,
                    child: Text(_error!, style: const TextStyle(color: AppColors.danger, fontSize: 16, fontWeight: FontWeight.w600)),
                  ),
                  const SizedBox(height: 12),
                ],
                if (check.ready)
                  FilledButton.icon(
                    style: FilledButton.styleFrom(
                      backgroundColor: AppColors.success,
                      minimumSize: const Size.fromHeight(60),
                      textStyle: const TextStyle(fontSize: 18, fontWeight: FontWeight.w700),
                    ),
                    icon: _saving
                        ? const SizedBox.square(dimension: 22, child: CircularProgressIndicator(strokeWidth: 3, color: Colors.white))
                        : const Icon(Icons.check_circle_outline, size: 28),
                    label: Text(_saving ? l.saving : l.handOverButton),
                    onPressed: _saving ? null : () => _handOver(check),
                  ),
                const SizedBox(height: 8),
                OutlinedButton.icon(
                  icon: const Icon(Icons.qr_code_scanner),
                  label: Text(l.scanAgain),
                  onPressed: _saving ? null : () => context.pop(),
                ),
                const SizedBox(height: 24),
              ],
            ),
    );
  }
}

class _Verdict extends StatelessWidget {
  const _Verdict({required this.check});

  final CustomerCheck check;

  @override
  Widget build(BuildContext context) {
    final l = AppLocalizations.of(context);
    final ready = check.ready;
    final color = ready ? AppColors.success : AppColors.danger;
    return Card(
      color: ready ? AppColors.successSoft : AppColors.dangerSoft,
      child: Padding(
        padding: const EdgeInsets.all(18),
        child: Semantics(
          liveRegion: true,
          child: Row(crossAxisAlignment: CrossAxisAlignment.start, children: [
            Icon(ready ? Icons.check_circle : Icons.block, color: color, size: 40),
            const SizedBox(width: 14),
            Expanded(
              child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                Text(ready ? l.readyTitle : l.blockedTitle, style: TextStyle(color: color, fontSize: 22, fontWeight: FontWeight.w800)),
                const SizedBox(height: 4),
                Text(ready ? l.readyBody : blockedReasonIn(l, check.blockedReason), style: const TextStyle(fontSize: 16)),
              ]),
            ),
          ]),
        ),
      ),
    );
  }
}

class _CustomerCard extends StatelessWidget {
  const _CustomerCard({required this.check});

  final CustomerCheck check;

  @override
  Widget build(BuildContext context) {
    final l = AppLocalizations.of(context);
    return SectionCard(
      title: l.customer,
      icon: Icons.person_outline,
      trailing: StatusPill(text: check.method == CheckMethod.otp ? l.identifiedByOtp : l.identifiedByQr, tone: PillTone.neutral),
      child: Column(crossAxisAlignment: CrossAxisAlignment.stretch, children: [
        Text(check.name, style: const TextStyle(fontSize: 22, fontWeight: FontWeight.w700)),
        const SizedBox(height: 8),
        InfoRow(label: l.beneficiaryId, value: valueText(check.beneficiaryCode)),
        InfoRow(label: l.registeredMobile, value: valueText(check.mobileMasked)),
        InfoRow(label: l.familyId, value: valueText(check.familyCode)),
        if (check.schemeName.isNotEmpty) InfoRow(label: l.cardScheme, value: valueText(check.schemeName)),
        InfoRow(label: l.familyMembers, value: valueText(l.eligibleMembersOf(check.eligibleMembers, check.familySize))),
        const Divider(height: 24),
        InfoRow(label: l.tokenNumber, value: valueText(check.tokenNumber)),
        if (check.collectionDate != null) InfoRow(label: l.collectionDate, value: valueText(longDate(context, check.collectionDate!))),
        if (check.bookingTime.isNotEmpty) InfoRow(label: l.collectionTime, value: valueText(timeLabel(context, check.bookingTime))),
      ]),
    );
  }
}

class _ChecksCard extends StatelessWidget {
  const _ChecksCard({required this.check});

  final CustomerCheck check;

  @override
  Widget build(BuildContext context) {
    final l = AppLocalizations.of(context);
    final rows = [
      (l.checkAadhaar, check.aadhaarVerified),
      (l.checkPassbook, check.passbookVerified),
      (l.checkMobile, check.mobileVerified),
      (l.checkToken, check.tokenValid),
      (l.checkFamily, check.familyEligible),
      (l.checkEntitlement, check.entitlementLeft),
    ];
    return SectionCard(
      title: l.checksTitle,
      icon: Icons.fact_check_outlined,
      child: Column(children: [
        for (final (label, passed) in rows)
          // One item for screen readers: "Aadhaar verified: Yes".
          Semantics(
            container: true,
            label: '$label: ${passed ? l.checkPassed : l.checkFailed}',
            excludeSemantics: true,
            child: Padding(
              padding: const EdgeInsets.symmetric(vertical: 5),
              child: Row(children: [
                Icon(passed ? Icons.check_circle : Icons.cancel, color: passed ? AppColors.success : AppColors.danger, size: 24),
                const SizedBox(width: 10),
                Expanded(child: Text(label, style: const TextStyle(fontSize: 16))),
                Text(passed ? l.checkPassed : l.checkFailed,
                    style: TextStyle(fontWeight: FontWeight.w700, color: passed ? AppColors.success : AppColors.danger)),
              ]),
            ),
          ),
      ]),
    );
  }
}

class _ItemsCard extends ConsumerWidget {
  const _ItemsCard({required this.tokenId});

  final int tokenId;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final l = AppLocalizations.of(context);
    final token = ref.watch(shopTokenProvider(tokenId));
    return SectionCard(
      title: l.itemsToHandOver,
      icon: Icons.shopping_bag_outlined,
      child: token.when(
        loading: () => const Center(child: CircularProgressIndicator()),
        error: (e, _) => Column(children: [
          Text(e is ApiException ? e.messageIn(l) : l.errorGeneric),
          TextButton(onPressed: () => ref.invalidate(shopTokenProvider(tokenId)), child: Text(l.tryAgain)),
        ]),
        data: (t) => Column(children: [
          for (final (type, quantity) in t.items)
            Padding(
              padding: const EdgeInsets.symmetric(vertical: 5),
              child: Row(children: [
                Icon(itemIcon(type), color: AppColors.muted, size: 24),
                const SizedBox(width: 10),
                Expanded(child: Text(itemWord(l, type), style: const TextStyle(fontSize: 17))),
                Text('${amount(quantity)} ${unitWord(l, type)}', style: const TextStyle(fontSize: 17, fontWeight: FontWeight.w700)),
              ]),
            ),
        ]),
      ),
    );
  }
}
