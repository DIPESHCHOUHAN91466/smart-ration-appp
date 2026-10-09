import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:qr_flutter/qr_flutter.dart';

import '../../app/theme.dart';
import '../../core/network/api_exception.dart';
import '../../core/password_field.dart';
import '../../l10n/app_localizations.dart';
import '../auth/auth_controller.dart';
import '../auth/login_screen.dart' show Notice;
import '../auth/session.dart';
import '../citizen/citizen_widgets.dart' show DemoDataBanner, PillTone, StatusPill;
import 'account_data.dart';

/// A titled card on My account.
class AccountCard extends StatelessWidget {
  const AccountCard({super.key, required this.icon, required this.title, required this.children});

  final IconData icon;
  final String title;
  final List<Widget> children;

  @override
  Widget build(BuildContext context) => Card(
        child: Padding(
          padding: const EdgeInsets.all(16),
          child: Column(crossAxisAlignment: CrossAxisAlignment.stretch, children: [
            Row(children: [
              Icon(icon),
              const SizedBox(width: 12),
              Expanded(child: Text(title, style: Theme.of(context).textTheme.titleMedium?.copyWith(fontWeight: FontWeight.w700))),
            ]),
            const SizedBox(height: 12),
            ...children,
          ]),
        ),
      );
}

/// The backend's reasons for a refused form, in the person's language where we know them; else its message.
String formProblem(AppLocalizations l, ApiException e) {
  if (e.errors.isEmpty) return e.messageIn(l);
  return e.errors.map((x) {
    if (x.startsWith('Password:') || x == 'CurrentPassword: The password is incorrect.') return l.mfaWrongPassword;
    if (x.startsWith('Code:')) return l.mfaWrongCode;
    return x.replaceFirst(RegExp(r'^[A-Za-z$.]+:\s*'), '');
  }).join('\n');
}

/// Name and mobile number (PUT /api/users/profile). The email is the sign-in name and is shown read-only.
/// A new mobile number needs the current password: sign-in codes and password resets go to that number.
class ProfileCard extends ConsumerStatefulWidget {
  const ProfileCard({super.key});

  @override
  ConsumerState<ProfileCard> createState() => _ProfileCardState();
}

class _ProfileCardState extends ConsumerState<ProfileCard> {
  final _form = GlobalKey<FormState>();
  final _name = TextEditingController();
  final _mobile = TextEditingController();
  final _password = TextEditingController();
  bool _busy = false;
  String? _error;

  @override
  void initState() {
    super.initState();
    _mobile.addListener(() => setState(() {}));   // the password field appears as soon as the number differs
  }

  @override
  void dispose() {
    _name.dispose();
    _mobile.dispose();
    _password.dispose();
    super.dispose();
  }

  /// The number as typed differs from the saved one (spaces and +91 are not a change).
  bool _mobileChanged(SessionUser user) => (normalizeMobile(_mobile.text) ?? _mobile.text.trim()) != user.mobileNumber.trim();

