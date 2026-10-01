import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../app/routes.dart';
import '../../app/theme.dart';
import '../../l10n/app_localizations.dart';
import '../auth/auth_controller.dart';
import '../auth/session.dart';

/// The signed-in home for every role. Each milestone after M4 fills in its own role's dashboard.
class RoleHomeScreen extends ConsumerWidget {
  const RoleHomeScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final l = AppLocalizations.of(context);
    final user = ref.watch(authControllerProvider);
    // Signed out a moment ago: the router is already moving to the sign-in screen.
    if (user == null) return const Scaffold(body: SizedBox.shrink());

    final (roleName, intro, icon) = switch (user.role) {
      AppRole.ruralUser => (l.roleRuralUser, l.citizenDashboardIntro, Icons.family_restroom),
      AppRole.shopOwner => (l.roleShopOwner, l.shopDashboardIntro, Icons.storefront),
      AppRole.governmentOfficial => (l.roleOfficial, l.officialDashboardIntro, Icons.account_balance),
      AppRole.admin => (l.roleAdmin, l.officialDashboardIntro, Icons.admin_panel_settings),
    };
    final text = Theme.of(context).textTheme;

    return Scaffold(
      appBar: AppBar(
        title: Text(l.appTitle),
        actions: [
          IconButton(
            icon: const Icon(Icons.translate),
            tooltip: l.language,
            iconSize: 28,
            onPressed: () => context.push(Routes.changeLanguage),
          ),
          IconButton(
            icon: const Icon(Icons.logout),
            tooltip: l.signOut,
            iconSize: 28,
            onPressed: () => ref.read(authControllerProvider.notifier).signOut(),
          ),
        ],
      ),
      body: ListView(
        padding: const EdgeInsets.all(20),
        children: [
          Card(
            child: Padding(
              padding: const EdgeInsets.all(20),
              child: Row(children: [
                CircleAvatar(
                  radius: 28,
                  backgroundColor: const Color(0xFFE7F1FF),
                  child: Icon(icon, color: AppColors.blue, size: 30),
                ),
                const SizedBox(width: 16),
                Expanded(
                  child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                    Text(l.greeting(user.fullName), style: text.titleLarge?.copyWith(fontWeight: FontWeight.w700)),
                    const SizedBox(height: 4),
                    Text(roleName, style: const TextStyle(color: AppColors.blue, fontWeight: FontWeight.w600, fontSize: 16)),
                    if (user.rationShopId != null)
                      Text(l.shopLinked(user.rationShopId!), style: const TextStyle(color: AppColors.muted)),
                  ]),
                ),
              ]),
            ),
          ),
          const SizedBox(height: 16),
          Card(
            child: Padding(
              padding: const EdgeInsets.all(20),
              child: Text(intro, style: text.bodyLarge),
            ),
          ),
          const SizedBox(height: 16),
          OutlinedButton.icon(
            icon: const Icon(Icons.dns_outlined),
            label: Text(l.checkServer),
            onPressed: () => context.push(Routes.serverStatus),
          ),
        ],
      ),
    );
  }
}
