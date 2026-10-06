// ignore: unused_import
import 'package:intl/intl.dart' as intl;

import 'app_localizations.dart';

// ignore_for_file: type=lint

/// The translations for Marathi (`mr`).
class AppLocalizationsMr extends AppLocalizations {
  AppLocalizationsMr([String locale = 'mr']) : super(locale);

  @override
  String get appTitle => 'स्मार्ट रेशन AI';

  @override
  String get poweredBy => 'HSD2C द्वारे संचालित';

  @override
  String get tagline => 'AI ची शक्ती · प्रत्येक कुटुंबासाठी';

  @override
  String get loading => 'लोड होत आहे...';

  @override
  String get logoDescription => 'स्मार्ट रेशन AI चा लोगो, HSD2C द्वारे संचालित';

  @override
  String get chooseLanguageTitle => 'तुमची भाषा निवडा';

  @override
  String get chooseLanguageHelp =>
      'तुम्ही ती नंतर स्क्रीनच्या वरच्या भाषा बटणावरून बदलू शकता.';

  @override
  String get continueButton => 'पुढे चला';

  @override
  String get language => 'भाषा';

  @override
  String get serverChecking => 'सर्व्हरशी कनेक्शन तपासत आहे…';

  @override
  String get serverConnected => 'सर्व्हरशी जोडले गेले';

  @override
  String get serverNoDatabase =>
      'सर्व्हर त्याच्या डेटाबेसपर्यंत पोहोचू शकत नाही';

  @override
  String get statusOverall => 'एकूण स्थिती';

  @override
  String get statusDatabase => 'डेटाबेस';

  @override
  String get statusData => 'डेटा';

  @override
  String get statusHealthy => 'व्यवस्थित';

  @override
  String get statusDegraded => 'अंशतः सुरू';

  @override
  String get statusUnhealthy => 'काम करत नाही';

  @override
  String get statusUnknown => 'अज्ञात';

  @override
  String get dataSynthetic => 'डेमो डेटा (सिंथेटिक)';

  @override
  String get dataReal => 'वास्तविक डेटा';

  @override
  String serverAddress(String url, String environment) {
    return 'सर्व्हर: $url · $environment';
  }

  @override
  String get tryAgain => 'पुन्हा प्रयत्न करा';

  @override
  String get errorNoConnection =>
      'कनेक्ट होऊ शकले नाही. कृपया तुमचे इंटरनेट कनेक्शन तपासा.';

  @override
  String get errorTimeout =>
      'सर्व्हर उत्तर द्यायला खूप वेळ घेत आहे. कृपया पुन्हा प्रयत्न करा.';

  @override
  String get errorSessionEnded =>
      'तुमचे सत्र संपले आहे. कृपया पुन्हा साइन इन करा.';

  @override
  String get errorTooManyRequests =>
      'खूप जास्त प्रयत्न झाले. कृपया एक मिनिट थांबून पुन्हा प्रयत्न करा.';

  @override
  String get errorServer =>
      'सर्व्हरमध्ये अडचण आली. कृपया काही मिनिटांनी पुन्हा प्रयत्न करा.';

  @override
  String get errorGeneric => 'काहीतरी चुकले. कृपया पुन्हा प्रयत्न करा.';

  @override
  String get errorForbidden => 'तुम्हाला हे करण्याची परवानगी नाही.';

  @override
  String get errorNotFound => 'मागितलेली माहिती सापडली नाही.';

  @override
  String get errorRequestFailed =>
      'विनंती पूर्ण होऊ शकली नाही. कृपया तपासून पुन्हा प्रयत्न करा.';

  @override
  String get signInTitle => 'साइन इन करा';

  @override
  String get signInSubtitle =>
      'तुमच्या स्मार्ट रेशन खात्याचा ईमेल आणि पासवर्ड वापरा.';

  @override
  String get emailLabel => 'ईमेल';

  @override
  String get passwordLabel => 'पासवर्ड';

  @override
  String get showPassword => 'पासवर्ड दाखवा';

  @override
  String get hidePassword => 'पासवर्ड लपवा';

  @override
  String get signInButton => 'साइन इन करा';

  @override
  String get signingIn => 'साइन इन होत आहे...';

  @override
  String get emailRequired => 'कृपया तुमचा ईमेल टाका.';

  @override
  String get emailInvalid => 'कृपया योग्य ईमेल पत्ता टाका.';

  @override
  String get passwordRequired => 'कृपया तुमचा पासवर्ड टाका.';

  @override
  String get loginInvalid => 'ईमेल किंवा पासवर्ड चुकीचा आहे.';

  @override
  String get loginAccountDisabled =>
      'हे खाते बंद केले आहे. कृपया तुमच्या रेशन दुकानाशी किंवा जिल्हा कार्यालयाशी संपर्क साधा.';

  @override
  String get demoAccountsTitle => 'डेमो खाती (फक्त डेव्हलपमेंट बिल्डमध्ये)';

  @override
  String get demoAccountsHelp =>
      'ईमेल भरण्यासाठी एकावर टॅप करा. डेमो पासवर्ड प्रोजेक्टच्या README मध्ये आहे.';

  @override
  String get checkServer => 'सर्व्हर कनेक्शन तपासा';

  @override
  String get serverStatusTitle => 'सर्व्हरची स्थिती';

  @override
  String get roleRuralUser => 'ग्रामीण वापरकर्ता';

  @override
  String get roleShopOwner => 'दुकान मालक';

  @override
  String get roleOfficial => 'सरकारी अधिकारी';

  @override
  String get roleAdmin => 'प्रशासक';

  @override
  String greeting(String name) {
    return 'नमस्कार, $name';
  }

  @override
  String get signOut => 'साइन आउट';

  @override
  String shopLinked(int id) {
    return 'रेशन दुकान क्र. $id';
  }

  @override
  String get citizenDashboardIntro =>
      'तुमचे रेशन कार्ड, कुटुंबातील सदस्य, बुकिंग आणि टोकन येथे दिसतील.';