  Future<void> _save(SessionUser user) async {
    final l = AppLocalizations.of(context);
    FocusScope.of(context).unfocus();
    if (!_form.currentState!.validate()) return;
    final changed = _mobileChanged(user);
    setState(() {
      _busy = true;
      _error = null;
    });
    try {
      final saved = await ref.read(accountRepositoryProvider).saveProfile(
            _name.text.trim(),
            changed ? normalizeMobile(_mobile.text)! : user.mobileNumber,
            currentPassword: changed ? _password.text : null,
          );
      _password.clear();
      await ref.read(authControllerProvider.notifier).profileUpdated(saved);
      ref.invalidate(profileProvider);
      if (mounted) ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(l.profileSaved)));
    } on ApiException catch (e) {
      if (mounted) setState(() => _error = formProblem(l, e));
    } finally {
      if (mounted) setState(() => _busy = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final l = AppLocalizations.of(context);
    final profile = ref.watch(profileProvider);
    // Fill the form when the profile arrives (and again after saving), outside the build.
    ref.listen(profileProvider, (_, next) {
      final user = next.value;
      if (user == null || next.isLoading) return;
      _name.text = user.fullName;
      _mobile.text = user.mobileNumber;
    });
    return AccountCard(icon: Icons.person_outline, title: l.profileTitle, children: [
      ...profile.when(
        loading: () => [const Center(child: CircularProgressIndicator())],
        error: (e, _) => [
          Notice(text: e is ApiException ? e.messageIn(l) : l.errorGeneric),
          OutlinedButton(onPressed: () => ref.invalidate(profileProvider), child: Text(l.tryAgain)),
        ],
        data: (user) {
          final mobileChanged = _mobileChanged(user);
          return [
            Form(
              key: _form,
              child: Column(crossAxisAlignment: CrossAxisAlignment.stretch, children: [
                if (_error != null) Notice(text: _error!),
                TextFormField(
                  initialValue: user.email,
                  readOnly: true,
                  enabled: false,
                  decoration: InputDecoration(labelText: l.emailLabel, helperText: l.profileEmailNote, helperMaxLines: 2),
                ),
                const SizedBox(height: 12),
                TextFormField(
                  controller: _name,
                  enabled: !_busy,
                  maxLength: 150,
                  autofillHints: const [AutofillHints.name],
                  decoration: InputDecoration(labelText: l.profileNameLabel),
                  validator: (v) => (v ?? '').trim().length < 2 ? l.profileNameInvalid : null,
                ),
                TextFormField(
                  controller: _mobile,
                  enabled: !_busy,
                  keyboardType: TextInputType.phone,
                  autofillHints: const [AutofillHints.telephoneNumber],
                  decoration: InputDecoration(labelText: l.mobileLabel),
                  validator: (v) => mobileChanged && normalizeMobile(v ?? '') == null ? l.mobileInvalid : null,
                ),
                if (mobileChanged) ...[
                  const SizedBox(height: 12),
                  PasswordFormField(
                    controller: _password,
                    enabled: !_busy,
                    autofillHints: const [AutofillHints.password],
                    decoration: InputDecoration(
                        labelText: l.currentPasswordLabel, helperText: l.profileMobilePasswordNote, helperMaxLines: 3),
                    validator: (v) => (v ?? '').isEmpty ? l.passwordRequired : null,
                  ),
                ],
                const SizedBox(height: 16),
                FilledButton(onPressed: _busy ? null : () => _save(user), child: Text(l.profileSave)),
              ]),
            ),
          ];
        },
      ),
    ]);
  }
}

/// Citizens: is my Aadhaar, ration card and mobile number verified? (read-only; changes go through the office).
class VerificationCard extends ConsumerWidget {
  const VerificationCard({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final l = AppLocalizations.of(context);
    final verification = ref.watch(verificationProvider);
    return AccountCard(icon: Icons.verified_user_outlined, title: l.verificationTitle, children: [
      ...verification.when(
        loading: () => [const Center(child: CircularProgressIndicator())],
        error: (e, _) => [
          Notice(text: e is ApiException ? e.messageIn(l) : l.errorGeneric),
          OutlinedButton(onPressed: () => ref.invalidate(verificationProvider), child: Text(l.tryAgain)),
        ],
        data: (v) => [
          if (v.isDemoData) ...[const DemoDataBanner(), const SizedBox(height: 12)],
          _row(l, l.verificationAadhaar, v.aadhaar),
          _row(l, l.verificationRationCard, v.rationCard),
          _row(l, l.verificationMobile, v.mobile),
          // After a number change the new number starts unverified; a code sent to it fixes that (no office visit).
          if (v.mobile.status != 'Verified') ...[
            const SizedBox(height: 4),
            Notice(text: l.verificationMobileHint, warning: true),
          ],
          const SizedBox(height: 8),
          Text(l.verificationHelp, style: const TextStyle(color: AppColors.muted)),
        ],
      ),
    ]);
  }

  static Widget _row(AppLocalizations l, String label, VerificationItem item) {
    final (text, tone) = switch (item.status) {
      'Verified' => (l.verificationVerified, PillTone.good),
      'Pending' => (l.verificationPending, PillTone.warn),
      'Failed' => (l.verificationFailed, PillTone.bad),
      'Expired' => (l.verificationExpired, PillTone.bad),
      _ => (l.verificationNotVerified, PillTone.warn),
    };
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 6),
      child: Row(crossAxisAlignment: CrossAxisAlignment.start, children: [
        Expanded(
          child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
            Text(label, style: const TextStyle(fontWeight: FontWeight.w600)),
            if (item.detail.isNotEmpty) Text(item.detail, style: const TextStyle(color: AppColors.muted)),
          ]),
        ),
        const SizedBox(width: 8),
        StatusPill(text: text, tone: tone),
      ]),
    );
  }
}

