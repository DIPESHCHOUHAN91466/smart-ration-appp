import 'package:flutter/material.dart';
import 'package:intl/intl.dart';

import '../../l10n/app_localizations.dart';
import '../citizen/citizen_widgets.dart';
import 'booking_data.dart';

/// "Today", "Tomorrow" or e.g. "Fri, 3 Oct" in the user's language.
String dayLabel(BuildContext context, DateTime day, {DateTime? now}) {
  final l = AppLocalizations.of(context);
  final t = now ?? DateTime.now();
  final today = DateTime(t.year, t.month, t.day);
  final d = DateTime(day.year, day.month, day.day);
  if (d == today) return l.today;
  if (d == today.add(const Duration(days: 1))) return l.tomorrow;
  return DateFormat.MMMEd(l.localeName).format(d);
}

/// A full date, e.g. "Friday, 3 October 2026" in the user's language.
String longDate(BuildContext context, DateTime day) =>
    DateFormat.yMMMMEEEEd(AppLocalizations.of(context).localeName).format(day);

/// "09:05" -> "9:05 AM" (or the language's own form).
String timeLabel(BuildContext context, String hhmm) {
  final parts = hhmm.split(':');
  final h = int.tryParse(parts.first) ?? 0;
  final m = int.tryParse(parts.elementAtOrNull(1) ?? '') ?? 0;
  return DateFormat.jm(AppLocalizations.of(context).localeName).format(DateTime(2000, 1, 1, h, m));
}

String tokenStateWord(AppLocalizations l, TokenState s) => switch (s) {
      TokenState.booked => l.stateBooked,
      TokenState.collected => l.stateCollected,
      TokenState.cancelled => l.stateCancelled,
      TokenState.missed => l.stateMissed,
    };

PillTone tokenStateTone(TokenState s) => switch (s) {
      TokenState.booked => PillTone.good,
      TokenState.collected => PillTone.neutral,
      TokenState.cancelled => PillTone.bad,
      TokenState.missed => PillTone.warn,
    };
