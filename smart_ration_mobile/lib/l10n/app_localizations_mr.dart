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
}
