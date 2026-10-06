import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:intl/intl.dart';

import '../../app/routes.dart';
import '../../app/theme.dart';
import '../../core/network/api_exception.dart';
import '../../l10n/app_localizations.dart';
import '../booking/booking_data.dart';
import '../booking/booking_widgets.dart';
import '../citizen/citizen_widgets.dart';
import 'official_data.dart';
import 'official_words.dart';
import 'records_data.dart';
import 'shops_screen.dart' show StockLineRow;

// The officials' record screens: the same lists as the website's Bookings, Inventory, Reports, Audit and
// Users pages, read-only. Lists are filtered on the phone where the backend has no filter.

/// Loading, error (with "try again") and empty states shared by every list here.
List<Widget> _states<T>(BuildContext context, AsyncValue<List<T>> value, VoidCallback retry, String empty,
    List<Widget> Function(List<T>) build) {
  final l = AppLocalizations.of(context);
  return value.when(
    loading: () => [const SizedBox(height: 60), const Center(child: CircularProgressIndicator())],
    error: (e, _) => [
      Text(e is ApiException ? e.messageIn(l) : l.errorGeneric, textAlign: TextAlign.center),
      TextButton(onPressed: retry, child: Text(l.tryAgain)),
    ],
    data: (all) => all.isEmpty ? [Text(empty, style: Theme.of(context).textTheme.titleMedium)] : build(all),
  );
}

Widget _chips<T>(List<T?> options, T? selected, String Function(T?) label, void Function(T?) onSelected) =>
    Wrap(spacing: 8, runSpacing: 8, children: [
      for (final o in options) ChoiceChip(label: Text(label(o)), selected: selected == o, onSelected: (_) => onSelected(o)),
    ]);

// ---------------------------------------------------------------- bookings

class AllBookingsScreen extends ConsumerStatefulWidget {
  const AllBookingsScreen({super.key});

  @override
  ConsumerState<AllBookingsScreen> createState() => _AllBookingsScreenState();
}

class _AllBookingsScreenState extends ConsumerState<AllBookingsScreen> {
  TokenState? _only;
  String _query = '';

  @override
  Widget build(BuildContext context) {
    final l = AppLocalizations.of(context);
    final bookings = ref.watch(allBookingsProvider);
    final today = DateTime.now();
    final shown = [
      for (final b in bookings.value ?? const <BookingRecord>[])
        if ((_only == null || b.token.stateOn(today) == _only) && b.matches(_query)) b,
    ];
    final header = <Widget>[
      TextField(
        decoration: InputDecoration(prefixIcon: const Icon(Icons.search), labelText: l.bookingsSearchHint),
        onChanged: (v) => setState(() => _query = v),
      ),
      const SizedBox(height: 12),
      _chips<TokenState>([null, ...TokenState.values], _only, (s) => s == null ? l.filterAll : tokenStateWord(l, s),
          (s) => setState(() => _only = s)),
      const SizedBox(height: 12),
      if (bookings.hasValue) ...[
        Semantics(liveRegion: true, child: Text(l.bookingsCount(shown.length), style: const TextStyle(fontWeight: FontWeight.w700))),
        const SizedBox(height: 8),
      ],
    ];
    // Every booking ever made can be thousands of rows: build only the visible cards.
    final body = bookings.hasValue && shown.isNotEmpty
        ? null
        : _states(context, bookings, () => ref.invalidate(allBookingsProvider), l.noBookingsHere, (_) => [Text(l.noBookingsHere)]);
    return Scaffold(
      appBar: AppBar(title: Text(l.allBookingsTitle)),
      body: RefreshIndicator(
        onRefresh: () => ref.refresh(allBookingsProvider.future),
        child: ListView.builder(
          padding: const EdgeInsets.all(16),
          itemCount: header.length + (body?.length ?? shown.length),
          itemBuilder: (context, i) {
            if (i < header.length) return header[i];
            final at = i - header.length;
            return body != null ? body[at] : _BookingCard(record: shown[at], today: today);
          },
        ),
      ),
    );
  }
}

class _BookingCard extends StatelessWidget {
  const _BookingCard({required this.record, required this.today});

  final BookingRecord record;
  final DateTime today;

