import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../app/routes.dart';
import '../../app/theme.dart';
import '../../core/network/api_exception.dart';
import '../../l10n/app_localizations.dart';
import '../citizen/citizen_widgets.dart';
import '../official/official_words.dart';
import 'notifications_data.dart';

/// The bell in each dashboard's top bar, with the number of unread notifications. It checks again
/// whenever the app comes back to the front.
class NotificationsBell extends ConsumerStatefulWidget {
  const NotificationsBell({super.key});

  @override
  ConsumerState<NotificationsBell> createState() => _NotificationsBellState();
}

class _NotificationsBellState extends ConsumerState<NotificationsBell> {
  late final AppLifecycleListener _lifecycle;

  @override
  void initState() {
    super.initState();
    _lifecycle = AppLifecycleListener(onResume: () => ref.invalidate(notificationsProvider));
  }

  @override
  void dispose() {
    _lifecycle.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final l = AppLocalizations.of(context);
    final unread = ref.watch(unreadCountProvider);
    return IconButton(
      iconSize: 28,
      tooltip: l.notificationsTooltip(unread),
      icon: Badge(
        isLabelVisible: unread > 0,
        label: Text(unread > 99 ? '99+' : '$unread'),
        child: const Icon(Icons.notifications_outlined),
      ),
      onPressed: () async {
        await context.push(Routes.notifications);
        ref.invalidate(notificationsProvider);
      },
    );
  }
}

/// My notifications, newest first. Opening the list marks the new ones as read; they keep a "New"
/// label until the screen is closed so it's clear which ones just arrived.
class NotificationsScreen extends ConsumerStatefulWidget {
  const NotificationsScreen({super.key});

  @override
  ConsumerState<NotificationsScreen> createState() => _NotificationsScreenState();
}

class _NotificationsScreenState extends ConsumerState<NotificationsScreen> {
  bool _marked = false;

  void _markShownAsRead(List<AppNotification> all) {
    if (_marked) return;
    _marked = true;
    final unread = [for (final n in all) if (!n.read) n.id];
    if (unread.isEmpty) return;
    // Best effort: if it fails, they are simply marked next time.
    ref.read(notificationsRepositoryProvider).markRead(unread).catchError((Object _) {});
  }

  @override
  Widget build(BuildContext context) {
    final l = AppLocalizations.of(context);
    final notifications = ref.watch(notificationsProvider);
    return Scaffold(
      appBar: AppBar(title: Text(l.notificationsTitle)),
      body: RefreshIndicator(
        onRefresh: () => ref.refresh(notificationsProvider.future),
        child: ListView(
          padding: const EdgeInsets.all(16),
          children: notifications.when(
            loading: () => [const SizedBox(height: 80), const Center(child: CircularProgressIndicator())],
            error: (e, _) => [
              Text(e is ApiException ? e.messageIn(l) : l.errorGeneric, textAlign: TextAlign.center),
              TextButton(onPressed: () => ref.invalidate(notificationsProvider), child: Text(l.tryAgain)),
            ],
            data: (all) {
              WidgetsBinding.instance.addPostFrameCallback((_) => _markShownAsRead(all));
              if (all.isEmpty) return [Text(l.noNotifications, style: Theme.of(context).textTheme.titleMedium)];
              return [for (final n in all) _NotificationCard(notification: n)];
            },
          ),
        ),
      ),
    );
  }
}

class _NotificationCard extends StatelessWidget {
  const _NotificationCard({required this.notification});

  final AppNotification notification;

  @override
  Widget build(BuildContext context) {
    final l = AppLocalizations.of(context);
    final n = notification;
    final english = Localizations.localeOf(context).languageCode == 'en';
    return Card(
      margin: const EdgeInsets.only(bottom: 10),
      color: n.read ? null : const Color(0xFFF2F7FF),
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Row(crossAxisAlignment: CrossAxisAlignment.start, children: [
          Icon(notificationIcon(n.type), color: AppColors.blue, size: 28),
          const SizedBox(width: 12),
          Expanded(
            child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
              Row(children: [
                Expanded(
                  child: Text(notificationTitle(l, n.type, n.title), style: const TextStyle(fontSize: 17, fontWeight: FontWeight.w700)),
                ),
                if (!n.read) StatusPill(text: l.newLabel, tone: PillTone.warn),
              ]),
              if (n.createdAt != null) Text(localMoment(context, n.createdAt!), style: const TextStyle(color: AppColors.muted)),
              if (n.message.isNotEmpty) ...[
                const SizedBox(height: 6),
                // The backend writes these in English only.
                if (!english) Text(l.alertDetailsInEnglish, style: const TextStyle(color: AppColors.muted, fontSize: 13)),
                Text(n.message, style: const TextStyle(fontSize: 15)),
              ],
            ]),
          ),
        ]),
      ),
    );
  }
}

String notificationTitle(AppLocalizations l, String type, String fallback) => switch (type) {
      'BookingConfirmed' => l.nBookingConfirmed,
      'TokenGenerated' => l.nTokenGenerated,
      'SlotReminder' => l.nSlotReminder,
      'CollectionCompleted' => l.nCollectionCompleted,
      'BookingCancelled' => l.nBookingCancelled,
      'LowInventory' => l.nLowInventory,
      'VerificationResult' => l.nVerificationResult,
      'AIAlert' => l.nAlert,
      'SystemAnnouncement' => l.nAnnouncement,
      _ => fallback,
    };

IconData notificationIcon(String type) => switch (type) {
      'BookingConfirmed' || 'TokenGenerated' => Icons.confirmation_number_outlined,
      'SlotReminder' => Icons.alarm,
      'CollectionCompleted' => Icons.check_circle_outline,
      'BookingCancelled' => Icons.event_busy,
      'LowInventory' => Icons.inventory_2_outlined,
      'VerificationResult' => Icons.verified_user_outlined,
      'AIAlert' => Icons.notification_important_outlined,
      _ => Icons.campaign_outlined,
    };
