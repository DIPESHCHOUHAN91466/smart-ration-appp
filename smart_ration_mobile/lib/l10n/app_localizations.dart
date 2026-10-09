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

  /// No description provided for @demoAccountsPublicTitle.
  ///
  /// In en, this message translates to:
  /// **'Try a demo account'**
  String get demoAccountsPublicTitle;

  /// Login screen of a public demo build.
  ///
  /// In en, this message translates to:
  /// **'Tap a role to fill in its email and password. Demo password: {password}. Demo accounts hold sample data only.'**
  String demoAccountsPublicHelp(String password);

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

  /// No description provided for @bookRation.
  ///
  /// In en, this message translates to:
  /// **'Book ration'**
  String get bookRation;

  /// No description provided for @chooseShopTitle.
  ///
  /// In en, this message translates to:
  /// **'Choose your ration shop'**
  String get chooseShopTitle;

  /// No description provided for @chooseShopLabel.
  ///
  /// In en, this message translates to:
  /// **'Ration shop'**
  String get chooseShopLabel;

  /// No description provided for @stepDay.
  ///
  /// In en, this message translates to:
  /// **'1. Choose a day'**
  String get stepDay;

  /// No description provided for @stepTime.
  ///
  /// In en, this message translates to:
  /// **'2. Choose a 5-minute time'**
  String get stepTime;

  /// No description provided for @stepItems.
  ///
  /// In en, this message translates to:
  /// **'3. Choose items'**
  String get stepItems;

  /// No description provided for @today.
  ///
  /// In en, this message translates to:
  /// **'Today'**
  String get today;

  /// No description provided for @tomorrow.
  ///
  /// In en, this message translates to:
  /// **'Tomorrow'**
  String get tomorrow;

  /// No description provided for @noSlots.
  ///
  /// In en, this message translates to:
  /// **'No times are open on this day. Please choose another day.'**
  String get noSlots;

  /// No description provided for @slotFull.
  ///
  /// In en, this message translates to:
  /// **'Full'**
  String get slotFull;

  /// No description provided for @placesLeft.
  ///
  /// In en, this message translates to:
  /// **'{count} left'**
  String placesLeft(int count);

  /// No description provided for @perVisitLimit.
  ///
  /// In en, this message translates to:
  /// **'Up to {amount} {unit} this visit'**
  String perVisitLimit(String amount, String unit);

  /// No description provided for @notAvailableNow.
  ///
  /// In en, this message translates to:
  /// **'Not available now'**
  String get notAvailableNow;

  /// Screen-reader label of the + button.
  ///
  /// In en, this message translates to:
  /// **'More {item}'**
  String increaseItem(String item);

  /// Screen-reader label of the - button.
  ///
  /// In en, this message translates to:
  /// **'Less {item}'**
  String decreaseItem(String item);

  /// No description provided for @bookAndGetToken.
  ///
  /// In en, this message translates to:
  /// **'Book and get token'**
  String get bookAndGetToken;

  /// No description provided for @bookingInProgress.
  ///
  /// In en, this message translates to:
  /// **'Booking...'**
  String get bookingInProgress;

  /// No description provided for @chooseTimeFirst.
  ///
  /// In en, this message translates to:
  /// **'Please choose a time.'**
  String get chooseTimeFirst;

  /// No description provided for @chooseItemFirst.
  ///
  /// In en, this message translates to:
  /// **'Please choose at least one item.'**
  String get chooseItemFirst;

  /// No description provided for @noShopAssigned.
  ///
  /// In en, this message translates to:
  /// **'Your ration shop is not set yet. Please contact your district office.'**
  String get noShopAssigned;

  /// No description provided for @tokenReady.
  ///
  /// In en, this message translates to:
  /// **'Your token is ready.'**
  String get tokenReady;

  /// No description provided for @myToken.
  ///
  /// In en, this message translates to:
  /// **'My token'**
  String get myToken;

  /// No description provided for @myTokens.
  ///
  /// In en, this message translates to:
  /// **'My tokens'**
  String get myTokens;

  /// No description provided for @tokenNumber.
  ///
  /// In en, this message translates to:
  /// **'Token number'**
  String get tokenNumber;

  /// No description provided for @collectionDate.
  ///
  /// In en, this message translates to:
  /// **'Date'**
  String get collectionDate;

  /// No description provided for @collectionTime.
  ///
  /// In en, this message translates to:
  /// **'Time'**
  String get collectionTime;

  /// No description provided for @tokenItems.
  ///
  /// In en, this message translates to:
  /// **'Items'**
  String get tokenItems;

  /// No description provided for @stateBooked.
  ///
  /// In en, this message translates to:
  /// **'Booked'**
  String get stateBooked;

  /// No description provided for @stateCollected.
  ///
  /// In en, this message translates to:
  /// **'Collected'**
  String get stateCollected;

  /// No description provided for @stateCancelled.
  ///
  /// In en, this message translates to:
  /// **'Cancelled'**
  String get stateCancelled;

  /// No description provided for @stateMissed.
  ///
  /// In en, this message translates to:
  /// **'Missed'**
  String get stateMissed;

  /// No description provided for @showQrAtShop.
  ///
  /// In en, this message translates to:
  /// **'Show this QR code at the ration shop.'**
  String get showQrAtShop;

  /// No description provided for @qrManualCode.
  ///
  /// In en, this message translates to:
  /// **'If the QR cannot be scanned, the shop can type this code:'**
  String get qrManualCode;

  /// No description provided for @qrNoPersonalData.
  ///
  /// In en, this message translates to:
  /// **'The QR code holds no personal details.'**
  String get qrNoPersonalData;

  /// Screen-reader label of the QR image.
  ///
  /// In en, this message translates to:
  /// **'QR code for token {number}'**
  String qrCodeLabel(String number);

  /// No description provided for @cancelBooking.
  ///
  /// In en, this message translates to:
  /// **'Cancel booking'**
  String get cancelBooking;

  /// No description provided for @cancelConfirmTitle.
  ///
  /// In en, this message translates to:
  /// **'Cancel this booking?'**
  String get cancelConfirmTitle;

  /// No description provided for @cancelConfirmBody.
  ///
  /// In en, this message translates to:
  /// **'Your time will be freed for someone else.'**
  String get cancelConfirmBody;

  /// No description provided for @keepBooking.
  ///
  /// In en, this message translates to:
  /// **'Keep it'**
  String get keepBooking;

  /// No description provided for @bookingCancelled.
  ///
  /// In en, this message translates to:
  /// **'Booking cancelled.'**
  String get bookingCancelled;

  /// No description provided for @noTokens.
  ///
  /// In en, this message translates to:
  /// **'You have no tokens yet.'**
  String get noTokens;

  /// No description provided for @nextCollection.
  ///
  /// In en, this message translates to:
  /// **'Your next collection'**
  String get nextCollection;

  /// No description provided for @noUpcomingBooking.
  ///
  /// In en, this message translates to:
  /// **'No upcoming booking. Book a time to collect your ration.'**
  String get noUpcomingBooking;

  /// No description provided for @showQr.
  ///
  /// In en, this message translates to:
  /// **'Show QR code'**
  String get showQr;

  /// No description provided for @allMyTokens.
  ///
  /// In en, this message translates to:
  /// **'All my tokens'**
  String get allMyTokens;

  /// No description provided for @shopTodayTitle.
  ///
  /// In en, this message translates to:
  /// **'Today at your shop'**
  String get shopTodayTitle;

  /// No description provided for @shopTokensToday.
  ///
  /// In en, this message translates to:
  /// **'Tokens'**
  String get shopTokensToday;

  /// No description provided for @shopCollected.
  ///
  /// In en, this message translates to:
  /// **'Collected'**
  String get shopCollected;

  /// No description provided for @shopWaiting.
  ///
  /// In en, this message translates to:
  /// **'Waiting'**
  String get shopWaiting;

  /// No description provided for @shopCancelled.
  ///
  /// In en, this message translates to:
  /// **'Cancelled'**
  String get shopCancelled;

  /// No description provided for @scanCustomerQr.
  ///
  /// In en, this message translates to:
  /// **'Scan customer\'s QR'**
  String get scanCustomerQr;

  /// No description provided for @verifyByMobile.
  ///
  /// In en, this message translates to:
  /// **'No QR? Verify with mobile code'**
  String get verifyByMobile;

  /// No description provided for @scannerTitle.
  ///
  /// In en, this message translates to:
  /// **'Scan QR code'**
  String get scannerTitle;

  /// No description provided for @scannerHelp.
  ///
  /// In en, this message translates to:
  /// **'Point the camera at the customer\'s QR code.'**
  String get scannerHelp;

  /// No description provided for @typeCodeLabel.
  ///
  /// In en, this message translates to:
  /// **'Or type the code shown under the QR'**
  String get typeCodeLabel;

  /// No description provided for @typeCodeInvalid.
  ///
  /// In en, this message translates to:
  /// **'Please type the code that starts with SRQR-.'**
  String get typeCodeInvalid;

  /// No description provided for @checkCode.
  ///
  /// In en, this message translates to:
  /// **'Check'**
  String get checkCode;

  /// No description provided for @checking.
  ///
  /// In en, this message translates to:
  /// **'Checking…'**
  String get checking;

  /// No description provided for @cameraDenied.
  ///
  /// In en, this message translates to:
  /// **'Camera permission is off. Allow it in the phone\'s Settings, or type the code below.'**
  String get cameraDenied;

  /// No description provided for @cameraUnavailable.
  ///
  /// In en, this message translates to:
  /// **'The camera could not start. Type the code below instead.'**
  String get cameraUnavailable;

  /// No description provided for @scanRejectedTitle.
  ///
  /// In en, this message translates to:
  /// **'Cannot accept this token'**
  String get scanRejectedTitle;

  /// No description provided for @scanInvalidSignature.
  ///
  /// In en, this message translates to:
  /// **'This QR code is not genuine. Do not hand over ration.'**
  String get scanInvalidSignature;

  /// No description provided for @scanNotOurs.
  ///
  /// In en, this message translates to:
  /// **'This is not a Smart Ration token QR code.'**
  String get scanNotOurs;

  /// No description provided for @scanUnreadable.
  ///
  /// In en, this message translates to:
  /// **'The QR code could not be read. Scan again or type the code.'**
  String get scanUnreadable;

  /// No description provided for @scanExpired.
  ///
  /// In en, this message translates to:
  /// **'This token\'s collection day has passed.'**
  String get scanExpired;

  /// No description provided for @scanNoBooking.
  ///
  /// In en, this message translates to:
  /// **'No booking matches this code.'**
  String get scanNoBooking;

  /// No description provided for @scanWrongShop.
  ///
  /// In en, this message translates to:
  /// **'This token is for a different ration shop.'**
  String get scanWrongShop;

  /// No description provided for @scanAlreadyCollected.
  ///
  /// In en, this message translates to:
  /// **'This token has already been used to collect ration.'**
  String get scanAlreadyCollected;

  /// No description provided for @scanBookingCancelled.
  ///
  /// In en, this message translates to:
  /// **'This booking was cancelled.'**
  String get scanBookingCancelled;

  /// No description provided for @scanAgain.
  ///
  /// In en, this message translates to:
  /// **'Scan again'**
  String get scanAgain;

  /// No description provided for @checkTitle.
  ///
  /// In en, this message translates to:
  /// **'Customer check'**
  String get checkTitle;

  /// No description provided for @readyTitle.
  ///
  /// In en, this message translates to:
  /// **'Ready to collect'**
  String get readyTitle;

  /// No description provided for @readyBody.
  ///
  /// In en, this message translates to:
  /// **'All checks passed. Hand over the items below.'**
  String get readyBody;

  /// No description provided for @blockedTitle.
  ///
  /// In en, this message translates to:
  /// **'Do not hand over ration'**
  String get blockedTitle;

  /// No description provided for @identifiedByQr.
  ///
  /// In en, this message translates to:
  /// **'Identified by QR code'**
  String get identifiedByQr;

  /// No description provided for @identifiedByOtp.
  ///
  /// In en, this message translates to:
  /// **'Identified by mobile code'**
  String get identifiedByOtp;

  /// No description provided for @customer.
  ///
  /// In en, this message translates to:
  /// **'Customer'**
  String get customer;

  /// No description provided for @beneficiaryId.
  ///
  /// In en, this message translates to:
  /// **'Beneficiary ID'**
  String get beneficiaryId;

  /// No description provided for @registeredMobile.
  ///
  /// In en, this message translates to:
  /// **'Registered mobile'**
  String get registeredMobile;

  /// No description provided for @checksTitle.
  ///
  /// In en, this message translates to:
  /// **'Checks'**
  String get checksTitle;

  /// No description provided for @checkAadhaar.
  ///
  /// In en, this message translates to:
  /// **'Aadhaar verified'**
  String get checkAadhaar;

  /// No description provided for @checkPassbook.
  ///
  /// In en, this message translates to:
  /// **'Passbook verified'**
  String get checkPassbook;

  /// No description provided for @checkMobile.
  ///
  /// In en, this message translates to:
  /// **'Mobile number verified'**
  String get checkMobile;

  /// No description provided for @checkToken.
  ///
  /// In en, this message translates to:
  /// **'Token valid for collection'**
  String get checkToken;

  /// No description provided for @checkFamily.
  ///
  /// In en, this message translates to:
  /// **'Family eligible'**
  String get checkFamily;

  /// No description provided for @checkEntitlement.
  ///
  /// In en, this message translates to:
  /// **'Ration left this month'**
  String get checkEntitlement;

  /// No description provided for @checkPassed.
  ///
  /// In en, this message translates to:
  /// **'Yes'**
  String get checkPassed;

  /// No description provided for @checkFailed.
  ///
  /// In en, this message translates to:
  /// **'No'**
  String get checkFailed;

  /// No description provided for @itemsToHandOver.
  ///
  /// In en, this message translates to:
  /// **'Items to hand over'**
  String get itemsToHandOver;

  /// No description provided for @handOverButton.
  ///
  /// In en, this message translates to:
  /// **'Hand over and confirm'**
  String get handOverButton;

  /// No description provided for @handOverConfirmTitle.
  ///
  /// In en, this message translates to:
  /// **'Confirm handover?'**
  String get handOverConfirmTitle;

  /// Asked before the handover is saved.
  ///
  /// In en, this message translates to:
  /// **'Confirm only after you have given these items to {name}. Your stock will be reduced.'**
  String handOverConfirmBody(String name);

  /// No description provided for @notYet.
  ///
  /// In en, this message translates to:
  /// **'Not yet'**
  String get notYet;

  /// No description provided for @yesHandedOver.
  ///
  /// In en, this message translates to:
  /// **'Yes, handed over'**
  String get yesHandedOver;

  /// No description provided for @saving.
  ///
  /// In en, this message translates to:
  /// **'Saving…'**
  String get saving;

  /// No description provided for @errorInsufficientStock.
  ///
  /// In en, this message translates to:
  /// **'Not enough stock for this token. Nothing was handed over or deducted.'**
  String get errorInsufficientStock;

  /// No description provided for @errorConcurrentUpdate.
  ///
  /// In en, this message translates to:
  /// **'This token was just updated at another counter. Please scan it again.'**
  String get errorConcurrentUpdate;

  /// No description provided for @reasonAccountBlocked.
  ///
  /// In en, this message translates to:
  /// **'This beneficiary account is blocked.'**
  String get reasonAccountBlocked;

  /// No description provided for @reasonAccountInactive.
  ///
  /// In en, this message translates to:
  /// **'This beneficiary account is not active.'**
  String get reasonAccountInactive;

  /// No description provided for @reasonTokenInvalid.
  ///
  /// In en, this message translates to:
  /// **'This token is not valid for collection.'**
  String get reasonTokenInvalid;

  /// No description provided for @reasonAadhaarFailed.
  ///
  /// In en, this message translates to:
  /// **'Aadhaar verification failed.'**
  String get reasonAadhaarFailed;

  /// No description provided for @reasonAadhaarExpired.
  ///
  /// In en, this message translates to:
  /// **'Aadhaar verification has expired.'**
  String get reasonAadhaarExpired;

  /// No description provided for @reasonAadhaarPending.
  ///
  /// In en, this message translates to:
  /// **'Aadhaar verification is pending.'**
  String get reasonAadhaarPending;

  /// No description provided for @reasonPassbookPending.
  ///
  /// In en, this message translates to:
  /// **'Passbook verification is pending.'**
  String get reasonPassbookPending;

  /// No description provided for @reasonMobileRequired.
  ///
  /// In en, this message translates to:
  /// **'The customer\'s mobile number must be verified first.'**
  String get reasonMobileRequired;

  /// No description provided for @reasonNotEligible.
  ///
  /// In en, this message translates to:
  /// **'This family is not eligible under its scheme.'**
  String get reasonNotEligible;

  /// No description provided for @reasonNoEntitlement.
  ///
  /// In en, this message translates to:
  /// **'No ration is left for this family this month.'**
  String get reasonNoEntitlement;

  /// No description provided for @otpCheckTitle.
  ///
  /// In en, this message translates to:
  /// **'Verify with mobile code'**
  String get otpCheckTitle;

  /// No description provided for @otpCheckHelp.
  ///
  /// In en, this message translates to:
  /// **'Type the customer\'s registered mobile number. A 6-digit code will be sent to it.'**
  String get otpCheckHelp;

  /// No description provided for @customerMobileLabel.
  ///
  /// In en, this message translates to:
  /// **'Customer\'s mobile number'**
  String get customerMobileLabel;

  /// After a code is sent to the customer's mobile.
  ///
  /// In en, this message translates to:
  /// **'Ask the customer for the code sent to {mobile}. It is valid for {minutes} minutes.'**
  String askCustomerForCode(String mobile, int minutes);

  /// No description provided for @verifyCodeButton.
  ///
  /// In en, this message translates to:
  /// **'Verify code'**
  String get verifyCodeButton;

  /// No description provided for @otpNoCustomer.
  ///
  /// In en, this message translates to:
  /// **'No customer is registered with this mobile number.'**
  String get otpNoCustomer;

  /// No description provided for @otpNoBookingHere.
  ///
  /// In en, this message translates to:
  /// **'This customer has no active booking at your shop.'**
  String get otpNoBookingHere;

  /// No description provided for @receiptTitle.
  ///
  /// In en, this message translates to:
  /// **'Ration handed over'**
  String get receiptTitle;

  /// No description provided for @receiptCollectionId.
  ///
  /// In en, this message translates to:
  /// **'Collection ID'**
  String get receiptCollectionId;

  /// No description provided for @receiptSaved.
  ///
  /// In en, this message translates to:
  /// **'Saved. Stock has been reduced and the customer has been notified.'**
  String get receiptSaved;

  /// No description provided for @scanNextCustomer.
  ///
  /// In en, this message translates to:
  /// **'Scan next customer'**
  String get scanNextCustomer;

  /// No description provided for @backToDashboard.
  ///
  /// In en, this message translates to:
  /// **'Back to dashboard'**
  String get backToDashboard;

  /// No description provided for @nothingToCheck.
  ///
  /// In en, this message translates to:
  /// **'Nothing to check. Scan a QR code first.'**
  String get nothingToCheck;

  /// No description provided for @queueButton.
  ///
  /// In en, this message translates to:
  /// **'Today\'s queue'**
  String get queueButton;

  /// No description provided for @stockButton.
  ///
  /// In en, this message translates to:
  /// **'Stock'**
  String get stockButton;

  /// On the shop dashboard.
  ///
  /// In en, this message translates to:
  /// **'{count, plural, =1{1 item is low on stock} other{{count} items are low on stock}}'**
  String lowStockBanner(int count);

  /// No description provided for @queueWaitingHeader.
  ///
  /// In en, this message translates to:
  /// **'Waiting ({count})'**
  String queueWaitingHeader(int count);

  /// No description provided for @queueDoneHeader.
  ///
  /// In en, this message translates to:
  /// **'Done ({count})'**
  String queueDoneHeader(int count);

  /// No description provided for @queueEmpty.
  ///
  /// In en, this message translates to:
  /// **'No tokens booked for today.'**
  String get queueEmpty;

  /// No description provided for @queueServeHint.
  ///
  /// In en, this message translates to:
  /// **'When this customer arrives, scan their QR or verify by mobile code.'**
  String get queueServeHint;

  /// No description provided for @stockAvailable.
  ///
  /// In en, this message translates to:
  /// **'In stock'**
  String get stockAvailable;

  /// No description provided for @stockMinimum.
  ///
  /// In en, this message translates to:
  /// **'Minimum level'**
  String get stockMinimum;

  /// No description provided for @stockHandedOut.
  ///
  /// In en, this message translates to:
  /// **'Handed out'**
  String get stockHandedOut;

  /// No description provided for @stockLow.
  ///
  /// In en, this message translates to:
  /// **'Low'**
  String get stockLow;

  /// No description provided for @stockOk.
  ///
  /// In en, this message translates to:
  /// **'OK'**
  String get stockOk;

  /// No description provided for @noStockLines.
  ///
  /// In en, this message translates to:
  /// **'No stock lines for this shop yet.'**
  String get noStockLines;

  /// No description provided for @receiveStock.
  ///
  /// In en, this message translates to:
  /// **'Record delivery'**
  String get receiveStock;

  /// No description provided for @writeOffStock.
  ///
  /// In en, this message translates to:
  /// **'Write off damaged'**
  String get writeOffStock;

  /// No description provided for @quantityLabel.
  ///
  /// In en, this message translates to:
  /// **'Quantity ({unit})'**
  String quantityLabel(String unit);

  /// No description provided for @referenceLabel.
  ///
  /// In en, this message translates to:
  /// **'Delivery or report number (optional)'**
  String get referenceLabel;

  /// No description provided for @noteLabel.
  ///
  /// In en, this message translates to:
  /// **'Note (optional)'**
  String get noteLabel;

  /// No description provided for @stockAlreadySaved.
  ///
  /// In en, this message translates to:
  /// **'This was already saved a moment ago. Close this form and check the stock before entering it again.'**
  String get stockAlreadySaved;

  /// No description provided for @quantityInvalid.
  ///
  /// In en, this message translates to:
  /// **'Enter a quantity greater than 0.'**
  String get quantityInvalid;

  /// No description provided for @quantityTooLarge.
  ///
  /// In en, this message translates to:
  /// **'Enter a quantity up to 1,000,000.'**
  String get quantityTooLarge;

  /// No description provided for @writeOffTooMuch.
  ///
  /// In en, this message translates to:
  /// **'You can write off at most {max} {unit}.'**
  String writeOffTooMuch(String max, String unit);

  /// No description provided for @referenceInvalid.
  ///
  /// In en, this message translates to:
  /// **'Use only letters, numbers, spaces and - / _ .'**
  String get referenceInvalid;

  /// No description provided for @saveButton.
  ///
  /// In en, this message translates to:
  /// **'Save'**
  String get saveButton;

  /// No description provided for @cancelButton.
  ///
  /// In en, this message translates to:
  /// **'Cancel'**
  String get cancelButton;

  /// e.g. 'Write off 2 kg Rice?'
  ///
  /// In en, this message translates to:
  /// **'Write off {amount}?'**
  String writeOffConfirmTitle(String amount);

  /// No description provided for @writeOffConfirmBody.
  ///
  /// In en, this message translates to:
  /// **'This removes damaged stock for good. It is recorded in the stock ledger.'**
  String get writeOffConfirmBody;

  /// No description provided for @stockReceived.
  ///
  /// In en, this message translates to:
  /// **'Delivery recorded.'**
  String get stockReceived;

  /// No description provided for @stockWrittenOff.
  ///
  /// In en, this message translates to:
  /// **'Damaged stock written off.'**
  String get stockWrittenOff;

  /// No description provided for @officialTodayTitle.
  ///
  /// In en, this message translates to:
  /// **'Today across all shops'**
  String get officialTodayTitle;

  /// No description provided for @statShops.
  ///
  /// In en, this message translates to:
  /// **'Shops'**
  String get statShops;

  /// No description provided for @statBeneficiaries.
  ///
  /// In en, this message translates to:
  /// **'Beneficiaries'**
  String get statBeneficiaries;

  /// No description provided for @statBookings.
  ///
  /// In en, this message translates to:
  /// **'Bookings'**
  String get statBookings;

  /// No description provided for @statHandedOutToday.
  ///
  /// In en, this message translates to:
  /// **'Handed out today'**
  String get statHandedOutToday;

  /// No description provided for @statLowStockAlerts.
  ///
  /// In en, this message translates to:
  /// **'Low-stock items'**
  String get statLowStockAlerts;

  /// No description provided for @periodTitle.
  ///
  /// In en, this message translates to:
  /// **'Last 30 days'**
  String get periodTitle;

  /// No description provided for @statTokensBooked.
  ///
  /// In en, this message translates to:
  /// **'Tokens booked'**
  String get statTokensBooked;

  /// No description provided for @collectionRateLabel.
  ///
  /// In en, this message translates to:
  /// **'Collection rate'**
  String get collectionRateLabel;

  /// No description provided for @collectionRateValue.
  ///
  /// In en, this message translates to:
  /// **'{percent}% of booked tokens were collected'**
  String collectionRateValue(String percent);

  /// No description provided for @alertsButton.
  ///
  /// In en, this message translates to:
  /// **'Alerts ({count})'**
  String alertsButton(int count);

  /// No description provided for @alertsTitle.
  ///
  /// In en, this message translates to:
  /// **'Alerts'**
  String get alertsTitle;

  /// No description provided for @filterAll.
  ///
  /// In en, this message translates to:
  /// **'All'**
  String get filterAll;

  /// No description provided for @stockCritical.
  ///
  /// In en, this message translates to:
  /// **'Critical'**
  String get stockCritical;

  /// No description provided for @shopTodayLine.
  ///
  /// In en, this message translates to:
  /// **'Today: {booked} booked · {collected} collected'**
  String shopTodayLine(int booked, int collected);

  /// No description provided for @shopOwnerLabel.
  ///
  /// In en, this message translates to:
  /// **'Shop owner'**
  String get shopOwnerLabel;

  /// No description provided for @shopPlaceLabel.
  ///
  /// In en, this message translates to:
  /// **'Place'**
  String get shopPlaceLabel;

  /// No description provided for @shopCodeLabel.
  ///
  /// In en, this message translates to:
  /// **'Shop code'**
  String get shopCodeLabel;

  /// No description provided for @noShops.
  ///
  /// In en, this message translates to:
  /// **'No shops found.'**
  String get noShops;

  /// No description provided for @alertsNotice.
  ///
  /// In en, this message translates to:
  /// **'These are warnings to review, not proof of fraud. Check before acting.'**
  String get alertsNotice;

  /// No description provided for @noAlerts.
  ///
  /// In en, this message translates to:
  /// **'No open alerts.'**
  String get noAlerts;

  /// No description provided for @severityHigh.
  ///
  /// In en, this message translates to:
  /// **'High'**
  String get severityHigh;

  /// No description provided for @severityMedium.
  ///
  /// In en, this message translates to:
  /// **'Medium'**
  String get severityMedium;

  /// No description provided for @severityLow.
  ///
  /// In en, this message translates to:
  /// **'Low'**
  String get severityLow;

  /// No description provided for @alertDuplicateCollection.
  ///
  /// In en, this message translates to:
  /// **'Repeated collection attempts'**
  String get alertDuplicateCollection;

  /// No description provided for @alertRepeatedQrScan.
  ///
  /// In en, this message translates to:
  /// **'Same QR scanned many times'**
  String get alertRepeatedQrScan;

  /// No description provided for @alertFailedVerification.
  ///
  /// In en, this message translates to:
  /// **'Repeated failed checks'**
  String get alertFailedVerification;

  /// No description provided for @alertLowStock.
  ///
  /// In en, this message translates to:
  /// **'Low stock'**
  String get alertLowStock;

  /// No description provided for @alertUnusualConsumption.
  ///
  /// In en, this message translates to:
  /// **'Unusual consumption'**
  String get alertUnusualConsumption;

  /// No description provided for @alertDetailsInEnglish.
  ///
  /// In en, this message translates to:
  /// **'Details from the system (English):'**
  String get alertDetailsInEnglish;

  /// No description provided for @alertUpdateButton.
  ///
  /// In en, this message translates to:
  /// **'Update'**
  String get alertUpdateButton;

  /// No description provided for @alertUpdateTitle.
  ///
  /// In en, this message translates to:
  /// **'Update this alert'**
  String get alertUpdateTitle;

  /// No description provided for @alertStatusUnderReview.
  ///
  /// In en, this message translates to:
  /// **'Under review'**
  String get alertStatusUnderReview;

  /// No description provided for @alertChooseReviewHint.
  ///
  /// In en, this message translates to:
  /// **'You are checking it. It stays on the list.'**
  String get alertChooseReviewHint;

  /// No description provided for @alertChooseResolved.
  ///
  /// In en, this message translates to:
  /// **'Resolved'**
  String get alertChooseResolved;

  /// No description provided for @alertChooseResolvedHint.
  ///
  /// In en, this message translates to:
  /// **'There was a problem and it has been dealt with.'**
  String get alertChooseResolvedHint;

  /// No description provided for @alertChooseDismissed.
  ///
  /// In en, this message translates to:
  /// **'Not a problem'**
  String get alertChooseDismissed;

  /// No description provided for @alertChooseDismissedHint.
  ///
  /// In en, this message translates to:
  /// **'Checked: nothing was wrong.'**
  String get alertChooseDismissedHint;

  /// No description provided for @alertNoteHint.
  ///
  /// In en, this message translates to:
  /// **'Do not write Aadhaar numbers, OTPs or passwords.'**
  String get alertNoteHint;

  /// No description provided for @alertReviewNote.
  ///
  /// In en, this message translates to:
  /// **'Official\'s note'**
  String get alertReviewNote;

  /// No description provided for @alertUpdated.
  ///
  /// In en, this message translates to:
  /// **'Alert updated'**
  String get alertUpdated;

  /// No description provided for @helpTitle.
  ///
  /// In en, this message translates to:
  /// **'Help — Ration Mitra'**
  String get helpTitle;

  /// No description provided for @helpButton.
  ///
  /// In en, this message translates to:
  /// **'Help'**
  String get helpButton;

  /// No description provided for @assistantName.
  ///
  /// In en, this message translates to:
  /// **'Ration Mitra'**
  String get assistantName;

  /// No description provided for @youLabel.
  ///
  /// In en, this message translates to:
  /// **'You'**
  String get youLabel;

  /// No description provided for @helpPrivacy.
  ///
  /// In en, this message translates to:
  /// **'Don\'t type Aadhaar numbers, OTPs or passwords. Nothing you type is saved on this phone.'**
  String get helpPrivacy;

  /// No description provided for @askHint.
  ///
  /// In en, this message translates to:
  /// **'Type your question'**
  String get askHint;

  /// No description provided for @sendQuestion.
  ///
  /// In en, this message translates to:
  /// **'Send'**
  String get sendQuestion;

  /// No description provided for @speakQuestion.
  ///
  /// In en, this message translates to:
  /// **'Ask by voice'**
  String get speakQuestion;

  /// No description provided for @stopListening.
  ///
  /// In en, this message translates to:
  /// **'Stop listening'**
  String get stopListening;

  /// No description provided for @listening.
  ///
  /// In en, this message translates to:
  /// **'Listening… speak now'**
  String get listening;

  /// No description provided for @voiceNote.
  ///
  /// In en, this message translates to:
  /// **'Your phone\'s speech service turns your voice into text and may use the internet to do so.'**
  String get voiceNote;

  /// No description provided for @voiceUnavailable.
  ///
  /// In en, this message translates to:
  /// **'Voice input is not available. Allow the microphone in Settings, or type your question.'**
  String get voiceUnavailable;

  /// No description provided for @readAloud.
  ///
  /// In en, this message translates to:
  /// **'Read aloud'**
  String get readAloud;

  /// No description provided for @stopReading.
  ///
  /// In en, this message translates to:
  /// **'Stop reading'**
  String get stopReading;

  /// No description provided for @voiceMissing.
  ///
  /// In en, this message translates to:
  /// **'This phone has no voice for this language. You can add one in the phone\'s text-to-speech settings.'**
  String get voiceMissing;

  /// No description provided for @relatedTitle.
  ///
  /// In en, this message translates to:
  /// **'Related'**
  String get relatedTitle;

  /// No description provided for @thinking.
  ///
  /// In en, this message translates to:
  /// **'Ration Mitra is typing…'**
  String get thinking;

  /// No description provided for @noSpeechHeard.
  ///
  /// In en, this message translates to:
  /// **'I didn\'t hear anything. Tap the mic and try again.'**
  String get noSpeechHeard;

  /// No description provided for @offlineBanner.
  ///
  /// In en, this message translates to:
  /// **'No internet. Showing what was saved on this phone; it may be out of date. Pull down to refresh.'**
  String get offlineBanner;

  /// No description provided for @offlineQrNote.
  ///
  /// In en, this message translates to:
  /// **'Saved on this phone. The shop can still scan this QR without your internet.'**
  String get offlineQrNote;

  /// No description provided for @notificationsTitle.
  ///
  /// In en, this message translates to:
  /// **'Notifications'**
  String get notificationsTitle;

  /// Tooltip / screen-reader label of the bell.
  ///
  /// In en, this message translates to:
  /// **'{count, plural, =0{Notifications} =1{Notifications, 1 new} other{Notifications, {count} new}}'**
  String notificationsTooltip(int count);

  /// No description provided for @noNotifications.
  ///
  /// In en, this message translates to:
  /// **'No notifications yet.'**
  String get noNotifications;

  /// No description provided for @newLabel.
  ///
  /// In en, this message translates to:
  /// **'New'**
  String get newLabel;

  /// No description provided for @nBookingConfirmed.
  ///
  /// In en, this message translates to:
  /// **'Booking confirmed'**
  String get nBookingConfirmed;

  /// No description provided for @nTokenGenerated.
  ///
  /// In en, this message translates to:
  /// **'Token ready'**
  String get nTokenGenerated;

  /// No description provided for @nSlotReminder.
  ///
  /// In en, this message translates to:
  /// **'Reminder: your collection time'**
  String get nSlotReminder;

  /// No description provided for @nCollectionCompleted.
  ///
  /// In en, this message translates to:
  /// **'Ration collected'**
  String get nCollectionCompleted;

  /// No description provided for @nBookingCancelled.
  ///
  /// In en, this message translates to:
  /// **'Booking cancelled'**
  String get nBookingCancelled;

  /// No description provided for @nLowInventory.
  ///
  /// In en, this message translates to:
  /// **'Low stock'**
  String get nLowInventory;

  /// No description provided for @nVerificationResult.
  ///
  /// In en, this message translates to:
  /// **'Verification result'**
  String get nVerificationResult;

  /// No description provided for @nAlert.
  ///
  /// In en, this message translates to:
  /// **'Alert'**
  String get nAlert;

  /// No description provided for @complaintTitle.
  ///
  /// In en, this message translates to:
  /// **'Report a problem'**
  String get complaintTitle;

  /// No description provided for @complaintWhat.
  ///
  /// In en, this message translates to:
  /// **'What is the problem?'**
  String get complaintWhat;

  /// No description provided for @catLessRation.
  ///
  /// In en, this message translates to:
  /// **'Got less ration'**
  String get catLessRation;

  /// No description provided for @catPoorQuality.
  ///
  /// In en, this message translates to:
  /// **'Bad quality grain'**
  String get catPoorQuality;

  /// No description provided for @catShopClosed.
  ///
  /// In en, this message translates to:
  /// **'Shop was closed'**
  String get catShopClosed;

  /// No description provided for @catOvercharged.
  ///
  /// In en, this message translates to:
  /// **'Asked for extra money'**
  String get catOvercharged;

  /// No description provided for @catTokenProblem.
  ///
  /// In en, this message translates to:
  /// **'Token or QR problem'**
  String get catTokenProblem;

  /// No description provided for @catVerificationProblem.
  ///
  /// In en, this message translates to:
  /// **'Identity check problem'**
  String get catVerificationProblem;

  /// No description provided for @catStaffBehaviour.
  ///
  /// In en, this message translates to:
  /// **'Rude behaviour'**
  String get catStaffBehaviour;

  /// No description provided for @catOther.
  ///
  /// In en, this message translates to:
  /// **'Something else'**
  String get catOther;

  /// No description provided for @complaintItem.
  ///
  /// In en, this message translates to:
  /// **'Which item? (optional)'**
  String get complaintItem;

  /// No description provided for @complaintNoItem.
  ///
  /// In en, this message translates to:
  /// **'Not one item'**
  String get complaintNoItem;

  /// No description provided for @complaintDescribe.
  ///
  /// In en, this message translates to:
  /// **'Tell us what happened'**
  String get complaintDescribe;

  /// No description provided for @complaintDescribeHint.
  ///
  /// In en, this message translates to:
  /// **'For example: This month I got 2 kg less wheat.'**
  String get complaintDescribeHint;

  /// No description provided for @complaintDescribeShort.
  ///
  /// In en, this message translates to:
  /// **'Please write a little more (at least 10 letters).'**
  String get complaintDescribeShort;

  /// No description provided for @complaintNoPrivate.
  ///
  /// In en, this message translates to:
  /// **'Do not write Aadhaar numbers, OTPs or passwords.'**
  String get complaintNoPrivate;

  /// No description provided for @complaintChooseCategory.
  ///
  /// In en, this message translates to:
  /// **'Choose what the problem is.'**
  String get complaintChooseCategory;

  /// No description provided for @complaintYourDetails.
  ///
  /// In en, this message translates to:
  /// **'Your details (from your account)'**
  String get complaintYourDetails;

  /// No description provided for @complaintNameLabel.
  ///
  /// In en, this message translates to:
  /// **'Name'**
  String get complaintNameLabel;

  /// No description provided for @complaintReviewButton.
  ///
  /// In en, this message translates to:
  /// **'Review'**
  String get complaintReviewButton;

  /// No description provided for @complaintReviewTitle.
  ///
  /// In en, this message translates to:
  /// **'Check before sending'**
  String get complaintReviewTitle;

  /// No description provided for @complaintReviewNote.
  ///
  /// In en, this message translates to:
  /// **'Please review your information before submitting.'**
  String get complaintReviewNote;

  /// No description provided for @complaintEdit.
  ///
  /// In en, this message translates to:
  /// **'Change'**
  String get complaintEdit;

  /// No description provided for @complaintSubmit.
  ///
  /// In en, this message translates to:
  /// **'Confirm and send'**
  String get complaintSubmit;

  /// No description provided for @complaintSent.
  ///
  /// In en, this message translates to:
  /// **'Complaint registered'**
  String get complaintSent;

  /// No description provided for @complaintReference.
  ///
  /// In en, this message translates to:
  /// **'Reference number'**
  String get complaintReference;

  /// No description provided for @complaintSentSpoken.
  ///
  /// In en, this message translates to:
  /// **'Your complaint has been registered. Your reference number is {reference}.'**
  String complaintSentSpoken(String reference);

  /// No description provided for @complaintKeepReference.
  ///
  /// In en, this message translates to:
  /// **'Keep this number. You will be told in Notifications when the status changes.'**
  String get complaintKeepReference;

  /// No description provided for @complaintFilledByAi.
  ///
  /// In en, this message translates to:
  /// **'Filled in from what you said. Please check it.'**
  String get complaintFilledByAi;

  /// No description provided for @myComplaints.
  ///
  /// In en, this message translates to:
  /// **'My complaints'**
  String get myComplaints;

  /// No description provided for @noComplaints.
  ///
  /// In en, this message translates to:
  /// **'You have not reported any problem.'**
  String get noComplaints;

  /// No description provided for @complaintStatusSubmitted.
  ///
  /// In en, this message translates to:
  /// **'Received'**
  String get complaintStatusSubmitted;

  /// No description provided for @complaintStatusUnderReview.
  ///
  /// In en, this message translates to:
  /// **'Being checked'**
  String get complaintStatusUnderReview;

  /// No description provided for @complaintStatusResolved.
  ///
  /// In en, this message translates to:
  /// **'Resolved'**
  String get complaintStatusResolved;

  /// No description provided for @complaintStatusRejected.
  ///
  /// In en, this message translates to:
  /// **'Closed'**
  String get complaintStatusRejected;

  /// No description provided for @complaintOfficeReply.
  ///
  /// In en, this message translates to:
  /// **'Reply from the office'**
  String get complaintOfficeReply;

  /// No description provided for @doneButton.
  ///
  /// In en, this message translates to:
  /// **'Done'**
  String get doneButton;

  /// No description provided for @nComplaint.
  ///
  /// In en, this message translates to:
  /// **'Complaint'**
  String get nComplaint;

  /// No description provided for @aiButton.
  ///
  /// In en, this message translates to:
  /// **'Ask AI'**
  String get aiButton;

  /// No description provided for @aiHowCanIHelp.
  ///
  /// In en, this message translates to:
  /// **'How can I help you?'**
  String get aiHowCanIHelp;

  /// No description provided for @aiTypeHint.
  ///
  /// In en, this message translates to:
  /// **'Say or type what you need'**
  String get aiTypeHint;

  /// No description provided for @aiExample.
  ///
  /// In en, this message translates to:
  /// **'For example: “When will I get my ration?” or “I got less wheat, I want to complain.”'**
  String get aiExample;

  /// No description provided for @aiReadScreen.
  ///
  /// In en, this message translates to:
  /// **'Read this screen'**
  String get aiReadScreen;

  /// No description provided for @aiNothingToRead.
  ///
  /// In en, this message translates to:
  /// **'There is nothing to read on this screen yet.'**
  String get aiNothingToRead;

  /// No description provided for @aiLanguageChanged.
  ///
  /// In en, this message translates to:
  /// **'Language changed.'**
  String get aiLanguageChanged;

  /// No description provided for @aiHomeSummary.
  ///
  /// In en, this message translates to:
  /// **'Your next ration collection: token {token}, {day}, {start} to {end}, at {shop}.'**
  String aiHomeSummary(
    String token,
    String day,
    String start,
    String end,
    String shop,
  );

  /// No description provided for @aiHomeNoBooking.
  ///
  /// In en, this message translates to:
  /// **'You have no ration collection booked. Say “book ration” to book one.'**
  String get aiHomeNoBooking;

  /// No description provided for @aiSignInHelp.
  ///
  /// In en, this message translates to:
  /// **'Need help signing in? Ask AI'**
  String get aiSignInHelp;

  /// No description provided for @nAnnouncement.
  ///
  /// In en, this message translates to:
  /// **'Announcement'**
  String get nAnnouncement;

  /// No description provided for @mfaPrompt.
  ///
  /// In en, this message translates to:
  /// **'Two-factor sign-in is on for this account. Enter the 6-digit code from your authenticator app.'**
  String get mfaPrompt;

  /// No description provided for @mfaCodeLabel.
  ///
  /// In en, this message translates to:
  /// **'Code from the authenticator app'**
  String get mfaCodeLabel;

  /// No description provided for @mfaCodeWrong.
  ///
  /// In en, this message translates to:
  /// **'The code is wrong or has expired. Use the current code from your authenticator app.'**
  String get mfaCodeWrong;

  /// No description provided for @mfaExpired.
  ///
  /// In en, this message translates to:
  /// **'The sign-in took too long. Please enter your email and password again.'**
  String get mfaExpired;

  /// No description provided for @mfaStartAgain.
  ///
  /// In en, this message translates to:
  /// **'Start again'**
  String get mfaStartAgain;

  /// No description provided for @forgotPassword.
  ///
  /// In en, this message translates to:
  /// **'Forgot password?'**
  String get forgotPassword;

  /// No description provided for @resetTitle.
  ///
  /// In en, this message translates to:
  /// **'Reset your password'**
  String get resetTitle;

  /// No description provided for @resetIntro.
  ///
  /// In en, this message translates to:
  /// **'Enter the mobile number registered with your account. We will send a 6-digit code to it.'**
  String get resetIntro;

  /// No description provided for @resetCodeSent.
  ///
  /// In en, this message translates to:
  /// **'If {mobile} is registered, a 6-digit code has been sent to it.'**
  String resetCodeSent(String mobile);

  /// No description provided for @resetSendCode.
  ///
  /// In en, this message translates to:
  /// **'Send code'**
  String get resetSendCode;

  /// No description provided for @resetSetPassword.
  ///
  /// In en, this message translates to:
  /// **'Set new password'**
  String get resetSetPassword;

  /// No description provided for @resetDone.
  ///
  /// In en, this message translates to:
  /// **'Password changed. Please sign in with the new password.'**
  String get resetDone;

  /// No description provided for @newPasswordLabel.
  ///
  /// In en, this message translates to:
  /// **'New password'**
  String get newPasswordLabel;

  /// No description provided for @confirmPasswordLabel.
  ///
  /// In en, this message translates to:
  /// **'Confirm new password'**
  String get confirmPasswordLabel;

  /// No description provided for @currentPasswordLabel.
  ///
  /// In en, this message translates to:
  /// **'Current password'**
  String get currentPasswordLabel;

  /// No description provided for @passwordRules.
  ///
  /// In en, this message translates to:
  /// **'At least 12 characters. A few unrelated words work well. Do not use your name, mobile number or a common password.'**
  String get passwordRules;

  /// No description provided for @passwordTooShort.
  ///
  /// In en, this message translates to:
  /// **'Use at least 12 characters.'**
  String get passwordTooShort;

  /// No description provided for @passwordsMismatch.
  ///
  /// In en, this message translates to:
  /// **'The passwords do not match.'**
  String get passwordsMismatch;

  /// No description provided for @changePasswordTitle.
  ///
  /// In en, this message translates to:
  /// **'Change password'**
  String get changePasswordTitle;

  /// No description provided for @changePasswordButton.
  ///
  /// In en, this message translates to:
  /// **'Change password'**
  String get changePasswordButton;

  /// No description provided for @passwordChanged.
  ///
  /// In en, this message translates to:
  /// **'Password changed. Other devices have been signed out.'**
  String get passwordChanged;

  /// No description provided for @passwordChangeSignsOut.
  ///
  /// In en, this message translates to:
  /// **'Changing it signs you out on every other device.'**
  String get passwordChangeSignsOut;

  /// No description provided for @passwordChangeFailed.
  ///
  /// In en, this message translates to:
  /// **'The password could not be changed. Please try again.'**
  String get passwordChangeFailed;

  /// No description provided for @officialComplaintsTitle.
  ///
  /// In en, this message translates to:
  /// **'Citizen complaints'**
  String get officialComplaintsTitle;

  /// No description provided for @noComplaintsHere.
  ///
  /// In en, this message translates to:
  /// **'No complaints here.'**
  String get noComplaintsHere;

  /// No description provided for @complaintShopLabel.
  ///
  /// In en, this message translates to:
  /// **'Shop'**
  String get complaintShopLabel;

  /// No description provided for @complaintUpdateTitle.
  ///
  /// In en, this message translates to:
  /// **'Update this complaint'**
  String get complaintUpdateTitle;

  /// No description provided for @complaintChooseReviewHint.
  ///
  /// In en, this message translates to:
  /// **'You are checking it. The citizen is told.'**
  String get complaintChooseReviewHint;

  /// No description provided for @complaintChooseResolvedHint.
  ///
  /// In en, this message translates to:
  /// **'The problem has been fixed.'**
  String get complaintChooseResolvedHint;

  /// No description provided for @complaintChooseRejectedHint.
  ///
  /// In en, this message translates to:
  /// **'No action can be taken. Say why in the reply.'**
  String get complaintChooseRejectedHint;

  /// No description provided for @complaintReplyLabel.
  ///
  /// In en, this message translates to:
  /// **'Reply to the citizen (optional)'**
  String get complaintReplyLabel;

  /// No description provided for @complaintReplyHint.
  ///
  /// In en, this message translates to:
  /// **'The citizen sees this reply. Do not write Aadhaar numbers, OTPs or passwords.'**
  String get complaintReplyHint;

  /// No description provided for @complaintUpdated.
  ///
  /// In en, this message translates to:
  /// **'Complaint updated'**
  String get complaintUpdated;

  /// No description provided for @recordsTitle.
  ///
  /// In en, this message translates to:
  /// **'Records'**
  String get recordsTitle;

  /// No description provided for @allBookingsTitle.
  ///
  /// In en, this message translates to:
  /// **'All bookings'**
  String get allBookingsTitle;

  /// No description provided for @stockAllShopsTitle.
  ///
  /// In en, this message translates to:
  /// **'Stock in all shops'**
  String get stockAllShopsTitle;

  /// No description provided for @reportsTitle.
  ///
  /// In en, this message translates to:
  /// **'Reports'**
  String get reportsTitle;

  /// No description provided for @auditTitle.
  ///
  /// In en, this message translates to:
  /// **'Verification record'**
  String get auditTitle;

  /// No description provided for @usersTitle.
  ///
  /// In en, this message translates to:
  /// **'People and staff'**
  String get usersTitle;

  /// No description provided for @bookingsSearchHint.
  ///
  /// In en, this message translates to:
  /// **'Search token, name or shop'**
  String get bookingsSearchHint;

  /// No description provided for @bookingsCount.
  ///
  /// In en, this message translates to:
  /// **'{count} bookings'**
  String bookingsCount(int count);

  /// No description provided for @noBookingsHere.
  ///
  /// In en, this message translates to:
  /// **'No bookings here.'**
  String get noBookingsHere;

  /// No description provided for @lowStockOnly.
  ///
  /// In en, this message translates to:
  /// **'Low stock only'**
  String get lowStockOnly;

  /// No description provided for @noLowStock.
  ///
  /// In en, this message translates to:
  /// **'No shop is low on stock.'**
  String get noLowStock;

  /// No description provided for @reportsChangeDates.
  ///
  /// In en, this message translates to:
  /// **'Change dates'**
  String get reportsChangeDates;

  /// No description provided for @reportsInPeriod.
  ///
  /// In en, this message translates to:
  /// **'in this period'**
  String get reportsInPeriod;

  /// No description provided for @reportCollections.
  ///
  /// In en, this message translates to:
  /// **'Collections completed'**
  String get reportCollections;

  /// No description provided for @reportTokens.
  ///
  /// In en, this message translates to:
  /// **'Tokens booked'**
  String get reportTokens;

  /// No description provided for @reportCounterChecks.
  ///
  /// In en, this message translates to:
  /// **'Collections confirmed at the counter'**
  String get reportCounterChecks;

  /// No description provided for @reportCancelled.
  ///
  /// In en, this message translates to:
  /// **'Bookings cancelled'**
  String get reportCancelled;

  /// No description provided for @reportsNoDownload.
  ///
  /// In en, this message translates to:
  /// **'File download is not available yet.'**
  String get reportsNoDownload;

  /// No description provided for @auditSuccess.
  ///
  /// In en, this message translates to:
  /// **'Success'**
  String get auditSuccess;

  /// No description provided for @auditBlocked.
  ///
  /// In en, this message translates to:
  /// **'Blocked'**
  String get auditBlocked;

  /// No description provided for @auditFailed.
  ///
  /// In en, this message translates to:
  /// **'Failed'**
  String get auditFailed;

  /// No description provided for @auditQrScanned.
  ///
  /// In en, this message translates to:
  /// **'QR scanned'**
  String get auditQrScanned;

  /// No description provided for @auditBeneficiaryVerified.
  ///
  /// In en, this message translates to:
  /// **'Beneficiary checked'**
  String get auditBeneficiaryVerified;

  /// No description provided for @auditAadhaarChecked.
  ///
  /// In en, this message translates to:
  /// **'Aadhaar status checked'**
  String get auditAadhaarChecked;

  /// No description provided for @auditPassbookChecked.
  ///
  /// In en, this message translates to:
  /// **'Passbook status checked'**
  String get auditPassbookChecked;

  /// No description provided for @auditOtpRequested.
  ///
  /// In en, this message translates to:
  /// **'OTP sent'**
  String get auditOtpRequested;

  /// No description provided for @auditOtpVerified.
  ///
  /// In en, this message translates to:
  /// **'OTP correct'**
  String get auditOtpVerified;

  /// No description provided for @auditOtpFailed.
  ///
  /// In en, this message translates to:
  /// **'OTP wrong'**
  String get auditOtpFailed;

  /// No description provided for @auditCollectionConfirmed.
  ///
  /// In en, this message translates to:
  /// **'Ration handed over'**
  String get auditCollectionConfirmed;

  /// No description provided for @auditCollectionRejected.
  ///
  /// In en, this message translates to:
  /// **'Collection refused'**
  String get auditCollectionRejected;

  /// No description provided for @auditTokenUsed.
  ///
  /// In en, this message translates to:
  /// **'Token already used'**
  String get auditTokenUsed;

  /// No description provided for @auditMethod.
  ///
  /// In en, this message translates to:
  /// **'Method'**
  String get auditMethod;

  /// No description provided for @auditBeneficiary.
  ///
  /// In en, this message translates to:
  /// **'Beneficiary no.'**
  String get auditBeneficiary;

  /// No description provided for @noEntriesHere.
  ///
  /// In en, this message translates to:
  /// **'No entries here.'**
  String get noEntriesHere;

  /// No description provided for @usersSearchHint.
  ///
  /// In en, this message translates to:
  /// **'Search by name'**
  String get usersSearchHint;

  /// No description provided for @usersContactHidden.
  ///
  /// In en, this message translates to:
  /// **'Contact details are partly hidden on the phone. See the website for full details.'**
  String get usersContactHidden;

  /// No description provided for @noUsersHere.
  ///
  /// In en, this message translates to:
  /// **'No one here.'**
  String get noUsersHere;

  /// No description provided for @aiCenterTitle.
  ///
  /// In en, this message translates to:
  /// **'AI insights'**
  String get aiCenterTitle;

  /// No description provided for @aiCenterNotice.
  ///
  /// In en, this message translates to:
  /// **'Decision support only. Nothing here refuses ration, cancels a card or proves fraud. A person must check before acting.'**
  String get aiCenterNotice;

  /// No description provided for @aiDemoData.
  ///
  /// In en, this message translates to:
  /// **'Calculated from demo data.'**
  String get aiDemoData;

  /// No description provided for @aiShopsAttention.
  ///
  /// In en, this message translates to:
  /// **'Shops needing stock'**
  String get aiShopsAttention;

  /// No description provided for @aiAverageWait.
  ///
  /// In en, this message translates to:
  /// **'Average wait'**
  String get aiAverageWait;

  /// No description provided for @aiAlertsToReview.
  ///
  /// In en, this message translates to:
  /// **'Alerts to review'**
  String get aiAlertsToReview;

  /// No description provided for @minutesShort.
  ///
  /// In en, this message translates to:
  /// **'{minutes} min'**
  String minutesShort(String minutes);

  /// No description provided for @aiDemandTitle.
  ///
  /// In en, this message translates to:
  /// **'Demand: next 30 days'**
  String get aiDemandTitle;

  /// No description provided for @aiDemandLine.
  ///
  /// In en, this message translates to:
  /// **'Last 30 days {last} · before that {previous}'**
  String aiDemandLine(String last, String previous);

  /// No description provided for @aiDemandExpected.
  ///
  /// In en, this message translates to:
  /// **'Expected'**
  String get aiDemandExpected;

  /// No description provided for @aiNoDemand.
  ///
  /// In en, this message translates to:
  /// **'Not enough collections yet to estimate demand.'**
  String get aiNoDemand;

  /// No description provided for @aiStockRiskTitle.
  ///
  /// In en, this message translates to:
  /// **'Stock running out'**
  String get aiStockRiskTitle;

  /// No description provided for @aiShowAllStock.
  ///
  /// In en, this message translates to:
  /// **'Show all items'**
  String get aiShowAllStock;

  /// No description provided for @aiDaysLeft.
  ///
  /// In en, this message translates to:
  /// **'Reorder in about {days} days'**
  String aiDaysLeft(int days);

  /// No description provided for @aiReorderNow.
  ///
  /// In en, this message translates to:
  /// **'Reorder now'**
  String get aiReorderNow;

  /// No description provided for @aiNoRecentUse.
  ///
  /// In en, this message translates to:
  /// **'No recent use'**
  String get aiNoRecentUse;

  /// No description provided for @aiQueueTitle.
  ///
  /// In en, this message translates to:
  /// **'Expected wait today'**
  String get aiQueueTitle;

  /// No description provided for @aiQueueLine.
  ///
  /// In en, this message translates to:
  /// **'{count} waiting'**
  String aiQueueLine(int count);

  /// No description provided for @aiNoQueue.
  ///
  /// In en, this message translates to:
  /// **'No one is waiting at any shop.'**
  String get aiNoQueue;

  /// No description provided for @correctStock.
  ///
  /// In en, this message translates to:
  /// **'Correct count'**
  String get correctStock;

  /// No description provided for @correctStockHint.
  ///
  /// In en, this message translates to:
  /// **'Only to fix a counting mistake. Deliveries and damaged stock have their own buttons. Every correction is recorded.'**
  String get correctStockHint;

  /// No description provided for @correctInStock.
  ///
  /// In en, this message translates to:
  /// **'In stock now ({unit})'**
  String correctInStock(String unit);

  /// No description provided for @correctMinimum.
  ///
  /// In en, this message translates to:
  /// **'Minimum level ({unit})'**
  String correctMinimum(String unit);

  /// No description provided for @correctConfirmTitle.
  ///
  /// In en, this message translates to:
  /// **'Change {item} in stock from {from} to {to}?'**
  String correctConfirmTitle(String item, String from, String to);

  /// No description provided for @correctConfirmBody.
  ///
  /// In en, this message translates to:
  /// **'This is recorded as a manual correction with your name. Officials can see it.'**
  String get correctConfirmBody;

  /// No description provided for @correctNoChange.
  ///
  /// In en, this message translates to:
  /// **'Nothing was changed.'**
  String get correctNoChange;

  /// No description provided for @stockCorrected.
  ///
  /// In en, this message translates to:
  /// **'Stock corrected.'**
  String get stockCorrected;

  /// No description provided for @amountInvalid.
  ///
  /// In en, this message translates to:
  /// **'Enter a number, 0 or more.'**
  String get amountInvalid;

  /// No description provided for @helpTopicsTitle.
  ///
  /// In en, this message translates to:
  /// **'Help topics'**
  String get helpTopicsTitle;

  /// No description provided for @helpSearchLabel.
  ///
  /// In en, this message translates to:
  /// **'Search help'**
  String get helpSearchLabel;

  /// No description provided for @helpResultsFor.
  ///
  /// In en, this message translates to:
  /// **'Results for “{query}”'**
  String helpResultsFor(String query);

  /// No description provided for @helpNoResults.
  ///
  /// In en, this message translates to:
  /// **'Nothing found. Try other words or ask the assistant.'**
  String get helpNoResults;

  /// No description provided for @helpAskAssistant.
  ///
  /// In en, this message translates to:
  /// **'Ask the assistant'**
  String get helpAskAssistant;

  /// No description provided for @helpArticleCount.
  ///
  /// In en, this message translates to:
  /// **'{count, plural, =1{1 article} other{{count} articles}}'**
  String helpArticleCount(int count);

  /// No description provided for @accountTitle.
  ///
  /// In en, this message translates to:
  /// **'My account'**
  String get accountTitle;

  /// No description provided for @closeAccountTitle.
  ///
  /// In en, this message translates to:
  /// **'Close my account'**
  String get closeAccountTitle;

  /// No description provided for @closeAccountIntro.
  ///
  /// In en, this message translates to:
  /// **'Your account is switched off at once and you are signed out. Your records are erased within one year, as the privacy policy explains. Your ration card itself is not affected.'**
  String get closeAccountIntro;

  /// No description provided for @closeAccountConfirm.
  ///
  /// In en, this message translates to:
  /// **'Close my account permanently'**
  String get closeAccountConfirm;

  /// No description provided for @closeAccountClosing.
  ///
  /// In en, this message translates to:
  /// **'Closing…'**
  String get closeAccountClosing;

  /// No description provided for @closeAccountDone.
  ///
  /// In en, this message translates to:
  /// **'Your account is closed.'**
  String get closeAccountDone;

  /// No description provided for @exportTitle.
  ///
  /// In en, this message translates to:
  /// **'Download my data'**
  String get exportTitle;

  /// No description provided for @exportIntro.
  ///
  /// In en, this message translates to:
  /// **'Get a copy of everything this service holds about you: your account, ration card and family, bookings, collections, complaints, notifications and account activity. Passwords and security keys are never included. Keep the file private.'**
  String get exportIntro;

  /// No description provided for @exportDownload.
  ///
  /// In en, this message translates to:
  /// **'Download my data (JSON)'**
  String get exportDownload;

  /// No description provided for @exportPreparing.
  ///
  /// In en, this message translates to:
  /// **'Preparing…'**
  String get exportPreparing;

  /// No description provided for @exportDone.
  ///
  /// In en, this message translates to:
  /// **'Your data has been saved.'**
  String get exportDone;

  /// No description provided for @exportFailed.
  ///
  /// In en, this message translates to:
  /// **'Could not prepare your data. Please try again.'**
  String get exportFailed;

  /// No description provided for @profileTitle.
  ///
  /// In en, this message translates to:
  /// **'My profile'**
  String get profileTitle;

  /// No description provided for @profileEmailNote.
  ///
  /// In en, this message translates to:
  /// **'Your email is your sign-in name and cannot be changed here.'**
  String get profileEmailNote;

  /// No description provided for @profileNameLabel.
  ///
  /// In en, this message translates to:
  /// **'Full name'**
  String get profileNameLabel;

  /// No description provided for @profileNameInvalid.
  ///
  /// In en, this message translates to:
  /// **'Please enter your full name.'**
  String get profileNameInvalid;

  /// No description provided for @profileSave.
  ///
  /// In en, this message translates to:
  /// **'Save'**
  String get profileSave;

  /// No description provided for @profileSaved.
  ///
  /// In en, this message translates to:
  /// **'Profile saved'**
  String get profileSaved;

  /// No description provided for @verificationTitle.
  ///
  /// In en, this message translates to:
  /// **'My verification'**
  String get verificationTitle;

  /// No description provided for @verificationAadhaar.
  ///
  /// In en, this message translates to:
  /// **'Aadhaar'**
  String get verificationAadhaar;

  /// No description provided for @verificationRationCard.
  ///
  /// In en, this message translates to:
  /// **'Ration card'**
  String get verificationRationCard;

  /// No description provided for @verificationMobile.
  ///
  /// In en, this message translates to:
  /// **'Mobile number'**
  String get verificationMobile;

  /// No description provided for @verificationVerified.
  ///
  /// In en, this message translates to:
  /// **'Verified'**
  String get verificationVerified;

  /// No description provided for @verificationPending.
  ///
  /// In en, this message translates to:
  /// **'Pending'**
  String get verificationPending;

  /// No description provided for @verificationNotVerified.
  ///
  /// In en, this message translates to:
  /// **'Not verified'**
  String get verificationNotVerified;

  /// No description provided for @verificationFailed.
  ///
  /// In en, this message translates to:
  /// **'Failed'**
  String get verificationFailed;

  /// No description provided for @verificationExpired.
  ///
  /// In en, this message translates to:
  /// **'Expired'**
  String get verificationExpired;

  /// No description provided for @verificationHelp.
  ///
  /// In en, this message translates to:
  /// **'If something here is wrong, visit your ration office with your documents.'**
  String get verificationHelp;

  /// No description provided for @mfaTitle.
  ///
  /// In en, this message translates to:
  /// **'Two-factor sign-in'**
  String get mfaTitle;

  /// No description provided for @mfaIntro.
  ///
  /// In en, this message translates to:
  /// **'Protect this staff account with a second step: after your password, enter the 6-digit code from an authenticator app (Google Authenticator, Microsoft Authenticator or similar).'**
  String get mfaIntro;

  /// No description provided for @mfaStart.
  ///
  /// In en, this message translates to:
  /// **'Set up two-factor sign-in'**
  String get mfaStart;

  /// No description provided for @mfaScan.
  ///
  /// In en, this message translates to:
  /// **'Scan this QR code with your authenticator app, then enter the 6-digit code it shows.'**
  String get mfaScan;

  /// No description provided for @mfaQrLabel.
  ///
  /// In en, this message translates to:
  /// **'QR code for the authenticator app'**
  String get mfaQrLabel;

  /// No description provided for @mfaManualKey.
  ///
  /// In en, this message translates to:
  /// **'Or type this key'**
  String get mfaManualKey;

  /// No description provided for @mfaCopyKey.
  ///
  /// In en, this message translates to:
  /// **'Copy key'**
  String get mfaCopyKey;

  /// No description provided for @mfaTurnOn.
  ///
  /// In en, this message translates to:
  /// **'Turn on'**
  String get mfaTurnOn;

  /// No description provided for @mfaIsOn.
  ///
  /// In en, this message translates to:
  /// **'Two-factor sign-in is on.'**
  String get mfaIsOn;

  /// No description provided for @mfaOffHint.
  ///
  /// In en, this message translates to:
  /// **'To turn it off, enter your password and a current code.'**
  String get mfaOffHint;

  /// No description provided for @mfaTurnOff.
  ///
  /// In en, this message translates to:
  /// **'Turn off two-factor sign-in'**
  String get mfaTurnOff;

  /// No description provided for @mfaTurnedOn.
  ///
  /// In en, this message translates to:
  /// **'Two-factor sign-in is on.'**
  String get mfaTurnedOn;

  /// No description provided for @mfaTurnedOff.
  ///
  /// In en, this message translates to:
  /// **'Two-factor sign-in is off.'**
  String get mfaTurnedOff;

  /// No description provided for @mfaWrongPassword.
  ///
  /// In en, this message translates to:
  /// **'The password is incorrect.'**
  String get mfaWrongPassword;

  /// No description provided for @mfaWrongCode.
  ///
  /// In en, this message translates to:
  /// **'The code is wrong or has expired. Use the current code from your authenticator app.'**
  String get mfaWrongCode;

  /// No description provided for @registerTitle.
  ///
  /// In en, this message translates to:
  /// **'Create an account'**
  String get registerTitle;

  /// No description provided for @registerLink.
  ///
  /// In en, this message translates to:
  /// **'New here? Create an account'**
  String get registerLink;

  /// No description provided for @registerIntro.
  ///
  /// In en, this message translates to:
  /// **'For ration card holders. Shop owners and officials get their accounts from the office.'**
  String get registerIntro;

  /// No description provided for @fullNameLabel.
  ///
  /// In en, this message translates to:
  /// **'Full name'**
  String get fullNameLabel;

  /// No description provided for @nameTooShort.
  ///
  /// In en, this message translates to:
  /// **'Please enter your full name.'**
  String get nameTooShort;

  /// No description provided for @confirmPasswordPlain.
  ///
  /// In en, this message translates to:
  /// **'Confirm password'**
  String get confirmPasswordPlain;

  /// No description provided for @consentText.
  ///
  /// In en, this message translates to:
  /// **'I have read the privacy policy and agree that my details are used to provide my ration, as it describes.'**
  String get consentText;

  /// No description provided for @consentRequired.
  ///
  /// In en, this message translates to:
  /// **'Please read the privacy policy and tick the box to continue.'**
  String get consentRequired;

  /// No description provided for @readPrivacyPolicy.
  ///
  /// In en, this message translates to:
  /// **'Read the privacy policy'**
  String get readPrivacyPolicy;

  /// No description provided for @registerButton.
  ///
  /// In en, this message translates to:
  /// **'Create account'**
  String get registerButton;

  /// No description provided for @registerFailed.
  ///
  /// In en, this message translates to:
  /// **'The account could not be created. Please try again.'**
  String get registerFailed;

  /// No description provided for @registerAlreadyExists.
  ///
  /// In en, this message translates to:
  /// **'An account with this email or mobile number already exists. Sign in instead, or reset your password.'**
  String get registerAlreadyExists;

  /// No description provided for @registered.
  ///
  /// In en, this message translates to:
  /// **'Welcome! Your account is ready.'**
  String get registered;

  /// No description provided for @profileMobilePasswordNote.
  ///
  /// In en, this message translates to:
  /// **'Sign-in codes and password resets go to this number, so changing it needs your password.'**
  String get profileMobilePasswordNote;

  /// No description provided for @verificationMobileHint.
  ///
  /// In en, this message translates to:
  /// **'Changed your mobile number? Sign in once with a code sent to the new number, or ask your ration shop to verify it with a code.'**
  String get verificationMobileHint;
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
