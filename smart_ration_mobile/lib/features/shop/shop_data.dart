import 'dart:math';

import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../core/network/api_client.dart';
import '../../core/network/api_exception.dart';
import '../../core/providers.dart';
import '../booking/booking_data.dart';

/// The shop counter, on the existing backend routes (all of them check that the caller owns this shop):
///   GET  /api/shop/dashboard                 today's counts at my shop
///   POST /api/qr/scan                        a scanned or typed QR -> a status, plus the customer check
///   POST /api/verification/otp/request       no QR: send a code to the customer's registered mobile
///   POST /api/verification/otp/verify        the code -> the customer check
///   GET  /api/tokens/{id}                    the items on the token (what to hand over)
///   POST /api/ration/collection/confirm      hand over: the backend re-checks everything, then reduces
///                                            stock, completes the token and writes the receipt in one go

class ShopDashboard {
  const ShopDashboard(
      {required this.shopName, required this.total, required this.collected, required this.waiting, required this.cancelled, this.lowStock = 0});

  final String shopName;
  final int total;
  final int collected;
  final int waiting;
  final int cancelled;

  /// How many items are at or below their minimum stock level.
  final int lowStock;

  static ShopDashboard parse(Object? j) {
    if (j is! Map) throw const ApiException(ApiErrorKind.unknown);
    return ShopDashboard(
      shopName: _text(j['shopName']),
      total: _int(j['todayTotalTokens']),
      collected: _int(j['todayCompleted']),
      waiting: _int(j['todayPending']),
      cancelled: _int(j['todayCancelled']),
      lowStock: (j['inventory'] as List? ?? const []).whereType<Map>().where((i) => i['isLowStock'] == true).length,
    );
  }
}

/// How the customer was identified: their token's QR (scanned or typed) or a code sent to their mobile.
enum CheckMethod { qr, otp }

class CheckedMember {
  const CheckedMember({required this.name, required this.relationship, required this.eligible});

  final String name;
  final String relationship;
  final bool eligible;
}

/// The backend's verdict on one customer and their booking. Only the backend decides [ready]; the
/// app just shows it. Personal details are limited to what the counter needs (no Aadhaar number).
class CustomerCheck {
  const CustomerCheck({
    required this.method,
    required this.name,
    required this.beneficiaryCode,
    required this.mobileMasked,
    required this.familyCode,
    required this.familySize,
    required this.eligibleMembers,
    required this.members,
    required this.schemeName,
    required this.tokenId,
    required this.tokenNumber,
    required this.collectionDate,
    required this.bookingTime,
    required this.aadhaarVerified,
    required this.passbookVerified,
    required this.mobileVerified,
    required this.tokenValid,
    required this.familyEligible,
    required this.entitlementLeft,
    required this.ready,
    required this.blockedReason,
  });

  final CheckMethod method;
  final String name;
  final String beneficiaryCode;
  final String mobileMasked;
  final String familyCode;
  final int familySize;
  final int eligibleMembers;
  final List<CheckedMember> members;
  final String schemeName;
  final int tokenId;
  final String tokenNumber;
  final DateTime? collectionDate;

  /// "10:05"
  final String bookingTime;
  final bool aadhaarVerified;
  final bool passbookVerified;
  final bool mobileVerified;
  final bool tokenValid;
  final bool familyEligible;
  final bool entitlementLeft;

  /// True only when the backend says READY_FOR_RATION_COLLECTION.
  final bool ready;

  /// The backend's reason when not ready (English; see blockedReasonIn for the translation).
  final String? blockedReason;

  static CustomerCheck? tryParse(Object? j, CheckMethod method) {
    if (j is! Map) return null;
    final who = _map(j['beneficiary']);
    final family = _map(j['family']);
    final booking = _map(j['booking']);
    final summary = _map(j['verificationSummary']);
    final entitlement = _map(j['entitlement']);
    if (booking['tokenId'] is! int) return null;
    final reason = summary['blockedReason'];
    return CustomerCheck(
      method: method,
      name: _text(who['fullName']),
      beneficiaryCode: _text(who['beneficiaryCode']),
      mobileMasked: _text(who['mobileMasked']),
      familyCode: _text(family['familyCode']),
      familySize: _int(family['familySize']),
      eligibleMembers: _int(family['eligibleMemberCount']),
      members: [
        for (final m in (family['members'] as List? ?? const []).whereType<Map>())
          CheckedMember(name: _text(m['fullName']), relationship: _text(m['relationship']), eligible: m['eligibility'] == 'Eligible'),
      ],
      schemeName: _text(entitlement['schemeName']),
      tokenId: booking['tokenId'] as int,
      tokenNumber: _text(booking['tokenNumber']),
      collectionDate: DateTime.tryParse(_text(booking['collectionDate'])),
      bookingTime: _text(booking['bookingTime']),
      aadhaarVerified: summary['aadhaarVerified'] == true,
      passbookVerified: summary['passbookVerified'] == true,
      mobileVerified: summary['mobileVerified'] == true,
      tokenValid: summary['tokenValid'] == true,
      familyEligible: summary['familyEligible'] == true,
      entitlementLeft: summary['entitlementAvailable'] == true,
      ready: summary['overallStatus'] == 'READY_FOR_RATION_COLLECTION',
      blockedReason: reason is String && reason.isNotEmpty ? reason : null,
    );
  }
}

