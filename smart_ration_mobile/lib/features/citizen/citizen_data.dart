import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../core/network/api_client.dart';
import '../../core/network/api_exception.dart';
import '../../core/providers.dart';

/// Everything the citizen's home, family, ration card and eligibility screens show, read from:
///   GET /api/beneficiaries/me                 profile, family, Aadhaar (masked), ration card, shop
///   GET /api/beneficiaries/{id}/entitlement   this month's quota per item
///   GET /api/beneficiaries/{id}/collections   what was collected before
/// The app never calculates entitlement itself: the backend's numbers are shown as they are.
class CitizenOverview {
  const CitizenOverview({
    required this.beneficiaryId,
    required this.fullName,
    required this.mobileMasked,
    required this.address,
    required this.accountActive,
    required this.familyCode,
    required this.members,
    required this.familySize,
    required this.eligibleMembers,
    required this.aadhaarMasked,
    required this.aadhaarVerified,
    required this.cardNumber,
    required this.cardActive,
    required this.isDemoData,
    required this.shop,
    required this.schemeName,
    required this.entitlement,
    required this.collections,
  });

  final int beneficiaryId;
  final String fullName;
  final String mobileMasked;
  final String address;
  final bool accountActive;
  final String familyCode;
  final List<FamilyMember> members;
  final int familySize;
  final int eligibleMembers;
  final String aadhaarMasked;
  final bool aadhaarVerified;
  final String cardNumber;
  final bool cardActive;

  /// True for the synthetic demonstration data; screens say so clearly.
  final bool isDemoData;
  final AssignedShop? shop;
  final String schemeName;
  final List<EntitlementItem> entitlement;
  final List<Collection> collections;

  FamilyEligibility get eligibility {
    if (!accountActive || !cardActive || eligibleMembers == 0) return FamilyEligibility.notEligible;
    return eligibleMembers < familySize ? FamilyEligibility.partiallyEligible : FamilyEligibility.eligible;
  }
}

/// ELIGIBLE / PARTIALLY ELIGIBLE / NOT ELIGIBLE, from the backend's per-member decisions and card status.
enum FamilyEligibility { eligible, partiallyEligible, notEligible }

class FamilyMember {
  const FamilyMember({required this.id, required this.fullName, required this.age, required this.relationship, required this.eligibility});

  final int id;
  final String fullName;
  final int age;

  /// Head, Spouse, Son, Daughter, Parent or Other (the backend's words).
  final String relationship;

  /// Eligible, NotEligible, Pending or VerificationRequired (the backend's words).
  final String eligibility;

  bool get isHead => relationship == 'Head';
  bool get isEligible => eligibility == 'Eligible';
}

class AssignedShop {
  const AssignedShop({required this.name, required this.address, required this.district});

  final String name;
  final String address;
  final String district;
}

class EntitlementItem {
  const EntitlementItem({required this.rationType, required this.monthly, required this.collected, required this.remaining});

  /// Rice, Wheat, Sugar, Pulses, EdibleOil or Salt.
  final String rationType;
  final double monthly;
  final double collected;
  final double remaining;
}

class Collection {
  const Collection({required this.code, required this.collectedAt, required this.shopName, required this.items});

  final String code;

  /// The backend's local time text, e.g. "2026-09-29 07:17".
  final String collectedAt;
  final String shopName;
  final List<(String rationType, double quantity)> items;
}

class CitizenRepository {
  const CitizenRepository(this._api);

  final ApiClient _api;

  Future<CitizenOverview> load() async {
    final me = _map(await _api.get<Object?>('/api/beneficiaries/me'));
    final beneficiary = _map(me['beneficiary']);
    final id = beneficiary['id'];
    if (id is! int) throw const ApiException(ApiErrorKind.unknown);

    final (entitlementData, collectionsData) = await (
      _api.get<Object?>('/api/beneficiaries/$id/entitlement'),
      _api.get<Object?>('/api/beneficiaries/$id/collections'),
    ).wait;
    return parseOverview(me, _map(entitlementData), collectionsData);
  }
}

