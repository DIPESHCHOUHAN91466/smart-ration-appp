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

  @override
  String get signInTitle => 'Sign in';

  @override
  String get signInSubtitle =>
      'Use the email and password of your Smart Ration account.';

  @override
  String get emailLabel => 'Email';

  @override
  String get passwordLabel => 'Password';

  @override
  String get showPassword => 'Show password';

  @override
  String get hidePassword => 'Hide password';

  @override
  String get signInButton => 'Sign in';

  @override
  String get signingIn => 'Signing in...';

  @override
  String get emailRequired => 'Please enter your email.';

  @override
  String get emailInvalid => 'Please enter a valid email address.';

  @override
  String get passwordRequired => 'Please enter your password.';

  @override
  String get loginInvalid => 'The email or password is not correct.';

  @override
  String get loginAccountDisabled =>
      'This account has been turned off. Please contact your ration shop or district office.';

  @override
  String get demoAccountsTitle => 'Demo accounts (development builds only)';

  @override
  String get demoAccountsHelp =>
      'Tap one to fill in its email. The demo password is in the project README.';

  @override
  String get checkServer => 'Check server connection';

  @override
  String get serverStatusTitle => 'Server status';

  @override
  String get roleRuralUser => 'Rural User';

  @override
  String get roleShopOwner => 'Shop Owner';

  @override
  String get roleOfficial => 'Government Official';

  @override
  String get roleAdmin => 'Administrator';

  @override
  String greeting(String name) {
    return 'Namaste, $name';
  }

  @override
  String get signOut => 'Sign out';

  @override
  String shopLinked(int id) {
    return 'Ration shop no. $id';
  }

  @override
  String get citizenDashboardIntro =>
      'Your ration card, family members, booking and token will appear here.';

  @override
  String get shopDashboardIntro =>
      'Today\'s tokens, the QR scanner, stock and collections will appear here.';

  @override
  String get officialDashboardIntro =>
      'Shops, distribution, stock alerts and reports will appear here.';

  @override
  String get signInWithMobile => 'Mobile & code';

  @override
  String get signInWithEmail => 'Email & password';

  @override
  String get mobileSignInSubtitle =>
      'We will send a 6-digit code to your registered mobile number.';

  @override
  String get mobileLabel => 'Mobile number';

  @override
  String get mobileInvalid => 'Please enter a 10-digit mobile number.';

  @override
  String get sendCode => 'Send code';

  @override
  String get sendingCode => 'Sending code...';

  @override
  String codeSentTo(String mobile) {
    return 'If $mobile is registered, a code has been sent to it.';
  }

  @override
  String get codeLabel => '6-digit code';

  @override
  String get codeInvalidFormat => 'Please enter the 6-digit code.';

  @override
  String get otpInvalid =>
      'The code is wrong or has expired. Please try again or ask for a new code.';

  @override
  String get otpSendFailed =>
      'The code could not be sent right now. Please try again, or sign in with email and password.';

  @override
  String resendIn(int seconds) {
    return 'Send a new code in $seconds s';
  }

  @override
  String get resendCode => 'Send a new code';

  @override
  String get changeNumber => 'Change number';

  @override
  String demoCodeHint(String code) {
    return 'Development demo code: $code';
  }

  @override
  String get otpStaffNote =>
      'Ration shop owners and officials sign in with email and password.';
}