  @override
  String get shopDashboardIntro =>
      'आजचे टोकन, QR स्कॅनर, साठा आणि वितरण येथे दिसतील.';

  @override
  String get officialDashboardIntro =>
      'दुकाने, वितरण, साठ्याचे इशारे आणि अहवाल येथे दिसतील.';

  @override
  String get signInWithMobile => 'मोबाइल व कोड';

  @override
  String get signInWithEmail => 'ईमेल व पासवर्ड';

  @override
  String get mobileSignInSubtitle =>
      'आम्ही तुमच्या नोंदणीकृत मोबाइल नंबरवर 6 अंकी कोड पाठवू.';

  @override
  String get mobileLabel => 'मोबाइल नंबर';

  @override
  String get mobileInvalid => 'कृपया 10 अंकी मोबाइल नंबर टाका.';

  @override
  String get sendCode => 'कोड पाठवा';

  @override
  String get sendingCode => 'कोड पाठवत आहे...';

  @override
  String codeSentTo(String mobile) {
    return '$mobile नोंदणीकृत असल्यास त्यावर कोड पाठवला आहे.';
  }

  @override
  String get codeLabel => '6 अंकी कोड';

  @override
  String get codeInvalidFormat => 'कृपया 6 अंकी कोड टाका.';

  @override
  String get otpInvalid =>
      'कोड चुकीचा आहे किंवा त्याची मुदत संपली आहे. कृपया पुन्हा प्रयत्न करा किंवा नवीन कोड मागवा.';

  @override
  String get otpSendFailed =>
      'आत्ता कोड पाठवता आला नाही. कृपया पुन्हा प्रयत्न करा किंवा ईमेल व पासवर्डने साइन इन करा.';

  @override
  String resendIn(int seconds) {
    return '$seconds सेकंदांत नवीन कोड पाठवा';
  }

  @override
  String get resendCode => 'नवीन कोड पाठवा';

  @override
  String get changeNumber => 'नंबर बदला';

  @override
  String demoCodeHint(String code) {
    return 'डेव्हलपमेंट डेमो कोड: $code';
  }

  @override
  String get otpStaffNote =>
      'रेशन दुकानदार आणि अधिकारी ईमेल व पासवर्डने साइन इन करतात.';

  @override
  String get rationCard => 'रेशन कार्ड';

  @override
  String get cardNumber => 'कार्ड क्रमांक';

  @override
  String get cardScheme => 'कार्डचा प्रकार (योजना)';

  @override
  String get cardStatus => 'स्थिती';

  @override
  String get cardActive => 'सक्रिय';

  @override
  String get cardInactive => 'निष्क्रिय';

  @override
  String get familyId => 'कुटुंब आयडी';

  @override
  String get familySizeLabel => 'कुटुंबाचा आकार';

  @override
  String memberCount(int count) {
    return '$count सदस्य';
  }

  @override
  String get assignedShop => 'रेशन दुकान';

  @override
  String get familyMembers => 'कुटुंबातील सदस्य';

  @override
  String ageYears(int age) {
    return '$age वर्षे';
  }

  @override
  String get relHead => 'कुटुंबप्रमुख';

  @override
  String get relSpouse => 'पती/पत्नी';

  @override
  String get relSon => 'मुलगा';

  @override
  String get relDaughter => 'मुलगी';

  @override
  String get relParent => 'आई/वडील';

  @override
  String get relOther => 'इतर नातेवाईक';

  @override
  String get memberEligible => 'पात्र';

  @override
  String get memberNotEligible => 'अपात्र';

  @override
  String get memberPending => 'प्रलंबित';

  @override
  String get memberVerificationRequired => 'पडताळणी आवश्यक';

  @override
  String get eligibilityTitle => 'पात्रता';

  @override
  String get familyEligible => 'पात्र';

  @override
  String get familyPartiallyEligible => 'अंशतः पात्र';

  @override
  String get familyNotEligible => 'अपात्र';

  @override
  String eligibleMembersOf(int eligible, int total) {
    return '$total पैकी $eligible सदस्य पात्र';
  }

  @override
  String get eligibilityExplainEligible =>
      'तुमच्या कुटुंबातील सर्व सदस्य या महिन्यात रेशन घेऊ शकतात.';

  @override
  String get eligibilityExplainPartial =>
      'काही सदस्य अद्याप पात्र नाहीत. तुमचा हक्क फक्त पात्र सदस्यांवर मोजला जातो.';

  @override
  String get eligibilityExplainNot =>
      'तुमचे कुटुंब सध्या रेशन घेऊ शकत नाही. कृपया तुमच्या रेशन दुकानाशी किंवा जिल्हा कार्यालयाशी संपर्क साधा.';

  @override
  String get monthlyEntitlement => 'या महिन्याचा हक्क';

  @override
  String remainingOf(String remaining, String total, String unit) {
    return '$total $unit पैकी $remaining $unit शिल्लक';
  }

  @override
  String collectedAmount(String amount, String unit) {
    return 'घेतले: $amount $unit';
  }

  @override
  String get itemRice => 'तांदूळ';

  @override
  String get itemWheat => 'गहू';

  @override
  String get itemSugar => 'साखर';

  @override
  String get itemPulses => 'डाळी';

  @override
  String get itemOil => 'खाद्यतेल';

  @override
  String get itemSalt => 'मीठ';

  @override
  String get unitKg => 'किलो';

  @override
  String get unitLitre => 'लिटर';

  @override
  String get collectionHistory => 'रेशन घेतल्याचा इतिहास';

  @override
  String get noCollections => 'अद्याप रेशन घेतलेले नाही.';

  @override
  String get aadhaarVerified => 'आधार पडताळलेले';

  @override
  String get aadhaarNotVerified => 'आधार पडताळलेले नाही';

  @override
  String get viewDetails => 'तपशील पहा';

  @override
  String get noBeneficiaryProfile =>
      'तुमचे रेशन कार्ड अद्याप जोडलेले नाही. कृपया तुमच्या रेशन दुकानाशी संपर्क साधा.';

  @override
  String get demoDataNotice => 'डेमो डेटा: हे खरे रेशन कार्ड नाही.';

