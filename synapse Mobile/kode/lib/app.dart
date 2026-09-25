import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'core/theme/theme.dart';
import 'core/theme/theme_mode.dart';
import 'shell/routes.dart';

class SynapseApp extends ConsumerWidget {
  const SynapseApp({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    // watch STATE (bukan .notifier) supaya rebuild saat tema berubah
    final pilihan = ref.watch(themeChoiceProvider);

    return MaterialApp.router(
      title: 'Synapse Mobile',
      debugShowCheckedModeBanner: false,
      theme: AppTheme.light,
      darkTheme: AppTheme.dark,
      themeMode: pilihan == AppThemeChoice.dark ? ThemeMode.dark : ThemeMode.light,
      routerConfig: router,
    );
  }
}
