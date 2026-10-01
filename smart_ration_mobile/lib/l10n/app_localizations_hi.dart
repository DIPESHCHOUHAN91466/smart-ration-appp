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
}