  @override
  String get genderMale => 'पुरुष';

  @override
  String get genderFemale => 'स्त्री';

  @override
  String get genderOther => 'इतर';

  @override
  String get bookRation => 'रेशन बुक करा';

  @override
  String get stepDay => '1. दिवस निवडा';

  @override
  String get stepTime => '2. 5 मिनिटांची वेळ निवडा';

  @override
  String get stepItems => '3. वस्तू निवडा';

  @override
  String get today => 'आज';

  @override
  String get tomorrow => 'उद्या';

  @override
  String get noSlots =>
      'या दिवशी कोणतीही वेळ उपलब्ध नाही. कृपया दुसरा दिवस निवडा.';

  @override
  String get slotFull => 'भरले';

  @override
  String placesLeft(int count) {
    return '$count शिल्लक';
  }

  @override
  String perVisitLimit(String amount, String unit) {
    return 'या वेळी जास्तीत जास्त $amount $unit';
  }

  @override
  String get notAvailableNow => 'सध्या उपलब्ध नाही';

  @override
  String increaseItem(String item) {
    return '$item वाढवा';
  }

  @override
  String decreaseItem(String item) {
    return '$item कमी करा';
  }

  @override
  String get bookAndGetToken => 'बुक करा आणि टोकन मिळवा';

  @override
  String get bookingInProgress => 'बुकिंग होत आहे...';

  @override
  String get chooseTimeFirst => 'कृपया वेळ निवडा.';

  @override
  String get chooseItemFirst => 'कृपया किमान एक वस्तू निवडा.';

  @override
  String get noShopAssigned =>
      'तुमचे रेशन दुकान अद्याप ठरलेले नाही. कृपया जिल्हा कार्यालयाशी संपर्क साधा.';

  @override
  String get tokenReady => 'तुमचे टोकन तयार आहे.';

  @override
  String get myToken => 'माझे टोकन';

  @override
  String get myTokens => 'माझी टोकने';

  @override
  String get tokenNumber => 'टोकन क्रमांक';

  @override
  String get collectionDate => 'तारीख';

  @override
  String get collectionTime => 'वेळ';

  @override
  String get tokenItems => 'वस्तू';

  @override
  String get stateBooked => 'बुक केले';

  @override
  String get stateCollected => 'घेतले';

  @override
  String get stateCancelled => 'रद्द';

  @override
  String get stateMissed => 'चुकले';

  @override
  String get showQrAtShop => 'रेशन दुकानात हा QR कोड दाखवा.';

  @override
  String get qrManualCode =>
      'QR स्कॅन न झाल्यास दुकानदार हा कोड टाइप करू शकतो:';

  @override
  String get qrNoPersonalData => 'QR कोडमध्ये कोणतीही वैयक्तिक माहिती नाही.';

  @override
  String qrCodeLabel(String number) {
    return 'टोकन $number चा QR कोड';
  }

  @override
  String get cancelBooking => 'बुकिंग रद्द करा';

  @override
  String get cancelConfirmTitle => 'ही बुकिंग रद्द करायची?';

  @override
  String get cancelConfirmBody => 'तुमची वेळ दुसऱ्या कोणासाठी मोकळी होईल.';

  @override
  String get keepBooking => 'राहू द्या';

  @override
  String get bookingCancelled => 'बुकिंग रद्द झाली.';

  @override
  String get noTokens => 'तुमच्याकडे अद्याप टोकन नाही.';

  @override
  String get nextCollection => 'तुमचे पुढील रेशन';

  @override
  String get noUpcomingBooking =>
      'पुढील बुकिंग नाही. रेशन घेण्यासाठी वेळ बुक करा.';

  @override
  String get showQr => 'QR कोड दाखवा';

  @override
  String get allMyTokens => 'माझी सर्व टोकने';

  @override
  String get shopTodayTitle => 'आज तुमच्या दुकानात';

  @override
  String get shopTokensToday => 'टोकन';

  @override
  String get shopCollected => 'दिले';

  @override
  String get shopWaiting => 'बाकी';

  @override
  String get shopCancelled => 'रद्द';

  @override
  String get scanCustomerQr => 'ग्राहकाचा QR स्कॅन करा';

  @override
  String get verifyByMobile => 'QR नाही? मोबाइल कोडने तपासा';

  @override
  String get scannerTitle => 'QR कोड स्कॅन करा';

  @override
  String get scannerHelp => 'कॅमेरा ग्राहकाच्या QR कोडकडे धरा.';

  @override
  String get typeCodeLabel => 'किंवा QR खाली दिसणारा कोड लिहा';

  @override
  String get typeCodeInvalid => 'कृपया SRQR- ने सुरू होणारा कोड लिहा.';

  @override
  String get checkCode => 'तपासा';

  @override
  String get checking => 'तपासत आहे…';

  @override
  String get cameraDenied =>
      'कॅमेऱ्याची परवानगी बंद आहे. फोनच्या सेटिंगमध्ये परवानगी द्या, किंवा खाली कोड लिहा.';

  @override
  String get cameraUnavailable =>
      'कॅमेरा सुरू होऊ शकला नाही. त्याऐवजी खाली कोड लिहा.';

  @override
  String get scanRejectedTitle => 'हे टोकन स्वीकारता येत नाही';

  @override
  String get scanInvalidSignature => 'हा QR कोड खरा नाही. रेशन देऊ नका.';

  @override
  String get scanNotOurs => 'हा Smart Ration टोकनचा QR कोड नाही.';

  @override
  String get scanUnreadable =>
      'QR कोड वाचता आला नाही. पुन्हा स्कॅन करा किंवा कोड लिहा.';

  @override
  String get scanExpired => 'या टोकनचा रेशन घेण्याचा दिवस निघून गेला आहे.';

  @override
  String get scanNoBooking => 'या कोडशी जुळणारी बुकिंग नाही.';

  @override
  String get scanWrongShop => 'हे टोकन दुसऱ्या रेशन दुकानाचे आहे.';

  @override
  String get scanAlreadyCollected => 'या टोकनवर रेशन आधीच दिले गेले आहे.';

