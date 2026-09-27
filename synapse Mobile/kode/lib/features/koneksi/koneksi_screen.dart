import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import '../../core/api/api_client.dart';
import '../../core/api/api_config.dart';
import '../../core/api/api_providers.dart';
import '../../core/theme/spacing.dart';

/// Layar pengaturan koneksi AI:
///  1. Isi Base URL + API Key
///  2. Klik "Deteksi Model" -> app ambil daftar model dari server
///  3. Pilih model (atau "ya/tidak" kalau cuma 1)
///  4. Atur context window + display name
class KoneksiScreen extends ConsumerStatefulWidget {
  const KoneksiScreen({super.key});
  @override
  ConsumerState<KoneksiScreen> createState() => _KoneksiScreenState();
}

class _KoneksiScreenState extends ConsumerState<KoneksiScreen> {
  late TextEditingController _url;
  late TextEditingController _key;
  late TextEditingController _name;
  late TextEditingController _ctx;
  late TextEditingController _manual;
  String _vision = 'auto';

  List<String> _model = [];
  String? _dipilih;
  bool _sibuk = false;
  String? _pesan;
  bool _ok = false;

  @override
  void initState() {
    super.initState();
    final c = ref.read(apiConfigProvider);
    // JEBAKAN #103 (v1.2.6): DULU kalau kosong diisi teks ASLI
    // 'http://127.0.0.1:8642' -> user harus HAPUS manual dulu (merepotkan).
    // Sekarang kolom BENAR-BENAR kosong; contoh hanya HINT (visual).
    _url = TextEditingController(text: c.baseUrl);
    _key = TextEditingController(text: c.apiKey);
    _name = TextEditingController(text: c.displayName ?? '');
    _ctx = TextEditingController(text: (c.contextWindow ?? 128000).toString());
    _manual = TextEditingController();
    _dipilih = c.model;
    _vision = c.visionProvider;
  }

  @override
  void dispose() {
    _url.dispose(); _key.dispose(); _name.dispose(); _ctx.dispose(); _manual.dispose();
    super.dispose();
  }

  Future<void> _deteksi() async {
    setState(() { _sibuk = true; _pesan = null; });
    try {
      final cfg = ApiConfig(baseUrl: _url.text.trim(), apiKey: _key.text.trim());
      final klien = ApiClient(cfg);
      final h = await klien.health(); // TOLERAN: boleh null (tanpa /health)
      final m = await klien.daftarModel();
      setState(() {
        _model = m;
        _dipilih = m.isNotEmpty ? m.first : null;
        _ok = true;
        final info = (h == null)
            ? 'Terhubung — ${m.length} model ditemukan'
            : 'Terhubung ke ${h['platform'] ?? 'server'} v${h['version'] ?? '?'} — ${m.length} model ditemukan';
        _pesan = info;
      });
    } catch (e) {
      setState(() { _ok = false; _pesan = 'Gagal: $e'; });
    } finally {
      setState(() => _sibuk = false);
    }
  }

  /// Hapus konfigurasi (Base URL + API Key) DENGAN konfirmasi.
  /// Permintaan user v1.2.4: biar bisa mengosongkan cepat tanpa hapus 1-1.
  Future<void> _hapusKonfigurasi() async {
    final ya = await showDialog<bool>(
      context: context,
      builder: (c) => AlertDialog(
        title: const Text('Hapus konfigurasi?'),
        content: const Text(
            'Apakah kamu ingin menghapus konfigurasi yang sudah ada dan ingin menggantinya?\n\n'
            'Base URL dan API Key akan DIKOSONGKAN, dan koneksi AI dimatikan. '
            'Kamu harus mengetik ulang untuk menyambung lagi.'),
        actions: [
          TextButton(
              onPressed: () => Navigator.pop(c, false),
              child: const Text('Tidak')),
          FilledButton(
            style: FilledButton.styleFrom(backgroundColor: Colors.red),
            onPressed: () => Navigator.pop(c, true),
            child: const Text('Ya, hapus'),
          ),
        ],
      ),
    );
    if (ya != true) return;

    await ref.read(apiConfigProvider.notifier).kosongkan();
    if (!mounted) return;
    setState(() {
      _url.clear();
      _key.clear();
      _name.clear();
      _manual.clear();
      _model = [];
      _dipilih = null;
      _pesan = null;
      _ok = false;
    });
    ScaffoldMessenger.of(context).showSnackBar(
      const SnackBar(
          content: Text('Konfigurasi dihapus — Base URL & API Key dikosongkan')),
    );
  }

