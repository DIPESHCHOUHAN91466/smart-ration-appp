import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../app/theme.dart';
import '../../core/network/api_exception.dart';
import '../../l10n/app_localizations.dart';
import 'citizen_data.dart';

// ---------------------------------------------------------------- words for the backend's values

String relationshipWord(AppLocalizations l, String value) => switch (value) {
      'Head' => l.relHead,
      'Spouse' => l.relSpouse,
      'Son' => l.relSon,
      'Daughter' => l.relDaughter,
      'Parent' => l.relParent,
      _ => l.relOther,
    };

String itemWord(AppLocalizations l, String rationType) => switch (rationType) {
      'Rice' => l.itemRice,
      'Wheat' => l.itemWheat,
      'Sugar' => l.itemSugar,
      'Pulses' => l.itemPulses,
      'EdibleOil' => l.itemOil,
      'Salt' => l.itemSalt,
      _ => rationType,
    };

/// Edible oil is measured in litres, everything else in kilograms (database/seeds/synthetic/ration_items.json).
String unitWord(AppLocalizations l, String rationType) => rationType == 'EdibleOil' ? l.unitLitre : l.unitKg;

/// 15 -> "15", 1.5 -> "1.5", 0.75 -> "0.75".
String amount(double value) {
  if (value == value.roundToDouble()) return value.toInt().toString();
  return value.toStringAsFixed(2).replaceFirst(RegExp(r'0+$'), '').replaceFirst(RegExp(r'\.$'), '');
}

IconData itemIcon(String rationType) => switch (rationType) {
      'EdibleOil' => Icons.water_drop_outlined,
      'Salt' || 'Sugar' => Icons.grain,
      _ => Icons.rice_bowl_outlined,
    };

// ---------------------------------------------------------------- small building blocks

enum PillTone { good, warn, bad, neutral }

/// A coloured label. Always words, never colour alone.
class StatusPill extends StatelessWidget {
  const StatusPill({super.key, required this.text, required this.tone});

  final String text;
  final PillTone tone;

  @override
  Widget build(BuildContext context) {
    final (fg, bg) = switch (tone) {
      PillTone.good => (AppColors.success, AppColors.successSoft),
      PillTone.warn => (AppColors.warning, AppColors.warningSoft),
      PillTone.bad => (AppColors.danger, AppColors.dangerSoft),
      PillTone.neutral => (AppColors.muted, const Color(0xFFEDF2F7)),
    };
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 5),
      decoration: BoxDecoration(color: bg, borderRadius: BorderRadius.circular(99)),
      child: Text(text, style: TextStyle(color: fg, fontWeight: FontWeight.w700, fontSize: 14)),
    );
  }
}

PillTone eligibilityTone(FamilyEligibility e) => switch (e) {
      FamilyEligibility.eligible => PillTone.good,
      FamilyEligibility.partiallyEligible => PillTone.warn,
      FamilyEligibility.notEligible => PillTone.bad,
    };

String eligibilityWord(AppLocalizations l, FamilyEligibility e) => switch (e) {
      FamilyEligibility.eligible => l.familyEligible,
      FamilyEligibility.partiallyEligible => l.familyPartiallyEligible,
      FamilyEligibility.notEligible => l.familyNotEligible,
    };

/// A white card with a heading; tappable when [onTap] is given.
class SectionCard extends StatelessWidget {
  const SectionCard({super.key, required this.title, required this.icon, required this.child, this.trailing, this.onTap});

  final String title;
  final IconData icon;
  final Widget child;
  final Widget? trailing;
  final VoidCallback? onTap;