  @override
  Widget build(BuildContext context) {
    final l = AppLocalizations.of(context);
    final t = record.token;
    final state = t.stateOn(today);
    final locale = Localizations.localeOf(context).toLanguageTag();
    return Card(
      margin: const EdgeInsets.only(bottom: 10),
      child: Padding(
        padding: const EdgeInsets.all(14),
        child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
          Text(t.number, style: const TextStyle(fontSize: 16, fontWeight: FontWeight.w700)),
          const SizedBox(height: 4),
          StatusPill(text: tokenStateWord(l, state), tone: tokenStateTone(state)),
          const SizedBox(height: 6),
          if (record.customerName.isNotEmpty) Text(record.customerName, style: const TextStyle(fontSize: 15, fontWeight: FontWeight.w600)),
          if (t.shopName.isNotEmpty) Text(t.shopName, style: const TextStyle(color: AppColors.blue)),
          Text('${DateFormat.yMMMd(locale).format(t.date)} · ${t.start}–${t.end}', style: const TextStyle(color: AppColors.muted)),
        ]),
      ),
    );
  }
}

// ---------------------------------------------------------------- stock in every shop

class StockOverviewScreen extends ConsumerStatefulWidget {
  const StockOverviewScreen({super.key});

  @override
  ConsumerState<StockOverviewScreen> createState() => _StockOverviewScreenState();
}

class _StockOverviewScreenState extends ConsumerState<StockOverviewScreen> {
  bool _lowOnly = false;

  @override
  Widget build(BuildContext context) {
    final l = AppLocalizations.of(context);
    final stock = ref.watch(allStockProvider);
    // Shop names come from the shops list; a shop missing there still shows, by number.
    final names = {for (final s in ref.watch(shopsProvider).value ?? const <ShopSummary>[]) s.id: s.name};

    Future<void> refresh() {
      ref.invalidate(shopsProvider);
      return ref.refresh(allStockProvider.future);
    }

    return Scaffold(
      appBar: AppBar(title: Text(l.stockAllShopsTitle)),
      body: RefreshIndicator(
        onRefresh: refresh,
        child: ListView(
          padding: const EdgeInsets.all(16),
          children: [
            _chips<bool>([false, true], _lowOnly, (low) => low == true ? l.lowStockOnly : l.filterAll,
                (low) => setState(() => _lowOnly = low ?? false)),
            const SizedBox(height: 12),
            ..._states(context, stock, () => ref.invalidate(allStockProvider), l.noStockLines, (all) {
              final byShop = <int, List<ShopStockLine>>{};
              for (final s in all) {
                (byShop[s.shopId] ??= []).add(s);
              }
              bool hasLow(int shop) => byShop[shop]!.any((s) => s.line.low);
              // Shops with something low first, then by name.
              final shops = byShop.keys.where((id) => !_lowOnly || hasLow(id)).toList()
                ..sort((a, b) {
                  final low = (hasLow(a) ? 0 : 1).compareTo(hasLow(b) ? 0 : 1);
                  return low != 0 ? low : (names[a] ?? '').compareTo(names[b] ?? '');
                });
              if (shops.isEmpty) return [Text(l.noLowStock, style: Theme.of(context).textTheme.titleMedium)];
              return [
                for (final id in shops)
                  Padding(
                    padding: const EdgeInsets.only(bottom: 12),
                    child: Card(
                      child: Padding(
                        padding: const EdgeInsets.fromLTRB(16, 4, 16, 12),
                        child: Column(crossAxisAlignment: CrossAxisAlignment.stretch, children: [
                          ListTile(
                            contentPadding: EdgeInsets.zero,
                            leading: const Icon(Icons.storefront, color: AppColors.blue),
                            title: Text(names[id] ?? l.shopLinked(id), style: const TextStyle(fontWeight: FontWeight.w700)),
                            trailing: const Icon(Icons.chevron_right),
                            onTap: () => context.push(Routes.officialShop(id)),
                          ),
                          for (final s in byShop[id]!.where((s) => !_lowOnly || s.line.low).toList()
                            ..sort((a, b) => (a.line.low ? 0 : 1).compareTo(b.line.low ? 0 : 1)))
                            StockLineRow(line: s.line),
                        ]),
                      ),
                    ),
                  ),
              ];
            }),
          ],
        ),
      ),
    );
  }
}

// ---------------------------------------------------------------- reports

/// The four report names the backend sends, in the user's language (others show as sent).
String reportWord(AppLocalizations l, String name) => switch (name) {
      'Daily Collection Report' => l.reportCollections,
      'Token Generation Report' => l.reportTokens,
      'QR Verification Report' => l.reportCounterChecks,
      'Cancelled Bookings Report' => l.reportCancelled,
      _ => name,
    };

class ReportsScreen extends ConsumerStatefulWidget {
  const ReportsScreen({super.key});

  @override
  ConsumerState<ReportsScreen> createState() => _ReportsScreenState();
}

