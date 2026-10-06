import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../app/routes.dart';
import '../../core/network/api_client.dart';
import '../../core/network/api_exception.dart';
import '../../core/providers.dart';

/// The Public Help assistant ("Ration Mitra"), on the existing backend routes (no sign-in needed):
///   GET  /api/chatbot/welcome?language=     greeting and quick-topic buttons
///   POST /api/chatbot/message               a typed question, a quick topic or a related article
///   GET  /api/public-help/categories        the help page's sections and their articles
///   GET  /api/public-help/search?q=         search the help articles
///   GET  /api/public-help/articles/{id}     one article
/// The backend answers in en / hi / mr, never logs the message text, and refuses Aadhaar numbers,
/// OTPs and passwords. A signed-in citizen's token is sent as usual, so "my booking" gets their own
/// bookings. Nothing of the conversation is stored on the phone.

/// A quick-topic button, e.g. "Documents".
class HelpTopic {
  const HelpTopic({required this.id, required this.label});

  final String id;
  final String label;
}

/// A button that opens a screen of this app, e.g. "Book a slot".
class HelpLink {
  const HelpLink({required this.route, required this.label});

  final String route;
  final String label;
}

class HelpRelated {
  const HelpRelated({required this.articleId, required this.title});

  final String articleId;
  final String title;
}

class HelpReply {
  const HelpReply({required this.kind, required this.text, this.title, this.links = const [], this.topics = const [], this.related = const []});

  /// answer, fallback, welcome, personal, sensitive_input, ... (the backend's words).
  final String kind;
  final String text;
  final String? title;
  final List<HelpLink> links;
  final List<HelpTopic> topics;
  final List<HelpRelated> related;

  static HelpReply parse(Object? j) {
    if (j is! Map || j['text'] is! String) throw const ApiException(ApiErrorKind.unknown);
    List<Map> maps(Object? v) => (v as List? ?? const []).whereType<Map>().toList();
    final title = j['title'];
    return HelpReply(
      kind: '${j['kind'] ?? ''}',
      text: j['text'] as String,
      title: title is String && title.isNotEmpty ? title : null,
      links: [
        for (final l in maps(j['links']))
          if (appRouteForHelpLink('${l['path']}') case final route?) HelpLink(route: route, label: '${l['label'] ?? ''}'),
      ],
      topics: [
        for (final s in maps(j['suggestions']))
          if (s['topic'] is String) HelpTopic(id: s['topic'] as String, label: '${s['label'] ?? s['topic']}'),
      ],
      related: [
        for (final r in maps(j['related']))
          if (r['id'] is String) HelpRelated(articleId: r['id'] as String, title: '${r['title'] ?? ''}'),
      ],
    );
  }
}

/// The assistant writes website paths; this is the same place in the app. Unknown paths give null,
/// and their button is simply not shown.
String? appRouteForHelpLink(String path) {
  if (path == '/login') return Routes.login;
  if (path == '/rural/book') return Routes.citizenBook;
  if (path == '/rural/verification') return Routes.citizenCard;
  final token = RegExp(r'^/rural/token/(\d+)$').firstMatch(path);
  if (token != null) return Routes.citizenToken(int.parse(token.group(1)!));
  return null;
}

/// A section of the help page, e.g. "Booking and tokens", with its articles.
class HelpCategory {
  const HelpCategory({required this.id, required this.title, required this.description, required this.articles});

  final String id;
  final String title;
  final String description;
  final List<HelpRelated> articles;

  static HelpCategory? tryParse(Object? j) {
    if (j is! Map || j['id'] is! String) return null;
    return HelpCategory(
      id: j['id'] as String,
      title: '${j['title'] ?? ''}',
      description: '${j['description'] ?? ''}',
      articles: [
        for (final a in (j['articles'] as List? ?? const []).whereType<Map>())
          if (a['id'] is String) HelpRelated(articleId: a['id'] as String, title: '${a['title'] ?? ''}'),
      ],
    );
  }
}

/// A search hit: the article and the first line of its answer.
class HelpHit {
  const HelpHit({required this.articleId, required this.title, required this.excerpt});

  final String articleId;
  final String title;
  final String excerpt;

  static HelpHit? tryParse(Object? j) {
    if (j is! Map || j['id'] is! String) return null;
    return HelpHit(articleId: j['id'] as String, title: '${j['title'] ?? ''}', excerpt: '${j['excerpt'] ?? ''}');
  }
}

/// The backend's limit for one search.
const helpSearchMaxLength = 100;

/// The backend's limit for one question.
const helpMessageMaxLength = 500;

class HelpRepository {
  const HelpRepository(this._api);

  final ApiClient _api;

  Future<HelpReply> welcome(String language) async =>
      HelpReply.parse(await _api.get<Object?>('/api/chatbot/welcome', query: {'language': language}));

  /// Exactly one of [message], [topic] or [articleId].
  Future<HelpReply> ask(String language, {String? message, String? topic, String? articleId}) async =>
      HelpReply.parse(await _api.post<Object?>('/api/chatbot/message', body: {
        'language': language,
        'message': ?message,
        'topic': ?topic,
        'articleId': ?articleId,
      }));

  /// The help page's sections, in [language] (public, no sign-in).
  Future<List<HelpCategory>> categories(String language) async {
    final data = await _api.get<Object?>('/api/public-help/categories', query: {'language': language});
    return data is List ? [for (final e in data) ?HelpCategory.tryParse(e)] : (throw const ApiException(ApiErrorKind.unknown));
  }

  Future<List<HelpHit>> search(String query, String language) async {
    final data = await _api.get<Object?>('/api/public-help/search', query: {'q': query.trim(), 'language': language});
    return data is List ? [for (final e in data) ?HelpHit.tryParse(e)] : (throw const ApiException(ApiErrorKind.unknown));
  }

  /// One article, in the same shape as a chat answer (title, text, links, related articles).
  Future<HelpReply> article(String id, String language) async =>
      HelpReply.parse(await _api.get<Object?>('/api/public-help/articles/${Uri.encodeComponent(id)}', query: {'language': language}));
}

final helpRepositoryProvider = Provider<HelpRepository>((ref) => HelpRepository(ref.watch(apiClientProvider)));

final helpCategoriesProvider =
    FutureProvider.autoDispose.family<List<HelpCategory>, String>((ref, language) => ref.watch(helpRepositoryProvider).categories(language));

final helpSearchProvider = FutureProvider.autoDispose.family<List<HelpHit>, ({String query, String language})>(
    (ref, q) => ref.watch(helpRepositoryProvider).search(q.query, q.language));

final helpArticleProvider = FutureProvider.autoDispose.family<HelpReply, ({String id, String language})>(
    (ref, a) => ref.watch(helpRepositoryProvider).article(a.id, a.language));
