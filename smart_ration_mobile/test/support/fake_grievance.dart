import 'package:dio/dio.dart';

import 'fake_backend.dart';

/// A citizen backend that also takes complaints (same shapes as the real /api/grievances answers), remembering
/// them like the real one: the same Idempotency-Key returns the first complaint; numbers count up from 1.
/// Anything else is answered by [fallback] (the demo citizen by default).
FakeReply Function(RequestOptions) complaintServer({FakeReply Function(RequestOptions)? fallback, FakeReply? refuseWith}) {
  final filed = <Map<String, Object?>>[];
  final byKey = <String, Map<String, Object?>>{};
  return (r) {
    if (r.path == '/api/grievances' && r.method == 'POST') {
      if (refuseWith != null) return refuseWith;
      final key = r.headers['Idempotency-Key'] as String?;
      if (key != null && byKey[key] != null) return FakeReply.ok(byKey[key]);
      final body = r.data as Map;
      final complaint = complaintJson(filed.length + 1, body['category'] as String, body['description'] as String,
          rationType: body['rationType'] as String?, source: body['source'] as String? ?? 'APP');
      filed.insert(0, complaint);
      if (key != null) byKey[key] = complaint;
      return FakeReply.ok(complaint);
    }
    if (r.path == '/api/grievances/mine') return FakeReply.ok(filed);
    return (fallback ?? demoServer)(r);
  };
}

Map<String, Object?> complaintJson(int id, String category, String description,
        {String? rationType, String status = 'Submitted', String source = 'APP', String? reply}) =>
    {
      'id': id, 'referenceNumber': 'GRV-2026-${id.toString().padLeft(6, '0')}', 'category': category,
      'rationType': rationType, 'description': description, 'status': status, 'source': source, 'shopId': 3,
      'shopName': 'Satnavari Ration Shop', 'resolutionNote': reply, 'createdAt': '2026-10-02T05:30:00.000000',
      'updatedAt': '2026-10-02T05:30:00.000000',
    };
