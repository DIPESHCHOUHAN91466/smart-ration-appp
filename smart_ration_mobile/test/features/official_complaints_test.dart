import 'package:dio/dio.dart';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:smart_ration_mobile/app/routes.dart';

import '../support/fake_backend.dart';
import '../support/fake_grievance.dart';
import 'official_test.dart' show openOfficial;

/// The officials' complaint list, behaving like the real /api/grievances routes: filtered by ?status=,
/// newest first, and POST .../status moving one complaint and replacing its reply.
FakeReply Function(RequestOptions) complaintsBackend({FakeReply? updateReply}) {
  final rows = [
    complaintJson(3, 'ShopClosed', 'The shop was closed on the distribution day.'),
    complaintJson(2, 'LessRation', 'This month I got 2 kg less wheat.', rationType: 'Wheat', status: 'UnderReview',
        reply: 'Asked the shop owner.'),
    complaintJson(1, 'Overcharged', 'They took 10 rupees extra for sugar.', status: 'Resolved', reply: 'Money returned.'),
  ];
  return (r) {
    final m = RegExp(r'^/api/grievances/(\d+)/status$').firstMatch(r.path);
    if (m != null && r.method == 'POST') {
      if (updateReply != null) return updateReply;
      final row = rows.firstWhere((c) => c['id'] == int.parse(m.group(1)!));
      final body = r.data as Map;
      row['status'] = body['Status'];
      row['resolutionNote'] = body['Note'];
      return FakeReply.ok(row);
    }
    if (r.path == '/api/grievances' && r.method == 'GET') {
      final only = r.queryParameters['status'];
      return FakeReply.ok([for (final c in rows) if (only == null || c['status'] == only) c]);
    }
    return officialServer(r);
  };
}

void main() {
  testWidgets('the dashboard leads to the complaints, which open on the new ones', (tester) async {
    final backend = await openOfficial(tester, server: complaintsBackend());

    await tester.tap(find.text('Citizen complaints'));
    await tester.pumpAndSettle();

    expect(backend.requests.last.queryParameters, {'status': 'Submitted'});
    expect(find.text('Shop was closed'), findsOneWidget);
    expect(find.text('GRV-2026-000003'), findsOneWidget);
    expect(find.text('Satnavari Ration Shop'), findsOneWidget);
    expect(find.text('Got less ration'), findsNothing); // being checked, not new
  });

  testWidgets('"All" shows every complaint; finished ones cannot be updated', (tester) async {
    final backend = await openOfficial(tester, path: Routes.officialComplaints, server: complaintsBackend());

    await tester.tap(find.widgetWithText(ChoiceChip, 'All'));
    await tester.pumpAndSettle();

    expect(backend.requests.last.queryParameters, isEmpty);
    expect(find.text('GRV-2026-000001'), findsOneWidget);
    expect(find.text('Money returned.'), findsOneWidget);
    expect(find.text('Update'), findsNWidgets(2)); // the resolved one has no button
  });

  testWidgets('marking a new complaint "being checked" sends the status and the trimmed reply', (tester) async {
    final backend = await openOfficial(tester, path: Routes.officialComplaints, server: complaintsBackend());

    await tester.tap(find.text('Update'));
    await tester.pumpAndSettle();
    expect(find.text('Update this complaint'), findsOneWidget);
    expect(find.text('The citizen sees this reply. Do not write Aadhaar numbers, OTPs or passwords.'), findsOneWidget);

    await tester.enterText(find.widgetWithText(TextField, 'Reply to the citizen (optional)'), '  We will visit the shop.  ');
    await tester.tap(find.text('Save'));
    await tester.pumpAndSettle();

    final sent = backend.requests.singleWhere((r) => r.method == 'POST');
    expect(sent.path, '/api/grievances/3/status');
    expect(sent.data, {'Status': 'UnderReview', 'Note': 'We will visit the shop.'});
    expect(find.text('Complaint updated'), findsOneWidget);
    expect(find.text('Shop was closed'), findsNothing); // no longer new
  });

  testWidgets('a complaint being checked can be resolved or closed, not sent back; its reply is kept', (tester) async {
    final backend = await openOfficial(tester, path: Routes.officialComplaints, server: complaintsBackend());
    await tester.tap(find.widgetWithText(ChoiceChip, 'Being checked'));
    await tester.pumpAndSettle();

    await tester.tap(find.text('Update'));
    await tester.pumpAndSettle();
    expect(find.text('You are checking it. The citizen is told.'), findsNothing);
    expect(find.widgetWithText(TextField, 'Asked the shop owner.'), findsOneWidget);

    await tester.tap(find.text('No action can be taken. Say why in the reply.'));
    await tester.tap(find.text('Save'));
    await tester.pumpAndSettle();

    expect(backend.requests.singleWhere((r) => r.method == 'POST').data, {'Status': 'Rejected', 'Note': 'Asked the shop owner.'});
  });

  testWidgets('an Aadhaar-like number in the reply is stopped before sending', (tester) async {
    final backend = await openOfficial(tester, path: Routes.officialComplaints, server: complaintsBackend());
    await tester.tap(find.text('Update'));
    await tester.pumpAndSettle();

    await tester.enterText(find.byType(TextField), 'Card 1234 5678 9012 checked');
    await tester.tap(find.text('Save'));
    await tester.pumpAndSettle();

    expect(find.text('Do not write Aadhaar numbers, OTPs or passwords.'), findsOneWidget);
    expect(backend.requests.where((r) => r.method == 'POST'), isEmpty);
  });

  testWidgets("the backend's refusal is shown in the form, which stays open", (tester) async {
    await openOfficial(tester,
        path: Routes.officialComplaints,
        server: complaintsBackend(
            updateReply: const FakeReply(400, {
          'success': false, 'message': 'Remove private data.', 'errorCode': 'SENSITIVE_DATA', 'data': null, 'errors': null,
        })));
    await tester.tap(find.text('Update'));
    await tester.pumpAndSettle();
    await tester.tap(find.text('Save'));
    await tester.pumpAndSettle();

    expect(find.text('Do not write Aadhaar numbers, OTPs or passwords.'), findsOneWidget);
    expect(find.text('Update this complaint'), findsOneWidget);
    expect(find.text('Complaint updated'), findsNothing);
  });
}
