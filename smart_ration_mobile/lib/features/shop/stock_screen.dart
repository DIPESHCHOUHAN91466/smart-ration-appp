import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../app/theme.dart';
import '../../core/network/api_exception.dart';
import '../../l10n/app_localizations.dart';
import '../citizen/citizen_widgets.dart';
import 'shop_data.dart';

/// My shop's stock. Deliveries and damaged stock are recorded as movements in the backend's stock
/// ledger (never by overwriting the balance), so every change can be traced later.
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
}

class _MovementForm extends ConsumerStatefulWidget {
  const _MovementForm({required this.line, required this.kind});

  final StockLine line;
  final _Movement kind;

  @override
  ConsumerState<_MovementForm> createState() => _MovementFormState();
}

class _MovementFormState extends ConsumerState<_MovementForm> {
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
        await repo.receive(widget.line.id, quantity, reference: _reference.text, note: _note.text);
      } else {
        await repo.writeOff(widget.line.id, quantity, reference: _reference.text, note: _note.text);
      }
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
