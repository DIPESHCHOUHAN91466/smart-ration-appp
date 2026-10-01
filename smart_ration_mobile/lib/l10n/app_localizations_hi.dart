// ignore: unused_import
import 'package:intl/intl.dart' as intl;

import 'app_localizations.dart';

// ignore_for_file: type=lint

/// The translations for Hindi (`hi`).
class AppLocalizationsHi extends AppLocalizations {
  AppLocalizationsHi([String locale = 'hi']) : super(locale);

  @override
  String get appTitle => 'स्मार्ट राशन AI';

  @override
  String get poweredBy => 'HSD2C द्वारा संचालित';

  @override
  String get tagline => 'AI की शक्ति · हर परिवार के लिए';

  @override
  String get loading => 'लोड हो रहा है...';

  @override
  String get logoDescription => 'स्मार्ट राशन AI का लोगो, HSD2C द्वारा संचालित';

  @override
  String get chooseLanguageTitle => 'अपनी भाषा चुनें';

  @override
  String get chooseLanguageHelp =>
      'आप इसे बाद में स्क्रीन के ऊपर दिए भाषा बटन से बदल सकते हैं।';

  @override
  String get continueButton => 'आगे बढ़ें';

  @override
  String get language => 'भाषा';

  @override
  String get serverChecking => 'सर्वर से कनेक्शन जाँचा जा रहा है…';

  @override
  String get serverConnected => 'सर्वर से जुड़ गए';

  @override
  String get serverNoDatabase => 'सर्वर अपने डेटाबेस तक नहीं पहुँच पा रहा है';

  @override
  String get statusOverall => 'कुल स्थिति';

  @override
  String get statusDatabase => 'डेटाबेस';

  @override
  String get statusData => 'डेटा';

  @override
  String get statusHealthy => 'ठीक है';

  @override
  String get statusDegraded => 'आंशिक रूप से चालू';

  @override
  String get statusUnhealthy => 'काम नहीं कर रहा';

  @override
  String get statusUnknown => 'अज्ञात';

  @override
  String get dataSynthetic => 'डेमो डेटा (सिंथेटिक)';

  @override
  String get dataReal => 'वास्तविक डेटा';

  @override
  String serverAddress(String url, String environment) {
    return 'सर्वर: $url · $environment';
  }

  @override
  String get tryAgain => 'पुनः प्रयास करें';

  @override
  String get errorNoConnection =>
      'कनेक्ट नहीं हो सका। कृपया अपना इंटरनेट कनेक्शन जाँचें।';

  @override
  String get errorTimeout =>
      'सर्वर जवाब देने में बहुत समय ले रहा है। कृपया पुनः प्रयास करें।';

  @override
  String get errorSessionEnded =>
      'आपका सत्र समाप्त हो गया है। कृपया फिर से साइन इन करें।';

  @override
  String get errorTooManyRequests =>
      'बहुत अधिक प्रयास हुए। कृपया एक मिनट रुककर पुनः प्रयास करें।';

  @override
  String get errorServer =>
      'सर्वर में समस्या आई। कृपया कुछ मिनट बाद पुनः प्रयास करें।';

  @override
  String get errorGeneric => 'कुछ गलत हो गया। कृपया पुनः प्रयास करें।';

  @override
  String get errorForbidden => 'आपको यह करने की अनुमति नहीं है।';

  @override
  String get errorNotFound => 'मांगी गई जानकारी नहीं मिली।';

  @override
  String get errorRequestFailed =>
      'अनुरोध पूरा नहीं हो सका। कृपया जाँचकर पुनः प्रयास करें।';

  @override
  String get signInTitle => 'साइन इन करें';

  @override
  String get signInSubtitle =>
      'अपने स्मार्ट राशन खाते का ईमेल और पासवर्ड डालें।';

  @override
  String get emailLabel => 'ईमेल';

  @override
  String get passwordLabel => 'पासवर्ड';

  @override
  String get showPassword => 'पासवर्ड दिखाएं';

