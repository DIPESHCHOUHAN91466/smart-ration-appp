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

/// New passwords: at least 12 characters (the backend also refuses common and personal ones).
const passwordMinLength = 12;

String? _newPasswordProblem(AppLocalizations l, String? value) =>
    (value ?? '').length < passwordMinLength ? l.passwordTooShort : null;

/// Why the backend refused the form: its reasons without the field name (English; e.g. "This password is too
/// common."), else the translated sentence.
String _problem(AppLocalizations l, ApiException e) {
  if (e.errors.isNotEmpty) return e.errors.map((x) => x.replaceFirst(RegExp(r'^[A-Za-z$.]+:\s*'), '')).join('\n');
  return e.kind == ApiErrorKind.badRequest || e.kind == ApiErrorKind.validation ? l.passwordChangeFailed : e.messageIn(l);
}

/// Forgotten password: a code goes to the account's registered mobile, then a new password is set.
/// Every session of the account ends; the person signs in again with the new password.
class ForgotPasswordScreen extends ConsumerStatefulWidget {
  const ForgotPasswordScreen({super.key});

  @override
  ConsumerState<ForgotPasswordScreen> createState() => _ForgotPasswordScreenState();
}

class _ForgotPasswordScreenState extends ConsumerState<ForgotPasswordScreen> {
  final _form = GlobalKey<FormState>();
  final _mobile = TextEditingController();
  final _code = TextEditingController();
  final _password = TextEditingController();
  final _confirm = TextEditingController();
  OtpSent? _sent;
  String? _sentTo;
  bool _busy = false;
  String? _error;

  @override
  void dispose() {
    for (final c in [_mobile, _code, _password, _confirm]) {
      c.dispose();
    }
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
    final repo = ref.read(authRepositoryProvider);
    try {
      if (_sent == null) {
        final mobile = normalizeMobile(_mobile.text)!;
        final sent = await repo.requestPasswordReset(mobile);
        if (mounted) {
          setState(() {
            _sent = sent;
            _sentTo = mobile;
          });
        }
      } else {
        await repo.confirmPasswordReset(_sentTo!, _code.text.trim(), _password.text);
        if (!mounted) return;
        ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(l.resetDone)));
        context.go(Routes.login);
      }
    } on ApiException catch (e) {
      if (mounted) setState(() => _error = e.kind == ApiErrorKind.unauthorized ? l.otpInvalid : _problem(l, e));
    } finally {
      if (mounted) setState(() => _busy = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final l = AppLocalizations.of(context);
    final sent = _sent;
    return Scaffold(
      appBar: AppBar(title: Text(l.resetTitle)),
      body: SafeArea(
        child: Form(
          key: _form,
          child: ListView(padding: const EdgeInsets.all(20), children: [
            if (_error != null) Notice(text: _error!),
            if (sent == null) ...[
              Text(l.resetIntro, style: const TextStyle(fontSize: 16)),
              const SizedBox(height: 16),
              TextFormField(
                controller: _mobile,
                enabled: !_busy,
                keyboardType: TextInputType.phone,
                autofillHints: const [AutofillHints.telephoneNumber],
                decoration: InputDecoration(labelText: l.mobileLabel, prefixIcon: const Icon(Icons.phone_android)),
                validator: (v) => normalizeMobile(v ?? '') == null ? l.mobileInvalid : null,
              ),
            ] else ...[
              Text(l.resetCodeSent(sent.mobileMasked), style: const TextStyle(fontSize: 16)),
              if (sent.demoCode != null) ...[
                const SizedBox(height: 8),
                Text(l.demoCodeHint(sent.demoCode!), style: const TextStyle(color: AppColors.muted)),
              ],
              const SizedBox(height: 16),
              TextFormField(
                controller: _code,
                enabled: !_busy,
                keyboardType: TextInputType.number,
                maxLength: 6,
                autofillHints: const [AutofillHints.oneTimeCode],
                decoration: InputDecoration(labelText: l.codeLabel),
                validator: (v) => RegExp(r'^\d{6}$').hasMatch(v?.trim() ?? '') ? null : l.codeInvalidFormat,
              ),
              const SizedBox(height: 8),
              PasswordFormField(
                controller: _password,
                enabled: !_busy,
                autofillHints: const [AutofillHints.newPassword],
                decoration: InputDecoration(labelText: l.newPasswordLabel, helperText: l.passwordRules, helperMaxLines: 3),
                validator: (v) => _newPasswordProblem(l, v),
              ),
              const SizedBox(height: 16),
              PasswordFormField(
                controller: _confirm,
                enabled: !_busy,
                decoration: InputDecoration(labelText: l.confirmPasswordLabel),
                validator: (v) => v != _password.text ? l.passwordsMismatch : null,
              ),
            ],
            const SizedBox(height: 24),
            FilledButton(
              onPressed: _busy ? null : _submit,
              child: Text(sent == null ? l.resetSendCode : l.resetSetPassword),
            ),
          ]),
        ),
      ),
    );
  }
}

/// Change the password while signed in. The backend signs out every other device; this phone keeps going with
/// the new session it returns.
class ChangePasswordScreen extends ConsumerStatefulWidget {
  const ChangePasswordScreen({super.key});

  @override
  ConsumerState<ChangePasswordScreen> createState() => _ChangePasswordScreenState();
}

class _ChangePasswordScreenState extends ConsumerState<ChangePasswordScreen> {
  final _form = GlobalKey<FormState>();
  final _current = TextEditingController();
  final _password = TextEditingController();
  final _confirm = TextEditingController();
  bool _busy = false;
  String? _error;

  @override
  void dispose() {
    for (final c in [_current, _password, _confirm]) {
      c.dispose();
    }
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
      await ref.read(authControllerProvider.notifier).changePassword(_current.text, _password.text);
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(l.passwordChanged)));
      context.pop();
    } on ApiException catch (e) {
      if (mounted) setState(() => _error = _problem(l, e));
    } finally {
      if (mounted) setState(() => _busy = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final l = AppLocalizations.of(context);
    return Scaffold(
      appBar: AppBar(title: Text(l.changePasswordTitle)),
      body: SafeArea(
        child: Form(
          key: _form,
          child: ListView(padding: const EdgeInsets.all(20), children: [
            if (_error != null) Notice(text: _error!),
            PasswordFormField(
              controller: _current,
              enabled: !_busy,
              autofillHints: const [AutofillHints.password],
              decoration: InputDecoration(labelText: l.currentPasswordLabel),
              validator: (v) => (v ?? '').isEmpty ? l.passwordRequired : null,
            ),
            const SizedBox(height: 16),
            PasswordFormField(
              controller: _password,
              enabled: !_busy,
              autofillHints: const [AutofillHints.newPassword],
              decoration: InputDecoration(labelText: l.newPasswordLabel, helperText: l.passwordRules, helperMaxLines: 3),
              validator: (v) => _newPasswordProblem(l, v),
            ),
            const SizedBox(height: 16),
            PasswordFormField(
              controller: _confirm,
              enabled: !_busy,
              decoration: InputDecoration(labelText: l.confirmPasswordLabel),
              validator: (v) => v != _password.text ? l.passwordsMismatch : null,
            ),
            const SizedBox(height: 8),
            Text(l.passwordChangeSignsOut, style: const TextStyle(color: AppColors.muted)),
            const SizedBox(height: 24),
            FilledButton(onPressed: _busy ? null : _submit, child: Text(l.changePasswordButton)),
          ]),
        ),
      ),
    );
  }
}
