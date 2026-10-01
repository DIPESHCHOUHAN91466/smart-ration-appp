import '../../core/network/api_exception.dart';
import '../../l10n/app_localizations.dart';

/// Why a scan was refused, from the backend's stable status code. Unknown codes show the backend's
/// own sentence, so a new backend rule is never hidden.
String scanRefusalIn(AppLocalizations l, String status, String serverMessage) => switch (status) {
      'INVALID_SIGNATURE' => l.scanInvalidSignature,
      'INVALID_PROJECT' || 'INVALID_TYPE' => l.scanNotOurs,
      'INVALID_FORMAT' || 'MISSING_FIELDS' || 'UNSUPPORTED_VERSION' => l.scanUnreadable,
      'EXPIRED' => l.scanExpired,
      'TOKEN_NOT_FOUND' => l.scanNoBooking,
      'WRONG_SHOP' => l.scanWrongShop,
      'ALREADY_COLLECTED' => l.scanAlreadyCollected,
      'BOOKING_CANCELLED' => l.scanBookingCancelled,
      _ => serverMessage.isNotEmpty ? serverMessage : l.errorGeneric,
    };

/// The backend's reason for blocking a collection (verification_service._summary), translated.
String blockedReasonIn(AppLocalizations l, String? reason) {
  if (reason == null) return l.errorGeneric;
  if (reason.startsWith('Token is not valid for collection')) return l.reasonTokenInvalid;
  return switch (reason) {
    'This beneficiary account is blocked.' => l.reasonAccountBlocked,
    'This beneficiary account is not active.' => l.reasonAccountInactive,
    'This token has already been used for collection.' => l.scanAlreadyCollected,
    'This booking was cancelled.' => l.scanBookingCancelled,
    'This token has expired — the booked collection date has passed.' => l.scanExpired,
    'Aadhaar verification failed.' => l.reasonAadhaarFailed,
    'Aadhaar verification has expired.' => l.reasonAadhaarExpired,
    'Aadhaar verification is pending.' => l.reasonAadhaarPending,
    'Passbook verification is pending.' => l.reasonPassbookPending,
    'Mobile OTP verification required.' => l.reasonMobileRequired,
    'This beneficiary is not eligible under the selected scheme.' => l.reasonNotEligible,
    'No remaining ration entitlement.' => l.reasonNoEntitlement,
    _ => reason,
  };
}

/// A failed handover. Nothing was issued in any of these cases (the backend works in one transaction).
String handoverErrorIn(AppLocalizations l, ApiException e) => switch (e.errorCode) {
      'INSUFFICIENT_STOCK' => l.errorInsufficientStock,
      'CONCURRENT_UPDATE' => l.errorConcurrentUpdate,
      _ when e.kind == ApiErrorKind.conflict => blockedReasonIn(l, e.serverMessage),
      _ => e.messageIn(l),
    };

/// A failed OTP step at the counter.
String counterOtpErrorIn(AppLocalizations l, ApiException e) {
  final message = e.serverMessage ?? '';
  if (message.startsWith('No beneficiary is registered')) return l.otpNoCustomer;
  if (message.startsWith('No active booking')) return l.otpNoBookingHere;
  if (e.kind == ApiErrorKind.badRequest && (message.contains('OTP') || message.contains('code'))) return l.otpInvalid;
  return e.messageIn(l);
}