  @override
  String get hidePassword => 'पासवर्ड छिपाएं';

  @override
  String get signInButton => 'साइन इन करें';

  @override
  String get signingIn => 'साइन इन हो रहा है...';

  @override
  String get emailRequired => 'कृपया अपना ईमेल डालें।';

  @override
  String get emailInvalid => 'कृपया सही ईमेल पता डालें।';

  @override
  String get passwordRequired => 'कृपया अपना पासवर्ड डालें।';

  @override
  String get loginInvalid => 'ईमेल या पासवर्ड सही नहीं है।';

  @override
  String get loginAccountDisabled =>
      'यह खाता बंद कर दिया गया है। कृपया अपनी राशन दुकान या जिला कार्यालय से संपर्क करें।';

  @override
  String get demoAccountsTitle => 'डेमो खाते (केवल डेवलपमेंट बिल्ड में)';

  @override
  String get demoAccountsHelp =>
      'ईमेल भरने के लिए किसी एक पर टैप करें। डेमो पासवर्ड प्रोजेक्ट की README में है।';

  @override
  String get checkServer => 'सर्वर कनेक्शन जाँचें';

  @override
  String get serverStatusTitle => 'सर्वर की स्थिति';

  @override
  String get roleRuralUser => 'ग्रामीण उपयोगकर्ता';

  @override
  String get roleShopOwner => 'दुकान मालिक';

  @override
  String get roleOfficial => 'सरकारी अधिकारी';

  @override
  String get roleAdmin => 'प्रशासक';

  @override
  String greeting(String name) {
    return 'नमस्ते, $name';
  }

  @override
  String get signOut => 'साइन आउट';

  @override
  String shopLinked(int id) {
    return 'राशन दुकान क्र. $id';
  }

  @override
  String get citizenDashboardIntro =>
      'आपका राशन कार्ड, परिवार के सदस्य, बुकिंग और टोकन यहाँ दिखाई देंगे।';

  @override
  String get shopDashboardIntro =>
      'आज के टोकन, QR स्कैनर, स्टॉक और वितरण यहाँ दिखाई देंगे।';

  @override
  String get officialDashboardIntro =>
      'दुकानें, वितरण, स्टॉक चेतावनियाँ और रिपोर्ट यहाँ दिखाई देंगी।';

  @override
  String get signInWithMobile => 'मोबाइल और कोड';

  @override
  String get signInWithEmail => 'ईमेल और पासवर्ड';

  @override
  String get mobileSignInSubtitle =>
      'हम आपके पंजीकृत मोबाइल नंबर पर 6 अंकों का कोड भेजेंगे।';

  @override
  String get mobileLabel => 'मोबाइल नंबर';

  @override
  String get mobileInvalid => 'कृपया 10 अंकों का मोबाइल नंबर डालें।';

  @override
  String get sendCode => 'कोड भेजें';

  @override
  String get sendingCode => 'कोड भेजा जा रहा है...';

  @override
  String codeSentTo(String mobile) {
    return 'अगर $mobile पंजीकृत है, तो उस पर कोड भेज दिया गया है।';
  }

  @override
  String get codeLabel => '6 अंकों का कोड';

  @override
  String get codeInvalidFormat => 'कृपया 6 अंकों का कोड डालें।';

  @override
  String get otpInvalid =>
      'कोड गलत है या उसकी समय-सीमा खत्म हो गई है। कृपया फिर से कोशिश करें या नया कोड मँगाएँ।';

  @override
  String get otpSendFailed =>
      'अभी कोड नहीं भेजा जा सका। कृपया फिर से कोशिश करें या ईमेल और पासवर्ड से साइन इन करें।';

  @override
  String resendIn(int seconds) {
    return '$seconds सेकंड में नया कोड भेजें';
  }

  @override
  String get resendCode => 'नया कोड भेजें';

  @override
  String get changeNumber => 'नंबर बदलें';

  @override
  String demoCodeHint(String code) {
    return 'डेवलपमेंट डेमो कोड: $code';
  }

