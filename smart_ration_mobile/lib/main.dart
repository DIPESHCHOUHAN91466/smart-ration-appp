import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import 'app/app.dart';
import 'app/env.dart';
import 'core/providers.dart';

void main() {
  WidgetsFlutterBinding.ensureInitialized();
  // Stops right here, with a clear message, if the build settings are wrong (e.g. production without https).
  final env = Env.fromDefines();
  runApp(ProviderScope(
    retry: noAutomaticRetry,
    overrides: [envProvider.overrideWithValue(env)],
    child: const SmartRationApp(),
  ));
}
