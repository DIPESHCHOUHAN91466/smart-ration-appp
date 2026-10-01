import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../app/routes.dart';
import '../../app/theme.dart';
import '../../core/network/api_exception.dart';
import '../../core/providers.dart';
import '../../l10n/app_localizations.dart';
import 'auth_controller.dart';

/// Demo accounts from the synthetic data (README). Only the email is filled in: the password is
/// never written into the app.
const _demoEmails = ['rural@example.com', 'shop@example.com', 'officer@example.com'];

class LoginScreen extends ConsumerStatefulWidget {
  const LoginScreen({super.key});

  @override
  ConsumerState<LoginScreen> createState() => _LoginScreenState();
}

class _LoginScreenState extends ConsumerState<LoginScreen> {
  final _form = GlobalKey<FormState>();
  final _email = TextEditingController();
  final _password = TextEditingController();
  bool _hidePassword = true;
  bool _busy = false;
  String? _error;

  @override
  void dispose() {
    _email.dispose();
    _password.dispose();
    super.dispose();
  }

  Future<void> _submit() async {
    final l = AppLocalizations.of(context);
    FocusScope.of(context).unfocus();
    if (!_form.currentState!.validate()) return;
    setState(() {
      _busy = true;
      _error = null;
    });
    try {
      await ref.read(authControllerProvider.notifier).signIn(_email.text, _password.text);
      // The router now sends the user to their dashboard.
    } on ApiException catch (e) {
      if (!mounted) return;
      setState(() => _error = switch (e.kind) {
            ApiErrorKind.unauthorized => l.loginInvalid,
            ApiErrorKind.forbidden => l.loginAccountDisabled,
            ApiErrorKind.badRequest || ApiErrorKind.validation => l.loginInvalid,
            _ => e.messageIn(l),
          });
    } finally {
      if (mounted) setState(() => _busy = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final l = AppLocalizations.of(context);
    final expired = ref.watch(sessionExpiredNoticeProvider);
    final showDemo = ref.watch(envProvider).isDevelopment;
    final text = Theme.of(context).textTheme;

    return Scaffold(
      appBar: AppBar(
        title: Text(l.appTitle),
        automaticallyImplyLeading: false,
        actions: [
          IconButton(
            icon: const Icon(Icons.translate),
            tooltip: l.language,
            iconSize: 28,
            onPressed: () => context.push(Routes.changeLanguage),
          ),
        ],
      ),
      body: SafeArea(
        child: AutofillGroup(
          child: Form(
            key: _form,
            child: ListView(
              padding: const EdgeInsets.fromLTRB(20, 24, 20, 32),
              children: [
                // The emblem image has a white background, so it sits in a white circle on this light page.
                Center(
                  child: Container(
                    width: 96,
                    height: 96,
                    padding: const EdgeInsets.all(8),
                    decoration: const BoxDecoration(color: Colors.white, shape: BoxShape.circle),
                    child: Image.asset('assets/images/ration_mitra_emblem.png',
                        fit: BoxFit.contain, semanticLabel: l.logoDescription),
                  ),
                ),
                const SizedBox(height: 16),
                Text(l.signInTitle, style: text.headlineSmall?.copyWith(fontWeight: FontWeight.w700)),
                const SizedBox(height: 6),
                Text(l.signInSubtitle, style: const TextStyle(color: AppColors.muted, fontSize: 16)),
                const SizedBox(height: 20),
                if (expired && _error == null) _Notice(text: l.errorSessionEnded, warning: true),
                if (_error != null) _Notice(text: _error!),
                TextFormField(
                  controller: _email,
                  enabled: !_busy,
                  keyboardType: TextInputType.emailAddress,
                  textInputAction: TextInputAction.next,
                  autofillHints: const [AutofillHints.email, AutofillHints.username],
                  autocorrect: false,
                  decoration: InputDecoration(labelText: l.emailLabel, prefixIcon: const Icon(Icons.email_outlined)),
                  validator: (value) {
                    final v = value?.trim() ?? '';
                    if (v.isEmpty) return l.emailRequired;
                    if (!RegExp(r'^[^@\s]+@[^@\s]+\.[^@\s]+$').hasMatch(v)) return l.emailInvalid;
                    return null;
                  },
                ),
                const SizedBox(height: 16),
                TextFormField(
                  controller: _password,
                  enabled: !_busy,
                  obscureText: _hidePassword,
                  textInputAction: TextInputAction.done,
                  autofillHints: const [AutofillHints.password],
                  onFieldSubmitted: (_) => _submit(),
                  decoration: InputDecoration(
                    labelText: l.passwordLabel,
                    prefixIcon: const Icon(Icons.lock_outline),
                    suffixIcon: IconButton(
                      icon: Icon(_hidePassword ? Icons.visibility_outlined : Icons.visibility_off_outlined),
                      tooltip: _hidePassword ? l.showPassword : l.hidePassword,
                      onPressed: () => setState(() => _hidePassword = !_hidePassword),
                    ),
                  ),
                  validator: (value) => (value ?? '').isEmpty ? l.passwordRequired : null,
                ),
                const SizedBox(height: 24),
                FilledButton(
                  onPressed: _busy ? null : _submit,
                  child: _busy
                      ? Row(mainAxisAlignment: MainAxisAlignment.center, children: [
                          const SizedBox(
                              width: 22, height: 22, child: CircularProgressIndicator(strokeWidth: 2.5, color: Colors.white)),
                          const SizedBox(width: 12),
                          Text(l.signingIn),
                        ])
                      : Text(l.signInButton),
                ),
                if (showDemo) ...[
                  const SizedBox(height: 28),
                  Text(l.demoAccountsTitle, style: text.titleSmall),
                  const SizedBox(height: 4),
                  Text(l.demoAccountsHelp, style: const TextStyle(color: AppColors.muted)),
                  const SizedBox(height: 8),
                  Wrap(spacing: 8, runSpacing: 8, children: [
                    for (final email in _demoEmails)
                      ActionChip(label: Text(email), onPressed: _busy ? null : () => setState(() => _email.text = email)),
                  ]),
                ],
                const SizedBox(height: 20),
                Center(
                  child: TextButton.icon(
                    icon: const Icon(Icons.dns_outlined),
                    label: Text(l.checkServer),
                    onPressed: () => context.push(Routes.serverStatus),
                  ),
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }
}

class _Notice extends StatelessWidget {
  const _Notice({required this.text, this.warning = false});

  final String text;
  final bool warning;

  @override
  Widget build(BuildContext context) => Container(
        margin: const EdgeInsets.only(bottom: 16),
        padding: const EdgeInsets.all(14),
        decoration: BoxDecoration(
          color: warning ? AppColors.warningSoft : AppColors.dangerSoft,
          borderRadius: BorderRadius.circular(12),
        ),
        child: Row(children: [
          Icon(warning ? Icons.info_outline : Icons.error_outline,
              color: warning ? AppColors.warning : AppColors.danger),
          const SizedBox(width: 10),
          Expanded(
            child: Text(text,
                style: TextStyle(color: warning ? AppColors.warning : AppColors.danger, fontWeight: FontWeight.w600)),
          ),
        ]),
      );
}
