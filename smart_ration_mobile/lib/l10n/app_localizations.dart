import 'dart:async';

import 'package:flutter/foundation.dart';
import 'package:flutter/widgets.dart';
import 'package:flutter_localizations/flutter_localizations.dart';
import 'package:intl/intl.dart' as intl;

import 'app_localizations_en.dart';
import 'app_localizations_hi.dart';
import 'app_localizations_mr.dart';

// ignore_for_file: type=lint

/// Callers can lookup localized strings with an instance of AppLocalizations
/// returned by `AppLocalizations.of(context)`.
///
/// Applications need to include `AppLocalizations.delegate()` in their app's
/// `localizationDelegates` list, and the locales they support in the app's
/// `supportedLocales` list. For example:
///
/// ```dart
/// import 'l10n/app_localizations.dart';
///
/// return MaterialApp(
///   localizationsDelegates: AppLocalizations.localizationsDelegates,
///   supportedLocales: AppLocalizations.supportedLocales,
///   home: MyApplicationHome(),
/// );
/// ```
///
/// ## Update pubspec.yaml
///
/// Please make sure to update your pubspec.yaml to include the following
/// packages:
///
/// ```yaml
/// dependencies:
///   # Internationalization support.
///   flutter_localizations:
///     sdk: flutter
///   intl: any # Use the pinned version from flutter_localizations
///
///   # Rest of dependencies
/// ```
///
/// ## iOS Applications
///
/// iOS applications define key application metadata, including supported
/// locales, in an Info.plist file that is built into the application bundle.
/// To configure the locales supported by your app, you’ll need to edit this
/// file.
///
/// First, open your project’s ios/Runner.xcworkspace Xcode workspace file.
/// Then, in the Project Navigator, open the Info.plist file under the Runner
/// project’s Runner folder.
///
/// Next, select the Information Property List item, select Add Item from the
/// Editor menu, then select Localizations from the pop-up menu.
///
/// Select and expand the newly-created Localizations item then, for each
/// locale your application supports, add a new item and select the locale
/// you wish to add from the pop-up menu in the Value field. This list should
/// be consistent with the languages listed in the AppLocalizations.supportedLocales
/// property.
abstract class AppLocalizations {
  AppLocalizations(String locale)
    : localeName = intl.Intl.canonicalizedLocale(locale.toString());

  final String localeName;

  static AppLocalizations of(BuildContext context) {
    return Localizations.of<AppLocalizations>(context, AppLocalizations)!;
  }

  static const LocalizationsDelegate<AppLocalizations> delegate =
      _AppLocalizationsDelegate();

  /// A list of this localizations delegate along with the default localizations
  /// delegates.
  ///
  /// Returns a list of localizations delegates containing this delegate along with
  /// GlobalMaterialLocalizations.delegate, GlobalCupertinoLocalizations.delegate,
  /// and GlobalWidgetsLocalizations.delegate.
  ///
  /// Additional delegates can be added by appending to this list in
  /// MaterialApp. This list does not have to be used at all if a custom list
  /// of delegates is preferred or required.
  static const List<LocalizationsDelegate<dynamic>> localizationsDelegates =
      <LocalizationsDelegate<dynamic>>[
        delegate,
        GlobalMaterialLocalizations.delegate,
        GlobalCupertinoLocalizations.delegate,
        GlobalWidgetsLocalizations.delegate,
      ];

  /// A list of this localizations delegate's supported locales.
  static const List<Locale> supportedLocales = <Locale>[
    Locale('en'),
    Locale('hi'),
    Locale('mr'),
  ];

  /// No description provided for @appTitle.
  ///
  /// In en, this message translates to:
  /// **'Smart Ration AI'**
  String get appTitle;

  /// Brand line under the app name. HSD2C is a company name and is never translated.
  ///
  /// In en, this message translates to:
  /// **'Powered by HSD2C'**
  String get poweredBy;

  /// No description provided for @tagline.
  ///
  /// In en, this message translates to:
  /// **'AI powered · For every family'**
  String get tagline;

