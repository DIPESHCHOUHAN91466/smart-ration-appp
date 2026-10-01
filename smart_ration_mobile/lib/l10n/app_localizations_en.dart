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

  @override
  String get rationCard => 'Ration card';

  @override
  String get cardNumber => 'Card number';

  @override
  String get cardScheme => 'Card type (scheme)';

  @override
  String get cardStatus => 'Status';

  @override
  String get cardActive => 'Active';

  @override
  String get cardInactive => 'Not active';

  @override
  String get familyId => 'Family ID';

  @override
  String get familySizeLabel => 'Family size';

  @override
  String memberCount(int count) {
    return '$count members';
  }

  @override
  String get assignedShop => 'Ration shop';

  @override
  String get familyMembers => 'Family members';

  @override
  String ageYears(int age) {
    return '$age years';
  }

  @override
  String get relHead => 'Head of family';

  @override
  String get relSpouse => 'Spouse';

  @override
  String get relSon => 'Son';

  @override
  String get relDaughter => 'Daughter';

  @override
  String get relParent => 'Parent';

  @override
  String get relOther => 'Other relative';

  @override
  String get memberEligible => 'Eligible';

  @override
  String get memberNotEligible => 'Not eligible';

  @override
  String get memberPending => 'Pending';

  @override
  String get memberVerificationRequired => 'Verification required';

  @override
  String get eligibilityTitle => 'Eligibility';

  @override
  String get familyEligible => 'Eligible';

  @override
  String get familyPartiallyEligible => 'Partially eligible';

  @override
  String get familyNotEligible => 'Not eligible';

  @override
  String eligibleMembersOf(int eligible, int total) {
    return '$eligible of $total members eligible';
  }

  @override
  String get eligibilityExplainEligible =>
      'Every member of your family can receive rations this month.';

  @override
  String get eligibilityExplainPartial =>
      'Some members are not eligible yet. Your entitlement counts only the eligible members.';

  @override
  String get eligibilityExplainNot =>
      'Your family cannot receive rations right now. Please contact your ration shop or district office.';

  @override
  String get monthlyEntitlement => 'This month\'s entitlement';

  @override
  String remainingOf(String remaining, String total, String unit) {
    return '$remaining $unit left of $total $unit';
  }

  @override
  String collectedAmount(String amount, String unit) {
    return 'Collected: $amount $unit';
  }

  @override
  String get itemRice => 'Rice';

  @override
  String get itemWheat => 'Wheat';

  @override
  String get itemSugar => 'Sugar';

  @override
  String get itemPulses => 'Pulses (dal)';

  @override
  String get itemOil => 'Edible oil';

  @override
  String get itemSalt => 'Salt';

  @override
  String get unitKg => 'kg';

  @override
  String get unitLitre => 'L';

  @override
  String get collectionHistory => 'Collection history';

  @override
  String get noCollections => 'No rations collected yet.';

  @override
  String get aadhaarVerified => 'Aadhaar verified';

  @override
  String get aadhaarNotVerified => 'Aadhaar not verified';

  @override
  String get viewDetails => 'View details';

  @override
  String get noBeneficiaryProfile =>
      'Your ration card is not linked yet. Please contact your ration shop.';

  @override
  String get demoDataNotice => 'Demo data: this is not a real ration card.';

  @override
  String get genderMale => 'Male';

  @override
  String get genderFemale => 'Female';

  @override
  String get genderOther => 'Other';

  @override
  String get bookRation => 'Book ration';

  @override
  String get stepDay => '1. Choose a day';

  @override
  String get stepTime => '2. Choose a 5-minute time';

  @override
  String get stepItems => '3. Choose items';

  @override
  String get today => 'Today';

  @override
  String get tomorrow => 'Tomorrow';

  @override
  String get noSlots =>
      'No times are open on this day. Please choose another day.';

  @override
  String get slotFull => 'Full';

  @override
  String placesLeft(int count) {
    return '$count left';
  }

  @override
  String perVisitLimit(String amount, String unit) {
    return 'Up to $amount $unit this visit';
  }

  @override
  String get notAvailableNow => 'Not available now';

  @override
  String increaseItem(String item) {
    return 'More $item';
  }

  @override
  String decreaseItem(String item) {
    return 'Less $item';
  }

  @override
  String get bookAndGetToken => 'Book and get token';

  @override
  String get bookingInProgress => 'Booking...';

  @override
  String get chooseTimeFirst => 'Please choose a time.';

  @override
  String get chooseItemFirst => 'Please choose at least one item.';

  @override
  String get noShopAssigned =>
      'Your ration shop is not set yet. Please contact your district office.';

  @override
  String get tokenReady => 'Your token is ready.';

  @override
  String get myToken => 'My token';

  @override
  String get myTokens => 'My tokens';

  @override
  String get tokenNumber => 'Token number';

  @override
  String get collectionDate => 'Date';

  @override
  String get collectionTime => 'Time';

  @override
  String get tokenItems => 'Items';

  @override
  String get stateBooked => 'Booked';

  @override
  String get stateCollected => 'Collected';

  @override
  String get stateCancelled => 'Cancelled';

  @override
  String get stateMissed => 'Missed';

  @override
  String get showQrAtShop => 'Show this QR code at the ration shop.';

  @override
  String get qrManualCode =>
      'If the QR cannot be scanned, the shop can type this code:';

  @override
  String get qrNoPersonalData => 'The QR code holds no personal details.';

  @override
  String qrCodeLabel(String number) {
    return 'QR code for token $number';
  }

  @override
  String get cancelBooking => 'Cancel booking';

  @override
  String get cancelConfirmTitle => 'Cancel this booking?';

  @override
  String get cancelConfirmBody => 'Your time will be freed for someone else.';

  @override
  String get keepBooking => 'Keep it';

  @override
  String get bookingCancelled => 'Booking cancelled.';

  @override
  String get noTokens => 'You have no tokens yet.';

  @override
  String get nextCollection => 'Your next collection';

  @override
  String get noUpcomingBooking =>
      'No upcoming booking. Book a time to collect your ration.';

  @override
  String get showQr => 'Show QR code';

  @override
  String get allMyTokens => 'All my tokens';

  @override
  String get shopTodayTitle => 'Today at your shop';

  @override
  String get shopTokensToday => 'Tokens';

  @override
  String get shopCollected => 'Collected';

  @override
  String get shopWaiting => 'Waiting';

  @override
  String get shopCancelled => 'Cancelled';

  @override
  String get scanCustomerQr => 'Scan customer\'s QR';

  @override
  String get verifyByMobile => 'No QR? Verify with mobile code';

  @override
  String get scannerTitle => 'Scan QR code';

  @override
  String get scannerHelp => 'Point the camera at the customer\'s QR code.';

  @override
  String get typeCodeLabel => 'Or type the code shown under the QR';

  @override
  String get typeCodeInvalid => 'Please type the code that starts with SRQR-.';

  @override
  String get checkCode => 'Check';

  @override
  String get checking => 'Checking…';

  @override
  String get cameraDenied =>
      'Camera permission is off. Allow it in the phone\'s Settings, or type the code below.';

  @override
  String get cameraUnavailable =>
      'The camera could not start. Type the code below instead.';

  @override
  String get scanRejectedTitle => 'Cannot accept this token';

  @override
  String get scanInvalidSignature =>
      'This QR code is not genuine. Do not hand over ration.';

  @override
  String get scanNotOurs => 'This is not a Smart Ration token QR code.';

  @override
  String get scanUnreadable =>
      'The QR code could not be read. Scan again or type the code.';

  @override
  String get scanExpired => 'This token\'s collection day has passed.';

  @override
  String get scanNoBooking => 'No booking matches this code.';

  @override
  String get scanWrongShop => 'This token is for a different ration shop.';

  @override
  String get scanAlreadyCollected =>
      'This token has already been used to collect ration.';

  @override
  String get scanBookingCancelled => 'This booking was cancelled.';

  @override
  String get scanAgain => 'Scan again';

  @override
  String get checkTitle => 'Customer check';

  @override
  String get readyTitle => 'Ready to collect';

  @override
  String get readyBody => 'All checks passed. Hand over the items below.';

  @override
  String get blockedTitle => 'Do not hand over ration';

  @override
  String get identifiedByQr => 'Identified by QR code';

  @override
  String get identifiedByOtp => 'Identified by mobile code';

  @override
  String get customer => 'Customer';

  @override
  String get beneficiaryId => 'Beneficiary ID';

  @override
  String get registeredMobile => 'Registered mobile';

  @override
  String get checksTitle => 'Checks';

  @override
  String get checkAadhaar => 'Aadhaar verified';

  @override
  String get checkPassbook => 'Passbook verified';

  @override
  String get checkMobile => 'Mobile number verified';

  @override
  String get checkToken => 'Token valid for collection';

  @override
  String get checkFamily => 'Family eligible';

  @override
  String get checkEntitlement => 'Ration left this month';

  @override
  String get checkPassed => 'Yes';

  @override
  String get checkFailed => 'No';

  @override
  String get itemsToHandOver => 'Items to hand over';

  @override
  String get handOverButton => 'Hand over and confirm';

  @override
  String get handOverConfirmTitle => 'Confirm handover?';

  @override
  String handOverConfirmBody(String name) {
    return 'Confirm only after you have given these items to $name. Your stock will be reduced.';
  }

  @override
  String get notYet => 'Not yet';

  @override
  String get yesHandedOver => 'Yes, handed over';

  @override
  String get saving => 'Saving…';

  @override
  String get errorInsufficientStock =>
      'Not enough stock for this token. Nothing was handed over or deducted.';

  @override
  String get errorConcurrentUpdate =>
      'This token was just updated at another counter. Please scan it again.';

  @override
  String get reasonAccountBlocked => 'This beneficiary account is blocked.';

  @override
  String get reasonAccountInactive => 'This beneficiary account is not active.';

  @override
  String get reasonTokenInvalid => 'This token is not valid for collection.';

  @override
  String get reasonAadhaarFailed => 'Aadhaar verification failed.';

  @override
  String get reasonAadhaarExpired => 'Aadhaar verification has expired.';

  @override
  String get reasonAadhaarPending => 'Aadhaar verification is pending.';

  @override
  String get reasonPassbookPending => 'Passbook verification is pending.';

  @override
  String get reasonMobileRequired =>
      'The customer\'s mobile number must be verified first.';

  @override
  String get reasonNotEligible =>
      'This family is not eligible under its scheme.';

  @override
  String get reasonNoEntitlement =>
      'No ration is left for this family this month.';

  @override
  String get otpCheckTitle => 'Verify with mobile code';

  @override
  String get otpCheckHelp =>
      'Type the customer\'s registered mobile number. A 6-digit code will be sent to it.';

  @override
  String get customerMobileLabel => 'Customer\'s mobile number';

  @override
  String askCustomerForCode(String mobile, int minutes) {
    return 'Ask the customer for the code sent to $mobile. It is valid for $minutes minutes.';
  }

  @override
  String get verifyCodeButton => 'Verify code';

  @override
  String get otpNoCustomer =>
      'No customer is registered with this mobile number.';

  @override
  String get otpNoBookingHere =>
      'This customer has no active booking at your shop.';

  @override
  String get receiptTitle => 'Ration handed over';

  @override
  String get receiptCollectionId => 'Collection ID';

  @override
  String get receiptSaved =>
      'Saved. Stock has been reduced and the customer has been notified.';

  @override
  String get scanNextCustomer => 'Scan next customer';

  @override
  String get backToDashboard => 'Back to dashboard';

  @override
  String get nothingToCheck => 'Nothing to check. Scan a QR code first.';

  @override
  String get queueButton => 'Today\'s queue';

  @override
  String get stockButton => 'Stock';

  @override
  String lowStockBanner(int count) {
    String _temp0 = intl.Intl.pluralLogic(
      count,
      locale: localeName,
      other: '$count items are low on stock',
      one: '1 item is low on stock',
    );
    return '$_temp0';
  }

  @override
  String queueWaitingHeader(int count) {
    return 'Waiting ($count)';
  }

  @override
  String queueDoneHeader(int count) {
    return 'Done ($count)';
  }

  @override
  String get queueEmpty => 'No tokens booked for today.';

  @override
  String get queueServeHint =>
      'When this customer arrives, scan their QR or verify by mobile code.';

  @override
  String get stockAvailable => 'In stock';

  @override
  String get stockMinimum => 'Minimum level';

  @override
  String get stockHandedOut => 'Handed out';

  @override
  String get stockLow => 'Low';

  @override
  String get stockOk => 'OK';

  @override
  String get noStockLines => 'No stock lines for this shop yet.';

  @override
  String get receiveStock => 'Record delivery';

  @override
  String get writeOffStock => 'Write off damaged';

  @override
  String quantityLabel(String unit) {
    return 'Quantity ($unit)';
  }

  @override
  String get referenceLabel => 'Delivery or report number (optional)';

  @override
  String get noteLabel => 'Note (optional)';

  @override
  String get quantityInvalid => 'Enter a quantity greater than 0.';

  @override
  String get quantityTooLarge => 'Enter a quantity up to 1,000,000.';

  @override
  String writeOffTooMuch(String max, String unit) {
    return 'You can write off at most $max $unit.';
  }

  @override
  String get referenceInvalid =>
      'Use only letters, numbers, spaces and - / _ .';

  @override
  String get saveButton => 'Save';

  @override
  String get cancelButton => 'Cancel';

  @override
  String writeOffConfirmTitle(String amount) {
    return 'Write off $amount?';
  }

  @override
  String get writeOffConfirmBody =>
      'This removes damaged stock for good. It is recorded in the stock ledger.';

  @override
  String get stockReceived => 'Delivery recorded.';

  @override
  String get stockWrittenOff => 'Damaged stock written off.';

  @override
  String get officialTodayTitle => 'Today across all shops';

  @override
  String get statShops => 'Shops';

  @override
  String get statBeneficiaries => 'Beneficiaries';

  @override
  String get statBookings => 'Bookings';

  @override
  String get statHandedOutToday => 'Handed out today';

  @override
  String get statLowStockAlerts => 'Low-stock items';

  @override
  String get periodTitle => 'Last 30 days';

  @override
  String get statTokensBooked => 'Tokens booked';

  @override
  String get collectionRateLabel => 'Collection rate';

  @override
  String collectionRateValue(String percent) {
    return '$percent% of booked tokens were collected';
  }

  @override
  String alertsButton(int count) {
    return 'Alerts ($count)';
  }

  @override
  String get alertsTitle => 'Alerts';

  @override
  String get filterAll => 'All';

  @override
  String get stockCritical => 'Critical';

  @override
  String shopTodayLine(int booked, int collected) {
    return 'Today: $booked booked · $collected collected';
  }

  @override
  String get shopOwnerLabel => 'Shop owner';

  @override
  String get shopPlaceLabel => 'Place';

  @override
  String get shopCodeLabel => 'Shop code';

  @override
  String get noShops => 'No shops found.';

  @override
  String get alertsNotice =>
      'These are warnings to review, not proof of fraud. Check before acting.';

  @override
  String get noAlerts => 'No open alerts.';

  @override
  String get severityHigh => 'High';

  @override
  String get severityMedium => 'Medium';

  @override
  String get severityLow => 'Low';

  @override
  String get alertDuplicateCollection => 'Repeated collection attempts';

  @override
  String get alertRepeatedQrScan => 'Same QR scanned many times';

  @override
  String get alertFailedVerification => 'Repeated failed checks';

  @override
  String get alertLowStock => 'Low stock';

  @override
  String get alertUnusualConsumption => 'Unusual consumption';

  @override
  String get alertDetailsInEnglish => 'Details from the system (English):';

  @override
  String get helpTitle => 'Help — Ration Mitra';

  @override
  String get helpButton => 'Help';

  @override
  String get assistantName => 'Ration Mitra';

  @override
  String get youLabel => 'You';

  @override
  String get helpPrivacy =>
      'Don\'t type Aadhaar numbers, OTPs or passwords. Nothing you type is saved on this phone.';

  @override
  String get askHint => 'Type your question';

  @override
  String get sendQuestion => 'Send';

  @override
  String get speakQuestion => 'Ask by voice';

  @override
  String get stopListening => 'Stop listening';

  @override
  String get listening => 'Listening… speak now';

  @override
  String get voiceNote =>
      'Your phone\'s speech service turns your voice into text and may use the internet to do so.';

  @override
  String get voiceUnavailable =>
      'Voice input is not available. Allow the microphone in Settings, or type your question.';

  @override
  String get readAloud => 'Read aloud';

  @override
  String get stopReading => 'Stop reading';

  @override
  String get voiceMissing =>
      'This phone has no voice for this language. You can add one in the phone\'s text-to-speech settings.';

  @override
  String get relatedTitle => 'Related';

  @override
  String get thinking => 'Ration Mitra is typing…';

  @override
  String get noSpeechHeard =>
      'I didn\'t hear anything. Tap the mic and try again.';
}
