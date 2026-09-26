import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../core/api/api_providers.dart';
import '../../core/theme/spacing.dart';

/// Backup & Restore LENGKAP (perbaikan v1.2.1).
///
/// SEBELUM: hanya kirim perintah "buat backup" ke agent, TIDAK ADA restore.
/// SESUDAH: backup PENUH (semua data Synapse) + RESTORE + lihat/kelola
/// daftar backup dari HP.
///
/// Isi backup (LENGKAP = seluruh "diri" Synapse):
///   config.yaml, .env, memories/, skills/, SOUL.md, sessions.db,
///   plus folder lain di ~/.synapse (seluruh folder konfigurasi).
class BackupScreen extends ConsumerStatefulWidget {
  const BackupScreen({super.key});
  @override
  ConsumerState<BackupScreen> createState() => _BackupScreenState();
}

class _BackupScreenState extends ConsumerState<BackupScreen> {
  bool _sibuk = false;
  String? _hasil;

  static const _item = <Map<String, String>>[
    {'nama': 'config.yaml', 'desk': 'Pengaturan Synapse (model, gateway, platform)'},
    {'nama': '.env', 'desk': 'Kredensial & API key (RAHASIA — hati-hati!)'},
    {'nama': 'memories/', 'desk': 'Memori jangka panjang (MEMORY.md, USER.md)'},
    {'nama': 'skills/', 'desk': 'Semua skill terpasang'},
    {'nama': 'SOUL.md', 'desk': 'Kepribadian & instruksi inti agent'},
    {'nama': 'sessions.db', 'desk': 'Riwayat percakapan'},
    {'nama': 'cron/', 'desk': 'Tugas terjadwal'},
    {'nama': 'folder lain', 'desk': 'Seluruh isi ~/.synapse (backup PENUH)'},
  ];

  Future<void> _jalankan(String cmd, {bool panjang = false}) async {
    final klien = ref.read(apiClientProvider);
    if (klien == null) {
      _pesan('Belum tersambung. Isi Base URL + API Key di Setelan.');
      return;
    }
    setState(() {
      _sibuk = true;
      _hasil = null;
    });
    try {
      final hasil = await klien.perintahAgent(cmd, panjang: panjang);
      if (!mounted) return;
      setState(() {
        _hasil = hasil.trim().isEmpty ? '(selesai, tanpa output)' : hasil.trim();
        _sibuk = false;
      });
    } catch (e) {
      if (!mounted) return;
      setState(() {
        _hasil = 'Gagal: $e';
        _sibuk = false;
      });
    }
  }

