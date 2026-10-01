import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:smart_ration_mobile/app/routes.dart';
import 'package:smart_ration_mobile/features/shop/scanner_screen.dart';
import 'package:smart_ration_mobile/features/shop/stock_screen.dart';

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
}
