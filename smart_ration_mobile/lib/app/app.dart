import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../core/network/network_status.dart';
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
        builder: (context, child) => _OfflineFrame(child: child ?? const SizedBox.shrink()),
      );
}

/// Every screen, with a "No internet" banner above it while the backend can't be reached.
class _OfflineFrame extends ConsumerWidget {
  const _OfflineFrame({required this.child});

  final Widget child;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final offline = !ref.watch(networkOnlineProvider);
    final l = AppLocalizations.of(context);
    // The same structure online and offline: changing it would rebuild every open screen from
    // scratch (losing what was typed and where the user was). Only the banner appears or not.
    return Column(children: [
      if (offline) Material(
        color: AppColors.ink,
        child: SafeArea(
          bottom: false,
          child: Semantics(
            liveRegion: true,
            child: Padding(
              padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 10),
              child: Row(children: [
                const Icon(Icons.wifi_off, color: Colors.white),
                const SizedBox(width: 10),
                Expanded(child: Text(l.offlineBanner, style: const TextStyle(color: Colors.white, fontSize: 14))),
              ]),
            ),
          ),
        ),
      ),
      // The banner already sits below the status bar, so the screen must not leave room for it again.
      Expanded(child: MediaQuery.removePadding(context: context, removeTop: offline, child: child)),
    ]);
  }
}
