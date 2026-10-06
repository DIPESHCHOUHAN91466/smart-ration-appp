import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../core/network/api_client.dart';
import '../../core/network/api_exception.dart';
import '../../core/providers.dart';

/// Citizens' complaints, on the backend routes (citizens only):
///   POST /api/grievances        file one (Idempotency-Key); returns its reference number, e.g. GRV-2026-000123
///   GET  /api/grievances/mine   my complaints, newest first, with their status
/// and for officials (the backend refuses everyone else):
///   GET  /api/grievances?status=  every complaint, newest first, optionally one status
///   POST /api/grievances/{id}/status  move one to UnderReview / Resolved / Rejected, with a reply the citizen sees
/// The citizen's name, mobile and shop come from their account on the backend, never from this form.

/// What the complaint is about (the backend's names).
enum ComplaintCategory {
  lessRation('LessRation'),
  poorQuality('PoorQuality'),
  shopClosed('ShopClosed'),
  overcharged('Overcharged'),
  tokenProblem('TokenProblem'),
  verificationProblem('VerificationProblem'),
  staffBehaviour('StaffBehaviour'),
  other('Other');

  const ComplaintCategory(this.wire);

  final String wire;

  static ComplaintCategory? fromWire(Object? v) => values.where((c) => c.wire == v).firstOrNull;
}

/// The ration items a complaint can be about (the backend's names).
const complaintItems = ['Rice', 'Wheat', 'Sugar', 'Pulses', 'EdibleOil', 'Salt'];

enum ComplaintStatus {
  submitted('Submitted'),
  underReview('UnderReview'),
  resolved('Resolved'),
  rejected('Rejected');

  const ComplaintStatus(this.wire);

  /// The backend's name for it.
  final String wire;

  /// Resolved and rejected complaints are finished; the office no longer acts on them.
  bool get isOpen => this == submitted || this == underReview;
}

ComplaintStatus _status(Object? v) => ComplaintStatus.values.where((s) => s.wire == v).firstOrNull ?? ComplaintStatus.submitted;

/// A complaint being written, possibly pre-filled by the AI assistant from what the person said.
class ComplaintDraft {
  const ComplaintDraft({this.category, this.rationType, this.description = '', this.fromAssistant = false});

  final ComplaintCategory? category;

  /// One of [complaintItems], or null when it is not about one item.
  final String? rationType;
  final String description;

  /// Filled by the assistant: the form says so and asks the person to check it.
  final bool fromAssistant;

  /// The assistant's proposal (`fields` of POST /api/assistant/understand), kept only where it fits.
  static ComplaintDraft fromAssistantFields(Map<Object?, Object?> fields) {
    final item = fields['rationType'];
    final description = fields['description'];
    return ComplaintDraft(
      category: ComplaintCategory.fromWire(fields['category']),
      rationType: complaintItems.contains(item) ? item as String : null,
      description: description is String ? description : '',
      fromAssistant: true,
    );
  }
}

class Complaint {
  const Complaint({
    required this.id,
    required this.reference,
    required this.category,
    required this.rationType,
    required this.description,
    required this.status,
    required this.shopName,
    required this.officeReply,
    required this.createdAt,
  });

  final int id;
  final String reference;
  final ComplaintCategory category;
  final String? rationType;
  final String description;
  final ComplaintStatus status;
  final String shopName;
  final String officeReply;

  /// UTC, as the backend stores it.
  final DateTime? createdAt;

  static Complaint? tryParse(Object? j) {
    if (j is! Map || j['id'] is! int || j['referenceNumber'] is! String) return null;
    String text(Object? v) => v is String ? v : '';
    final at = j['createdAt'];
    return Complaint(
      id: j['id'] as int,
      reference: j['referenceNumber'] as String,
      category: ComplaintCategory.fromWire(j['category']) ?? ComplaintCategory.other,
      rationType: complaintItems.contains(j['rationType']) ? j['rationType'] as String : null,
      description: text(j['description']),
      status: _status(j['status']),
      shopName: text(j['shopName']),
      officeReply: text(j['resolutionNote']),
      createdAt: at is String ? DateTime.tryParse(at.endsWith('Z') ? at : '${at}Z') : null,
    );
  }
}

/// The backend's limits for the description.
const complaintMinLength = 10;
const complaintMaxLength = 1000;

class GrievanceRepository {
  const GrievanceRepository(this._api);

  final ApiClient _api;

  /// [requestKey] must stay the same when the same complaint is sent again (e.g. after a timeout), so it is
  /// filed once. [fromAssistant] records that the AI assistant filled the form (the person still reviewed it).
  Future<Complaint> submit({
    required ComplaintCategory category,
    required String description,
    String? rationType,
    required bool fromAssistant,
    required String requestKey,
  }) async {
    final data = await _api.post<Object?>('/api/grievances', body: {
      'category': category.wire,
      'description': description.trim(),
      'rationType': ?rationType,
      'source': fromAssistant ? 'ASSISTANT' : 'APP',
    }, headers: {'Idempotency-Key': requestKey});
    return Complaint.tryParse(data) ?? (throw const ApiException(ApiErrorKind.unknown));
  }

  Future<List<Complaint>> mine() async => _list(await _api.get<Object?>('/api/grievances/mine'));

  /// Officials: every complaint (newest first), or only those with [status].
  Future<List<Complaint>> all({ComplaintStatus? status}) async =>
      _list(await _api.get<Object?>('/api/grievances', query: {'status': ?status?.wire}));

  /// Officials: records the outcome and the reply. The backend replaces any earlier reply, tells the
  /// citizen in their notifications and keeps an audit record of who did it.
  Future<Complaint> updateStatus(int id, ComplaintStatus status, {String note = ''}) async {
    assert(status != ComplaintStatus.submitted, 'a complaint cannot go back to Submitted');
    final data = await _api.post<Object?>('/api/grievances/$id/status', body: {
      'Status': status.wire,
      if (note.trim().isNotEmpty) 'Note': note.trim(),
    });
    return Complaint.tryParse(data) ?? (throw const ApiException(ApiErrorKind.unknown));
  }

  static List<Complaint> _list(Object? data) =>
      data is List ? [for (final e in data) ?Complaint.tryParse(e)] : (throw const ApiException(ApiErrorKind.unknown));
}

final grievanceRepositoryProvider = Provider<GrievanceRepository>((ref) => GrievanceRepository(ref.watch(apiClientProvider)));

final myComplaintsProvider = FutureProvider.autoDispose<List<Complaint>>((ref) => ref.watch(grievanceRepositoryProvider).mine());

/// Officials' list; null = every status.
final allComplaintsProvider = FutureProvider.autoDispose.family<List<Complaint>, ComplaintStatus?>(
    (ref, status) => ref.watch(grievanceRepositoryProvider).all(status: status));
