import 'dart:convert';
import 'package:flutter/material.dart';
import 'package:flutter/services.dart' show rootBundle;
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:package_info_plus/package_info_plus.dart';
import 'package:shared_preferences/shared_preferences.dart';
import '../core/notif/notif_provider.dart';

/// Satu item navigasi bawah.
class _Nav {
  final String path;
  final IconData icon;
  final IconData iconAktif;
  final String label;
  /// Apakah badge notifikasi tampil di layar ini?
  final bool adaBadge;
  const _Nav(this.path, this.icon, this.iconAktif, this.label,
      {this.adaBadge = false});
}

/// Navigasi bawah Synapse Mobile.
///
/// 6 tab: Chat | Special Chat | Skills | MCP | CLI | Setelan
/// (Notif DIHAPUS dari sini -> pindah jadi badge lonceng di pojok kanan atas)
const _nav = <_Nav>[
  _Nav('/chat', Icons.chat_bubble_outline, Icons.chat_bubble, 'Chat',
      adaBadge: true),
  _Nav('/special', Icons.auto_awesome_outlined, Icons.auto_awesome,
      'Special Chat', adaBadge: true),
  _Nav('/skills', Icons.extension_outlined, Icons.extension, 'Skills'),
  _Nav('/mcp', Icons.hub_outlined, Icons.hub, 'MCP'),
  _Nav('/cli', Icons.terminal_outlined, Icons.terminal, 'CLI'),
  _Nav('/settings', Icons.settings_outlined, Icons.settings, 'Setelan'),
];

/// Kerangka aplikasi: AppBar + isi + navigasi bawah.
///
/// Badge notifikasi (lonceng) HANYA tampil di Chat & Special Chat.
///
/// TAMBAHAN v1.2.1: dialog PATCHNOTE otomatis saat pertama buka setelah
/// update (menampilkan "Update dari X ke Y" + daftar perbaikan).
class AppShell extends ConsumerStatefulWidget {
  const AppShell({super.key, required this.child, required this.lokasi});

  final Widget child;
  final String lokasi;

  @override
  ConsumerState<AppShell> createState() => _AppShellState();
}

class _AppShellState extends ConsumerState<AppShell> {
  static const _kunciVersiDilihat = 'versi_patchnote_dilihat';

  @override
  void initState() {
    super.initState();
    _cekPatchnote();
  }