  @override
  String get otpStaffNote =>
      'राशन दुकानदार और अधिकारी ईमेल और पासवर्ड से साइन इन करते हैं।';

  @override
  String get rationCard => 'राशन कार्ड';

  @override
  String get cardNumber => 'कार्ड नंबर';

  @override
  String get cardScheme => 'कार्ड का प्रकार (योजना)';

  @override
  String get cardStatus => 'स्थिति';

  @override
  String get cardActive => 'सक्रिय';

  @override
  String get cardInactive => 'निष्क्रिय';

  @override
  String get familyId => 'परिवार आईडी';

  @override
  String get familySizeLabel => 'परिवार का आकार';

  @override
  String memberCount(int count) {
    return '$count सदस्य';
  }

  @override
  String get assignedShop => 'राशन दुकान';

  @override
  String get familyMembers => 'परिवार के सदस्य';

  @override
  String ageYears(int age) {
    return '$age वर्ष';
  }

  @override
  String get relHead => 'परिवार के मुखिया';

  @override
  String get relSpouse => 'पति/पत्नी';

  @override
  String get relSon => 'पुत्र';

  @override
  String get relDaughter => 'पुत्री';

  @override
  String get relParent => 'माता/पिता';

  @override
  String get relOther => 'अन्य संबंधी';

  @override
  String get memberEligible => 'पात्र';

  @override
  String get memberNotEligible => 'अपात्र';

  @override
  String get memberPending => 'लंबित';

  @override
  String get memberVerificationRequired => 'सत्यापन आवश्यक';

  @override
  String get eligibilityTitle => 'पात्रता';

  @override
  String get familyEligible => 'पात्र';

  @override
  String get familyPartiallyEligible => 'आंशिक रूप से पात्र';

  @override
  String get familyNotEligible => 'अपात्र';

  @override
  String eligibleMembersOf(int eligible, int total) {
    return '$total में से $eligible सदस्य पात्र';
  }

  @override
  String get eligibilityExplainEligible =>
      'आपके परिवार के सभी सदस्य इस महीने राशन ले सकते हैं।';

  @override
  String get eligibilityExplainPartial =>
      'कुछ सदस्य अभी पात्र नहीं हैं। आपकी पात्रता केवल पात्र सदस्यों के आधार पर गिनी जाती है।';

  @override
  String get eligibilityExplainNot =>
      'आपका परिवार अभी राशन नहीं ले सकता। कृपया अपनी राशन दुकान या जिला कार्यालय से संपर्क करें।';

  @override
  String get monthlyEntitlement => 'इस महीने की पात्रता';

  @override
  String remainingOf(String remaining, String total, String unit) {
    return '$total $unit में से $remaining $unit बाकी';
  }

  @override
  String collectedAmount(String amount, String unit) {
    return 'लिया गया: $amount $unit';
  }

  @override
  String get itemRice => 'चावल';

  @override
  String get itemWheat => 'गेहूं';

  @override
  String get itemSugar => 'चीनी';

  @override
  String get itemPulses => 'दाल';

  @override
  String get itemOil => 'खाद्य तेल';

  @override
  String get itemSalt => 'नमक';

  @override
  String get unitKg => 'किग्रा';

  @override
  String get unitLitre => 'लीटर';

  @override
  String get collectionHistory => 'राशन लेने का इतिहास';

  @override
  String get noCollections => 'अभी तक कोई राशन नहीं लिया गया।';

  @override
  String get aadhaarVerified => 'आधार सत्यापित';

  @override
  String get aadhaarNotVerified => 'आधार सत्यापित नहीं';

  @override
  String get viewDetails => 'विवरण देखें';

  @override
  String get noBeneficiaryProfile =>
      'आपका राशन कार्ड अभी जुड़ा नहीं है। कृपया अपनी राशन दुकान से संपर्क करें।';

  @override
  String get demoDataNotice => 'डेमो डेटा: यह असली राशन कार्ड नहीं है।';

  @override
  String get genderMale => 'पुरुष';

