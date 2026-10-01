import 'dart:convert';
import 'dart:io';

import 'package:flutter_test/flutter_test.dart';

/// Every sentence must exist in every language, with the same {placeholders}.
/// English (app_en.arb) is the master list.
void main() {
  Map<String, String> load(String code) {
    final json = jsonDecode(File('lib/l10n/app_$code.arb').readAsStringSync()) as Map<String, dynamic>;
    return {
      for (final e in json.entries)
        if (!e.key.startsWith('@')) e.key: e.value as String,
    };
  }

  Set<String> placeholders(String text) => RegExp(r'\{(\w+)\}').allMatches(text).map((m) => m.group(1)!).toSet();

  final english = load('en');

  for (final code in ['hi', 'mr']) {
    group('$code translations', () {
      final other = load(code);

      test('have every English sentence and nothing extra', () {
        expect(other.keys.toSet().difference(english.keys.toSet()), isEmpty, reason: 'keys not in English');
        expect(english.keys.toSet().difference(other.keys.toSet()), isEmpty, reason: 'missing translations');
      });

      test('are not empty and not left in English', () {
        for (final key in english.keys) {
          expect(other[key]!.trim(), isNotEmpty, reason: key);
        }
        // Words that are the same in every language (names, abbreviations) are listed here.
        const sameEverywhere = {'serverAddress'};
        final untranslated = english.keys.where((k) => !sameEverywhere.contains(k) && other[k] == english[k]).toList();
        expect(untranslated, isEmpty, reason: 'still in English');
      });

      test('keep the same {placeholders}', () {
        for (final key in english.keys) {
          expect(placeholders(other[key]!), placeholders(english[key]!), reason: key);
        }
      });
    });
  }
}
