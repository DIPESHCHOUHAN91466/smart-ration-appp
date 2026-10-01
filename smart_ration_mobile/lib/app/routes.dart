import '../features/auth/session.dart';

/// Screen addresses, in one place so a typo can't send someone to a blank page.
abstract final class Routes {
  static const splash = '/';
  static const chooseLanguage = '/welcome/language';
  static const changeLanguage = '/settings/language';
  static const serverStatus = '/settings/server';
  static const login = '/login';

  static const citizenHome = '/citizen';
  static const shopHome = '/shop';
  static const officialHome = '/official';

  /// Screens anyone may open without signing in.
  static const public = {splash, chooseLanguage, changeLanguage, serverStatus, login};

  /// The dashboard for each role. Admins use the officials' dashboard, as on the website.
  static String homeFor(AppRole role) => switch (role) {
        AppRole.ruralUser => citizenHome,
        AppRole.shopOwner => shopHome,
        AppRole.governmentOfficial || AppRole.admin => officialHome,
      };

  /// Which role's area a location belongs to (null = shared or public).
  static String? areaOf(String location) {
    for (final home in [citizenHome, shopHome, officialHome]) {
      if (location == home || location.startsWith('$home/')) return home;
    }
    return null;
  }
}
