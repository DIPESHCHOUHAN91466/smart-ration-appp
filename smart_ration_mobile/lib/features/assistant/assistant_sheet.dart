import 'dart:async';

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../app/routes.dart';
import '../../app/theme.dart';
import '../../core/network/api_exception.dart';
import '../../l10n/app_localizations.dart';
import '../auth/auth_controller.dart';
import '../auth/session.dart';
import '../grievance/grievance_data.dart';
import '../help/help_data.dart';
import '../help/voice.dart';
import '../language/app_language.dart';
import 'assistant_data.dart';

/// What the current screen says in one or two sentences, for "Read this screen" (null: nothing to read yet).
typedef ScreenSummary = String? Function(BuildContext context, WidgetRef ref);

/// The AI button: opens the assistant for the current screen.
class AiButton extends StatelessWidget {
  const AiButton({super.key, required this.screen, this.summary});

  /// Where the person is, so the assistant understands "this" (e.g. home, complaint_form).
  final String screen;
  final ScreenSummary? summary;

  @override
  Widget build(BuildContext context) {
    final l = AppLocalizations.of(context);
    return FloatingActionButton.extended(
      heroTag: 'ai-button',
      icon: const Icon(Icons.auto_awesome),
      label: Text(l.aiButton, style: const TextStyle(fontSize: 17, fontWeight: FontWeight.w700)),
      onPressed: () => showModalBottomSheet<void>(
        context: context,
        isScrollControlled: true,
        showDragHandle: true,
        builder: (_) => AssistantSheet(screen: screen, summary: summary),
      ),
    );
  }
}

/// "How can I help you?": speak or type, or tap a quick action. One request gives one action, checked by the
/// backend for the person's role; forms open pre-filled for review and are never sent from here.
class AssistantSheet extends ConsumerStatefulWidget {
  const AssistantSheet({super.key, required this.screen, this.summary});

  final String screen;
  final ScreenSummary? summary;

  @override
  ConsumerState<AssistantSheet> createState() => _AssistantSheetState();
}

class _AssistantSheetState extends ConsumerState<AssistantSheet> {
  final _input = TextEditingController();
  bool _busy = false;
  bool _listening = false;
  bool _reading = false;

  /// What to show under the input: an answer, the screen's summary, or a problem.
  HelpReply? _answer;
  String? _note;
  bool _noteIsError = false;

  /// "Language changed", worded when the sheet is redrawn so it appears in the new language.
  bool _languageChanged = false;
  late final VoiceInput _voice = ref.read(voiceInputProvider);
  late final Speaker _speaker = ref.read(speakerProvider);

  String get _language => Localizations.localeOf(context).languageCode;

  @override
  void dispose() {
    if (_listening) _voice.stop();
    if (_reading) _speaker.stop();
    _input.dispose();
    super.dispose();
  }

  void _show({HelpReply? answer, String? note, bool error = false, bool languageChanged = false}) => setState(() {
        _answer = answer;
        _note = note;
        _noteIsError = error;
        _languageChanged = languageChanged;
      });

  Future<void> _ask() async {
    final text = _input.text.trim();
    if (text.isEmpty || _busy) return;
    final l = AppLocalizations.of(context);
    if (_reading) await _stopReading();
    setState(() => _busy = true);
    _show();
    try {
      final action = await ref.read(assistantRepositoryProvider).understand(text, _language, screen: widget.screen);
      if (mounted) await _carryOut(action);
    } on ApiException catch (e) {
      if (mounted) _show(note: e.messageIn(l), error: true);
    } finally {
      if (mounted) setState(() => _busy = false);
    }
  }

  Future<void> _carryOut(AssistantAction action) async {
    final l = AppLocalizations.of(context);
    final user = ref.read(authControllerProvider);
    switch (action) {
      case OpenScreen(:final screen):
        final route = user == null ? null : routeForAssistantScreen(screen, user.role);
        if (route != null) _leaveFor(route);
      case FillForm(:final form, :final fields) when form == 'grievance':
        _leaveFor(Routes.citizenComplaint, extra: ComplaintDraft.fromAssistantFields(fields));
      case FillForm():
        break;
      case ChangeLanguage(:final language):
        final chosen = AppLanguage.values.where((a) => a.name == language).firstOrNull;
        if (chosen != null) await ref.read(languageProvider.notifier).choose(chosen);
        if (mounted) _show(languageChanged: true);
      case ReadScreen():
        final summary = widget.summary?.call(context, ref);
        if (summary == null) {
          _show(note: l.aiNothingToRead);
        } else {
          _show(note: summary);
          unawaited(_readAloud(summary));
        }
      case Answer(:final reply):
        _show(answer: reply);
    }
  }