  @override
  String get genderFemale => 'महिला';

  @override
  String get genderOther => 'अन्य';

  @override
  String get bookRation => 'राशन बुक करें';

  @override
  String get stepDay => '1. दिन चुनें';

  @override
  String get stepTime => '2. 5 मिनट का समय चुनें';

  @override
  String get stepItems => '3. सामान चुनें';

  @override
  String get today => 'आज';

  @override
  String get tomorrow => 'कल';

  @override
  String get noSlots => 'इस दिन कोई समय उपलब्ध नहीं है। कृपया दूसरा दिन चुनें।';

  @override
  String get slotFull => 'भरा हुआ';

  @override
  String placesLeft(int count) {
    return '$count बाकी';
  }

  @override
  String perVisitLimit(String amount, String unit) {
    return 'इस बार अधिकतम $amount $unit';
  }

  @override
  String get notAvailableNow => 'अभी उपलब्ध नहीं';

  @override
  String increaseItem(String item) {
    return '$item बढ़ाएँ';
  }

  @override
  String decreaseItem(String item) {
    return '$item घटाएँ';
  }

  @override
  String get bookAndGetToken => 'बुक करें और टोकन पाएँ';

  @override
  String get bookingInProgress => 'बुकिंग हो रही है...';

  @override
  String get chooseTimeFirst => 'कृपया समय चुनें।';

  @override
  String get chooseItemFirst => 'कृपया कम से कम एक वस्तु चुनें।';

  @override
  String get noShopAssigned =>
      'आपकी राशन दुकान अभी तय नहीं है। कृपया जिला कार्यालय से संपर्क करें।';

  @override
  String get tokenReady => 'आपका टोकन तैयार है।';

  @override
  String get myToken => 'मेरा टोकन';

  @override
  String get myTokens => 'मेरे टोकन';

  @override
  String get tokenNumber => 'टोकन नंबर';

  @override
  String get collectionDate => 'तारीख';

  @override
  String get collectionTime => 'समय';

  @override
  String get tokenItems => 'सामान';

  @override
  String get stateBooked => 'बुक है';

  @override
  String get stateCollected => 'ले लिया';

  @override
  String get stateCancelled => 'रद्द';

  @override
  String get stateMissed => 'छूट गया';

  @override
  String get showQrAtShop => 'राशन दुकान पर यह QR कोड दिखाएँ।';

  @override
  String get qrManualCode =>
      'अगर QR स्कैन न हो, तो दुकानदार यह कोड लिख सकता है:';

  @override
  String get qrNoPersonalData => 'QR कोड में कोई निजी जानकारी नहीं है।';

  @override
  String qrCodeLabel(String number) {
    return 'टोकन $number का QR कोड';
  }

  @override
  String get cancelBooking => 'बुकिंग रद्द करें';

  @override
  String get cancelConfirmTitle => 'क्या यह बुकिंग रद्द करें?';

  @override
  String get cancelConfirmBody => 'आपका समय किसी और के लिए खाली हो जाएगा।';

  @override
  String get keepBooking => 'रहने दें';

  @override
  String get bookingCancelled => 'बुकिंग रद्द हो गई।';

  @override
  String get noTokens => 'आपके पास अभी कोई टोकन नहीं है।';

  @override
  String get nextCollection => 'आपका अगला राशन';

  @override
  String get noUpcomingBooking =>
      'कोई आने वाली बुकिंग नहीं है। राशन लेने के लिए समय बुक करें।';

  @override
  String get showQr => 'QR कोड दिखाएँ';

  @override
  String get allMyTokens => 'मेरे सभी टोकन';

  @override
  String get shopTodayTitle => 'आज आपकी दुकान पर';

  @override
  String get shopTokensToday => 'टोकन';

  @override
  String get shopCollected => 'दिया गया';

  @override
  String get shopWaiting => 'बाकी';

  @override
  String get shopCancelled => 'रद्द';

  @override
  String get scanCustomerQr => 'ग्राहक का QR स्कैन करें';

