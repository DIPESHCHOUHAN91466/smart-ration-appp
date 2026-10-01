import 'dart:convert';
import 'dart:typed_data';

import 'package:dio/dio.dart';

/// Stands in for the real backend in tests: answers each request from [handler] and remembers
/// what the app sent. [delay] makes every answer slow, to test requests that overlap.
class FakeBackend implements HttpClientAdapter {
  FakeBackend(this.handler, {this.delay = Duration.zero});

  final FakeReply Function(RequestOptions request) handler;
  final Duration delay;
  final List<RequestOptions> requests = [];

  List<String> get paths => requests.map((r) => r.path).toList();

  @override
  Future<ResponseBody> fetch(RequestOptions options, Stream<Uint8List>? requestStream, Future<void>? cancelFuture) async {
    requests.add(options);
    if (delay > Duration.zero) await Future<void>.delayed(delay);
    final reply = handler(options);
    if (reply.error != null) {
      throw DioException(requestOptions: options, type: reply.error!);
    }
    return ResponseBody.fromString(
      jsonEncode(reply.body),
      reply.status,
      headers: {
        Headers.contentTypeHeader: [Headers.jsonContentType],
      },
    );
  }

  @override
  void close({bool force = false}) {}
}

class FakeReply {
  const FakeReply(this.status, this.body) : error = null;
  const FakeReply.fails(DioExceptionType this.error)
      : status = 0,
        body = null;

  final int status;
  final Object? body;
  final DioExceptionType? error;

  /// The backend's success envelope around [data].
  static FakeReply ok(Object? data) => FakeReply(200, {'success': true, 'message': 'Success', 'data': data, 'errors': null});

  /// The backend's failure envelope.
  static FakeReply fail(int status, String message) =>
      FakeReply(status, {'success': false, 'message': message, 'data': null, 'errors': null});
}

/// The `user` part of a sign-in answer, as the backend sends it.
Map<String, Object?> userJson({
  int id = 7,
  String fullName = 'Asha Devi',
  String role = 'RuralUser',
  int? rationShopId,
}) =>
    {
      'id': id,
      'fullName': fullName,
      'email': 'asha@example.com',
      'mobileNumber': '9800000007',
      'role': role,
      'rationShopId': rationShopId,
    };

/// A full sign-in / refresh answer.
FakeReply signedIn({String access = 'access-1', String refresh = 'refresh-1', Map<String, Object?>? user}) => FakeReply.ok({
      'accessToken': access,
      'refreshToken': refresh,
      'accessTokenExpiresAt': '2026-10-01T10:15:00Z',
      'user': user ?? userJson(),
    });

/// A backend with the demo citizen's data (same shapes as the real /api/beneficiaries answers),
/// a working /health, and nothing else.
FakeReply demoServer(RequestOptions r) => switch ((r.method, r.path)) {
      (_, '/api/beneficiaries/me') => FakeReply.ok(citizenProfileJson()),
      (_, '/api/beneficiaries/1/entitlement') => FakeReply.ok(citizenEntitlementJson()),
      (_, '/api/beneficiaries/1/collections') => FakeReply.ok(citizenCollectionsJson()),
      ('GET', '/api/ration/bookings') => FakeReply.ok([tokenJson()]),
      ('POST', '/api/ration/bookings') => FakeReply.ok(tokenJson(id: 502, number: 'SR-2026-000502')),
      ('DELETE', '/api/ration/bookings/501') => FakeReply.ok(null),
      (_, '/api/tokens/501') => FakeReply.ok(tokenJson()),
      (_, '/api/tokens/502') => FakeReply.ok(tokenJson(id: 502, number: 'SR-2026-000502')),
      (_, '/api/qr/payload/501') => FakeReply.ok(demoQrPayload),
      (_, '/api/qr/payload/502') => FakeReply.ok(demoQrPayload),
      (_, '/api/slots') => FakeReply.ok(slotsJson('${r.queryParameters['date']}')),
      (_, '/api/ration/items') => FakeReply.ok(bookableItemsJson()),
      _ => const FakeReply(200, {'status': 'healthy', 'database': 'healthy', 'dataMode': 'synthetic'}),
    };

/// The signed QR text the backend sends (shape only; the signature is not real).
const demoQrPayload = '{"version":"1.0","project":"SMART_RATION_HSD2C","type":"RATION_TOKEN",'
    '"reference":"SRQR-501-ABCDEF0123456789","token":"SR-2026-000501","signature":"00"}';

String _ymd(DateTime d) => d.toIso8601String().substring(0, 10);

