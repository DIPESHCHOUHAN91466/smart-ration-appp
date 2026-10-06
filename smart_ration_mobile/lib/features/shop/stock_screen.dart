import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../app/theme.dart';
import '../../core/network/api_exception.dart';
import '../../l10n/app_localizations.dart';
import '../citizen/citizen_widgets.dart';
import 'shop_data.dart';

/// My shop's stock. Deliveries and damaged stock are recorded as movements in the backend's stock
/// ledger, so every change can be traced later. "Correct count" (the website's inventory edit) sets the
/// balance directly for counting mistakes; the backend records that as a manual correction in the same ledger.
class StockScreen extends ConsumerWidget {
  const StockScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final l = AppLocalizations.of(context);
    final stock = ref.watch(shopStockProvider);
    return Scaffold(
      appBar: AppBar(title: Text(l.stockButton)),
      body: RefreshIndicator(
        onRefresh: () => ref.refresh(shopStockProvider.future),
        child: ListView(
          padding: const EdgeInsets.all(16),
          children: stock.when(
            loading: () => [const SizedBox(height: 80), const Center(child: CircularProgressIndicator())],
            error: (e, _) => [
              Text(e is ApiException ? e.messageIn(l) : l.errorGeneric, textAlign: TextAlign.center),
              TextButton(onPressed: () => ref.invalidate(shopStockProvider), child: Text(l.tryAgain)),
            ],
            data: (lines) => lines.isEmpty
                ? [Text(l.noStockLines, style: Theme.of(context).textTheme.titleMedium)]
                : [
                    // Low items first, so they are seen.
                    for (final line in [...lines.where((s) => s.low), ...lines.where((s) => !s.low)]) _StockCard(line: line),
                  ],
          ),
        ),
      ),
    );
  }
}

enum _Movement { receive, writeOff }

class _StockCard extends ConsumerWidget {
  const _StockCard({required this.line});

  final StockLine line;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final l = AppLocalizations.of(context);
    final unit = unitWord(l, line.rationType);
    return Card(
      margin: const EdgeInsets.only(bottom: 12),
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(crossAxisAlignment: CrossAxisAlignment.stretch, children: [
          Row(children: [
            Icon(itemIcon(line.rationType), color: AppColors.blue, size: 26),
            const SizedBox(width: 10),
            Expanded(
              child: Text(itemWord(l, line.rationType), style: Theme.of(context).textTheme.titleMedium?.copyWith(fontWeight: FontWeight.w700)),
            ),
            StatusPill(text: line.low ? l.stockLow : l.stockOk, tone: line.low ? PillTone.bad : PillTone.good),
          ]),
          const SizedBox(height: 10),
          InfoRow(
            label: l.stockAvailable,
            value: Text('${amount(line.available)} $unit',
                textAlign: TextAlign.end,
                style: TextStyle(fontSize: 20, fontWeight: FontWeight.w800, color: line.low ? AppColors.danger : AppColors.ink)),
          ),
          InfoRow(label: l.stockMinimum, value: valueText('${amount(line.minimum)} $unit')),
          InfoRow(label: l.stockHandedOut, value: valueText('${amount(line.handedOut)} $unit')),
          const SizedBox(height: 10),
          Wrap(spacing: 10, runSpacing: 8, children: [
            FilledButton.tonalIcon(
              icon: const Icon(Icons.local_shipping_outlined),
              label: Text(l.receiveStock),
              onPressed: () => _open(context, ref, _Movement.receive),
            ),
            OutlinedButton.icon(
              style: OutlinedButton.styleFrom(foregroundColor: AppColors.danger),
              icon: const Icon(Icons.delete_outline),
              label: Text(l.writeOffStock),
              onPressed: line.available > 0 ? () => _open(context, ref, _Movement.writeOff) : null,
            ),
            TextButton.icon(
              icon: const Icon(Icons.edit_outlined),
              label: Text(l.correctStock),
              onPressed: () => _correct(context, ref),
            ),
          ]),
        ]),
      ),
    );
  }

  Future<void> _open(BuildContext context, WidgetRef ref, _Movement kind) async {
    final l = AppLocalizations.of(context);
    final messenger = ScaffoldMessenger.of(context);
    final saved = await showModalBottomSheet<bool>(
      context: context,
      isScrollControlled: true,
      showDragHandle: true,
      builder: (_) => _MovementForm(line: line, kind: kind),
    );
    if (saved != true) return;
    ref.invalidate(shopStockProvider);
    ref.invalidate(shopDashboardProvider);
    messenger.showSnackBar(SnackBar(content: Text(kind == _Movement.receive ? l.stockReceived : l.stockWrittenOff)));
  }

  Future<void> _correct(BuildContext context, WidgetRef ref) async {
    final l = AppLocalizations.of(context);
    final messenger = ScaffoldMessenger.of(context);
    final saved = await showModalBottomSheet<bool>(
      context: context,
      isScrollControlled: true,
      showDragHandle: true,
      builder: (_) => _CorrectForm(line: line),
    );
    if (saved != true) return;
    ref.invalidate(shopStockProvider);
    ref.invalidate(shopDashboardProvider);
    messenger.showSnackBar(SnackBar(content: Text(l.stockCorrected)));
  }
}

