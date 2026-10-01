import 'package:dio/dio.dart';

import 'fake_backend.dart';

/// The Public Help assistant (same shapes as the real /api/chatbot answers).
FakeReply helpServer(RequestOptions r) {
  Map<String, Object?> reply(String kind, String text,
          {String? title, List<Object?> links = const [], List<Object?> suggestions = const [], List<Object?> related = const []}) =>
      {
        'kind': kind,
        'language': 'en',
        'text': text,
        'articleId': null,
        'title': title,
        'links': links,
        'suggestions': suggestions,
        'related': related,
        'requiresLogin': false,
        'confidence': 1.0,
      };
  if (r.path == '/api/chatbot/welcome') {
    return FakeReply.ok(reply('welcome', 'Namaste! 👋\nI am Ration Mitra (${r.queryParameters['language']}).',
        suggestions: [
          {'topic': 'documents', 'label': 'Documents', 'ask': 'Which documents?'},
        ]));
  }
  final body = (r.data as Map?) ?? const {};
  if (body['topic'] == 'documents') {
    return FakeReply.ok(reply('answer', '• Identity proof\n• Address proof', title: 'Documents usually required', related: [
      {'id': 'eligibility', 'title': 'Who is eligible'},
    ]));
  }
  if (body['articleId'] == 'eligibility') return FakeReply.ok(reply('answer', 'Eligible families ...', title: 'Who is eligible'));
  if ('${body['message']}'.contains('booking')) {
    return FakeReply.ok(reply('personal', 'You have no upcoming bookings.', links: [
      {'path': '/rural/book', 'label': 'Book a slot'},
      {'path': '/somewhere/unknown', 'label': 'Unknown page'},
    ]));
  }
  return FakeReply.ok(reply('fallback', 'Sorry, I am not able to verify that information.'));
}

/// Help questions go to the assistant; everything else to the demo citizen's backend.
FakeReply helpOrDemo(RequestOptions r) => r.path.startsWith('/api/chatbot') ? helpServer(r) : demoServer(r);