  @override
  String get scanBookingCancelled => 'ही बुकिंग रद्द केली होती.';

  @override
  String get scanAgain => 'पुन्हा स्कॅन करा';

  @override
  String get checkTitle => 'ग्राहक तपासणी';

  @override
  String get readyTitle => 'रेशन देण्यास तयार';

  @override
  String get readyBody => 'सर्व तपासण्या बरोबर आहेत. खालील वस्तू द्या.';

  @override
  String get blockedTitle => 'रेशन देऊ नका';

  @override
  String get identifiedByQr => 'QR कोडने ओळखले';

  @override
  String get identifiedByOtp => 'मोबाइल कोडने ओळखले';

  @override
  String get customer => 'ग्राहक';

  @override
  String get beneficiaryId => 'लाभार्थी ID';

  @override
  String get registeredMobile => 'नोंदणीकृत मोबाइल';

  @override
  String get checksTitle => 'तपासण्या';

  @override
  String get checkAadhaar => 'आधार पडताळले';

  @override
  String get checkPassbook => 'पासबुक पडताळले';

  @override
  String get checkMobile => 'मोबाइल नंबर पडताळला';

  @override
  String get checkToken => 'टोकन रेशनसाठी वैध';

  @override
  String get checkFamily => 'कुटुंब पात्र';

  @override
  String get checkEntitlement => 'या महिन्याचे रेशन बाकी';

  @override
  String get checkPassed => 'होय';

  @override
  String get checkFailed => 'नाही';

  @override
  String get itemsToHandOver => 'द्यायच्या वस्तू';

  @override
  String get handOverButton => 'रेशन द्या आणि खात्री करा';

  @override
  String get handOverConfirmTitle => 'रेशन दिल्याची खात्री करायची?';

  @override
  String handOverConfirmBody(String name) {
    return '$name यांना या वस्तू दिल्यानंतरच खात्री करा. तुमचा साठा कमी होईल.';
  }

  @override
  String get notYet => 'अजून नाही';

  @override
  String get yesHandedOver => 'होय, दिले';

  @override
  String get saving => 'जतन होत आहे…';

  @override
  String get errorInsufficientStock =>
      'या टोकनसाठी पुरेसा साठा नाही. काहीही दिले नाही आणि साठा कमी झाला नाही.';

  @override
  String get errorConcurrentUpdate =>
      'हे टोकन आत्ताच दुसऱ्या काउंटरवर बदलले. कृपया पुन्हा स्कॅन करा.';

  @override
  String get reasonAccountBlocked => 'हे लाभार्थी खाते रोखले आहे.';

  @override
  String get reasonAccountInactive => 'हे लाभार्थी खाते सक्रिय नाही.';

  @override
  String get reasonTokenInvalid => 'हे टोकन रेशनसाठी वैध नाही.';

  @override
  String get reasonAadhaarFailed => 'आधार पडताळणी अयशस्वी झाली.';

  @override
  String get reasonAadhaarExpired => 'आधार पडताळणीची मुदत संपली आहे.';

  @override
  String get reasonAadhaarPending => 'आधार पडताळणी बाकी आहे.';

  @override
  String get reasonPassbookPending => 'पासबुक पडताळणी बाकी आहे.';

  @override
  String get reasonMobileRequired =>
      'आधी ग्राहकाचा मोबाइल नंबर पडताळला गेला पाहिजे.';

  @override
  String get reasonNotEligible => 'हे कुटुंब त्याच्या योजनेअंतर्गत पात्र नाही.';

  @override
  String get reasonNoEntitlement => 'या महिन्यात या कुटुंबाचे रेशन बाकी नाही.';

  @override
  String get otpCheckTitle => 'मोबाइल कोडने तपासा';

  @override
  String get otpCheckHelp =>
      'ग्राहकाचा नोंदणीकृत मोबाइल नंबर लिहा. त्यावर 6 अंकी कोड पाठवला जाईल.';

  @override
  String get customerMobileLabel => 'ग्राहकाचा मोबाइल नंबर';

  @override
  String askCustomerForCode(String mobile, int minutes) {
    return '$mobile वर पाठवलेला कोड ग्राहकाला विचारा. तो $minutes मिनिटे वैध आहे.';
  }

  @override
  String get verifyCodeButton => 'कोड तपासा';

  @override
  String get otpNoCustomer => 'या मोबाइल नंबरवर कोणताही ग्राहक नोंदणीकृत नाही.';

  @override
  String get otpNoBookingHere =>
      'या ग्राहकाची तुमच्या दुकानात कोणतीही सक्रिय बुकिंग नाही.';

  @override
  String get receiptTitle => 'रेशन दिले';

  @override
  String get receiptCollectionId => 'वितरण ID';

  @override
  String get receiptSaved =>
      'जतन झाले. साठा कमी केला आहे आणि ग्राहकाला सूचना पाठवली आहे.';

  @override
  String get scanNextCustomer => 'पुढच्या ग्राहकाचे स्कॅन करा';

  @override
  String get backToDashboard => 'डॅशबोर्डवर परत';

  @override
  String get nothingToCheck => 'तपासण्यासारखे काही नाही. आधी QR कोड स्कॅन करा.';

  @override
  String get queueButton => 'आजची रांग';

  @override
  String get stockButton => 'साठा';

  @override
  String lowStockBanner(int count) {
    return '$count वस्तूंचा साठा कमी आहे';
  }

  @override
  String queueWaitingHeader(int count) {
    return 'बाकी ($count)';
  }

  @override
  String queueDoneHeader(int count) {
    return 'पूर्ण ($count)';
  }

  @override
  String get queueEmpty => 'आजसाठी कोणतेही टोकन बुक केलेले नाही.';

  @override
  String get queueServeHint =>
      'हा ग्राहक आल्यावर त्यांचा QR स्कॅन करा किंवा मोबाइल कोडने तपासा.';

  @override
  String get stockAvailable => 'साठ्यात';

  @override
  String get stockMinimum => 'किमान पातळी';

