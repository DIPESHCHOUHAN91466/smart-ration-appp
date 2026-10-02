import 'dart:io';

import 'package:dio/dio.dart';

import '../../l10n/app_localizations.dart';

/// What kind of failure happened, so screens can react (e.g. go to login on [unauthorized]).
enum ApiErrorKind {
  noConnection,
  timeout,
  badRequest,
  unauthorized,
  forbidden,
  notFound,
  conflict,
  validation,
  tooManyRequests,
  server,
  unknown,
}

/// Every failed backend call becomes one of these. Screens show [messageIn], never the raw error.
class ApiException implements Exception {
  const ApiException(this.kind, {this.serverMessage, this.errorCode, this.statusCode});

  final ApiErrorKind kind;

  /// The backend's own explanation (e.g. "This time slot is full."). The backend writes these for
  /// users and never puts technical details in them.
  final String? serverMessage;

  /// A stable code from the backend, e.g. `INVALID_SIGNATURE` or `WRONG_SHOP`.
  final String? errorCode;
  final int? statusCode;

  /// The backend could not be reached at all (as opposed to answering with an error).
  bool get isOffline => kind == ApiErrorKind.noConnection || kind == ApiErrorKind.timeout;

  /// The sentence to show, in the user's language.
  ///
  /// When the backend explained a refusal (e.g. "This time slot is full.") that explanation is shown,
  /// because it is more useful than a general sentence. The backend writes these in English only, so
  /// later features translate the ones they expect by [errorCode].
  String messageIn(AppLocalizations l) => switch (kind) {
        ApiErrorKind.noConnection => l.errorNoConnection,
        ApiErrorKind.timeout => l.errorTimeout,
        ApiErrorKind.unauthorized => l.errorSessionEnded,
        ApiErrorKind.tooManyRequests => l.errorTooManyRequests,
        ApiErrorKind.server => l.errorServer,
        ApiErrorKind.unknown => l.errorGeneric,
        ApiErrorKind.forbidden => serverMessage ?? l.errorForbidden,
        ApiErrorKind.notFound => serverMessage ?? l.errorNotFound,
        ApiErrorKind.badRequest || ApiErrorKind.conflict || ApiErrorKind.validation => serverMessage ?? l.errorRequestFailed,
      };

  factory ApiException.fromDio(DioException e) {
    switch (e.type) {
      case DioExceptionType.connectionTimeout:
      case DioExceptionType.sendTimeout:
      case DioExceptionType.receiveTimeout:
      case DioExceptionType.transformTimeout:
        return const ApiException(ApiErrorKind.timeout);
      case DioExceptionType.connectionError:
        return const ApiException(ApiErrorKind.noConnection);
      case DioExceptionType.badResponse:
        return ApiException.fromResponse(e.response?.statusCode, e.response?.data);
      case DioExceptionType.unknown:
        return ApiException(e.error is SocketException ? ApiErrorKind.noConnection : ApiErrorKind.unknown);
      case DioExceptionType.badCertificate:
      case DioExceptionType.cancel:
        return const ApiException(ApiErrorKind.unknown);
    }
  }

  /// Builds the exception from an HTTP status and the backend's `{success, message, errorCode}` body.
  factory ApiException.fromResponse(int? status, Object? body) {
    String? message;
    String? code;
    if (body is Map) {
      final m = body['message'];
      final c = body['errorCode'];
      if (m is String && m.trim().isNotEmpty) message = m;
      if (c is String && c.isNotEmpty) code = c;
    }
    final kind = switch (status) {
      400 => ApiErrorKind.badRequest,
      401 => ApiErrorKind.unauthorized,
      403 => ApiErrorKind.forbidden,
      404 => ApiErrorKind.notFound,
      409 => ApiErrorKind.conflict,
      422 => ApiErrorKind.validation,
      429 => ApiErrorKind.tooManyRequests,
      final s? when s >= 500 => ApiErrorKind.server,
      _ => ApiErrorKind.unknown,
    };
    // Server errors (5xx) are never shown in the backend's words: they are not written for users.
    final shown = kind == ApiErrorKind.server ? null : message;
    return ApiException(kind, serverMessage: shown, errorCode: code, statusCode: status);
  }

  @override
  String toString() => 'ApiException($kind, status: $statusCode, code: $errorCode)';
}
