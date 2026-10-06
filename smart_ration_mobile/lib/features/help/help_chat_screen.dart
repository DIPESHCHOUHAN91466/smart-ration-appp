import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../app/routes.dart';
import '../../app/theme.dart';
import '../../core/network/api_exception.dart';
import '../../l10n/app_localizations.dart';
import 'help_data.dart';
import 'voice.dart';

/// One line of the conversation: the person's question, an answer, or a problem reaching the assistant.
sealed class _Entry {
  const _Entry();
}

class _Asked extends _Entry {
  const _Asked(this.text);
  final String text;
}

class _Answered extends _Entry {
  const _Answered(this.reply);
  final HelpReply reply;
}

class _Failed extends _Entry {
  const _Failed(this.message);
  final String message;
}

/// Chat with the Public Help assistant, by typing or by voice, with answers read aloud on request.
/// The conversation lives only in this screen: closing it forgets everything.
class HelpChatScreen extends ConsumerStatefulWidget {
  const HelpChatScreen({super.key});

  @override
  ConsumerState<HelpChatScreen> createState() => _HelpChatScreenState();
}

class _HelpChatScreenState extends ConsumerState<HelpChatScreen> {
  final _entries = <_Entry>[];
  final _input = TextEditingController();
  final _scroll = ScrollController();
  bool _busy = false;
  bool _listening = false;

  /// Which answer is being read aloud (index into [_entries]).
  int? _reading;
  late final VoiceInput _voice = ref.read(voiceInputProvider);
  late final Speaker _speaker = ref.read(speakerProvider);

