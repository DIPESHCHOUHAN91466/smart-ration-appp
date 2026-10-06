import '../features/auth/session.dart';

/// Screen addresses, in one place so a typo can't send someone to a blank page.
abstract final class Routes {
  static const splash = '/';
  static const chooseLanguage = '/welcome/language';
  static const changeLanguage = '/settings/language';
  static const serverStatus = '/settings/server';
  static const login = '/login';

  /// Forgotten password (public): a code to the registered mobile, then a new password.
  static const forgotPassword = '/login/forgot';

  /// My account (any signed-in role): change password, download my data.
  static const account = '/account';

  /// Change my password (any signed-in role).
  static const changePassword = '/account/password';

  /// The Public Help assistant: open to everyone, signed in or not.
  static const help = '/help';

  /// The help page's sections and search (public), and one article.
  static const helpTopics = '/help/topics';
  static const helpArticlePattern = '/help/topics/:id';
  static String helpArticle(String id) => '/help/topics/${Uri.encodeComponent(id)}';

  /// My notifications (any signed-in role).
  static const notifications = '/notifications';

  static const citizenHome = '/citizen';
  static const citizenFamily = '/citizen/family';
  static const citizenCard = '/citizen/card';
  static const citizenEligibility = '/citizen/eligibility';
  static const citizenBook = '/citizen/book';
  static const citizenTokens = '/citizen/tokens';
  static const citizenTokenPattern = '/citizen/token/:id';
  static String citizenToken(int id) => '/citizen/token/$id';

  /// Report a problem; may receive a ComplaintDraft (pre-filled by the AI assistant) as `extra`.
  static const citizenComplaint = '/citizen/complaint';
  static const citizenComplaints = '/citizen/complaints';
  static const shopHome = '/shop';
  static const shopScan = '/shop/scan';
  static const shopOtp = '/shop/otp';
  static const shopQueue = '/shop/queue';
  static const shopStock = '/shop/stock';

  /// The customer check and the receipt receive their data from the previous screen (`extra`).
  static const shopCheck = '/shop/check';
  static const shopReceipt = '/shop/receipt';
  static const officialHome = '/official';
  static const officialShops = '/official/shops';
  static const officialShopPattern = '/official/shops/:id';
  static String officialShop(int id) => '/official/shops/$id';
  static const officialAlerts = '/official/alerts';
  static const officialComplaints = '/official/complaints';
  static const officialBookings = '/official/bookings';
  static const officialStock = '/official/stock';
  static const officialReports = '/official/reports';
  static const officialAudit = '/official/audit';
  static const officialUsers = '/official/users';
  static const officialInsights = '/official/insights';

  /// Screens anyone may open without signing in.
  static const public = {splash, chooseLanguage, changeLanguage, serverStatus, login, forgotPassword, help, helpTopics};

  /// [public], plus every help article.
  static bool isPublic(String location) => public.contains(location) || location.startsWith('$helpTopics/');

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
