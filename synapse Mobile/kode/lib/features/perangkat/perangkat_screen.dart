import 'dart:convert';
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:go_router/go_router.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../core/api/api_config.dart';
import '../../core/api/api_providers.dart';
import '../../core/theme/spacing.dart';

/// M13 — PANEL PERANGKAT (kontrol HP lewat agent + ADB).
///
/// Cara kerja:
///   App kirim perintah -> agent di laptop -> agent jalankan `adb` -> HP.
///   Hasil dikembalikan sebagai teks.
///
/// Jadi app TIDAK minta izin SMS/kontak/lokasi. Kekuatan ada di agent.
class PerangkatScreen extends ConsumerStatefulWidget {
  const PerangkatScreen({super.key});
  @override
  ConsumerState<PerangkatScreen> createState() => _PerangkatScreenState();
}

class _PerangkatScreenState extends ConsumerState<PerangkatScreen> {
  final _input = TextEditingController();
  bool _sibuk = false;
  String? _hasil;

  // ---- Aksi cepat (satu ketuk) ----
  final _aksi = <Map<String, dynamic>>[
    {
      'nama': 'Daftar Aplikasi',
      'ikon': Icons.apps,
      'desk': 'Lihat semua app di HP',
      'cmd': 'Tampilkan 30 aplikasi pihak ketiga yang terpasang di HP saya '
          '(adb shell pm list packages -3), kelompokkan rapi.',
    },
    {
      'nama': 'Buka Aplikasi',
      'ikon': Icons.open_in_new,
      'desk': 'Jalankan app di HP',
      'cmd': '__BUKA__',
    },
    {
      'nama': 'Screenshot',
      'ikon': Icons.screenshot_monitor,
      'desk': 'Tangkap layar HP sekarang',
      'cmd': 'Ambil screenshot layar HP saya sekarang dengan '
          '`adb shell screencap -p /sdcard/syn.png` lalu `adb pull` ke '
          'folder kerja, dan laporkan ukuran file hasilnya.',
    },
    {
      'nama': 'Layar Sekarang',
      'ikon': Icons.visibility,
      'desk': 'Apa yang sedang tampil?',
      'cmd': 'Periksa apa yang sedang tampil di layar HP saya: jalankan '
          '`adb shell dumpsys activity activities | grep topResumedActivity` '
          'dan laporkan aplikasi yang sedang aktif.',
    },
    {
      'nama': 'Ketuk Layar',
      'ikon': Icons.touch_app,
      'desk': 'Tap di posisi x,y',
      'cmd': '__TAP__',
    },
    {
      'nama': 'Ketik Teks',
      'ikon': Icons.keyboard,
      'desk': 'Ketik di HP',
      'cmd': '__KETIK__',
    },
    {
      'nama': 'Buka URL',
      'ikon': Icons.link,
      'desk': 'Buka alamat web di HP',
      'cmd': '__URL__',
    },
    {
      'nama': 'Info Baterai',
      'ikon': Icons.battery_full,
      'desk': 'Status baterai HP',
      'cmd': 'Tampilkan status baterai HP saya (`adb shell dumpsys battery`) '
          'dan laporkan persentase + status pengisian.',
    },
    {
      'nama': 'Penyimpanan',
      'ikon': Icons.sd_storage,
      'desk': 'Ruang kosong HP',
      'cmd': 'Tampilkan ruang penyimpanan HP saya (`adb shell df -h /sdcard`) '
          'dan laporkan terpakai vs tersedia.',
    },
    {
      'nama': 'Rekam Layar',
      'ikon': Icons.videocam,
      'desk': 'Rekam 10 detik',
      'cmd': 'Rekam layar HP saya 10 detik (`adb shell screenrecord '
          '--time-limit 10 /sdcard/syn.mp4`) lalu `adb pull` ke folder kerja, '
          'laporkan ukuran filenya.',
    },
    {
      'nama': 'Isi Klipboard',
      'ikon': Icons.content_paste,
      'desk': 'Salin teks ke HP',
      'cmd': '__KLIP__',
    },
    {
      'nama': 'Cek Koneksi HP',
      'ikon': Icons.usb,
      'desk': 'HP tersambung?',
      'cmd': 'Periksa apakah HP saya tersambung ke laptop (`adb devices -l`) '
          'dan laporkan model + versi Android-nya.',
    },
    {
      'nama': 'Sambung Wireless',
      'ikon': Icons.wifi,
      'desk': 'Lepas kabel (WiFi)',
      'cmd': '__WIFI_ON__',
    },
    {
      'nama': 'Putus Wireless',
      'ikon': Icons.wifi_off,
      'desk': 'Kembali ke kabel',
      'cmd': '__WIFI_OFF__',
    },
    {
      'nama': 'Status Wireless',
      'ikon': Icons.network_check,
      'desk': 'Cek mode wireless',
      'cmd': 'Periksa status koneksi wireless ADB ke HP saya: jalankan '
          '`adb devices -l` dan laporkan apakah HP tersambung lewat USB atau '
          'WiFi (lihat ada alamat IP:5555 atau tidak).',
    },
  ];

