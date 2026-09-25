import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../core/api/api_config.dart';
import '../../core/api/api_providers.dart';
import '../../core/theme/spacing.dart';

/// M15 — PANEL OTONOM: agent LIHAT layar HP -> PUTUSKAN -> TAP sendiri.
///
/// Cara kerja (terbukti):
///   1. Agent baca layar HP (uiautomator dump -> daftar elemen + koordinat)
///   2. Agent pikirkan langkah berikutnya
///   3. Agent tap/ketik sendiri lewat adb
///   4. Ulangi sampai tugas selesai
class OtonomScreen extends ConsumerStatefulWidget {
  const OtonomScreen({super.key});
  @override
  ConsumerState<OtonomScreen> createState() => _OtonomScreenState();
}

class _OtonomScreenState extends ConsumerState<OtonomScreen> {
  final _tugas = TextEditingController();
  bool _sibuk = false;
  String? _hasil;
  int _langkah = 0;

  @override
  void dispose() {
    _tugas.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final t = Theme.of(context);
    final siap = ref.watch(apiConfigProvider).terisi;

    return Scaffold(
      appBar: AppBar(title: const Text('Mode Otonom')),
      body: ListView(
        padding: const EdgeInsets.all(AppSpacing.md),
        children: [
          Container(
            padding: const EdgeInsets.all(AppSpacing.md),
            decoration: BoxDecoration(
              color: Colors.purple.withValues(alpha: 0.10),
              borderRadius: BorderRadius.circular(10),
              border: Border.all(color: Colors.purple.withValues(alpha: 0.35)),
            ),
            child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
              Row(children: [
                const Icon(Icons.auto_awesome, size: 18, color: Colors.purple),
                const SizedBox(width: 8),
                Text('Agent bekerja sendiri', style: t.textTheme.titleSmall),
              ]),
              const SizedBox(height: 6),
              Text(
                'Agent akan MELIHAT layar HP, MEMUTUSKAN langkah, lalu '
                'MENGETUK sendiri — berulang sampai tugas selesai. '
                'HP Anda akan bergerak sendiri (normal).',
                style: t.textTheme.bodySmall,
              ),
            ]),
          ),

          const SizedBox(height: AppSpacing.lg),
          Text('Tugas untuk agent', style: t.textTheme.titleSmall),
          const SizedBox(height: AppSpacing.sm),
          TextField(
            controller: _tugas,
            maxLines: 3,
            decoration: const InputDecoration(
              hintText: 'Contoh: Buka WhatsApp, cari chat "Budi", '
                  'lalu kirim pesan "Halo"',
              border: OutlineInputBorder(),
            ),
          ),

          const SizedBox(height: AppSpacing.md),
          Text('Contoh cepat:', style: t.textTheme.bodySmall),
          const SizedBox(height: 6),
          Wrap(spacing: 6, runSpacing: 6, children: [
            _chip('Buka Setelan lalu masuk Wi-Fi'),
            _chip('Buka WhatsApp dan tunjukkan chat teratas'),
            _chip('Buka Kamera lalu ambil foto'),
            _chip('Nyalakan mode pesawat lalu matikan'),
          ]),

          const SizedBox(height: AppSpacing.lg),
          FilledButton.icon(
            onPressed: (_sibuk || !siap) ? null : _jalankan,
            icon: _sibuk
                ? const SizedBox(
                    width: 16, height: 16,
                    child: CircularProgressIndicator(strokeWidth: 2))
                : const Icon(Icons.play_circle),
            label: Text(_sibuk ? 'Agent bekerja...' : 'Jalankan Otonom'),
            style: FilledButton.styleFrom(
              minimumSize: const Size(double.infinity, 48),
              backgroundColor: Colors.purple,
            ),
          ),

          if (!siap) ...[
            const SizedBox(height: AppSpacing.sm),
            Text('Isi Base URL + API Key dulu di Setelan > Koneksi AI.',
                style: t.textTheme.bodySmall),
          ],

          if (_sibuk) ...[
            const SizedBox(height: AppSpacing.lg),
            Center(
              child: Column(children: [
                const CircularProgressIndicator(),
                const SizedBox(height: AppSpacing.sm),
                Text('Agent sedang melihat & mengerjakan...',
                    style: t.textTheme.bodySmall),
                Text('Langkah ke-$_langkah',
                    style: t.textTheme.bodySmall),
              ]),
            ),
          ],

          if (_hasil != null) ...[
            const SizedBox(height: AppSpacing.lg),
            Text('Laporan agent', style: t.textTheme.titleSmall),
            const SizedBox(height: AppSpacing.sm),
            Container(
              width: double.infinity,
              padding: const EdgeInsets.all(AppSpacing.md),
              decoration: BoxDecoration(
                color: t.colorScheme.surfaceContainerHighest,
                borderRadius: BorderRadius.circular(10),
              ),
              child: SelectableText(_hasil!, style: t.textTheme.bodySmall),
            ),
          ],
        ],
      ),
    );
  }

  Widget _chip(String teks) => ActionChip(
        label: Text(teks, style: const TextStyle(fontSize: 11)),
        onPressed: () => setState(() => _tugas.text = teks),
      );

  Future<void> _jalankan() async {
    final tugas = _tugas.text.trim();
    if (tugas.isEmpty) return;
    final klien = ref.read(apiClientProvider);
    if (klien == null) return;

    setState(() {
      _sibuk = true;
      _hasil = null;
      _langkah = 0;
    });

    final perintah =
        'KERJAKAN TUGAS INI DI HP ANDROID SAYA SECARA OTONOM (sendiri):\n'
        'TUGAS: $tugas\n\n'
        'CARA KERJA (ikuti berulang sampai tugas selesai):\n'
        '1. LIHAT layar HP:\n'
        '   - `adb -s IJW8EII77HJVOVZ5 shell uiautomator dump /sdcard/u.xml`\n'
        '   - `adb -s IJW8EII77HJVOVZ5 shell cat /sdcard/u.xml`\n'
        '   - dari XML itu, baca daftar elemen + koordinat bounds-nya\n'
        '   - kalau uiautomator kosong (app Flutter), pakai screenshot + '
        'baca piksel/OCR\n'
        '2. PUTUSKAN langkah berikutnya (tap di mana / ketik apa)\n'
        '3. LAKUKAN: `adb -s IJW8EII77HJVOVZ5 shell input tap X Y` atau '
        '`input text "..."` atau `input swipe ...`\n'
        '4. Tunggu 2 detik, lalu ULANGI dari langkah 1\n'
        '5. BERHENTI kalau tugas sudah selesai atau mentok (max 15 langkah)\n\n'
        'CATATAN PENTING:\n'
        '- adb ada di C:/Users/user/AppData/Local/Android/Sdk/platform-tools/adb.exe\n'
        '- SELALU pakai -s IJW8EII77HJVOVZ5 (ada 2 device: USB + WiFi)\n'
        '- Kalau ada lebih dari satu device tanpa -s -> error\n'
        '- Laporkan: langkah apa saja yang dilakukan + hasil akhirnya';

    try {
      final h = await klien.perintahAgent(perintah);
      if (!mounted) return;
      setState(() => _hasil = h);
    } catch (e) {
      if (!mounted) return;
      setState(() => _hasil = 'Gagal: $e');
    } finally {
      if (mounted) setState(() => _sibuk = false);
    }
  }
}
