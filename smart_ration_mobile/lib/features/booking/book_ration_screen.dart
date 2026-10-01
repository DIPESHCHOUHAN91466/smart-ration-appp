import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../app/routes.dart';
import '../../app/theme.dart';
import '../../core/network/api_exception.dart';
import '../../l10n/app_localizations.dart';
import '../citizen/citizen_data.dart';
import '../citizen/citizen_widgets.dart';
import 'booking_data.dart';
import 'booking_widgets.dart';

/// How many days ahead a citizen can book.
const bookingDays = 7;

final _slotsProvider = FutureProvider.autoDispose.family<List<Slot>, (int, String)>(
    (ref, key) => ref.watch(bookingRepositoryProvider).slots(key.$1, DateTime.parse(key.$2)));
final _itemsProvider =
    FutureProvider.autoDispose.family<List<BookableItem>, int>((ref, shopId) => ref.watch(bookingRepositoryProvider).items(shopId));

/// Book a 5-minute slot at the family's own ration shop: day -> time -> items -> token.
/// The backend checks everything again (slot still free, within quota, in stock) and creates the token.
class BookRationScreen extends ConsumerStatefulWidget {
  const BookRationScreen({super.key, this.now});

  /// For tests; otherwise the phone's clock.
  final DateTime Function()? now;

  @override
  ConsumerState<BookRationScreen> createState() => _BookRationScreenState();
}

class _BookRationScreenState extends ConsumerState<BookRationScreen> {
  late DateTime _day;
  int? _slotId;
  Map<String, double>? _quantities; // set when the items arrive: each starts at its maximum
  bool _busy = false;
  String? _error;

  DateTime get _now => widget.now?.call() ?? DateTime.now();

  @override
  void initState() {
    super.initState();
    final n = _now;
    _day = DateTime(n.year, n.month, n.day);
  }

  Future<void> _book(int shopId) async {
    final l = AppLocalizations.of(context);
    final items = {for (final e in (_quantities ?? const <String, double>{}).entries) if (e.value > 0) e.key: e.value};
    if (_slotId == null) return setState(() => _error = l.chooseTimeFirst);
    if (items.isEmpty) return setState(() => _error = l.chooseItemFirst);

    setState(() {
      _busy = true;
      _error = null;
    });
    try {
      final token = await ref.read(bookingRepositoryProvider).book(shopId: shopId, slotId: _slotId!, items: items);
      ref.invalidate(myTokensProvider);
      ref.invalidate(citizenOverviewProvider);
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(l.tokenReady)));
      context.pushReplacement(Routes.citizenToken(token.id));
    } on ApiException catch (e) {
      if (!mounted) return;
      setState(() => _error = e.messageIn(l));
      ref.invalidate(_slotsProvider((shopId, ymd(_day)))); // the slot may have just filled up
    } finally {
      if (mounted) setState(() => _busy = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final l = AppLocalizations.of(context);
    return Scaffold(
      appBar: AppBar(title: Text(l.bookRation)),
      body: CitizenDataView(builder: (context, overview) {
        final shop = overview.shop;
        if (shop == null) return [Text(l.noShopAssigned, style: Theme.of(context).textTheme.titleMedium)];
        return [
          Text(shop.name, style: Theme.of(context).textTheme.titleMedium?.copyWith(fontWeight: FontWeight.w700)),
          Text([shop.address, shop.district].where((s) => s.isNotEmpty).join(', '),
              style: const TextStyle(color: AppColors.muted)),
          const SizedBox(height: 20),
          _Heading(l.stepDay),
          _DayPicker(
            now: _now,
            selected: _day,
            onChanged: (d) => setState(() {
              _day = d;
              _slotId = null;
              _error = null;
            }),
          ),
          const SizedBox(height: 20),
          _Heading(l.stepTime),
          _SlotPicker(
            slots: ref.watch(_slotsProvider((shop.id, ymd(_day)))),
            now: _now,
            selected: _slotId,
            onChanged: (id) => setState(() {
              _slotId = id;
              _error = null;
            }),
            onRetry: () => ref.invalidate(_slotsProvider((shop.id, ymd(_day)))),
          ),
          const SizedBox(height: 20),
          _Heading(l.stepItems),
          ...ref.watch(_itemsProvider(shop.id)).when(
                loading: () => [const Center(child: Padding(padding: EdgeInsets.all(16), child: CircularProgressIndicator()))],
                error: (e, _) => [
                  _InlineError(
                      message: e is ApiException ? e.messageIn(l) : l.errorGeneric,
                      onRetry: () => ref.invalidate(_itemsProvider(shop.id))),
                ],
                data: (items) {
                  _quantities ??= {for (final i in items) i.rationType: i.maxQuantity};
                  return [
                    for (final item in items)
                      _ItemStepper(
                        item: item,
                        quantity: _quantities![item.rationType] ?? 0,
                        onChanged: _busy ? null : (q) => setState(() => _quantities![item.rationType] = q),
                      ),
                  ];
                },
              ),
          const SizedBox(height: 16),
          if (_error != null) ...[
            _InlineError(message: _error!),
            const SizedBox(height: 12),
          ],
          FilledButton.icon(
            onPressed: _busy ? null : () => _book(shop.id),
            icon: _busy
                ? const SizedBox(width: 22, height: 22, child: CircularProgressIndicator(strokeWidth: 2.5, color: Colors.white))
                : const Icon(Icons.confirmation_number_outlined),
            label: Text(_busy ? l.bookingInProgress : l.bookAndGetToken),
          ),
          const SizedBox(height: 24),
        ];
      }),
    );
  }
}

