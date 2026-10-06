import 'package:dio/dio.dart';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:smart_ration_mobile/app/router.dart';
import 'package:smart_ration_mobile/app/routes.dart';
import 'package:smart_ration_mobile/features/auth/session.dart';
import 'package:smart_ration_mobile/features/grievance/grievance_data.dart';
import 'package:smart_ration_mobile/features/help/voice.dart';
import 'package:smart_ration_mobile/features/shop/scanner_screen.dart';
import 'package:smart_ration_mobile/features/shop/shop_data.dart';

import '../support/fake_backend.dart';
import '../support/fake_help.dart';
import '../support/fake_grievance.dart';
import '../support/test_app.dart';

/// Release check: every main screen, in every language, on a small low-cost phone (360 x 640) with
/// large text (130 %), must lay out without overflowing (Flutter reports overflow as an error).

class _SilentVoice implements VoiceInput {
  @override
  Future<bool> start({required String language, required void Function(String, bool) onWords, required void Function() onStopped}) async =>
      false;

  @override
  Future<void> stop() async {}
}

class _SilentSpeaker implements Speaker {
  @override
  Future<bool> speak(String text, String language) async => false;

  @override
  Future<void> stop() async {}
}

/// One fake backend for all three roles.
FakeReply everything(RequestOptions r) {
  final p = r.path;
  if (p.startsWith('/api/chatbot')) return helpServer(r);
  if (p == '/api/grievances/mine') {
    return FakeReply.ok([complaintJson(1, 'LessRation', 'This month I got 2 kg less wheat.', rationType: 'Wheat', status: 'UnderReview',
        reply: 'The shop owner has been asked to explain.')]);
  }
  if (p == '/api/grievances' && r.method == 'GET') {
    return FakeReply.ok([complaintJson(2, 'StaffBehaviour', 'The shop keeper shouted at my mother and sent her home.',
        status: 'Submitted')]);
  }
  if (p == '/api/notifications') {
    return FakeReply.ok([
      {'id': 1, 'type': 'CollectionCompleted', 'title': 'Ration collected', 'message': 'Collection ID COL-DEMO-000042.',
          'isRead': false, 'createdAt': '2026-10-01T10:11:05'},
    ]);
  }
  if (p.startsWith('/api/shop/') || p.startsWith('/api/inventory') || p == '/api/qr/scan' || p.startsWith('/api/verification')) {
    return shopServer(r);
  }
  if (p.startsWith('/api/admin') || p.startsWith('/api/shops') || p.startsWith('/api/ai')) return officialServer(r);
  return demoServer(r);
}

SessionUser official() => SessionUser.tryParse(userJson(id: 4, fullName: 'District Government Officer', role: 'GovernmentOfficial'))!;

/// (who is signed in, where to go, what the screen needs passed to it)
final screens = <(String, SessionUser? Function(), String, Object? Function())>[
  ('signed out', () => null, Routes.login, () => null),
  ('signed out', () => null, Routes.help, () => null),
  ('signed out', () => null, Routes.forgotPassword, () => null),
  ('citizen', citizen, Routes.changePassword, () => null),
  ('official', official, Routes.changePassword, () => null),
  ('citizen', citizen, Routes.citizenHome, () => null),
  ('citizen', citizen, Routes.citizenFamily, () => null),
  ('citizen', citizen, Routes.citizenCard, () => null),
  ('citizen', citizen, Routes.citizenEligibility, () => null),
  ('citizen', citizen, Routes.citizenBook, () => null),
  ('citizen', citizen, Routes.citizenTokens, () => null),
  ('citizen', citizen, Routes.citizenToken(501), () => null),
  ('citizen', citizen, Routes.notifications, () => null),
  ('citizen', citizen, Routes.citizenComplaint, () => null),
  ('citizen', citizen, Routes.citizenComplaint,
      () => ComplaintDraft.fromAssistantFields({'category': 'StaffBehaviour', 'rationType': 'EdibleOil', 'description': 'The shop owner shouted at my mother.'})),
  ('citizen', citizen, Routes.citizenComplaints, () => null),
  ('shop', shopOwner, Routes.shopHome, () => null),
  ('shop', shopOwner, Routes.shopScan, () => null),
  ('shop', shopOwner, Routes.shopOtp, () => null),
  ('shop', shopOwner, Routes.shopCheck, () => CustomerCheck.tryParse(verificationJson(), CheckMethod.qr)),
  ('shop', shopOwner, Routes.shopCheck, () => CustomerCheck.tryParse(verificationJson(ready: false, reason: 'Mobile OTP verification required.'), CheckMethod.otp)),
  ('shop', shopOwner, Routes.shopReceipt, () => Receipt.parse(receiptJson())),
  ('shop', shopOwner, Routes.shopQueue, () => null),
  ('shop', shopOwner, Routes.shopStock, () => null),
  ('official', official, Routes.officialHome, () => null),
  ('official', official, Routes.officialShops, () => null),
  ('official', official, Routes.officialShop(1), () => null),
  ('official', official, Routes.officialAlerts, () => null),
  ('official', official, Routes.officialComplaints, () => null),
];

