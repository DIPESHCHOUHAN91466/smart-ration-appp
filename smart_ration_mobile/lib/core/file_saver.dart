import 'package:flutter/services.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

/// "Save as" for a file the app made. The person picks where it goes (Android's own file picker), so the app
/// needs no storage permission and keeps no copy. Tests replace this with a fake.
abstract interface class FileSaver {
  /// True once saved; false if the person closed the picker without saving. Throws if the write failed.
  Future<bool> save({required String name, required String mimeType, required Uint8List bytes});
}

/// Uses the native handler in MainActivity.kt.
class AndroidFileSaver implements FileSaver {
  const AndroidFileSaver();

  static const _channel = MethodChannel('smart_ration/files');

  @override
  Future<bool> save({required String name, required String mimeType, required Uint8List bytes}) async =>
      await _channel.invokeMethod<bool>('saveDocument', {'name': name, 'mimeType': mimeType, 'bytes': bytes}) ?? false;
}

final fileSaverProvider = Provider<FileSaver>((ref) => const AndroidFileSaver());