  String get _language => Localizations.localeOf(context).languageCode;

  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addPostFrameCallback((_) => _run(() => ref.read(helpRepositoryProvider).welcome(_language)));
  }

  @override
  void dispose() {
    if (_listening) _voice.stop();
    if (_reading != null) _speaker.stop();
    _input.dispose();
    _scroll.dispose();
    super.dispose();
  }

  /// Shows [asked] as the person's line (if any), then the assistant's answer to [call].
  Future<void> _run(Future<HelpReply> Function() call, {String? asked}) async {
    final l = AppLocalizations.of(context);
    setState(() {
      if (asked != null) _entries.add(_Asked(asked));
      _busy = true;
    });
    _toBottom();
    _Entry result;
    try {
      result = _Answered(await call());
    } on ApiException catch (e) {
      result = _Failed(e.messageIn(l));
    }
    if (!mounted) return;
    setState(() {
      _entries.add(result);
      _busy = false;
    });
    _toBottom();
  }

  void _send() {
    final text = _input.text.trim();
    if (text.isEmpty || _busy) return;
    _input.clear();
    _run(() => ref.read(helpRepositoryProvider).ask(_language, message: text), asked: text);
  }

  void _toBottom() => WidgetsBinding.instance.addPostFrameCallback((_) {
        if (_scroll.hasClients) {
          _scroll.animateTo(_scroll.position.maxScrollExtent, duration: const Duration(milliseconds: 250), curve: Curves.easeOut);
        }
      });

  Future<void> _toggleMic() async {
    final l = AppLocalizations.of(context);
    if (_listening) {
      await _voice.stop();
      return;
    }
    if (_reading != null) await _speaker.stop();
    if (!mounted) return;
    final messenger = ScaffoldMessenger.of(context);
    var heard = false;
    final started = await _voice.start(
      language: _language,
      onWords: (words, done) {
        if (!mounted) return;
        heard = heard || words.trim().isNotEmpty;
        _input.text = words;
        // A finished sentence is sent straight away, so nobody has to read or type.
        if (done && words.trim().isNotEmpty) _send();
      },
      onStopped: () {
        if (!mounted) return;
        setState(() => _listening = false);
        // Silence or noise: say so, otherwise the button just seems not to work.
        if (!heard) messenger.showSnackBar(SnackBar(content: Text(l.noSpeechHeard)));
      },
    );
    if (!mounted) return;
    if (!started) {
      ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(l.voiceUnavailable)));
      return;
    }
    setState(() => _listening = true);
  }

  Future<void> _readAloud(int index, HelpReply reply) async {
    final l = AppLocalizations.of(context);
    final messenger = ScaffoldMessenger.of(context);
    if (_reading == index) {
      await _speaker.stop();
      if (mounted) setState(() => _reading = null);
      return;
    }
    setState(() => _reading = index);
    final spoken = await _speaker.speak([?reply.title, reply.text].join('\n'), _language);
    if (!mounted) return;
    if (!spoken) messenger.showSnackBar(SnackBar(content: Text(l.voiceMissing)));
    // Reading has ended (or another answer took over).
    if (_reading == index) setState(() => _reading = null);
  }

  @override
  Widget build(BuildContext context) {
    final l = AppLocalizations.of(context);
    final lastAnswer = _entries.lastOrNull is _Answered ? _entries.length - 1 : null;
    return Scaffold(
      appBar: AppBar(title: Text(l.helpTitle), actions: [
        IconButton(
          icon: const Icon(Icons.menu_book_outlined),
          tooltip: l.helpTopicsTitle,
          iconSize: 28,
          onPressed: () => context.push(Routes.helpTopics),
        ),
      ]),
      body: Column(children: [
        Container(
          width: double.infinity,
          color: AppColors.warningSoft,
          padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 10),
          child: Row(children: [
            const Icon(Icons.lock_outline, size: 20, color: AppColors.warning),
            const SizedBox(width: 8),
            Expanded(child: Text(l.helpPrivacy, style: const TextStyle(fontSize: 14))),
          ]),
        ),
        Expanded(
          child: ListView.builder(
            controller: _scroll,
            padding: const EdgeInsets.all(12),
            itemCount: _entries.length + (_busy ? 1 : 0),
            itemBuilder: (context, i) {
              if (i == _entries.length) return _Thinking(text: l.thinking);
              return switch (_entries[i]) {
                _Asked(:final text) => _Bubble(mine: true, label: l.youLabel, child: Text(text, style: const TextStyle(fontSize: 16))),
                _Failed(:final message) => _Bubble(
                    mine: false,
                    label: l.assistantName,
                    child: Text(message, style: const TextStyle(fontSize: 16, color: AppColors.danger)),
                  ),
                _Answered(:final reply) => _AnswerBubble(
                    reply: reply,
                    reading: _reading == i,
                    onReadAloud: () => _readAloud(i, reply),
                    // Quick topics and related articles only under the latest answer.
                    showChoices: i == lastAnswer && !_busy,
                    onTopic: (t) => _run(() => ref.read(helpRepositoryProvider).ask(_language, topic: t.id), asked: t.label),
                    onRelated: (r) => _run(() => ref.read(helpRepositoryProvider).ask(_language, articleId: r.articleId), asked: r.title),
                  ),
              };
            },
          ),
        ),
        if (_listening)
          Semantics(
            liveRegion: true,
            child: Padding(
              padding: const EdgeInsets.only(top: 4),
              child: Text(l.listening, style: const TextStyle(color: AppColors.danger, fontWeight: FontWeight.w700)),
            ),
          ),
        SafeArea(
          top: false,
          child: Padding(
            padding: const EdgeInsets.fromLTRB(8, 6, 8, 8),
            child: Column(mainAxisSize: MainAxisSize.min, children: [
              Row(children: [
                IconButton.filledTonal(
                  iconSize: 28,
                  tooltip: _listening ? l.stopListening : l.speakQuestion,
                  style: _listening ? IconButton.styleFrom(backgroundColor: AppColors.dangerSoft, foregroundColor: AppColors.danger) : null,
                  icon: Icon(_listening ? Icons.stop : Icons.mic),
                  onPressed: _toggleMic,
                ),
                const SizedBox(width: 6),
                Expanded(
                  child: TextField(
                    controller: _input,
                    maxLength: helpMessageMaxLength,
                    minLines: 1,
                    maxLines: 4,
                    textInputAction: TextInputAction.send,
                    decoration: InputDecoration(hintText: l.askHint, counterText: ''),
                    onSubmitted: (_) => _send(),
                  ),
                ),
                const SizedBox(width: 6),
                IconButton.filled(iconSize: 26, tooltip: l.sendQuestion, icon: const Icon(Icons.send), onPressed: _busy ? null : _send),
              ]),
              Text(l.voiceNote, textAlign: TextAlign.center, style: const TextStyle(fontSize: 12, color: AppColors.muted)),
            ]),
          ),
        ),
      ]),
    );
  }
}