  /// No description provided for @loading.
  ///
  /// In en, this message translates to:
  /// **'Loading...'**
  String get loading;

  /// Read aloud by screen readers instead of the logo image.
  ///
  /// In en, this message translates to:
  /// **'Smart Ration AI logo, powered by HSD2C'**
  String get logoDescription;

  /// No description provided for @chooseLanguageTitle.
  ///
  /// In en, this message translates to:
  /// **'Choose your language'**
  String get chooseLanguageTitle;

  /// No description provided for @chooseLanguageHelp.
  ///
  /// In en, this message translates to:
  /// **'You can change it later from the language button at the top of the screen.'**
  String get chooseLanguageHelp;

  /// No description provided for @continueButton.
  ///
  /// In en, this message translates to:
  /// **'Continue'**
  String get continueButton;

  /// No description provided for @language.
  ///
  /// In en, this message translates to:
  /// **'Language'**
  String get language;

  /// No description provided for @serverChecking.
  ///
  /// In en, this message translates to:
  /// **'Checking the connection to the server…'**
  String get serverChecking;

  /// No description provided for @serverConnected.
  ///
  /// In en, this message translates to:
  /// **'Connected to the server'**
  String get serverConnected;

  /// No description provided for @serverNoDatabase.
  ///
  /// In en, this message translates to:
  /// **'The server cannot reach its database'**
  String get serverNoDatabase;

  /// No description provided for @statusOverall.
  ///
  /// In en, this message translates to:
  /// **'Overall'**
  String get statusOverall;

  /// No description provided for @statusDatabase.
  ///
  /// In en, this message translates to:
  /// **'Database'**
  String get statusDatabase;

  /// No description provided for @statusData.
  ///
  /// In en, this message translates to:
  /// **'Data'**
  String get statusData;

  /// No description provided for @statusHealthy.
  ///
  /// In en, this message translates to:
  /// **'Working'**
  String get statusHealthy;

  /// No description provided for @statusDegraded.
  ///
  /// In en, this message translates to:
  /// **'Partly working'**
  String get statusDegraded;

  /// No description provided for @statusUnhealthy.
  ///
  /// In en, this message translates to:
  /// **'Not working'**
  String get statusUnhealthy;

  /// No description provided for @statusUnknown.
  ///
  /// In en, this message translates to:
  /// **'Unknown'**
  String get statusUnknown;

  /// No description provided for @dataSynthetic.
  ///
  /// In en, this message translates to:
  /// **'Demo data (synthetic)'**
  String get dataSynthetic;

  /// No description provided for @dataReal.
  ///
  /// In en, this message translates to:
  /// **'Real data'**
  String get dataReal;

  /// Developer information at the bottom of the screen.
  ///
  /// In en, this message translates to:
  /// **'Server: {url} · {environment}'**
  String serverAddress(String url, String environment);

  /// No description provided for @tryAgain.
  ///
  /// In en, this message translates to:
  /// **'Try again'**
  String get tryAgain;

  /// No description provided for @errorNoConnection.
  ///
  /// In en, this message translates to:
  /// **'Unable to connect. Please check your internet connection.'**
  String get errorNoConnection;

  /// No description provided for @errorTimeout.
  ///
  /// In en, this message translates to:
  /// **'The server is taking too long to answer. Please try again.'**
  String get errorTimeout;

  /// No description provided for @errorSessionEnded.
  ///
  /// In en, this message translates to:
  /// **'Your session has ended. Please sign in again.'**
  String get errorSessionEnded;

  /// No description provided for @errorTooManyRequests.
  ///
  /// In en, this message translates to:
  /// **'Too many attempts. Please wait a minute and try again.'**
  String get errorTooManyRequests;

  /// No description provided for @errorServer.
  ///
  /// In en, this message translates to:
  /// **'The server had a problem. Please try again in a few minutes.'**
  String get errorServer;

  /// No description provided for @errorGeneric.
  ///
  /// In en, this message translates to:
  /// **'Something went wrong. Please try again.'**
  String get errorGeneric;

