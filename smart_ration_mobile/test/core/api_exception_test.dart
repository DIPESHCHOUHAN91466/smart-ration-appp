import 'package:dio/dio.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:smart_ration_mobile/core/network/api_exception.dart';

void main() {
  group('ApiException.fromResponse', () {
    final cases = {
      400: ApiErrorKind.badRequest,
      401: ApiErrorKind.unauthorized,
      403: ApiErrorKind.forbidden,
      404: ApiErrorKind.notFound,
      409: ApiErrorKind.conflict,
      422: ApiErrorKind.validation,
      429: ApiErrorKind.tooManyRequests,
      500: ApiErrorKind.server,
      502: ApiErrorKind.server,
    };
    cases.forEach((status, kind) {
      test('$status -> ${kind.name}', () {
        expect(ApiException.fromResponse(status, null).kind, kind);
      });
    });

    test('a server error never shows the backend wording', () {
      final e = ApiException.fromResponse(500, {'message': 'IntegrityError at line 42'});
      expect(e.serverMessage, isNull);
      expect(e.userMessage, 'The server had a problem. Please try again in a few minutes.');
    });

    test('an expired session asks the user to sign in again', () {
      expect(ApiException.fromResponse(401, {'message': 'Authentication required.'}).userMessage,
          'Your session has ended. Please sign in again.');
    });

    test('a forbidden action shows the backend reason', () {
      final e = ApiException.fromResponse(403, {'message': 'This token belongs to another ration shop.', 'errorCode': 'WRONG_SHOP'});
      expect(e.userMessage, 'This token belongs to another ration shop.');
      expect(e.errorCode, 'WRONG_SHOP');
    });

    test('a body without a message still gives a sentence', () {
      expect(ApiException.fromResponse(400, 'not json').userMessage, isNotEmpty);
    });
  });

  group('ApiException.fromDio', () {
    DioException dio(DioExceptionType type) => DioException(requestOptions: RequestOptions(path: '/x'), type: type);

    test('timeouts', () {
      for (final t in [DioExceptionType.connectionTimeout, DioExceptionType.sendTimeout, DioExceptionType.receiveTimeout]) {
        expect(ApiException.fromDio(dio(t)).kind, ApiErrorKind.timeout);
      }
    });

    test('no connection', () {
      expect(ApiException.fromDio(dio(DioExceptionType.connectionError)).kind, ApiErrorKind.noConnection);
    });

    test('a technical error never reaches the user', () {
      final e = ApiException.fromDio(dio(DioExceptionType.unknown));
      expect(e.userMessage, 'Something went wrong. Please try again.');
      expect(e.userMessage, isNot(contains('Exception')));
    });
  });
}