  @override
  String get verifyByMobile => 'QR नहीं है? मोबाइल कोड से जाँचें';

  @override
  String get scannerTitle => 'QR कोड स्कैन करें';

  @override
  String get scannerHelp => 'कैमरा ग्राहक के QR कोड की ओर रखें।';

  @override
  String get typeCodeLabel => 'या QR के नीचे दिखा कोड लिखें';

  @override
  String get typeCodeInvalid => 'कृपया SRQR- से शुरू होने वाला कोड लिखें।';

  @override
  String get checkCode => 'जाँचें';

  @override
  String get checking => 'जाँच हो रही है…';

  @override
  String get cameraDenied =>
      'कैमरे की अनुमति बंद है। फ़ोन की सेटिंग में अनुमति दें, या नीचे कोड लिखें।';

  @override
  String get cameraUnavailable =>
      'कैमरा शुरू नहीं हो सका। इसके बजाय नीचे कोड लिखें।';

  @override
  String get scanRejectedTitle => 'यह टोकन स्वीकार नहीं किया जा सकता';

  @override
  String get scanInvalidSignature => 'यह QR कोड असली नहीं है। राशन न दें।';

  @override
  String get scanNotOurs => 'यह Smart Ration टोकन का QR कोड नहीं है।';

  @override
  String get scanUnreadable =>
      'QR कोड पढ़ा नहीं जा सका। फिर से स्कैन करें या कोड लिखें।';

  @override
  String get scanExpired => 'इस टोकन का राशन लेने का दिन निकल गया है।';

  @override
  String get scanNoBooking => 'इस कोड से कोई बुकिंग नहीं मिली।';

  @override
  String get scanWrongShop => 'यह टोकन किसी दूसरी राशन दुकान का है।';

  @override
  String get scanAlreadyCollected => 'इस टोकन पर राशन पहले ही दिया जा चुका है।';

  @override
  String get scanBookingCancelled => 'यह बुकिंग रद्द कर दी गई थी।';

  @override
  String get scanAgain => 'फिर से स्कैन करें';

  @override
  String get checkTitle => 'ग्राहक जाँच';

  @override
  String get readyTitle => 'राशन देने के लिए तैयार';

  @override
  String get readyBody => 'सभी जाँच सही हैं। नीचे दी गई चीज़ें दें।';

  @override
  String get blockedTitle => 'राशन न दें';

  @override
  String get identifiedByQr => 'QR कोड से पहचाना गया';

  @override
  String get identifiedByOtp => 'मोबाइल कोड से पहचाना गया';

  @override
  String get customer => 'ग्राहक';

  @override
  String get beneficiaryId => 'लाभार्थी ID';

  @override
  String get registeredMobile => 'पंजीकृत मोबाइल';

  @override
  String get checksTitle => 'जाँच';

  @override
  String get checkAadhaar => 'आधार सत्यापित';

  @override
  String get checkPassbook => 'पासबुक सत्यापित';

  @override
  String get checkMobile => 'मोबाइल नंबर सत्यापित';

  @override
  String get checkToken => 'टोकन राशन लेने के लिए मान्य';

  @override
  String get checkFamily => 'परिवार पात्र';

  @override
  String get checkEntitlement => 'इस महीने का राशन बाकी';

  @override
  String get checkPassed => 'हाँ';

  @override
  String get checkFailed => 'नहीं';

  @override
  String get itemsToHandOver => 'देने वाली चीज़ें';

  @override
  String get handOverButton => 'राशन दें और पुष्टि करें';

  @override
  String get handOverConfirmTitle => 'राशन देने की पुष्टि करें?';

  @override
  String handOverConfirmBody(String name) {
    return 'पुष्टि तभी करें जब आपने ये चीज़ें $name को दे दी हों। आपका स्टॉक कम हो जाएगा।';
  }

  @override
  String get notYet => 'अभी नहीं';

  @override
  String get yesHandedOver => 'हाँ, दे दिया';

  @override
  String get saving => 'सेव हो रहा है…';