  /// No description provided for @errorForbidden.
  ///
  /// In en, this message translates to:
  /// **'You do not have permission to do this.'**
  String get errorForbidden;

  /// No description provided for @errorNotFound.
  ///
  /// In en, this message translates to:
  /// **'The requested information was not found.'**
  String get errorNotFound;

  /// No description provided for @errorRequestFailed.
  ///
  /// In en, this message translates to:
  /// **'The request could not be completed. Please check and try again.'**
  String get errorRequestFailed;

  /// No description provided for @signInTitle.
  ///
  /// In en, this message translates to:
  /// **'Sign in'**
  String get signInTitle;

  /// No description provided for @signInSubtitle.
  ///
  /// In en, this message translates to:
  /// **'Use the email and password of your Smart Ration account.'**
  String get signInSubtitle;

  /// No description provided for @emailLabel.
  ///
  /// In en, this message translates to:
  /// **'Email'**
  String get emailLabel;

  /// No description provided for @passwordLabel.
  ///
  /// In en, this message translates to:
  /// **'Password'**
  String get passwordLabel;

  /// No description provided for @showPassword.
  ///
  /// In en, this message translates to:
  /// **'Show password'**
  String get showPassword;

  /// No description provided for @hidePassword.
  ///
  /// In en, this message translates to:
  /// **'Hide password'**
  String get hidePassword;

  /// No description provided for @signInButton.
  ///
  /// In en, this message translates to:
  /// **'Sign in'**
  String get signInButton;

  /// No description provided for @signingIn.
  ///
  /// In en, this message translates to:
  /// **'Signing in...'**
  String get signingIn;

  /// No description provided for @emailRequired.
  ///
  /// In en, this message translates to:
  /// **'Please enter your email.'**
  String get emailRequired;

  /// No description provided for @emailInvalid.
  ///
  /// In en, this message translates to:
  /// **'Please enter a valid email address.'**
  String get emailInvalid;

  /// No description provided for @passwordRequired.
  ///
  /// In en, this message translates to:
  /// **'Please enter your password.'**
  String get passwordRequired;

  /// No description provided for @loginInvalid.
  ///
  /// In en, this message translates to:
  /// **'The email or password is not correct.'**
  String get loginInvalid;

  /// No description provided for @loginAccountDisabled.
  ///
  /// In en, this message translates to:
  /// **'This account has been turned off. Please contact your ration shop or district office.'**
  String get loginAccountDisabled;

  /// Shown only in development builds.
  ///
  /// In en, this message translates to:
  /// **'Demo accounts (development builds only)'**
  String get demoAccountsTitle;

  /// No description provided for @demoAccountsHelp.
  ///
  /// In en, this message translates to:
  /// **'Tap one to fill in its email. The demo password is in the project README.'**
  String get demoAccountsHelp;

  /// No description provided for @checkServer.
  ///
  /// In en, this message translates to:
  /// **'Check server connection'**
  String get checkServer;

  /// No description provided for @serverStatusTitle.
  ///
  /// In en, this message translates to:
  /// **'Server status'**
  String get serverStatusTitle;

  /// No description provided for @roleRuralUser.
  ///
  /// In en, this message translates to:
  /// **'Rural User'**
  String get roleRuralUser;

  /// No description provided for @roleShopOwner.
  ///
  /// In en, this message translates to:
  /// **'Shop Owner'**
  String get roleShopOwner;

  /// No description provided for @roleOfficial.
  ///
  /// In en, this message translates to:
  /// **'Government Official'**
  String get roleOfficial;

  /// No description provided for @roleAdmin.
  ///
  /// In en, this message translates to:
  /// **'Administrator'**
  String get roleAdmin;

  /// Greeting on the dashboard.
  ///
  /// In en, this message translates to:
  /// **'Namaste, {name}'**
  String greeting(String name);

  /// No description provided for @signOut.
  ///
  /// In en, this message translates to:
  /// **'Sign out'**
  String get signOut;

  /// The shop a shop owner serves.
  ///
  /// In en, this message translates to:
  /// **'Ration shop no. {id}'**
  String shopLinked(int id);

