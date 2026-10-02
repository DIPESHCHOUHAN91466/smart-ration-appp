import 'package:flutter/widgets.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_riverpod/misc.dart' show Override;
import 'package:shared_preferences/shared_preferences.dart';
import 'package:smart_ration_mobile/app/app.dart';
import 'package:smart_ration_mobile/app/env.dart';
import 'package:smart_ration_mobile/core/providers.dart';
import 'package:smart_ration_mobile/core/storage/offline_store.dart';
import 'package:smart_ration_mobile/core/storage/token_storage.dart';
import 'package:smart_ration_mobile/features/auth/auth_controller.dart';
import 'package:smart_ration_mobile/features/auth/session.dart';
import 'package:smart_ration_mobile/features/language/app_language.dart';
import 'package:smart_ration_mobile/features/splash/splash_screen.dart';

import 'fake_backend.dart';

/// The whole app, wired to a fake backend and fake phone storage.
///  * [savedLanguage]: what the phone remembers from a previous launch (null = first launch);
///  * [signedInAs]: a session saved on the phone from a previous launch (null = signed out);
///  * [overrides]: anything else to replace, e.g. the camera.
class TestApp {
  TestApp._(this.widget, this.preferences, this.tokens, this.offline);

  final Widget widget;
  final SharedPreferences preferences;
  final MemoryTokenStorage tokens;

  /// The saved copies for offline use (tokens and QR codes).
  final MemoryOfflineStore offline;

  static Future<TestApp> build(FakeBackend backend, {String? savedLanguage, SessionUser? signedInAs, List<Override> overrides = const []}) async {
    SharedPreferences.setMockInitialValues({LanguageController.storageKey: ?savedLanguage});
    final preferences = await SharedPreferences.getInstance();
    final tokens = MemoryTokenStorage();
    final offline = MemoryOfflineStore();
    if (signedInAs != null) {
      await AuthResult(accessToken: 'saved-access', refreshToken: 'saved-refresh', user: signedInAs).saveTo(tokens);
    }
    final widget = ProviderScope(
      retry: noAutomaticRetry,
      overrides: [
        envProvider.overrideWithValue(Env.parse(environment: 'development', apiBaseUrl: 'http://test.local')),
        sharedPreferencesProvider.overrideWithValue(preferences),
        splashDurationProvider.overrideWithValue(Duration.zero),
        httpAdapterProvider.overrideWithValue(backend),
        tokenStorageProvider.overrideWithValue(tokens),
        offlineStoreProvider.overrideWithValue(offline),
        restoredSessionProvider.overrideWithValue(signedInAs),
        ...overrides,
      ],
      child: const SmartRationApp(),
    );
    return TestApp._(widget, preferences, tokens, offline);
  }
}

/// The app's shared state, for tests that need to trigger something directly.
ProviderContainer containerOf(Element element) => ProviderScope.containerOf(element);

const healthyServer = FakeReply(200, {'status': 'healthy', 'database': 'healthy', 'dataMode': 'synthetic'});

SessionUser citizen() => SessionUser.tryParse(userJson())!;
SessionUser shopOwner() => SessionUser.tryParse(userJson(id: 3, fullName: 'Ramesh Patil', role: 'ShopOwner', rationShopId: 3))!;
