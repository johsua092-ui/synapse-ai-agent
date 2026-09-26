import 'dart:convert';
import 'dart:io';
import 'package:flutter/material.dart';
import 'package:flutter/services.dart' show rootBundle;
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:http/http.dart' as http;
import 'package:open_file/open_file.dart';
import 'package:package_info_plus/package_info_plus.dart';
import 'package:path_provider/path_provider.dart';
import '../../core/theme/spacing.dart';

/// Update + PATCHNOTE (log perubahan).
///
/// PERBAIKAN v1.2.1:
///   - Versi terpasang dibaca dari APK (bukan hardcode "0.1.0").
///   - Ada PATCHNOTE: daftar apa yang diperbaiki tiap versi.
class UpdateScreen extends ConsumerStatefulWidget {
  const UpdateScreen({super.key});
  @override
  ConsumerState<UpdateScreen> createState() => _UpdateScreenState();
}

class _UpdateScreenState extends ConsumerState<UpdateScreen> {
  bool _cek = false;
  bool? _ada;
  String _versiSekarang = '...';
  String? _versiBaru;
  bool _mengunduh = false;
  double _progres = 0;
  String? _infoUnduh;
  String? _urlApk;
  String? _catatanRilis;
  List<Map<String, dynamic>> _riwayat = [];

  /// Repo GitHub sumber update (folder "synapse Mobile" ada di dalamnya).
  static const _repo = 'johsua092-ui/synapse-ai-agent';

  @override
  void initState() {
    super.initState();
    _muat();
  }

  Future<void> _muat() async {
    // versi asli dari APK
    try {
      final p = await PackageInfo.fromPlatform();
      if (mounted) setState(() => _versiSekarang = p.version);
    } catch (_) {}

    // patchnote (dibawa di dalam APK)
    try {
      final raw = await rootBundle.loadString('assets/patchnote.json');
      final d = jsonDecode(raw) as Map<String, dynamic>;
      final r = ((d['riwayat'] as List?) ?? const [])
          .map((e) => Map<String, dynamic>.from(e as Map))
          .toList();
      if (mounted) {
        setState(() {
          _riwayat = r;
        });
      }
    } catch (_) {}
  }

  /// Bandingkan dua versi semantik (mis. "1.2.2" vs "1.2.10").
  static int _banding(String a, String b) {
    final x = a.split('.').map((e) => int.tryParse(e) ?? 0).toList();
    final y = b.split('.').map((e) => int.tryParse(e) ?? 0).toList();
    for (var i = 0; i < 3; i++) {
      final p = i < x.length ? x[i] : 0;
      final q = i < y.length ? y[i] : 0;
      if (p != q) return p.compareTo(q);
    }
    return 0;
  }

  /// Cek update NYATA dari GitHub Releases (bukan dari patchnote di APK).
  Future<void> _cekUpdate() async {
    setState(() {
      _cek = true;
      _ada = null;
      _infoUnduh = null;
      _urlApk = null;
      _catatanRilis = null;
    });
    try {
      final r = await http.get(
        Uri.parse('https://api.github.com/repos/$_repo/releases/latest'),
        headers: {'Accept': 'application/vnd.github+json'},
      ).timeout(const Duration(seconds: 25));
      if (r.statusCode != 200) {
        throw Exception('GitHub HTTP ${r.statusCode}');
      }
      final d = jsonDecode(r.body) as Map<String, dynamic>;
      var tag = (d['tag_name'] ?? '').toString().trim();
      if (tag.startsWith('v') || tag.startsWith('V')) {
        tag = tag.substring(1);
      }
      // cari aset APK di rilis
      String? urlApk;
      for (final a in ((d['assets'] as List?) ?? const [])) {
        final nama = (a['name'] ?? '').toString().toLowerCase();
        if (nama.endsWith('.apk')) {
          urlApk = (a['browser_download_url'] ?? '').toString();
          break;
        }
      }
      if (!mounted) return;
      final beda = tag.isNotEmpty && _banding(tag, _versiSekarang) > 0;
      setState(() {
        _cek = false;
        _ada = beda;
        _versiBaru = beda ? tag : null;
        _urlApk = urlApk;
        _catatanRilis = (d['body'] ?? '').toString();
      });
    } catch (e) {
      if (!mounted) return;
      setState(() {
        _cek = false;
        _ada = null;
        _infoUnduh = 'Gagal memeriksa update: $e';
      });
    }
  }