  /// No description provided for @citizenDashboardIntro.
  ///
  /// In en, this message translates to:
  /// **'Your ration card, family members, booking and token will appear here.'**
  String get citizenDashboardIntro;

  /// No description provided for @shopDashboardIntro.
  ///
  /// In en, this message translates to:
  /// **'Today\'s tokens, the QR scanner, stock and collections will appear here.'**
  String get shopDashboardIntro;

  /// No description provided for @officialDashboardIntro.
  ///
  /// In en, this message translates to:
  /// **'Shops, distribution, stock alerts and reports will appear here.'**
  String get officialDashboardIntro;

  /// No description provided for @signInWithMobile.
  ///
  /// In en, this message translates to:
  /// **'Mobile & code'**
  String get signInWithMobile;

  /// No description provided for @signInWithEmail.
  ///
  /// In en, this message translates to:
  /// **'Email & password'**
  String get signInWithEmail;

  /// No description provided for @mobileSignInSubtitle.
  ///
  /// In en, this message translates to:
  /// **'We will send a 6-digit code to your registered mobile number.'**
  String get mobileSignInSubtitle;

  /// No description provided for @mobileLabel.
  ///
  /// In en, this message translates to:
  /// **'Mobile number'**
  String get mobileLabel;

  /// No description provided for @mobileInvalid.
  ///
  /// In en, this message translates to:
  /// **'Please enter a 10-digit mobile number.'**
  String get mobileInvalid;

  /// No description provided for @sendCode.
  ///
  /// In en, this message translates to:
  /// **'Send code'**
  String get sendCode;

  /// No description provided for @sendingCode.
  ///
  /// In en, this message translates to:
  /// **'Sending code...'**
  String get sendingCode;

  /// No description provided for @codeSentTo.
  ///
  /// In en, this message translates to:
  /// **'If {mobile} is registered, a code has been sent to it.'**
  String codeSentTo(String mobile);

  /// No description provided for @codeLabel.
  ///
  /// In en, this message translates to:
  /// **'6-digit code'**
  String get codeLabel;

  /// No description provided for @codeInvalidFormat.
  ///
  /// In en, this message translates to:
  /// **'Please enter the 6-digit code.'**
  String get codeInvalidFormat;

  /// No description provided for @otpInvalid.
  ///
  /// In en, this message translates to:
  /// **'The code is wrong or has expired. Please try again or ask for a new code.'**
  String get otpInvalid;

  /// No description provided for @otpSendFailed.
  ///
  /// In en, this message translates to:
  /// **'The code could not be sent right now. Please try again, or sign in with email and password.'**
  String get otpSendFailed;

  /// No description provided for @resendIn.
  ///
  /// In en, this message translates to:
  /// **'Send a new code in {seconds} s'**
  String resendIn(int seconds);

  /// No description provided for @resendCode.
  ///
  /// In en, this message translates to:
  /// **'Send a new code'**
  String get resendCode;

  /// No description provided for @changeNumber.
  ///
  /// In en, this message translates to:
  /// **'Change number'**
  String get changeNumber;

  /// Development builds only, when the server is in demo mode.
  ///
  /// In en, this message translates to:
  /// **'Development demo code: {code}'**
  String demoCodeHint(String code);

  /// No description provided for @otpStaffNote.
  ///
  /// In en, this message translates to:
  /// **'Ration shop owners and officials sign in with email and password.'**
  String get otpStaffNote;

  /// No description provided for @rationCard.
  ///
  /// In en, this message translates to:
  /// **'Ration card'**
  String get rationCard;

  /// No description provided for @cardNumber.
  ///
  /// In en, this message translates to:
  /// **'Card number'**
  String get cardNumber;

  /// No description provided for @cardScheme.
  ///
  /// In en, this message translates to:
  /// **'Card type (scheme)'**
  String get cardScheme;

  /// No description provided for @cardStatus.
  ///
  /// In en, this message translates to:
  /// **'Status'**
  String get cardStatus;

  /// No description provided for @cardActive.
  ///
  /// In en, this message translates to:
  /// **'Active'**
  String get cardActive;