class _Heading extends StatelessWidget {
  const _Heading(this.text);

  final String text;

  @override
  Widget build(BuildContext context) => Padding(
        padding: const EdgeInsets.only(bottom: 10),
        child: Text(text, style: Theme.of(context).textTheme.titleMedium?.copyWith(fontWeight: FontWeight.w700)),
      );
}

class _DayPicker extends StatelessWidget {
  const _DayPicker({required this.now, required this.selected, required this.onChanged});

  final DateTime now;
  final DateTime selected;
  final ValueChanged<DateTime> onChanged;

  @override
  Widget build(BuildContext context) {
    final today = DateTime(now.year, now.month, now.day);
    return SizedBox(
      height: 52,
      child: ListView.separated(
        scrollDirection: Axis.horizontal,
        itemCount: bookingDays,
        separatorBuilder: (_, _) => const SizedBox(width: 8),
        itemBuilder: (context, i) {
          final day = today.add(Duration(days: i));
          return ChoiceChip(
            label: Text(dayLabel(context, day, now: now), style: const TextStyle(fontSize: 16)),
            selected: day == selected,
            showCheckmark: false,
            padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 10),
            onSelected: (_) => onChanged(day),
          );
        },
      ),
    );
  }
}

class _SlotPicker extends StatelessWidget {
  const _SlotPicker({required this.slots, required this.now, required this.selected, required this.onChanged, required this.onRetry});

  final AsyncValue<List<Slot>> slots;
  final DateTime now;
  final int? selected;
  final ValueChanged<int> onChanged;
  final VoidCallback onRetry;

  @override
  Widget build(BuildContext context) {
    final l = AppLocalizations.of(context);
    return slots.when(
      loading: () => const Center(child: Padding(padding: EdgeInsets.all(16), child: CircularProgressIndicator())),
      error: (e, _) => _InlineError(message: e is ApiException ? e.messageIn(l) : l.errorGeneric, onRetry: onRetry),
      data: (all) {
        final open = all.where((s) => !s.hasStarted(now)).toList()..sort((a, b) => a.start.compareTo(b.start));
        if (open.isEmpty) return Text(l.noSlots, style: const TextStyle(fontSize: 16));
        return LayoutBuilder(builder: (context, constraints) {
          final width = (constraints.maxWidth - 16) / 3; // three per row
          return Wrap(spacing: 8, runSpacing: 8, children: [
            for (final s in open)
              SizedBox(
                width: width,
                child: _SlotButton(slot: s, selected: s.id == selected, onTap: s.isFull ? null : () => onChanged(s.id)),
              ),
          ]);
        });
      },
    );
  }
}

