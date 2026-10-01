import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../features/language/app_language.dart';
import '../l10n/app_localizations.dart';
import 'router.dart';
import 'theme.dart';

class SmartRationApp extends ConsumerWidget {
  const SmartRationApp({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) => MaterialApp.router(
        onGenerateTitle: (context) => AppLocalizations.of(context).appTitle,
        theme: buildAppTheme(),
        routerConfig: ref.watch(routerProvider),
        debugShowCheckedModeBanner: false,
        // The chosen language; before the first choice, the phone's language if we support it, else English.
        locale: ref.watch(languageProvider)?.locale,
        supportedLocales: AppLocalizations.supportedLocales,
        localizationsDelegates: AppLocalizations.localizationsDelegates,
      );
}