  /// No description provided for @cardInactive.
  ///
  /// In en, this message translates to:
  /// **'Not active'**
  String get cardInactive;

  /// No description provided for @familyId.
  ///
  /// In en, this message translates to:
  /// **'Family ID'**
  String get familyId;

  /// No description provided for @familySizeLabel.
  ///
  /// In en, this message translates to:
  /// **'Family size'**
  String get familySizeLabel;

  /// No description provided for @memberCount.
  ///
  /// In en, this message translates to:
  /// **'{count} members'**
  String memberCount(int count);

  /// No description provided for @assignedShop.
  ///
  /// In en, this message translates to:
  /// **'Ration shop'**
  String get assignedShop;

  /// No description provided for @familyMembers.
  ///
  /// In en, this message translates to:
  /// **'Family members'**
  String get familyMembers;

  /// No description provided for @ageYears.
  ///
  /// In en, this message translates to:
  /// **'{age} years'**
  String ageYears(int age);

  /// No description provided for @relHead.
  ///
  /// In en, this message translates to:
  /// **'Head of family'**
  String get relHead;

  /// No description provided for @relSpouse.
  ///
  /// In en, this message translates to:
  /// **'Spouse'**
  String get relSpouse;

  /// No description provided for @relSon.
  ///
  /// In en, this message translates to:
  /// **'Son'**
  String get relSon;

  /// No description provided for @relDaughter.
  ///
  /// In en, this message translates to:
  /// **'Daughter'**
  String get relDaughter;

  /// No description provided for @relParent.
  ///
  /// In en, this message translates to:
  /// **'Parent'**
  String get relParent;

  /// No description provided for @relOther.
  ///
  /// In en, this message translates to:
  /// **'Other relative'**
  String get relOther;

  /// No description provided for @memberEligible.
  ///
  /// In en, this message translates to:
  /// **'Eligible'**
  String get memberEligible;

  /// No description provided for @memberNotEligible.
  ///
  /// In en, this message translates to:
  /// **'Not eligible'**
  String get memberNotEligible;

  /// No description provided for @memberPending.
  ///
  /// In en, this message translates to:
  /// **'Pending'**
  String get memberPending;

  /// No description provided for @memberVerificationRequired.
  ///
  /// In en, this message translates to:
  /// **'Verification required'**
  String get memberVerificationRequired;

  /// No description provided for @eligibilityTitle.
  ///
  /// In en, this message translates to:
  /// **'Eligibility'**
  String get eligibilityTitle;

  /// No description provided for @familyEligible.
  ///
  /// In en, this message translates to:
  /// **'Eligible'**
  String get familyEligible;

  /// No description provided for @familyPartiallyEligible.
  ///
  /// In en, this message translates to:
  /// **'Partially eligible'**
  String get familyPartiallyEligible;

  /// No description provided for @familyNotEligible.
  ///
  /// In en, this message translates to:
  /// **'Not eligible'**
  String get familyNotEligible;

  /// No description provided for @eligibleMembersOf.
  ///
  /// In en, this message translates to:
  /// **'{eligible} of {total} members eligible'**
  String eligibleMembersOf(int eligible, int total);

  /// No description provided for @eligibilityExplainEligible.
  ///
  /// In en, this message translates to:
  /// **'Every member of your family can receive rations this month.'**
  String get eligibilityExplainEligible;

  /// No description provided for @eligibilityExplainPartial.
  ///
  /// In en, this message translates to:
  /// **'Some members are not eligible yet. Your entitlement counts only the eligible members.'**
  String get eligibilityExplainPartial;

  /// No description provided for @eligibilityExplainNot.
  ///
  /// In en, this message translates to:
  /// **'Your family cannot receive rations right now. Please contact your ration shop or district office.'**
  String get eligibilityExplainNot;

  /// No description provided for @monthlyEntitlement.
  ///
  /// In en, this message translates to:
  /// **'This month\'s entitlement'**
  String get monthlyEntitlement;