  /// Closes the assistant and opens [route] (the sheet's own context is gone afterwards).
  void _leaveFor(String route, {Object? extra}) {
    final router = GoRouter.of(context);
    Navigator.of(context).pop();
    router.push(route, extra: extra);
  }

  Future<void> _toggleMic() async {
    final l = AppLocalizations.of(context);
    if (_listening) {
      await _voice.stop();
      return;
    }
    if (_reading) await _stopReading();
    if (!mounted) return;
    var heard = false;
    final started = await _voice.start(
      language: _language,
      onWords: (words, done) {
        if (!mounted) return;
        heard = heard || words.trim().isNotEmpty;
        _input.text = words;
        if (done && words.trim().isNotEmpty) _ask();
      },
      onStopped: () {
        if (!mounted) return;
        setState(() => _listening = false);
        if (!heard) _show(note: l.noSpeechHeard, error: true);
      },
    );
    if (!mounted) return;
    if (!started) {
      _show(note: l.voiceUnavailable, error: true);
      return;
    }
    setState(() => _listening = true);
  }

  Future<void> _readAloud(String text) async {
    final l = AppLocalizations.of(context);
    setState(() => _reading = true);
    final spoken = await _speaker.speak(text, _language);
    if (!mounted) return;
    setState(() => _reading = false);
    if (!spoken) ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(l.voiceMissing)));
  }

  Future<void> _stopReading() async {
    await _speaker.stop();
    if (mounted) setState(() => _reading = false);
  }

  @override
  Widget build(BuildContext context) {
    final l = AppLocalizations.of(context);
    final role = ref.watch(authControllerProvider)?.role;
    return Padding(
      // Keeps the input above the keyboard.
      padding: EdgeInsets.fromLTRB(20, 0, 20, 16 + MediaQuery.viewInsetsOf(context).bottom),
      child: SingleChildScrollView(
        child: Column(mainAxisSize: MainAxisSize.min, crossAxisAlignment: CrossAxisAlignment.stretch, children: [
          Row(children: [
            const Icon(Icons.auto_awesome, color: AppColors.blue, size: 28),
            const SizedBox(width: 10),
            Expanded(
              child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                Text(l.appTitle, style: const TextStyle(color: AppColors.muted, fontWeight: FontWeight.w600)),
                Text(l.aiHowCanIHelp, style: Theme.of(context).textTheme.titleLarge?.copyWith(fontWeight: FontWeight.w800)),
              ]),
            ),
          ]),
          const SizedBox(height: 16),
          Center(
            child: Semantics(
              button: true,
              label: _listening ? l.stopListening : l.speakQuestion,
              excludeSemantics: true,
              child: InkWell(
                customBorder: const CircleBorder(),
                onTap: _busy ? null : _toggleMic,
                child: Ink(
                  width: 88,
                  height: 88,
                  decoration: BoxDecoration(shape: BoxShape.circle, color: _listening ? AppColors.danger : AppColors.blue),
                  child: Icon(_listening ? Icons.stop : Icons.mic, color: Colors.white, size: 44),
                ),
              ),
            ),
          ),
          const SizedBox(height: 6),
          Text(_listening ? l.listening : l.speakQuestion,
              textAlign: TextAlign.center,
              style: TextStyle(fontWeight: FontWeight.w700, color: _listening ? AppColors.danger : AppColors.ink)),
          const SizedBox(height: 12),
          Row(children: [
            Expanded(
              child: TextField(
                controller: _input,
                maxLength: helpMessageMaxLength,
                minLines: 1,
                maxLines: 3,
                textInputAction: TextInputAction.send,
                decoration: InputDecoration(hintText: l.aiTypeHint, counterText: ''),
                onSubmitted: (_) => _ask(),
              ),
            ),
            const SizedBox(width: 6),
            IconButton.filled(iconSize: 26, tooltip: l.sendQuestion, icon: const Icon(Icons.send), onPressed: _busy ? null : _ask),
          ]),
          const SizedBox(height: 6),
          Text(l.aiExample, style: const TextStyle(fontSize: 13, color: AppColors.muted)),
          const SizedBox(height: 12),
          if (_busy)
            Row(children: [
              const SizedBox.square(dimension: 18, child: CircularProgressIndicator(strokeWidth: 2)),
              const SizedBox(width: 10),
              Text(l.thinking, style: const TextStyle(color: AppColors.muted)),
            ])
          else if (_answer != null)
            _AnswerCard(
              reply: _answer!,
              reading: _reading,
              onRead: () => _reading ? _stopReading() : _readAloud([?_answer!.title, _answer!.text].join('\n')),
              onLink: (route) => _leaveFor(route),
            )
          else if (_note != null || _languageChanged)
            Semantics(
              liveRegion: true,
              child: Card(
                color: _noteIsError ? AppColors.dangerSoft : const Color(0xFFE7F1FF),
                child: Padding(
                  padding: const EdgeInsets.all(14),
                  child: Text(_languageChanged ? l.aiLanguageChanged : _note!,
                      style: TextStyle(fontSize: 16, fontWeight: FontWeight.w600, color: _noteIsError ? AppColors.danger : AppColors.ink)),
                ),
              ),
            ),
          const SizedBox(height: 12),
          Wrap(spacing: 8, runSpacing: 8, children: [
            if (widget.summary != null)
              ActionChip(
                avatar: Icon(_reading ? Icons.stop_circle_outlined : Icons.volume_up_outlined, size: 20),
                label: Text(_reading ? l.stopReading : l.aiReadScreen),
                onPressed: () => _reading ? _stopReading() : _carryOut(const ReadScreen(explain: false)),
              ),
            for (final (icon, label, route) in _quickActions(l, role))
              ActionChip(avatar: Icon(icon, size: 20), label: Text(label), onPressed: () => _leaveFor(route)),
          ]),
        ]),
      ),
    );
  }
}