class _ReportsScreenState extends ConsumerState<ReportsScreen> {
  // As on the website: the last 30 days, today included.
  late DayRange _range = () {
    final now = DateTime.now();
    final today = DateTime(now.year, now.month, now.day);
    return (from: today.subtract(const Duration(days: 29)), to: today);
  }();

  Future<void> _pickDates() async {
    final now = DateTime.now();
    final picked = await showDateRangePicker(
      context: context,
      firstDate: DateTime(2020),
      lastDate: DateTime(now.year, now.month, now.day),
      initialDateRange: DateTimeRange(start: _range.from, end: _range.to),
    );
    if (picked != null) setState(() => _range = (from: picked.start, to: picked.end));
  }

  @override
  Widget build(BuildContext context) {
    final l = AppLocalizations.of(context);
    final reports = ref.watch(reportsProvider(_range));
    final format = DateFormat.yMMMd(Localizations.localeOf(context).toLanguageTag());
    return Scaffold(
      appBar: AppBar(title: Text(l.reportsTitle)),
      body: RefreshIndicator(
        onRefresh: () => ref.refresh(reportsProvider(_range).future),
        child: ListView(
          padding: const EdgeInsets.all(16),
          children: [
            Text('${format.format(_range.from)} – ${format.format(_range.to)}',
                style: const TextStyle(fontSize: 17, fontWeight: FontWeight.w700)),
            const SizedBox(height: 8),
            OutlinedButton.icon(icon: const Icon(Icons.date_range), label: Text(l.reportsChangeDates), onPressed: _pickDates),
            const SizedBox(height: 12),
            ..._states(context, reports, () => ref.invalidate(reportsProvider(_range)), l.noEntriesHere, (all) => [
                  for (final r in all)
                    Card(
                      margin: const EdgeInsets.only(bottom: 10),
                      child: MergeSemantics(
                        child: ListTile(
                          leading: const Icon(Icons.description_outlined, color: AppColors.blue, size: 28),
                          title: Text(reportWord(l, r.name), style: const TextStyle(fontWeight: FontWeight.w700)),
                          subtitle: Text(l.reportsInPeriod),
                          trailing: Text('${r.count}', style: const TextStyle(fontSize: 22, fontWeight: FontWeight.w800, color: AppColors.ink)),
                        ),
                      ),
                    ),
                  if (all.every((r) => !r.downloadable)) Text(l.reportsNoDownload, style: const TextStyle(color: AppColors.muted)),
                ]),
          ],
        ),
      ),
    );
  }
}

// ---------------------------------------------------------------- verification record

String auditOutcomeWord(AppLocalizations l, AuditOutcome? o) => switch (o) {
      AuditOutcome.success => l.auditSuccess,
      AuditOutcome.blocked => l.auditBlocked,
      AuditOutcome.failed => l.auditFailed,
      null => '—',
    };

PillTone auditOutcomeTone(AuditOutcome? o) => switch (o) {
      AuditOutcome.success => PillTone.good,
      AuditOutcome.blocked => PillTone.bad,
      AuditOutcome.failed => PillTone.warn,
      null => PillTone.neutral,
    };

String auditActionWord(AppLocalizations l, String action) => switch (action) {
      'QrScanned' => l.auditQrScanned,
      'BeneficiaryVerified' => l.auditBeneficiaryVerified,
      'AadhaarStatusChecked' => l.auditAadhaarChecked,
      'PassbookStatusChecked' => l.auditPassbookChecked,
      'OtpRequested' => l.auditOtpRequested,
      'OtpVerified' => l.auditOtpVerified,
      'OtpFailed' => l.auditOtpFailed,
      'CollectionConfirmed' => l.auditCollectionConfirmed,
      'CollectionRejected' => l.auditCollectionRejected,
      'TokenAlreadyUsed' => l.auditTokenUsed,
      _ => action,
    };

class AuditScreen extends ConsumerStatefulWidget {
  const AuditScreen({super.key});

  @override
  ConsumerState<AuditScreen> createState() => _AuditScreenState();
}

class _AuditScreenState extends ConsumerState<AuditScreen> {
  AuditOutcome? _only;

