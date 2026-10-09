import 'dart:convert';

import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../app/routes.dart';
import '../../app/theme.dart';
import '../../core/file_saver.dart';
import '../../core/network/api_exception.dart';
import '../../core/providers.dart';
import '../../l10n/app_localizations.dart';
import '../auth/auth_controller.dart';
import '../auth/login_screen.dart' show Notice;
import '../auth/session.dart';
import 'account_data.dart';
import 'account_sections.dart';

/// File name for the export, e.g. smart-ration-my-data-2026-10-06.json (same as the website).
String exportFileName(DateTime now) =>
    'smart-ration-my-data-${now.year}-${now.month.toString().padLeft(2, '0')}-${now.day.toString().padLeft(2, '0')}.json';

/// My account (any signed-in role): my profile (name, mobile), citizens' verification status, staff two-factor sign-in,
/// change the password, and "Download my data" (DPDP Act 2023) — everything the
/// service holds about the person as one JSON file (GET /api/users/me/export). The file is made in memory and goes
/// straight to where the person chooses; the app keeps no copy.
class AccountScreen extends ConsumerStatefulWidget {
  const AccountScreen({super.key});

  @override
  ConsumerState<AccountScreen> createState() => _AccountScreenState();
}

class _AccountScreenState extends ConsumerState<AccountScreen> {
  bool _busy = false;
  String? _error;

  Future<void> _download() async {
    final l = AppLocalizations.of(context);
    setState(() {
      _busy = true;
      _error = null;
    });
    try {
      final data = await ref.read(apiClientProvider).get<Object?>('/api/users/me/export');
      if (data == null) throw const ApiException(ApiErrorKind.unknown);
      final bytes = Uint8List.fromList(utf8.encode(const JsonEncoder.withIndent('  ').convert(data)));
      final saved = await ref.read(fileSaverProvider).save(name: exportFileName(DateTime.now()), mimeType: 'application/json', bytes: bytes);
      if (saved && mounted) ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(l.exportDone)));
    } on ApiException catch (e) {
      if (mounted) setState(() => _error = e.kind == ApiErrorKind.unknown ? l.exportFailed : e.messageIn(l));
    } on PlatformException {
      if (mounted) setState(() => _error = l.exportFailed);
    } finally {
      if (mounted) setState(() => _busy = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final l = AppLocalizations.of(context);
    final heading = Theme.of(context).textTheme.titleMedium?.copyWith(fontWeight: FontWeight.w700);
    final isCitizen = ref.watch(authControllerProvider)?.role == AppRole.ruralUser;
    // Two-factor sign-in is for staff; it is shown when the server offers it, or when it is already on.
    final mfa = isCitizen ? null : ref.watch(mfaStatusProvider).value;
    return Scaffold(
      appBar: AppBar(title: Text(l.accountTitle)),
      body: SafeArea(
        child: ListView(padding: const EdgeInsets.all(20), children: [
          const ProfileCard(),
          const SizedBox(height: 16),
          if (isCitizen) ...[const VerificationCard(), const SizedBox(height: 16)],
          if (mfa != null && (mfa.available || mfa.enabled)) ...[MfaCard(status: mfa), const SizedBox(height: 16)],
          Card(
            child: ListTile(
              leading: const Icon(Icons.password),
              title: Text(l.changePasswordTitle),
              trailing: const Icon(Icons.chevron_right),
              onTap: () => context.push(Routes.changePassword),
            ),
          ),
          const SizedBox(height: 16),
          Card(
            child: Padding(
              padding: const EdgeInsets.all(16),
              child: Column(crossAxisAlignment: CrossAxisAlignment.stretch, children: [
                Row(children: [
                  const Icon(Icons.download),
                  const SizedBox(width: 12),
                  Expanded(child: Text(l.exportTitle, style: heading)),
                ]),
                const SizedBox(height: 8),
                Text(l.exportIntro, style: const TextStyle(color: AppColors.muted)),
                if (_error != null) ...[const SizedBox(height: 12), Notice(text: _error!)],
                const SizedBox(height: 16),
                OutlinedButton.icon(
                  onPressed: _busy ? null : _download,
                  icon: _busy
                      ? const SizedBox.square(dimension: 18, child: CircularProgressIndicator(strokeWidth: 2))
                      : const Icon(Icons.save_alt),
                  label: Text(_busy ? l.exportPreparing : l.exportDownload),
                ),
              ]),
            ),
          ),
          if (isCitizen) ...[const SizedBox(height: 16), const CloseAccountCard()],
        ]),
      ),
    );
  }
}
