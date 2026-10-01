import 'dart:async';

import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
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

enum _Method { mobile, email }

/// Sign-in. Citizens use their mobile number and a texted code (the default); shop owners and
/// officials use email and password. Either way the backend decides the role.
class LoginScreen extends ConsumerStatefulWidget {
  const LoginScreen({super.key});

  @override
  ConsumerState<LoginScreen> createState() => _LoginScreenState();
}

class _LoginScreenState extends ConsumerState<LoginScreen> {
  _Method _method = _Method.mobile;

  @override
  Widget build(BuildContext context) {
    final l = AppLocalizations.of(context);
    final expired = ref.watch(sessionExpiredNoticeProvider);
    final text = Theme.of(context).textTheme;

    return Scaffold(
      appBar: AppBar(
        title: Text(l.appTitle),
        automaticallyImplyLeading: false,
        actions: [
          IconButton(
            icon: const Icon(Icons.help_outline),
            tooltip: l.helpButton,
            iconSize: 28,
            onPressed: () => context.push(Routes.help),
          ),
          IconButton(
            icon: const Icon(Icons.translate),
            tooltip: l.language,
            iconSize: 28,
            onPressed: () => context.push(Routes.changeLanguage),
          ),
        ],
      ),
      body: SafeArea(
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
                child: ClipOval(
                  child: Image.asset('assets/images/ration_mitra_emblem.png',
                      fit: BoxFit.contain, semanticLabel: l.logoDescription),
                ),
              ),
            ),
            const SizedBox(height: 16),
            Text(l.signInTitle, style: text.headlineSmall?.copyWith(fontWeight: FontWeight.w700)),
            const SizedBox(height: 16),
            SegmentedButton<_Method>(
              segments: [
                ButtonSegment(value: _Method.mobile, label: Text(l.signInWithMobile), icon: const Icon(Icons.phone_android)),
                ButtonSegment(value: _Method.email, label: Text(l.signInWithEmail), icon: const Icon(Icons.email_outlined)),
              ],
              selected: {_method},
              showSelectedIcon: false,
              style: const ButtonStyle(minimumSize: WidgetStatePropertyAll(Size(0, 52))),
              onSelectionChanged: (s) => setState(() => _method = s.first),
            ),
            const SizedBox(height: 20),
            if (expired) Notice(text: l.errorSessionEnded, warning: true),
            if (_method == _Method.mobile) const _OtpForm() else const _PasswordForm(),
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
    );
  }
}

// ---------------------------------------------------------------- mobile number + code

class _OtpForm extends ConsumerStatefulWidget {
  const _OtpForm();

  @override
  ConsumerState<_OtpForm> createState() => _OtpFormState();
}

class _OtpFormState extends ConsumerState<_OtpForm> {
  final _mobileForm = GlobalKey<FormState>();
  final _codeForm = GlobalKey<FormState>();
  final _mobile = TextEditingController();
  final _code = TextEditingController();
  String? _sentTo; // the normalized number a code was sent to
  OtpSent? _sent;
  int _wait = 0;
  Timer? _timer;
  bool _busy = false;
  String? _error;

  @override
  void dispose() {
    _timer?.cancel();
    _mobile.dispose();
    _code.dispose();
    super.dispose();
  }

  void _startCountdown(int seconds) {
    _timer?.cancel();
    setState(() => _wait = seconds);
    _timer = Timer.periodic(const Duration(seconds: 1), (t) {
      if (!mounted || _wait <= 1) {
        t.cancel();
        if (mounted) setState(() => _wait = 0);
        return;
      }
      setState(() => _wait--);
    });
  }

  Future<void> _send() async {
    final l = AppLocalizations.of(context);
    final mobile = normalizeMobile(_mobile.text);
    if (_sentTo == null && !_mobileForm.currentState!.validate()) return;
    if (mobile == null) return;
    FocusScope.of(context).unfocus();
    await _run(() async {
      final sent = await ref.read(authRepositoryProvider).requestOtp(mobile);
      setState(() {
        _sentTo = mobile;
        _sent = sent;
        _code.clear();
      });
      _startCountdown(sent.resendAfterSeconds);
    }, (e) => e.errorCode == 'SMS_UNAVAILABLE'
        ? l.otpSendFailed
        : (e.kind == ApiErrorKind.badRequest || e.kind == ApiErrorKind.validation)
            ? l.mobileInvalid
            : e.messageIn(l));
  }

  Future<void> _verify() async {
    final l = AppLocalizations.of(context);
    if (!_codeForm.currentState!.validate()) return;
    FocusScope.of(context).unfocus();
    await _run(
      () => ref.read(authControllerProvider.notifier).signInWithOtp(_sentTo!, _code.text.trim()),
      (e) => e.kind == ApiErrorKind.unauthorized ? l.otpInvalid : e.messageIn(l),
    );
  }

  Future<void> _run(Future<void> Function() action, String Function(ApiException) message) async {
    setState(() {
      _busy = true;
      _error = null;
    });
    try {
      await action();
    } on ApiException catch (e) {
      if (mounted) setState(() => _error = message(e));
    } finally {
      if (mounted) setState(() => _busy = false);
    }
  }

  void _changeNumber() {
    _timer?.cancel();
    setState(() {
      _sentTo = null;
      _sent = null;
      _wait = 0;
      _error = null;
      _code.clear();
    });
  }

