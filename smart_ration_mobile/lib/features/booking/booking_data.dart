import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../core/network/api_client.dart';
import '../../core/network/api_exception.dart';
import '../../core/providers.dart';

/// Booking a 5-minute slot, the resulting token and its QR, on the existing backend routes:
///   GET    /api/slots?shopId=&date=          a shop's slots for one day
///   GET    /api/ration/items?shopId=         items with the per-visit limit, remaining quota and stock
///   POST   /api/ration/bookings              book -> token (the backend checks every rule again)
///   GET    /api/ration/bookings              my tokens
///   GET    /api/tokens/{id}                  one token
///   DELETE /api/ration/bookings/{id}         cancel
///   GET    /api/qr/payload/{id}              the signed QR text (no personal data)

class Slot {
  const Slot({required this.id, required this.date, required this.start, required this.end, required this.capacity, required this.booked, required this.status});

  final int id;
  final DateTime date;

  /// "09:05" (the shop's local time).
  final String start;
  final String end;
  final int capacity;
  final int booked;
  final String status;

  int get placesLeft => (capacity - booked).clamp(0, capacity);
  bool get isFull => placesLeft == 0 || status != 'Available';

  /// When the slot starts, as a time on the phone's clock (shops and citizens are in the same place).
  DateTime get startsAt {
    final parts = start.split(':');
    return DateTime(date.year, date.month, date.day, int.tryParse(parts[0]) ?? 0, int.tryParse(parts.elementAtOrNull(1) ?? '') ?? 0);
  }

  /// A slot that has already begun can't be booked. (The backend only checks the date, so the app hides these.)
  bool hasStarted(DateTime now) => !startsAt.isAfter(now);

  static Slot? tryParse(Object? j) {
    if (j is! Map || j['id'] is! int) return null;
    final date = DateTime.tryParse('${j['slotDate']}');
    if (date == null) return null;
    return Slot(
      id: j['id'] as int,
      date: DateTime(date.year, date.month, date.day),
      start: _hhmm(j['startTime']),
      end: _hhmm(j['endTime']),
      capacity: j['capacity'] is int ? j['capacity'] as int : 0,
      booked: j['bookedCount'] is int ? j['bookedCount'] as int : 0,
      status: '${j['status']}',
    );
  }
}

class BookableItem {
  const BookableItem({required this.rationType, required this.perVisit, required this.remainingThisMonth, required this.inStock});

  /// Rice, Wheat, Sugar, Pulses, EdibleOil or Salt.
  final String rationType;
  final double perVisit;
  final double? remainingThisMonth;
  final double? inStock;

  /// The most that can be asked for in one booking: per-visit limit, what is left this month and
  /// the shop's stock, whichever is smallest. The backend enforces the same limits.
  double get maxQuantity {
    var max = perVisit;
    if (remainingThisMonth != null && remainingThisMonth! < max) max = remainingThisMonth!;
    if (inStock != null && inStock! < max) max = inStock!;
    return max < 0 ? 0 : max;
  }

  static BookableItem? tryParse(Object? j) {
    if (j is! Map || j['rationType'] is! String) return null;
    double? n(Object? v) => v is num ? v.toDouble() : null;
    return BookableItem(
      rationType: j['rationType'] as String,
      perVisit: n(j['standardQuotaPerBooking']) ?? 0,
      remainingThisMonth: n(j['eligibleQuantity']),
      inStock: n(j['availableQuantity']),
    );
  }
}

/// What the person sees: booked (upcoming), collected, cancelled, or missed (the day passed).
enum TokenState { booked, collected, cancelled, missed }

class RationToken {
  const RationToken({
    required this.id,
    required this.number,
    required this.backendStatus,
    required this.shopName,
    required this.date,
    required this.start,
    required this.end,
    required this.items,
    required this.reference,
  });

  final int id;

  /// e.g. SR-2026-000125
  final String number;

  /// Pending, Confirmed, Completed, Cancelled or NoShow (the backend's words).
  final String backendStatus;
  final String shopName;
  final DateTime date;
  final String start;
  final String end;
  final List<(String rationType, double quantity)> items;

  /// SRQR-… code a shop can type when the camera can't read the QR.
  final String reference;