/// Shop owners, officials and admins: two-factor sign-in with an authenticator app (opt-in, like the website).
/// Once on, every password sign-in also asks for the app's 6-digit code.
class MfaCard extends ConsumerStatefulWidget {
  const MfaCard({super.key, required this.status});

  final MfaStatus status;

  @override
  ConsumerState<MfaCard> createState() => _MfaCardState();
}

class _MfaCardState extends ConsumerState<MfaCard> {
  final _form = GlobalKey<FormState>();
  final _password = TextEditingController();
  final _code = TextEditingController();
  MfaSetup? _setup;
  bool _busy = false;
  String? _error;

  @override
  void dispose() {
    _password.dispose();
    _code.dispose();
    super.dispose();
  }

  Future<void> _run(Future<void> Function(AccountRepository repo) action) async {
    FocusScope.of(context).unfocus();
    if (!_form.currentState!.validate()) return;
    final l = AppLocalizations.of(context);
    setState(() {
      _busy = true;
      _error = null;
    });
    try {
      await action(ref.read(accountRepositoryProvider));
    } on ApiException catch (e) {
      if (mounted) setState(() => _error = formProblem(l, e));
    } finally {
      if (mounted) setState(() => _busy = false);
    }
  }

  void _done(String message) {
    _password.clear();
    _code.clear();
    ref.invalidate(mfaStatusProvider);
    ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(message)));
  }

  @override
  Widget build(BuildContext context) {
    final l = AppLocalizations.of(context);
    final setup = _setup;
    final passwordField = PasswordFormField(
      controller: _password,
      enabled: !_busy,
      autofillHints: const [AutofillHints.password],
      decoration: InputDecoration(labelText: l.currentPasswordLabel),
      validator: (v) => (v ?? '').isEmpty ? l.passwordRequired : null,
    );
    final codeField = TextFormField(
      controller: _code,
      enabled: !_busy,
      keyboardType: TextInputType.number,
      maxLength: 6,
      autofillHints: const [AutofillHints.oneTimeCode],
      decoration: InputDecoration(labelText: l.codeLabel),
      validator: (v) => RegExp(r'^\d{6}$').hasMatch(v?.trim() ?? '') ? null : l.codeInvalidFormat,
    );

    final List<Widget> body;
    if (widget.status.enabled) {
      body = [
        Text(l.mfaIsOn, style: const TextStyle(fontWeight: FontWeight.w700)),
        const SizedBox(height: 4),
        Text(l.mfaOffHint, style: const TextStyle(color: AppColors.muted)),
        const SizedBox(height: 12),
        passwordField,
        const SizedBox(height: 8),
        codeField,
        OutlinedButton(
          onPressed: _busy
              ? null
              : () => _run((repo) async {
                    await repo.disableMfa(_password.text, _code.text.trim());
                    if (mounted) _done(l.mfaTurnedOff);
                  }),
          child: Text(l.mfaTurnOff),
        ),
      ];
    } else if (setup != null) {
      body = [
        Text(l.mfaScan),
        const SizedBox(height: 12),
        Center(
          child: Semantics(
            label: l.mfaQrLabel,
            child: Container(
              color: Colors.white,
              padding: const EdgeInsets.all(8),
              child: QrImageView(data: setup.otpauthUri, size: 180, errorCorrectionLevel: QrErrorCorrectLevel.M),
            ),
          ),
        ),
        const SizedBox(height: 12),
        Text(l.mfaManualKey, style: const TextStyle(color: AppColors.muted)),
        Row(children: [
          Expanded(child: SelectableText(setup.secret, style: const TextStyle(fontFamily: 'monospace', fontWeight: FontWeight.w600))),
          IconButton(
            icon: const Icon(Icons.copy),
            tooltip: l.mfaCopyKey,
            onPressed: () => Clipboard.setData(ClipboardData(text: setup.secret)),
          ),
        ]),
        const SizedBox(height: 8),
        codeField,
        FilledButton(
          onPressed: _busy
              ? null
              : () => _run((repo) async {
                    await repo.enableMfa(_code.text.trim());
                    if (!mounted) return;
                    setState(() => _setup = null);
                    _done(l.mfaTurnedOn);
                  }),
          child: Text(l.mfaTurnOn),
        ),
      ];
    } else {
      body = [
        Text(l.mfaIntro, style: const TextStyle(color: AppColors.muted)),
        const SizedBox(height: 12),
        passwordField,
        const SizedBox(height: 16),
        FilledButton(
          onPressed: _busy
              ? null
              : () => _run((repo) async {
                    final started = await repo.startMfa(_password.text);
                    _password.clear();
                    if (mounted) setState(() => _setup = started);
                  }),
          child: Text(l.mfaStart),
        ),
      ];
    }

    return AccountCard(icon: Icons.shield_outlined, title: l.mfaTitle, children: [
      Form(
        key: _form,
        child: Column(crossAxisAlignment: CrossAxisAlignment.stretch, children: [
          if (_error != null) Notice(text: _error!),
          ...body,
        ]),
      ),
    ]);
  }
}

