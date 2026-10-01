// ignore: unused_import
import 'package:intl/intl.dart' as intl;

import 'app_localizations.dart';

// ignore_for_file: type=lint

/// The translations for English (`en`).
class AppLocalizationsEn extends AppLocalizations {
  AppLocalizationsEn([String locale = 'en']) : super(locale);

  @override
  String get appTitle => 'Smart Ration AI';

  @override
  String get poweredBy => 'Powered by HSD2C';

  @override
  String get tagline => 'AI powered · For every family';

  @override
  String get loading => 'Loading...';

  @override
  String get logoDescription => 'Smart Ration AI logo, powered by HSD2C';

  @override
  String get chooseLanguageTitle => 'Choose your language';

  @override
  String get chooseLanguageHelp =>
      'You can change it later from the language button at the top of the screen.';

  @override
  String get continueButton => 'Continue';

  @override
  String get language => 'Language';

  @override
  String get serverChecking => 'Checking the connection to the server…';

  @override
  String get serverConnected => 'Connected to the server';

  @override
  String get serverNoDatabase => 'The server cannot reach its database';

  @override
  String get statusOverall => 'Overall';

  @override
  String get statusDatabase => 'Database';

  @override
  String get statusData => 'Data';

  @override
  String get statusHealthy => 'Working';

  @override
  String get statusDegraded => 'Partly working';

  @override
  String get statusUnhealthy => 'Not working';

  @override
  String get statusUnknown => 'Unknown';

  @override
  String get dataSynthetic => 'Demo data (synthetic)';

  @override
  String get dataReal => 'Real data';

  @override
  String serverAddress(String url, String environment) {
    return 'Server: $url · $environment';
  }

  @override
  String get tryAgain => 'Try again';

  @override
  String get errorNoConnection =>
      'Unable to connect. Please check your internet connection.';

  @override
  String get errorTimeout =>
      'The server is taking too long to answer. Please try again.';

  @override
  String get errorSessionEnded =>
      'Your session has ended. Please sign in again.';

  @override
  String get errorTooManyRequests =>
      'Too many attempts. Please wait a minute and try again.';

  @override
  String get errorServer =>
      'The server had a problem. Please try again in a few minutes.';

  @override
  String get errorGeneric => 'Something went wrong. Please try again.';

  @override
  String get errorForbidden => 'You do not have permission to do this.';

  @override
  String get errorNotFound => 'The requested information was not found.';

  @override
  String get errorRequestFailed =>
      'The request could not be completed. Please check and try again.';
}
