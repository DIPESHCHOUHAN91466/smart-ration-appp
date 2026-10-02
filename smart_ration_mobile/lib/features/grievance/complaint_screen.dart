import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../app/routes.dart';
import '../../app/theme.dart';
import '../../core/network/api_exception.dart';
import '../../core/privacy.dart';
import '../../l10n/app_localizations.dart';
import '../auth/auth_controller.dart';
import '../citizen/citizen_widgets.dart';
import '../help/voice.dart';
import '../shop/shop_data.dart' show newRequestKey;
import 'grievance_data.dart';
import 'grievance_words.dart';

enum _Step { write, review, sent }

/// Report a problem: write (or check what the AI assistant filled in), review, confirm, then the reference
/// number, shown and read aloud. Nothing is sent before the person taps "Confirm and send".
class ComplaintScreen extends ConsumerStatefulWidget {
  const ComplaintScreen({super.key, this.draft});

  /// Pre-filled by the AI assistant, or null for an empty form.
  final ComplaintDraft? draft;

  @override
  ConsumerState<ComplaintScreen> createState() => _ComplaintScreenState();
}

class _ComplaintScreenState extends ConsumerState<ComplaintScreen> {
  /// Chosen once and reused if "Confirm and send" is pressed again, so a lost answer never files it twice.
  final _requestKey = newRequestKey();
  late final _description = TextEditingController(text: widget.draft?.description ?? '');
  late ComplaintCategory? _category = widget.draft?.category;
  late String? _item = widget.draft?.rationType;
  late _Step _step = _complete ? _Step.review : _Step.write;
  bool _checked = false; // show what is missing only after the first attempt (or when the assistant filled it)
  bool _sending = false;
  bool _reading = false;
  String? _error;
  Complaint? _sent;
  late final Speaker _speaker = ref.read(speakerProvider);

  bool get _fromAssistant => widget.draft?.fromAssistant ?? false;
  String get _language => Localizations.localeOf(context).languageCode;

  bool get _descriptionOk => _description.text.trim().length >= complaintMinLength;
  bool get _privateOk => !aadhaarLikePattern.hasMatch(_description.text);
  bool get _complete => _category != null && _descriptionOk && _privateOk;

  @override
  void initState() {
    super.initState();
    _checked = _fromAssistant;
  }

  @override
  void dispose() {
    if (_reading) _speaker.stop();
    _description.dispose();
    super.dispose();
  }

  void _toReview() {
    setState(() => _checked = true);
    if (_complete) setState(() => _step = _Step.review);
  }

  Future<void> _send() async {
    final l = AppLocalizations.of(context);
    setState(() {
      _sending = true;
      _error = null;
    });
    try {
      final sent = await ref.read(grievanceRepositoryProvider).submit(
            category: _category!,
            description: _description.text,
            rationType: _item,
            fromAssistant: _fromAssistant,
            requestKey: _requestKey,
          );
      if (!mounted) return;
      ref.invalidate(myComplaintsProvider);
      setState(() {
        _sent = sent;
        _step = _Step.sent;
      });
      // Someone who spoke their complaint hears the result too.
      if (_fromAssistant) _readConfirmation();
    } on ApiException catch (e) {
      if (mounted) setState(() => _error = complaintErrorIn(l, e));
    } finally {
      if (mounted) setState(() => _sending = false);
    }
  }

  Future<void> _readConfirmation() async {
    final l = AppLocalizations.of(context);
    final messenger = ScaffoldMessenger.of(context);
    if (_reading) {
      await _speaker.stop();
      if (mounted) setState(() => _reading = false);
      return;
    }
    setState(() => _reading = true);
    final spoken = await _speaker.speak(l.complaintSentSpoken(spokenReference(_sent!.reference)), _language);
    if (!mounted) return;
    setState(() => _reading = false);
    if (!spoken) messenger.showSnackBar(SnackBar(content: Text(l.voiceMissing)));
  }

