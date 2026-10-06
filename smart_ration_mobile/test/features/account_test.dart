import 'dart:convert';

import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:smart_ration_mobile/core/file_saver.dart';
import 'package:smart_ration_mobile/features/account/account_screen.dart';
import 'package:smart_ration_mobile/features/auth/session.dart';

import '../support/fake_backend.dart';
import '../support/test_app.dart';

/// Records what would be saved; [answer] plays the person's choice in the file picker.
class FakeSaver implements FileSaver {
  FakeSaver([this.answer = _saved]);

  static Future<bool> _saved() async => true;

  final Future<bool> Function() answer;
  final saves = <(String, String, Uint8List)>[];

  @override
  Future<bool> save({required String name, required String mimeType, required Uint8List bytes}) {
    saves.add((name, mimeType, bytes));
    return answer();
  }
}

const exportData = {
  'format': 'smart-ration-personal-data',
  'account': {'FullName': 'Asha Devi', 'Email': 'asha@example.com'},
  'bookings': [],
};

Future<TestApp> openAccount(WidgetTester tester, FakeBackend backend, FakeSaver saver, {String language = 'en', SessionUser? user}) async {
  final app = await TestApp.build(backend,
      savedLanguage: language, signedInAs: user ?? citizen(), overrides: [fileSaverProvider.overrideWithValue(saver)]);
  await tester.pumpWidget(app.widget);
  await tester.pumpAndSettle();
  await tester.tap(find.byIcon(Icons.manage_accounts));
  await tester.pumpAndSettle();
  return app;
}

/// The export card is last on My account, below the screen's edge: scroll the page (the first Scrollable) to it.
Future<void> scrollTo(WidgetTester tester, Finder target) async {
  await tester.scrollUntilVisible(target, 200, scrollable: find.byType(Scrollable).first);
  await tester.pumpAndSettle();
}

Future<void> tapDownload(WidgetTester tester, String label) async {
  await scrollTo(tester, find.text(label));
  await tester.tap(find.text(label));
  await tester.pumpAndSettle();
}

void main() {
  test('the file is named after the day, like on the website', () {
    expect(exportFileName(DateTime(2026, 3, 7, 23, 59)), 'smart-ration-my-data-2026-03-07.json');
  });

  testWidgets('"Download my data" saves the export as a JSON file where the person chooses', (tester) async {
    final backend = FakeBackend((r) => r.path == '/api/users/me/export' ? FakeReply.ok(exportData) : demoServer(r));
    final saver = FakeSaver();
    await openAccount(tester, backend, saver);
    expect(find.text('My account'), findsOneWidget);

    await tapDownload(tester, 'Download my data (JSON)');

    expect(backend.requests.where((r) => r.path == '/api/users/me/export'), hasLength(1));
    final (name, mime, bytes) = saver.saves.single;
    expect(name, startsWith('smart-ration-my-data-'));
    expect(mime, 'application/json');
    expect(jsonDecode(utf8.decode(bytes)), exportData);
    expect(find.text('Your data has been saved.'), findsOneWidget);
  });

  testWidgets('closing the file picker saves nothing and says nothing', (tester) async {
    final backend = FakeBackend((r) => r.path == '/api/users/me/export' ? FakeReply.ok(exportData) : demoServer(r));
    final saver = FakeSaver(() async => false);
    await openAccount(tester, backend, saver);
    await tapDownload(tester, 'Download my data (JSON)');

    expect(saver.saves, hasLength(1));
    expect(find.text('Your data has been saved.'), findsNothing);
    expect(find.text('Could not prepare your data. Please try again.'), findsNothing);
    expect(find.text('Download my data (JSON)'), findsOneWidget);   // ready to try again
  });

  testWidgets('a refused request is shown and nothing is saved', (tester) async {
    final backend = FakeBackend((r) => r.path == '/api/users/me/export'
        ? const FakeReply(429, {'success': false, 'message': 'Too many requests.', 'data': null})
        : demoServer(r));
    final saver = FakeSaver();
    await openAccount(tester, backend, saver);
    await tapDownload(tester, 'Download my data (JSON)');
    expect(saver.saves, isEmpty);
    expect(find.text('Your data has been saved.'), findsNothing);
    expect(find.byType(SnackBar), findsNothing);
    expect(find.text('Download my data (JSON)'), findsOneWidget);
  });

  testWidgets('a failed write is shown, and nothing half-done is claimed', (tester) async {
    final failing = FakeSaver(() async => throw PlatformException(code: 'WRITE_FAILED'));
    await openAccount(tester, FakeBackend((r) => r.path == '/api/users/me/export' ? FakeReply.ok(exportData) : demoServer(r)), failing);
    await tapDownload(tester, 'Download my data (JSON)');
    expect(find.text('Could not prepare your data. Please try again.'), findsOneWidget);
    expect(find.text('Your data has been saved.'), findsNothing);
  });

  testWidgets('My account is translated', (tester) async {
    await openAccount(tester, FakeBackend(demoServer), FakeSaver(), language: 'hi');
    expect(find.text('मेरा खाता'), findsOneWidget);
    await scrollTo(tester, find.text('मेरा डेटा डाउनलोड करें (JSON)'));
    expect(find.text('मेरा डेटा डाउनलोड करें (JSON)'), findsOneWidget);
  });
}
