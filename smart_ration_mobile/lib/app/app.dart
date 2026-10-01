import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import 'router.dart';
import 'theme.dart';

class SmartRationApp extends ConsumerWidget {
  const SmartRationApp({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) => MaterialApp.router(
        title: 'Smart Ration AI',
        theme: buildAppTheme(),
        routerConfig: ref.watch(routerProvider),
        debugShowCheckedModeBanner: false,
      );
}
