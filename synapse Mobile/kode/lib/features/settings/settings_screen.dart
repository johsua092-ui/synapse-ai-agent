import 'package:flutter/material.dart';
import 'package:package_info_plus/package_info_plus.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import '../../core/api/api_config.dart';
import '../../core/theme/spacing.dart';
import '../../core/koneksi/koneksi_perangkat.dart';
import '../../core/theme/theme_mode.dart';

class SettingsScreen extends ConsumerWidget {
  const SettingsScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final t = Theme.of(context);
    final pilihan = ref.watch(themeChoiceProvider);
    final cfg = ref.watch(apiConfigProvider);
    final koneksi = ref.watch(koneksiPerangkatProvider);

    return Scaffold(
      appBar: AppBar(title: const Text('Setelan')),
      body: ListView(
      padding: const EdgeInsets.all(AppSpacing.md),
      children: [

        // ---- TAMPILAN ----
        Text('Tampilan', style: t.textTheme.titleSmall),
        const SizedBox(height: 6),
        Card(
          child: Column(children: [
            RadioListTile<AppThemeChoice>(
              value: AppThemeChoice.light,
              groupValue: pilihan,
              onChanged: (v) {
                if (v != null) ref.read(themeChoiceProvider.notifier).set(v);
              },
              title: const Text('Terang'),
              secondary: const Icon(Icons.light_mode),
            ),
            const Divider(height: 1),
            RadioListTile<AppThemeChoice>(
              value: AppThemeChoice.dark,
              groupValue: pilihan,
              onChanged: (v) {
                if (v != null) ref.read(themeChoiceProvider.notifier).set(v);
              },
              title: const Text('Gelap'),
              secondary: const Icon(Icons.dark_mode),
            ),
          ]),
        ),

        const SizedBox(height: AppSpacing.lg),

        // ---- KONEKSI AI ----
        Text('Koneksi AI', style: t.textTheme.titleSmall),
        const SizedBox(height: 6),
        Card(
          child: Column(children: [
            ListTile(
              leading: Icon(cfg.terisi ? Icons.cloud_done : Icons.cloud_off,
                  color: cfg.terisi ? Colors.green : null),
              title: const Text('Base URL & API Key'),
              subtitle: Text(cfg.terisi
                  ? '${cfg.baseUrl}  •  ${cfg.model ?? "model belum dipilih"}'
                  : 'Belum diatur'),
              trailing: const Icon(Icons.chevron_right),
              onTap: () => context.push('/koneksi'),
            ),
            const Divider(height: 1),
            // TOMBOL KONEKSI PERANGKAT — tepat di bawah "Base URL & API Key"
            ListTile(
              leading: Icon(
                koneksi.mode == ModeKoneksi.wifi
                    ? Icons.wifi
                    : Icons.usb,
                color: koneksi.terhubung ? Colors.green : null,
              ),
              title: const Text('Koneksi AI Agent Synapse PC ke Mobile'),
              subtitle: Text(
                koneksi.terhubung
                    ? 'Terhubung — ${koneksi.mode.label}'
                    : 'Mode: ${koneksi.mode.label}  •  ketuk untuk atur',
              ),
              trailing: const Icon(Icons.chevron_right),
              onTap: () => context.push('/koneksi-perangkat'),
            ),
          ]),
        ),

        const SizedBox(height: AppSpacing.lg),

        // ---- LAIN-LAIN ----
        Text('Lain-lain', style: t.textTheme.titleSmall),
        const SizedBox(height: 6),
        Card(
          child: Column(children: [
            ListTile(
              leading: const Icon(Icons.system_update_alt),
              title: const Text('Update'),
              subtitle: const Text('Cek versi terbaru dari GitHub'),
              trailing: const Icon(Icons.chevron_right),
              onTap: () => context.push('/update'),
            ),
            const Divider(height: 1),
            ListTile(
              leading: const Icon(Icons.backup_outlined),
              title: const Text('Backup & Restore'),
              subtitle: const Text('config, .env, memories, skills, SOUL.md'),
              trailing: const Icon(Icons.chevron_right),
              onTap: () => context.push('/backup'),
            ),
            const Divider(height: 1),
            ListTile(
              leading: const Icon(Icons.phonelink_lock_outlined),
              title: const Text('Akses Perangkat'),
              subtitle: const Text('Kamera, WhatsApp, lokasi, aplikasi, dll'),
              trailing: const Icon(Icons.chevron_right),
              onTap: () => context.push('/perangkat'),
            ),
            const Divider(height: 1),
            ListTile(
              leading: const Icon(Icons.notifications_outlined),
              title: const Text('Notifikasi'),
              subtitle: const Text('Pemberitahuan dari Synapse'),
              trailing: const Icon(Icons.chevron_right),
              onTap: () => context.push('/notifikasi'),
            ),
            const Divider(height: 1),
            ListTile(
              leading: const Icon(Icons.info_outline),
              title: const Text('Status'),
              subtitle: const Text('Koneksi, orientasi, mode tampilan'),
              trailing: const Icon(Icons.chevron_right),
              onTap: () => context.push('/status'),
            ),
          ]),
        ),

        const SizedBox(height: AppSpacing.lg),
        Center(
          child: FutureBuilder(
            future: PackageInfo.fromPlatform(),
            builder: (c, snap) => Text(
              'Synapse Mobile ${snap.data?.version ?? '...'}',
              style: t.textTheme.bodySmall,
            ),
          ),
        ),
      ],
      ),
    );
  }
}
