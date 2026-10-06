import 'package:flutter/material.dart';

import 'privacy_text.dart';

/// The privacy policy, the same text as the website's (generated from it, see tool/gen_privacy_policy.mjs),
/// in the app's language. Open to everyone; registration links here before asking for consent.
class PrivacyScreen extends StatelessWidget {
  const PrivacyScreen({super.key});

  @override
  Widget build(BuildContext context) {
    final policy = privacyPolicy[Localizations.localeOf(context).languageCode] ?? privacyPolicy['en']!;
    final text = Theme.of(context).textTheme;
    return Scaffold(
      appBar: AppBar(title: Text(policy.title)),
      body: ListView(
        padding: const EdgeInsets.all(20),
        children: [
          for (final section in policy.sections) ...[
            Semantics(
              header: true,
              child: Text(section.heading, style: text.titleMedium?.copyWith(fontWeight: FontWeight.w700)),
            ),
            const SizedBox(height: 6),
            for (final paragraph in section.paragraphs)
              Padding(
                padding: const EdgeInsets.only(bottom: 8),
                child: Text(paragraph, style: const TextStyle(fontSize: 16, height: 1.4)),
              ),
            const SizedBox(height: 12),
          ],
          // Keeps the last paragraph clear of the system navigation bar.
          SizedBox(height: MediaQuery.paddingOf(context).bottom),
        ],
      ),
    );
  }
}