  @override
  String get errorInsufficientStock =>
      'इस टोकन के लिए स्टॉक काफ़ी नहीं है। कुछ भी नहीं दिया गया और स्टॉक नहीं घटा।';

  @override
  String get errorConcurrentUpdate =>
      'यह टोकन अभी किसी दूसरे काउंटर पर बदला गया। कृपया फिर से स्कैन करें।';

  @override
  String get reasonAccountBlocked => 'यह लाभार्थी खाता रोका गया है।';

  @override
  String get reasonAccountInactive => 'यह लाभार्थी खाता सक्रिय नहीं है।';

  @override
  String get reasonTokenInvalid => 'यह टोकन राशन लेने के लिए मान्य नहीं है।';

  @override
  String get reasonAadhaarFailed => 'आधार सत्यापन विफल रहा।';

  @override
  String get reasonAadhaarExpired => 'आधार सत्यापन की अवधि समाप्त हो गई है।';

  @override
  String get reasonAadhaarPending => 'आधार सत्यापन बाकी है।';

  @override
  String get reasonPassbookPending => 'पासबुक सत्यापन बाकी है।';

  @override
  String get reasonMobileRequired =>
      'पहले ग्राहक का मोबाइल नंबर सत्यापित होना चाहिए।';

  @override
  String get reasonNotEligible => 'यह परिवार अपनी योजना के तहत पात्र नहीं है।';

  @override
  String get reasonNoEntitlement => 'इस महीने इस परिवार का राशन बाकी नहीं है।';

  @override
  String get otpCheckTitle => 'मोबाइल कोड से जाँचें';

  @override
  String get otpCheckHelp =>
      'ग्राहक का पंजीकृत मोबाइल नंबर लिखें। उस पर 6 अंकों का कोड भेजा जाएगा।';

  @override
  String get customerMobileLabel => 'ग्राहक का मोबाइल नंबर';

  @override
  String askCustomerForCode(String mobile, int minutes) {
    return '$mobile पर भेजा गया कोड ग्राहक से पूछें। यह $minutes मिनट तक मान्य है।';
  }

  @override
  String get verifyCodeButton => 'कोड जाँचें';

  @override
  String get otpNoCustomer => 'इस मोबाइल नंबर से कोई ग्राहक पंजीकृत नहीं है।';

  @override
  String get otpNoBookingHere =>
      'इस ग्राहक की आपकी दुकान पर कोई सक्रिय बुकिंग नहीं है।';

  @override
  String get receiptTitle => 'राशन दे दिया गया';

  @override
  String get receiptCollectionId => 'वितरण ID';

  @override
  String get receiptSaved =>
      'सेव हो गया। स्टॉक घटा दिया गया है और ग्राहक को सूचना भेज दी गई है।';

  @override
  String get scanNextCustomer => 'अगले ग्राहक का स्कैन करें';

  @override
  String get backToDashboard => 'डैशबोर्ड पर वापस';

  @override
  String get nothingToCheck =>
      'जाँचने के लिए कुछ नहीं। पहले QR कोड स्कैन करें।';

  @override
  String get queueButton => 'आज की कतार';

  @override
  String get stockButton => 'स्टॉक';

  @override
  String lowStockBanner(int count) {
    return '$count चीज़ों का स्टॉक कम है';
  }

  @override
  String queueWaitingHeader(int count) {
    return 'बाकी ($count)';
  }

  @override
  String queueDoneHeader(int count) {
    return 'पूरे ($count)';
  }

  @override
  String get queueEmpty => 'आज के लिए कोई टोकन बुक नहीं है।';

  @override
  String get queueServeHint =>
      'जब यह ग्राहक आए, उनका QR स्कैन करें या मोबाइल कोड से जाँचें।';

  @override
  String get stockAvailable => 'स्टॉक में';

  @override
  String get stockMinimum => 'न्यूनतम स्तर';

  @override
  String get stockHandedOut => 'बाँटा गया';

  @override
  String get stockLow => 'कम';

  @override
  String get stockOk => 'ठीक';

