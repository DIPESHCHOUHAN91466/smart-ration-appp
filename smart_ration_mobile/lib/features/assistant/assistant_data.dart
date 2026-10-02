import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../app/routes.dart';
import '../../core/network/api_client.dart';
import '../../core/network/api_exception.dart';
import '../../core/providers.dart';
import '../auth/session.dart';
import '../help/help_data.dart';

/// The AI assistant behind the AI button, on POST /api/assistant/understand (signed in).
/// The backend turns what the person said into ONE action it has checked for their role: open a screen,
/// pre-fill a form, change the language, read or explain the current screen, or an answer (from the person's
/// own bookings or the verified help pages). The phone carries it out; forms are never sent without review.

sealed class AssistantAction {
  const AssistantAction();

  static AssistantAction parse(Object? j) {
    if (j is! Map) throw const ApiException(ApiErrorKind.unknown);
    final target = j['target'];
    return switch (j['action']) {
      'navigate' when target is String => OpenScreen(target),
      'fill_form' when j['form'] is String =>
        FillForm(j['form'] as String, j['fields'] is Map ? j['fields'] as Map : const {}, [for (final m in (j['missing'] as List? ?? const [])) '$m']),
      'change_language' when target is String => ChangeLanguage(target),
      'read_screen' => const ReadScreen(explain: false),
      'explain_screen' => const ReadScreen(explain: true),
      'answer' => Answer(HelpReply.parse(j['reply']), intent: '${j['intent'] ?? ''}'),
      _ => throw const ApiException(ApiErrorKind.unknown),
    };
  }
}

class OpenScreen extends AssistantAction {
  const OpenScreen(this.screen);

  /// The backend's screen id, e.g. my_tokens (see [routeForAssistantScreen]).
  final String screen;
}

class FillForm extends AssistantAction {
  const FillForm(this.form, this.fields, this.missing);

  final String form;
  final Map<Object?, Object?> fields;
  final List<String> missing;
}

class ChangeLanguage extends AssistantAction {
  const ChangeLanguage(this.language);

  final String language;
}

class ReadScreen extends AssistantAction {
  const ReadScreen({required this.explain});

  final bool explain;
}

class Answer extends AssistantAction {
  const Answer(this.reply, {required this.intent});

  final HelpReply reply;

  /// collection_time, ask, sensitive, ...
  final String intent;
}

/// The app screen for the backend's screen id, or null if this app has none for the role (the backend has already
/// checked the role; this only maps names).
String? routeForAssistantScreen(String screen, AppRole role) => switch (screen) {
      'home' => Routes.homeFor(role),
      'help' => Routes.help,
      'notifications' => Routes.notifications,
      'my_tokens' => Routes.citizenTokens,
      'book' => Routes.citizenBook,
      'family' => Routes.citizenFamily,
      'ration_card' => Routes.citizenCard,
      'eligibility' => Routes.citizenEligibility,
      'my_complaints' => Routes.citizenComplaints,
      'scan' => Routes.shopScan,
      'queue' => Routes.shopQueue,
      'stock' => Routes.shopStock,
      'shops' => Routes.officialShops,
      'alerts' => Routes.officialAlerts,
      _ => null,
    };

class AssistantRepository {
  const AssistantRepository(this._api);

  final ApiClient _api;

  /// [screen] says where the person is (e.g. complaint_form), so "fill this in" means that form.
  Future<AssistantAction> understand(String text, String language, {String? screen}) async =>
      AssistantAction.parse(await _api.post<Object?>('/api/assistant/understand', body: {
        'text': text.trim(),
        'language': language,
        'screen': ?screen,
      }));
}

final assistantRepositoryProvider = Provider<AssistantRepository>((ref) => AssistantRepository(ref.watch(apiClientProvider)));
