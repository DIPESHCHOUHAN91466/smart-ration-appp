import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../core/network/api_client.dart';
import '../../core/network/api_exception.dart';
import '../../core/providers.dart';
import '../booking/booking_data.dart';
import '../shop/shop_data.dart';

/// The officials' record screens, on existing read-only backend routes (officials and admins only):
///   GET /api/ration/bookings        every booking at every shop, newest first (no paging on the backend)
///   GET /api/inventory              every shop's stock lines
///   GET /api/admin/reports          four record counts for a date range (fromDate/toDate, yyyy-MM-dd)
///   GET /api/audit/verification     QR / OTP / collection checks at the counters, newest first (status filter)
///   GET /api/admin/users            accounts, optionally one role

/// One booking as officials see it: the token plus whose it is.
class BookingRecord {
  const BookingRecord({required this.token, required this.customerName});

  final RationToken token;
  final String customerName;

  static BookingRecord? tryParse(Object? j) {
    final token = RationToken.tryParse(j);
    if (token == null || j is! Map) return null;
    return BookingRecord(token: token, customerName: _text(j['userName']));
  }

  bool matches(String query) {
    final q = query.trim().toLowerCase();
    return q.isEmpty ||
        token.number.toLowerCase().contains(q) ||
        customerName.toLowerCase().contains(q) ||
        token.shopName.toLowerCase().contains(q);
  }
}

/// A stock line and the shop it belongs to.
class ShopStockLine {
  const ShopStockLine({required this.shopId, required this.line});

  final int shopId;
  final StockLine line;

  static ShopStockLine? tryParse(Object? j) {
    final line = StockLine.tryParse(j);
    if (line == null || j is! Map || j['rationShopId'] is! int) return null;
    return ShopStockLine(shopId: j['rationShopId'] as int, line: line);
  }
}

class ReportCount {
  const ReportCount({required this.name, required this.description, required this.count, required this.downloadable});

  /// The backend's English name, e.g. "Daily Collection Report" (translated where known).
  final String name;
  final String description;
  final int count;
  final bool downloadable;

  static ReportCount? tryParse(Object? j) {
    if (j is! Map || j['reportName'] is! String) return null;
    return ReportCount(
      name: j['reportName'] as String,
      description: _text(j['description']),
      count: j['recordCount'] is int ? j['recordCount'] as int : 0,
      downloadable: j['exportAvailable'] == true,
    );
  }
}

/// What happened at a counter check, as the backend records it.
enum AuditOutcome {
  success('SUCCESS'),
  blocked('BLOCKED'),
  failed('FAILED');

  const AuditOutcome(this.wire);

  final String wire;
}

class AuditEntry {
  const AuditEntry({
    required this.id,
    required this.action,
    required this.method,
    required this.outcome,
    required this.tokenNumber,
    required this.beneficiaryId,
    required this.reason,
    required this.at,
  });

  final int id;

  /// e.g. QrScanned, OtpFailed, CollectionConfirmed (translated where known).
  final String action;

  /// QR or OTP.
  final String method;

  /// Null when the backend sends a status this app does not know.
  final AuditOutcome? outcome;
  final String tokenNumber;
  final int? beneficiaryId;

  /// The backend's English reason, e.g. OTP_INVALID.
  final String reason;

  /// UTC.
  final DateTime? at;

  static AuditEntry? tryParse(Object? j) {
    if (j is! Map || j['id'] is! int) return null;
    final at = j['timestamp'];
    return AuditEntry(
      id: j['id'] as int,
      action: _text(j['action']),
      method: _text(j['verificationMethod']),
      outcome: AuditOutcome.values.where((o) => o.wire == j['status']).firstOrNull,
      tokenNumber: _text(j['tokenNumber']),
      beneficiaryId: j['beneficiaryId'] is int ? j['beneficiaryId'] as int : null,
      reason: _text(j['reason']),
      // "2026-10-01 10:11:05", stored in UTC.
      at: at is String ? DateTime.tryParse('${at.replaceFirst(' ', 'T')}Z') : null,
    );
  }
}