  @override
  Widget build(BuildContext context) {
    final l = AppLocalizations.of(context);
    return Scaffold(
      appBar: AppBar(
        title: Text(_step == _Step.review ? l.complaintReviewTitle : _step == _Step.sent ? l.complaintSent : l.complaintTitle),
      ),
      body: ListView(padding: const EdgeInsets.all(16), children: switch (_step) {
        _Step.write => _writeStep(l),
        _Step.review => _reviewStep(l),
        _Step.sent => _sentStep(l),
      }),
    );
  }

  List<Widget> _writeStep(AppLocalizations l) {
    final text = Theme.of(context).textTheme;
    return [
      if (_fromAssistant) ...[
        _Banner(icon: Icons.auto_awesome, text: l.complaintFilledByAi),
        const SizedBox(height: 12),
      ],
      Text(l.complaintWhat, style: text.titleMedium?.copyWith(fontWeight: FontWeight.w700)),
      if (_checked && _category == null)
        Semantics(liveRegion: true, child: Text(l.complaintChooseCategory, style: const TextStyle(color: AppColors.danger, fontWeight: FontWeight.w600))),
      const SizedBox(height: 8),
      Wrap(spacing: 8, runSpacing: 8, children: [
        for (final c in ComplaintCategory.values)
          ChoiceChip(
            avatar: Icon(categoryIcon(c), size: 20),
            label: Text(categoryWord(l, c), style: const TextStyle(fontSize: 16)),
            selected: _category == c,
            onSelected: (_) => setState(() => _category = c),
          ),
      ]),
      const SizedBox(height: 20),
      Text(l.complaintItem, style: text.titleMedium?.copyWith(fontWeight: FontWeight.w700)),
      const SizedBox(height: 8),
      Wrap(spacing: 8, runSpacing: 8, children: [
        ChoiceChip(label: Text(l.complaintNoItem), selected: _item == null, onSelected: (_) => setState(() => _item = null)),
        for (final item in complaintItems)
          ChoiceChip(
            avatar: Icon(itemIcon(item), size: 20),
            label: Text(itemWord(l, item)),
            selected: _item == item,
            onSelected: (_) => setState(() => _item = item),
          ),
      ]),
      const SizedBox(height: 20),
      TextField(
        controller: _description,
        minLines: 3,
        maxLines: 8,
        maxLength: complaintMaxLength,
        onChanged: (_) => setState(() {}),
        decoration: InputDecoration(
          labelText: l.complaintDescribe,
          hintText: l.complaintDescribeHint,
          alignLabelWithHint: true,
          helperText: l.complaintNoPrivate,
          helperMaxLines: 2,
          errorMaxLines: 2,
          errorText: !_privateOk ? l.complaintNoPrivate : (_checked && !_descriptionOk ? l.complaintDescribeShort : null),
        ),
      ),
      const SizedBox(height: 12),
      _YourDetails(),
      const SizedBox(height: 20),
      FilledButton.icon(
        style: FilledButton.styleFrom(minimumSize: const Size.fromHeight(56)),
        icon: const Icon(Icons.fact_check_outlined),
        label: Text(l.complaintReviewButton),
        onPressed: _toReview,
      ),
    ];
  }

