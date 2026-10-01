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
FakeReply demoServer(RequestOptions r) => switch (r.path) {
      '/api/beneficiaries/me' => FakeReply.ok(citizenProfileJson()),
      '/api/beneficiaries/1/entitlement' => FakeReply.ok(citizenEntitlementJson()),
      '/api/beneficiaries/1/collections' => FakeReply.ok(citizenCollectionsJson()),
      _ => const FakeReply(200, {'status': 'healthy', 'database': 'healthy', 'dataMode': 'synthetic'}),
    };

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
  {'id': 1, 'fullName': 'Asha Devi', 'age': 34, 'relationship': 'Head', 'eligibility': 'Eligible'},
  {'id': 2, 'fullName': 'Ramesh Devi', 'age': 37, 'relationship': 'Spouse', 'eligibility': 'Eligible'},
  {'id': 3, 'fullName': 'Meena Devi', 'age': 9, 'relationship': 'Daughter', 'eligibility': 'Eligible'},
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
