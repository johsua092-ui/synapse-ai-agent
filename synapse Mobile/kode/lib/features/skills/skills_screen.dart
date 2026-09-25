import 'dart:convert';
import 'package:flutter/material.dart';
import 'package:flutter/services.dart' show rootBundle;
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../core/api/api_config.dart';
import '../../core/api/api_providers.dart';
import '../../core/theme/spacing.dart';

/// Satu skill di katalog.
class SkillItem {
  final String name;
  final String description;
  final String category;
  bool installed;
  SkillItem({
    required this.name,
    required this.description,
    this.category = '',
    this.installed = false,
  });

  factory SkillItem.fromJson(Map<String, dynamic> j) => SkillItem(
        name: (j['name'] ?? '').toString(),
        description: (j['description'] ?? '').toString(),
        category: (j['category'] ?? '').toString(),
        installed: j['installed'] == true,
      );
}

/// Katalog skill BAWAAN (dibawa di dalam APK) — supaya daftar SELALU tampil
/// walau belum tersambung ke server.
class KatalogNotifier extends StateNotifier<List<SkillItem>> {
  KatalogNotifier() : super([]) {
    _muat();
  }

  Future<void> _muat() async {
    try {
      final raw = await rootBundle.loadString('assets/katalog_skill.json');
      final d = jsonDecode(raw) as Map<String, dynamic>;
      final list = ((d['skills'] as List?) ?? const [])
          .map((e) => SkillItem.fromJson(e as Map<String, dynamic>))
          .toList();
      state = list;
    } catch (_) {
      state = [];
    }
  }
}

final katalogProvider =
    StateNotifierProvider<KatalogNotifier, List<SkillItem>>((ref) => KatalogNotifier());

/// Layar Skills:
///  - daftar skill SELALU tampil (dari katalog bawaan APK)
///  - tombol "i" (info) SELALU ada
///  - tombol Install/Uninstall HANYA kalau sudah isi Base URL + API Key
class SkillsScreen extends ConsumerStatefulWidget {
  const SkillsScreen({super.key});
  @override
  ConsumerState<SkillsScreen> createState() => _SkillsScreenState();
}

class _SkillsScreenState extends ConsumerState<SkillsScreen> {
  String _cari = '';
  final Set<String> _terpasang = {};

  @override
  Widget build(BuildContext context) {
    final t = Theme.of(context);
    final cfg = ref.watch(apiConfigProvider);
    final klien = ref.watch(apiClientProvider);
    final bolehUbah = cfg.terisi && klien != null;

    final semua = ref.watch(katalogProvider);
    final kunci = _cari.trim().toLowerCase();
    final data = kunci.isEmpty
        ? semua
        : semua
            .where((s) =>
                s.name.toLowerCase().contains(kunci) ||
                s.description.toLowerCase().contains(kunci))
            .toList();

    return Scaffold(
      appBar: AppBar(
        title: const Text('Skills'),
        actions: [
          Padding(
            padding: const EdgeInsets.only(right: 12),
            child: Center(
              child: Chip(
                avatar: Icon(
                  bolehUbah ? Icons.cloud_done : Icons.visibility,
                  size: 16,
                ),
                label: Text(bolehUbah
                    ? '${semua.length} skill'
                    : 'Hanya lihat · ${semua.length}'),
                backgroundColor: t.colorScheme.surfaceContainerHighest,
              ),
            ),
          ),
        ],
      ),
      body: Column(
        children: [
          Padding(
            padding: const EdgeInsets.all(AppSpacing.md),
            child: Column(
              children: [
                if (!bolehUbah) ...[
                  Row(children: [
                    Icon(Icons.info_outline,
                        size: 16, color: t.colorScheme.outline),
                    const SizedBox(width: 6),
                    Expanded(
                      child: Text(
                        'Isi Base URL + API Key di Setelan untuk mengaktifkan '
                        'Install/Uninstall. Sekarang hanya bisa lihat info (i).',
                        style: t.textTheme.bodySmall,
                      ),
                    ),
                  ]),
                  const SizedBox(height: AppSpacing.sm),
                ],
                TextField(
                  onChanged: (v) => setState(() => _cari = v),
                  decoration: const InputDecoration(
                    prefixIcon: Icon(Icons.search),
                    hintText: 'Cari skill...',
                    border: OutlineInputBorder(),
                    isDense: true,
                  ),
                ),
              ],
            ),
          ),
          Expanded(
            child: semua.isEmpty
                ? const Center(child: CircularProgressIndicator())
                : data.isEmpty
                    ? Center(
                        child: Padding(
                          padding: const EdgeInsets.all(AppSpacing.lg),
                          child: Text('Tidak ada skill cocok dengan "$_cari".',
                              textAlign: TextAlign.center,
                              style: t.textTheme.bodyMedium),
                        ),
                      )
                    : ListView.separated(
                        padding: const EdgeInsets.symmetric(
                            horizontal: AppSpacing.md),
                        itemCount: data.length,
                        separatorBuilder: (_, __) => const Divider(height: 1),
                        itemBuilder: (c, i) {
                          final s = data[i];
                          final on = _terpasang.contains(s.name);
                          return ListTile(
                            contentPadding: EdgeInsets.zero,
                            leading: Icon(
                              on ? Icons.check_circle : Icons.extension_outlined,
                              color: on ? Colors.green : null,
                            ),
                            title: Text(s.name, style: t.textTheme.titleSmall),
                            subtitle: Text(
                              s.description,
                              maxLines: 2,
                              overflow: TextOverflow.ellipsis,
                              style: t.textTheme.bodySmall,
                            ),
                            trailing: Row(mainAxisSize: MainAxisSize.min, children: [
                              // tombol "i" (info) — SELALU ada
                              IconButton(
                                icon: const Icon(Icons.info_outline),
                                tooltip: 'Info',
                                onPressed: () => _info(context, s),
                              ),
                              // tombol install/uninstall — HANYA kalau tersambung
                              if (bolehUbah)
                                IconButton(
                                  icon: Icon(on
                                      ? Icons.delete_outline
                                      : Icons.download_outlined),
                                  tooltip: on ? 'Uninstall' : 'Install',
                                  color: on ? Colors.red : t.colorScheme.primary,
                                  onPressed: () => _ubah(context, s, !on),
                                ),
                            ]),
                            onTap: () => _info(context, s),
                          );
                        },
                      ),
          ),
        ],
      ),
    );
  }

