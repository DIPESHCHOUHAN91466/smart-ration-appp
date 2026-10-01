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

  factory ApiClient.create({
    required String baseUrl,
    required TokenStorage tokens,
    bool logRequests = false,
    HttpClientAdapter? adapter,
  }) {
    final dio = Dio(BaseOptions(
      baseUrl: baseUrl,
      connectTimeout: const Duration(seconds: 10),
      receiveTimeout: const Duration(seconds: 20),
      contentType: Headers.jsonContentType,
      responseType: ResponseType.json,
    ));
    if (adapter != null) dio.httpClientAdapter = adapter;
    dio.interceptors.add(InterceptorsWrapper(onRequest: (options, handler) async {
      final token = await tokens.readAccessToken();
      if (token != null && token.isNotEmpty) options.headers['Authorization'] = 'Bearer $token';
      handler.next(options);
    }));
    if (logRequests) dio.interceptors.add(_RequestLog());
    return ApiClient(dio);
  }

  final Dio _dio;

  Future<T?> get<T>(String path, {Map<String, dynamic>? query}) =>
      _envelope<T>(() => _dio.get<Object?>(path, queryParameters: query));

  Future<T?> post<T>(String path, {Object? body}) => _envelope<T>(() => _dio.post<Object?>(path, data: body));

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
      throw ApiException.fromDio(e);
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