/// The answer to a scan. [status] is one of the backend's stable codes (VERIFIED, INVALID_SIGNATURE,
/// WRONG_SHOP, ALREADY_COLLECTED, ...). [check] is there whenever the QR matched a booking at this shop,
/// even if that booking can't be collected (so the shopkeeper sees why).
class ScanOutcome {
  const ScanOutcome({required this.status, required this.message, this.check});

  final String status;
  final String message;
  final CustomerCheck? check;

  static ScanOutcome parse(Object? j) {
    if (j is! Map) throw const ApiException(ApiErrorKind.unknown);
    return ScanOutcome(
      status: _text(j['status']),
      message: _text(j['message']),
      check: CustomerCheck.tryParse(j['verification'], CheckMethod.qr),
    );
  }
}

class OtpRequest {
  const OtpRequest({required this.id, required this.mobileMasked, required this.expiresInMinutes, this.demoCode});

  final int id;
  final String mobileMasked;
  final int expiresInMinutes;

  /// Only sent by a development server in demo mode; always null in production.
  final String? demoCode;

  static OtpRequest parse(Object? j) {
    if (j is! Map || j['otpVerificationId'] is! int) throw const ApiException(ApiErrorKind.unknown);
    final demo = j['demoOtpValue'];
    return OtpRequest(
      id: j['otpVerificationId'] as int,
      mobileMasked: _text(j['mobileMasked']),
      expiresInMinutes: _int(j['expiresInMinutes']),
      demoCode: demo is String && demo.isNotEmpty ? demo : null,
    );
  }
}

/// Proof of a completed handover, as the backend wrote it.
class Receipt {
  const Receipt({
    required this.collectionCode,
    required this.tokenNumber,
    required this.customerName,
    required this.familySize,
    required this.items,
    required this.totalKg,
    required this.shopName,
    required this.collectedAt,
  });

  /// e.g. COL-DEMO-000042
  final String collectionCode;
  final String tokenNumber;
  final String customerName;
  final int familySize;
  final List<(String rationType, double quantity)> items;
  final double totalKg;
  final String shopName;

  /// "2026-10-01 10:07" (the backend's clock, UTC).
  final String collectedAt;

  static Receipt parse(Object? j) {
    if (j is! Map || j['collectionCode'] is! String) throw const ApiException(ApiErrorKind.unknown);
    return Receipt(
      collectionCode: j['collectionCode'] as String,
      tokenNumber: _text(j['tokenNumber']),
      customerName: _text(j['beneficiaryName']),
      familySize: _int(j['familySize']),
      items: [
        for (final i in (j['issuedItems'] as List? ?? const []).whereType<Map>()) (_text(i['rationType']), _num(i['quantity'])),
      ],
      totalKg: _num(j['totalQuantityKg']),
      shopName: _text(j['shopName']),
      collectedAt: _text(j['collectedAt']),
    );
  }
}

/// One token in today's queue, with the customer's name so the shopkeeper can call them.
class QueueEntry {
  const QueueEntry({required this.token, required this.customerName});

  final RationToken token;
  final String customerName;

  /// Still to be served (booked and not yet collected or cancelled).
  bool get waiting => token.backendStatus == 'Confirmed' || token.backendStatus == 'Pending';

  static QueueEntry? tryParse(Object? j) {
    final token = RationToken.tryParse(j);
    if (token == null || j is! Map) return null;
    return QueueEntry(token: token, customerName: _text(j['userName']));
  }
}

/// One item's stock at the shop.
class StockLine {
  const StockLine({required this.id, required this.rationType, required this.available, required this.handedOut, required this.minimum, required this.low});

  final int id;
  final String rationType;
  final double available;

  /// Given out to customers so far (the backend's AllocatedQuantity).
  final double handedOut;
  final double minimum;

  /// At or below the minimum level (decided by the backend).
  final bool low;

  static StockLine? tryParse(Object? j) {
    if (j is! Map || j['id'] is! int || j['rationType'] is! String) return null;
    return StockLine(
      id: j['id'] as int,
      rationType: j['rationType'] as String,
      available: _num(j['availableQuantity']),
      handedOut: _num(j['allocatedQuantity']),
      minimum: _num(j['minimumStockLevel']),
      low: j['isLowStock'] == true,
    );
  }
}

