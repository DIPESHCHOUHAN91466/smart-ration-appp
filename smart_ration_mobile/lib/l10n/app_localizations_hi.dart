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
}