class _SlotButton extends StatelessWidget {
  const _SlotButton({required this.slot, required this.selected, required this.onTap});

  final Slot slot;
  final bool selected;
  final VoidCallback? onTap;

  @override
  Widget build(BuildContext context) {
    final l = AppLocalizations.of(context);
    final full = onTap == null;
    final fg = full ? AppColors.muted : (selected ? Colors.white : AppColors.ink);
    return Semantics(
      button: true,
      selected: selected,
      enabled: !full,
      child: Material(
        color: selected ? AppColors.blue : (full ? const Color(0xFFEDF2F7) : Colors.white),
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(12),
          side: BorderSide(color: selected ? AppColors.blue : AppColors.border),
        ),
        child: InkWell(
          borderRadius: BorderRadius.circular(12),
          onTap: onTap,
          child: Padding(
            padding: const EdgeInsets.symmetric(vertical: 10, horizontal: 4),
            child: Column(children: [
              Text(timeLabel(context, slot.start), style: TextStyle(color: fg, fontWeight: FontWeight.w700, fontSize: 16)),
              Text(full ? l.slotFull : l.placesLeft(slot.placesLeft),
                  style: TextStyle(color: selected ? Colors.white : (full ? AppColors.muted : AppColors.success), fontSize: 13)),
            ]),
          ),
        ),
      ),
    );
  }
}

class _ItemStepper extends StatelessWidget {
  const _ItemStepper({required this.item, required this.quantity, required this.onChanged});

  final BookableItem item;
  final double quantity;
  final ValueChanged<double>? onChanged;

  /// Oil and salt come in small amounts (0.5 L, 0.75 kg), so they move in quarters; grain in whole kilograms.
  double get _step => item.rationType == 'EdibleOil' || item.rationType == 'Salt' ? 0.25 : 1;

  @override
  Widget build(BuildContext context) {
    final l = AppLocalizations.of(context);
    final name = itemWord(l, item.rationType);
    final unit = unitWord(l, item.rationType);
    final max = item.maxQuantity;
    final change = onChanged;
    return Card(
      margin: const EdgeInsets.only(bottom: 10),
      child: Padding(
        padding: const EdgeInsets.fromLTRB(16, 12, 8, 12),
        child: Row(children: [
          Icon(itemIcon(item.rationType), color: AppColors.blue),
          const SizedBox(width: 12),
          Expanded(
            child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
              Text(name, style: const TextStyle(fontSize: 17, fontWeight: FontWeight.w700)),
              Text(max > 0 ? l.perVisitLimit(amount(max), unit) : l.notAvailableNow,
                  style: const TextStyle(color: AppColors.muted, fontSize: 14)),
            ]),
          ),
          IconButton.outlined(
            tooltip: l.decreaseItem(name),
            onPressed: change == null || quantity <= 0 ? null : () => change((quantity - _step).clamp(0, max)),
            icon: const Icon(Icons.remove),
          ),
          SizedBox(
            width: 64,
            child: Text('${amount(quantity)} $unit',
                textAlign: TextAlign.center, style: const TextStyle(fontSize: 16, fontWeight: FontWeight.w700)),
          ),
          IconButton.outlined(
            tooltip: l.increaseItem(name),
            onPressed: change == null || quantity >= max ? null : () => change((quantity + _step).clamp(0, max)),
            icon: const Icon(Icons.add),
          ),
        ]),
      ),
    );
  }
}

class _InlineError extends StatelessWidget {
  const _InlineError({required this.message, this.onRetry});

  final String message;
  final VoidCallback? onRetry;

  @override
  Widget build(BuildContext context) => Container(
        padding: const EdgeInsets.all(14),
        decoration: BoxDecoration(color: AppColors.dangerSoft, borderRadius: BorderRadius.circular(12)),
        child: Row(children: [
          const Icon(Icons.error_outline, color: AppColors.danger),
          const SizedBox(width: 10),
          Expanded(child: Text(message, style: const TextStyle(color: AppColors.danger, fontWeight: FontWeight.w600))),
          if (onRetry != null)
            TextButton(onPressed: onRetry, child: Text(AppLocalizations.of(context).tryAgain)),
        ]),
      );
}