/// Fixes a counting mistake: the balance and the minimum level, both filled in with today's values.
class _CorrectForm extends ConsumerStatefulWidget {
  const _CorrectForm({required this.line});

  final StockLine line;

  @override
  ConsumerState<_CorrectForm> createState() => _CorrectFormState();
}

class _CorrectFormState extends ConsumerState<_CorrectForm> {
  late final _available = TextEditingController(text: amount(widget.line.available));
  late final _minimum = TextEditingController(text: amount(widget.line.minimum));
  String? _availableError;
  String? _minimumError;
  String? _error;
  bool _saving = false;

  @override
  void dispose() {
    _available.dispose();
    _minimum.dispose();
    super.dispose();
  }

  /// 0 or more (unlike a delivery, a count may be zero); null after saying why not.
  double? _parse(AppLocalizations l, TextEditingController field, void Function(String?) showError) {
    final v = double.tryParse(field.text.trim().replaceAll(',', '.'));
    final problem = v == null || v < 0 ? l.amountInvalid : (v > 1000000 ? l.quantityTooLarge : null);
    showError(problem);
    return problem == null ? v : null;
  }

  Future<void> _save() async {
    final l = AppLocalizations.of(context);
    String? availableProblem;
    String? minimumProblem;
    final available = _parse(l, _available, (p) => availableProblem = p);
    final minimum = _parse(l, _minimum, (p) => minimumProblem = p);
    setState(() {
      _availableError = availableProblem;
      _minimumError = minimumProblem;
      _error = null;
    });
    if (available == null || minimum == null) return;
    final line = widget.line;
    if (available == line.available && minimum == line.minimum) {
      setState(() => _error = l.correctNoChange);
      return;
    }
    if (available != line.available) {
      final unit = unitWord(l, line.rationType);
      final yes = await showDialog<bool>(
        context: context,
        builder: (dialog) => AlertDialog(
          title: Text(l.correctConfirmTitle(itemWord(l, line.rationType), '${amount(line.available)} $unit', '${amount(available)} $unit')),
          content: Text(l.correctConfirmBody),
          actions: [
            TextButton(onPressed: () => Navigator.pop(dialog, false), child: Text(l.cancelButton)),
            FilledButton(onPressed: () => Navigator.pop(dialog, true), child: Text(l.saveButton)),
          ],
        ),
      );
      if (yes != true || !mounted) return;
    }
    setState(() => _saving = true);
    try {
      await ref.read(shopRepositoryProvider).correct(line.id, available: available, minimum: minimum);
      if (mounted) Navigator.pop(context, true);
    } on ApiException catch (e) {
      if (mounted) setState(() => _error = e.messageIn(l));
    } finally {
      if (mounted) setState(() => _saving = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final l = AppLocalizations.of(context);
    final unit = unitWord(l, widget.line.rationType);
    final number = [FilteringTextInputFormatter.allow(RegExp(r'[0-9.,]'))];
    return Padding(
      padding: EdgeInsets.fromLTRB(20, 0, 20, 20 + MediaQuery.viewInsetsOf(context).bottom),
      child: SingleChildScrollView(
        child: Column(mainAxisSize: MainAxisSize.min, crossAxisAlignment: CrossAxisAlignment.stretch, children: [
          Text('${l.correctStock}: ${itemWord(l, widget.line.rationType)}',
              style: Theme.of(context).textTheme.titleLarge?.copyWith(fontWeight: FontWeight.w700)),
          const SizedBox(height: 6),
          Text(l.correctStockHint, style: const TextStyle(color: AppColors.muted)),
          const SizedBox(height: 16),
          TextField(
            controller: _available,
            keyboardType: const TextInputType.numberWithOptions(decimal: true),
            inputFormatters: number,
            decoration: InputDecoration(labelText: l.correctInStock(unit), errorText: _availableError),
          ),
          const SizedBox(height: 12),
          TextField(
            controller: _minimum,
            keyboardType: const TextInputType.numberWithOptions(decimal: true),
            inputFormatters: number,
            decoration: InputDecoration(labelText: l.correctMinimum(unit), errorText: _minimumError),
          ),
          if (_error != null) ...[
            const SizedBox(height: 8),
            Semantics(liveRegion: true, child: Text(_error!, style: const TextStyle(color: AppColors.danger, fontWeight: FontWeight.w600))),
          ],
          const SizedBox(height: 16),
          FilledButton(
            onPressed: _saving ? null : _save,
            child: _saving
                ? const SizedBox.square(dimension: 22, child: CircularProgressIndicator(strokeWidth: 3))
                : Text(l.saveButton),
          ),
        ]),
      ),
    );
  }
}

class _MovementForm extends ConsumerStatefulWidget {
  const _MovementForm({required this.line, required this.kind});

  final StockLine line;
  final _Movement kind;

  @override
  ConsumerState<_MovementForm> createState() => _MovementFormState();
}

class _MovementFormState extends ConsumerState<_MovementForm> {
  /// Chosen once while this form is open and reused on every retry, so a save whose answer was lost
  /// (e.g. a timeout) is not recorded twice when Save is pressed again.
  final _requestKey = newRequestKey();
  final _quantity = TextEditingController();
  final _reference = TextEditingController();
  final _note = TextEditingController();
  String? _quantityError;
  String? _referenceError;
  String? _error;
  bool _saving = false;

  @override
  void dispose() {
    _quantity.dispose();
    _reference.dispose();
    _note.dispose();
    super.dispose();
  }

  /// The typed quantity, or null after showing why it can't be used.
  double? _validQuantity(AppLocalizations l) {
    final unit = unitWord(l, widget.line.rationType);
    final q = double.tryParse(_quantity.text.trim().replaceAll(',', '.'));
    String? problem;
    if (q == null || q <= 0) {
      problem = l.quantityInvalid;
    } else if (q > 1000000) {
      problem = l.quantityTooLarge;
    } else if (widget.kind == _Movement.writeOff && q > widget.line.available) {
      problem = l.writeOffTooMuch(amount(widget.line.available), unit);
    }
    setState(() => _quantityError = problem);
    return problem == null ? q : null;
  }

  Future<void> _save() async {
    final l = AppLocalizations.of(context);
    final quantity = _validQuantity(l);
    final referenceOk = stockReferencePattern.hasMatch(_reference.text.trim());
    setState(() => _referenceError = referenceOk ? null : l.referenceInvalid);
    if (quantity == null || !referenceOk) return;

    final unit = unitWord(l, widget.line.rationType);
    if (widget.kind == _Movement.writeOff) {
      final yes = await showDialog<bool>(
        context: context,
        builder: (dialog) => AlertDialog(
          title: Text(l.writeOffConfirmTitle('${amount(quantity)} $unit ${itemWord(l, widget.line.rationType)}')),
          content: Text(l.writeOffConfirmBody),
          actions: [
            TextButton(onPressed: () => Navigator.pop(dialog, false), child: Text(l.cancelButton)),
            FilledButton(
              style: FilledButton.styleFrom(backgroundColor: AppColors.danger),
              onPressed: () => Navigator.pop(dialog, true),
              child: Text(l.writeOffStock),
            ),
          ],
        ),
      );
      if (yes != true || !mounted) return;
    }

    setState(() {
      _saving = true;
      _error = null;
    });
    final repo = ref.read(shopRepositoryProvider);
    try {
      if (widget.kind == _Movement.receive) {
        await repo.receive(widget.line.id, quantity, requestKey: _requestKey, reference: _reference.text, note: _note.text);
      } else {
        await repo.writeOff(widget.line.id, quantity, requestKey: _requestKey, reference: _reference.text, note: _note.text);
      }
      if (mounted) Navigator.pop(context, true);
    } on ApiException catch (e) {
      // The key was already used: an earlier press of Save did go through, with different numbers.
      final alreadySaved = e.errorCode == 'IDEMPOTENCY_KEY_REUSED' || e.errorCode == 'CONCURRENT_UPDATE';
      if (mounted) setState(() => _error = alreadySaved ? l.stockAlreadySaved : e.messageIn(l));
    } finally {
      if (mounted) setState(() => _saving = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final l = AppLocalizations.of(context);
    final unit = unitWord(l, widget.line.rationType);
    final title = '${widget.kind == _Movement.receive ? l.receiveStock : l.writeOffStock}: ${itemWord(l, widget.line.rationType)}';
    return Padding(
      // Keeps the form above the keyboard.
      padding: EdgeInsets.fromLTRB(20, 0, 20, 20 + MediaQuery.viewInsetsOf(context).bottom),
      child: Column(mainAxisSize: MainAxisSize.min, crossAxisAlignment: CrossAxisAlignment.stretch, children: [
        Text(title, style: Theme.of(context).textTheme.titleLarge?.copyWith(fontWeight: FontWeight.w700)),
        Text('${l.stockAvailable}: ${amount(widget.line.available)} $unit', style: const TextStyle(color: AppColors.muted)),
        const SizedBox(height: 16),
        TextField(
          controller: _quantity,
          autofocus: true,
          keyboardType: const TextInputType.numberWithOptions(decimal: true),
          inputFormatters: [FilteringTextInputFormatter.allow(RegExp(r'[0-9.,]'))],
          decoration: InputDecoration(labelText: l.quantityLabel(unit), errorText: _quantityError),
        ),
        const SizedBox(height: 12),
        TextField(
          controller: _reference,
          maxLength: 64,
          decoration: InputDecoration(labelText: l.referenceLabel, errorText: _referenceError, counterText: ''),
        ),
        const SizedBox(height: 12),
        TextField(controller: _note, maxLength: 256, decoration: InputDecoration(labelText: l.noteLabel, counterText: '')),
        if (_error != null) ...[
          const SizedBox(height: 8),
          Semantics(liveRegion: true, child: Text(_error!, style: const TextStyle(color: AppColors.danger, fontWeight: FontWeight.w600))),
        ],
        const SizedBox(height: 16),
        FilledButton(
          style: widget.kind == _Movement.writeOff ? FilledButton.styleFrom(backgroundColor: AppColors.danger) : null,
          onPressed: _saving ? null : _save,
          child: _saving
              ? const SizedBox.square(dimension: 22, child: CircularProgressIndicator(strokeWidth: 3))
              : Text(l.saveButton),
        ),
      ]),
    );
  }
}
