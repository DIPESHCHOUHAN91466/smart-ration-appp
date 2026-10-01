import 'package:flutter/foundation.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../features/auth/auth_controller.dart';
import '../features/auth/login_screen.dart';
import '../features/auth/session.dart';
import '../features/home/role_home_screen.dart';
import '../features/language/language_screen.dart';
import '../features/server_status/server_status_screen.dart';
import '../features/splash/splash_screen.dart';
import 'routes.dart';

/// The list of screens, plus the sign-in rules applied before any screen opens:
///  * signed out -> only the public screens; anything else goes to sign-in;
///  * signed in  -> the sign-in screen goes to your dashboard, and another role's area goes to yours.
/// These rules are for convenience only. The backend checks the role on every request.
final routerProvider = Provider<GoRouter>((ref) {
  // Re-checks the rules whenever someone signs in or out (including an expired session).
  final authChanged = ValueNotifier<SessionUser?>(ref.read(authControllerProvider));
  ref.listen(authControllerProvider, (_, user) => authChanged.value = user);
  ref.onDispose(authChanged.dispose);

  return GoRouter(
    initialLocation: Routes.splash,
    refreshListenable: authChanged,
    redirect: (context, state) => redirectFor(ref.read(authControllerProvider), state.matchedLocation),
    routes: [
      GoRoute(path: Routes.splash, builder: (context, state) => const SplashScreen()),
      GoRoute(path: Routes.chooseLanguage, builder: (context, state) => const LanguageScreen(firstLaunch: true)),
      GoRoute(path: Routes.changeLanguage, builder: (context, state) => const LanguageScreen(firstLaunch: false)),
      GoRoute(path: Routes.serverStatus, builder: (context, state) => const ServerStatusScreen()),
      GoRoute(path: Routes.login, builder: (context, state) => const LoginScreen()),
      GoRoute(path: Routes.citizenHome, builder: (context, state) => const RoleHomeScreen()),
      GoRoute(path: Routes.shopHome, builder: (context, state) => const RoleHomeScreen()),
      GoRoute(path: Routes.officialHome, builder: (context, state) => const RoleHomeScreen()),
    ],
  );
});

/// Where to send someone instead of [location], or null to let them in. Kept separate so it can be tested.
String? redirectFor(SessionUser? user, String location) {
  if (user == null) return Routes.public.contains(location) ? null : Routes.login;
  final home = Routes.homeFor(user.role);
  if (location == Routes.login) return home;
  final area = Routes.areaOf(location);
  if (area != null && area != home) return home;
  return null;
}