  List<Widget> _reviewStep(AppLocalizations l) {
    return [
      _Banner(icon: Icons.info_outline, text: l.complaintReviewNote),
      const SizedBox(height: 12),
      SectionCard(
        title: l.complaintTitle,
        icon: Icons.report_problem_outlined,
        child: Column(crossAxisAlignment: CrossAxisAlignment.stretch, children: [
          InfoRow(label: l.complaintWhat, value: valueText(categoryWord(l, _category!))),
          if (_item != null) InfoRow(label: l.complaintItem, value: valueText(itemWord(l, _item!))),
          const SizedBox(height: 8),
          Text(l.complaintDescribe, style: const TextStyle(color: AppColors.muted)),
          const SizedBox(height: 4),
          Text(_description.text.trim(), style: const TextStyle(fontSize: 16)),
        ]),
      ),
      const SizedBox(height: 12),
      _YourDetails(),
      const SizedBox(height: 16),
      if (_error != null) ...[
        Semantics(liveRegion: true, child: Text(_error!, style: const TextStyle(color: AppColors.danger, fontSize: 16, fontWeight: FontWeight.w600))),
        const SizedBox(height: 12),
      ],
      FilledButton.icon(
        style: FilledButton.styleFrom(
          backgroundColor: AppColors.success,
          minimumSize: const Size.fromHeight(60),
          textStyle: const TextStyle(fontSize: 18, fontWeight: FontWeight.w700),
        ),
        icon: _sending
            ? const SizedBox.square(dimension: 22, child: CircularProgressIndicator(strokeWidth: 3, color: Colors.white))
            : const Icon(Icons.send, size: 26),
        label: Text(_sending ? l.saving : l.complaintSubmit),
        onPressed: _sending ? null : _send,
      ),
      const SizedBox(height: 8),
      OutlinedButton.icon(
        icon: const Icon(Icons.edit_outlined),
        label: Text(l.complaintEdit),
        onPressed: _sending ? null : () => setState(() => _step = _Step.write),
      ),
    ];
  }

  List<Widget> _sentStep(AppLocalizations l) {
    final sent = _sent!;
    return [
      Card(
        color: AppColors.successSoft,
        child: Padding(
          padding: const EdgeInsets.all(20),
          child: Semantics(
            liveRegion: true,
            child: Column(children: [
              const Icon(Icons.check_circle, color: AppColors.success, size: 56),
              const SizedBox(height: 8),
              Text(l.complaintSent, style: const TextStyle(color: AppColors.success, fontSize: 22, fontWeight: FontWeight.w800)),
              const SizedBox(height: 12),
              Text(l.complaintReference, style: const TextStyle(color: AppColors.muted)),
              SelectableText(sent.reference, style: const TextStyle(fontSize: 26, fontWeight: FontWeight.w800, letterSpacing: 1)),
            ]),
          ),
        ),
      ),
      const SizedBox(height: 12),
      Text(l.complaintKeepReference, style: const TextStyle(fontSize: 16)),
      const SizedBox(height: 16),
      OutlinedButton.icon(
        icon: Icon(_reading ? Icons.stop_circle_outlined : Icons.volume_up_outlined),
        label: Text(_reading ? l.stopReading : l.readAloud),
        onPressed: _readConfirmation,
      ),
      const SizedBox(height: 8),
      OutlinedButton.icon(
        icon: const Icon(Icons.list_alt),
        label: Text(l.myComplaints),
        onPressed: () => context.pushReplacement(Routes.citizenComplaints),
      ),
      const SizedBox(height: 8),
      FilledButton(onPressed: () => context.pop(), child: Text(l.doneButton)),
    ];
  }
}

class _Banner extends StatelessWidget {
  const _Banner({required this.icon, required this.text});

  final IconData icon;
  final String text;

  @override
  Widget build(BuildContext context) => Card(
        color: const Color(0xFFE7F1FF),
        child: Padding(
          padding: const EdgeInsets.all(14),
          child: Row(children: [
            Icon(icon, color: AppColors.blue),
            const SizedBox(width: 10),
            Expanded(child: Text(text, style: const TextStyle(fontSize: 15, fontWeight: FontWeight.w600))),
          ]),
        ),
      );
}

/// The person's own name and mobile, from their account: shown so they know who is complaining,
/// never typed again and never sent with the form (the backend knows them).
class _YourDetails extends ConsumerWidget {
  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final l = AppLocalizations.of(context);
    final user = ref.watch(authControllerProvider);
    if (user == null) return const SizedBox.shrink();
    return SectionCard(
      title: l.complaintYourDetails,
      icon: Icons.person_outline,
      child: Column(children: [
        InfoRow(label: l.complaintNameLabel, value: valueText(user.fullName)),
        InfoRow(label: l.registeredMobile, value: valueText(user.mobileNumber)),
      ]),
    );
  }
}
