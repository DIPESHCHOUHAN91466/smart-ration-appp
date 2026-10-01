import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../features/language/language_screen.dart';
import '../features/server_status/server_status_screen.dart';
import '../features/splash/splash_screen.dart';
import 'routes.dart';

/// The list of screens and their addresses. Login and the role dashboards are added in later
/// milestones; the login check (redirect) goes here too.
final routerProvider = Provider<GoRouter>((ref) => GoRouter(
      initialLocation: Routes.splash,
      routes: [
        GoRoute(path: Routes.splash, builder: (context, state) => const SplashScreen()),
        GoRoute(path: Routes.chooseLanguage, builder: (context, state) => const LanguageScreen(firstLaunch: true)),
        GoRoute(path: Routes.home, builder: (context, state) => const ServerStatusScreen()),
        GoRoute(path: Routes.changeLanguage, builder: (context, state) => const LanguageScreen(firstLaunch: false)),
      ],
    ));