/// Turns the three backend answers into a [CitizenOverview]. Missing optional parts become empty
/// values; a missing required part is reported as an error instead of showing wrong information.
CitizenOverview parseOverview(Map<String, dynamic> me, Map<String, dynamic> entitlement, Object? collections) {
  final beneficiary = _map(me['beneficiary']);
  final family = _map(me['family']);
  final aadhaar = me['aadhaarVerification'] is Map ? _map(me['aadhaarVerification']) : const <String, dynamic>{};
  final passbook = me['passbookVerification'] is Map ? _map(me['passbookVerification']) : const <String, dynamic>{};
  final shop = me['rationShop'] is Map ? _map(me['rationShop']) : null;

  final members = [
    for (final m in (family['members'] as List? ?? const []).whereType<Map>())
      FamilyMember(
        id: _int(m['id']),
        fullName: _text(m['fullName']),
        age: _int(m['age']),
        relationship: _text(m['relationship']),
        eligibility: _text(m['eligibility']),
      ),
  ];

  return CitizenOverview(
    beneficiaryId: _int(beneficiary['id']),
    fullName: _text(beneficiary['fullName']),
    mobileMasked: _text(beneficiary['mobileMasked']),
    address: _text(beneficiary['address']),
    accountActive: beneficiary['isActive'] == true && beneficiary['isBlocked'] != true,
    familyCode: _text(family['familyCode']),
    members: members,
    familySize: family['familySize'] is int ? family['familySize'] as int : members.length,
    eligibleMembers: family['eligibleMemberCount'] is int
        ? family['eligibleMemberCount'] as int
        : members.where((m) => m.isEligible).length,
    aadhaarMasked: _text(aadhaar['aadhaarMasked']),
    aadhaarVerified: aadhaar['status'] == 'Verified',
    cardNumber: _text(passbook['passbookNumber']),
    cardActive: passbook['status'] == 'ACTIVE',
    isDemoData: passbook['verificationSource'] == 'SYNTHETIC_DEMO' || aadhaar['verificationSource'] == 'SYNTHETIC_DEMO',
    shop: shop == null
        ? null
        : AssignedShop(name: _text(shop['shopName']), address: _text(shop['address']), district: _text(shop['district'])),
    schemeName: _text(entitlement['schemeName']),
    entitlement: [
      for (final i in (entitlement['items'] as List? ?? const []).whereType<Map>())
        EntitlementItem(
          rationType: _text(i['rationType']),
          monthly: _num(i['monthlyEntitlement']),
          collected: _num(i['alreadyCollected']),
          remaining: _num(i['remaining']),
        ),
    ],
    collections: [
      for (final c in (collections is List ? collections : const []).whereType<Map>())
        Collection(
          code: _text(c['collectionCode']),
          collectedAt: _text(c['collectedAt']),
          shopName: _text(c['shopName']),
          items: [
            for (final i in (c['items'] as List? ?? const []).whereType<Map>()) (_text(i['rationType']), _num(i['quantity'])),
          ],
        ),
    ],
  );
}

Map<String, dynamic> _map(Object? value) =>
    value is Map ? Map<String, dynamic>.from(value) : (throw const ApiException(ApiErrorKind.unknown));
String _text(Object? value) => value is String ? value : '';
int _int(Object? value) => value is int ? value : 0;
double _num(Object? value) => value is num ? value.toDouble() : 0;

final citizenRepositoryProvider = Provider<CitizenRepository>((ref) => CitizenRepository(ref.watch(apiClientProvider)));

/// Loaded when a citizen screen opens; pull down to reload.
final citizenOverviewProvider =
    FutureProvider.autoDispose<CitizenOverview>((ref) => ref.watch(citizenRepositoryProvider).load());