/// One tap to the most common places for each role (no AI needed).
List<(IconData, String, String)> _quickActions(AppLocalizations l, AppRole? role) => switch (role) {
      AppRole.ruralUser => [
          (Icons.confirmation_number_outlined, l.myToken, Routes.citizenTokens),
          (Icons.report_problem_outlined, l.complaintTitle, Routes.citizenComplaint),
          (Icons.list_alt, l.myComplaints, Routes.citizenComplaints),
          (Icons.event_available, l.bookRation, Routes.citizenBook),
          (Icons.translate, l.language, Routes.changeLanguage),
        ],
      AppRole.shopOwner => [
          (Icons.qr_code_scanner, l.scanCustomerQr, Routes.shopScan),
          (Icons.people_outline, l.queueButton, Routes.shopQueue),
          (Icons.inventory_2_outlined, l.stockButton, Routes.shopStock),
          (Icons.translate, l.language, Routes.changeLanguage),
        ],
      AppRole.governmentOfficial || AppRole.admin => [
          (Icons.storefront, l.statShops, Routes.officialShops),
          (Icons.notification_important_outlined, l.alertsTitle, Routes.officialAlerts),
          (Icons.translate, l.language, Routes.changeLanguage),
        ],
      null => [],
    };

class _AnswerCard extends StatelessWidget {
  const _AnswerCard({required this.reply, required this.reading, required this.onRead, required this.onLink});

  final HelpReply reply;
  final bool reading;
  final VoidCallback onRead;
  final ValueChanged<String> onLink;

  @override
  Widget build(BuildContext context) {
    final l = AppLocalizations.of(context);
    return Semantics(
      liveRegion: true,
      child: Card(
        child: Padding(
          padding: const EdgeInsets.all(14),
          child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
            if (reply.title != null) ...[
              Text(reply.title!, style: const TextStyle(fontSize: 17, fontWeight: FontWeight.w700)),
              const SizedBox(height: 6),
            ],
            Text(reply.text, style: const TextStyle(fontSize: 16, height: 1.35)),
            const SizedBox(height: 6),
            Wrap(spacing: 8, runSpacing: 4, children: [
              TextButton.icon(
                icon: Icon(reading ? Icons.stop_circle_outlined : Icons.volume_up_outlined),
                label: Text(reading ? l.stopReading : l.readAloud),
                onPressed: onRead,
              ),
              for (final link in reply.links)
                FilledButton.tonalIcon(icon: const Icon(Icons.open_in_new), label: Text(link.label), onPressed: () => onLink(link.route)),
            ]),
          ]),
        ),
      ),
    );
  }
}
