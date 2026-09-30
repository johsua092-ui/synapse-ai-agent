import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../core/api/api_client.dart';
import '../../core/api/api_config.dart';
import '../../core/theme/spacing.dart';

/// Layar TOOLS — daftar toolset yang tersedia di Synapse (dari /v1/toolsets).
///
/// Permintaan tim (v1.2.4): "sediain tools nya dong minimal kaya yang di cli".
/// Toolset dijalankan di SERVER (agent di laptop) — HP hanya menampilkan
/// daftar + status, dan bisa mengirim perintah bebas ke agent.
class ToolsScreen extends ConsumerStatefulWidget {
  const ToolsScreen({super.key});
  @override
  ConsumerState<ToolsScreen> createState() => _ToolsScreenState();
}

class _ToolsScreenState extends ConsumerState<ToolsScreen> {
  bool _sibuk = false;
  String? _pesan;
  bool _ok = false;
  List<Map<String, dynamic>> _toolsets = [];
  final _perintah = TextEditingController();
  String? _hasil;
  /// Nama toolset yang sedang diubah (supaya tombolnya jadi loading).
  String? _sedangUbah;

  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addPostFrameCallback((_) => _muat());
  }

  @override
  void dispose() {
    _perintah.dispose();
    super.dispose();
  }

  /// FIX v1.2.7 — pesan error yang JELAS (dulu cuma "Gagal: Exception: HTTP 404").
  /// Membedakan: server tidak terjangkau / endpoint tidak ada / API key ditolak.
  String _pesanRamah(Object e) {
    final s = e.toString();
    if (s.contains('SocketException') ||
        s.contains('Connection refused') ||
        s.contains('Failed host lookup') ||
        s.contains('Connection closed')) {
      return 'Server Synapse TIDAK TERJANGKAU.\n'
          'Cek: kabel/WiFi tersambung, lalu jalankan di PC:\n'
          '  adb reverse tcp:8642 tcp:8642\n'
          'dan pastikan Synapse (gateway) sedang berjalan.';
    }
    if (s.contains('404')) {
      return 'Server ini TIDAK punya fitur agent (HTTP 404).\n\n'
          'Penyebab paling umum: Base URL menunjuk ke ROUTER model\n'
          '(mis. 9router) — bukan ke Synapse agent.\n'
          'Router hanya melayani CHAT. Fitur Tools/Skills/Backup/MCP/\n'
          'Perangkat HANYA ada di Synapse agent (di PC).\n\n'
          'SOLUSI: Setelan -> Koneksi AI -> Base URL:\n'
          '  http://127.0.0.1:8642/v1\n'
          'lalu di PC jalankan: adb reverse tcp:8642 tcp:8642';
    }
    if (s.contains('401') || s.contains('403')) {
      return 'API Key DITOLAK (HTTP 401/403).\n'
          'Periksa kembali API Key di Setelan -> Koneksi AI.';
    }
    if (s.contains('TimeoutException') || s.contains('timed out')) {
      return 'Server TIDAK MERESPONS (timeout).\n'
          'Coba lagi — operasi berat (backup) bisa butuh beberapa menit.';
    }
    return 'Gagal: $s';
  }

  Future<void> _muat() async {
    setState(() {
      _sibuk = true;
      _pesan = null;
    });
    try {
      final cfg = ref.read(apiConfigProvider);
      if (!cfg.terisi) {
        throw Exception(
            'Belum diatur. Isi Base URL & API Key di Setelan -> Koneksi AI.');
      }
      final d = await ApiClient(cfg).toolsets();
      setState(() {
        _toolsets = d;
        _ok = true;
        _pesan = '${d.length} toolset ditemukan';
      });
    } catch (e) {
      setState(() {
        _ok = false;
        _pesan = _pesanRamah(e);
      });
    } finally {
      setState(() => _sibuk = false);
    }
  }

  /// Nyalakan / matikan satu toolset lewat AGENT (perintah native Synapse).
  /// Pola sama seperti MCP & Skill: agent yang mengeksekusi di host.
  Future<void> _ubah(Map<String, dynamic> e) async {
    final nama = (e['name'] ?? '').toString();
    if (nama.isEmpty) return;
    final aktif = e['enabled'] == true;
    final aksi = aktif ? 'disable' : 'enable';
    final kata = aktif ? 'MATIKAN' : 'NYALAKAN';

    final ya = await showDialog<bool>(
      context: context,
      builder: (c) => AlertDialog(
        title: Text('$kata toolset "$nama"?'),
        content: Text(
          aktif
              ? 'Toolset ini akan dimatikan untuk platform api_server (dipakai app mobile).'
              : 'Toolset ini akan dinyalakan untuk platform api_server (dipakai app mobile).',
        ),
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
      _sedangUbah = nama;
      _hasil = 'Menjalankan: synapse tools $aksi $nama --platform api_server ...';
    });
    try {
      final cfg = ref.read(apiConfigProvider);
      final h = await ApiClient(cfg).perintahAgent(
        'synapse tools $aksi $nama --platform api_server',
        panjang: true,
      );
      setState(() => _hasil = h.isEmpty ? '(tanpa keluaran)' : h);
      await _muat(); // ambil status terbaru dari server
    } catch (err) {
      setState(() => _hasil = 'Gagal: $err');
    } finally {
      if (mounted) setState(() => _sedangUbah = null);
    }
  }

  Future<void> _kirim() async {
    final p = _perintah.text.trim();
    if (p.isEmpty) return;
    setState(() {
      _hasil = 'Menjalankan...';
      _sibuk = true;
    });
    try {
      final cfg = ref.read(apiConfigProvider);
      final h = await ApiClient(cfg).perintahAgent(p, panjang: true);
      setState(() => _hasil = h.isEmpty ? '(tanpa keluaran)' : h);
    } catch (e) {
      setState(() => _hasil = 'Gagal: $e');
    } finally {
      setState(() => _sibuk = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final t = Theme.of(context);
    final aktif = _toolsets.where((e) => e['enabled'] == true).length;

    return Scaffold(
      appBar: AppBar(
        centerTitle: true,
        title: const Text('Tools'),
        actions: [
          IconButton(
            tooltip: 'Muat ulang',
            onPressed: _sibuk ? null : _muat,
            icon: const Icon(Icons.refresh),
          ),
        ],
      ),
      body: RefreshIndicator(
        onRefresh: _muat,
        child: ListView(
          padding: const EdgeInsets.all(AppSpacing.md),
          children: [
            Row(children: [
              Icon(Icons.handyman, size: 18, color: t.colorScheme.primary),
              const SizedBox(width: 8),
              Expanded(
                child: Text('Tools (kemampuan agent)',
                    style: t.textTheme.titleSmall),
              ),
            ]),
            const SizedBox(height: 4),
            Text(
              'Semua tool ini dijalankan di SERVER (agent di PC), bukan di HP. '
              'HP hanya menampilkan & mengirim perintah.',
              style: t.textTheme.bodySmall,
            ),
            const SizedBox(height: AppSpacing.md),

            if (_pesan != null)
              Container(
                padding: const EdgeInsets.all(AppSpacing.md),
                decoration: BoxDecoration(
                  color: (_ok ? Colors.green : Colors.red).withValues(alpha: 0.12),
                  borderRadius: BorderRadius.circular(8),
                ),
                child: Row(children: [
                  Icon(_ok ? Icons.check_circle : Icons.error,
                      size: 18, color: _ok ? Colors.green : Colors.red),
                  const SizedBox(width: 8),
                  Expanded(child: Text(_pesan!, style: t.textTheme.bodySmall)),
                ]),
              ),

            if (_toolsets.isNotEmpty) ...[
              const SizedBox(height: AppSpacing.sm),
              Text('$aktif aktif dari ${_toolsets.length} toolset',
                  style: t.textTheme.bodySmall),
              const SizedBox(height: AppSpacing.sm),
              ..._toolsets.map(_kartuToolset),
            ],

            const SizedBox(height: AppSpacing.xl),
            const Divider(thickness: 1),
            const SizedBox(height: AppSpacing.md),
            Row(children: [
              Icon(Icons.terminal, size: 18, color: t.colorScheme.primary),
              const SizedBox(width: 8),
              Expanded(
                child: Text('Perintah bebas ke agent',
                    style: t.textTheme.titleSmall),
              ),
            ]),
            const SizedBox(height: 6),
            TextField(
              controller: _perintah,
              maxLines: 2,
              minLines: 1,
              decoration: const InputDecoration(
                labelText: 'Perintah',
                hintText: 'mis. synapse tools list',
                border: OutlineInputBorder(),
              ),
            ),
            const SizedBox(height: AppSpacing.sm),
            FilledButton.icon(
              onPressed: _sibuk ? null : _kirim,
              icon: const Icon(Icons.play_arrow),
              label: const Text('Jalankan'),
            ),
            if (_hasil != null) ...[
              const SizedBox(height: AppSpacing.md),
              Container(
                width: double.infinity,
                padding: const EdgeInsets.all(AppSpacing.md),
                decoration: BoxDecoration(
                  color: t.colorScheme.surfaceContainerHighest,
                  borderRadius: BorderRadius.circular(8),
                ),
                child: SelectableText(_hasil!,
                    style: const TextStyle(fontFamily: 'monospace', fontSize: 13)),
              ),
            ],
            const SizedBox(height: AppSpacing.xl),
          ],
        ),
      ),
    );
  }

  Widget _kartuToolset(Map<String, dynamic> e) {
    final t = Theme.of(context);
    final aktif = e['enabled'] == true;
    final punyaKey = e['configured'] == true;
    final nama = (e['name'] ?? '').toString();
    final tools = ((e['tools'] as List?) ?? const []).map((x) => x.toString()).toList();
    final label = (e['label'] ?? e['name'] ?? '').toString();
    final desc = (e['description'] ?? '').toString();
    final sedang = _sedangUbah == nama;

    return Card(
      margin: const EdgeInsets.only(bottom: AppSpacing.sm),
      child: Padding(
        padding: const EdgeInsets.all(AppSpacing.md),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(children: [
              Expanded(
                child: Text(label,
                    style: t.textTheme.titleSmall
                        ?.copyWith(fontWeight: FontWeight.bold)),
              ),
              if (sedang)
                const Padding(
                  padding: EdgeInsets.symmetric(horizontal: 12),
                  child: SizedBox(
                      width: 18,
                      height: 18,
                      child: CircularProgressIndicator(strokeWidth: 2)),
                )
              else
                Switch(
                  value: aktif,
                  onChanged: (_) => _ubah(e),
                ),
            ]),
            Row(children: [
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 2),
                decoration: BoxDecoration(
                  color: (aktif ? Colors.green : Colors.grey).withValues(alpha: 0.15),
                  borderRadius: BorderRadius.circular(10),
                ),
                child: Text(aktif ? 'aktif' : 'nonaktif',
                    style: t.textTheme.labelSmall?.copyWith(
                        color: aktif ? Colors.green : Colors.grey)),
              ),
              const SizedBox(width: 6),
              if (!punyaKey)
                Container(
                  padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 2),
                  decoration: BoxDecoration(
                    color: Colors.orange.withValues(alpha: 0.15),
                    borderRadius: BorderRadius.circular(10),
                  ),
                  child: Text('belum ada key',
                      style: t.textTheme.labelSmall
                          ?.copyWith(color: Colors.orange)),
                ),
            ]),
            if (desc.isNotEmpty) ...[
              const SizedBox(height: 4),
              Text(desc, style: t.textTheme.bodySmall),
            ],
            if (tools.isNotEmpty) ...[
              const SizedBox(height: 8),
              Wrap(
                spacing: 6,
                runSpacing: 6,
                children: tools
                    .map((x) => Chip(
                          label: Text(x, style: const TextStyle(fontSize: 11)),
                          visualDensity: VisualDensity.compact,
                          materialTapTargetSize:
                              MaterialTapTargetSize.shrinkWrap,
                        ))
                    .toList(),
              ),
            ],
          ],
        ),
      ),
    );
  }
}