  /// Apakah isian form sekarang SAMA dengan config tersimpan (draft)?
  bool get _samaDenganTersimpan {
    final c = ref.read(apiConfigProvider);
    return _url.text.trim() == c.baseUrl &&
        _key.text.trim() == c.apiKey &&
        _dipilih == c.model &&
        _vision == c.visionProvider &&
        _name.text.trim() == (c.displayName ?? '');
  }

  /// Apakah konfigurasi sudah LENGKAP (base url + api key + model)?
  bool get _lengkap =>
      _url.text.trim().isNotEmpty &&
      _key.text.trim().isNotEmpty &&
      (_dipilih != null || _manual.text.trim().isNotEmpty);

  /// Apakah konfigurasi sudah TERBUKTI VALID (pernah dites ke server & sukses)?
  bool get _tervalidasi => ref.read(apiConfigProvider).tervalidasi;

  /// Simpan konfigurasi — DENGAN konfirmasi + validasi 100%.
  ///
  /// Permintaan user v1.2.6: user harus tahu persis berhasil atau tidak,
  /// dan kalau gagal HARUS diberi tahu APA yang salah/kurang.
  Future<void> _simpan({bool dariKeluar = false}) async {
    // 1. Konfirmasi "apakah ingin menyimpan?"
    if (!dariKeluar) {
      final ya = await showDialog<bool>(
        context: context,
        builder: (c) => AlertDialog(
          title: const Text('Simpan konfigurasi?'),
          content: const Text(
              'Apakah anda ingin menyimpan konfigurasi ini?'),
          actions: [
            TextButton(
                onPressed: () => Navigator.pop(c, false),
                child: const Text('Tidak')),
            FilledButton(
                onPressed: () => Navigator.pop(c, true),
                child: const Text('Ya, simpan')),
          ],
        ),
      );
      if (ya != true) return;
    }

    // 2. Cek kelengkapan dasar
    final c = ApiConfig(
      baseUrl: _url.text.trim(),
      apiKey: _key.text.trim(),
      model: _dipilih ?? (_manual.text.trim().isEmpty ? null : _manual.text.trim()),
      displayName: _name.text.trim().isEmpty ? null : _name.text.trim(),
      contextWindow: int.tryParse(_ctx.text.trim()),
      visionProvider: _vision,
      visionModel: _vision == 'auto' ? null : _vision,
    );

    setState(() => _sibuk = true);
    // UMPAN BALIK LANGSUNG (v1.2.6): tampilkan "Memeriksa..." SEKETIKA,
    // supaya user tahu sedang diproses (dulu: layar diam -> terasa 4-5 detik).
    if (mounted) {
      showDialog<void>(
        context: context,
        barrierDismissible: false,
        builder: (_) => const AlertDialog(
          content: Row(children: [
            SizedBox(
                width: 22, height: 22,
                child: CircularProgressIndicator(strokeWidth: 2.5)),
            SizedBox(width: 16),
            Expanded(child: Text('Memeriksa konfigurasi...')),
          ]),
        ),
      );
    }
    try {
      // 3. VALIDASI 100% — benar-benar bisa dipakai chat?
      final masalah = await ApiClient(c).validasi();
      if (!mounted) return;
      Navigator.of(context, rootNavigator: true).pop(); // tutup "Memeriksa..."

      if (masalah.isNotEmpty) {
        // GAGAL -> draft tetap tersimpan (progress user TIDAK hilang),
        // tapi BELUM tervalidasi -> jangan sampai salah bilang "selesai".
        await ref.read(apiConfigProvider.notifier).simpanDraft(c);
        if (!mounted) return;
        await showDialog<void>(
          context: context,
          builder: (ctx) => AlertDialog(
            icon: const Icon(Icons.cancel, color: Colors.red, size: 56),
            title: const Text('Konfigurasi GAGAL',
                style: TextStyle(color: Colors.red)),
            content: SingleChildScrollView(
              child: Column(
                mainAxisSize: MainAxisSize.min,
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  const Text('Chat BELUM bisa dipakai. Yang perlu diperbaiki:',
                      style: TextStyle(fontWeight: FontWeight.bold)),
                  const SizedBox(height: 10),
                  for (final m in masalah) ...[
                    Text('✗ ${m['judul']}',
                        style: const TextStyle(
                            color: Colors.red, fontWeight: FontWeight.bold)),
                    Padding(
                      padding: const EdgeInsets.only(left: 16, top: 2, bottom: 8),
                      child: Text(m['saran'] ?? '',
                          style: const TextStyle(fontSize: 12)),
                    ),
                  ],
                  const Divider(),
                  const Text(
                      'Isianmu SUDAH disimpan sebagai draft — tidak perlu '
                      'mengetik ulang. Perbaiki lalu simpan lagi.',
                      style: TextStyle(fontSize: 12, fontStyle: FontStyle.italic)),
                ],
              ),
            ),
            actions: [
              FilledButton(
                style: FilledButton.styleFrom(backgroundColor: Colors.red),
                onPressed: () => Navigator.pop(ctx),
                child: const Text('Perbaiki'),
              ),
            ],
          ),
        );
        return; // tetap di layar
      }

      // 4. VALID -> simpan + TANDAI tervalidasi (bukti 100% sudah selesai)
      await ref.read(apiConfigProvider.notifier).simpan(c.copyWith(tervalidasi: true));
      if (!mounted) return;
      await showDialog<void>(
        context: context,
        builder: (ctx) => AlertDialog(
          icon: const Icon(Icons.check_circle, color: Colors.green, size: 56),
          title: const Text('Konfigurasi BERHASIL',
              style: TextStyle(color: Colors.green)),
          content: const Text(
              'Konfigurasi valid dan tersimpan.\nChat sudah siap dipakai.'),
          actions: [
            FilledButton(
              style: FilledButton.styleFrom(backgroundColor: Colors.green),
              onPressed: () {
                Navigator.pop(ctx);
                if (dariKeluar) Navigator.pop(context); // keluar dari layar
              },
              child: const Text('Selesai'),
            ),
          ],
        ),
      );
    } finally {
      if (mounted) setState(() => _sibuk = false);
    }
  }

  /// Dipanggil saat user mau KELUAR dari layar ini (tombol back / back sistem).
  ///
  /// DETEKSI 100% (permintaan tim): status ditentukan oleh
  /// `tervalidasi` — penanda yang HANYA di-set kalau konfigurasi benar-benar
  /// sudah divalidasi nyata ke server & BERHASIL. Jadi app TIDAK akan salah
  /// bilang "belum selesai" padahal user sudah beres.
  Future<bool> _konfirmasiKeluar() async {
    // Sudah TERSIMPAN & TERBUKTI VALID -> langsung boleh keluar (tanpa nag).
    if (_tervalidasi && _samaDenganTersimpan) return true;

    // Ada isian yang belum disimpan -> simpan draft dulu (progress TIDAK hilang).
    if (!_samaDenganTersimpan && _lengkap) {
      final ya = await showDialog<bool>(
        context: context,
        builder: (c) => AlertDialog(
          title: const Text('Simpan konfigurasi ini?'),
          content: const Text(
              'Apakah anda ingin menyimpan konfigurasi ini?\n\n'
              'Kalau tidak disimpan, isian ini hilang.'),
          actions: [
            TextButton(
                onPressed: () => Navigator.pop(c, false),
                child: const Text('Tidak')),
            FilledButton(
                onPressed: () => Navigator.pop(c, true),
                child: const Text('Ya, simpan')),
          ],
        ),
      );
      if (ya == true) {
        await _simpan(dariKeluar: true); // validasi + laporan
        return false; // keluar ditangani dialog hasil
      }
      return false; // "Tidak" -> tetap di layar
    }

    // BELUM SELESAI / belum tervalidasi -> TAHAP 1: konfirmasi keluar
    // + jelaskan APA YANG KURANG (permintaan tim: jangan sekadar bilang
    //   "belum selesai" tanpa alasan yang jelas).
    final kurang = <String>[];
    if (_url.text.trim().isEmpty) kurang.add('Base URL belum diisi');
    if (_key.text.trim().isEmpty) kurang.add('API Key belum diisi');
    if (_dipilih == null && _manual.text.trim().isEmpty) {
      kurang.add('Model belum dipilih (tekan "Deteksi Model")');
    }
    if (kurang.isEmpty && !_tervalidasi) {
      kurang.add('Konfigurasi belum diverifikasi ke server '
          '(tekan "Simpan" untuk memeriksa)');
    }

    final keluar = await showDialog<bool>(
      context: context,
      builder: (c) => AlertDialog(
        icon: const Icon(Icons.help_outline, color: Colors.orange, size: 48),
        title: const Text('Konfigurasi belum selesai'),
        content: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            const Text('Yang masih KURANG:',
                style: TextStyle(fontWeight: FontWeight.bold)),
            const SizedBox(height: 6),
            for (final k in kurang)
              Padding(
                padding: const EdgeInsets.only(top: 2),
                child: Text('• $k', style: const TextStyle(fontSize: 13)),
              ),
            const SizedBox(height: 10),
            const Text('Apakah anda ingin keluar?'),
          ],
        ),
        actions: [
          FilledButton(
              onPressed: () => Navigator.pop(c, false),
              child: const Text('Lanjutkan konfigurasi')),
          TextButton(
              onPressed: () => Navigator.pop(c, true),
              child: const Text('Keluar')),
        ],
      ),
    );
    if (keluar != true) return false;
    if (!mounted) return false;

    // Simpan draft supaya progress user TIDAK hilang walau keluar.
    if (!_samaDenganTersimpan) {
      final draft = ApiConfig(
        baseUrl: _url.text.trim(),
        apiKey: _key.text.trim(),
        model: _dipilih ?? (_manual.text.trim().isEmpty ? null : _manual.text.trim()),
        displayName: _name.text.trim().isEmpty ? null : _name.text.trim(),
        contextWindow: int.tryParse(_ctx.text.trim()),
        visionProvider: _vision,
        visionModel: _vision == 'auto' ? null : _vision,
      );
      await ref.read(apiConfigProvider.notifier).simpanDraft(draft);
      if (!mounted) return false;
    }

    // TAHAP 2: SILANG MERAH BESAR (user MEMAKSA keluar)
    await showDialog<void>(
      context: context,
      builder: (c) => AlertDialog(
        icon: const Icon(Icons.cancel, color: Colors.red, size: 64),
        title: const Text('KONFIGURASI BELUM SELESAI',
            style: TextStyle(color: Colors.red, fontWeight: FontWeight.bold)),
        content: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            const Text('Yang masih KURANG:',
                style: TextStyle(
                    color: Colors.red, fontWeight: FontWeight.bold)),
            const SizedBox(height: 6),
            for (final k in kurang)
              Padding(
                padding: const EdgeInsets.only(top: 2),
                child: Text('• $k',
                    style: const TextStyle(
                        color: Colors.red, fontSize: 13)),
              ),
            const SizedBox(height: 10),
            const Text('SYNAPSE BELUM BISA DIPAKAI.',
                style: TextStyle(
                    color: Colors.red, fontWeight: FontWeight.bold)),
            const SizedBox(height: 8),
            const Text(
                'Chat akan tetap menampilkan "Belum tersambung" sampai '
                'konfigurasi diselesaikan.\n\n'
                'Isianmu sudah DISIMPAN sebagai draft — buka lagi: '
                'Setelan -> Koneksi AI.',
                style: TextStyle(fontSize: 12)),
          ],
        ),
        actions: [
          FilledButton(
            style: FilledButton.styleFrom(backgroundColor: Colors.red),
            onPressed: () => Navigator.pop(c),
            child: const Text('Saya mengerti'),
          ),
        ],
      ),
    );
    return true;
  }

  @override
  Widget build(BuildContext context) {
    final t = Theme.of(context);
    return PopScope(
      canPop: false,
      onPopInvokedWithResult: (didPop, _) async {
        if (didPop) return;
        final boleh = await _konfirmasiKeluar();
        if (boleh && mounted) Navigator.pop(context);
      },
      child: Scaffold(
      appBar: AppBar(
        title: const Text('Koneksi AI'),
        leading: IconButton(
          icon: const Icon(Icons.arrow_back),
          onPressed: () async {
            final boleh = await _konfirmasiKeluar();
            if (boleh && mounted) Navigator.pop(context);
          },
        ),
        actions: [
          // Tombol Simpan SELALU terlihat di AppBar (tidak perlu scroll)
          TextButton.icon(
            onPressed: _sibuk ? null : _simpan,
            icon: const Icon(Icons.save, size: 18),
            label: const Text('Simpan'),
          ),
          const SizedBox(width: 8),
        ],
      ),
      body: ListView(
      padding: const EdgeInsets.all(AppSpacing.md),
      children: [
        // ================================================================
        // BAGIAN 1 — KONEKSI SERVER (Base URL + API Key)
        // ================================================================
        Row(children: [
          Icon(Icons.dns, size: 18, color: t.colorScheme.primary),
          const SizedBox(width: 8),
          Expanded(
            child: Text('Koneksi Server', style: t.textTheme.titleSmall),
          ),
          // TOMBOL MERAH: kosongkan Base URL + API Key dengan cepat
          // (permintaan user v1.2.4) — tanpa hapus karakter satu per satu.
          TextButton.icon(
            onPressed: _sibuk ? null : _hapusKonfigurasi,
            style: TextButton.styleFrom(
              foregroundColor: Colors.red,
              visualDensity: VisualDensity.compact,
              padding: const EdgeInsets.symmetric(horizontal: 8),
            ),
            icon: const Icon(Icons.delete_forever, size: 18, color: Colors.red),
            label: const Text('Hapus Konfigurasi',
                style: TextStyle(color: Colors.red, fontSize: 12)),
          ),
        ]),
        const SizedBox(height: 4),
        Text('Masukkan Base URL dan API Key Synapse, lalu deteksi model.',
            style: t.textTheme.bodySmall),
        const SizedBox(height: AppSpacing.sm),

        TextField(
          controller: _url,
          decoration: InputDecoration(
            labelText: 'Base URL',
            // HINT = hanya VISUAL: abu-abu sangat pudar, hilang begitu user
            // mengetik 1 karakter. Kolomnya sendiri BENAR-BENAR kosong.
            hintText: 'contoh: http://127.0.0.1:8642/v1',
            hintStyle: TextStyle(
              color: t.colorScheme.onSurface.withValues(alpha: 0.18),
            ),
            border: const OutlineInputBorder(),
          ),
        ),
        const SizedBox(height: AppSpacing.md),
        TextField(
          controller: _key,
          obscureText: true,
          decoration: InputDecoration(
            labelText: 'API Key',
            // HINT = hanya VISUAL (abu-abu sangat pudar), hilang saat mengetik.
            hintText: 'contoh: kunci API_SERVER_KEY',
            hintStyle: TextStyle(
              color: t.colorScheme.onSurface.withValues(alpha: 0.18),
            ),
            border: const OutlineInputBorder(),
          ),
        ),

        // ================================================================
        // BAGIAN 2 — MODEL
        // ================================================================
        const SizedBox(height: AppSpacing.xl),
        const Divider(thickness: 1),
        const SizedBox(height: AppSpacing.md),
        Row(children: [
          Icon(Icons.memory, size: 18, color: t.colorScheme.primary),
          const SizedBox(width: 8),
          Expanded(child: Text('Model AI', style: t.textTheme.titleSmall)),
        ]),
        const SizedBox(height: AppSpacing.sm),

        FilledButton.icon(
          onPressed: _sibuk ? null : _deteksi,
          icon: _sibuk
              ? const SizedBox(width: 16, height: 16, child: CircularProgressIndicator(strokeWidth: 2))
              : const Icon(Icons.wifi_find),
          label: Text(_sibuk ? 'Mendeteksi...' : 'Deteksi Model'),
        ),
        const SizedBox(height: AppSpacing.sm),
        // Model MANUAL — untuk server/router yang tidak menyediakan /v1/models.
        TextField(
          controller: _manual,
          decoration: const InputDecoration(
            labelText: 'Model manual (opsional)',
            hintText: 'mis. synapse-agent / gpt-4o-mini',
            border: OutlineInputBorder(),
            helperText:
                'Isi ini kalau daftar model kosong. Dipakai bila tidak ada model terpilih di atas.',
          ),
        ),

        if (_pesan != null) ...[
          const SizedBox(height: AppSpacing.md),
          Container(
            padding: const EdgeInsets.all(AppSpacing.md),
            decoration: BoxDecoration(
              color: (_ok ? Colors.green : Colors.red).withValues(alpha: 0.12),
              borderRadius: BorderRadius.circular(8),
            ),
            child: Row(children: [
              Icon(_ok ? Icons.check_circle : Icons.error, size: 18,
                  color: _ok ? Colors.green : Colors.red),
              const SizedBox(width: 8),
              Expanded(child: Text(_pesan!, style: t.textTheme.bodySmall)),
            ]),
          ),
        ],

        if (_model.isNotEmpty) ...[
          const SizedBox(height: AppSpacing.lg),
          Text('Model', style: t.textTheme.titleSmall),
          const SizedBox(height: 6),
          if (_model.length == 1)
            // hanya 1 model -> konfirmasi ya/tidak
            Card(
              child: ListTile(
                leading: const Icon(Icons.smart_toy),
                title: Text(_model.first),
                subtitle: const Text('Satu model terdeteksi. Pakai model ini?'),
                trailing: Switch(
                  value: _dipilih == _model.first,
                  onChanged: (v) => setState(() => _dipilih = v ? _model.first : null),
                ),
              ),
            )
          else
            DropdownButtonFormField<String>(
              initialValue: _dipilih,
              decoration: const InputDecoration(
                labelText: 'Pilih model',
                border: OutlineInputBorder(),
              ),
              items: _model
                  .map((m) => DropdownMenuItem(value: m, child: Text(m)))
                  .toList(),
              onChanged: (v) => setState(() => _dipilih = v),
            ),
          const SizedBox(height: AppSpacing.lg),
          Text('Pengaturan Lanjutan', style: t.textTheme.titleSmall),
          const SizedBox(height: 6),
          // ===== OPSI VISION =====
          const SizedBox(height: AppSpacing.md),
          Text('Vision (baca gambar)', style: t.textTheme.titleSmall),
          const SizedBox(height: 6),
          DropdownButtonFormField<String>(
            initialValue: _vision,
            decoration: const InputDecoration(
              labelText: 'Model vision',
              border: OutlineInputBorder(),
              helperText: 'Model yang dipakai untuk membaca gambar',
            ),
            items: daftarVision
                .map((v) => DropdownMenuItem(
                      value: v.id,
                      child: Text(v.nama),
                    ))
                .toList(),
            onChanged: (v) => setState(() => _vision = v ?? 'auto'),
          ),
          Padding(
            padding: const EdgeInsets.only(top: 6),
            child: Text(
              daftarVision.firstWhere((v) => v.id == _vision).deskripsi,
              style: t.textTheme.bodySmall,
            ),
          ),
          const SizedBox(height: AppSpacing.md),
          TextField(
            controller: _name,
            decoration: const InputDecoration(
              labelText: 'Display name (opsional)',
              hintText: 'mis. Synapse Produksi',
              border: OutlineInputBorder(),
            ),
          ),
          const SizedBox(height: AppSpacing.md),
          TextField(
            controller: _ctx,
            keyboardType: TextInputType.number,
            decoration: const InputDecoration(
              labelText: 'Context window (token)',
              hintText: '128000',
              border: OutlineInputBorder(),
            ),
          ),
        ],

        const SizedBox(height: AppSpacing.lg),
        FilledButton(
          onPressed: _sibuk ? null : _simpan,
          child: const Text('Simpan'),
        ),
        const SizedBox(height: AppSpacing.sm),
        TextButton.icon(
          onPressed: _sibuk ? null : _hapusKonfigurasi,
          icon: const Icon(Icons.logout),
          label: const Text('Hapus konfigurasi'),
        ),
      ],
      ),
      ),
    );
  }
}
