import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
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
class AppShell extends ConsumerWidget {
  const AppShell({super.key, required this.child, required this.lokasi});

  final Widget child;
  final String lokasi;

  int get _indeks {
    for (var i = 0; i < _nav.length; i++) {
      if (lokasi.startsWith(_nav[i].path)) return i;
    }
    return 0;
  }

  bool get _tampilBadge {
    for (final n in _nav) {
      if (lokasi.startsWith(n.path)) return n.adaBadge;
    }
    return false;
  }

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final belumDibaca = ref.watch(notifProvider).where((n) => !n.dibaca).length;

    return Scaffold(
      // resize AKTIF: input naik sendiri saat keyboard muncul.
      // Avatar pakai TINGGI TETAP -> ukurannya tidak pernah berubah.
      resizeToAvoidBottomInset: true,
      // AppBar global: badge lonceng di pojok kanan atas
      appBar: AppBar(
        title: Text(_nav[_indeks].label),
        actions: [
          if (_tampilBadge)
            _TombolLonceng(jumlah: belumDibaca),
          const SizedBox(width: 4),
        ],
      ),
      body: SafeArea(child: child),
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
class _TombolLonceng extends StatelessWidget {
  const _TombolLonceng({required this.jumlah});
  final int jumlah;

  @override
  Widget build(BuildContext context) {
    final t = Theme.of(context);
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
            right: 4,
            top: 4,
            child: Container(
              padding: const EdgeInsets.symmetric(horizontal: 5, vertical: 1),
              constraints: const BoxConstraints(minWidth: 18),
              decoration: BoxDecoration(
                color: Colors.green,
                borderRadius: BorderRadius.circular(9),
                border: Border.all(color: t.colorScheme.surface, width: 1.5),
              ),
              child: Text(
                jumlah > 99 ? '99+' : '$jumlah',
                textAlign: TextAlign.center,
                style: const TextStyle(
                  color: Colors.white,
                  fontSize: 10,
                  fontWeight: FontWeight.bold,
                  height: 1.3,
                ),
              ),
            ),
          ),
      ],
    );
  }
}
