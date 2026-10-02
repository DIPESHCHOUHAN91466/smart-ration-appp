import 'dart:developer' as developer;

import 'package:dio/dio.dart';

import '../storage/token_storage.dart';
import 'api_exception.dart';

/// The one place the app talks to the backend. Every screen goes through this class, so the sign-in
/// token, timeouts, error messages and logging are handled the same way everywhere.
///
/// Backend responses look like `{success, message, data, errors}`; [get]/[post] return just `data`.
class ApiClient {
  ApiClient(this._dio);

  /// [refreshAccessToken] is called once when the backend answers 401 (the 15-minute access token
  /// has expired). It returns a new token, or null when the session is over; the request is then
  /// sent once more with the new token.
  factory ApiClient.create({
    required String baseUrl,
    required TokenStorage tokens,
    Future<String?> Function()? refreshAccessToken,
    bool logRequests = false,
    HttpClientAdapter? adapter,
    void Function(bool online)? onReachability,
  }) {
    final dio = createDio(baseUrl, adapter: adapter);
    // First, so it sees every outcome: any answer from the backend means online; no connection or
    // a timeout means offline.
    if (onReachability != null) {
      dio.interceptors.add(InterceptorsWrapper(
        onResponse: (response, handler) {
          onReachability(true);
          handler.next(response);
        },
        onError: (error, handler) {
          onReachability(!ApiException.fromDio(error).isOffline);
          handler.next(error);
        },
      ));
    }
    dio.interceptors.add(InterceptorsWrapper(
      onRequest: (options, handler) async {
        final token = await tokens.readAccessToken();
        if (token != null && token.isNotEmpty) options.headers['Authorization'] = 'Bearer $token';
        handler.next(options);
      },
      onError: (error, handler) async {
        final request = error.requestOptions;
        final canRetry = error.response?.statusCode == 401 &&
            refreshAccessToken != null &&
            request.extra['retriedAfterRefresh'] != true &&
            !request.path.startsWith('/api/auth/');
        if (!canRetry) return handler.next(error);
        try {
          final newToken = await refreshAccessToken();
          if (newToken == null) return handler.next(error);
          request.extra['retriedAfterRefresh'] = true;
          return handler.resolve(await dio.fetch<Object?>(request));
        } on DioException catch (retryError) {
          return handler.next(retryError);
        } on ApiException catch (refreshError) {
          // Could not reach the server to refresh: report that problem (e.g. "no connection").
          return handler.reject(DioException(requestOptions: request, error: refreshError, type: DioExceptionType.unknown));
        }
      },
    ));
    if (logRequests) dio.interceptors.add(_RequestLog());
    return ApiClient(dio);
  }

  /// A plain client with the app's address and timeouts, without any sign-in handling.
  static Dio createDio(String baseUrl, {HttpClientAdapter? adapter}) {
    final dio = Dio(BaseOptions(
      baseUrl: baseUrl,
      connectTimeout: const Duration(seconds: 10),
      receiveTimeout: const Duration(seconds: 20),
      contentType: Headers.jsonContentType,
      responseType: ResponseType.json,
    ));
    if (adapter != null) dio.httpClientAdapter = adapter;
    return dio;
  }

  final Dio _dio;

  Future<T?> get<T>(String path, {Map<String, dynamic>? query}) =>
      _envelope<T>(() => _dio.get<Object?>(path, queryParameters: query));

  Future<T?> post<T>(String path, {Object? body, Map<String, String>? headers}) =>
      _envelope<T>(() => _dio.post<Object?>(path, data: body, options: headers == null ? null : Options(headers: headers)));

  Future<T?> delete<T>(String path) => _envelope<T>(() => _dio.delete<Object?>(path));

  /// For the few backend routes that answer without the envelope, such as `/health`.
  /// [acceptedStatuses] lists error statuses whose body should still be returned (e.g. 503).
  Future<Map<String, dynamic>> getJson(String path, {Set<int> acceptedStatuses = const {}}) async {
    final response = await _send(() => _dio.get<Object?>(
          path,
          options: Options(validateStatus: (s) => s != null && (s < 300 || acceptedStatuses.contains(s))),
        ));
    final data = response.data;
    if (data is Map<String, dynamic>) return data;
    throw const ApiException(ApiErrorKind.unknown);
  }

  Future<T?> _envelope<T>(Future<Response<Object?>> Function() call) async {
    final response = await _send(call);
    final body = response.data;
    if (body is! Map || body['success'] != true) {
      throw ApiException.fromResponse(response.statusCode == 200 ? 400 : response.statusCode, body);
    }
    return body['data'] as T?;
  }

  Future<Response<Object?>> _send(Future<Response<Object?>> Function() call) async {
    try {
      return await call();
    } on DioException catch (e) {
      final inner = e.error;
      throw inner is ApiException ? inner : ApiException.fromDio(e);
    }
  }
}

/// Development logging: method, path, status and time only. Never headers or bodies, which can
/// contain tokens, OTPs or personal data.
class _RequestLog extends Interceptor {
  @override
  void onRequest(RequestOptions options, RequestInterceptorHandler handler) {
    options.extra['startedAt'] = DateTime.now();
    handler.next(options);
  }

  @override
  void onResponse(Response response, ResponseInterceptorHandler handler) {
    _log(response.requestOptions, response.statusCode);
    handler.next(response);
  }

  @override
  void onError(DioException err, ErrorInterceptorHandler handler) {
    _log(err.requestOptions, err.response?.statusCode, err.type.name);
    handler.next(err);
  }

  void _log(RequestOptions o, int? status, [String? error]) {
    final started = o.extra['startedAt'];
    final ms = started is DateTime ? DateTime.now().difference(started).inMilliseconds : null;
    developer.log('${o.method} ${o.uri.path} -> ${status ?? error} (${ms}ms)', name: 'api');
  }
}
