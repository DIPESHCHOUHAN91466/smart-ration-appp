import 'dart:convert';
import 'dart:typed_data';

import 'package:dio/dio.dart';

/// Stands in for the real backend in tests: answers each request from [handler] and remembers
/// what the app sent.
class FakeBackend implements HttpClientAdapter {
  FakeBackend(this.handler);

  final FakeReply Function(RequestOptions request) handler;
  final List<RequestOptions> requests = [];

  @override
  Future<ResponseBody> fetch(RequestOptions options, Stream<Uint8List>? requestStream, Future<void>? cancelFuture) async {
    requests.add(options);
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
}
