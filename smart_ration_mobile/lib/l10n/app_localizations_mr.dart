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
}