/// A citizen closes their own account (Google Play's account-deletion rule). It needs the password, signs out
/// at once, and the privacy policy says when the records are erased. Staff accounts are closed by the office.
class CloseAccountCard extends ConsumerStatefulWidget {
  const CloseAccountCard({super.key});

  @override
  ConsumerState<CloseAccountCard> createState() => _CloseAccountCardState();
}

class _CloseAccountCardState extends ConsumerState<CloseAccountCard> {
  final _form = GlobalKey<FormState>();
  final _password = TextEditingController();
  bool _open = false;
  bool _busy = false;
  String? _error;

  @override
  void dispose() {
    _password.dispose();
    super.dispose();
  }

  Future<void> _close() async {
    if (!_form.currentState!.validate()) return;
    final l = AppLocalizations.of(context);
    final messenger = ScaffoldMessenger.of(context);
    setState(() {
      _busy = true;
      _error = null;
    });
    try {
      await ref.read(accountRepositoryProvider).closeAccount(_password.text);
      messenger.showSnackBar(SnackBar(content: Text(l.closeAccountDone)));
      await ref.read(authControllerProvider.notifier).signOut();
    } on ApiException catch (e) {
      if (mounted) setState(() => _error = formProblem(l, e));
    } finally {
      if (mounted) setState(() => _busy = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final l = AppLocalizations.of(context);
    final danger = Theme.of(context).colorScheme.error;
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Form(
          key: _form,
          child: Column(crossAxisAlignment: CrossAxisAlignment.stretch, children: [
            Row(children: [
              Icon(Icons.person_remove_outlined, color: danger),
              const SizedBox(width: 12),
              Expanded(
                child: Text(l.closeAccountTitle,
                    style: Theme.of(context).textTheme.titleMedium?.copyWith(fontWeight: FontWeight.w700)),
              ),
            ]),
            const SizedBox(height: 8),
            Text(l.closeAccountIntro, style: const TextStyle(color: AppColors.muted)),
            const SizedBox(height: 16),
            if (!_open)
              OutlinedButton(
                style: OutlinedButton.styleFrom(foregroundColor: danger),
                onPressed: () => setState(() => _open = true),
                child: Text(l.closeAccountTitle),
              )
            else ...[
              PasswordFormField(
                controller: _password,
                enabled: !_busy,
                autofillHints: const [AutofillHints.password],
                decoration: InputDecoration(labelText: l.currentPasswordLabel),
                validator: (v) => (v ?? '').isEmpty ? l.passwordRequired : null,
              ),
              if (_error != null) ...[const SizedBox(height: 12), Notice(text: _error!)],
              const SizedBox(height: 16),
              FilledButton(
                style: FilledButton.styleFrom(backgroundColor: danger),
                onPressed: _busy ? null : _close,
                child: Text(_busy ? l.closeAccountClosing : l.closeAccountConfirm),
              ),
              TextButton(
                onPressed: _busy ? null : () => setState(() => _open = false),
                child: Text(l.cancelButton),
              ),
            ],
          ]),
        ),
      ),
    );
  }
}
