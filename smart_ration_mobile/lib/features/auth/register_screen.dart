import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../app/routes.dart';
import '../../app/theme.dart';
import '../../core/network/api_exception.dart';
import '../../core/password_field.dart';
import '../../l10n/app_localizations.dart';
import 'auth_controller.dart';
import 'login_screen.dart' show Notice;
import 'password_screens.dart' show passwordMinLength;

/// The website's registration form: a citizen (ration card holder) account. Staff accounts are made by the
/// office, never here. Consent to the privacy policy is required and recorded by the backend; the policy
/// itself is one tap away, in the app's language. On success the person is signed in and sent home.
class RegisterScreen extends ConsumerStatefulWidget {
  const RegisterScreen({super.key});

  @override
  ConsumerState<RegisterScreen> createState() => _RegisterScreenState();
}

class _RegisterScreenState extends ConsumerState<RegisterScreen> {
  final _form = GlobalKey<FormState>();
  final _name = TextEditingController();
  final _email = TextEditingController();
  final _mobile = TextEditingController();
  final _password = TextEditingController();
  final _confirm = TextEditingController();
  bool _consent = false;
  bool _consentMissing = false;
  bool _busy = false;
  String? _error;

  @override
  void dispose() {
    for (final c in [_name, _email, _mobile, _password, _confirm]) {
      c.dispose();
    }
    super.dispose();
  }

  Future<void> _submit() async {
    final l = AppLocalizations.of(context);
    FocusScope.of(context).unfocus();
    final valid = _form.currentState!.validate();
    setState(() {
      _consentMissing = !_consent;
      _error = null;
    });
    if (!valid || !_consent) return;
    setState(() => _busy = true);
    final messenger = ScaffoldMessenger.of(context);
    try {
      await ref.read(authControllerProvider.notifier).register(
            fullName: _name.text,
            email: _email.text,
            mobile: normalizeMobile(_mobile.text)!,
            password: _password.text,
          );
      // Signed in: the router sends the person to their dashboard.
      messenger.showSnackBar(SnackBar(content: Text(l.registered)));
    } on ApiException catch (e) {
      if (mounted) setState(() => _error = _problem(l, e));
    } finally {
      if (mounted) setState(() => _busy = false);
    }
  }

  /// The backend's reasons (e.g. "This password is too common.", English) without the field name, a clear
  /// sentence for an existing account, else the translated message.
  String _problem(AppLocalizations l, ApiException e) {
    if (e.kind == ApiErrorKind.conflict) return l.registerAlreadyExists;
    if (e.errors.isNotEmpty) return e.errors.map((x) => x.replaceFirst(RegExp(r'^[A-Za-z$.]+:\s*'), '')).join('\n');
    return e.kind == ApiErrorKind.badRequest || e.kind == ApiErrorKind.validation ? l.registerFailed : e.messageIn(l);
  }

  @override
  Widget build(BuildContext context) {
    final l = AppLocalizations.of(context);
    return Scaffold(
      appBar: AppBar(title: Text(l.registerTitle)),
      body: SafeArea(
        child: Form(
          key: _form,
          child: AutofillGroup(
            child: ListView(padding: const EdgeInsets.all(20), children: [
              Text(l.registerIntro, style: const TextStyle(color: AppColors.muted, fontSize: 15)),
              const SizedBox(height: 16),
              if (_error != null) Notice(text: _error!),
              TextFormField(
                controller: _name,
                enabled: !_busy,
                maxLength: 150,
                textCapitalization: TextCapitalization.words,
                autofillHints: const [AutofillHints.name],
                decoration: InputDecoration(labelText: l.fullNameLabel, counterText: ''),
                validator: (v) => (v ?? '').trim().length < 2 ? l.nameTooShort : null,
              ),
              const SizedBox(height: 16),
              TextFormField(
                controller: _email,
                enabled: !_busy,
                maxLength: 200,
                keyboardType: TextInputType.emailAddress,
                autofillHints: const [AutofillHints.email],
                decoration: InputDecoration(labelText: l.emailLabel, counterText: ''),
                validator: (value) {
                  final v = value?.trim() ?? '';
                  if (v.isEmpty) return l.emailRequired;
                  return RegExp(r'^[^@\s]+@[^@\s]+\.[^@\s]+$').hasMatch(v) ? null : l.emailInvalid;
                },
              ),
              const SizedBox(height: 16),
              TextFormField(
                controller: _mobile,
                enabled: !_busy,
                keyboardType: TextInputType.phone,
                autofillHints: const [AutofillHints.telephoneNumber],
                decoration: InputDecoration(labelText: l.mobileLabel),
                validator: (v) => normalizeMobile(v ?? '') == null ? l.mobileInvalid : null,
              ),
              const SizedBox(height: 16),
              PasswordFormField(
                controller: _password,
                enabled: !_busy,
                maxLength: 100,
                autofillHints: const [AutofillHints.newPassword],
                decoration: InputDecoration(labelText: l.passwordLabel, helperText: l.passwordRules, helperMaxLines: 3, counterText: ''),
                validator: (v) => (v ?? '').length < passwordMinLength ? l.passwordTooShort : null,
              ),
              const SizedBox(height: 16),
              PasswordFormField(
                controller: _confirm,
                enabled: !_busy,
                decoration: InputDecoration(labelText: l.confirmPasswordPlain),
                validator: (v) => v != _password.text ? l.passwordsMismatch : null,
              ),
              const SizedBox(height: 16),
              CheckboxListTile(
                value: _consent,
                onChanged: _busy ? null : (v) => setState(() => _consent = v ?? false),
                controlAffinity: ListTileControlAffinity.leading,
                contentPadding: EdgeInsets.zero,
                title: Text(l.consentText),
                subtitle: _consentMissing && !_consent
                    ? Semantics(liveRegion: true, child: Text(l.consentRequired, style: const TextStyle(color: AppColors.danger)))
                    : null,
              ),
              Align(
                alignment: AlignmentDirectional.centerStart,
                child: TextButton.icon(
                  icon: const Icon(Icons.privacy_tip_outlined),
                  label: Text(l.readPrivacyPolicy),
                  onPressed: () => context.push(Routes.privacy),
                ),
              ),
              const SizedBox(height: 16),
              FilledButton(
                onPressed: _busy ? null : _submit,
                child: _busy
                    ? const SizedBox.square(dimension: 22, child: CircularProgressIndicator(strokeWidth: 3))
                    : Text(l.registerButton),
              ),
            ]),
          ),
        ),
      ),
    );
  }
}
