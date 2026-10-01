import 'package:flutter/widgets.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'package:smart_ration_mobile/app/app.dart';
import 'package:smart_ration_mobile/app/env.dart';
import 'package:smart_ration_mobile/core/network/api_client.dart';
import 'package:smart_ration_mobile/core/providers.dart';
import 'package:smart_ration_mobile/core/storage/token_storage.dart';
import 'package:smart_ration_mobile/features/language/app_language.dart';
import 'package:smart_ration_mobile/features/splash/splash_screen.dart';

import 'fake_backend.dart';

/// The whole app, wired to a fake backend and a fake phone storage.
/// [savedLanguage] is what the phone remembers from a previous launch (null = first launch).
Future<(Widget, SharedPreferences)> buildTestApp(FakeBackend backend, {String? savedLanguage}) async {
  SharedPreferences.setMockInitialValues({LanguageController.storageKey: ?savedLanguage});
  final preferences = await SharedPreferences.getInstance();
  final app = ProviderScope(
    retry: noAutomaticRetry,
    overrides: [
      envProvider.overrideWithValue(Env.parse(environment: 'development', apiBaseUrl: '')),
      sharedPreferencesProvider.overrideWithValue(preferences),
      splashDurationProvider.overrideWithValue(Duration.zero),
      apiClientProvider.overrideWithValue(
          ApiClient.create(baseUrl: 'http://test.local', tokens: MemoryTokenStorage(), adapter: backend)),
    ],
    child: const SmartRationApp(),
  );
  return (app, preferences);
}

const healthyServer = FakeReply(200, {'status': 'healthy', 'database': 'healthy', 'dataMode': 'synthetic'});