  @override
  String get noStockLines => 'इस दुकान के लिए अभी कोई स्टॉक नहीं है।';

  @override
  String get receiveStock => 'आया माल दर्ज करें';

  @override
  String get writeOffStock => 'खराब माल घटाएँ';

  @override
  String quantityLabel(String unit) {
    return 'मात्रा ($unit)';
  }

  @override
  String get referenceLabel => 'डिलीवरी या रिपोर्ट नंबर (वैकल्पिक)';

  @override
  String get noteLabel => 'टिप्पणी (वैकल्पिक)';

  @override
  String get quantityInvalid => '0 से अधिक मात्रा लिखें।';

  @override
  String get quantityTooLarge => '1,000,000 तक की मात्रा लिखें।';

  @override
  String writeOffTooMuch(String max, String unit) {
    return 'आप अधिकतम $max $unit घटा सकते हैं।';
  }

  @override
  String get referenceInvalid =>
      'केवल अक्षर, अंक, खाली जगह और - / _ . का उपयोग करें।';

  @override
  String get saveButton => 'सेव करें';

  @override
  String get cancelButton => 'रद्द करें';

  @override
  String writeOffConfirmTitle(String amount) {
    return '$amount घटाएँ?';
  }

  @override
  String get writeOffConfirmBody =>
      'यह खराब माल को हमेशा के लिए घटाता है। यह स्टॉक रजिस्टर में दर्ज होता है।';

  @override
  String get stockReceived => 'आया माल दर्ज हो गया।';

  @override
  String get stockWrittenOff => 'खराब माल घटा दिया गया।';

  @override
  String get officialTodayTitle => 'आज सभी दुकानों में';

  @override
  String get statShops => 'दुकानें';

  @override
  String get statBeneficiaries => 'लाभार्थी';

  @override
  String get statBookings => 'बुकिंग';

  @override
  String get statHandedOutToday => 'आज बाँटा गया';

  @override
  String get statLowStockAlerts => 'कम स्टॉक वाली चीज़ें';

  @override
  String get periodTitle => 'पिछले 30 दिन';

  @override
  String get statTokensBooked => 'बुक हुए टोकन';

  @override
  String get collectionRateLabel => 'राशन लेने की दर';

  @override
  String collectionRateValue(String percent) {
    return '$percent% बुक टोकन पर राशन लिया गया';
  }

  @override
  String alertsButton(int count) {
    return 'अलर्ट ($count)';
  }

  @override
  String get alertsTitle => 'अलर्ट';

  @override
  String get filterAll => 'सभी';

  @override
  String get stockCritical => 'गंभीर';

  @override
  String shopTodayLine(int booked, int collected) {
    return 'आज: $booked बुक · $collected दिया गया';
  }

  @override
  String get shopOwnerLabel => 'दुकानदार';

  @override
  String get shopPlaceLabel => 'स्थान';

  @override
  String get shopCodeLabel => 'दुकान कोड';

  @override
  String get noShops => 'कोई दुकान नहीं मिली।';

  @override
  String get alertsNotice =>
      'ये जाँचने लायक चेतावनियाँ हैं, धोखाधड़ी का सबूत नहीं। कार्रवाई से पहले जाँचें।';

  @override
  String get noAlerts => 'कोई खुला अलर्ट नहीं।';

  @override
  String get severityHigh => 'उच्च';

  @override
  String get severityMedium => 'मध्यम';

  @override
  String get severityLow => 'निम्न';

  @override
  String get alertDuplicateCollection => 'बार-बार राशन लेने की कोशिश';

  @override
  String get alertRepeatedQrScan => 'एक ही QR कई बार स्कैन';

  @override
  String get alertFailedVerification => 'बार-बार जाँच विफल';

  @override
  String get alertLowStock => 'कम स्टॉक';

  @override
  String get alertUnusualConsumption => 'असामान्य खपत';

  @override
  String get alertDetailsInEnglish => 'सिस्टम का विवरण (अंग्रेज़ी में):';
}
