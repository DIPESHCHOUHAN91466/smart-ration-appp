import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../app/routes.dart';
import '../../app/theme.dart';
import '../../core/network/api_exception.dart';
import '../../l10n/app_localizations.dart';
import '../citizen/citizen_widgets.dart';
import '../official/official_words.dart' show localMoment;
import 'grievance_data.dart';
import 'grievance_words.dart';

/// My complaints, newest first: what, when, the reference number, the status and the office's reply.
class MyComplaintsScreen extends ConsumerWidget {
  const MyComplaintsScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final l = AppLocalizations.of(context);
    final complaints = ref.watch(myComplaintsProvider);
    return Scaffold(
      appBar: AppBar(title: Text(l.myComplaints)),
      floatingActionButton: FloatingActionButton.extended(
        icon: const Icon(Icons.report_problem_outlined),
        label: Text(l.complaintTitle),
        onPressed: () => context.push(Routes.citizenComplaint),
      ),
      body: RefreshIndicator(
        onRefresh: () => ref.refresh(myComplaintsProvider.future),
        child: ListView(
          padding: const EdgeInsets.fromLTRB(16, 16, 16, 96),
          children: complaints.when(
            loading: () => [const SizedBox(height: 80), const Center(child: CircularProgressIndicator())],
            error: (e, _) => [
              Text(e is ApiException ? e.messageIn(l) : l.errorGeneric, textAlign: TextAlign.center),
              TextButton(onPressed: () => ref.invalidate(myComplaintsProvider), child: Text(l.tryAgain)),
            ],
            data: (all) => all.isEmpty
                ? [Text(l.noComplaints, style: Theme.of(context).textTheme.titleMedium)]
                : [for (final c in all) _ComplaintCard(complaint: c)],
          ),
        ),
      ),
    );
  }
}

class _ComplaintCard extends StatelessWidget {
  const _ComplaintCard({required this.complaint});

  final Complaint complaint;

  @override
  Widget build(BuildContext context) {
    final l = AppLocalizations.of(context);
    final c = complaint;
    return Card(
      margin: const EdgeInsets.only(bottom: 10),
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
          Row(children: [
            Icon(categoryIcon(c.category), color: AppColors.blue),
            const SizedBox(width: 8),
            Expanded(child: Text(categoryWord(l, c.category), style: const TextStyle(fontSize: 17, fontWeight: FontWeight.w700))),
          ]),
          const SizedBox(height: 6),
          // Under the title, so it fits small phones with large text.
          StatusPill(text: complaintStatusWord(l, c.status), tone: complaintStatusTone(c.status)),
          const SizedBox(height: 8),
          InfoRow(label: l.complaintReference, value: valueText(c.reference)),
          if (c.rationType != null) InfoRow(label: l.complaintItem, value: valueText(itemWord(l, c.rationType!))),
          if (c.createdAt != null) Text(localMoment(context, c.createdAt!), style: const TextStyle(color: AppColors.muted)),
          const SizedBox(height: 6),
          Text(c.description, style: const TextStyle(fontSize: 15)),
          if (c.officeReply.isNotEmpty) ...[
            const SizedBox(height: 8),
            Text(l.complaintOfficeReply, style: const TextStyle(color: AppColors.muted, fontSize: 13)),
            Text(c.officeReply, style: const TextStyle(fontSize: 15, fontWeight: FontWeight.w600)),
          ],
        ]),
      ),
    );
  }
}