/// The optional delivery-note or report number: what the backend accepts (letters, numbers, - / _ . and spaces, 64 max).
final stockReferencePattern = RegExp(r'^[A-Za-z0-9\-/_. ]{0,64}$');

class ShopRepository {
  const ShopRepository(this._api);

  final ApiClient _api;

  Future<ShopDashboard> dashboard() async => ShopDashboard.parse(await _api.get<Object?>('/api/shop/dashboard'));

  /// Today's tokens at my shop, earliest time first.
  Future<List<QueueEntry>> queue() async => _list(await _api.get<Object?>('/api/shop/queue'), QueueEntry.tryParse);

  /// My shop's stock lines (the backend limits a shop owner to their own shop).
  Future<List<StockLine>> stock() async => _list(await _api.get<Object?>('/api/inventory'), StockLine.tryParse);

  /// A delivery arrived: adds [quantity] and records it in the stock ledger.
  Future<StockLine> receive(int id, double quantity, {String? reference, String? note}) =>
      _movement('/api/inventory/$id/receive', quantity, reference, note);

  /// Damaged or spoiled stock: removes [quantity] (never more than is in stock) and records it.
  Future<StockLine> writeOff(int id, double quantity, {String? reference, String? note}) =>
      _movement('/api/inventory/$id/damage', quantity, reference, note);

  Future<StockLine> _movement(String path, double quantity, String? reference, String? note) async {
    final data = await _api.post<Object?>(path, body: {
      'quantity': quantity,
      if (reference != null && reference.trim().isNotEmpty) 'reference': reference.trim(),
      if (note != null && note.trim().isNotEmpty) 'note': note.trim(),
    });
    return StockLine.tryParse(data) ?? (throw const ApiException(ApiErrorKind.unknown));
  }

  /// [text] is what the camera read, or the SRQR-… code typed by hand. The backend checks the signature.
  Future<ScanOutcome> scan(String text) async => ScanOutcome.parse(await _api.post<Object?>('/api/qr/scan', body: {'qrData': text.trim()}));

  Future<OtpRequest> requestOtp(String mobile) async =>
      OtpRequest.parse(await _api.post<Object?>('/api/verification/otp/request', body: {'mobileNumber': mobile}));

  Future<CustomerCheck> verifyOtp(int otpId, String code) async {
    final data = await _api.post<Object?>('/api/verification/otp/verify', body: {'otpVerificationId': otpId, 'code': code});
    return CustomerCheck.tryParse(data, CheckMethod.otp) ?? (throw const ApiException(ApiErrorKind.unknown));
  }

  Future<RationToken> token(int id) async =>
      RationToken.tryParse(await _api.get<Object?>('/api/tokens/$id')) ?? (throw const ApiException(ApiErrorKind.unknown));

  /// [requestKey] must stay the same if the shopkeeper retries the same handover: the backend then
  /// returns the first receipt instead of handing out the ration twice.
  Future<Receipt> confirm(CustomerCheck check, String requestKey) async => Receipt.parse(await _api.post<Object?>(
        '/api/ration/collection/confirm',
        body: {'tokenId': check.tokenId, 'verificationMethod': check.method == CheckMethod.otp ? 'OTP' : 'QR'},
        headers: {'Idempotency-Key': requestKey},
      ));
}

/// A random 32-character key for one handover (see [ShopRepository.confirm]).
String newRequestKey([Random? random]) {
  final r = random ?? Random.secure();
  return List.generate(32, (_) => r.nextInt(16).toRadixString(16)).join();
}

final shopRepositoryProvider = Provider<ShopRepository>((ref) => ShopRepository(ref.watch(apiClientProvider)));

final shopDashboardProvider = FutureProvider.autoDispose<ShopDashboard>((ref) => ref.watch(shopRepositoryProvider).dashboard());

final shopQueueProvider = FutureProvider.autoDispose<List<QueueEntry>>((ref) => ref.watch(shopRepositoryProvider).queue());

final shopStockProvider = FutureProvider.autoDispose<List<StockLine>>((ref) => ref.watch(shopRepositoryProvider).stock());

/// The items on a token, as the shop sees it.
final shopTokenProvider = FutureProvider.autoDispose.family<RationToken, int>((ref, id) => ref.watch(shopRepositoryProvider).token(id));

List<T> _list<T>(Object? data, T? Function(Object?) parse) =>
    data is List ? [for (final e in data) ?parse(e)] : (throw const ApiException(ApiErrorKind.unknown));

Map<String, dynamic> _map(Object? value) => value is Map ? Map<String, dynamic>.from(value) : const {};
String _text(Object? value) => value is String ? value : '';
int _int(Object? value) => value is int ? value : 0;
double _num(Object? value) => value is num ? value.toDouble() : 0;
