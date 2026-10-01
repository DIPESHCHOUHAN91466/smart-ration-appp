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
}
