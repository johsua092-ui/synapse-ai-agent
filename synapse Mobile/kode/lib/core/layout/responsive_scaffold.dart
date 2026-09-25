import 'package:flutter/material.dart';

import '../theme/spacing.dart';
import 'breakpoints.dart';

/// Kerangka responsif: SATU widget, DUA tata letak.
///
/// - Potrait (9:16)  -> [body] 1 kolom, [navItems] jadi navigasi BAWAH
/// - Landscape (16:9) -> [body] + [sideList] 2 kolom, [navItems] jadi navigasi SAMPING
///
/// Ini yang membuat aplikasi NYAMAN di dua mode — bukan sekadar memutar potrait.
class ResponsiveScaffold extends StatelessWidget {
  const ResponsiveScaffold({
    super.key,
    required this.title,
    required this.body,
    this.sideList,
    this.navItems = const [],
    this.navIndex = 0,
    this.onNavTap,
    this.actions,
  });

  final String title;
  final Widget body;
  /// Panel kiri (hanya dipakai di landscape 16:9).
  final Widget? sideList;
  final List<NavItem> navItems;
  final int navIndex;
  final ValueChanged<int>? onNavTap;
  final List<Widget>? actions;

  @override
  Widget build(BuildContext context) {
    final twoPane = Breakpoints.useTwoPane(context);

    if (twoPane) {
      // ===== LANDSCAPE 16:9: navigasi SAMPING + 2 kolom =====
      return Scaffold(
        body: SafeArea(
          child: Row(
            children: [
              if (navItems.isNotEmpty)
                _SideNav(items: navItems, index: navIndex, onTap: onNavTap),
              if (sideList != null) ...[
                SizedBox(width: 320, child: sideList!),
                const VerticalDivider(width: 1),
              ],
              Expanded(
                child: Column(
                  children: [
                    _Header(title: title, actions: actions),
                    Expanded(child: body),
                  ],
                ),
              ),
            ],
          ),
        ),
      );
    }

    // ===== POTRAIT 9:16: navigasi BAWAH =====
    return Scaffold(
      appBar: AppBar(
        title: Text(title),
        actions: actions,
      ),
      body: SafeArea(child: body),
      bottomNavigationBar: navItems.isEmpty
          ? null
          : NavigationBar(
              height: AppSpacing.navBarHeight,
              selectedIndex: navIndex,
              onDestinationSelected: onNavTap,
              destinations: navItems
                  .map((e) => NavigationDestination(icon: Icon(e.icon), label: e.label))
                  .toList(),
            ),
    );
  }
}

/// Item navigasi.
class NavItem {
  const NavItem({required this.icon, required this.label});
  final IconData icon;
  final String label;
}

class _Header extends StatelessWidget {
  const _Header({required this.title, this.actions});
  final String title;
  final List<Widget>? actions;

  @override
  Widget build(BuildContext context) {
    return SizedBox(
      height: AppSpacing.headerHeight,
      child: Padding(
        padding: const EdgeInsets.symmetric(horizontal: AppSpacing.lg),
        child: Row(
          children: [
            Text(title, style: Theme.of(context).textTheme.titleLarge),
            const Spacer(),
            if (actions != null) ...actions!,
          ],
        ),
      ),
    );
  }
}

/// Navigasi samping (khusus landscape 16:9).
class _SideNav extends StatelessWidget {
  const _SideNav({required this.items, required this.index, this.onTap});
  final List<NavItem> items;
  final int index;
  final ValueChanged<int>? onTap;

  @override
  Widget build(BuildContext context) {
    final surface = Theme.of(context).colorScheme.surface;
    return Container(
      width: 88,
      color: surface,
      child: Column(
        children: [
          const SizedBox(height: AppSpacing.md),
          for (var i = 0; i < items.length; i++)
            _SideNavTile(
              item: items[i],
              selected: i == index,
              onTap: () => onTap?.call(i),
            ),
        ],
      ),
    );
  }
}

class _SideNavTile extends StatelessWidget {
  const _SideNavTile({required this.item, required this.selected, this.onTap});
  final NavItem item;
  final bool selected;
  final VoidCallback? onTap;

  @override
  Widget build(BuildContext context) {
    final scheme = Theme.of(context).colorScheme;
    return InkWell(
      onTap: onTap,
      child: Container(
        height: 64,
        margin: const EdgeInsets.symmetric(vertical: AppSpacing.xs / 2),
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Icon(item.icon, size: 22,
                color: selected ? scheme.primary : scheme.onSurface.withValues(alpha: 0.6)),
            const SizedBox(height: 4),
            Text(item.label,
                style: TextStyle(fontSize: 11,
                    color: selected ? scheme.primary : scheme.onSurface.withValues(alpha: 0.6))),
          ],
        ),
      ),
    );
  }
}
