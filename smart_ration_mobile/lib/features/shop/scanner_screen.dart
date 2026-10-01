import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:mobile_scanner/mobile_scanner.dart';

import '../../app/routes.dart';
import '../../app/theme.dart';
import '../../core/network/api_exception.dart';
import '../../l10n/app_localizations.dart';
import 'shop_data.dart';
import 'shop_words.dart';

/// Shows the camera and calls [onCode] with the text of each QR code it sees.
typedef CameraView = Widget Function(BuildContext context, ValueChanged<String> onCode);

/// The live camera. Tests replace it, since there is no camera in a test.
final cameraViewProvider = Provider<CameraView>((ref) => (context, onCode) => _LiveCamera(onCode: onCode));

/// Scan the customer's QR (or type the code under it). The phone only reads the code; the backend
/// checks the signature, the shop, the date and the customer, and answers with a status.
class ScannerScreen extends ConsumerStatefulWidget {
  const ScannerScreen({super.key});

  @override
  ConsumerState<ScannerScreen> createState() => _ScannerScreenState();
}

class _ScannerScreenState extends ConsumerState<ScannerScreen> {
  final _typed = TextEditingController();
  bool _busy = false;

  /// The last code handled. The camera sees the same QR many times a second, so it is ignored
  /// until the shopkeeper taps "Scan again" or shows a different code.
  String? _lastCode;
  String? _refusal;
  String? _typedError;

  @override
  void dispose() {
    _typed.dispose();
    super.dispose();
  }

  void _fromCamera(String code) {
    if (_busy || code == _lastCode || !(ModalRoute.of(context)?.isCurrent ?? true)) return;
    HapticFeedback.mediumImpact();
    _check(code);
  }

  void _fromKeyboard() {
    final l = AppLocalizations.of(context);
    final code = _typed.text.trim().toUpperCase();
    if (!code.startsWith('SRQR-')) {
      setState(() => _typedError = l.typeCodeInvalid);
      return;
    }
    FocusScope.of(context).unfocus();
    setState(() => _typedError = null);
    _check(code);
  }

  Future<void> _check(String code) async {
    final l = AppLocalizations.of(context);
    setState(() {
      _busy = true;
      _refusal = null;
      _lastCode = code;
    });
    String? refusal;
    try {
      final outcome = await ref.read(shopRepositoryProvider).scan(code);
      final check = outcome.check;
      if (check != null) {
        // A booking at this shop: the check screen shows whether it can be collected, and why not.
        if (!mounted) return;
        setState(() => _busy = false);
        context.push(Routes.shopCheck, extra: check);
        return;
      }
      refusal = scanRefusalIn(l, outcome.status, outcome.message);
    } on ApiException catch (e) {
      refusal = e.messageIn(l);
    }
    if (mounted) {
      setState(() {
        _busy = false;
        _refusal = refusal;
      });
    }
  }

  void _scanAgain() => setState(() {
        _lastCode = null;
        _refusal = null;
      });

  @override
  Widget build(BuildContext context) {
    final l = AppLocalizations.of(context);
    final camera = ref.watch(cameraViewProvider);
    // The camera runs only while this screen is in front: it is released while the customer check
    // (or anything else) is open on top, and starts again on return.
    final inFront = ModalRoute.of(context)?.isCurrent ?? true;
    return Scaffold(
      appBar: AppBar(title: Text(l.scannerTitle)),
      body: ListView(
        padding: const EdgeInsets.all(16),
        children: [
          Text(l.scannerHelp, textAlign: TextAlign.center, style: Theme.of(context).textTheme.titleMedium),
          const SizedBox(height: 12),
          AspectRatio(
            aspectRatio: 1,
            child: ClipRRect(
              borderRadius: BorderRadius.circular(16),
              child: ColoredBox(
                color: Colors.black,
                child: _busy || !inFront
                    ? const Center(child: CircularProgressIndicator(color: Colors.white))
                    : Stack(fit: StackFit.expand, children: [
                        camera(context, _fromCamera),
                        const IgnorePointer(child: _Frame()),
                      ]),
              ),
            ),
          ),
          const SizedBox(height: 12),
          if (_busy)
            Text(l.checking, textAlign: TextAlign.center, style: const TextStyle(fontSize: 16))
          else if (_refusal != null)
            _Refusal(message: _refusal!, onScanAgain: _scanAgain)
          else if (_lastCode != null)
            TextButton.icon(onPressed: _scanAgain, icon: const Icon(Icons.refresh), label: Text(l.scanAgain)),
          const SizedBox(height: 16),
          TextField(
            controller: _typed,
            textCapitalization: TextCapitalization.characters,
            autocorrect: false,
            enableSuggestions: false,
            decoration: InputDecoration(labelText: l.typeCodeLabel, hintText: 'SRQR-…', errorText: _typedError),
            onSubmitted: (_) => _fromKeyboard(),
          ),
          const SizedBox(height: 12),
          OutlinedButton.icon(
            icon: const Icon(Icons.keyboard),
            label: Text(l.checkCode),
            onPressed: _busy ? null : _fromKeyboard,
          ),
        ],
      ),
    );
  }
}

class _LiveCamera extends StatelessWidget {
  const _LiveCamera({required this.onCode});

  final ValueChanged<String> onCode;

  @override
  Widget build(BuildContext context) {
    final l = AppLocalizations.of(context);
    return MobileScanner(
      onDetect: (capture) {
        final text = capture.barcodes.map((b) => b.rawValue).nonNulls.where((v) => v.isNotEmpty).firstOrNull;
        if (text != null) onCode(text);
      },
      errorBuilder: (context, error) => Center(
        child: Padding(
          padding: const EdgeInsets.all(20),
          child: Text(
            error.errorCode == MobileScannerErrorCode.permissionDenied ? l.cameraDenied : l.cameraUnavailable,
            textAlign: TextAlign.center,
            style: const TextStyle(color: Colors.white, fontSize: 16),
          ),
        ),
      ),
    );
  }
}

/// Corner marks showing where to hold the QR.
class _Frame extends StatelessWidget {
  const _Frame();

  @override
  Widget build(BuildContext context) => Padding(
        padding: const EdgeInsets.all(40),
        child: DecoratedBox(
          decoration: BoxDecoration(border: Border.all(color: Colors.white70, width: 3), borderRadius: BorderRadius.circular(12)),
        ),
      );
}

class _Refusal extends StatelessWidget {
  const _Refusal({required this.message, required this.onScanAgain});

  final String message;
  final VoidCallback onScanAgain;

  @override
  Widget build(BuildContext context) {
    final l = AppLocalizations.of(context);
    return Card(
      color: AppColors.dangerSoft,
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(crossAxisAlignment: CrossAxisAlignment.stretch, children: [
          // Read out as soon as it appears.
          Semantics(
            liveRegion: true,
            child: Row(children: [
              const Icon(Icons.block, color: AppColors.danger, size: 28),
              const SizedBox(width: 10),
              Expanded(
                child: Text(l.scanRejectedTitle,
                    style: const TextStyle(color: AppColors.danger, fontWeight: FontWeight.w800, fontSize: 18)),
              ),
            ]),
          ),
          const SizedBox(height: 8),
          Text(message, style: const TextStyle(fontSize: 16)),
          const SizedBox(height: 8),
          Align(
            alignment: AlignmentDirectional.centerEnd,
            child: TextButton.icon(onPressed: onScanAgain, icon: const Icon(Icons.refresh), label: Text(l.scanAgain)),
          ),
        ]),
      ),
    );
  }
}
