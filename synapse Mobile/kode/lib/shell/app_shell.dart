import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:go_router/go_router.dart';

/// Item navigasi utama.
class _Nav {
  final String path;
  final IconData icon;
  final IconData iconAktif;
  final String label;
  const _Nav(this.path, this.icon, this.iconAktif, this.label);
}

const _items = <_Nav>[
  _Nav('/chat', Icons.chat_bubble_outline, Icons.chat_bubble, 'Chat'),
  _Nav('/skills', Icons.extension_outlined, Icons.extension, 'Skills'),
  _Nav('/mcp', Icons.hub_outlined, Icons.hub, 'MCP'),
  _Nav('/cli', Icons.terminal_outlined, Icons.terminal, 'CLI'),
  _Nav('/notifikasi', Icons.notifications_outlined, Icons.notifications, 'Notif'),
  _Nav('/settings', Icons.settings_outlined, Icons.settings, 'Setelan'),
];

/// Kerangka aplikasi:
///  - POTRAIT  (9:16)  -> navigasi BAWAH
///  - LANDSCAPE(16:9)  -> navigasi SAMPING
///
/// Perilaku tombol BACK:
///  - Di sub-menu (Skills/MCP/CLI/Setelan/...) -> kembali ke layar Chat
///  - Di layar utama (Chat) -> minta konfirmasi "tekan sekali lagi untuk keluar"
class AppShell extends StatefulWidget {
  final Widget child;
  const AppShell({super.key, required this.child});

  @override
  State<AppShell> createState() => _AppShellState();
}

class _AppShellState extends State<AppShell> {
  DateTime? _backTerakhir;

  int _indeks(BuildContext c) {
    final lok = GoRouterState.of(c).uri.path;
    final i = _items.indexWhere((e) => lok.startsWith(e.path));
    return i < 0 ? 0 : i;
  }

  void _pindah(BuildContext c, int i) => c.go(_items[i].path);

  bool _diLayarUtama(BuildContext c) {
    final lok = GoRouterState.of(c).uri.path;
    return lok == '/chat' || lok == '/';
  }

  /// Dipanggil saat tombol back ditekan.
  /// return false = jangan keluar aplikasi.
  ///
  /// URUTAN (sesuai permintaan user):
  ///  1. Kalau ada HISTORY (mis. Setelan -> Status) -> kembali ke INDUK (Setelan)
  ///  2. Kalau tidak ada history & bukan di Chat -> ke Chat
  ///  3. Kalau di Chat -> minta konfirmasi (tekan 2x baru keluar)
  bool _tanganiBack(BuildContext c) {
    final router = GoRouter.of(c);

    // 1. Ada history? -> kembali satu tingkat (ke halaman INDUK)
    if (router.canPop()) {
      router.pop();
      return false;   // jangan keluar
    }

    // 2. Bukan di layar utama -> ke Chat
    if (!_diLayarUtama(c)) {
      c.go('/chat');
      return false;   // jangan keluar
    }

    // 3. Di layar utama -> minta konfirmasi (tekan 2x)
    final sekarang = DateTime.now();
    final baru = _backTerakhir == null ||
        sekarang.difference(_backTerakhir!) > const Duration(seconds: 2);

    if (baru) {
      _backTerakhir = sekarang;
      ScaffoldMessenger.of(c).showSnackBar(
        const SnackBar(
          content: Text('Tekan sekali lagi tombol back untuk keluar'),
          duration: Duration(seconds: 2),
        ),
      );
      return false;   // jangan keluar (tunggu tekan ke-2)
    }

    return true;      // tekan ke-2 -> keluar
  }

  @override
  Widget build(BuildContext context) {
    final w = MediaQuery.sizeOf(context).width;
    final h = MediaQuery.sizeOf(context).height;
    final landscape = w > h;
    final idx = _indeks(context);

    return PopScope(
      // canPop=false -> kita tangani sendiri lewat onPopInvoked
      canPop: false,
      onPopInvokedWithResult: (didPop, _) {
        if (didPop) return;
        final bolehKeluar = _tanganiBack(context);
        if (bolehKeluar) {
          // keluar aplikasi (SystemNavigator = benar-benar keluar,
          // bukan Navigator.maybePop yang bikin loop)
          SystemNavigator.pop();
        }
      },
      child: landscape
          ? _landscape(idx, context)
          : _potrait(idx, context),
    );
  }

  // ===== LANDSCAPE 16:9 -> navigasi samping =====
  Widget _landscape(int idx, BuildContext context) => Scaffold(
        body: Row(children: [
          NavigationRail(
            selectedIndex: idx,
            onDestinationSelected: (i) => _pindah(context, i),
            labelType: NavigationRailLabelType.all,
            leading: const Padding(
              padding: EdgeInsets.symmetric(vertical: 12),
              child: Icon(Icons.bolt, size: 26),
            ),
            destinations: _items
                .map((e) => NavigationRailDestination(
                      icon: Icon(e.icon),
                      selectedIcon: Icon(e.iconAktif),
                      label: Text(e.label),
                    ))
                .toList(),
          ),
          const VerticalDivider(width: 1),
          Expanded(child: widget.child),
        ]),
      );

  // ===== POTRAIT 9:16 -> navigasi bawah =====
  Widget _potrait(int idx, BuildContext context) => Scaffold(
        body: widget.child,
        bottomNavigationBar: NavigationBar(
          selectedIndex: idx,
          onDestinationSelected: (i) => _pindah(context, i),
          destinations: _items
              .map((e) => NavigationDestination(
                    icon: Icon(e.icon),
                    selectedIcon: Icon(e.iconAktif),
                    label: e.label,
                  ))
              .toList(),
        ),
      );
}