/// A token for tomorrow (so it is always upcoming), as /api/ration/bookings returns it.
Map<String, Object?> tokenJson({int id = 501, String number = 'SR-2026-000501', String status = 'Confirmed', int dayOffset = 1}) => {
      'id': id,
      'tokenNumber': number,
      'status': status,
      'rationShopId': 1,
      'rationShopName': 'Satnavari Ration Shop',
      'timeSlotId': 77,
      'slotDate': '${_ymd(DateTime.now().add(Duration(days: dayOffset)))}T00:00:00',
      'startTime': '10:05:00',
      'endTime': '10:10:00',
      'qrCodeValue': 'SRQR-$id-ABCDEF0123456789',
      'items': [
        {'rationType': 'Rice', 'quantity': 5},
        {'rationType': 'EdibleOil', 'quantity': 0.5},
      ],
    };

/// Three slots on [date]: 06:00 (always already started), 23:50 open, 23:55 full.
List<Map<String, Object?>> slotsJson(String date) => [
      {'id': 70, 'slotDate': '${date}T00:00:00', 'startTime': '00:00:00', 'endTime': '00:05:00', 'capacity': 2, 'bookedCount': 0, 'status': 'Available'},
      {'id': 77, 'slotDate': '${date}T00:00:00', 'startTime': '23:50:00', 'endTime': '23:55:00', 'capacity': 2, 'bookedCount': 1, 'status': 'Available'},
      {'id': 78, 'slotDate': '${date}T00:00:00', 'startTime': '23:55:00', 'endTime': '23:59:00', 'capacity': 2, 'bookedCount': 2, 'status': 'Full'},
    ];

List<Map<String, Object?>> bookableItemsJson() => [
      {'rationType': 'Rice', 'standardQuotaPerBooking': 5, 'eligibleQuantity': 15, 'availableQuantity': 100},
      {'rationType': 'Wheat', 'standardQuotaPerBooking': 5, 'eligibleQuantity': 3, 'availableQuantity': 100},
      {'rationType': 'Salt', 'standardQuotaPerBooking': 1, 'eligibleQuantity': 0.75, 'availableQuantity': 50},
    ];

Map<String, Object?> citizenProfileJson({String cardStatus = 'ACTIVE', List<Map<String, Object?>>? members}) => {
      'beneficiary': {
        'id': 1,
        'beneficiaryCode': 'BEN-DEMO-0001',
        'fullName': 'Asha Devi',
        'mobileMasked': '******0001',
        'address': 'Satnavari',
        'isActive': true,
        'isBlocked': false,
      },
      'family': {
        'familyCode': 'FAM-DEMO-0001',
        'familyHeadName': 'Asha Devi',
        'familySize': (members ?? _members).length,
        'eligibleMemberCount': (members ?? _members).where((m) => m['eligibility'] == 'Eligible').length,
        'members': members ?? _members,
      },
      'aadhaarVerification': {
        'status': 'Verified',
        'aadhaarMasked': 'XXXX-XXXX-7173',
        'verificationSource': 'SYNTHETIC_DEMO',
      },
      'passbookVerification': {
        'passbookNumber': 'PB-DEMO-0001',
        'status': cardStatus,
        'verificationStatus': 'Verified',
        'verificationSource': 'SYNTHETIC_DEMO',
      },
      'mobileVerification': {'mobileMasked': '******0001', 'status': 'Verified'},
      'rationShop': {'id': 1, 'shopName': 'Satnavari Ration Shop', 'shopCode': 'FPS-001', 'address': 'Main road', 'district': 'Nagpur'},
    };

const _members = [
  {'id': 1, 'fullName': 'Asha Devi', 'age': 34, 'relationship': 'Head', 'eligibility': 'Eligible', 'gender': 'Female'},
  {'id': 2, 'fullName': 'Ramesh Devi', 'age': 37, 'relationship': 'Spouse', 'eligibility': 'Eligible', 'gender': null},
  {'id': 3, 'fullName': 'Meena Devi', 'age': 9, 'relationship': 'Daughter', 'eligibility': 'Eligible', 'gender': 'Female'},
];

Map<String, Object?> citizenEntitlementJson() => {
      'schemeCode': 'DEMO-NFSA',
      'schemeName': 'Demo National Food Security Scheme',
      'familySize': 3,
      'eligibleMemberCount': 3,
      'items': [
        {'rationType': 'Rice', 'monthlyEntitlement': 15, 'alreadyCollected': 5, 'remaining': 10, 'todayAllocation': 5},
        {'rationType': 'Wheat', 'monthlyEntitlement': 9, 'alreadyCollected': 0, 'remaining': 9, 'todayAllocation': 5},
        {'rationType': 'EdibleOil', 'monthlyEntitlement': 1.5, 'alreadyCollected': 0, 'remaining': 1.5, 'todayAllocation': 1},
        {'rationType': 'Salt', 'monthlyEntitlement': 0.75, 'alreadyCollected': 0, 'remaining': 0.75, 'todayAllocation': 0.75},
      ],
    };

List<Map<String, Object?>> citizenCollectionsJson() => [
      {
        'collectionCode': 'COL-DEMO-000042',
        'collectedAt': '2026-09-29 07:17',
        'shopName': 'Satnavari Ration Shop',
        'items': [
          {'rationType': 'Rice', 'quantity': 5},
        ],
      },
    ];

