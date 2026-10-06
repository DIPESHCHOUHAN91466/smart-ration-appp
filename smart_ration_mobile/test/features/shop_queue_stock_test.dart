import 'package:dio/dio.dart';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:smart_ration_mobile/app/routes.dart';
import 'package:smart_ration_mobile/features/shop/scanner_screen.dart';
import 'package:smart_ration_mobile/features/shop/stock_screen.dart';

import '../support/fake_backend.dart';
import 'shop_test.dart' show openShop, tapText;

void main() {
  testWidgets('the dashboard warns about low stock and opens the stock screen', (tester) async {
    await openShop(tester);

    expect(find.text('1 item is low on stock'), findsOneWidget);
    expect(find.text("Today's queue"), findsOneWidget);
    await tapText(tester, '1 item is low on stock');
    expect(find.byType(StockScreen), findsOneWidget);
  });

  testWidgets('the queue: who is waiting, who is done, and serving only through QR or mobile code', (tester) async {
    await openShop(tester, path: Routes.shopQueue);

    expect(find.text('Waiting (1)'), findsOneWidget);
    expect(find.text('Done (1)'), findsOneWidget);
    expect(find.text('Asha Devi'), findsOneWidget);
    expect(find.text('Mohan Lal'), findsOneWidget);
    expect(find.text('Collected'), findsOneWidget);

    // A customer already served can't be opened again.
    await tapText(tester, 'Mohan Lal');
    expect(find.text('When this customer arrives, scan their QR or verify by mobile code.'), findsNothing);

    await tapText(tester, 'Asha Devi');
    expect(find.text('When this customer arrives, scan their QR or verify by mobile code.'), findsOneWidget);
    expect(find.textContaining('collected', findRichText: true), findsNothing); // no "mark collected" shortcut
    await tapText(tester, "Scan customer's QR");
    expect(find.byType(ScannerScreen), findsOneWidget);
  });

  testWidgets('stock: low items first, and a delivery is recorded with its number', (tester) async {
    final backend = await openShop(tester, path: Routes.shopStock);

    // Salt (low) is listed before rice.
    expect(tester.getTopLeft(find.text('Salt')).dy, lessThan(tester.getTopLeft(find.text('Rice')).dy));
    expect(find.text('Low'), findsOneWidget);
    expect(find.text('480 kg'), findsOneWidget);

    await tester.tap(find.text('Record delivery').last); // rice
    await tester.pumpAndSettle();
    await tester.enterText(find.byType(TextField).at(0), '0');
    await tapText(tester, 'Save');
    expect(find.text('Enter a quantity greater than 0.'), findsOneWidget);

    await tester.enterText(find.byType(TextField).at(0), '50');
    await tester.enterText(find.byType(TextField).at(1), 'DC#14');
    await tapText(tester, 'Save');
    expect(find.text('Use only letters, numbers, spaces and - / _ .'), findsOneWidget);
    expect(backend.requests.where((r) => r.method == 'POST'), isEmpty);

    await tester.enterText(find.byType(TextField).at(1), 'DC-2026/14');
    await tapText(tester, 'Save');
    expect(backend.requests.singleWhere((r) => r.path == '/api/inventory/11/receive').data, {'quantity': 50.0, 'reference': 'DC-2026/14'});
    expect(find.text('Delivery recorded.'), findsOneWidget);
  });

  group('correcting a count', () {
    /// The shop backend plus PUT /api/inventory/{id}, answering with the corrected line like the real one.
    FakeReply correctingServer(RequestOptions r) {
      if (r.method == 'PUT' && r.path == '/api/inventory/11') {
        final body = r.data as Map;
        return FakeReply.ok({...stockJson().first, 'availableQuantity': body['availableQuantity'], 'minimumStockLevel': body['minimumStockLevel']});
      }
      return shopServer(r);
    }

    List<RequestOptions> puts(FakeBackend b) => b.requests.where((r) => r.method == 'PUT').toList();

    testWidgets('a new balance is confirmed (from and to) before it is sent', (tester) async {
      final backend = await openShop(tester, path: Routes.shopStock, handler: correctingServer);
      await tester.tap(find.text('Correct count').last); // rice
      await tester.pumpAndSettle();

      expect(find.textContaining('Only to fix a counting mistake.'), findsOneWidget);
      expect(find.widgetWithText(TextField, '480'), findsOneWidget);
      expect(find.widgetWithText(TextField, '100'), findsOneWidget);

      await tester.enterText(find.byType(TextField).at(0), '470.5');
      await tapText(tester, 'Save');
      expect(find.text('Change Rice in stock from 480 kg to 470.5 kg?'), findsOneWidget);
      await tester.tap(find.text('Cancel'));
      await tester.pumpAndSettle();
      expect(puts(backend), isEmpty);

      await tapText(tester, 'Save');
      await tester.tap(find.widgetWithText(FilledButton, 'Save').last);
      await tester.pumpAndSettle();
      expect(puts(backend).single.data, {'availableQuantity': 470.5, 'minimumStockLevel': 100.0});
      expect(find.text('Stock corrected.'), findsOneWidget);
    });

    testWidgets('only the minimum level changed: no confirmation needed', (tester) async {
      final backend = await openShop(tester, path: Routes.shopStock, handler: correctingServer);
      await tester.tap(find.text('Correct count').last);
      await tester.pumpAndSettle();

      await tester.enterText(find.byType(TextField).at(1), '150');
      await tapText(tester, 'Save');
      expect(find.byType(AlertDialog), findsNothing);
      expect(puts(backend).single.data, {'availableQuantity': 480.0, 'minimumStockLevel': 150.0});
    });

    testWidgets('nothing changed, or numbers that cannot be used: nothing is sent', (tester) async {
      final backend = await openShop(tester, path: Routes.shopStock, handler: correctingServer);
      await tester.tap(find.text('Correct count').last);
      await tester.pumpAndSettle();

      await tapText(tester, 'Save');
      expect(find.text('Nothing was changed.'), findsOneWidget);

      await tester.enterText(find.byType(TextField).at(0), '');
      await tester.enterText(find.byType(TextField).at(1), '2000000');
      await tapText(tester, 'Save');
      expect(find.text('Enter a number, 0 or more.'), findsOneWidget);
      expect(find.text('Enter a quantity up to 1,000,000.'), findsOneWidget);
      expect(puts(backend), isEmpty);
    });

    testWidgets('a count of zero is allowed', (tester) async {
      final backend = await openShop(tester, path: Routes.shopStock, handler: correctingServer);
      await tester.tap(find.text('Correct count').last);
      await tester.pumpAndSettle();
      await tester.enterText(find.byType(TextField).at(0), '0');
      await tapText(tester, 'Save');
      await tester.tap(find.widgetWithText(FilledButton, 'Save').last);
      await tester.pumpAndSettle();
      expect(puts(backend).single.data, {'availableQuantity': 0.0, 'minimumStockLevel': 100.0});
    });
  });

  testWidgets('writing off damaged stock: never more than is in stock, and only after confirming', (tester) async {
    final backend = await openShop(tester, path: Routes.shopStock);
    Iterable<Object?> writeOffs() => backend.requests.where((r) => r.path == '/api/inventory/12/damage').map((r) => r.data);

    await tester.tap(find.text('Write off damaged').first); // salt, 3.5 kg in stock
    await tester.pumpAndSettle();
    await tester.enterText(find.byType(TextField).at(0), '5');
    await tapText(tester, 'Save');
    expect(find.text('You can write off at most 3.5 kg.'), findsOneWidget);

    await tester.enterText(find.byType(TextField).at(0), '1,5'); // a comma works as the decimal point too
    await tapText(tester, 'Save');
    expect(find.text('Write off 1.5 kg Salt?'), findsOneWidget);
    await tapText(tester, 'Cancel');
    expect(writeOffs(), isEmpty);

    await tapText(tester, 'Save');
    await tester.tap(find.widgetWithText(FilledButton, 'Write off damaged').last);
    await tester.pumpAndSettle();
    expect(writeOffs().single, {'quantity': 1.5});
    expect(find.text('Damaged stock written off.'), findsOneWidget);
  });

  group('a stock change is recorded once', () {
    String keyOf(RequestOptions r) => r.headers['Idempotency-Key'] as String;

    testWidgets('a retry after a lost answer sends the same request key; a new form uses a new one', (tester) async {
      var calls = 0;
      final backend = await openShop(tester, path: Routes.shopStock, handler: (r) {
        if (r.path == '/api/inventory/11/receive' && ++calls == 1) return const FakeReply.fails(DioExceptionType.receiveTimeout);
        return shopServer(r);
      });
      List<RequestOptions> deliveries() => backend.requests.where((r) => r.path == '/api/inventory/11/receive').toList();

      await tester.tap(find.text('Record delivery').last); // rice
      await tester.pumpAndSettle();
      await tester.enterText(find.byType(TextField).at(0), '50');
      await tapText(tester, 'Save');
      expect(find.text('Delivery recorded.'), findsNothing); // the answer was lost; the form stays open
      await tapText(tester, 'Save');
      expect(find.text('Delivery recorded.'), findsOneWidget);

      expect(deliveries(), hasLength(2));
      expect(keyOf(deliveries()[0]), matches(RegExp(r'^[0-9a-f]{32}$')));
      expect(keyOf(deliveries()[1]), keyOf(deliveries()[0]));

      await tester.tap(find.text('Record delivery').last);
      await tester.pumpAndSettle();
      await tester.enterText(find.byType(TextField).at(0), '10');
      await tapText(tester, 'Save');
      expect(deliveries(), hasLength(3));
      expect(keyOf(deliveries()[2]), isNot(keyOf(deliveries()[0])));
    });

    testWidgets('if the key was already used, the shopkeeper is told it was saved and to check the stock', (tester) async {
      await openShop(tester, path: Routes.shopStock, handler: (r) {
        if (r.path == '/api/inventory/11/receive') {
          return const FakeReply(409, {'success': false, 'message': 'This request key was already used for a different stock change.',
              'errorCode': 'IDEMPOTENCY_KEY_REUSED', 'data': null, 'errors': null});
        }
        return shopServer(r);
      });

      await tester.tap(find.text('Record delivery').last);
      await tester.pumpAndSettle();
      await tester.enterText(find.byType(TextField).at(0), '50');
      await tapText(tester, 'Save');
      expect(find.text('This was already saved a moment ago. Close this form and check the stock before entering it again.'),
          findsOneWidget);
      expect(find.text('Delivery recorded.'), findsNothing);
    });
  });
}