  @override
  String get stockHandedOut => 'वाटप केले';

  @override
  String get stockLow => 'कमी';

  @override
  String get stockOk => 'ठीक';

  @override
  String get noStockLines => 'या दुकानासाठी अजून कोणताही साठा नाही.';

  @override
  String get receiveStock => 'आलेला माल नोंदवा';

  @override
  String get writeOffStock => 'खराब माल वजा करा';

  @override
  String quantityLabel(String unit) {
    return 'प्रमाण ($unit)';
  }

  @override
  String get referenceLabel => 'डिलिव्हरी किंवा अहवाल क्रमांक (ऐच्छिक)';

  @override
  String get noteLabel => 'टीप (ऐच्छिक)';

  @override
  String get stockAlreadySaved =>
      'हे आत्ताच जतन झाले आहे. हा फॉर्म बंद करा आणि पुन्हा नोंदवण्यापूर्वी साठा तपासा.';

  @override
  String get quantityInvalid => '0 पेक्षा जास्त प्रमाण लिहा.';

  @override
  String get quantityTooLarge => '1,000,000 पर्यंत प्रमाण लिहा.';

  @override
  String writeOffTooMuch(String max, String unit) {
    return 'तुम्ही जास्तीत जास्त $max $unit वजा करू शकता.';
  }

  @override
  String get referenceInvalid =>
      'फक्त अक्षरे, अंक, मोकळी जागा आणि - / _ . वापरा.';

  @override
  String get saveButton => 'जतन करा';

  @override
  String get cancelButton => 'रद्द करा';

  @override
  String writeOffConfirmTitle(String amount) {
    return '$amount वजा करायचे?';
  }

  @override
  String get writeOffConfirmBody =>
      'यामुळे खराब माल कायमचा वजा होतो. हे साठा नोंदवहीत नोंदवले जाते.';

  @override
  String get stockReceived => 'आलेला माल नोंदवला.';

  @override
  String get stockWrittenOff => 'खराब माल वजा केला.';

  @override
  String get officialTodayTitle => 'आज सर्व दुकानांमध्ये';

  @override
  String get statShops => 'दुकाने';

  @override
  String get statBeneficiaries => 'लाभार्थी';

  @override
  String get statBookings => 'बुकिंग';

  @override
  String get statHandedOutToday => 'आज वाटप';

  @override
  String get statLowStockAlerts => 'कमी साठ्याच्या वस्तू';

  @override
  String get periodTitle => 'मागील 30 दिवस';

  @override
  String get statTokensBooked => 'बुक झालेली टोकने';

  @override
  String get collectionRateLabel => 'रेशन घेण्याचा दर';

  @override
  String collectionRateValue(String percent) {
    return '$percent% बुक टोकनवर रेशन घेतले';
  }

  @override
  String alertsButton(int count) {
    return 'सूचना ($count)';
  }

  @override
  String get alertsTitle => 'सूचना';

  @override
  String get filterAll => 'सर्व';

  @override
  String get stockCritical => 'गंभीर';

  @override
  String shopTodayLine(int booked, int collected) {
    return 'आज: $booked बुक · $collected दिले';
  }

  @override
  String get shopOwnerLabel => 'दुकानदार';

  @override
  String get shopPlaceLabel => 'ठिकाण';

  @override
  String get shopCodeLabel => 'दुकान कोड';

  @override
  String get noShops => 'कोणतेही दुकान सापडले नाही.';

  @override
  String get alertsNotice =>
      'या तपासण्याजोग्या सूचना आहेत, फसवणुकीचा पुरावा नाही. कारवाईपूर्वी तपासा.';

  @override
  String get noAlerts => 'कोणतीही उघडी सूचना नाही.';

  @override
  String get severityHigh => 'उच्च';

  @override
  String get severityMedium => 'मध्यम';

  @override
  String get severityLow => 'कमी';

  @override
  String get alertDuplicateCollection => 'वारंवार रेशन घेण्याचा प्रयत्न';

  @override
  String get alertRepeatedQrScan => 'एकच QR अनेक वेळा स्कॅन';

  @override
  String get alertFailedVerification => 'वारंवार तपासणी अयशस्वी';

  @override
  String get alertLowStock => 'कमी साठा';

  @override
  String get alertUnusualConsumption => 'असामान्य वापर';

  @override
  String get alertDetailsInEnglish => 'प्रणालीकडील तपशील (इंग्रजीत):';

  @override
  String get alertUpdateButton => 'अद्ययावत करा';

  @override
  String get alertUpdateTitle => 'ही सूचना अद्ययावत करा';

  @override
  String get alertStatusUnderReview => 'तपासणी सुरू';

  @override
  String get alertChooseReviewHint => 'तुम्ही ती तपासत आहात. ती यादीत राहील.';

  @override
  String get alertChooseResolved => 'सोडवली';

  @override
  String get alertChooseResolvedHint => 'समस्या होती आणि ती सोडवली आहे.';

  @override
  String get alertChooseDismissed => 'समस्या नाही';

  @override
  String get alertChooseDismissedHint => 'तपासले: काहीही चुकीचे नव्हते.';

  @override
  String get alertNoteHint => 'आधार क्रमांक, OTP किंवा पासवर्ड लिहू नका.';

  @override
  String get alertReviewNote => 'अधिकाऱ्याची टीप';

  @override
  String get alertUpdated => 'सूचना अद्ययावत झाली';

  @override
  String get helpTitle => 'मदत — रेशन मित्र';

  @override
  String get helpButton => 'मदत';

  @override
  String get assistantName => 'रेशन मित्र';

  @override
  String get youLabel => 'तुम्ही';

  @override
  String get helpPrivacy =>
      'आधार क्रमांक, OTP किंवा पासवर्ड लिहू नका. तुम्ही लिहिलेले या फोनवर जतन होत नाही.';

  @override
  String get askHint => 'तुमचा प्रश्न लिहा';

  @override
  String get sendQuestion => 'पाठवा';

  @override
  String get speakQuestion => 'बोलून विचारा';

  @override
  String get stopListening => 'ऐकणे थांबवा';