  /// No description provided for @remainingOf.
  ///
  /// In en, this message translates to:
  /// **'{remaining} {unit} left of {total} {unit}'**
  String remainingOf(String remaining, String total, String unit);

  /// No description provided for @collectedAmount.
  ///
  /// In en, this message translates to:
  /// **'Collected: {amount} {unit}'**
  String collectedAmount(String amount, String unit);

  /// No description provided for @itemRice.
  ///
  /// In en, this message translates to:
  /// **'Rice'**
  String get itemRice;

  /// No description provided for @itemWheat.
  ///
  /// In en, this message translates to:
  /// **'Wheat'**
  String get itemWheat;

  /// No description provided for @itemSugar.
  ///
  /// In en, this message translates to:
  /// **'Sugar'**
  String get itemSugar;

  /// No description provided for @itemPulses.
  ///
  /// In en, this message translates to:
  /// **'Pulses (dal)'**
  String get itemPulses;

  /// No description provided for @itemOil.
  ///
  /// In en, this message translates to:
  /// **'Edible oil'**
  String get itemOil;

  /// No description provided for @itemSalt.
  ///
  /// In en, this message translates to:
  /// **'Salt'**
  String get itemSalt;

  /// No description provided for @unitKg.
  ///
  /// In en, this message translates to:
  /// **'kg'**
  String get unitKg;

  /// No description provided for @unitLitre.
  ///
  /// In en, this message translates to:
  /// **'L'**
  String get unitLitre;

  /// No description provided for @collectionHistory.
  ///
  /// In en, this message translates to:
  /// **'Collection history'**
  String get collectionHistory;

  /// No description provided for @noCollections.
  ///
  /// In en, this message translates to:
  /// **'No rations collected yet.'**
  String get noCollections;

  /// No description provided for @aadhaarVerified.
  ///
  /// In en, this message translates to:
  /// **'Aadhaar verified'**
  String get aadhaarVerified;

  /// No description provided for @aadhaarNotVerified.
  ///
  /// In en, this message translates to:
  /// **'Aadhaar not verified'**
  String get aadhaarNotVerified;

  /// No description provided for @viewDetails.
  ///
  /// In en, this message translates to:
  /// **'View details'**
  String get viewDetails;

  /// No description provided for @noBeneficiaryProfile.
  ///
  /// In en, this message translates to:
  /// **'Your ration card is not linked yet. Please contact your ration shop.'**
  String get noBeneficiaryProfile;

  /// Shown on every citizen screen while the backend serves synthetic data.
  ///
  /// In en, this message translates to:
  /// **'Demo data: this is not a real ration card.'**
  String get demoDataNotice;

  /// No description provided for @genderMale.
  ///
  /// In en, this message translates to:
  /// **'Male'**
  String get genderMale;

  /// No description provided for @genderFemale.
  ///
  /// In en, this message translates to:
  /// **'Female'**
  String get genderFemale;

  /// No description provided for @genderOther.
  ///
  /// In en, this message translates to:
  /// **'Other'**
  String get genderOther;
}

class _AppLocalizationsDelegate
    extends LocalizationsDelegate<AppLocalizations> {
  const _AppLocalizationsDelegate();

  @override
  Future<AppLocalizations> load(Locale locale) {
    return SynchronousFuture<AppLocalizations>(lookupAppLocalizations(locale));
  }

  @override
  bool isSupported(Locale locale) =>
      <String>['en', 'hi', 'mr'].contains(locale.languageCode);

  @override
  bool shouldReload(_AppLocalizationsDelegate old) => false;
}

AppLocalizations lookupAppLocalizations(Locale locale) {
  // Lookup logic when only language code is specified.
  switch (locale.languageCode) {
    case 'en':
      return AppLocalizationsEn();
    case 'hi':
      return AppLocalizationsHi();
    case 'mr':
      return AppLocalizationsMr();
  }

  throw FlutterError(
    'AppLocalizations.delegate failed to load unsupported locale "$locale". This is likely '
    'an issue with the localizations generation tool. Please file an issue '
    'on GitHub with a reproducible sample app and the gen-l10n configuration '
    'that was used.',
  );
}
