import 'dart:convert';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:shared_preferences/shared_preferences.dart';
import '../../core/api/api_config.dart';
import '../../core/api/api_providers.dart';
import '../../core/theme/spacing.dart';

/// MCP (Model Context Protocol) — daftar server + TAMBAH MCP SENDIRI.
///
/// PERBAIKAN v1.2.1:
///   Versi lama hanya toggle on/off (tidak tersimpan, tidak bisa tambah).
///   Sekarang: MCP tersimpan permanen + bisa TAMBAH/EDIT/HAPUS MCP sendiri
///   (nama, URL, tipe transport, auth) + tombol pasang ke agent.
class McpScreen extends ConsumerStatefulWidget {
  const McpScreen({super.key});
  @override
  ConsumerState<McpScreen> createState() => _McpScreenState();
}

class _McpScreenState extends ConsumerState<McpScreen> {
  /// Katalog MCP bawaan (dari repo Synapse: optional-mcps/)
  static const _katalog = <Map<String, String>>[
    {'nama': 'airtable', 'desk': 'Database Airtable: baca/tulis record, tabel, view.'},
    {'nama': 'asana', 'desk': 'Manajemen tugas Asana: proyek, task, assignment.'},
    {'nama': 'atlassian', 'desk': 'Jira & Confluence: issue, sprint, dokumen.'},
    {'nama': 'comfy-cloud', 'desk': 'ComfyUI Cloud: workflow gambar generatif.'},
    {'nama': 'datadog', 'desk': 'Monitoring & log Datadog: metrik, alert, trace.'},
    {'nama': 'figma', 'desk': 'Figma: baca file, komponen, komentar desain.'},
    {'nama': 'hugging_face', 'desk': 'Hugging Face: model, dataset, Space.'},
    {'nama': 'intercom', 'desk': 'Intercom: percakapan pelanggan, tiket.'},
    {'nama': 'linear', 'desk': 'Linear: issue, siklus, proyek tim.'},
    {'nama': 'n8n', 'desk': 'n8n: jalankan workflow otomasi.'},
    {'nama': 'netlify', 'desk': 'Netlify: deploy situs, kelola build.'},
    {'nama': 'notion', 'desk': 'Notion: halaman, database, pencarian.'},
    {'nama': 'paypal', 'desk': 'PayPal: transaksi, invoice.'},
    {'nama': 'sentry', 'desk': 'Sentry: error tracking, issue, release.'},
    {'nama': 'square', 'desk': 'Square: pembayaran, katalog, pelanggan.'},
  ];

  static const _kunci = 'mcp_aktif';
  static const _kunciCustom = 'mcp_custom';

  final Set<String> _aktif = {};
  /// MCP buatan user: [{nama, url, tipe, auth, desk}]
  List<Map<String, dynamic>> _custom = [];
  bool _muat = true;

  @override
  void initState() {
    super.initState();
    _muatDariDisk();
  }

  Future<void> _muatDariDisk() async {
    try {
      final p = await SharedPreferences.getInstance();
      final a = p.getStringList(_kunci) ?? [];
      final c = p.getString(_kunciCustom);
      if (!mounted) return;
      setState(() {
        _aktif
          ..clear()
          ..addAll(a);
        if (c != null && c.isNotEmpty) {
          _custom = (jsonDecode(c) as List)
              .map((e) => Map<String, dynamic>.from(e as Map))
              .toList();
        }
        _muat = false;
      });
    } catch (_) {
      if (mounted) setState(() => _muat = false);
    }
  }

  Future<void> _simpan() async {
    final p = await SharedPreferences.getInstance();
    await p.setStringList(_kunci, _aktif.toList());
    await p.setString(_kunciCustom, jsonEncode(_custom));
  }

  /// Toggle MCP bawaan.
  void _toggle(String nama, bool v) {
    setState(() {
      if (v) {
        _aktif.add(nama);
      } else {
        _aktif.remove(nama);
      }
    });
    _simpan();
  }

