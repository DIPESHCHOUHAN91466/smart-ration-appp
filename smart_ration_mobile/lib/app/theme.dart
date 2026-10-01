import 'package:flutter/material.dart';

/// Smart Ration brand colours, taken from the website (frontend/src/styles/global.css).
class AppColors {
  static const blue = Color(0xFF0757B8);
  static const blueBright = Color(0xFF0A6ED1);
  static const navy = Color(0xFF063D82);
  static const ink = Color(0xFF102A43);
  static const muted = Color(0xFF456078);
  static const background = Color(0xFFF3F8FC);
  static const border = Color(0xFFDCE6F0);

  // Status colours: always paired with an icon or a word, never colour alone.
  static const success = Color(0xFF15803D);
  static const successSoft = Color(0xFFE8F8EE);
  static const warning = Color(0xFFB45309);
  static const warningSoft = Color(0xFFFFF5DB);
  static const danger = Color(0xFFB91C1C);
  static const dangerSoft = Color(0xFFFEECEC);
}

/// Material 3, blue and white, with large touch targets and readable text for first-time phone users.
ThemeData buildAppTheme() {
  final scheme = ColorScheme.fromSeed(
    seedColor: AppColors.blue,
    primary: AppColors.blue,
    onPrimary: Colors.white,
    surface: Colors.white,
    onSurface: AppColors.ink,
    error: AppColors.danger,
  );
  const minTouch = Size(64, 52); // Android's minimum is 48; 52 is easier for older users.

  return ThemeData(
    useMaterial3: true,
    colorScheme: scheme,
    scaffoldBackgroundColor: AppColors.background,
    textTheme: Typography.material2021().black.apply(bodyColor: AppColors.ink, displayColor: AppColors.ink).copyWith(
          bodyLarge: const TextStyle(fontSize: 17, height: 1.45),
          bodyMedium: const TextStyle(fontSize: 15, height: 1.45),
        ),
    appBarTheme: const AppBarTheme(
      backgroundColor: AppColors.blue,
      foregroundColor: Colors.white,
      centerTitle: false,
      titleTextStyle: TextStyle(fontSize: 20, fontWeight: FontWeight.w600, color: Colors.white),
    ),
    cardTheme: CardThemeData(
      color: Colors.white,
      elevation: 0,
      margin: EdgeInsets.zero,
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(14),
        side: const BorderSide(color: AppColors.border),
      ),
    ),
    filledButtonTheme: FilledButtonThemeData(
      style: FilledButton.styleFrom(
        minimumSize: minTouch,
        textStyle: const TextStyle(fontSize: 17, fontWeight: FontWeight.w600),
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
      ),
    ),
    outlinedButtonTheme: OutlinedButtonThemeData(
      style: OutlinedButton.styleFrom(
        minimumSize: minTouch,
        textStyle: const TextStyle(fontSize: 17, fontWeight: FontWeight.w600),
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
      ),
    ),
    inputDecorationTheme: InputDecorationTheme(
      filled: true,
      fillColor: Colors.white,
      contentPadding: const EdgeInsets.symmetric(horizontal: 16, vertical: 16),
      border: OutlineInputBorder(borderRadius: BorderRadius.circular(12)),
    ),
  );
}