  @override
  String get listening => 'ऐकत आहे… आता बोला';

  @override
  String get voiceNote =>
      'तुमच्या फोनची स्पीच सेवा आवाजाचे मजकुरात रूपांतर करते आणि त्यासाठी इंटरनेट वापरू शकते.';

  @override
  String get voiceUnavailable =>
      'आवाजाने विचारणे उपलब्ध नाही. सेटिंगमध्ये मायक्रोफोनला परवानगी द्या, किंवा प्रश्न लिहा.';

  @override
  String get readAloud => 'वाचून दाखवा';

  @override
  String get stopReading => 'वाचन थांबवा';

  @override
  String get voiceMissing =>
      'या फोनमध्ये या भाषेचा आवाज नाही. फोनच्या टेक्स्ट-टू-स्पीच सेटिंगमध्ये जोडू शकता.';

  @override
  String get relatedTitle => 'संबंधित';

  @override
  String get thinking => 'रेशन मित्र लिहित आहे…';

  @override
  String get noSpeechHeard => 'काहीच ऐकू आले नाही. माइक दाबून पुन्हा बोला.';

  @override
  String get offlineBanner =>
      'इंटरनेट नाही. या फोनवर जतन केलेली माहिती दिसत आहे; ती जुनी असू शकते. ताजी करण्यासाठी खाली ओढा.';

  @override
  String get offlineQrNote =>
      'हे या फोनवर जतन आहे. तुमच्या इंटरनेटशिवायही दुकान हा QR स्कॅन करू शकते.';

  @override
  String get notificationsTitle => 'सूचना';

  @override
  String notificationsTooltip(int count) {
    String _temp0 = intl.Intl.pluralLogic(
      count,
      locale: localeName,
      other: 'सूचना, $count नवीन',
      zero: 'सूचना',
    );
    return '$_temp0';
  }

  @override
  String get noNotifications => 'अजून कोणतीही सूचना नाही.';

  @override
  String get newLabel => 'नवीन';

  @override
  String get nBookingConfirmed => 'बुकिंग निश्चित झाली';

  @override
  String get nTokenGenerated => 'टोकन तयार';

  @override
  String get nSlotReminder => 'आठवण: तुमची रेशन घेण्याची वेळ';

  @override
  String get nCollectionCompleted => 'रेशन मिळाले';

  @override
  String get nBookingCancelled => 'बुकिंग रद्द';

  @override
  String get nLowInventory => 'कमी साठा';

  @override
  String get nVerificationResult => 'पडताळणी निकाल';

  @override
  String get nAlert => 'सूचना';

  @override
  String get complaintTitle => 'समस्या कळवा';

  @override
  String get complaintWhat => 'काय समस्या आहे?';

  @override
  String get catLessRation => 'रेशन कमी मिळाले';

  @override
  String get catPoorQuality => 'धान्य खराब होते';

  @override
  String get catShopClosed => 'दुकान बंद होते';

  @override
  String get catOvercharged => 'जास्त पैसे मागितले';

  @override
  String get catTokenProblem => 'टोकन किंवा QR ची समस्या';

  @override
  String get catVerificationProblem => 'ओळख पडताळणीची समस्या';

  @override
  String get catStaffBehaviour => 'उद्धट वागणूक';

  @override
  String get catOther => 'दुसरे काही';

  @override
  String get complaintItem => 'कोणती वस्तू? (ऐच्छिक)';

  @override
  String get complaintNoItem => 'एक वस्तू नाही';

  @override
  String get complaintDescribe => 'काय झाले ते सांगा';

  @override
  String get complaintDescribeHint =>
      'उदाहरण: या महिन्यात मला 2 किलो गहू कमी मिळाला.';

  @override
  String get complaintDescribeShort =>
      'कृपया थोडे अधिक लिहा (किमान 10 अक्षरे).';

  @override
  String get complaintNoPrivate => 'आधार क्रमांक, OTP किंवा पासवर्ड लिहू नका.';

  @override
  String get complaintChooseCategory => 'समस्या निवडा.';

  @override
  String get complaintYourDetails => 'तुमचा तपशील (तुमच्या खात्यातून)';

  @override
  String get complaintNameLabel => 'नाव';

  @override
  String get complaintReviewButton => 'तपासा';

  @override
  String get complaintReviewTitle => 'पाठवण्यापूर्वी तपासा';

  @override
  String get complaintReviewNote =>
      'सादर करण्यापूर्वी कृपया तुमची माहिती तपासा.';

  @override
  String get complaintEdit => 'बदला';

  @override
  String get complaintSubmit => 'खात्री करा आणि पाठवा';

  @override
  String get complaintSent => 'तक्रार नोंदवली गेली';

  @override
  String get complaintReference => 'संदर्भ क्रमांक';

  @override
  String complaintSentSpoken(String reference) {
    return 'तुमची तक्रार यशस्वीपणे नोंदवली गेली आहे. तुमचा संदर्भ क्रमांक $reference आहे.';
  }

  @override
  String get complaintKeepReference =>
      'हा क्रमांक जपून ठेवा. स्थिती बदलल्यावर तुम्हाला सूचनांमध्ये कळवले जाईल.';

  @override
  String get complaintFilledByAi =>
      'तुम्ही सांगितलेल्यावरून भरले आहे. कृपया तपासा.';

  @override
  String get myComplaints => 'माझ्या तक्रारी';

  @override
  String get noComplaints => 'तुम्ही कोणतीही समस्या नोंदवलेली नाही.';

  @override
  String get complaintStatusSubmitted => 'मिळाली';

  @override
  String get complaintStatusUnderReview => 'तपासणी सुरू';

  @override
  String get complaintStatusResolved => 'सोडवली';

  @override
  String get complaintStatusRejected => 'बंद';

  @override
  String get complaintOfficeReply => 'कार्यालयाचे उत्तर';

  @override
  String get doneButton => 'झाले';

  @override
  String get nComplaint => 'तक्रार';

  @override
  String get aiButton => 'AI ला विचारा';

