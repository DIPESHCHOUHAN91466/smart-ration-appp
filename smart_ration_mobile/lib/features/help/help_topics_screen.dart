import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../app/routes.dart';
import '../../app/theme.dart';
import '../../core/network/api_exception.dart';
import '../../l10n/app_localizations.dart';
import 'help_data.dart';
import 'voice.dart';

/// The website's Public Help page: search, then the sections with their articles. Open to everyone.
/// Anything not found here can be asked in the help chat.
class HelpTopicsScreen extends ConsumerStatefulWidget {
  const HelpTopicsScreen({super.key});

  @override
  ConsumerState<HelpTopicsScreen> createState() => _HelpTopicsScreenState();
}

class _HelpTopicsScreenState extends ConsumerState<HelpTopicsScreen> {
  final _search = TextEditingController();

  /// The search that was sent (null = show the sections).
  String? _query;

  @override
  void dispose() {
    _search.dispose();
    super.dispose();
  }

  void _submit() {
    final q = _search.text.trim();
    setState(() => _query = q.isEmpty ? null : q);
  }

  @override
  Widget build(BuildContext context) {
    final l = AppLocalizations.of(context);
    final language = Localizations.localeOf(context).languageCode;
    return Scaffold(
      appBar: AppBar(title: Text(l.helpTopicsTitle)),
      body: ListView(
        padding: const EdgeInsets.all(16),
        children: [
          TextField(
            controller: _search,
            maxLength: helpSearchMaxLength,
            textInputAction: TextInputAction.search,
            onSubmitted: (_) => _submit(),
            decoration: InputDecoration(
              labelText: l.helpSearchLabel,
              counterText: '',
              prefixIcon: const Icon(Icons.search),
              suffixIcon: _query == null
                  ? IconButton(icon: const Icon(Icons.arrow_forward), tooltip: l.helpSearchLabel, onPressed: _submit)
                  : IconButton(
                      icon: const Icon(Icons.close),
                      tooltip: l.cancelButton,
                      onPressed: () {
                        _search.clear();
                        setState(() => _query = null);
                      },
                    ),
            ),
          ),
          const SizedBox(height: 8),
          Text(l.helpPrivacy, style: const TextStyle(color: AppColors.muted)),
          const SizedBox(height: 12),
          ...(_query == null ? _sections(context, l, language) : _results(context, l, language, _query!)),
          const SizedBox(height: 16),
          OutlinedButton.icon(
            icon: const Icon(Icons.chat_outlined),
            label: Text(l.helpAskAssistant),
            onPressed: () => context.push(Routes.help),
          ),
        ],
      ),
    );
  }

  List<Widget> _sections(BuildContext context, AppLocalizations l, String language) {
    final categories = ref.watch(helpCategoriesProvider(language));
    return categories.when(
      loading: () => [const SizedBox(height: 40), const Center(child: CircularProgressIndicator())],
      error: (e, _) => [
        Text(e is ApiException ? e.messageIn(l) : l.errorGeneric, textAlign: TextAlign.center),
        TextButton(onPressed: () => ref.invalidate(helpCategoriesProvider(language)), child: Text(l.tryAgain)),
      ],
      data: (all) => [
        for (final c in all)
          Card(
            margin: const EdgeInsets.only(bottom: 10),
            clipBehavior: Clip.antiAlias,
            child: ExpansionTile(
              title: Text(c.title, style: const TextStyle(fontSize: 16, fontWeight: FontWeight.w700)),
              subtitle: Text('${c.description}\n${l.helpArticleCount(c.articles.length)}'),
              children: [
                for (final a in c.articles)
                  ListTile(
                    title: Text(a.title),
                    trailing: const Icon(Icons.chevron_right),
                    onTap: () => context.push(Routes.helpArticle(a.articleId)),
                  ),
              ],
            ),
          ),
      ],
    );
  }

