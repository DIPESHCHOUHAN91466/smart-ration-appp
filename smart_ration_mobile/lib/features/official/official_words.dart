import 'package:flutter/widgets.dart';
import 'package:intl/intl.dart';

import '../../l10n/app_localizations.dart';
import '../citizen/citizen_widgets.dart';
import 'official_data.dart';

String stockStatusWord(AppLocalizations l, StockStatus s) => switch (s) {
      StockStatus.critical => l.stockCritical,
      StockStatus.low => l.stockLow,
      StockStatus.normal => l.stockOk,
    };

PillTone stockStatusTone(StockStatus s) => switch (s) {
      StockStatus.critical => PillTone.bad,
      StockStatus.low => PillTone.warn,
      StockStatus.normal => PillTone.good,
    };

String severityWord(AppLocalizations l, String severity) => switch (severity) {
      'HIGH' => l.severityHigh,
      'MEDIUM' => l.severityMedium,
      'LOW' => l.severityLow,
      _ => severity,
    };

PillTone severityTone(String severity) => switch (severity) {
      'HIGH' => PillTone.bad,
      'MEDIUM' => PillTone.warn,
      _ => PillTone.neutral,
    };

/// The alert's kind in the user's language; an unknown kind shows the backend's name.
String alertTypeWord(AppLocalizations l, String type) => switch (type) {
      'DuplicateCollectionAttempt' => l.alertDuplicateCollection,
      'RepeatedQrScan' => l.alertRepeatedQrScan,
      'RepeatedFailedVerification' => l.alertFailedVerification,
      'LOW_STOCK' => l.alertLowStock,
      'UNUSUAL_CONSUMPTION' => l.alertUnusualConsumption,
      _ => type,
    };

/// A UTC moment on the phone's clock, e.g. "Sep 24, 2026, 8:11 AM".
String localMoment(BuildContext context, DateTime utc) {
  final locale = Localizations.localeOf(context).toLanguageTag();
  final local = utc.toLocal();
  return '${DateFormat.yMMMd(locale).format(local)}, ${DateFormat.jm(locale).format(local)}';
}