  @override
  Widget build(BuildContext context) {
    final l = AppLocalizations.of(context);
    return Card(
      clipBehavior: Clip.antiAlias,
      child: InkWell(
        onTap: onTap,
        child: Padding(
          padding: const EdgeInsets.all(18),
          child: Column(crossAxisAlignment: CrossAxisAlignment.stretch, children: [
            Row(children: [
              Icon(icon, color: AppColors.blue, size: 26),
              const SizedBox(width: 10),
              Expanded(child: Text(title, style: Theme.of(context).textTheme.titleMedium?.copyWith(fontWeight: FontWeight.w700))),
              ?trailing,
            ]),
            const SizedBox(height: 14),
            child,
            if (onTap != null) ...[
              const SizedBox(height: 10),
              Align(
                alignment: AlignmentDirectional.centerEnd,
                child: Row(mainAxisSize: MainAxisSize.min, children: [
                  Text(l.viewDetails, style: const TextStyle(color: AppColors.blue, fontWeight: FontWeight.w600)),
                  const Icon(Icons.chevron_right, color: AppColors.blue),
                ]),
              ),
            ],
          ]),
        ),
      ),
    );
  }
}

/// "Label ........ value" on one line; the value wraps instead of overflowing.
class InfoRow extends StatelessWidget {
  const InfoRow({super.key, required this.label, required this.value});

  final String label;
  final Widget value;

  @override
  Widget build(BuildContext context) => Padding(
        padding: const EdgeInsets.symmetric(vertical: 6),
        child: Row(crossAxisAlignment: CrossAxisAlignment.start, children: [
          Expanded(flex: 2, child: Text(label, style: const TextStyle(color: AppColors.muted, fontSize: 15))),
          const SizedBox(width: 12),
          Expanded(flex: 3, child: Align(alignment: AlignmentDirectional.centerEnd, child: value)),
        ]),
      );
}

Text valueText(String text) => Text(text, textAlign: TextAlign.end, style: const TextStyle(fontSize: 16, fontWeight: FontWeight.w600));

/// Shown while the backend serves synthetic data, so nobody mistakes it for a real card.
class DemoDataBanner extends StatelessWidget {
  const DemoDataBanner({super.key});

  @override
  Widget build(BuildContext context) => Container(
        padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 10),
        decoration: BoxDecoration(color: AppColors.warningSoft, borderRadius: BorderRadius.circular(12)),
        child: Row(children: [
          const Icon(Icons.science_outlined, color: AppColors.warning),
          const SizedBox(width: 10),
          Expanded(
            child: Text(AppLocalizations.of(context).demoDataNotice,
                style: const TextStyle(color: AppColors.warning, fontWeight: FontWeight.w600)),
          ),
        ]),
      );
}

/// Loads the citizen's data and shows loading / error (with Try again) / the content.
/// Pull down to reload.
class CitizenDataView extends ConsumerWidget {
  const CitizenDataView({super.key, required this.builder, this.alsoRefresh});

  final List<Widget> Function(BuildContext context, CitizenOverview data) builder;

  /// Anything else the screen shows that a pull should reload too (e.g. the dashboard's tokens).
  final void Function(WidgetRef ref)? alsoRefresh;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final l = AppLocalizations.of(context);
    final data = ref.watch(citizenOverviewProvider);
    return RefreshIndicator(
      onRefresh: () {
        alsoRefresh?.call(ref);
        return ref.refresh(citizenOverviewProvider.future);
      },
      child: ListView(
        padding: const EdgeInsets.all(16),
        children: data.when(
          loading: () => [
            const SizedBox(height: 80),
            const Center(child: CircularProgressIndicator()),
            const SizedBox(height: 16),
            Center(child: Text(l.loading)),
          ],
          error: (error, _) => [
            const SizedBox(height: 40),
            Icon(Icons.error_outline, color: AppColors.danger, size: 48, semanticLabel: l.errorGeneric),
            const SizedBox(height: 12),
            Text(
              error is ApiException && error.kind == ApiErrorKind.notFound
                  ? l.noBeneficiaryProfile
                  : error is ApiException
                      ? error.messageIn(l)
                      : l.errorGeneric,
              textAlign: TextAlign.center,
              style: Theme.of(context).textTheme.titleMedium,
            ),
            const SizedBox(height: 20),
            FilledButton.icon(
              onPressed: () => ref.invalidate(citizenOverviewProvider),
              icon: const Icon(Icons.refresh),
              label: Text(l.tryAgain),
            ),
          ],
          data: (overview) => [
            if (overview.isDemoData) ...[const DemoDataBanner(), const SizedBox(height: 12)],
            ...builder(context, overview),
          ],
        ),
      ),
    );
  }
}