  @override
  String get aiHowCanIHelp => 'मी तुमची कशी मदत करू?';

  @override
  String get aiTypeHint => 'तुम्हाला काय हवे ते बोला किंवा लिहा';

  @override
  String get aiExample =>
      'उदाहरण: “माझं रेशन कधी मिळेल?” किंवा “मला गहू कमी मिळाला, तक्रार करायची आहे.”';

  @override
  String get aiReadScreen => 'ही स्क्रीन वाचा';

  @override
  String get aiNothingToRead => 'या स्क्रीनवर अजून वाचण्यासारखे काही नाही.';

  @override
  String get aiLanguageChanged => 'भाषा बदलली.';

  @override
  String aiHomeSummary(
    String token,
    String day,
    String start,
    String end,
    String shop,
  ) {
    return 'तुमचे पुढील रेशन: टोकन $token, $day, $start ते $end, $shop येथे.';
  }

  @override
  String get aiHomeNoBooking =>
      'तुमची कोणतीही रेशन बुकिंग नाही. बुक करण्यासाठी “रेशन बुक करा” म्हणा.';

  @override
  String get aiSignInHelp => 'साइन इन करण्यासाठी मदत हवी? AI ला विचारा';

  @override
  String get nAnnouncement => 'घोषणा';

  @override
  String get mfaPrompt =>
      'या खात्यासाठी दोन-टप्पी साइन इन चालू आहे. आपल्या ऑथेंटिकेटर अॅपमधील 6 अंकी कोड टाका.';

  @override
  String get mfaCodeLabel => 'ऑथेंटिकेटर अॅपमधील कोड';

  @override
  String get mfaCodeWrong =>
      'कोड चुकीचा आहे किंवा त्याची मुदत संपली आहे. ऑथेंटिकेटर अॅपमधील सध्याचा कोड वापरा.';

  @override
  String get mfaExpired =>
      'साइन इनला खूप वेळ लागला. कृपया आपला ईमेल आणि पासवर्ड पुन्हा टाका.';

  @override
  String get mfaStartAgain => 'पुन्हा सुरू करा';

  @override
  String get forgotPassword => 'पासवर्ड विसरलात?';

  @override
  String get resetTitle => 'आपला पासवर्ड रीसेट करा';

  @override
  String get resetIntro =>
      'आपल्या खात्याशी जोडलेला मोबाइल नंबर टाका. आम्ही त्यावर 6 अंकी कोड पाठवू.';

  @override
  String resetCodeSent(String mobile) {
    return '$mobile नोंदणीकृत असल्यास त्यावर 6 अंकी कोड पाठवला आहे.';
  }

  @override
  String get resetSendCode => 'कोड पाठवा';

  @override
  String get resetSetPassword => 'नवीन पासवर्ड सेट करा';

  @override
  String get resetDone => 'पासवर्ड बदलला. कृपया नवीन पासवर्डने साइन इन करा.';

  @override
  String get newPasswordLabel => 'नवीन पासवर्ड';

  @override
  String get confirmPasswordLabel => 'नवीन पासवर्डची पुष्टी करा';

  @override
  String get currentPasswordLabel => 'सध्याचा पासवर्ड';

  @override
  String get passwordRules =>
      'किमान 12 अक्षरे. काही असंबंधित शब्द चांगले असतात. आपले नाव, मोबाइल नंबर किंवा सामान्य पासवर्ड वापरू नका.';

  @override
  String get passwordTooShort => 'किमान 12 अक्षरे वापरा.';

  @override
  String get passwordsMismatch => 'पासवर्ड जुळत नाहीत.';

  @override
  String get changePasswordTitle => 'पासवर्ड बदला';

  @override
  String get changePasswordButton => 'पासवर्ड बदला';

  @override
  String get passwordChanged =>
      'पासवर्ड बदलला. इतर उपकरणांवरून साइन आउट केले आहे.';

  @override
  String get passwordChangeSignsOut =>
      'बदलल्यावर आपण इतर सर्व उपकरणांवरून साइन आउट व्हाल.';

  @override
  String get passwordChangeFailed =>
      'पासवर्ड बदलता आला नाही. कृपया पुन्हा प्रयत्न करा.';

  @override
  String get officialComplaintsTitle => 'नागरिकांच्या तक्रारी';

  @override
  String get noComplaintsHere => 'येथे कोणतीही तक्रार नाही.';

  @override
  String get complaintShopLabel => 'दुकान';

  @override
  String get complaintUpdateTitle => 'ही तक्रार अपडेट करा';

  @override
  String get complaintChooseReviewHint =>
      'तुम्ही याची तपासणी करत आहात. नागरिकाला कळवले जाईल.';

  @override
  String get complaintChooseResolvedHint => 'समस्या दूर केली आहे.';

  @override
  String get complaintChooseRejectedHint =>
      'कोणतीही कारवाई करता येत नाही. उत्तरात कारण लिहा.';

  @override
  String get complaintReplyLabel => 'नागरिकाला उत्तर (ऐच्छिक)';

  @override
  String get complaintReplyHint =>
      'नागरिकाला हे उत्तर दिसेल. आधार क्रमांक, OTP किंवा पासवर्ड लिहू नका.';

  @override
  String get complaintUpdated => 'तक्रार अपडेट झाली';

  @override
  String get recordsTitle => 'नोंदी';

  @override
  String get allBookingsTitle => 'सर्व बुकिंग';

  @override
  String get stockAllShopsTitle => 'सर्व दुकानांतील साठा';

  @override
  String get reportsTitle => 'अहवाल';

  @override
  String get auditTitle => 'पडताळणी नोंद';

  @override
  String get usersTitle => 'लोक आणि कर्मचारी';

  @override
  String get bookingsSearchHint => 'टोकन, नाव किंवा दुकान शोधा';

  @override
  String bookingsCount(int count) {
    return '$count बुकिंग';
  }

  @override
  String get noBookingsHere => 'येथे कोणतीही बुकिंग नाही.';

  @override
  String get lowStockOnly => 'फक्त कमी साठा';

  @override
  String get noLowStock => 'कोणत्याही दुकानात साठा कमी नाही.';