  @override
  void dispose() {
    _input.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final t = Theme.of(context);
    final cfg = ref.watch(apiConfigProvider);
    final siap = cfg.terisi;

    return Scaffold(
      appBar: AppBar(
        title: const Text('Perangkat'),
        actions: [
          IconButton(
            tooltip: 'Mode Otonom (agent kerja sendiri)',
            icon: const Icon(Icons.auto_awesome),
            onPressed: () => context.push('/otonom'),
          ),
          IconButton(
            tooltip: 'Bersihkan hasil',
            icon: const Icon(Icons.refresh),
            onPressed: () => setState(() => _hasil = null),
          ),
        ],
      ),
      body: ListView(
        padding: const EdgeInsets.all(AppSpacing.md),
        children: [
          // ---- status koneksi ----
          Container(
            padding: const EdgeInsets.all(AppSpacing.md),
            decoration: BoxDecoration(
              color: (siap ? Colors.green : Colors.orange).withValues(alpha: 0.12),
              borderRadius: BorderRadius.circular(10),
              border: Border.all(
                  color: (siap ? Colors.green : Colors.orange).withValues(alpha: 0.4)),
            ),
            child: Row(children: [
              Icon(siap ? Icons.check_circle : Icons.warning_amber,
                  size: 18, color: siap ? Colors.green : Colors.orange),
              const SizedBox(width: 8),
              Expanded(
                child: Text(
                  siap
                      ? 'Terhubung ke agent. Perintah dijalankan di HP lewat '
                          'ADB (agent di laptop).'
                      : 'Belum tersambung. Isi Base URL + API Key di Setelan '
                          'dulu supaya bisa mengontrol HP.',
                  style: t.textTheme.bodySmall,
                ),
              ),
            ]),
          ),

          const SizedBox(height: AppSpacing.md),
          Text('Aksi Cepat', style: t.textTheme.titleSmall),
          Text('Ketuk untuk langsung menjalankan lewat agent',
              style: t.textTheme.bodySmall),
          const SizedBox(height: AppSpacing.sm),

          // ---- grid aksi ----
          GridView.builder(
            shrinkWrap: true,
            physics: const NeverScrollableScrollPhysics(),
            gridDelegate: const SliverGridDelegateWithFixedCrossAxisCount(
              crossAxisCount: 2,
              mainAxisSpacing: AppSpacing.sm,
              crossAxisSpacing: AppSpacing.sm,
              childAspectRatio: 1.35,
            ),
            itemCount: _aksi.length,
            itemBuilder: (c, i) {
              final a = _aksi[i];
              return Card(
                margin: EdgeInsets.zero,
                child: InkWell(
                  borderRadius: BorderRadius.circular(12),
                  onTap: (_sibuk || !siap) ? null : () => _jalankan(a),
                  child: Padding(
                    padding: const EdgeInsets.all(AppSpacing.sm),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      mainAxisAlignment: MainAxisAlignment.center,
                      children: [
                        Icon(a['ikon'] as IconData,
                            size: 22,
                            color: siap ? t.colorScheme.primary : t.disabledColor),
                        const SizedBox(height: 6),
                        Text(a['nama'] as String,
                            style: t.textTheme.labelLarge,
                            maxLines: 1,
                            overflow: TextOverflow.ellipsis),
                        Text(a['desk'] as String,
                            style: t.textTheme.bodySmall,
                            maxLines: 2,
                            overflow: TextOverflow.ellipsis),
                      ],
                    ),
                  ),
                ),
              );
            },
          ),

          const SizedBox(height: AppSpacing.lg),
          Text('Perintah Bebas', style: t.textTheme.titleSmall),
          const SizedBox(height: AppSpacing.sm),
          TextField(
            controller: _input,
            maxLines: 2,
            decoration: const InputDecoration(
              hintText: 'Contoh: buka WhatsApp lalu kirim pesan ke Budi',
              border: OutlineInputBorder(),
              isDense: true,
            ),
          ),
          const SizedBox(height: AppSpacing.sm),
          FilledButton.icon(
            onPressed: (_sibuk || !siap) ? null : _kirimBebas,
            icon: const Icon(Icons.play_arrow),
            label: const Text('Jalankan'),
          ),

          // ---- hasil ----
          if (_sibuk) ...[
            const SizedBox(height: AppSpacing.lg),
            const Center(child: CircularProgressIndicator()),
            const SizedBox(height: AppSpacing.sm),
            Center(
                child: Text('Agent sedang mengerjakan...',
                    style: t.textTheme.bodySmall)),
          ],
          if (_hasil != null) ...[
            const SizedBox(height: AppSpacing.lg),
            Row(children: [
              Text('Hasil', style: t.textTheme.titleSmall),
              const Spacer(),
              IconButton(
                tooltip: 'Salin',
                icon: const Icon(Icons.copy, size: 18),
                onPressed: () {
                  Clipboard.setData(ClipboardData(text: _hasil!));
                  ScaffoldMessenger.of(context).showSnackBar(
                      const SnackBar(content: Text('Hasil disalin')));
                },
              ),
            ]),
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

  // ---------------- AKSI ----------------

  Future<void> _jalankan(Map<String, dynamic> a) async {
    final cmd = a['cmd'] as String;

    // aksi yang butuh input tambahan
    if (cmd == '__BUKA__') return _dialogBuka();
    if (cmd == '__TAP__') return _dialogTap();
    if (cmd == '__KETIK__') return _dialogKetik();
    if (cmd == '__URL__') return _dialogUrl();
    if (cmd == '__KLIP__') return _dialogKlip();
    if (cmd == '__WIFI_ON__') return _dialogWifi(true);
    if (cmd == '__WIFI_OFF__') return _dialogWifi(false);

    await _kirim(cmd);
  }

  Future<void> _kirimBebas() async {
    final teks = _input.text.trim();
    if (teks.isEmpty) return;
    await _kirim(
        'Di HP Android saya (tersambung lewat adb di laptop), $teks. '
        'Jalankan dengan adb, lalu laporkan hasilnya singkat.');
  }

  Future<void> _kirim(String perintah) async {
    final klien = ref.read(apiClientProvider);
    if (klien == null) return;
    // Catatan penting: kalau ada >1 device (USB + WiFi), agent WAJIB pakai -s.
    perintah = '$perintah\n\n'
        '(Catatan: kalau `adb devices` menampilkan lebih dari satu device '
        '— misal USB dan WiFi bersamaan — WAJIB pakai `-s <serial>` supaya '
        'tidak error "more than one device".)';
    setState(() {
      _sibuk = true;
      _hasil = null;
    });
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

  // ---------------- DIALOG ----------------

  Future<void> _dialogBuka() async {
    final c = TextEditingController();
    final nama = await showDialog<String>(
      context: context,
      builder: (x) => AlertDialog(
        title: const Text('Buka aplikasi di HP'),
        content: TextField(
          controller: c,
          autofocus: true,
          decoration: const InputDecoration(
            labelText: 'Nama / paket aplikasi',
            hintText: 'Contoh: whatsapp, com.instagram.android',
          ),
        ),
        actions: [
          TextButton(onPressed: () => Navigator.pop(x), child: const Text('Batal')),
          FilledButton(
              onPressed: () => Navigator.pop(x, c.text.trim()),
              child: const Text('Buka')),
        ],
      ),
    );
    if (nama == null || nama.isEmpty) return;
    await _kirim(
        'Buka aplikasi "$nama" di HP saya (pakai `adb shell monkey -p <paket> '
        '-c android.intent.category.LAUNCHER 1`, atau cari paketnya dulu dengan '
        '`adb shell pm list packages | grep -i $nama`). Laporkan berhasil/gagal.');
  }

  Future<void> _dialogTap() async {
    final x = TextEditingController();
    final y = TextEditingController();
    final ok = await showDialog<bool>(
      context: context,
      builder: (c) => AlertDialog(
        title: const Text('Ketuk layar HP'),
        content: Column(mainAxisSize: MainAxisSize.min, children: [
          Row(children: [
            Expanded(
                child: TextField(
                    controller: x,
                    keyboardType: TextInputType.number,
                    decoration: const InputDecoration(labelText: 'X'))),
            const SizedBox(width: 8),
            Expanded(
                child: TextField(
                    controller: y,
                    keyboardType: TextInputType.number,
                    decoration: const InputDecoration(labelText: 'Y'))),
          ]),
          const SizedBox(height: 8),
          const Text('Layar HP Anda: 1220 x 2712 px',
              style: TextStyle(fontSize: 11)),
        ]),
        actions: [
          TextButton(onPressed: () => Navigator.pop(c, false), child: const Text('Batal')),
          FilledButton(onPressed: () => Navigator.pop(c, true), child: const Text('Ketuk')),
        ],
      ),
    );
    if (ok != true) return;
    await _kirim('Ketuk layar HP saya di posisi x=${x.text}, y=${y.text} '
        '(`adb shell input tap ${x.text} ${y.text}`). Laporkan hasilnya.');
  }

  Future<void> _dialogKetik() async {
    final c = TextEditingController();
    final teks = await showDialog<String>(
      context: context,
      builder: (x) => AlertDialog(
        title: const Text('Ketik di HP'),
        content: TextField(
            controller: c,
            autofocus: true,
            decoration: const InputDecoration(
                labelText: 'Teks', hintText: 'Halo, ini dari Synapse')),
        actions: [
          TextButton(onPressed: () => Navigator.pop(x), child: const Text('Batal')),
          FilledButton(
              onPressed: () => Navigator.pop(x, c.text.trim()),
              child: const Text('Ketik')),
        ],
      ),
    );
    if (teks == null || teks.isEmpty) return;
    final aman = teks.replaceAll(' ', '%s');
    await _kirim('Ketik teks ini di HP saya: "$teks" '
        '(`adb shell input text "$aman"`). Laporkan hasilnya.');
  }

  Future<void> _dialogUrl() async {
    final c = TextEditingController();
    final url = await showDialog<String>(
      context: context,
      builder: (x) => AlertDialog(
        title: const Text('Buka URL di HP'),
        content: TextField(
            controller: c,
            autofocus: true,
            keyboardType: TextInputType.url,
            decoration: const InputDecoration(
                labelText: 'Alamat', hintText: 'https://google.com')),
        actions: [
          TextButton(onPressed: () => Navigator.pop(x), child: const Text('Batal')),
          FilledButton(
              onPressed: () => Navigator.pop(x, c.text.trim()),
              child: const Text('Buka')),
        ],
      ),
    );
    if (url == null || url.isEmpty) return;
    await _kirim('Buka alamat ini di browser HP saya: $url '
        '(`adb shell am start -a android.intent.action.VIEW -d "$url"`). '
        'Laporkan hasilnya.');
  }

  /// M14 - Wireless ADB: sambung/putus tanpa kabel.
  Future<void> _dialogWifi(bool nyalakan) async {
    final c = TextEditingController(text: '192.168.1.7');
    final ip = await showDialog<String>(
      context: context,
      builder: (x) => AlertDialog(
        title: Text(nyalakan ? 'Sambung Wireless ADB' : 'Putus Wireless ADB'),
        content: Column(mainAxisSize: MainAxisSize.min, children: [
          if (nyalakan) ...[
            const Text(
                'HP dan laptop harus di WiFi yang SAMA.\n'
                'Masukkan IP HP (lihat di Setelan > WiFi > Detail):',
                style: TextStyle(fontSize: 12)),
            const SizedBox(height: 10),
            TextField(
              controller: c,
              autofocus: true,
              keyboardType: TextInputType.number,
              decoration: const InputDecoration(
                  labelText: 'IP HP', hintText: '192.168.1.7'),
            ),
            const SizedBox(height: 8),
            const Text('Port: 5555 (otomatis)',
                style: TextStyle(fontSize: 11)),
          ] else
            const Text('Kembalikan HP ke mode kabel (USB)?'),
        ]),
        actions: [
          TextButton(
              onPressed: () => Navigator.pop(x), child: const Text('Batal')),
          FilledButton(
            onPressed: () => Navigator.pop(x, nyalakan ? c.text.trim() : 'ok'),
            child: Text(nyalakan ? 'Sambung' : 'Putus'),
          ),
        ],
      ),
    );
    if (ip == null || ip.isEmpty) return;

    if (nyalakan) {
      await _kirim(
          'Aktifkan wireless ADB ke HP saya di alamat $ip port 5555. '
          'Langkah: (1) pastikan HP tersambung USB dulu, '
          '(2) jalankan `adb tcpip 5555`, '
          '(3) tunggu 3 detik, '
          '(4) jalankan `adb connect $ip:5555`, '
          '(5) verifikasi dengan `adb devices -l` dan laporkan apakah muncul '
          'koneksi IP:5555. Pakai adb di '
          'C:/Users/user/AppData/Local/Android/Sdk/platform-tools/adb.exe. '
          'Laporkan hasilnya singkat.');
    } else {
      await _kirim(
          'Putuskan koneksi wireless ADB ke HP saya dan kembalikan ke mode USB: '
          'jalankan `adb disconnect` lalu `adb usb`, dan laporkan hasilnya.');
    }
  }

  Future<void> _dialogKlip() async {
    final c = TextEditingController();
    final teks = await showDialog<String>(
      context: context,
      builder: (x) => AlertDialog(
        title: const Text('Salin teks ke HP'),
        content: TextField(
            controller: c,
            autofocus: true,
            maxLines: 3,
            decoration: const InputDecoration(
                labelText: 'Teks yang mau disalin ke HP')),
        actions: [
          TextButton(onPressed: () => Navigator.pop(x), child: const Text('Batal')),
          FilledButton(
              onPressed: () => Navigator.pop(x, c.text.trim()),
              child: const Text('Salin')),
        ],
      ),
    );
    if (teks == null || teks.isEmpty) return;
    await _kirim('Salin teks berikut ke clipboard HP saya: "$teks". '
        'Gunakan cara yang benar untuk Android (mis. lewat `adb shell am '
        'broadcast` atau service clipboard), lalu laporkan hasilnya.');
  }
}
