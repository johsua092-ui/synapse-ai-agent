import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../core/api/api_providers.dart';
import '../../core/theme/spacing.dart';

/// Backup & Restore pengaturan Synapse.
/// Mencakup: config.yaml, .env (kredensial), memories, skills, SOUL.md.
class BackupScreen extends ConsumerStatefulWidget {
  const BackupScreen({super.key});
  @override
  ConsumerState<BackupScreen> createState() => _BackupScreenState();
}

class _BackupScreenState extends ConsumerState<BackupScreen> {
  bool _sibuk = false;
  String? _hasil;

  /// Item yang bisa di-backup.
  static const _item = <Map<String, String>>[
    {'nama': 'config.yaml', 'desk': 'Pengaturan Synapse (model, gateway, platform)'},
    {'nama': '.env', 'desk': 'Kredensial & API key (RAHASIA — hati-hati!)'},
    {'nama': 'memories', 'desk': 'Memori jangka panjang (MEMORY.md, USER.md)'},
    {'nama': 'skills', 'desk': 'Skill terpasang'},
    {'nama': 'SOUL.md', 'desk': 'Kepribadian & instruksi inti agent'},
    {'nama': 'sessions.db', 'desk': 'Riwayat percakapan'},
  ];

  Future<void> _jalankan(String cmd, String label) async {
    final klien = ref.read(apiClientProvider);
    if (klien == null) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Belum tersambung ke Synapse')),
      );
      return;
    }
    setState(() { _sibuk = true; _hasil = null; });
    try {
      final hasil = await klien.perintahAgent(cmd);
      if (!mounted) return;
      setState(() { _hasil = hasil; _sibuk = false; });
    } catch (e) {
      if (!mounted) return;
      setState(() { _hasil = 'Gagal: $e'; _sibuk = false; });
    }
  }

  @override
  Widget build(BuildContext context) {
    final t = Theme.of(context);
    return Scaffold(
      appBar: AppBar(title: const Text('Backup & Restore')),
      body: ListView(
        padding: const EdgeInsets.all(AppSpacing.md),
        children: [
          Text('Isi backup', style: t.textTheme.titleSmall),
          const SizedBox(height: 6),
          Card(
            child: Column(children: [
              for (var i = 0; i < _item.length; i++) ...[
                ListTile(
                  dense: true,
                  leading: Icon(_item[i]['nama'] == '.env'
                      ? Icons.key
                      : _item[i]['nama'] == 'SOUL.md'
                          ? Icons.psychology
                          : Icons.description_outlined),
                  title: Text(_item[i]['nama']!),
                  subtitle: Text(_item[i]['desk']!, style: t.textTheme.bodySmall),
                ),
                if (i < _item.length - 1) const Divider(height: 1),
              ],
            ]),
          ),

          const SizedBox(height: AppSpacing.lg),
          Text('Aksi', style: t.textTheme.titleSmall),
          const SizedBox(height: 6),

          FilledButton.icon(
            onPressed: _sibuk
                ? null
                : () => _jalankan(
                    'Buat backup lengkap Synapse (config, .env, memories, skills, '
                    'SOUL.md) ke folder backup, lalu laporkan nama file backup-nya.',
                    'backup'),
            icon: _sibuk
                ? const SizedBox(width: 16, height: 16,
                    child: CircularProgressIndicator(strokeWidth: 2))
                : const Icon(Icons.backup),
            label: const Text('Buat Backup Sekarang'),
          ),
          const SizedBox(height: AppSpacing.sm),
          OutlinedButton.icon(
            onPressed: _sibuk
                ? null
                : () => _jalankan(
                    'Tampilkan daftar backup Synapse yang tersedia (nama + tanggal).',
                    'daftar'),
            icon: const Icon(Icons.list),
            label: const Text('Lihat Daftar Backup'),
          ),
          const SizedBox(height: AppSpacing.sm),
          OutlinedButton.icon(
            onPressed: _sibuk
                ? null
                : () => _jalankan(
                    'Tampilkan isi folder konfigurasi Synapse (config.yaml, .env, '
                    'memories, skills, SOUL.md) beserta ukurannya.',
                    'cek'),
            icon: const Icon(Icons.folder_open),
            label: const Text('Periksa File Konfigurasi'),
          ),

          if (_hasil != null) ...[
            const SizedBox(height: AppSpacing.lg),
            Text('Hasil', style: t.textTheme.titleSmall),
            const SizedBox(height: 6),
            Container(
              width: double.infinity,
              padding: const EdgeInsets.all(AppSpacing.md),
              decoration: BoxDecoration(
                color: t.colorScheme.surfaceContainerHighest,
                borderRadius: BorderRadius.circular(8),
              ),
              child: SelectableText(_hasil!, style: t.textTheme.bodySmall),
            ),
          ],

          const SizedBox(height: AppSpacing.lg),
          Card(
            color: Colors.orange.withValues(alpha: 0.10),
            child: const ListTile(
              leading: Icon(Icons.warning_amber, color: Colors.orange),
              title: Text('Perhatian'),
              subtitle: Text(
                'Backup berisi .env (API key & kredensial). Simpan di tempat aman, '
                'jangan dibagikan.',
                style: TextStyle(fontSize: 12),
              ),
            ),
          ),
        ],
      ),
    );
  }
}
