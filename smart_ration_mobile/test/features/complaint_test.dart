import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:smart_ration_mobile/app/router.dart';
import 'package:smart_ration_mobile/app/routes.dart';
import 'package:smart_ration_mobile/features/citizen/citizen_home_screen.dart';
import 'package:smart_ration_mobile/features/grievance/grievance_data.dart';
import 'package:smart_ration_mobile/features/grievance/grievance_words.dart';
import 'package:smart_ration_mobile/features/help/voice.dart';

import '../support/fake_backend.dart';
import '../support/fake_grievance.dart';
import '../support/test_app.dart';
import 'help_test.dart' show FakeSpeaker;
import 'shop_test.dart' show tapText;

/// Opens the app as the demo citizen, then the complaint form (with [draft] as the AI assistant would pass it).
Future<FakeBackend> openComplaint(WidgetTester tester,
    {ComplaintDraft? draft, String language = 'en', Speaker? speaker, FakeReply? refuseWith, String path = Routes.citizenComplaint}) async {
  tester.view.physicalSize = const Size(1080, 3600);
  tester.view.devicePixelRatio = 2.0;
  addTearDown(tester.view.reset);
  final backend = FakeBackend(complaintServer(refuseWith: refuseWith));
  final app = await TestApp.build(backend, savedLanguage: language, signedInAs: citizen(),
      overrides: [speakerProvider.overrideWithValue(speaker ?? FakeSpeaker())]);
  await tester.pumpWidget(app.widget);
  await tester.pumpAndSettle();
  containerOf(tester.element(find.byType(CitizenHomeScreen))).read(routerProvider).push(path, extra: draft);
  await tester.pumpAndSettle();
  return backend;
}

List<RequestOptionsLike> sentComplaints(FakeBackend b) =>
    b.requests.where((r) => r.path == '/api/grievances' && r.method == 'POST').map((r) => (data: r.data, key: r.headers['Idempotency-Key'])).toList();

typedef RequestOptionsLike = ({Object? data, Object? key});