void main() {
  for (final language in ['en', 'hi', 'mr']) {
    for (final (who, user, path, extra) in screens) {
      testWidgets('$language · $who · $path fits a small phone with large text', (tester) async {
        tester.view.physicalSize = const Size(720, 1280);
        tester.view.devicePixelRatio = 2.0;
        tester.platformDispatcher.textScaleFactorTestValue = 1.3;
        addTearDown(tester.view.reset);
        addTearDown(tester.platformDispatcher.clearTextScaleFactorTestValue);

        final app = await TestApp.build(FakeBackend(everything), savedLanguage: language, signedInAs: user(), overrides: [
          cameraViewProvider.overrideWithValue((context, onCode) => const ColoredBox(color: Colors.black)),
          voiceInputProvider.overrideWithValue(_SilentVoice()),
          speakerProvider.overrideWithValue(_SilentSpeaker()),
        ]);
        await tester.pumpWidget(app.widget);
        await tester.pumpAndSettle();
        containerOf(tester.element(find.byType(Scaffold).first)).read(routerProvider).push(path, extra: extra());
        await tester.pumpAndSettle();

        expect(tester.takeException(), isNull, reason: '$language $path');
        expect(find.byType(Scaffold), findsWidgets);
      });
    }

    for (final (who, user) in [('citizen', citizen), ('shop', shopOwner), ('official', official)]) {
      testWidgets('$language · $who · the AI assistant fits a small phone with large text', (tester) async {
        tester.view.physicalSize = const Size(720, 1280);
        tester.view.devicePixelRatio = 2.0;
        tester.platformDispatcher.textScaleFactorTestValue = 1.3;
        addTearDown(tester.view.reset);
        addTearDown(tester.platformDispatcher.clearTextScaleFactorTestValue);

        final app = await TestApp.build(FakeBackend(everything), savedLanguage: language, signedInAs: user(), overrides: [
          voiceInputProvider.overrideWithValue(_SilentVoice()),
          speakerProvider.overrideWithValue(_SilentSpeaker()),
        ]);
        await tester.pumpWidget(app.widget);
        await tester.pumpAndSettle();
        await tester.tap(find.byIcon(Icons.auto_awesome));
        await tester.pumpAndSettle();

        expect(tester.takeException(), isNull, reason: '$language $who assistant');
        expect(find.byIcon(Icons.mic), findsOneWidget);
      });
    }

    testWidgets('$language · official · the alert update form fits a small phone with large text', (tester) async {
      tester.view.physicalSize = const Size(720, 1280);
      tester.view.devicePixelRatio = 2.0;
      tester.platformDispatcher.textScaleFactorTestValue = 1.3;
      addTearDown(tester.view.reset);
      addTearDown(tester.platformDispatcher.clearTextScaleFactorTestValue);

      final app = await TestApp.build(FakeBackend(everything), savedLanguage: language, signedInAs: official());
      await tester.pumpWidget(app.widget);
      await tester.pumpAndSettle();
      containerOf(tester.element(find.byType(Scaffold).first)).read(routerProvider).push(Routes.officialAlerts);
      await tester.pumpAndSettle();
      await tester.ensureVisible(find.byIcon(Icons.edit_note).first); // below the fold on a small phone
      await tester.pumpAndSettle();
      await tester.tap(find.byIcon(Icons.edit_note).first);
      await tester.pumpAndSettle();

      expect(tester.takeException(), isNull, reason: '$language alert update form');
      expect(find.byType(TextField), findsOneWidget); // the form is open
    });

    testWidgets('$language · official · the complaint update form fits a small phone with large text', (tester) async {
      tester.view.physicalSize = const Size(720, 1280);
      tester.view.devicePixelRatio = 2.0;
      tester.platformDispatcher.textScaleFactorTestValue = 1.3;
      addTearDown(tester.view.reset);
      addTearDown(tester.platformDispatcher.clearTextScaleFactorTestValue);

      final app = await TestApp.build(FakeBackend(everything), savedLanguage: language, signedInAs: official());
      await tester.pumpWidget(app.widget);
      await tester.pumpAndSettle();
      containerOf(tester.element(find.byType(Scaffold).first)).read(routerProvider).push(Routes.officialComplaints);
      await tester.pumpAndSettle();
      await tester.ensureVisible(find.byIcon(Icons.edit_note).first);
      await tester.pumpAndSettle();
      await tester.tap(find.byIcon(Icons.edit_note).first);
      await tester.pumpAndSettle();

      expect(tester.takeException(), isNull, reason: '$language complaint update form');
      expect(find.byType(TextField), findsOneWidget);
    });
  }
}
