import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../app/theme.dart';
import '../../core/network/api_exception.dart';
import '../../core/privacy.dart';
import '../../l10n/app_localizations.dart';
import '../citizen/citizen_widgets.dart';
import '../grievance/grievance_data.dart';
import '../grievance/grievance_words.dart';
import 'official_words.dart';

/// Officials: every citizen complaint, newest first, filtered by status (new ones first, as on the website).
/// An open complaint can be moved to "being checked", resolved or closed, with a reply the citizen sees.
class OfficialComplaintsScreen extends ConsumerStatefulWidget {
  const OfficialComplaintsScreen({super.key});

  @override
  ConsumerState<OfficialComplaintsScreen> createState() => _OfficialComplaintsScreenState();
}

class _OfficialComplaintsScreenState extends ConsumerState<OfficialComplaintsScreen> {
  ComplaintStatus? _only = ComplaintStatus.submitted;

  @override
  Widget build(BuildContext context) {
    final l = AppLocalizations.of(context);
    final complaints = ref.watch(allComplaintsProvider(_only));
    return Scaffold(
      appBar: AppBar(title: Text(l.officialComplaintsTitle)),
      body: RefreshIndicator(
        onRefresh: () => ref.refresh(allComplaintsProvider(_only).future),
        child: ListView(
          padding: const EdgeInsets.all(16),
          children: [
            Wrap(spacing: 8, runSpacing: 8, children: [
              for (final option in <ComplaintStatus?>[...ComplaintStatus.values, null])
                ChoiceChip(
                  label: Text(option == null ? l.filterAll : complaintStatusWord(l, option)),
                  selected: _only == option,
                  onSelected: (_) => setState(() => _only = option),
                ),
            ]),
            const SizedBox(height: 12),
            ...complaints.when(
              loading: () => [const SizedBox(height: 60), const Center(child: CircularProgressIndicator())],
              error: (e, _) => [
                Text(e is ApiException ? e.messageIn(l) : l.errorGeneric, textAlign: TextAlign.center),
                TextButton(onPressed: () => ref.invalidate(allComplaintsProvider(_only)), child: Text(l.tryAgain)),
              ],
              data: (all) => all.isEmpty
                  ? [Text(l.noComplaintsHere, style: Theme.of(context).textTheme.titleMedium)]
                  : [for (final c in all) _ComplaintCard(complaint: c)],
            ),
          ],
        ),
      ),
    );
  }
}

class _ComplaintCard extends ConsumerWidget {
  const _ComplaintCard({required this.complaint});

  final Complaint complaint;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final l = AppLocalizations.of(context);
    final c = complaint;
    return Card(
      margin: const EdgeInsets.only(bottom: 10),
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
          Row(children: [
            Icon(categoryIcon(c.category), color: AppColors.blue),
            const SizedBox(width: 8),
            Expanded(child: Text(categoryWord(l, c.category), style: const TextStyle(fontSize: 17, fontWeight: FontWeight.w700))),
          ]),
          const SizedBox(height: 6),
          StatusPill(text: complaintStatusWord(l, c.status), tone: complaintStatusTone(c.status)),
          const SizedBox(height: 8),
          InfoRow(label: l.complaintReference, value: valueText(c.reference)),
          if (c.shopName.isNotEmpty) InfoRow(label: l.complaintShopLabel, value: valueText(c.shopName)),
          if (c.rationType != null) InfoRow(label: l.complaintItem, value: valueText(itemWord(l, c.rationType!))),
          if (c.createdAt != null) Text(localMoment(context, c.createdAt!), style: const TextStyle(color: AppColors.muted)),
          const SizedBox(height: 6),
          Text(c.description, style: const TextStyle(fontSize: 15)),
          if (c.officeReply.isNotEmpty) ...[
            const SizedBox(height: 8),
            Text(l.complaintOfficeReply, style: const TextStyle(color: AppColors.muted, fontSize: 13)),
            Text(c.officeReply, style: const TextStyle(fontSize: 15, fontWeight: FontWeight.w600)),
          ],
          if (c.status.isOpen) ...[
            const SizedBox(height: 10),
            Align(
              alignment: AlignmentDirectional.centerEnd,
              child: OutlinedButton.icon(
                icon: const Icon(Icons.edit_note),
                label: Text(l.alertUpdateButton),
                onPressed: () => _open(context, ref),
              ),
            ),
          ],
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
      builder: (_) => _UpdateForm(complaint: complaint),
    );
    if (saved != true) return;
    // Every filter may have changed (the complaint moves from one status to another).
    ref.invalidate(allComplaintsProvider);
    messenger.showSnackBar(SnackBar(content: Text(l.complaintUpdated)));
  }
}

class _UpdateForm extends ConsumerStatefulWidget {
  const _UpdateForm({required this.complaint});

  final Complaint complaint;

  @override
  ConsumerState<_UpdateForm> createState() => _UpdateFormState();
}

class _UpdateFormState extends ConsumerState<_UpdateForm> {
  // The backend replaces the reply on every update, so start from the one already there.
  late final _note = TextEditingController(text: widget.complaint.officeReply);
  late ComplaintStatus _decision =
      widget.complaint.status == ComplaintStatus.submitted ? ComplaintStatus.underReview : ComplaintStatus.resolved;
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
    setState(() => _noteError = aadhaarLike ? l.complaintNoPrivate : null);
    if (aadhaarLike) return;
    setState(() {
      _saving = true;
      _error = null;
    });
    try {
      await ref.read(grievanceRepositoryProvider).updateStatus(widget.complaint.id, _decision, note: _note.text);
      if (mounted) Navigator.pop(context, true);
    } on ApiException catch (e) {
      if (mounted) setState(() => _error = complaintErrorIn(l, e));
    } finally {
      if (mounted) setState(() => _saving = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final l = AppLocalizations.of(context);
    final choices = [
      // As on the website: "being checked" only for a complaint nobody has looked at yet.
      if (widget.complaint.status == ComplaintStatus.submitted)
        (ComplaintStatus.underReview, l.complaintStatusUnderReview, l.complaintChooseReviewHint),
      (ComplaintStatus.resolved, l.complaintStatusResolved, l.complaintChooseResolvedHint),
      (ComplaintStatus.rejected, l.complaintStatusRejected, l.complaintChooseRejectedHint),
    ];
    return Padding(
      // Keeps the form above the keyboard.
      padding: EdgeInsets.fromLTRB(20, 0, 20, 20 + MediaQuery.viewInsetsOf(context).bottom),
      child: SingleChildScrollView(
        child: Column(mainAxisSize: MainAxisSize.min, crossAxisAlignment: CrossAxisAlignment.stretch, children: [
          Text(l.complaintUpdateTitle, style: Theme.of(context).textTheme.titleLarge?.copyWith(fontWeight: FontWeight.w700)),
          Text(widget.complaint.reference, style: const TextStyle(color: AppColors.muted)),
          const SizedBox(height: 8),
          RadioGroup<ComplaintStatus>(
            groupValue: _decision,
            onChanged: (d) {
              if (d != null && !_saving) setState(() => _decision = d);
            },
            child: Column(children: [
              for (final (value, title, hint) in choices)
                RadioListTile<ComplaintStatus>(
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
            decoration: InputDecoration(
              labelText: l.complaintReplyLabel,
              helperText: l.complaintReplyHint,
              helperMaxLines: 3,
              errorText: _noteError,
              errorMaxLines: 2,
            ),
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