  @override
  Widget build(BuildContext context) {
    final l = AppLocalizations.of(context);
    final entries = ref.watch(auditProvider(_only));
    final english = Localizations.localeOf(context).languageCode == 'en';
    return Scaffold(
      appBar: AppBar(title: Text(l.auditTitle)),
      body: RefreshIndicator(
        onRefresh: () => ref.refresh(auditProvider(_only).future),
        child: ListView(
          padding: const EdgeInsets.all(16),
          children: [
            _chips<AuditOutcome>([null, ...AuditOutcome.values], _only, (o) => o == null ? l.filterAll : auditOutcomeWord(l, o),
                (o) => setState(() => _only = o)),
            const SizedBox(height: 12),
            ..._states(context, entries, () => ref.invalidate(auditProvider(_only)), l.noEntriesHere, (all) => [
                  for (final e in all)
                    Card(
                      margin: const EdgeInsets.only(bottom: 10),
                      child: Padding(
                        padding: const EdgeInsets.all(14),
                        child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                          Text(auditActionWord(l, e.action), style: const TextStyle(fontSize: 16, fontWeight: FontWeight.w700)),
                          const SizedBox(height: 4),
                          StatusPill(text: auditOutcomeWord(l, e.outcome), tone: auditOutcomeTone(e.outcome)),
                          const SizedBox(height: 6),
                          if (e.method.isNotEmpty) InfoRow(label: l.auditMethod, value: valueText(e.method)),
                          if (e.tokenNumber.isNotEmpty) InfoRow(label: l.tokenNumber, value: valueText(e.tokenNumber)),
                          if (e.beneficiaryId != null) InfoRow(label: l.auditBeneficiary, value: valueText('${e.beneficiaryId}')),
                          if (e.at != null) Text(localMoment(context, e.at!), style: const TextStyle(color: AppColors.muted)),
                          if (e.reason.isNotEmpty) ...[
                            const SizedBox(height: 6),
                            if (!english) Text(l.alertDetailsInEnglish, style: const TextStyle(color: AppColors.muted, fontSize: 13)),
                            Text(e.reason),
                          ],
                        ]),
                      ),
                    ),
                ]),
          ],
        ),
      ),
    );
  }
}

// ---------------------------------------------------------------- people and staff

String accountRoleWord(AppLocalizations l, AccountRole? r) => switch (r) {
      AccountRole.ruralUser => l.roleRuralUser,
      AccountRole.shopOwner => l.roleShopOwner,
      AccountRole.official => l.roleOfficial,
      AccountRole.admin => l.roleAdmin,
      null => '—',
    };

class UsersScreen extends ConsumerStatefulWidget {
  const UsersScreen({super.key});

  @override
  ConsumerState<UsersScreen> createState() => _UsersScreenState();
}

class _UsersScreenState extends ConsumerState<UsersScreen> {
  AccountRole? _only;
  String _query = '';

  @override
  Widget build(BuildContext context) {
    final l = AppLocalizations.of(context);
    final accounts = ref.watch(accountsProvider(_only));
    final q = _query.trim().toLowerCase();
    return Scaffold(
      appBar: AppBar(title: Text(l.usersTitle)),
      body: RefreshIndicator(
        onRefresh: () => ref.refresh(accountsProvider(_only).future),
        child: ListView(
          padding: const EdgeInsets.all(16),
          children: [
            Text(l.usersContactHidden, style: const TextStyle(color: AppColors.muted)),
            const SizedBox(height: 12),
            TextField(
              decoration: InputDecoration(prefixIcon: const Icon(Icons.search), labelText: l.usersSearchHint),
              onChanged: (v) => setState(() => _query = v),
            ),
            const SizedBox(height: 12),
            _chips<AccountRole>([null, ...AccountRole.values], _only, (r) => r == null ? l.filterAll : accountRoleWord(l, r),
                (r) => setState(() => _only = r)),
            const SizedBox(height: 12),
            ..._states(context, accounts, () => ref.invalidate(accountsProvider(_only)), l.noUsersHere, (all) {
              final shown = [for (final a in all) if (q.isEmpty || a.name.toLowerCase().contains(q)) a];
              if (shown.isEmpty) return [Text(l.noUsersHere, style: Theme.of(context).textTheme.titleMedium)];
              return [
                for (final a in shown)
                  Card(
                    margin: const EdgeInsets.only(bottom: 10),
                    child: Padding(
                      padding: const EdgeInsets.all(14),
                      child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                        Text(a.name, style: const TextStyle(fontSize: 16, fontWeight: FontWeight.w700)),
                        Text(accountRoleWord(l, a.role), style: const TextStyle(color: AppColors.blue, fontWeight: FontWeight.w600)),
                        if (a.mobile.isNotEmpty) Text(a.maskedMobile, style: const TextStyle(color: AppColors.muted)),
                        if (a.email.isNotEmpty) Text(a.maskedEmail, style: const TextStyle(color: AppColors.muted)),
                      ]),
                    ),
                  ),
              ];
            }),
          ],
        ),
      ),
    );
  }
}