  /// Dialog TAMBAH / EDIT MCP sendiri.
  Future<void> _dialogMcp({Map<String, dynamic>? awal, int? indeks}) async {
    final nama = TextEditingController(text: (awal?['nama'] ?? '') as String);
    final url = TextEditingController(text: (awal?['url'] ?? '') as String);
    final desk = TextEditingController(text: (awal?['desk'] ?? '') as String);
    var tipe = (awal?['tipe'] ?? 'http') as String;
    var auth = (awal?['auth'] ?? 'none') as String;

    await showDialog<void>(
      context: context,
      builder: (c) => StatefulBuilder(builder: (c, setD) {
        return AlertDialog(
          title: Text(indeks == null ? 'Tambah MCP Sendiri' : 'Edit MCP'),
          content: SingleChildScrollView(
            child: Column(mainAxisSize: MainAxisSize.min, children: [
              TextField(
                controller: nama,
                decoration: const InputDecoration(
                  labelText: 'Nama MCP',
                  hintText: 'mis. server-ku',
                ),
              ),
              const SizedBox(height: 10),
              TextField(
                controller: url,
                decoration: const InputDecoration(
                  labelText: 'URL Server',
                  hintText: 'https://contoh.com/mcp',
                ),
              ),
              const SizedBox(height: 10),
              TextField(
                controller: desk,
                decoration: const InputDecoration(
                  labelText: 'Keterangan (opsional)',
                ),
              ),
              const SizedBox(height: 12),
              Row(children: [
                const Text('Tipe: '),
                const SizedBox(width: 8),
                DropdownButton<String>(
                  value: tipe,
                  items: const [
                    DropdownMenuItem(value: 'http', child: Text('http')),
                    DropdownMenuItem(value: 'sse', child: Text('sse')),
                    DropdownMenuItem(value: 'stdio', child: Text('stdio')),
                  ],
                  onChanged: (v) => setD(() => tipe = v ?? 'http'),
                ),
                const Spacer(),
                const Text('Auth: '),
                const SizedBox(width: 8),
                DropdownButton<String>(
                  value: auth,
                  items: const [
                    DropdownMenuItem(value: 'none', child: Text('tidak ada')),
                    DropdownMenuItem(value: 'oauth', child: Text('oauth')),
                    DropdownMenuItem(value: 'token', child: Text('token')),
                  ],
                  onChanged: (v) => setD(() => auth = v ?? 'none'),
                ),
              ]),
            ]),
          ),
          actions: [
            TextButton(
              onPressed: () => Navigator.pop(c),
              child: const Text('Batal'),
            ),
            FilledButton(
              onPressed: () {
                if (nama.text.trim().isEmpty) return;
                setState(() {
                  final data = {
                    'nama': nama.text.trim(),
                    'url': url.text.trim(),
                    'desk': desk.text.trim().isEmpty
                        ? 'MCP buatan sendiri'
                        : desk.text.trim(),
                    'tipe': tipe,
                    'auth': auth,
                  };
                  if (indeks == null) {
                    _custom.add(data);
                    _aktif.add(data['nama'] as String);
                  } else {
                    final lama = _custom[indeks]['nama'];
                    _custom[indeks] = data;
                    if (_aktif.remove(lama)) {
                      _aktif.add(data['nama'] as String);
                    }
                  }
                });
                _simpan();
                Navigator.pop(c);
              },
              child: const Text('Simpan'),
            ),
          ],
        );
      }),
    );
  }

  /// Hapus MCP sendiri.
  Future<void> _hapus(int indeks) async {
    final nama = _custom[indeks]['nama'];
    final ya = await showDialog<bool>(
      context: context,
      builder: (c) => AlertDialog(
        title: const Text('Hapus MCP?'),
        content: Text('MCP "$nama" akan dihapus dari daftar.'),
        actions: [
          TextButton(
              onPressed: () => Navigator.pop(c, false),
              child: const Text('Tidak')),
          FilledButton(
              onPressed: () => Navigator.pop(c, true),
              child: const Text('Ya')),
        ],
      ),
    );
    if (ya != true) return;
    setState(() {
      _aktif.remove(nama);
      _custom.removeAt(indeks);
    });
    _simpan();
  }

  /// Pasang MCP ke agent (buat manifest.yaml + aktifkan).
  Future<void> _pasang(String nama, {String? url, String? tipe, String? auth, String? desk}) async {
    final klien = ref.read(apiClientProvider);
    if (klien == null) {
      _pesan('Belum tersambung. Isi Base URL + API Key di Setelan.');
      return;
    }
    _pesan('Memasang MCP "$nama" di laptop...');
    try {
      final perintah = url == null
          ? 'Aktifkan MCP "$nama" di Synapse (dari katalog optional-mcps), '
            'lalu laporkan hasilnya.'
          : 'Buat MCP baru di Synapse dengan data ini:\n'
            'NAMA: $nama\nURL: $url\nTIPE: ${tipe ?? "http"}\n'
            'AUTH: ${auth ?? "none"}\nKETERANGAN: ${desk ?? "-"}\n\n'
            'Buat file manifest.yaml di folder MCP Synapse dengan format yang '
            'sama seperti optional-mcps/ lainnya (manifest_version, name, '
            'description, transport{type,url}, auth), lalu aktifkan. '
            'Laporkan singkat: berhasil/gagal + path file.';
      final hasil = await klien.perintahAgent(perintah, panjang: true);
      _pesan(hasil.trim().isEmpty ? 'Selesai.' : hasil.trim());
    } catch (e) {
      _pesan('Gagal: $e');
    }
  }

