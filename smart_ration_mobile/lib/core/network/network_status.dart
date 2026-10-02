import 'package:flutter_riverpod/flutter_riverpod.dart';

/// Whether the backend could be reached on the last request: any answer (even an error) means
/// online; no connection or a timeout means offline. Drives the "No internet" banner.
class NetworkStatus extends Notifier<bool> {
  @override
  bool build() => true;

  void reached(bool online) {
    if (state != online) state = online;
  }
}

final networkOnlineProvider = NotifierProvider<NetworkStatus, bool>(NetworkStatus.new);