  TokenState stateOn(DateTime today) {
    switch (backendStatus) {
      case 'Completed':
        return TokenState.collected;
      case 'Cancelled':
        return TokenState.cancelled;
      case 'NoShow':
        return TokenState.missed;
    }
    final day = DateTime(today.year, today.month, today.day);
    return date.isBefore(day) ? TokenState.missed : TokenState.booked;
  }

  static RationToken? tryParse(Object? j) {
    if (j is! Map || j['id'] is! int) return null;
    final date = DateTime.tryParse('${j['slotDate']}');
    if (date == null) return null;
    return RationToken(
      id: j['id'] as int,
      number: '${j['tokenNumber'] ?? ''}',
      backendStatus: '${j['status'] ?? ''}',
      shopName: '${j['rationShopName'] ?? ''}',
      date: DateTime(date.year, date.month, date.day),
      start: _hhmm(j['startTime']),
      end: _hhmm(j['endTime']),
      items: [
        for (final i in (j['items'] as List? ?? const []).whereType<Map>())
          ('${i['rationType']}', i['quantity'] is num ? (i['quantity'] as num).toDouble() : 0),
      ],
      reference: '${j['qrCodeValue'] ?? ''}',
    );
  }
}

String _hhmm(Object? v) {
  final s = '${v ?? ''}';
  return s.length >= 5 ? s.substring(0, 5) : s;
}

String ymd(DateTime d) =>
    '${d.year.toString().padLeft(4, '0')}-${d.month.toString().padLeft(2, '0')}-${d.day.toString().padLeft(2, '0')}';

List<T> _list<T>(Object? data, T? Function(Object?) parse) =>
    data is List ? [for (final e in data) ?parse(e)] : (throw const ApiException(ApiErrorKind.unknown));

class BookingRepository {
  const BookingRepository(this._api);

  final ApiClient _api;

  Future<List<Slot>> slots(int shopId, DateTime day) async =>
      _list(await _api.get<Object?>('/api/slots', query: {'shopId': shopId, 'date': ymd(day)}), Slot.tryParse);

  Future<List<BookableItem>> items(int shopId) async =>
      _list(await _api.get<Object?>('/api/ration/items', query: {'shopId': shopId}), BookableItem.tryParse);

  Future<RationToken> book({required int shopId, required int slotId, required Map<String, double> items}) async {
    final data = await _api.post<Object?>('/api/ration/bookings', body: {
      'rationShopId': shopId,
      'timeSlotId': slotId,
      'items': [
        for (final e in items.entries)
          if (e.value > 0) {'rationType': e.key, 'quantity': e.value},
      ],
    });
    return RationToken.tryParse(data) ?? (throw const ApiException(ApiErrorKind.unknown));
  }

  Future<List<RationToken>> myTokens() async => _list(await _api.get<Object?>('/api/ration/bookings'), RationToken.tryParse);

  Future<RationToken> token(int id) async =>
      RationToken.tryParse(await _api.get<Object?>('/api/tokens/$id')) ?? (throw const ApiException(ApiErrorKind.unknown));

  Future<void> cancel(int id) => _api.delete('/api/ration/bookings/$id');

  Future<String> qrPayload(int id) async {
    final data = await _api.get<Object?>('/api/qr/payload/$id');
    return data is String && data.isNotEmpty ? data : (throw const ApiException(ApiErrorKind.unknown));
  }
}

final bookingRepositoryProvider = Provider<BookingRepository>((ref) => BookingRepository(ref.watch(apiClientProvider)));

/// All my tokens, newest first (as the backend sends them).
final myTokensProvider = FutureProvider.autoDispose<List<RationToken>>((ref) => ref.watch(bookingRepositoryProvider).myTokens());

final tokenProvider = FutureProvider.autoDispose.family<RationToken, int>((ref, id) => ref.watch(bookingRepositoryProvider).token(id));

final qrPayloadProvider = FutureProvider.autoDispose.family<String, int>((ref, id) => ref.watch(bookingRepositoryProvider).qrPayload(id));

/// The next token still to be collected (today or later), if any.
RationToken? nextToken(List<RationToken> tokens, DateTime now) {
  final upcoming = tokens.where((t) => t.stateOn(now) == TokenState.booked).toList()
    ..sort((a, b) {
      final byDate = a.date.compareTo(b.date);
      return byDate != 0 ? byDate : a.start.compareTo(b.start);
    });
  return upcoming.firstOrNull;
}
