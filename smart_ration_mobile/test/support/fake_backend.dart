import 'dart:convert';
import 'dart:typed_data';

import 'package:dio/dio.dart';

/// Stands in for the real backend in tests: answers each request from [handler] and remembers
/// what the app sent. [delay] makes every answer slow, to test requests that overlap.
class FakeBackend implements HttpClientAdapter {
  FakeBackend(this.handler, {this.delay = Duration.zero});

  final FakeReply Function(RequestOptions request) handler;
  final Duration delay;
  final List<RequestOptions> requests = [];

  List<String> get paths => requests.map((r) => r.path).toList();

  @override
  Future<ResponseBody> fetch(RequestOptions options, Stream<Uint8List>? requestStream, Future<void>? cancelFuture) async {
    requests.add(options);
    if (delay > Duration.zero) await Future<void>.delayed(delay);
    final reply = handler(options);
    if (reply.error != null) {
      throw DioException(requestOptions: options, type: reply.error!);
    }
    return ResponseBody.fromString(
      jsonEncode(reply.body),
      reply.status,
      headers: {
        Headers.contentTypeHeader: [Headers.jsonContentType],
      },
    );
  }

  @override
  void close({bool force = false}) {}
}

class FakeReply {
  const FakeReply(this.status, this.body) : error = null;
  const FakeReply.fails(DioExceptionType this.error)
      : status = 0,
        body = null;

  final int status;
  final Object? body;
  final DioExceptionType? error;

  /// The backend's success envelope around [data].
  static FakeReply ok(Object? data) => FakeReply(200, {'success': true, 'message': 'Success', 'data': data, 'errors': null});

  /// The backend's failure envelope.
  static FakeReply fail(int status, String message) =>
      FakeReply(status, {'success': false, 'message': message, 'data': null, 'errors': null});
}

/// The `user` part of a sign-in answer, as the backend sends it.
Map<String, Object?> userJson({
  int id = 7,
  String fullName = 'Asha Devi',
  String role = 'RuralUser',
  int? rationShopId,
}) =>
    {
      'id': id,
      'fullName': fullName,
      'email': 'asha@example.com',
      'mobileNumber': '9800000007',
      'role': role,
      'rationShopId': rationShopId,
    };

/// A full sign-in / refresh answer.
FakeReply signedIn({String access = 'access-1', String refresh = 'refresh-1', Map<String, Object?>? user}) => FakeReply.ok({
      'accessToken': access,
      'refreshToken': refresh,
      'accessTokenExpiresAt': '2026-10-01T10:15:00Z',
      'user': user ?? userJson(),
    });
