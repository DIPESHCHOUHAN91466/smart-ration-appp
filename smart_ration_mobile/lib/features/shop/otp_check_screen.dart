import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../app/routes.dart';
import '../../app/theme.dart';
import '../../core/network/api_exception.dart';
import '../../core/providers.dart';
import '../../l10n/app_localizations.dart';
import 'shop_data.dart';
import 'shop_words.dart';

/// For a customer without their QR: a 6-digit code goes to their registered mobile, they read it
/// out, and the backend finds their booking at this shop. The code is checked only on the backend.
class OtpCheckScreen extends ConsumerStatefulWidget {
  const OtpCheckScreen({super.key});

  @override
  ConsumerState<OtpCheckScreen> createState() => _OtpCheckScreenState();
}

class _OtpCheckScreenState extends ConsumerState<OtpCheckScreen> {
  final _mobile = TextEditingController();
  final _code = TextEditingController();
  OtpRequest? _sent;
  bool _busy = false;
  String? _error;

  @override
  void dispose() {
    _mobile.dispose();
    _code.dispose();
    super.dispose();
  }

  Future<void> _send() async {
    final l = AppLocalizations.of(context);
    final mobile = _mobile.text.trim();
    if (!RegExp(r'^[0-9]{10}$').hasMatch(mobile)) {
      setState(() => _error = l.mobileInvalid);
      return;
    }
    await _run(() async {
      final sent = await ref.read(shopRepositoryProvider).requestOtp(mobile);
      if (mounted) setState(() => _sent = sent);
    });
  }

  Future<void> _verify() async {
    final l = AppLocalizations.of(context);
    final code = _code.text.trim();
    if (!RegExp(r'^[0-9]{6}$').hasMatch(code)) {
      setState(() => _error = l.codeInvalidFormat);
      return;
    }
    await _run(() async {
      final check = await ref.read(shopRepositoryProvider).verifyOtp(_sent!.id, code);
      if (mounted) context.pushReplacement(Routes.shopCheck, extra: check);
    });
  }

  Future<void> _run(Future<void> Function() step) async {
    final l = AppLocalizations.of(context);
    FocusScope.of(context).unfocus();
    setState(() {
      _busy = true;
      _error = null;
    });
    try {
      await step();
    } on ApiException catch (e) {
      if (mounted) setState(() => _error = counterOtpErrorIn(l, e));
    } finally {
      if (mounted) setState(() => _busy = false);
    }
  }

  void _changeNumber() => setState(() {
        _sent = null;
        _code.clear();
        _error = null;
      });

  @override
  Widget build(BuildContext context) {
    final l = AppLocalizations.of(context);
    final sent = _sent;
    final showDemo = ref.watch(envProvider).isDevelopment;
    return Scaffold(
      appBar: AppBar(title: Text(l.otpCheckTitle)),
      body: ListView(
        padding: const EdgeInsets.all(16),
        children: [
          if (sent == null) ...[
            Text(l.otpCheckHelp, style: const TextStyle(fontSize: 16)),
            const SizedBox(height: 16),
            TextField(
              controller: _mobile,
              keyboardType: TextInputType.phone,
              inputFormatters: [FilteringTextInputFormatter.digitsOnly, LengthLimitingTextInputFormatter(10)],
              decoration: InputDecoration(labelText: l.customerMobileLabel, prefixIcon: const Icon(Icons.phone_android)),
              onSubmitted: (_) => _send(),
            ),
          ] else ...[
            Text(l.askCustomerForCode(sent.mobileMasked, sent.expiresInMinutes), style: const TextStyle(fontSize: 16)),
            if (showDemo && sent.demoCode != null) ...[
              const SizedBox(height: 8),
              Text(l.demoCodeHint(sent.demoCode!), style: const TextStyle(color: AppColors.muted)),
            ],
            const SizedBox(height: 16),
            TextField(
              controller: _code,
              keyboardType: TextInputType.number,
              inputFormatters: [FilteringTextInputFormatter.digitsOnly, LengthLimitingTextInputFormatter(6)],
              autofillHints: const [AutofillHints.oneTimeCode],
              decoration: InputDecoration(labelText: l.codeLabel, prefixIcon: const Icon(Icons.pin_outlined)),
              onSubmitted: (_) => _verify(),
            ),
          ],
          if (_error != null) ...[
            const SizedBox(height: 12),
            Semantics(
              liveRegion: true,
              child: Text(_error!, style: const TextStyle(color: AppColors.danger, fontSize: 16, fontWeight: FontWeight.w600)),
            ),
          ],
          const SizedBox(height: 20),
          FilledButton(
            onPressed: _busy ? null : (sent == null ? _send : _verify),
            child: _busy
                ? const SizedBox.square(dimension: 22, child: CircularProgressIndicator(strokeWidth: 3))
                : Text(sent == null ? l.sendCode : l.verifyCodeButton),
          ),
          if (sent != null) TextButton(onPressed: _busy ? null : _changeNumber, child: Text(l.changeNumber)),
        ],
      ),
    );
  }
}
