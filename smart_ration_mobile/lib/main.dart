import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:shared_preferences/shared_preferences.dart';

import 'app/app.dart';
import 'app/env.dart';
import 'core/providers.dart';
import 'features/language/app_language.dart';

Future<void> main() async {
  WidgetsFlutterBinding.ensureInitialized();
  // Stops right here, with a clear message, if the build settings are wrong (e.g. production without https).
  final env = Env.fromDefines();
  final preferences = await SharedPreferences.getInstance();
  runApp(ProviderScope(
    retry: noAutomaticRetry,
    overrides: [
      envProvider.overrideWithValue(env),
      sharedPreferencesProvider.overrideWithValue(preferences),
    ],
    child: const SmartRationApp(),
  ));
}