void main() {
  test('reference numbers are read one character at a time', () {
    expect(spokenReference('GRV-2026-000123'), 'G R V, 2 0 2 6, 0 0 0 1 2 3');
  });

  testWidgets('typing a complaint: what is missing is pointed out, then review, confirm and a reference number', (tester) async {
    final backend = await openComplaint(tester);

    await tapText(tester, 'Review');
    expect(find.text('Choose what the problem is.'), findsOneWidget);
    expect(find.text('Please write a little more (at least 10 letters).'), findsOneWidget);

    await tapText(tester, 'Got less ration');
    await tapText(tester, 'Wheat');
    await tester.enterText(find.byType(TextField), 'This month I got 2 kg less wheat.');
    await tapText(tester, 'Review');

    // The review screen: everything at a glance, with the person's own details from their account.
    expect(find.text('Please review your information before submitting.'), findsOneWidget);
    expect(find.text('This month I got 2 kg less wheat.'), findsOneWidget);
    expect(find.text('Asha Devi'), findsOneWidget);
    expect(find.text('9800000007'), findsOneWidget);
    expect(sentComplaints(backend), isEmpty); // nothing sent before Confirm

    await tapText(tester, 'Confirm and send');
    final sent = sentComplaints(backend).single;
    expect(sent.data, {'category': 'LessRation', 'description': 'This month I got 2 kg less wheat.', 'rationType': 'Wheat', 'source': 'APP'});
    expect(sent.key, matches(RegExp(r'^[0-9a-f]{32}$')));
    expect(find.text('Complaint registered'), findsWidgets);
    expect(find.text('GRV-2026-000001'), findsOneWidget);

    await tapText(tester, 'My complaints');
    expect(find.text('GRV-2026-000001'), findsOneWidget);
    expect(find.text('Received'), findsOneWidget);
    expect(find.text('Got less ration'), findsOneWidget);
  });

  testWidgets('an Aadhaar-like number in the description stops it before sending', (tester) async {
    final backend = await openComplaint(tester);
    await tester.tap(find.text('Got less ration'));
    await tester.enterText(find.byType(TextField), 'My Aadhaar is 1234 5678 9012 and I got less rice');
    await tester.pumpAndSettle();
    expect(find.text('Do not write Aadhaar numbers, OTPs or passwords.'), findsOneWidget); // shown as the error
    await tapText(tester, 'Review');
    expect(find.text('Please review your information before submitting.'), findsNothing);
    expect(sentComplaints(backend), isEmpty);
  });

  testWidgets('a complete draft from the assistant opens at review; sending reads the reference aloud', (tester) async {
    final speaker = FakeSpeaker();
    final backend = await openComplaint(tester,
        language: 'hi',
        speaker: speaker,
        draft: ComplaintDraft.fromAssistantFields({
          'category': 'LessRation', 'rationType': 'Wheat', 'description': 'मुझे इस महीने गेहूं कम मिला।', 'ignored': 'x',
        }));

    expect(find.text('जमा करने से पहले कृपया अपनी जानकारी जाँच लें।'), findsOneWidget);
    expect(find.text('मुझे इस महीने गेहूं कम मिला।'), findsOneWidget);
    await tapText(tester, 'पुष्टि करें और भेजें');

    expect(sentComplaints(backend).single.data,
        {'category': 'LessRation', 'description': 'मुझे इस महीने गेहूं कम मिला।', 'rationType': 'Wheat', 'source': 'ASSISTANT'});
    expect(speaker.spoken.single, ('आपकी शिकायत सफलतापूर्वक दर्ज हो गई है। आपका संदर्भ नंबर है G R V, 2 0 2 6, 0 0 0 0 0 1।', 'hi'));
    speaker.finish();
    await tester.pumpAndSettle();
  });

  testWidgets('an incomplete draft from the assistant asks only for what is missing', (tester) async {
    await openComplaint(tester, draft: ComplaintDraft.fromAssistantFields({'description': 'The shop was not open when I went today.'}));

    expect(find.text('Filled in from what you said. Please check it.'), findsOneWidget);
    expect(find.text('Choose what the problem is.'), findsOneWidget);
    expect(find.text('Please write a little more (at least 10 letters).'), findsNothing); // the description is fine
    await tester.tap(find.text('Shop was closed'));
    await tapText(tester, 'Review');
    expect(find.text('Please review your information before submitting.'), findsOneWidget);
  });

  testWidgets("the backend's refusal is shown in the person's language and the form stays", (tester) async {
    await openComplaint(tester,
        refuseWith: const FakeReply(400, {'success': false, 'message': 'Please remove Aadhaar numbers, OTPs and passwords from the description.',
            'errorCode': 'SENSITIVE_DATA', 'data': null, 'errors': null}),
        draft: ComplaintDraft.fromAssistantFields({'category': 'Other', 'description': 'Something the app did not catch here.'}));

    await tapText(tester, 'Confirm and send');
    expect(find.text('Do not write Aadhaar numbers, OTPs or passwords.'), findsOneWidget);
    expect(find.text('Confirm and send'), findsOneWidget);
  });

  testWidgets('my complaints shows the status and the office reply', (tester) async {
    tester.view.physicalSize = const Size(1080, 3600);
    tester.view.devicePixelRatio = 2.0;
    addTearDown(tester.view.reset);
    final backend = FakeBackend((r) => r.path == '/api/grievances/mine'
        ? FakeReply.ok([complaintJson(7, 'ShopClosed', 'Closed at 10 am.', status: 'Resolved', reply: 'Shop told to keep its hours.')])
        : demoServer(r));
    final app = await TestApp.build(backend, savedLanguage: 'en', signedInAs: citizen());
    await tester.pumpWidget(app.widget);
    await tester.pumpAndSettle();
    await tapText(tester, 'My complaints'); // from the home screen

    expect(find.text('GRV-2026-000007'), findsOneWidget);
    expect(find.text('Resolved'), findsOneWidget);
    expect(find.text('Reply from the office'), findsOneWidget);
    expect(find.text('Shop told to keep its hours.'), findsOneWidget);
  });
}
