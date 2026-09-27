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
    _url = TextEditingController(text: c.baseUrl.isEmpty ? 'http://127.0.0.1:8642' : c.baseUrl);
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

  Future<void> _simpan() async {
    // VALIDASI: cegah simpan kalau Base URL / API Key kosong
    if (_url.text.trim().isEmpty) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Base URL belum diisi')),
      );
      return;
    }
    if (_key.text.trim().isEmpty) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('API Key belum diisi')),
      );
      return;
    }

    final c = ApiConfig(
      baseUrl: _url.text.trim(),
      apiKey: _key.text.trim(),
      model: _dipilih ?? (_manual.text.trim().isEmpty ? null : _manual.text.trim()),
      displayName: _name.text.trim().isEmpty ? null : _name.text.trim(),
      contextWindow: int.tryParse(_ctx.text.trim()),
      visionProvider: _vision,
      visionModel: _vision == 'auto' ? null : _vision,
    );
    await ref.read(apiConfigProvider.notifier).simpan(c);
    if (mounted) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Konfigurasi disimpan')),
      );
    }
  }

  @override
  Widget build(BuildContext context) {
    final t = Theme.of(context);
    return Scaffold(
      appBar: AppBar(
        title: const Text('Koneksi AI'),
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
          decoration: const InputDecoration(
            labelText: 'Base URL',
            hintText: 'http://127.0.0.1:8642',
            border: OutlineInputBorder(),
          ),
        ),
        const SizedBox(height: AppSpacing.md),
        TextField(
          controller: _key,
          obscureText: true,
          decoration: const InputDecoration(
            labelText: 'API Key',
            hintText: 'API_SERVER_KEY',
            border: OutlineInputBorder(),
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
          onPressed: _simpan,
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
    );
  }
}
