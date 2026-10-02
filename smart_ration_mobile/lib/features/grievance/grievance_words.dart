import 'package:flutter/material.dart';

import '../../core/network/api_exception.dart';
import '../../l10n/app_localizations.dart';
import '../citizen/citizen_widgets.dart';
import 'grievance_data.dart';

String categoryWord(AppLocalizations l, ComplaintCategory c) => switch (c) {
      ComplaintCategory.lessRation => l.catLessRation,
      ComplaintCategory.poorQuality => l.catPoorQuality,
      ComplaintCategory.shopClosed => l.catShopClosed,
      ComplaintCategory.overcharged => l.catOvercharged,
      ComplaintCategory.tokenProblem => l.catTokenProblem,
      ComplaintCategory.verificationProblem => l.catVerificationProblem,
      ComplaintCategory.staffBehaviour => l.catStaffBehaviour,
      ComplaintCategory.other => l.catOther,
    };

IconData categoryIcon(ComplaintCategory c) => switch (c) {
      ComplaintCategory.lessRation => Icons.scale_outlined,
      ComplaintCategory.poorQuality => Icons.bug_report_outlined,
      ComplaintCategory.shopClosed => Icons.store_mall_directory_outlined,
      ComplaintCategory.overcharged => Icons.currency_rupee,
      ComplaintCategory.tokenProblem => Icons.qr_code_2,
      ComplaintCategory.verificationProblem => Icons.verified_user_outlined,
      ComplaintCategory.staffBehaviour => Icons.sentiment_dissatisfied_outlined,
      ComplaintCategory.other => Icons.more_horiz,
    };

String complaintStatusWord(AppLocalizations l, ComplaintStatus s) => switch (s) {
      ComplaintStatus.submitted => l.complaintStatusSubmitted,
      ComplaintStatus.underReview => l.complaintStatusUnderReview,
      ComplaintStatus.resolved => l.complaintStatusResolved,
      ComplaintStatus.rejected => l.complaintStatusRejected,
    };

PillTone complaintStatusTone(ComplaintStatus s) => switch (s) {
      ComplaintStatus.submitted => PillTone.neutral,
      ComplaintStatus.underReview => PillTone.warn,
      ComplaintStatus.resolved => PillTone.good,
      ComplaintStatus.rejected => PillTone.bad,
    };

/// The backend refuses a few things by code; say them in the person's language.
String complaintErrorIn(AppLocalizations l, ApiException e) => switch (e.errorCode) {
      'SENSITIVE_DATA' => l.complaintNoPrivate,
      'DESCRIPTION_TOO_SHORT' => l.complaintDescribeShort,
      'INVALID_CATEGORY' => l.complaintChooseCategory,
      _ => e.messageIn(l),
    };

/// "GRV-2026-000123" as it should be read aloud: one character at a time, so it can be written down.
String spokenReference(String reference) =>
    reference.split('-').map((part) => part.split('').join(' ')).join(', ');
