import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../app/routes.dart';
import '../../app/theme.dart';
import '../../l10n/app_localizations.dart';
import '../assistant/assistant_sheet.dart';
import '../auth/auth_controller.dart';
import '../booking/booking_data.dart';
import '../booking/booking_widgets.dart';
import '../notifications/notifications_data.dart';
import '../notifications/notifications_screen.dart';
import 'citizen_data.dart';
import 'citizen_widgets.dart';

/// The citizen's dashboard: ration card, eligibility and family at a glance, each opening its own screen.
/// Booking, token and QR join it in the next milestone.
class CitizenHomeScreen extends ConsumerWidget {
  const CitizenHomeScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final l = AppLocalizations.of(context);
    final user = ref.watch(authControllerProvider);
    if (user == null) return const Scaffold(body: SizedBox.shrink());
    final text = Theme.of(context).textTheme;

    return Scaffold(
      floatingActionButton: const AiButton(screen: 'home', summary: citizenHomeSummary),
      appBar: AppBar(
        title: Text(l.appTitle),
        actions: [
          const NotificationsBell(),
          IconButton(
            icon: const Icon(Icons.help_outline),
            tooltip: l.helpButton,
            iconSize: 28,
            onPressed: () => context.push(Routes.help),
          ),
          IconButton(
            icon: const Icon(Icons.translate),
            tooltip: l.language,
            iconSize: 28,
            onPressed: () => context.push(Routes.changeLanguage),
          ),
          IconButton(
            icon: const Icon(Icons.manage_accounts),
            tooltip: l.accountTitle,
            iconSize: 28,
            onPressed: () => context.push(Routes.account),
          ),
          IconButton(
            icon: const Icon(Icons.logout),
            tooltip: l.signOut,
            iconSize: 28,
            onPressed: () => ref.read(authControllerProvider.notifier).signOut(),
          ),
        ],
      ),
      body: CitizenDataView(
        alsoRefresh: (ref) {
          ref.invalidate(myTokensProvider);
          ref.invalidate(notificationsProvider);
        },
        builder: (context, data) => [
          Text(l.greeting(user.fullName), style: text.headlineSmall?.copyWith(fontWeight: FontWeight.w700)),
          const SizedBox(height: 4),
          Text(l.roleRuralUser, style: const TextStyle(color: AppColors.blue, fontWeight: FontWeight.w600, fontSize: 16)),
          const SizedBox(height: 16),
          const _QuickMenu(),
          const SizedBox(height: 16),
          const _NextCollectionCard(),
          const SizedBox(height: 12),
          SectionCard(
            title: l.rationCard,
            icon: Icons.credit_card,
            trailing: StatusPill(text: data.cardActive ? l.cardActive : l.cardInactive,
                tone: data.cardActive ? PillTone.good : PillTone.bad),
            onTap: () => context.push(Routes.citizenCard),
            child: Column(children: [
              InfoRow(label: l.cardNumber, value: valueText(data.cardNumber)),
              InfoRow(label: l.cardScheme, value: valueText(data.schemeName)),
              if (data.shop != null) InfoRow(label: l.assignedShop, value: valueText(data.shop!.name)),
            ]),
          ),
          const SizedBox(height: 12),
          SectionCard(
            title: l.eligibilityTitle,
            icon: Icons.verified_outlined,
            trailing: StatusPill(text: eligibilityWord(l, data.eligibility), tone: eligibilityTone(data.eligibility)),
            onTap: () => context.push(Routes.citizenEligibility),
            child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
              Text(l.eligibleMembersOf(data.eligibleMembers, data.familySize), style: text.bodyLarge),
              const SizedBox(height: 12),
              for (final item in data.entitlement.take(3)) _RemainingLine(item: item),
            ]),
          ),
          const SizedBox(height: 12),
          SectionCard(
            title: l.familyMembers,
            icon: Icons.family_restroom,
            trailing: StatusPill(text: l.memberCount(data.familySize), tone: PillTone.neutral),
            onTap: () => context.push(Routes.citizenFamily),
            child: Wrap(spacing: 8, runSpacing: 8, children: [
              for (final m in data.members) Chip(avatar: Initials(name: m.fullName, radius: 12), label: Text(m.fullName)),
            ]),
          ),
          const SizedBox(height: 12),
          SectionCard(
            title: l.complaintTitle,
            icon: Icons.report_problem_outlined,
            child: Wrap(spacing: 8, runSpacing: 8, children: [
              FilledButton.tonalIcon(
                icon: const Icon(Icons.edit_note),
                label: Text(l.complaintTitle),
                onPressed: () => context.push(Routes.citizenComplaint),
              ),
              OutlinedButton.icon(
                icon: const Icon(Icons.list_alt),
                label: Text(l.myComplaints),
                onPressed: () => context.push(Routes.citizenComplaints),
              ),
            ]),
          ),
          const SizedBox(height: 16),
          OutlinedButton.icon(
            icon: const Icon(Icons.dns_outlined),
            label: Text(l.checkServer),
            onPressed: () => context.push(Routes.serverStatus),
          ),
          const SizedBox(height: 88),
        ],
      ),
    );
  }
}