  void _pesan(String s) {
    if (!mounted) return;
    showDialog<void>(
      context: context,
      builder: (c) => AlertDialog(
        title: const Text('Hasil'),
        content: SingleChildScrollView(child: Text(s)),
        actions: [
          TextButton(
              onPressed: () => Navigator.pop(c), child: const Text('Tutup')),
        ],
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    final t = Theme.of(context);
    if (_muat) {
      return const Scaffold(body: Center(child: CircularProgressIndicator()));
    }
    return Scaffold(
      appBar: AppBar(
        title: const Text('MCP Server'),
        actions: [
          Padding(
            padding: const EdgeInsets.only(right: 6),
            child: Center(
              child: Chip(
                label: Text('${_aktif.length} aktif'),
                backgroundColor: t.colorScheme.surfaceContainerHighest,
              ),
            ),
          ),
        ],
      ),
      floatingActionButton: FloatingActionButton.extended(
        onPressed: () => _dialogMcp(),
        icon: const Icon(Icons.add),
        label: const Text('Tambah MCP'),
      ),
      body: ListView(
        padding: const EdgeInsets.fromLTRB(
            AppSpacing.md, AppSpacing.md, AppSpacing.md, 90),
        children: [
          Text(
            'Model Context Protocol — menghubungkan Synapse ke layanan luar. '
            'MCP tersimpan permanen; tombol pasang mengirim perintah ke agent.',
            style: t.textTheme.bodySmall,
          ),
          const SizedBox(height: AppSpacing.md),

          // ---- MCP BUATAN SENDIRI ----
          Row(children: [
            Icon(Icons.person_outline, size: 18, color: t.colorScheme.primary),
            const SizedBox(width: 6),
            Text('MCP Saya (${_custom.length})', style: t.textTheme.titleSmall),
          ]),
          const SizedBox(height: 6),
          if (_custom.isEmpty)
            Card(
              child: Padding(
                padding: const EdgeInsets.all(AppSpacing.md),
                child: Text(
                  'Belum ada MCP sendiri. Ketuk "Tambah MCP" untuk membuat '
                  '(nama + URL + tipe + auth).',
                  style: t.textTheme.bodySmall,
                ),
              ),
            )
          else
            ...List.generate(_custom.length, (i) {
              final m = _custom[i];
              final nama = m['nama'] as String;
              final on = _aktif.contains(nama);
              return Card(
                margin: const EdgeInsets.only(bottom: AppSpacing.sm),
                child: Column(children: [
                  SwitchListTile(
                    value: on,
                    onChanged: (v) => _toggle(nama, v),
                    secondary: Icon(on ? Icons.hub : Icons.hub_outlined,
                        color: on ? t.colorScheme.primary : null),
                    title: Text(nama, style: t.textTheme.titleSmall),
                    subtitle: Text(
                      '${m['tipe']} • ${m['auth']}\n${m['desk']}',
                      style: t.textTheme.bodySmall,
                    ),
                    isThreeLine: true,
                  ),
                  OverflowBar(children: [
                    TextButton.icon(
                      onPressed: () => _pasang(nama,
                          url: m['url'] as String,
                          tipe: m['tipe'] as String,
                          auth: m['auth'] as String,
                          desk: m['desk'] as String),
                      icon: const Icon(Icons.cloud_upload_outlined, size: 18),
                      label: const Text('Pasang'),
                    ),
                    TextButton.icon(
                      onPressed: () => _dialogMcp(awal: m, indeks: i),
                      icon: const Icon(Icons.edit_outlined, size: 18),
                      label: const Text('Edit'),
                    ),
                    TextButton.icon(
                      onPressed: () => _hapus(i),
                      icon: const Icon(Icons.delete_outline, size: 18),
                      label: const Text('Hapus'),
                    ),
                  ]),
                ]),
              );
            }),

          const SizedBox(height: AppSpacing.lg),

          // ---- MCP BAWAAN ----
          Row(children: [
            Icon(Icons.inventory_2_outlined, size: 18, color: t.colorScheme.primary),
            const SizedBox(width: 6),
            Text('MCP Bawaan (${_katalog.length})',
                style: t.textTheme.titleSmall),
          ]),
          const SizedBox(height: 6),
          ..._katalog.map((m) {
            final nama = m['nama']!;
            final on = _aktif.contains(nama);
            return Card(
              margin: const EdgeInsets.only(bottom: AppSpacing.sm),
              child: SwitchListTile(
                value: on,
                onChanged: (v) => _toggle(nama, v),
                secondary: Icon(on ? Icons.hub : Icons.hub_outlined,
                    color: on ? t.colorScheme.primary : null),
                title: Text(nama, style: t.textTheme.titleSmall),
                subtitle: Text(m['desk']!, style: t.textTheme.bodySmall),
              ),
            );
          }),
        ],
      ),
    );
  }
}
