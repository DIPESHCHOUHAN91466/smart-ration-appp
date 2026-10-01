import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../features/server_status/server_status_screen.dart';

/// The list of screens and their addresses. Splash, login and the role dashboards are added in later
/// milestones; the login check (redirect) goes here too.
final routerProvider = Provider<GoRouter>((ref) => GoRouter(
      initialLocation: '/',
      routes: [
        GoRoute(path: '/', builder: (context, state) => const ServerStatusScreen()),
      ],
    ));
