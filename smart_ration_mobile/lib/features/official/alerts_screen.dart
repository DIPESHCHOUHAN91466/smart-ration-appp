import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../app/theme.dart';
import '../../core/network/api_exception.dart';
import '../../core/privacy.dart';
import '../../l10n/app_localizations.dart';
import '../citizen/citizen_widgets.dart';
import 'official_data.dart';
import 'official_words.dart';

/// Open warnings from the backend's rules (e.g. the same QR scanned many times), most serious first.
/// They point at something worth checking; they never prove wrongdoing, and the screen says so.
/// An official can mark one under review, resolved or "not a problem"; the backend records who did it.
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

class _AlertCard extends ConsumerWidget {
  const _AlertCard({required this.alert});

  final AlertItem alert;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
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
          if (alert.underReview) ...[
            StatusPill(text: l.alertStatusUnderReview, tone: PillTone.neutral),
            const SizedBox(height: 4),
          ],
          if (alert.shopName.isNotEmpty) Text(alert.shopName, style: const TextStyle(color: AppColors.blue, fontWeight: FontWeight.w600)),
          if (alert.detectedAt != null) Text(localMoment(context, alert.detectedAt!), style: const TextStyle(color: AppColors.muted)),
          if (alert.description.isNotEmpty) ...[
            const SizedBox(height: 8),
            // The rule's own words come from the backend in English only.
            if (Localizations.localeOf(context).languageCode != 'en')
              Text(l.alertDetailsInEnglish, style: const TextStyle(color: AppColors.muted, fontSize: 13)),
            Text(alert.description, style: const TextStyle(fontSize: 15)),
          ],
          if (alert.note.isNotEmpty) ...[
            const SizedBox(height: 8),
            Text(l.alertReviewNote, style: const TextStyle(color: AppColors.muted, fontSize: 13)),
            Text(alert.note, style: const TextStyle(fontSize: 15)),
          ],
          const SizedBox(height: 10),
          Align(
            alignment: AlignmentDirectional.centerEnd,
            child: OutlinedButton.icon(
              icon: const Icon(Icons.edit_note),
              label: Text(l.alertUpdateButton),
              onPressed: () => _open(context, ref),
            ),
          ),
        ]),
      ),
    );
  }

  Future<void> _open(BuildContext context, WidgetRef ref) async {
    final l = AppLocalizations.of(context);
    final messenger = ScaffoldMessenger.of(context);
    final saved = await showModalBottomSheet<bool>(
      context: context,
      isScrollControlled: true,
      showDragHandle: true,
      builder: (_) => _UpdateForm(alert: alert),
    );
    if (saved != true) return;
    ref.invalidate(alertsProvider);
    messenger.showSnackBar(SnackBar(content: Text(l.alertUpdated)));
  }
}

class _UpdateForm extends ConsumerStatefulWidget {
  const _UpdateForm({required this.alert});

  final AlertItem alert;

  @override
  ConsumerState<_UpdateForm> createState() => _UpdateFormState();
}

class _UpdateFormState extends ConsumerState<_UpdateForm> {
  // The backend replaces the note on every update, so start from the one already there.
  late final _note = TextEditingController(text: widget.alert.note);
  late AlertDecision _decision = widget.alert.underReview ? AlertDecision.resolved : AlertDecision.underReview;
  String? _noteError;
  String? _error;
  bool _saving = false;

  @override
  void dispose() {
    _note.dispose();
    super.dispose();
  }

  Future<void> _save() async {
    final l = AppLocalizations.of(context);
    final aadhaarLike = aadhaarLikePattern.hasMatch(_note.text);
    setState(() => _noteError = aadhaarLike ? l.alertNoteHint : null);
    if (aadhaarLike) return;
    setState(() {
      _saving = true;
      _error = null;
    });
    try {
      await ref.read(officialRepositoryProvider).updateAlert(widget.alert.id, _decision, note: _note.text);
      if (mounted) Navigator.pop(context, true);
    } on ApiException catch (e) {
      if (mounted) setState(() => _error = e.messageIn(l));
    } finally {
      if (mounted) setState(() => _saving = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final l = AppLocalizations.of(context);
    final choices = [
      (AlertDecision.underReview, l.alertStatusUnderReview, l.alertChooseReviewHint),
      (AlertDecision.resolved, l.alertChooseResolved, l.alertChooseResolvedHint),
      (AlertDecision.dismissed, l.alertChooseDismissed, l.alertChooseDismissedHint),
    ];
    return Padding(
      // Keeps the form above the keyboard.
      padding: EdgeInsets.fromLTRB(20, 0, 20, 20 + MediaQuery.viewInsetsOf(context).bottom),
      child: SingleChildScrollView(
        child: Column(mainAxisSize: MainAxisSize.min, crossAxisAlignment: CrossAxisAlignment.stretch, children: [
          Text(l.alertUpdateTitle, style: Theme.of(context).textTheme.titleLarge?.copyWith(fontWeight: FontWeight.w700)),
          Text(alertTypeWord(l, widget.alert.type), style: const TextStyle(color: AppColors.muted)),
          const SizedBox(height: 8),
          RadioGroup<AlertDecision>(
            groupValue: _decision,
            onChanged: (d) {
              if (d != null && !_saving) setState(() => _decision = d);
            },
            child: Column(children: [
              for (final (value, title, hint) in choices)
                RadioListTile<AlertDecision>(
                  value: value,
                  contentPadding: EdgeInsets.zero,
                  title: Text(title, style: const TextStyle(fontWeight: FontWeight.w600)),
                  subtitle: Text(hint),
                ),
            ]),
          ),
          const SizedBox(height: 8),
          TextField(
            controller: _note,
            maxLength: 500,
            maxLines: 3,
            minLines: 1,
            decoration: InputDecoration(labelText: l.noteLabel, helperText: l.alertNoteHint, helperMaxLines: 2, errorText: _noteError, errorMaxLines: 2),
          ),
          if (_error != null) ...[
            const SizedBox(height: 8),
            Semantics(liveRegion: true, child: Text(_error!, style: const TextStyle(color: AppColors.danger, fontWeight: FontWeight.w600))),
          ],
          const SizedBox(height: 16),
          FilledButton(
            onPressed: _saving ? null : _save,
            child: _saving
                ? const SizedBox.square(dimension: 22, child: CircularProgressIndicator(strokeWidth: 3))
                : Text(l.saveButton),
          ),
        ]),
      ),
    );
  }
}
