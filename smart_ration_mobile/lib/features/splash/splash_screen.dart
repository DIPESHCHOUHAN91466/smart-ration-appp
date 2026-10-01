import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../app/routes.dart';
import '../../app/theme.dart';
import '../../l10n/app_localizations.dart';
import '../auth/auth_controller.dart';
import '../language/app_language.dart';

/// How long the logo stays on screen. Tests set it to zero.
final splashDurationProvider = Provider<Duration>((ref) => const Duration(milliseconds: 1500));

/// The first screen: the Ration Mitra logo, then the language choice (first launch), the sign-in
/// screen, or straight to the dashboard when a session was saved.
class SplashScreen extends ConsumerStatefulWidget {
  const SplashScreen({super.key});

  @override
  ConsumerState<SplashScreen> createState() => _SplashScreenState();
}

class _SplashScreenState extends ConsumerState<SplashScreen> {
  @override
  void initState() {
    super.initState();
    Future.delayed(ref.read(splashDurationProvider), () {
      if (!mounted) return;
      final user = ref.read(authControllerProvider);
      if (ref.read(languageProvider) == null) {
        context.go(Routes.chooseLanguage);
      } else {
        context.go(user == null ? Routes.login : Routes.homeFor(user.role));
      }
    });
  }

  @override
  Widget build(BuildContext context) {
    final l = AppLocalizations.of(context);
    final logoWidth = (MediaQuery.sizeOf(context).width * 0.8).clamp(0.0, 360.0);
    return Scaffold(
      backgroundColor: Colors.white,
      body: SafeArea(
        child: Center(
          child: Column(mainAxisSize: MainAxisSize.min, children: [
            // The logo already contains "Powered by HSD2C". BoxFit.contain keeps its shape.
            Image.asset(
              'assets/images/ration_mitra_logo.webp',
              width: logoWidth,
              fit: BoxFit.contain,
              semanticLabel: l.logoDescription,
            ),
            const SizedBox(height: 24),
            Text(l.tagline, style: const TextStyle(fontSize: 17, color: AppColors.muted)),
            const SizedBox(height: 32),
            const SizedBox(width: 28, height: 28, child: CircularProgressIndicator(strokeWidth: 3)),
          ]),
        ),
      ),
    );
  }
}