  /// Tampilkan patchnote SEKALI per versi (bukti update dari versi lama).
  Future<void> _cekPatchnote() async {
    try {
      final info = await PackageInfo.fromPlatform();
      final versiKini = info.version;
      final p = await SharedPreferences.getInstance();
      final terakhir = p.getString(_kunciVersiDilihat);
      if (terakhir == versiKini) return; // sudah dilihat

      final raw = await rootBundle.loadString('assets/patchnote.json');
      final d = jsonDecode(raw) as Map<String, dynamic>;
      final riwayat = ((d['riwayat'] as List?) ?? const [])
          .map((e) => Map<String, dynamic>.from(e as Map))
          .toList();
      final kini = riwayat.firstWhere(
        (r) => r['versi'] == versiKini,
        orElse: () => <String, dynamic>{},
      );
      if (kini.isEmpty) return;

      await p.setString(_kunciVersiDilihat, versiKini);
      if (!mounted) return;

      final fix = ((kini['perbaikan'] as List?) ?? const [])
          .map((e) => e.toString())
          .toList();
      final baru = ((kini['fitur_baru'] as List?) ?? const [])
          .map((e) => e.toString())
          .toList();

      showDialog<void>(
        context: context,
        builder: (c) => AlertDialog(
          title: Row(children: [
            const Icon(Icons.celebration, color: Colors.green),
            const SizedBox(width: 8),
            Expanded(child: Text('Update ke v$versiKini')),
          ]),
          content: SingleChildScrollView(
            child: Column(
              mainAxisSize: MainAxisSize.min,
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  terakhir == null
                      ? 'Selamat datang di Synapse Mobile v$versiKini!'
                      : 'Update dari v$terakhir ke v$versiKini',
                  style: const TextStyle(fontWeight: FontWeight.bold),
                ),
                if ((kini['judul'] ?? '').toString().isNotEmpty) ...[
                  const SizedBox(height: 4),
                  Text(kini['judul'].toString(),
                      style: const TextStyle(fontSize: 12)),
                ],
                const SizedBox(height: 12),
                if (fix.isNotEmpty) ...[
                  const Text('Perbaikan:',
                      style: TextStyle(fontWeight: FontWeight.bold)),
                  for (final f in fix)
                    Padding(
                      padding: const EdgeInsets.only(top: 4),
                      child: Row(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          const Text('• '),
                          Expanded(child: Text(f,
                              style: const TextStyle(fontSize: 12))),
                        ],
                      ),
                    ),
                ],
                if (baru.isNotEmpty) ...[
                  const SizedBox(height: 10),
                  const Text('Fitur baru:',
                      style: TextStyle(fontWeight: FontWeight.bold)),
                  for (final f in baru)
                    Padding(
                      padding: const EdgeInsets.only(top: 4),
                      child: Row(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          const Text('• '),
                          Expanded(child: Text(f,
                              style: const TextStyle(fontSize: 12))),
                        ],
                      ),
                    ),
                ],
              ],
            ),
          ),
          actions: [
            FilledButton(
              onPressed: () => Navigator.pop(c),
              child: const Text('Oke, mengerti'),
            ),
          ],
        ),
      );
    } catch (_) {}
  }

  int get _indeks {
    for (var i = 0; i < _nav.length; i++) {
      if (widget.lokasi.startsWith(_nav[i].path)) return i;
    }
    return 0;
  }

  bool get _tampilBadge {
    for (final n in _nav) {
      if (widget.lokasi.startsWith(n.path)) return n.adaBadge;
    }
    return false;
  }

  @override
  Widget build(BuildContext context) {
    final belumDibaca =
        ref.watch(notifProvider).where((n) => !n.dibaca).length;

    return Scaffold(
      // resize AKTIF: input naik sendiri saat keyboard muncul.
      // Avatar pakai TINGGI TETAP -> ukurannya tidak pernah berubah.
      resizeToAvoidBottomInset: true,
      // AppBar global: badge lonceng di pojok kanan atas
      // JEBAKAN #74: title AppBar TIDAK otomatis di tengah kalau ada
      // `actions`. Supaya SIMETRIS, pakai centerTitle + leading/actions
      // yang lebarnya SAMA (48px, ukuran standar IconButton).
      appBar: AppBar(
        centerTitle: true,
        leading: const SizedBox(width: 48),
        // JEBAKAN #74b: judul panjang ("Special Chat") masih bisa bergeser
        // kalau ruang kanan-kiri tidak sama. Pakai titleSpacing 0 + title
        // yang direntangkan penuh supaya BENAR-BENAR di tengah.
        titleSpacing: 0,
        title: SizedBox(
          width: double.infinity,
          child: Text(
            _nav[_indeks].label,
            textAlign: TextAlign.center,
          ),
        ),
        actions: [
          if (_tampilBadge)
            _TombolLonceng(jumlah: belumDibaca)
          else
            const SizedBox(width: 48),
          const SizedBox(width: 4),
        ],
      ),
      body: SafeArea(child: widget.child),
      bottomNavigationBar: NavigationBar(
        selectedIndex: _indeks,
        onDestinationSelected: (i) => context.go(_nav[i].path),
        destinations: [
          for (final e in _nav)
            NavigationDestination(
              icon: Icon(e.icon),
              selectedIcon: Icon(e.iconAktif),
              label: e.label,
            ),
        ],
      ),
    );
  }
}

/// Tombol lonceng dengan bulatan hijau + angka (jumlah notif belum dibaca).
class _TombolLonceng extends ConsumerWidget {
  const _TombolLonceng({required this.jumlah});
  final int jumlah;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    return Stack(
      clipBehavior: Clip.none,
      children: [
        IconButton(
          tooltip: 'Notifikasi',
          icon: const Icon(Icons.notifications_outlined),
          onPressed: () => context.push('/notifikasi'),
        ),
        if (jumlah > 0)
          Positioned(
            right: 6,
            top: 6,
            child: Container(
              padding: const EdgeInsets.symmetric(horizontal: 5, vertical: 1),
              constraints: const BoxConstraints(minWidth: 18),
              decoration: BoxDecoration(
                color: Colors.green,
                borderRadius: BorderRadius.circular(9),
                border: Border.all(color: Colors.white, width: 1.5),
              ),
              child: Text(
                jumlah > 99 ? '99+' : '$jumlah',
                textAlign: TextAlign.center,
                style: const TextStyle(
                  color: Colors.white,
                  fontSize: 10,
                  fontWeight: FontWeight.bold,
                ),
              ),
            ),
          ),
      ],
    );
  }
}