/// "Read this screen" on the citizen's home: the next collection (token, day, time, shop), from the same data
/// the screen shows; null while it is loading.
String? citizenHomeSummary(BuildContext context, WidgetRef ref) {
  final l = AppLocalizations.of(context);
  final tokens = ref.read(myTokensProvider).value;
  if (tokens == null) return null;
  final next = nextToken(tokens, DateTime.now());
  if (next == null) return l.aiHomeNoBooking;
  return l.aiHomeSummary(next.number, dayLabel(context, next.date), timeLabel(context, next.start), timeLabel(context, next.end), next.shopName);
}

/// The token to bring to the shop next, or a big "Book ration" button when nothing is booked.
class _NextCollectionCard extends ConsumerWidget {
  const _NextCollectionCard();

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final l = AppLocalizations.of(context);
    final tokens = ref.watch(myTokensProvider);
    final next = tokens.whenOrNull(data: (all) => nextToken(all, DateTime.now()));
    return Card(
      color: const Color(0xFFE7F1FF),
      child: Padding(
        padding: const EdgeInsets.all(18),
        child: Column(crossAxisAlignment: CrossAxisAlignment.stretch, children: [
          Row(children: [
            const Icon(Icons.confirmation_number_outlined, color: AppColors.blue, size: 26),
            const SizedBox(width: 10),
            Expanded(
              child: Text(l.nextCollection,
                  style: Theme.of(context).textTheme.titleMedium?.copyWith(fontWeight: FontWeight.w700)),
            ),
          ]),
          const SizedBox(height: 12),
          if (tokens.isLoading)
            const Center(child: CircularProgressIndicator())
          else if (next != null) ...[
            Text(next.number, style: const TextStyle(fontSize: 24, fontWeight: FontWeight.w800, color: AppColors.blue)),
            const SizedBox(height: 4),
            Text('${dayLabel(context, next.date)} · ${timeLabel(context, next.start)} – ${timeLabel(context, next.end)}',
                style: const TextStyle(fontSize: 17, fontWeight: FontWeight.w600)),
            Text(next.shopName, style: const TextStyle(color: AppColors.muted)),
            const SizedBox(height: 12),
            FilledButton.icon(
              icon: const Icon(Icons.qr_code_2),
              label: Text(l.showQr),
              onPressed: () => context.push(Routes.citizenToken(next.id)),
            ),
          ] else ...[
            Text(l.noUpcomingBooking, style: const TextStyle(fontSize: 16)),
            const SizedBox(height: 12),
            FilledButton.icon(
              icon: const Icon(Icons.event_available),
              label: Text(l.bookRation),
              onPressed: () => context.push(Routes.citizenBook),
            ),
          ],
          TextButton(onPressed: () => context.push(Routes.citizenTokens), child: Text(l.allMyTokens)),
        ]),
      ),
    );
  }
}

class _RemainingLine extends StatelessWidget {
  const _RemainingLine({required this.item});

  final EntitlementItem item;