  void _pesan(String s) {
    if (!mounted) return;
    ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(s)));
  }

  /// Konfirmasi sebelum restore (berbahaya: menimpa data sekarang).
  Future<void> _konfirmasiRestore(String namaFile) async {
    final ya = await showDialog<bool>(
      context: context,
      builder: (c) => AlertDialog(
        title: const Text('Restore data Synapse?'),
        content: Text(
          'Data Synapse SEKARANG akan DIGANTI dengan isi backup:\n\n'
          '"$namaFile"\n\n'
          'Ini mengembalikan SELURUH "diri" Synapse (config, .env, memori, '
          'skill, SOUL, riwayat). Lanjutkan?',
        ),
        actions: [
          TextButton(
              onPressed: () => Navigator.pop(c, false),
              child: const Text('Batal')),
          FilledButton(
            onPressed: () => Navigator.pop(c, true),
            style: FilledButton.styleFrom(backgroundColor: Colors.red),
            child: const Text('Ya, Restore'),
          ),
        ],
      ),
    );
    if (ya != true) return;

    _jalankan(
      'WAJIB pakai perintah NATIVE Synapse (JANGAN mengarang skrip sendiri).\n'
      'Langkah 1 — AMANKAN dulu data sekarang (wajib):\n'
      '  "C:\\Users\\user\\AppData\\Local\\synapse\\bin\\synapse.exe" backup '
      '-o "C:\\Users\\user\\backup\\sebelum-restore-<stamp>.zip"\n'
      'Langkah 2 — RESTORE penuh dari file backup "$namaFile" '
      '(cari di C:\\Users\\user\\backup\\ kalau perlu):\n'
      '  "C:\\Users\\user\\AppData\\Local\\synapse\\bin\\synapse.exe" import '
      '"C:\\Users\\user\\backup\\$namaFile"\n'
      'Ini mengembalikan SELURUH "diri" Synapse (config.yaml, .env, memories/, '
      'skills/, SOUL.md, state.db, cron/, dll) dengan menimpa data sekarang. '
      'Tunggu sampai selesai (bisa beberapa menit), lalu laporkan: '
      'berhasil/gagal + apa saja yang dipulihkan.',
      panjang: true,
    );
  }

  /// Dialog pilih file backup untuk restore.
  Future<void> _dialogRestore() async {
    final ctl = TextEditingController();
    await showDialog<void>(
      context: context,
      builder: (c) => AlertDialog(
        title: const Text('Restore dari Backup'),
        content: SingleChildScrollView(
          child: Column(mainAxisSize: MainAxisSize.min, children: [
            const Text(
              'Masukkan nama file backup (lihat "Daftar Backup" dulu), '
              'lalu ketuk Restore. Seluruh data Synapse akan dikembalikan.',
              style: TextStyle(fontSize: 12),
            ),
            const SizedBox(height: 12),
            TextField(
              controller: ctl,
              decoration: const InputDecoration(
                labelText: 'Nama file backup',
                hintText: 'mis. synapse-backup-2026-09-25.zip',
              ),
            ),
          ]),
        ),
        actions: [
          TextButton(
              onPressed: () => Navigator.pop(c), child: const Text('Batal')),
          FilledButton(
            onPressed: () {
              final n = ctl.text.trim();
              Navigator.pop(c);
              if (n.isNotEmpty) _konfirmasiRestore(n);
            },
            child: const Text('Lanjut'),
          ),
        ],
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    final t = Theme.of(context);
    return Scaffold(
      appBar: AppBar(title: const Text('Backup & Restore')),
      body: ListView(
        padding: const EdgeInsets.all(AppSpacing.md),
        children: [
          Text('Isi backup (PENUH)', style: t.textTheme.titleSmall),
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
                          : _item[i]['nama']!.startsWith('memories')
                              ? Icons.memory
                              : _item[i]['nama']!.startsWith('skills')
                                  ? Icons.extension
                                  : _item[i]['nama']!.startsWith('cron')
                                      ? Icons.schedule
                                      : Icons.description_outlined),
                  title: Text(_item[i]['nama']!),
                  subtitle: Text(_item[i]['desk']!, style: t.textTheme.bodySmall),
                ),
                if (i < _item.length - 1) const Divider(height: 1),
              ],
            ]),
          ),

          const SizedBox(height: AppSpacing.lg),
          Text('Backup', style: t.textTheme.titleSmall),
          const SizedBox(height: 6),

          FilledButton.icon(
            onPressed: _sibuk
                ? null
                : () => _jalankan(
                    'WAJIB pakai perintah NATIVE Synapse (JANGAN mengarang '
                    'skrip sendiri, jangan pakai os.walk manual): jalankan\n'
                    '  "C:\\Users\\user\\AppData\\Local\\synapse\\bin\\synapse.exe" '
                    'backup -o "C:\\Users\\user\\backup\\synapse-backup-<stamp>.zip"\n'
                    'Perintah ini mem-backup SELURUH isi ~/.synapse (config.yaml, '
                    '.env, memories/, skills/, SOUL.md, state.db, cron/, dll) '
                    'dengan pengecualian resmi (synapse-agent/, node_modules/, '
                    'cache/, __pycache__/). Tunggu sampai benar-benar selesai '
                    '(butuh ~2-3 menit), lalu laporkan: path file .zip + ukuran '
                    '+ jumlah file.',
                    panjang: true,
                  ),
            icon: _sibuk
                ? const SizedBox(
                    width: 16,
                    height: 16,
                    child: CircularProgressIndicator(strokeWidth: 2))
                : const Icon(Icons.backup),
            label: const Text('Buat Backup PENUH Sekarang'),
          ),
          const SizedBox(height: AppSpacing.sm),
          OutlinedButton.icon(
            onPressed: _sibuk
                ? null
                : () => _jalankan(
                    'Tampilkan daftar backup Synapse di folder '
                    'C:\\Users\\user\\backup\\ (nama file + tanggal + ukuran, '
                    'urut terbaru dulu). Kalau folder itu kosong, cek juga '
                    'folder home C:\\Users\\user\\.',
                  ),
            icon: const Icon(Icons.list),
            label: const Text('Lihat Daftar Backup'),
          ),

          const SizedBox(height: AppSpacing.lg),
          Text('Restore', style: t.textTheme.titleSmall),
          const SizedBox(height: 6),
          FilledButton.icon(
            onPressed: _sibuk ? null : _dialogRestore,
            style: FilledButton.styleFrom(backgroundColor: Colors.red),
            icon: const Icon(Icons.restore),
            label: const Text('Restore dari Backup'),
          ),
          const SizedBox(height: AppSpacing.sm),
          OutlinedButton.icon(
            onPressed: _sibuk
                ? null
                : () => _jalankan(
                    'Tampilkan isi folder konfigurasi Synapse (config.yaml, .env, '
                    'memories, skills, SOUL.md, sessions.db) beserta ukurannya.',
                  ),
            icon: const Icon(Icons.folder_open),
            label: const Text('Periksa File Konfigurasi'),
          ),

          if (_sibuk)
            const Padding(
              padding: EdgeInsets.only(top: AppSpacing.md),
              child: LinearProgressIndicator(),
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
                'jangan dibagikan. Restore akan MENIMPA data sekarang.',
                style: TextStyle(fontSize: 12),
              ),
            ),
          ),
        ],
      ),
    );
  }
}
