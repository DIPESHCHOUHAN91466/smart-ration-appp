import 'package:dio/dio.dart';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:qr_flutter/qr_flutter.dart';
import 'package:smart_ration_mobile/app/router.dart';
import 'package:smart_ration_mobile/app/routes.dart';
import 'package:smart_ration_mobile/features/citizen/citizen_home_screen.dart';

import '../support/fake_backend.dart';
import '../support/test_app.dart';

/// The demo citizen's backend plus notifications; [online] can be switched off to "unplug" it.
class Switchable {
  bool online = true;

  FakeReply handle(RequestOptions r) {
    if (!online) return const FakeReply.fails(DioExceptionType.connectionError);
    if (r.method == 'GET' && r.path == '/api/notifications') {
      return FakeReply.ok([
        {'id': 41, 'type': 'CollectionCompleted', 'title': 'Ration collected', 'message': 'Collection ID COL-DEMO-000042.',
            'isRead': false, 'createdAt': '2026-10-01T10:11:05.269655'},
        {'id': 40, 'type': 'BookingConfirmed', 'title': 'Booking confirmed', 'message': 'Token SR-2026-000501.',
            'isRead': false, 'createdAt': '2026-09-30T08:00:00'},
        {'id': 30, 'type': 'SystemAnnouncement', 'title': 'Welcome', 'message': 'Old news.', 'isRead': true,
            'createdAt': '2026-09-01T08:00:00'},
      ]);
    }
    if (r.path == '/api/notifications/read') return FakeReply.ok(null);
    return demoServer(r);
  }
}

Future<(TestApp, FakeBackend)> openCitizen(WidgetTester tester, Switchable server, {String language = 'en'}) async {
  tester.view.physicalSize = const Size(1080, 3200);
  tester.view.devicePixelRatio = 2.0;
  addTearDown(tester.view.reset);
  final backend = FakeBackend(server.handle);
  final app = await TestApp.build(backend, savedLanguage: language, signedInAs: citizen());
  await tester.pumpWidget(app.widget);
  await tester.pumpAndSettle();
  return (app, backend);
}

Future<void> go(WidgetTester tester, String path) async {
  containerOf(tester.element(find.byType(Scaffold).first)).read(routerProvider).push(path);
  await tester.pumpAndSettle();
}

void main() {
  testWidgets("pulling the dashboard down reloads the tokens and notifications too", (tester) async {
    final (_, backend) = await openCitizen(tester, Switchable());
    int count(String path) => backend.requests.where((r) => r.method == 'GET' && r.path == path).length;
    final tokensBefore = count('/api/ration/bookings');
    final notificationsBefore = count('/api/notifications');

    await tester.fling(find.textContaining('Namaste'), const Offset(0, 400), 1000);   // from the top of the page
    await tester.pumpAndSettle();
    expect(count('/api/ration/bookings'), tokensBefore + 1);
    expect(count('/api/notifications'), notificationsBefore + 1);
  });

  testWidgets("pulling down also works when the finger starts on a menu button", (tester) async {
    final (_, backend) = await openCitizen(tester, Switchable());
    int count() => backend.requests.where((r) => r.method == 'GET' && r.path == '/api/ration/bookings').length;
    final before = count();
    await tester.fling(find.text('Booking history'), const Offset(0, 900), 1000);
    await tester.pumpAndSettle();
    expect(count(), before + 1);
  });

  group('notifications', () {
    testWidgets('the bell counts unread ones; opening the list shows them and marks them read', (tester) async {
      final (_, backend) = await openCitizen(tester, Switchable());

      expect(find.byTooltip('Notifications, 2 new'), findsOneWidget);
      await tester.tap(find.byTooltip('Notifications, 2 new'));
      await tester.pumpAndSettle();

      expect(find.text('Ration collected'), findsOneWidget);
      expect(find.text('Booking confirmed'), findsOneWidget);
      expect(find.text('Announcement'), findsOneWidget);
      expect(find.text('New'), findsNWidgets(2));
      expect(backend.requests.singleWhere((r) => r.path == '/api/notifications/read').data, {
        'notificationIds': [41, 40],
      });
    });

    testWidgets('in Hindi the kinds are translated and the English message is labelled', (tester) async {
      await openCitizen(tester, Switchable(), language: 'hi');
      await tester.tap(find.byTooltip('सूचनाएँ, 2 नई'));
      await tester.pumpAndSettle();
      expect(find.text('राशन मिल गया'), findsOneWidget);
      expect(find.text('सिस्टम का विवरण (अंग्रेज़ी में):'), findsNWidgets(3));
    });
  });

  group('offline', () {
    testWidgets('no internet: a banner, and the token QR from the copy saved on the phone', (tester) async {
      final server = Switchable();
      final (_, backend) = await openCitizen(tester, server);
      // The dashboard's token list saved the upcoming token's QR in the background.
      expect(backend.paths, contains('/api/qr/payload/501'));
      expect(find.byIcon(Icons.wifi_off), findsNothing);

      server.online = false;
      await go(tester, Routes.citizenToken(501));

      expect(find.byIcon(Icons.wifi_off), findsOneWidget);
      expect(find.textContaining('No internet. Showing what was saved on this phone'), findsOneWidget);
      expect(find.text('SR-2026-000501'), findsOneWidget);
      expect(find.byType(QrImageView), findsOneWidget);
      expect(find.text('Saved on this phone. The shop can still scan this QR without your internet.'), findsOneWidget);
    });

    testWidgets('no internet and nothing saved: says so plainly', (tester) async {
      final server = Switchable()..online = false;
      await openCitizen(tester, server);
      expect(find.byIcon(Icons.wifi_off), findsOneWidget);
      expect(find.textContaining('Unable to connect'), findsWidgets);
    });

    testWidgets('back online: the banner goes after the next successful request', (tester) async {
      final server = Switchable();
      await openCitizen(tester, server);
      server.online = false;
      await go(tester, Routes.citizenToken(501));
      expect(find.byIcon(Icons.wifi_off), findsOneWidget);

      server.online = true;
      await tester.fling(find.byType(ListView).first, const Offset(0, 400), 1000); // pull to refresh
      await tester.pumpAndSettle();
      expect(find.byIcon(Icons.wifi_off), findsNothing);
      expect(find.text('Saved on this phone. The shop can still scan this QR without your internet.'), findsNothing);
    });

    testWidgets('a different person on the same phone never sees the saved copy, and signing out wipes it', (tester) async {
      final (app, _) = await openCitizen(tester, Switchable());
      expect(app.offline.values.keys, everyElement(startsWith('u7.')));
      expect(app.offline.values, isNotEmpty);

      await tester.tap(find.byTooltip('Sign out'));
      await tester.pumpAndSettle();
      expect(app.offline.values, isEmpty);
      expect(find.byType(CitizenHomeScreen), findsNothing);
    });
  });
}