  /// Tombol "i" — beberkan deskripsi lengkap + tombol install/uninstall.
  void _info(BuildContext context, SkillItem s) {
    final bolehUbah = ref.read(apiConfigProvider).terisi;
    showModalBottomSheet(
      context: context,
      showDragHandle: true,
      isScrollControlled: true,
      builder: (c) {
        final t = Theme.of(c);
        final on = _terpasang.contains(s.name);
        return Padding(
          padding: const EdgeInsets.all(AppSpacing.lg),
          child: Column(
            mainAxisSize: MainAxisSize.min,
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Row(children: [
                const Icon(Icons.extension),
                const SizedBox(width: 8),
                Expanded(
                    child: Text(s.name, style: t.textTheme.titleMedium)),
              ]),
              if (s.category.isNotEmpty) ...[
                const SizedBox(height: 4),
                Text(s.category,
                    style: t.textTheme.bodySmall
                        ?.copyWith(color: t.colorScheme.outline)),
              ],
              const SizedBox(height: AppSpacing.md),
              Text(s.description.isEmpty ? '(tanpa deskripsi)' : s.description),
              const SizedBox(height: AppSpacing.lg),
              if (bolehUbah)
                Row(children: [
                  Expanded(
                    child: FilledButton.icon(
                      onPressed: () {
                        Navigator.pop(c);
                        _ubah(context, s, true);
                      },
                      icon: const Icon(Icons.download),
                      label: const Text('Install'),
                    ),
                  ),
                  const SizedBox(width: AppSpacing.sm),
                  Expanded(
                    child: OutlinedButton.icon(
                      onPressed: () {
                        Navigator.pop(c);
                        _ubah(context, s, false);
                      },
                      icon: const Icon(Icons.delete_outline),
                      label: const Text('Uninstall'),
                    ),
                  ),
                ])
              else
                Container(
                  padding: const EdgeInsets.all(AppSpacing.md),
                  decoration: BoxDecoration(
                    color: t.colorScheme.surfaceContainerHighest,
                    borderRadius: BorderRadius.circular(8),
                  ),
                  child: Row(children: [
                    Icon(Icons.lock_outline,
                        size: 16, color: t.colorScheme.outline),
                    const SizedBox(width: 8),
                    Expanded(
                      child: Text(
                        'Isi Base URL + API Key di Setelan untuk memasang skill.',
                        style: t.textTheme.bodySmall,
                      ),
                    ),
                  ]),
                ),
              const SizedBox(height: AppSpacing.sm),
            ],
          ),
        );
      },
    );
  }

  /// Konfirmasi Ya/Tidak -> install/uninstall lewat AGENT.
  Future<void> _ubah(BuildContext context, SkillItem s, bool install) async {
    final ya = await showDialog<bool>(
      context: context,
      builder: (c) => AlertDialog(
        title: Text(install ? 'Install skill?' : 'Uninstall skill?'),
        content: Text('${install ? 'Install' : 'Uninstall'} "${s.name}"?'),
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
    if (ya != true || !mounted) return;

    final klien = ref.read(apiClientProvider);
    if (klien == null) return;

    final cmd = install
        ? 'synapse skills install ${s.name}'
        : 'synapse skills uninstall ${s.name}';

    ScaffoldMessenger.of(context).showSnackBar(SnackBar(
        content: Text('${install ? 'Menginstall' : 'Menghapus'} "${s.name}"...')));

    try {
      final hasil = await klien.perintahAgent(cmd);
      if (!mounted) return;
      setState(() {
        if (install) {
          _terpasang.add(s.name);
        } else {
          _terpasang.remove(s.name);
        }
      });
      ScaffoldMessenger.of(context).showSnackBar(SnackBar(
        content: Text(hasil.length > 120 ? '${hasil.substring(0, 120)}...' : hasil),
        duration: const Duration(seconds: 6),
      ));
    } catch (e) {
      if (!mounted) return;
      ScaffoldMessenger.of(context)
          .showSnackBar(SnackBar(content: Text('Gagal: $e')));
    }
  }
}
