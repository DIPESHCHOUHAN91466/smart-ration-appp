import 'package:flutter_test/flutter_test.dart';
import 'package:smart_ration_mobile/app/env.dart';

void main() {
  group('Env.parse', () {
    test('development defaults to the PC as seen from the emulator', () {
      final env = Env.parse(environment: 'development', apiBaseUrl: '');
      expect(env.environment, AppEnvironment.development);
      expect(env.apiBaseUrl, 'http://10.0.2.2:8000');
      expect(env.isDevelopment, isTrue);
    });

    test('removes a trailing slash', () {
      expect(Env.parse(environment: 'development', apiBaseUrl: 'http://192.168.1.5:8000/').apiBaseUrl,
          'http://192.168.1.5:8000');
    });

    test('production accepts a public https address', () {
      final env = Env.parse(environment: 'production', apiBaseUrl: 'https://api.smartration.example.org');
      expect(env.environment, AppEnvironment.production);
      expect(env.isDevelopment, isFalse);
    });

    test('production and staging require an address', () {
      expect(() => Env.parse(environment: 'production', apiBaseUrl: ''), throwsArgumentError);
      expect(() => Env.parse(environment: 'staging', apiBaseUrl: ''), throwsArgumentError);
    });

    test('production refuses plain http', () {
      expect(() => Env.parse(environment: 'production', apiBaseUrl: 'http://api.smartration.example.org'),
          throwsArgumentError);
    });

    for (final local in [
      'https://localhost:8000',
      'https://127.0.0.1',
      'https://10.0.2.2:8000',
      'https://192.168.1.20',
      'https://172.16.0.4',
    ]) {
      test('production refuses the local address $local', () {
        expect(() => Env.parse(environment: 'production', apiBaseUrl: local), throwsArgumentError);
      });
    }

    test('rejects an unknown environment name', () {
      expect(() => Env.parse(environment: 'prod', apiBaseUrl: 'https://x.example.org'), throwsArgumentError);
    });

    test('rejects something that is not an address', () {
      expect(() => Env.parse(environment: 'development', apiBaseUrl: 'not a url'), throwsArgumentError);
    });
  });
}
