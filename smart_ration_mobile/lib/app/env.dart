/// Which backend the app talks to. It is chosen when the app is built, never typed in by a user:
///
///   flutter run                                  -> development: the emulator talks to your PC
///   flutter build apk --dart-define=APP_ENV=staging --dart-define=API_BASE_URL=https://staging.example.org
///
/// Staging and production builds refuse to start without an https address that is not on this PC.
enum AppEnvironment { development, staging, production }

class Env {
  const Env({required this.environment, required this.apiBaseUrl});

  final AppEnvironment environment;

  /// The backend's address without a trailing slash, e.g. `http://10.0.2.2:8000`.
  final String apiBaseUrl;

  bool get isDevelopment => environment == AppEnvironment.development;

  /// The Android emulator reaches your PC's `localhost` at 10.0.2.2.
  static const developmentDefaultUrl = 'http://10.0.2.2:8000';

  /// Reads the `--dart-define` values given at build time.
  static Env fromDefines() => Env.parse(
        environment: const String.fromEnvironment('APP_ENV', defaultValue: 'development'),
        apiBaseUrl: const String.fromEnvironment('API_BASE_URL'),
      );

  static Env parse({required String environment, required String apiBaseUrl}) {
    final env = AppEnvironment.values.where((e) => e.name == environment).firstOrNull;
    if (env == null) {
      throw ArgumentError('Unknown APP_ENV "$environment". Use development, staging or production.');
    }

    var url = apiBaseUrl.trim();
    if (url.isEmpty && env == AppEnvironment.development) url = developmentDefaultUrl;
    if (url.isEmpty) throw ArgumentError('API_BASE_URL is required for ${env.name} builds.');
    while (url.endsWith('/')) {
      url = url.substring(0, url.length - 1);
    }

    final uri = Uri.tryParse(url);
    if (uri == null || !uri.hasScheme || uri.host.isEmpty) {
      throw ArgumentError('API_BASE_URL "$url" is not a valid address.');
    }
    if (env != AppEnvironment.development) {
      if (uri.scheme != 'https') throw ArgumentError('${env.name} builds must use https, not "$url".');
      if (_isPrivateHost(uri.host)) {
        throw ArgumentError('${env.name} builds must not point at a local or private address ("$url").');
      }
    }
    return Env(environment: env, apiBaseUrl: url);
  }

  static bool _isPrivateHost(String host) =>
      host == 'localhost' ||
      host.startsWith('127.') ||
      host.startsWith('10.') ||
      host.startsWith('192.168.') ||
      RegExp(r'^172\.(1[6-9]|2\d|3[01])\.').hasMatch(host);
}
