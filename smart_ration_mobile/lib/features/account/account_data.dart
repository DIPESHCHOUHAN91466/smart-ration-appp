import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../core/network/api_client.dart';
import '../../core/network/api_exception.dart';
import '../../core/providers.dart';
import '../auth/session.dart';

/// My account, read and changed through:
///   GET/PUT /api/users/profile                 name and mobile number (email is the sign-in name, read-only)
///   GET     /api/beneficiaries/me              citizens: Aadhaar, ration card and mobile verification
///   GET     /api/auth/mfa/status|setup|enable|disable   staff: two-factor sign-in with an authenticator app
class AccountRepository {
  const AccountRepository(this._api);

  final ApiClient _api;

  Future<SessionUser> profile() async => _user(await _api.get<Object?>('/api/users/profile'));

  /// [currentPassword] is needed (and only sent) when the mobile number changes.
  Future<SessionUser> saveProfile(String fullName, String mobileNumber, {String? currentPassword}) async =>
      _user(await _api.put<Object?>('/api/users/profile', body: {
        'fullName': fullName,
        'mobileNumber': mobileNumber,
        'currentPassword': ?currentPassword,
      }));

  /// Closes the signed-in citizen's account (POST /api/users/me/close); the caller then signs out.
  Future<void> closeAccount(String currentPassword) =>
      _api.post<Object?>('/api/users/me/close', body: {'currentPassword': currentPassword});

  Future<Verification> verification() async {
    final data = await _api.get<Object?>('/api/beneficiaries/me');
    if (data is! Map) throw const ApiException(ApiErrorKind.unknown);
    return Verification.parse(data);
  }

  Future<MfaStatus> mfaStatus() async => MfaStatus.parse(await _api.get<Object?>('/api/auth/mfa/status'));

  /// Asks for the password again; the answer is the secret for the authenticator app.
  Future<MfaSetup> startMfa(String password) async {
    final data = await _api.post<Object?>('/api/auth/mfa/setup', body: {'password': password});
    final secret = data is Map ? data['secret'] : null;
    final uri = data is Map ? data['otpauthUri'] : null;
    if (secret is! String || uri is! String) throw const ApiException(ApiErrorKind.unknown);
    return MfaSetup(secret: secret, otpauthUri: uri);
  }

  Future<MfaStatus> enableMfa(String code) async =>
      MfaStatus.parse(await _api.post<Object?>('/api/auth/mfa/enable', body: {'code': code}));

  Future<MfaStatus> disableMfa(String password, String code) async =>
      MfaStatus.parse(await _api.post<Object?>('/api/auth/mfa/disable', body: {'password': password, 'code': code}));

  static SessionUser _user(Object? data) => SessionUser.tryParse(data) ?? (throw const ApiException(ApiErrorKind.unknown));
}

/// One check from the beneficiary record: Verified, Pending, NotVerified, Failed or Expired (the backend's words).
class VerificationItem {
  const VerificationItem({required this.status, this.detail = '', this.date = ''});

  final String status;

  /// Masked Aadhaar, ration card number or masked mobile — never the full Aadhaar.
  final String detail;
  final String date;

  bool get isVerified => status == 'Verified';
}

class Verification {
  const Verification({required this.aadhaar, required this.rationCard, required this.mobile, required this.isDemoData});

  final VerificationItem aadhaar;
  final VerificationItem rationCard;
  final VerificationItem mobile;
  final bool isDemoData;

  static Verification parse(Map<dynamic, dynamic> me) {
    Map<dynamic, dynamic> part(String key) => me[key] is Map ? me[key] as Map : const {};
    String text(Object? v) => v is String ? v : '';
    final aadhaar = part('aadhaarVerification');
    final passbook = part('passbookVerification');
    final mobile = part('mobileVerification');
    String status(Object? v) => v is String && v.isNotEmpty ? v : 'NotVerified';
    return Verification(
      aadhaar: VerificationItem(
          status: status(aadhaar['status']), detail: text(aadhaar['aadhaarMasked']), date: text(aadhaar['verificationDate'])),
      rationCard: VerificationItem(
          status: status(passbook['verificationStatus']), detail: text(passbook['passbookNumber']), date: text(passbook['lastUpdated'])),
      mobile: VerificationItem(status: status(mobile['status']), detail: text(mobile['mobileMasked']), date: text(mobile['verifiedAt'])),
      isDemoData: passbook['verificationSource'] == 'SYNTHETIC_DEMO' || aadhaar['verificationSource'] == 'SYNTHETIC_DEMO',
    );
  }
}

class MfaStatus {
  const MfaStatus({required this.enabled, required this.available});

  final bool enabled;

  /// This account may use it and the server is set up for it (shop owners, officials and admins).
  final bool available;

  static MfaStatus parse(Object? data) {
    if (data is! Map) throw const ApiException(ApiErrorKind.unknown);
    return MfaStatus(enabled: data['enabled'] == true, available: data['available'] == true);
  }
}

class MfaSetup {
  const MfaSetup({required this.secret, required this.otpauthUri});

  /// Base32, for typing into the authenticator app.
  final String secret;
  final String otpauthUri;
}

final accountRepositoryProvider = Provider<AccountRepository>((ref) => AccountRepository(ref.watch(apiClientProvider)));

final profileProvider = FutureProvider.autoDispose<SessionUser>((ref) => ref.watch(accountRepositoryProvider).profile());

final verificationProvider = FutureProvider.autoDispose<Verification>((ref) => ref.watch(accountRepositoryProvider).verification());

final mfaStatusProvider = FutureProvider.autoDispose<MfaStatus>((ref) => ref.watch(accountRepositoryProvider).mfaStatus());