  List<Widget> _results(BuildContext context, AppLocalizations l, String language, String query) {
    final results = ref.watch(helpSearchProvider((query: query, language: language)));
    return [
      Semantics(header: true, child: Text(l.helpResultsFor(query), style: const TextStyle(fontSize: 17, fontWeight: FontWeight.w700))),
      const SizedBox(height: 8),
      ...results.when(
        loading: () => [const SizedBox(height: 40), const Center(child: CircularProgressIndicator())],
        error: (e, _) => [Text(e is ApiException ? e.messageIn(l) : l.errorGeneric)],
        data: (hits) => hits.isEmpty
            ? [Semantics(liveRegion: true, child: Text(l.helpNoResults, style: Theme.of(context).textTheme.titleMedium))]
            : [
                for (final h in hits)
                  Card(
                    margin: const EdgeInsets.only(bottom: 8),
                    child: ListTile(
                      title: Text(h.title, style: const TextStyle(fontWeight: FontWeight.w700)),
                      subtitle: h.excerpt.isEmpty ? null : Text(h.excerpt, maxLines: 3, overflow: TextOverflow.ellipsis),
                      trailing: const Icon(Icons.chevron_right),
                      onTap: () => context.push(Routes.helpArticle(h.articleId)),
                    ),
                  ),
              ],
      ),
    ];
  }
}

/// One help article, with "read aloud", buttons into the app where the article points to one, and related articles.
class HelpArticleScreen extends ConsumerStatefulWidget {
  const HelpArticleScreen({super.key, required this.articleId});

  final String articleId;

  @override
  ConsumerState<HelpArticleScreen> createState() => _HelpArticleScreenState();
}

class _HelpArticleScreenState extends ConsumerState<HelpArticleScreen> {
  late final Speaker _speaker = ref.read(speakerProvider);
  bool _reading = false;

  @override
  void dispose() {
    if (_reading) _speaker.stop();
    super.dispose();
  }

  Future<void> _readAloud(HelpReply article, String language) async {
    if (_reading) {
      await _speaker.stop();
      if (mounted) setState(() => _reading = false);
      return;
    }
    setState(() => _reading = true);
    await _speaker.speak(speakable([article.title, article.text].whereType<String>().join('. ')), language);
    if (mounted) setState(() => _reading = false);
  }

  @override
  Widget build(BuildContext context) {
    final l = AppLocalizations.of(context);
    final language = Localizations.localeOf(context).languageCode;
    final key = (id: widget.articleId, language: language);
    final article = ref.watch(helpArticleProvider(key));
    return Scaffold(
      appBar: AppBar(title: Text(l.helpTopicsTitle)),
      body: ListView(
        padding: const EdgeInsets.all(16),
        children: article.when(
          loading: () => [const SizedBox(height: 80), const Center(child: CircularProgressIndicator())],
          error: (e, _) => [
            Text(e is ApiException ? e.messageIn(l) : l.errorGeneric, textAlign: TextAlign.center),
            TextButton(onPressed: () => ref.invalidate(helpArticleProvider(key)), child: Text(l.tryAgain)),
          ],
          data: (a) => [
            if (a.title != null)
              Semantics(header: true, child: Text(a.title!, style: Theme.of(context).textTheme.headlineSmall?.copyWith(fontWeight: FontWeight.w700))),
            const SizedBox(height: 10),
            Text(a.text, style: const TextStyle(fontSize: 17, height: 1.4)),
            const SizedBox(height: 8),
            Align(
              alignment: AlignmentDirectional.centerStart,
              child: TextButton.icon(
                icon: Icon(_reading ? Icons.stop_circle_outlined : Icons.volume_up_outlined),
                label: Text(_reading ? l.stopReading : l.readAloud),
                onPressed: () => _readAloud(a, language),
              ),
            ),
            for (final link in a.links)
              Padding(
                padding: const EdgeInsets.only(top: 6),
                child: FilledButton.tonalIcon(
                  icon: const Icon(Icons.open_in_new),
                  label: Text(link.label),
                  onPressed: () => context.push(link.route),
                ),
              ),
            if (a.related.isNotEmpty) ...[
              const SizedBox(height: 16),
              Text(l.relatedTitle, style: const TextStyle(color: AppColors.muted, fontWeight: FontWeight.w600)),
              for (final r in a.related)
                ListTile(
                  contentPadding: EdgeInsets.zero,
                  title: Text(r.title),
                  trailing: const Icon(Icons.chevron_right),
                  onTap: () => context.push(Routes.helpArticle(r.articleId)),
                ),
            ],
            const SizedBox(height: 16),
            OutlinedButton.icon(
              icon: const Icon(Icons.chat_outlined),
              label: Text(l.helpAskAssistant),
              onPressed: () => context.push(Routes.help),
            ),
          ],
        ),
      ),
    );
  }
}