class _Bubble extends StatelessWidget {
  const _Bubble({required this.mine, required this.label, required this.child});

  final bool mine;

  /// Who is speaking, for screen readers ("You", "Ration Mitra").
  final String label;
  final Widget child;

  @override
  Widget build(BuildContext context) => Align(
        alignment: mine ? AlignmentDirectional.centerEnd : AlignmentDirectional.centerStart,
        child: ConstrainedBox(
          constraints: BoxConstraints(maxWidth: MediaQuery.sizeOf(context).width * 0.86),
          child: Semantics(
            container: true,
            label: label,
            child: Container(
              margin: const EdgeInsets.symmetric(vertical: 5),
              padding: const EdgeInsets.all(14),
              decoration: BoxDecoration(
                color: mine ? const Color(0xFFE7F1FF) : Colors.white,
                border: Border.all(color: AppColors.border),
                borderRadius: BorderRadius.circular(16),
              ),
              child: child,
            ),
          ),
        ),
      );
}

class _AnswerBubble extends StatelessWidget {
  const _AnswerBubble({
    required this.reply,
    required this.reading,
    required this.onReadAloud,
    required this.showChoices,
    required this.onTopic,
    required this.onRelated,
  });

  final HelpReply reply;
  final bool reading;
  final VoidCallback onReadAloud;
  final bool showChoices;
  final ValueChanged<HelpTopic> onTopic;
  final ValueChanged<HelpRelated> onRelated;

  @override
  Widget build(BuildContext context) {
    final l = AppLocalizations.of(context);
    return _Bubble(
      mine: false,
      label: l.assistantName,
      child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
        if (reply.title != null) ...[
          Text(reply.title!, style: const TextStyle(fontSize: 17, fontWeight: FontWeight.w700)),
          const SizedBox(height: 6),
        ],
        Text(reply.text, style: const TextStyle(fontSize: 16, height: 1.35)),
        const SizedBox(height: 6),
        Align(
          alignment: AlignmentDirectional.centerStart,
          child: TextButton.icon(
            icon: Icon(reading ? Icons.stop_circle_outlined : Icons.volume_up_outlined),
            label: Text(reading ? l.stopReading : l.readAloud),
            onPressed: onReadAloud,
          ),
        ),
        for (final link in reply.links)
          Padding(
            padding: const EdgeInsets.only(top: 4),
            child: FilledButton.tonalIcon(
              icon: const Icon(Icons.open_in_new),
              label: Text(link.label),
              onPressed: () => context.push(link.route),
            ),
          ),
        if (showChoices && reply.related.isNotEmpty) ...[
          const SizedBox(height: 8),
          Text(l.relatedTitle, style: const TextStyle(color: AppColors.muted, fontWeight: FontWeight.w600)),
          Wrap(spacing: 8, runSpacing: 4, children: [
            for (final r in reply.related) ActionChip(label: Text(r.title), onPressed: () => onRelated(r)),
          ]),
        ],
        if (showChoices && reply.topics.isNotEmpty) ...[
          const SizedBox(height: 8),
          Wrap(spacing: 8, runSpacing: 4, children: [
            for (final t in reply.topics) ActionChip(label: Text(t.label), onPressed: () => onTopic(t)),
          ]),
        ],
      ]),
    );
  }
}

class _Thinking extends StatelessWidget {
  const _Thinking({required this.text});

  final String text;

  @override
  Widget build(BuildContext context) => Padding(
        padding: const EdgeInsets.all(8),
        child: Row(children: [
          const SizedBox.square(dimension: 18, child: CircularProgressIndicator(strokeWidth: 2)),
          const SizedBox(width: 10),
          Text(text, style: const TextStyle(color: AppColors.muted)),
        ]),
      );
}