  @override
  Widget build(BuildContext context) {
    final l = AppLocalizations.of(context);
    final unit = unitWord(l, item.rationType);
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 4),
      child: Row(children: [
        Icon(itemIcon(item.rationType), color: AppColors.muted, size: 22),
        const SizedBox(width: 10),
        Expanded(child: Text(itemWord(l, item.rationType), style: const TextStyle(fontSize: 16))),
        Flexible(
          child: Text(l.remainingOf(amount(item.remaining), amount(item.monthly), unit),
              textAlign: TextAlign.end, style: const TextStyle(fontWeight: FontWeight.w600)),
        ),
      ]),
    );
  }
}

/// A round placeholder with the person's initials, where a photo will go later.
class Initials extends StatelessWidget {
  const Initials({super.key, required this.name, this.radius = 24});

  final String name;
  final double radius;

  @override
  Widget build(BuildContext context) {
    final parts = name.trim().split(RegExp(r'\s+')).where((p) => p.isNotEmpty).toList();
    final letters = parts.isEmpty ? '?' : parts.take(2).map((p) => p.characters.first.toUpperCase()).join();
    return ExcludeSemantics(
      child: CircleAvatar(
        radius: radius,
        backgroundColor: const Color(0xFFE7F1FF),
        child: Text(letters, style: TextStyle(color: AppColors.blue, fontWeight: FontWeight.w700, fontSize: radius * 0.75)),
      ),
    );
  }
}

/// The website's side menu as large buttons at the top of the home screen, so every citizen page is one tap away
/// (Book ration is always here, also when a booking already exists).
class _QuickMenu extends ConsumerWidget {
  const _QuickMenu();

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final l = AppLocalizations.of(context);
    final unread = ref.watch(unreadCountProvider);
    final items = [
      (Icons.event_available, l.bookRation, Routes.citizenBook, true, 0),
      (Icons.history, l.bookingHistory, Routes.citizenTokens, false, 0),
      (Icons.verified_user_outlined, l.verificationTitle, Routes.account, false, 0),
      (Icons.report_problem_outlined, l.myComplaints, Routes.citizenComplaints, false, 0),
      (Icons.notifications_outlined, l.notificationsTitle, Routes.notifications, false, unread),
      (Icons.settings_outlined, l.accountTitle, Routes.account, false, 0),
    ];
    return Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
      Text(l.quickMenuTitle, style: Theme.of(context).textTheme.titleMedium?.copyWith(fontWeight: FontWeight.w700)),
      const SizedBox(height: 10),
      LayoutBuilder(builder: (context, box) {
        const gap = 10.0;
        final width = (box.maxWidth - gap * 2) / 3;
        return Wrap(spacing: gap, runSpacing: gap, children: [
          for (final (icon, label, route, primary, badge) in items)
            SizedBox(
              width: width,
              child: _MenuTile(icon: icon, label: label, primary: primary, badge: badge, onTap: () => context.push(route)),
            ),
        ]);
      }),
    ]);
  }
}

class _MenuTile extends StatelessWidget {
  const _MenuTile({required this.icon, required this.label, required this.primary, required this.badge, required this.onTap});

  final IconData icon;
  final String label;
  final bool primary;
  final int badge;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    final fg = primary ? Colors.white : AppColors.blue;
    return Material(
      color: primary ? AppColors.blue : Colors.white,
      borderRadius: BorderRadius.circular(14),
      child: InkWell(
        borderRadius: BorderRadius.circular(14),
        onTap: onTap,
        child: Container(
          constraints: const BoxConstraints(minHeight: 96),
          padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 12),
          decoration: BoxDecoration(
            borderRadius: BorderRadius.circular(14),
            border: primary ? null : Border.all(color: AppColors.border),
          ),
          child: Column(mainAxisAlignment: MainAxisAlignment.center, children: [
            Badge(isLabelVisible: badge > 0, label: Text('$badge'), child: Icon(icon, color: fg, size: 30)),
            const SizedBox(height: 8),
            Text(label,
                textAlign: TextAlign.center,
                maxLines: 3,
                overflow: TextOverflow.ellipsis,
                style: TextStyle(color: primary ? Colors.white : AppColors.ink, fontWeight: FontWeight.w600, fontSize: 13)),
          ]),
        ),
      ),
    );
  }
}
