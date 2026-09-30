import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../core/api/api_providers.dart';
import '../../core/theme/spacing.dart';

/// Backup & Restore — memakai ENDPOINT NATIVE di Synapse agent (v1.2.7).
///
/// SEBELUM: mengirim perintah TEKS ke agent (LLM) lewat chat ->
///   lambat, kena timeout 180s (jebakan #78), agent bisa mengarang skrip
///   salah (#79), dan restore saat Synapse hidup MERUSAK state.db (#81).
///
/// SESUDAH: memanggil endpoint khusus di api_server:
///   GET  /v1/backup          daftar file backup
///   POST /v1/backup          buat backup PENUH (perintah native, tanpa LLM)
///   POST /v1/restore         mulai restore (dijalankan TERPISAH di laptop,
///                            otomatis: backup pengaman -> gateway stop ->
///                            import -> gateway start)
///   GET  /v1/restore/status  status restore terakhir
///
/// Isi backup (LENGKAP = seluruh "diri" Synapse): config.yaml, .env,
/// memories/, skills/, SOUL.md, state.db, cron/, dll.
class BackupScreen extends ConsumerStatefulWidget {
  const BackupScreen({super.key});
  @override
  ConsumerState<BackupScreen> createState() => _BackupScreenState();
}

class _BackupScreenState extends ConsumerState<BackupScreen> {
  bool _sibuk = false;
  String? _hasil;
  String _tahap = '';
  List<Map<String, dynamic>> _daftar = [];
  bool _memuatDaftar = false;

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

  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addPostFrameCallback((_) => _muatDaftar());
  }

  void _pesan(String s) {
    if (!mounted) return;
    ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(s)));
  }

  /// Pesan ramah kalau endpoint tidak ada (mis. Base URL masih ke router).
  String _pesanGagal(Object e) {
    final s = e.toString();
    if (s.contains('404')) {
      return 'Fitur Backup/Restore hanya ada di Synapse AGENT (laptop), '
          'bukan di router model.\n\n'
          'Perbaiki: Setelan -> Koneksi AI -> isi "Base URL Agent (opsional)" '
          'dengan http://127.0.0.1:8642 lalu di laptop jalankan '
          'adb reverse tcp:8642 tcp:8642.';
    }
    if (s.contains('TimeoutException') || s.contains('timeout')) {
      return 'Koneksi ke agent terputus (timeout). Pastikan laptop menyala + '
          'adb reverse aktif, lalu coba lagi.';
    }
    return 'Gagal: $s';
  }

  Future<void> _muatDaftar() async {
    final klien = ref.read(apiClientProvider);
    if (klien == null) {
      _pesan('Belum tersambung. Isi Base URL + API Key di Setelan.');
      return;
    }
    setState(() => _memuatDaftar = true);
    try {
      final d = await klien.daftarBackup();
      if (!mounted) return;
      setState(() {
        _daftar = d;
        _memuatDaftar = false;
      });
    } catch (e) {
      if (!mounted) return;
      setState(() {
        _memuatDaftar = false;
        _hasil = _pesanGagal(e);
      });
    }
  }

  /// Buat backup PENUH lewat endpoint native (tanpa LLM).
  Future<void> _buatBackup() async {
    final klien = ref.read(apiClientProvider);
    if (klien == null) {
      _pesan('Belum tersambung. Isi Base URL + API Key di Setelan.');
      return;
    }
    setState(() {
      _sibuk = true;
      _hasil = null;
      _tahap = 'Membuat backup PENUH di laptop... (bisa 1-3 menit)';
    });
    try {
      final d = await klien.buatBackup(label: 'mobile');
      if (!mounted) return;
      setState(() {
        _sibuk = false;
        _tahap = '';
        _hasil = 'Backup BERHASIL.\n'
            'File   : ${d['file']}\n'
            'Lokasi : ${d['path']}\n'
            'Ukuran : ${d['size_text']}\n'
            'Waktu  : ${d['duration']} detik';
      });
      await _muatDaftar();
    } catch (e) {
      if (!mounted) return;
      setState(() {
        _sibuk = false;
        _tahap = '';
        _hasil = _pesanGagal(e);
      });
    }
  }

  /// Restore: konfirmasi -> mulai di laptop -> pantau status.
  Future<void> _restore(String namaFile) async {
    final ya = await showDialog<bool>(
      context: context,
      builder: (c) => AlertDialog(
        title: const Text('Restore data Synapse?'),
        content: Text(
          'Data Synapse SEKARANG akan DIGANTI dengan isi backup:\n\n'
          '"$namaFile"\n\n'
          'Laptop akan: (1) membuat backup pengaman, (2) menghentikan Synapse, '
          '(3) memulihkan data, (4) menyalakan Synapse lagi. '
          'Proses ini ~1-3 menit dan koneksi app akan terputus sebentar.\n\n'
          'Lanjutkan?',
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

    final klien = ref.read(apiClientProvider);
    if (klien == null) {
      _pesan('Belum tersambung.');
      return;
    }
    setState(() {
      _sibuk = true;
      _hasil = null;
      _tahap = 'Memulai restore di laptop...';
    });
    try {
      final d = await klien.mulaiRestore(namaFile);
      if (!mounted) return;
      setState(() {
        _tahap = 'Restore BERJALAN di laptop. Synapse berhenti sebentar...';
        _hasil = (d['catatan'] ?? 'Restore dimulai.').toString();
      });
      await _pantauRestore(klien);
    } catch (e) {
      if (!mounted) return;
      setState(() {
        _sibuk = false;
        _tahap = '';
        _hasil = _pesanGagal(e);
      });
    }
  }

  /// Pantau status restore sampai selesai (gateway hidup lagi).
  Future<void> _pantauRestore(dynamic klien) async {
    for (var i = 0; i < 60; i++) {
      await Future.delayed(const Duration(seconds: 5));
      if (!mounted) return;
      try {
        final st = await klien.statusRestore();
        final status = (st['status'] ?? '').toString();
        final step = (st['step'] ?? '').toString();
        if (!mounted) return;
        setState(() {
          _tahap = 'Restore: $status ($step) — ${i * 5 + 5}s';
        });
        if (status == 'ok' || status == 'failed') {
          setState(() {
            _sibuk = false;
            _tahap = '';
            _hasil = status == 'ok'
                ? 'RESTORE BERHASIL.\n\n${st['output'] ?? ''}'
                : 'RESTORE GAGAL.\n\n${st['output'] ?? ''}';
          });
          return;
        }
      } catch (_) {
        // gateway sedang mati/nyala — wajar, coba lagi
        if (!mounted) return;
        setState(() => _tahap = 'Menunggu Synapse menyala kembali... ${i * 5 + 5}s');
      }
    }
    if (!mounted) return;
    setState(() {
      _sibuk = false;
      _tahap = '';
      _hasil = 'Status restore tidak terpantau selesai. Cek "Cek Status Restore".';
    });
  }

  Future<void> _cekStatus() async {
    final klien = ref.read(apiClientProvider);
    if (klien == null) return;
    try {
      final st = await klien.statusRestore();
      if (!mounted) return;
      setState(() {
        _hasil = 'Status restore terakhir:\n'
            'status : ${st['status']}\n'
            'tahap  : ${st['step']}\n'
            'arsip  : ${st['arsip']}\n'
            'durasi : ${st['duration'] ?? '-'} detik\n\n'
            '${st['output'] ?? ''}';
      });
    } catch (e) {
      if (!mounted) return;
      setState(() => _hasil = _pesanGagal(e));
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
            onPressed: _sibuk ? null : _buatBackup,
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
            onPressed: _sibuk || _memuatDaftar ? null : _muatDaftar,
            icon: const Icon(Icons.refresh),
            label: Text(_memuatDaftar ? 'Memuat...' : 'Muat Ulang Daftar Backup'),
          ),

          const SizedBox(height: AppSpacing.lg),
          Row(children: [
            Text('Daftar Backup (${_daftar.length})',
                style: t.textTheme.titleSmall),
            const Spacer(),
            Text('ketuk untuk restore', style: t.textTheme.bodySmall),
          ]),
          const SizedBox(height: 6),
          if (_daftar.isEmpty)
            Card(
              child: ListTile(
                dense: true,
                leading: const Icon(Icons.inbox),
                title: Text(
                  _memuatDaftar ? 'Memuat daftar...' : 'Belum ada file backup.',
                  style: t.textTheme.bodySmall,
                ),
              ),
            )
          else
            Card(
              child: Column(children: [
                for (var i = 0; i < _daftar.length; i++) ...[
                  ListTile(
                    dense: true,
                    leading: const Icon(Icons.archive_outlined),
                    title: Text((_daftar[i]['name'] ?? '').toString(),
                        style: t.textTheme.bodyMedium),
                    subtitle: Text(
                        '${_daftar[i]['size_text'] ?? ''} · ketuk untuk restore',
                        style: t.textTheme.bodySmall),
                    trailing: const Icon(Icons.restore, size: 18),
                    onTap: _sibuk
                        ? null
                        : () => _restore((_daftar[i]['name'] ?? '').toString()),
                  ),
                  if (i < _daftar.length - 1) const Divider(height: 1),
                ],
              ]),
            ),

          const SizedBox(height: AppSpacing.lg),
          OutlinedButton.icon(
            onPressed: _sibuk ? null : _cekStatus,
            icon: const Icon(Icons.info_outline),
            label: const Text('Cek Status Restore'),
          ),

          if (_sibuk) ...[
            const SizedBox(height: AppSpacing.md),
            const LinearProgressIndicator(),
            if (_tahap.isNotEmpty) ...[
              const SizedBox(height: 6),
              Text(_tahap, style: t.textTheme.bodySmall),
            ],
          ],

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