/// A backend with the demo shop's counter (same shapes as the real /api/shop, /api/qr/scan,
/// /api/verification and /api/ration/collection answers).
FakeReply shopServer(RequestOptions r) => switch ((r.method, r.path)) {
      (_, '/api/shop/dashboard') => FakeReply.ok(shopDashboardJson()),
      ('POST', '/api/qr/scan') => FakeReply.ok(scanJson('${(r.data as Map)['qrData']}')),
      (_, '/api/tokens/501') => FakeReply.ok(tokenJson()),
      ('POST', '/api/verification/otp/request') => FakeReply.ok(
          {'otpVerificationId': 31, 'mobileMasked': '******0007', 'expiresInMinutes': 5, 'demoOtpValue': '123456'}),
      ('POST', '/api/verification/otp/verify') => (r.data as Map)['code'] == '123456'
          ? FakeReply.ok(verificationJson())
          : FakeReply.fail(400, 'Incorrect OTP. 2 attempt(s) remaining.'),
      ('POST', '/api/ration/collection/confirm') => FakeReply.ok(receiptJson()),
      _ => healthyReply,
    };

const healthyReply = FakeReply(200, {'status': 'healthy', 'database': 'healthy', 'dataMode': 'synthetic'});

Map<String, Object?> shopDashboardJson() => {
      'shopId': 3,
      'shopName': 'Satnavari Ration Shop',
      'todayTotalTokens': 12,
      'todayCompleted': 5,
      'todayPending': 6,
      'todayCancelled': 1,
      'inventory': [],
    };

/// What /api/qr/scan answers for the demo codes:
///   SRQR-501-…  ready;  SRQR-777-…  already collected;  SRQR-999-…  forged;  anything else  not ours.
Map<String, Object?> scanJson(String code) {
  if (code.startsWith('SRQR-501-')) {
    return {'verified': true, 'status': 'VERIFIED', 'message': 'QR verified successfully', 'tokenNumber': 'SR-2026-000501',
        'verification': verificationJson()};
  }
  if (code.startsWith('SRQR-777-')) {
    return {'verified': false, 'status': 'ALREADY_COLLECTED', 'message': 'This token has already been used for collection.',
        'tokenNumber': 'SR-2026-000501',
        'verification': verificationJson(ready: false, reason: 'This token has already been used for collection.')};
  }
  if (code.startsWith('SRQR-999-')) {
    return {'verified': false, 'status': 'INVALID_SIGNATURE', 'message': 'QR code signature is invalid.', 'tokenNumber': null, 'verification': null};
  }
  return {'verified': false, 'status': 'INVALID_PROJECT', 'message': 'This QR code does not belong to the Smart Ration system.',
      'tokenNumber': null, 'verification': null};
}

/// The verification bundle (verification_service.build_response), trimmed to what the app reads.
Map<String, Object?> verificationJson({bool ready = true, String? reason}) => {
      'beneficiary': {'id': 1, 'beneficiaryCode': 'BEN-DEMO-0001', 'fullName': 'Asha Devi', 'mobileMasked': '******0007',
          'isActive': true, 'isBlocked': false},
      'family': {'familyCode': 'FAM-DEMO-0001', 'familyHeadName': 'Asha Devi', 'familySize': 4, 'eligibleMemberCount': 3,
          'members': [
            {'fullName': 'Asha Devi', 'relationship': 'Head', 'eligibility': 'Eligible'},
            {'fullName': 'Ravi Devi', 'relationship': 'Son', 'eligibility': 'Eligible'},
          ]},
      'booking': {'tokenId': 501, 'tokenNumber': 'SR-2026-000501', 'status': ready ? 'Confirmed' : 'Completed',
          'collectionDate': DateTime.now().toIso8601String().substring(0, 10), 'bookingTime': '10:05', 'shopId': 3,
          'shopName': 'Satnavari Ration Shop', 'collectionCompleted': !ready},
      'entitlement': {'schemeCode': 'PHH', 'schemeName': 'Priority Household', 'items': []},
      'verificationSummary': {'aadhaarVerified': true, 'passbookVerified': true, 'mobileVerified': true, 'tokenValid': ready,
          'familyEligible': true, 'entitlementAvailable': true,
          'overallStatus': ready ? 'READY_FOR_RATION_COLLECTION' : 'COLLECTION_BLOCKED', 'blockedReason': reason},
    };

Map<String, Object?> receiptJson() => {
      'collectionCode': 'COL-DEMO-000042',
      'tokenNumber': 'SR-2026-000501',
      'beneficiaryName': 'Asha Devi',
      'familySize': 4,
      'schemeCode': 'PHH',
      'issuedItems': [
        {'rationType': 'Rice', 'quantity': 5},
        {'rationType': 'EdibleOil', 'quantity': 0.5},
      ],
      'totalQuantityKg': 5.5,
      'shopName': 'Satnavari Ration Shop',
      'collectedAt': '2026-10-01 04:37',
    };