  @override
  String get reportsChangeDates => 'तारखा बदला';

  @override
  String get reportsInPeriod => 'या कालावधीत';

  @override
  String get reportCollections => 'पूर्ण झालेले वितरण';

  @override
  String get reportTokens => 'बुक केलेले टोकन';

  @override
  String get reportCounterChecks => 'काउंटरवर पुष्टी केलेले वितरण';

  @override
  String get reportCancelled => 'रद्द केलेल्या बुकिंग';

  @override
  String get reportsNoDownload => 'फाइल डाउनलोड अद्याप उपलब्ध नाही.';

  @override
  String get auditSuccess => 'यशस्वी';

  @override
  String get auditBlocked => 'रोखले';

  @override
  String get auditFailed => 'अयशस्वी';

  @override
  String get auditQrScanned => 'QR स्कॅन झाला';

  @override
  String get auditBeneficiaryVerified => 'लाभार्थी तपासला';

  @override
  String get auditAadhaarChecked => 'आधार स्थिती तपासली';

  @override
  String get auditPassbookChecked => 'पासबुक स्थिती तपासली';

  @override
  String get auditOtpRequested => 'OTP पाठवला';

  @override
  String get auditOtpVerified => 'OTP बरोबर';

  @override
  String get auditOtpFailed => 'OTP चुकीचा';

  @override
  String get auditCollectionConfirmed => 'रेशन दिले';

  @override
  String get auditCollectionRejected => 'वितरण नाकारले';

  @override
  String get auditTokenUsed => 'टोकन आधीच वापरला';

  @override
  String get auditMethod => 'पद्धत';

  @override
  String get auditBeneficiary => 'लाभार्थी क्रमांक';

  @override
  String get noEntriesHere => 'येथे कोणतीही नोंद नाही.';

  @override
  String get usersSearchHint => 'नावाने शोधा';

  @override
  String get usersContactHidden =>
      'फोनवर संपर्क तपशील अंशतः लपवले आहेत. पूर्ण तपशील वेबसाइटवर पाहा.';

  @override
  String get noUsersHere => 'येथे कोणी नाही.';

  @override
  String get aiCenterTitle => 'AI माहिती';

  @override
  String get aiCenterNotice =>
      'फक्त निर्णयासाठी मदत. येथील काहीही रेशन नाकारत नाही, कार्ड रद्द करत नाही किंवा फसवणूक सिद्ध करत नाही. कारवाईपूर्वी एखाद्या व्यक्तीने तपासणी केली पाहिजे.';

  @override
  String get aiDemoData => 'डेमो डेटावरून मोजले.';

  @override
  String get aiShopsAttention => 'साठ्याची गरज असलेली दुकाने';

  @override
  String get aiAverageWait => 'सरासरी प्रतीक्षा';

  @override
  String get aiAlertsToReview => 'तपासण्यासाठी अलर्ट';

  @override
  String minutesShort(String minutes) {
    return '$minutes मिनिटे';
  }

  @override
  String get aiDemandTitle => 'मागणी: पुढील 30 दिवस';

  @override
  String aiDemandLine(String last, String previous) {
    return 'मागील 30 दिवस $last · त्यापूर्वी $previous';
  }

  @override
  String get aiDemandExpected => 'अंदाज';

  @override
  String get aiNoDemand =>
      'मागणीचा अंदाज लावण्यासाठी अजून पुरेसे वितरण झालेले नाही.';

  @override
  String get aiStockRiskTitle => 'संपत चाललेला साठा';

  @override
  String get aiShowAllStock => 'सर्व वस्तू दाखवा';

  @override
  String aiDaysLeft(int days) {
    return 'सुमारे $days दिवसांत पुन्हा मागवा';
  }

  @override
  String get aiReorderNow => 'आता मागवा';

  @override
  String get aiNoRecentUse => 'अलीकडे वापर नाही';

  @override
  String get aiQueueTitle => 'आज अपेक्षित प्रतीक्षा';

  @override
  String aiQueueLine(int count) {
    return '$count प्रतीक्षेत';
  }

  @override
  String get aiNoQueue => 'कोणत्याही दुकानात कोणी प्रतीक्षेत नाही.';

  @override
  String get correctStock => 'मोजणी दुरुस्त करा';

  @override
  String get correctStockHint =>
      'फक्त मोजणीतील चूक दुरुस्त करण्यासाठी. पुरवठा आणि खराब साठ्यासाठी वेगळी बटणे आहेत. प्रत्येक दुरुस्ती नोंदवली जाते.';

  @override
  String correctInStock(String unit) {
    return 'आता साठ्यात ($unit)';
  }

  @override
  String correctMinimum(String unit) {
    return 'किमान पातळी ($unit)';
  }

  @override
  String correctConfirmTitle(String item, String from, String to) {
    return '$item चा साठा $from वरून $to करायचा?';
  }

  @override
  String get correctConfirmBody =>
      'हे तुमच्या नावाने हाताने केलेली दुरुस्ती म्हणून नोंदवले जाईल. अधिकारी ते पाहू शकतात.';

  @override
  String get correctNoChange => 'काहीही बदलले नाही.';

  @override
  String get stockCorrected => 'साठा दुरुस्त केला.';

  @override
  String get amountInvalid => '0 किंवा त्याहून जास्त संख्या लिहा.';

  @override
  String get helpTopicsTitle => 'मदत विषय';

  @override
  String get helpSearchLabel => 'मदत शोधा';

  @override
  String helpResultsFor(String query) {
    return '“$query” चे परिणाम';
  }

  @override
  String get helpNoResults =>
      'काहीही सापडले नाही. दुसरे शब्द वापरून पाहा किंवा सहाय्यकाला विचारा.';

  @override
  String get helpAskAssistant => 'सहाय्यकाला विचारा';

  @override
  String helpArticleCount(int count) {
    String _temp0 = intl.Intl.pluralLogic(
      count,
      locale: localeName,
      other: '$count लेख',
      one: '1 लेख',
    );
    return '$_temp0';
  }
}
