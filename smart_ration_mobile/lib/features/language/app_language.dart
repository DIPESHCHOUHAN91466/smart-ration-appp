import 'dart:ui';

import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:shared_preferences/shared_preferences.dart';

/// The languages the app speaks. To add one: add it here and add lib/l10n/app_<code>.arb.
enum AppLanguage {
  en('English'),
  hi('हिंदी'),
  mr('मराठी');

  const AppLanguage(this.nativeName);

  /// Always written in the language itself, so people can find their own language.
  final String nativeName;

  Locale get locale => Locale(name);
}

/// Small, non-secret settings kept on the phone (the language). Loaded once in main.dart.
final sharedPreferencesProvider =
    Provider<SharedPreferences>((ref) => throw UnimplementedError('sharedPreferencesProvider is set in main.dart'));

/// The chosen language, or null before the user has picked one (first launch).
class LanguageController extends Notifier<AppLanguage?> {
  static const storageKey = 'language';

  @override
  AppLanguage? build() {
    final saved = ref.watch(sharedPreferencesProvider).getString(storageKey);
    return AppLanguage.values.where((l) => l.name == saved).firstOrNull;
  }

  /// Switches the whole app at once and remembers the choice for next time.
  Future<void> choose(AppLanguage language) async {
    state = language;
    await ref.read(sharedPreferencesProvider).setString(storageKey, language.name);
  }
}

final languageProvider = NotifierProvider<LanguageController, AppLanguage?>(LanguageController.new);