/// The backend's role names, for the users filter.
enum AccountRole {
  ruralUser('RuralUser'),
  shopOwner('ShopOwner'),
  official('GovernmentOfficial'),
  admin('Admin');

  const AccountRole(this.wire);

  final String wire;
}

class Account {
  const Account({required this.id, required this.name, required this.role, required this.email, required this.mobile});

  final int id;
  final String name;
  final AccountRole? role;

  /// Kept whole in memory; screens show [maskedEmail] / [maskedMobile] only.
  final String email;
  final String mobile;

  static Account? tryParse(Object? j) {
    if (j is! Map || j['id'] is! int) return null;
    return Account(
      id: j['id'] as int,
      name: _text(j['fullName']),
      role: AccountRole.values.where((r) => r.wire == j['role']).firstOrNull,
      email: _text(j['email']),
      mobile: _text(j['mobileNumber']),
    );
  }

  /// "••••••3210": enough to tell two people apart, not enough to call or message them.
  String get maskedMobile => maskTail(mobile);

  /// "a•••@example.com"
  String get maskedEmail {
    final at = email.indexOf('@');
    if (at < 1) return maskTail(email);
    return '${email[0]}•••${email.substring(at)}';
  }
}

/// Everything but the last four characters replaced by dots.
String maskTail(String value) {
  final v = value.trim();
  if (v.length <= 4) return v.isEmpty ? '' : '••••';
  return '${'•' * (v.length - 4)}${v.substring(v.length - 4)}';
}

/// The report period: whole days, both ends included.
typedef DayRange = ({DateTime from, DateTime to});

class RecordsRepository {
  const RecordsRepository(this._api);

  final ApiClient _api;

  Future<List<BookingRecord>> bookings() async => _list(await _api.get<Object?>('/api/ration/bookings'), BookingRecord.tryParse);

  Future<List<ShopStockLine>> stock() async => _list(await _api.get<Object?>('/api/inventory'), ShopStockLine.tryParse);

  Future<List<ReportCount>> reports(DayRange range) async => _list(
      await _api.get<Object?>('/api/admin/reports', query: {'fromDate': ymd(range.from), 'toDate': ymd(range.to)}),
      ReportCount.tryParse);

  Future<List<AuditEntry>> audit({AuditOutcome? outcome}) async =>
      _list(await _api.get<Object?>('/api/audit/verification', query: {'status': ?outcome?.wire}), AuditEntry.tryParse);

  Future<List<Account>> accounts({AccountRole? role}) async =>
      _list(await _api.get<Object?>('/api/admin/users', query: {'role': ?role?.wire}), Account.tryParse);
}

final recordsRepositoryProvider = Provider<RecordsRepository>((ref) => RecordsRepository(ref.watch(apiClientProvider)));

final allBookingsProvider = FutureProvider.autoDispose<List<BookingRecord>>((ref) => ref.watch(recordsRepositoryProvider).bookings());

final allStockProvider = FutureProvider.autoDispose<List<ShopStockLine>>((ref) => ref.watch(recordsRepositoryProvider).stock());

final reportsProvider =
    FutureProvider.autoDispose.family<List<ReportCount>, DayRange>((ref, range) => ref.watch(recordsRepositoryProvider).reports(range));

final auditProvider =
    FutureProvider.autoDispose.family<List<AuditEntry>, AuditOutcome?>((ref, o) => ref.watch(recordsRepositoryProvider).audit(outcome: o));

final accountsProvider =
    FutureProvider.autoDispose.family<List<Account>, AccountRole?>((ref, r) => ref.watch(recordsRepositoryProvider).accounts(role: r));

List<T> _list<T>(Object? data, T? Function(Object?) parse) =>
    data is List ? [for (final e in data) ?parse(e)] : (throw const ApiException(ApiErrorKind.unknown));

String _text(Object? value) => value is String ? value : '';
