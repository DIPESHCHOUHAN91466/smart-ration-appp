import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../app/routes.dart';
import '../../app/theme.dart';
import '../../l10n/app_localizations.dart';
import 'app_language.dart';

/// Language choice. On first launch it leads on to the app; opened from the language button, it goes back.
/// Tapping a language switches the whole app straight away, so people can see the result before going on.
class LanguageScreen extends ConsumerWidget {
  const LanguageScreen({super.key, required this.firstLaunch});

  final bool firstLaunch;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final l = AppLocalizations.of(context);
    final selected = ref.watch(languageProvider);

    void done() => firstLaunch ? context.go(Routes.home) : context.pop();

    return Scaffold(
      appBar: firstLaunch ? null : AppBar(title: Text(l.language)),
      backgroundColor: firstLaunch ? Colors.white : null,
      body: SafeArea(
        child: ListView(
          padding: const EdgeInsets.fromLTRB(20, 24, 20, 24),
          children: [
            if (firstLaunch) ...[
              Center(
                child: Image.asset('assets/images/ration_mitra_emblem.png',
                    width: 96, height: 96, fit: BoxFit.contain, semanticLabel: l.logoDescription),
              ),
              const SizedBox(height: 20),
            ],
            Text(l.chooseLanguageTitle,
                style: Theme.of(context).textTheme.headlineSmall?.copyWith(fontWeight: FontWeight.w700)),
            const SizedBox(height: 8),
            Text(l.chooseLanguageHelp, style: const TextStyle(color: AppColors.muted, fontSize: 16)),
            const SizedBox(height: 24),
            for (final language in AppLanguage.values) ...[
              _LanguageOption(
                language: language,
                selected: language == selected,
                onTap: () => ref.read(languageProvider.notifier).choose(language),
              ),
              const SizedBox(height: 12),
            ],
            const SizedBox(height: 12),
            FilledButton(onPressed: selected == null ? null : done, child: Text(l.continueButton)),
          ],
        ),
      ),
    );
  }
}

class _LanguageOption extends StatelessWidget {
  const _LanguageOption({required this.language, required this.selected, required this.onTap});

  final AppLanguage language;
  final bool selected;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    return Semantics(
      selected: selected,
      inMutuallyExclusiveGroup: true,
      button: true,
      child: Material(
        color: selected ? const Color(0xFFF1F7FF) : Colors.white,
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(14),
          side: BorderSide(color: selected ? AppColors.blue : AppColors.border, width: selected ? 2 : 1),
        ),
        child: InkWell(
          borderRadius: BorderRadius.circular(14),
          onTap: onTap,
          child: Padding(
            padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 18),
            child: Row(children: [
              Expanded(
                child: Text(language.nativeName, style: const TextStyle(fontSize: 22, fontWeight: FontWeight.w600)),
              ),
              Icon(selected ? Icons.check_circle : Icons.circle_outlined,
                  color: selected ? AppColors.blue : AppColors.border, size: 28),
            ]),
          ),
        ),
      ),
    );
  }
}