  @override
  Widget build(BuildContext context) {
    final l = AppLocalizations.of(context);
    final showDemo = ref.watch(envProvider).isDevelopment;
    final sent = _sent;

    if (sent == null) {
      return Form(
        key: _mobileForm,
        child: Column(crossAxisAlignment: CrossAxisAlignment.stretch, children: [
          Text(l.mobileSignInSubtitle, style: const TextStyle(color: AppColors.muted, fontSize: 16)),
          const SizedBox(height: 16),
          if (_error != null) Notice(text: _error!),
          TextFormField(
            controller: _mobile,
            enabled: !_busy,
            keyboardType: TextInputType.phone,
            textInputAction: TextInputAction.done,
            autofillHints: const [AutofillHints.telephoneNumberNational],
            inputFormatters: [FilteringTextInputFormatter.allow(RegExp(r'[0-9+\s\-]')), LengthLimitingTextInputFormatter(16)],
            onFieldSubmitted: (_) => _send(),
            decoration: InputDecoration(
              labelText: l.mobileLabel,
              prefixIcon: const Icon(Icons.phone_android),
              prefixText: '+91 ',
            ),
            validator: (value) => normalizeMobile(value ?? '') == null ? l.mobileInvalid : null,
          ),
          const SizedBox(height: 24),
          _BusyButton(busy: _busy, label: l.sendCode, busyLabel: l.sendingCode, onPressed: _send),
          const SizedBox(height: 16),
          Text(l.otpStaffNote, style: const TextStyle(color: AppColors.muted)),
        ]),
      );
    }

    return Form(
      key: _codeForm,
      child: Column(crossAxisAlignment: CrossAxisAlignment.stretch, children: [
        Text(l.codeSentTo(sent.mobileMasked), style: const TextStyle(fontSize: 16)),
        if (showDemo && sent.demoCode != null) ...[
          const SizedBox(height: 8),
          Text(l.demoCodeHint(sent.demoCode!), style: const TextStyle(color: AppColors.muted)),
        ],
        const SizedBox(height: 16),
        if (_error != null) Notice(text: _error!),
        TextFormField(
          controller: _code,
          enabled: !_busy,
          autofocus: true,
          keyboardType: TextInputType.number,
          textInputAction: TextInputAction.done,
          autofillHints: const [AutofillHints.oneTimeCode],
          inputFormatters: [FilteringTextInputFormatter.digitsOnly, LengthLimitingTextInputFormatter(6)],
          style: const TextStyle(fontSize: 24, letterSpacing: 8, fontWeight: FontWeight.w600),
          onFieldSubmitted: (_) => _verify(),
          decoration: InputDecoration(labelText: l.codeLabel, prefixIcon: const Icon(Icons.pin_outlined)),
          validator: (value) => RegExp(r'^\d{6}$').hasMatch(value ?? '') ? null : l.codeInvalidFormat,
        ),
        const SizedBox(height: 24),
        _BusyButton(busy: _busy, label: l.signInButton, busyLabel: l.signingIn, onPressed: _verify),
        const SizedBox(height: 8),
        Wrap(alignment: WrapAlignment.spaceBetween, crossAxisAlignment: WrapCrossAlignment.center, children: [
          TextButton(
            onPressed: _busy || _wait > 0 ? null : _send,
            child: Text(_wait > 0 ? l.resendIn(_wait) : l.resendCode),
          ),
          TextButton(onPressed: _busy ? null : _changeNumber, child: Text(l.changeNumber)),
        ]),
      ]),
    );
  }
}

// ---------------------------------------------------------------- email + password

class _PasswordForm extends ConsumerStatefulWidget {
  const _PasswordForm();

  @override
  ConsumerState<_PasswordForm> createState() => _PasswordFormState();
}

class _PasswordFormState extends ConsumerState<_PasswordForm> {
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
    final showDemo = ref.watch(envProvider).isDevelopment;

    return AutofillGroup(
      child: Form(
        key: _form,
        child: Column(crossAxisAlignment: CrossAxisAlignment.stretch, children: [
          Text(l.signInSubtitle, style: const TextStyle(color: AppColors.muted, fontSize: 16)),
          const SizedBox(height: 16),
          if (_error != null) Notice(text: _error!),
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
          _BusyButton(busy: _busy, label: l.signInButton, busyLabel: l.signingIn, onPressed: _submit),
          if (showDemo) ...[
            const SizedBox(height: 28),
            Text(l.demoAccountsTitle, style: Theme.of(context).textTheme.titleSmall),
            const SizedBox(height: 4),
            Text(l.demoAccountsHelp, style: const TextStyle(color: AppColors.muted)),
            const SizedBox(height: 8),
            Wrap(spacing: 8, runSpacing: 8, children: [
              for (final email in _demoEmails)
                ActionChip(label: Text(email), onPressed: _busy ? null : () => setState(() => _email.text = email)),
            ]),
          ],
        ]),
      ),
    );
  }
}

// ---------------------------------------------------------------- shared pieces

class _BusyButton extends StatelessWidget {
  const _BusyButton({required this.busy, required this.label, required this.busyLabel, required this.onPressed});

  final bool busy;
  final String label;
  final String busyLabel;
  final VoidCallback onPressed;

  @override
  Widget build(BuildContext context) => FilledButton(
        onPressed: busy ? null : onPressed,
        child: busy
            ? Row(mainAxisAlignment: MainAxisAlignment.center, children: [
                const SizedBox(width: 22, height: 22, child: CircularProgressIndicator(strokeWidth: 2.5, color: Colors.white)),
                const SizedBox(width: 12),
                Flexible(child: Text(busyLabel)),
              ])
            : Text(label),
      );
}

/// A coloured message box above a form: red for errors, amber for information.
class Notice extends StatelessWidget {
  const Notice({super.key, required this.text, this.warning = false});

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
          Icon(warning ? Icons.info_outline : Icons.error_outline, color: warning ? AppColors.warning : AppColors.danger),
          const SizedBox(width: 10),
          Expanded(
            child: Text(text,
                style: TextStyle(color: warning ? AppColors.warning : AppColors.danger, fontWeight: FontWeight.w600)),
          ),
        ]),
      );
}