  /// Unduh APK dari GitHub, lalu buka installer Android.
  Future<void> _unduh() async {
    final url = _urlApk;
    if (url == null || url.isEmpty) {
      setState(() => _infoUnduh =
          'Rilis terbaru belum menyertakan file APK. Hubungi pengembang.');
      return;
    }
    setState(() {
      _mengunduh = true;
      _progres = 0;
      _infoUnduh = 'Mengunduh...';
    });
    try {
      final req = http.Request('GET', Uri.parse(url));
      final resp = await req.send();
      if (resp.statusCode != 200) {
        throw Exception('HTTP ${resp.statusCode}');
      }
      final total = resp.contentLength ?? 0;
      final dir = await getApplicationDocumentsDirectory();
      final file = File('${dir.path}/synapse-update.apk');
      final sink = file.openWrite();
      var terima = 0;
      await for (final chunk in resp.stream) {
        sink.add(chunk);
        terima += chunk.length;
        if (total > 0 && mounted) {
          setState(() => _progres = terima / total);
        }
      }
      await sink.flush();
      await sink.close();
      if (!mounted) return;
      setState(() {
        _mengunduh = false;
        _infoUnduh = 'Terunduh ${(terima / 1048576).toStringAsFixed(1)} MB. '
            'Lanjut ke pemasangan...';
      });
      final hasil = await OpenFile.open(file.path, type: 'application/vnd.android.package-archive');
      if (!mounted) return;
      if (hasil.type != ResultType.done) {
        setState(() => _infoUnduh =
            'APK tersimpan, tapi pemasangan dibatalkan/gagal (${hasil.type.name}). '
            'File: ${file.path}');
      }
    } catch (e) {
      if (!mounted) return;
      setState(() {
        _mengunduh = false;
        _infoUnduh = 'Gagal mengunduh: $e';
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    final t = Theme.of(context);
    return Scaffold(
      appBar: AppBar(title: const Text('Update & Patchnote')),
      body: ListView(
        padding: const EdgeInsets.all(AppSpacing.md),
        children: [
          Card(
            child: ListTile(
              leading: const Icon(Icons.system_update_alt),
              title: const Text('Versi terpasang'),
              trailing:
                  Text(_versiSekarang, style: t.textTheme.titleSmall),
            ),
          ),
          const SizedBox(height: AppSpacing.md),
          FilledButton.icon(
            onPressed: _cek ? null : _cekUpdate,
            icon: _cek
                ? const SizedBox(
                    width: 16,
                    height: 16,
                    child: CircularProgressIndicator(strokeWidth: 2))
                : const Icon(Icons.refresh),
            label: Text(_cek ? 'Memeriksa...' : 'Cek Update'),
          ),

          if (_ada == false) ...[
            const SizedBox(height: AppSpacing.md),
            Card(
              color: Colors.green.withValues(alpha: 0.12),
              child: const ListTile(
                leading: Icon(Icons.check_circle, color: Colors.green),
                title: Text('Sudah versi terbaru'),
                subtitle: Text('Tidak ada update tersedia.'),
              ),
            ),
          ],

          if (_ada == true) ...[
            const SizedBox(height: AppSpacing.md),
            Card(
              color: Colors.orange.withValues(alpha: 0.12),
              child: ListTile(
                leading: const Icon(Icons.new_releases, color: Colors.orange),
                title: Text('Update tersedia: $_versiBaru'),
                subtitle: Text('Update dari $_versiSekarang ke $_versiBaru'),
              ),
            ),
            if ((_catatanRilis ?? '').trim().isNotEmpty) ...[
              const SizedBox(height: AppSpacing.sm),
              Card(
                child: Padding(
                  padding: const EdgeInsets.all(AppSpacing.md),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text('Catatan rilis:', style: t.textTheme.labelMedium),
                      const SizedBox(height: 4),
                      Text(_catatanRilis!.trim(),
                          style: t.textTheme.bodySmall),
                    ],
                  ),
                ),
              ),
            ],
            const SizedBox(height: AppSpacing.sm),
            if (_mengunduh) ...[
              LinearProgressIndicator(value: _progres),
              const SizedBox(height: 6),
              Text('Mengunduh ${(_progres * 100).toStringAsFixed(0)}%',
                  style: t.textTheme.bodySmall),
            ] else
              FilledButton.icon(
                onPressed: (_urlApk == null || _urlApk!.isEmpty) ? null : _unduh,
                icon: const Icon(Icons.download),
                label: Text((_urlApk == null || _urlApk!.isEmpty)
                    ? 'Rilis belum menyertakan APK'
                    : 'Unduh & Pasang Update'),
              ),
          ],

          if ((_infoUnduh ?? '').isNotEmpty) ...[
            const SizedBox(height: AppSpacing.sm),
            Card(
              color: Colors.blueGrey.withValues(alpha: 0.10),
              child: ListTile(
                leading: const Icon(Icons.info_outline),
                title: const Text('Info Update'),
                subtitle: Text(_infoUnduh!),
              ),
            ),
          ],

          const SizedBox(height: AppSpacing.lg),
          Row(children: [
            Icon(Icons.history, size: 18, color: t.colorScheme.primary),
            const SizedBox(width: 6),
            Text('Patchnote / Log Update', style: t.textTheme.titleSmall),
          ]),
          const SizedBox(height: 6),
          Text(
            'Daftar perubahan tiap versi Synapse Mobile.',
            style: t.textTheme.bodySmall,
          ),
          const SizedBox(height: AppSpacing.sm),

          if (_riwayat.isEmpty)
            const Center(child: Padding(
              padding: EdgeInsets.all(AppSpacing.lg),
              child: CircularProgressIndicator(),
            ))
          else
            ..._riwayat.map((r) {
              final versi = (r['versi'] ?? '').toString();
              final tgl = (r['tanggal'] ?? '').toString();
              final judul = (r['judul'] ?? '').toString();
              final fix = ((r['perbaikan'] as List?) ?? const [])
                  .map((e) => e.toString())
                  .toList();
              final baru = ((r['fitur_baru'] as List?) ?? const [])
                  .map((e) => e.toString())
                  .toList();
              final terbaru = versi == _versiSekarang;
              return Card(
                margin: const EdgeInsets.only(bottom: AppSpacing.sm),
                child: ExpansionTile(
                  initiallyExpanded: terbaru,
                  leading: Icon(
                    terbaru ? Icons.verified : Icons.article_outlined,
                    color: terbaru ? Colors.green : t.colorScheme.primary,
                  ),
                  title: Text('v$versi — $judul',
                      style: t.textTheme.titleSmall),
                  subtitle: Text(
                    terbaru ? '$tgl • terpasang' : tgl,
                    style: t.textTheme.bodySmall,
                  ),
                  children: [
                    Padding(
                      padding: const EdgeInsets.fromLTRB(
                          AppSpacing.md, 0, AppSpacing.md, AppSpacing.md),
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          if (fix.isNotEmpty) ...[
                            Text('Perbaikan:',
                                style: t.textTheme.labelMedium),
                            for (final f in fix)
                              Padding(
                                padding: const EdgeInsets.only(top: 4),
                                child: Row(
                                  crossAxisAlignment:
                                      CrossAxisAlignment.start,
                                  children: [
                                    const Text('• '),
                                    Expanded(
                                        child: Text(f,
                                            style: t.textTheme.bodySmall)),
                                  ],
                                ),
                              ),
                          ],
                          if (baru.isNotEmpty) ...[
                            const SizedBox(height: 8),
                            Text('Fitur baru:',
                                style: t.textTheme.labelMedium),
                            for (final f in baru)
                              Padding(
                                padding: const EdgeInsets.only(top: 4),
                                child: Row(
                                  crossAxisAlignment:
                                      CrossAxisAlignment.start,
                                  children: [
                                    const Text('• '),
                                    Expanded(
                                        child: Text(f,
                                            style: t.textTheme.bodySmall)),
                                  ],
                                ),
                              ),
                          ],
                          if (fix.isEmpty && baru.isEmpty)
                            Text('(tidak ada catatan)',
                                style: t.textTheme.bodySmall),
                        ],
                      ),
                    ),
                  ],
                ),
              );
            }),
        ],
      ),
    );
  }
}
