import 'package:flutter_test/flutter_test.dart';
import 'package:smart_ration_mobile/app/router.dart';
import 'package:smart_ration_mobile/app/routes.dart';
import 'package:smart_ration_mobile/features/auth/session.dart';

import '../support/test_app.dart';

SessionUser as(String role) => SessionUser(id: 1, fullName: 'X', email: 'x@example.com', mobileNumber: '1', role: AppRole.fromApi(role)!);

void main() {
  group('signed out', () {
    test('public screens open', () {
      for (final location in Routes.public) {
        expect(redirectFor(null, location), isNull, reason: location);
      }
    });

    test('every dashboard sends you to sign-in', () {
      for (final location in [Routes.citizenHome, Routes.shopHome, Routes.officialHome, '/shop/scanner']) {
        expect(redirectFor(null, location), Routes.login, reason: location);
      }
    });
  });

  group('signed in', () {
    test('the sign-in screen sends you to your own dashboard', () {
      expect(redirectFor(citizen(), Routes.login), Routes.citizenHome);
      expect(redirectFor(shopOwner(), Routes.login), Routes.shopHome);
      expect(redirectFor(as('GovernmentOfficial'), Routes.login), Routes.officialHome);
      expect(redirectFor(as('Admin'), Routes.login), Routes.officialHome);
    });

    test("another role's area sends you back to yours", () {
      expect(redirectFor(citizen(), Routes.shopHome), Routes.citizenHome);
      expect(redirectFor(citizen(), '/shop/scanner'), Routes.citizenHome);
      expect(redirectFor(shopOwner(), Routes.officialHome), Routes.shopHome);
      expect(redirectFor(as('GovernmentOfficial'), Routes.citizenHome), Routes.officialHome);
    });

    test('your own area and shared screens open', () {
      expect(redirectFor(citizen(), Routes.citizenHome), isNull);
      expect(redirectFor(shopOwner(), '/shop/scanner'), isNull);
      expect(redirectFor(citizen(), Routes.changeLanguage), isNull);
      expect(redirectFor(citizen(), Routes.serverStatus), isNull);
    });
  });

  test('an unknown role from the server is treated as signed out', () {
    expect(SessionUser.tryParse({'id': 1, 'role': 'SuperUser'}), isNull);
  });
}
