import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'core/theme/theme.dart';
import 'core/theme/theme_mode.dart';
import 'shell/routes.dart';
import 'main.dart' show isiLoncengUpdate;
import 'core/update/pengingat_update.dart';

class SynapseApp extends ConsumerWidget {
  const SynapseApp({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    // watch STATE (bukan .notifier) supaya rebuild saat tema berubah
    final pilihan = ref.watch(themeChoiceProvider);

    // FIX v1.2.7 — LAPIS 2 pengingat update: isi LONCENG di dalam app
    // (badge di pojok kanan atas) kalau ada versi baru.
    WidgetsBinding.instance.addPostFrameCallback((_) {
      try { isiLoncengUpdate(ref); } catch (_) {}
    });

    // FIX v1.2.7 — kalau app dibuka DARI NOTIFIKASI UPDATE (notif di luar app),
    // langsung arahkan ke menu "Update" supaya user bisa update cepat 1 ketuk.
    WidgetsBinding.instance.addPostFrameCallback((_) async {
      try {
        if (await PengingatUpdate.dibukaDariNotifUpdate()) {
          router.go('/update');
        }
      } catch (_) {}
    });

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
