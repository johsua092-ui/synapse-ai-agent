import 'dart:convert';
import 'package:flutter/material.dart';
import 'package:flutter/services.dart' show rootBundle;
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../core/api/api_config.dart';
import '../../core/api/api_providers.dart';
import '../../core/theme/spacing.dart';
import 'package:shared_preferences/shared_preferences.dart';

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
  /// Skill buatan user: [{nama, desk, isi}]
  List<Map<String, dynamic>> _custom = [];
  static const _kunciCustom = 'skill_custom';

  @override
  void initState() {
    super.initState();
    _muatCustom();
  }

  Future<void> _muatCustom() async {
    try {
      final p = await SharedPreferences.getInstance();
      final c = p.getString(_kunciCustom);
      if (c != null && c.isNotEmpty && mounted) {
        setState(() => _custom = (jsonDecode(c) as List)
            .map((e) => Map<String, dynamic>.from(e as Map))
            .toList());
      }
    } catch (_) {}
  }

  Future<void> _simpanCustom() async {
    final p = await SharedPreferences.getInstance();
    await p.setString(_kunciCustom, jsonEncode(_custom));
  }

  /// Dialog BUAT / EDIT skill sendiri.
  Future<void> _dialogSkill({Map<String, dynamic>? awal, int? indeks}) async {
    final nama = TextEditingController(text: (awal?['nama'] ?? '') as String);
    final desk = TextEditingController(text: (awal?['desk'] ?? '') as String);
    final isi = TextEditingController(text: (awal?['isi'] ?? '') as String);

    await showDialog<void>(
      context: context,
      builder: (c) => AlertDialog(
        title: Text(indeks == null ? 'Buat Skill Sendiri' : 'Edit Skill'),
        content: SingleChildScrollView(
          child: Column(mainAxisSize: MainAxisSize.min, children: [
            TextField(
              controller: nama,
              decoration: const InputDecoration(
                  labelText: 'Nama skill', hintText: 'mis. catat-keuangan'),
            ),
            const SizedBox(height: 10),
            TextField(
              controller: desk,
              decoration: const InputDecoration(labelText: 'Keterangan'),
            ),
            const SizedBox(height: 10),
            TextField(
              controller: isi,
              maxLines: 5,
              decoration: const InputDecoration(
                labelText: 'Isi skill (instruksi)',
                hintText: 'Tulis langkah/instruksi untuk AI...',
                alignLabelWithHint: true,
              ),
            ),
          ]),
        ),
        actions: [
          TextButton(
              onPressed: () => Navigator.pop(c), child: const Text('Batal')),
          FilledButton(
            onPressed: () {
              if (nama.text.trim().isEmpty) return;
              setState(() {
                final d = {
                  'nama': nama.text.trim(),
                  'desk': desk.text.trim().isEmpty
                      ? 'Skill buatan sendiri'
                      : desk.text.trim(),
                  'isi': isi.text.trim(),
                };
                if (indeks == null) {
                  _custom.add(d);
                } else {
                  _custom[indeks] = d;
                }
              });
              _simpanCustom();
              Navigator.pop(c);
            },
            child: const Text('Simpan'),
          ),
        ],
      ),
    );
  }

  Future<void> _hapusSkill(int i) async {
    final nama = _custom[i]['nama'];
    final ya = await showDialog<bool>(
      context: context,
      builder: (c) => AlertDialog(
        title: const Text('Hapus skill?'),
        content: Text('Skill "$nama" akan dihapus.'),
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
    setState(() => _custom.removeAt(i));
    _simpanCustom();
  }

  /// Pasang skill sendiri ke agent.
  Future<void> _pasangSkill(int i) async {
    final m = _custom[i];
    final klien = ref.read(apiClientProvider);
    if (klien == null) {
      _pesan('Belum tersambung. Isi Base URL + API Key di Setelan.');
      return;
    }
    _pesan('Memasang skill "${m['nama']}" di laptop...');
    try {
      final perintah =
          'Buat skill Synapse baru dengan data ini:\n'
          'NAMA: ${m['nama']}\nKETERANGAN: ${m['desk']}\n'
          'ISI/INSTRUKSI:\n${m['isi']}\n\n'
          'Buat file SKILL.md di folder skills Synapse dengan frontmatter '
          '(name, description) + isi instruksi di atas, lalu laporkan singkat: '
          'berhasil/gagal + path file.';
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
          IconButton(
            tooltip: 'Buat skill sendiri',
            icon: const Icon(Icons.add),
            onPressed: () => _dialogSkill(),
          ),
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
          // ---- SKILL SAYA (buatan sendiri) ----
          if (_custom.isNotEmpty) ...[
            Padding(
              padding: const EdgeInsets.fromLTRB(
                  AppSpacing.md, AppSpacing.sm, AppSpacing.md, 4),
              child: Row(children: [
                Icon(Icons.person_outline,
                    size: 18, color: t.colorScheme.primary),
                const SizedBox(width: 6),
                Text('Skill Saya (${_custom.length})',
                    style: t.textTheme.titleSmall),
              ]),
            ),
            ...List.generate(_custom.length, (i) {
              final m = _custom[i];
              return ListTile(
                leading: Icon(Icons.extension, color: t.colorScheme.primary),
                title: Text(m['nama'] as String),
                subtitle: Text(m['desk'] as String,
                    maxLines: 2, overflow: TextOverflow.ellipsis),
                trailing: Row(mainAxisSize: MainAxisSize.min, children: [
                  IconButton(
                    icon: const Icon(Icons.cloud_upload_outlined),
                    tooltip: 'Pasang ke agent',
                    color: t.colorScheme.primary,
                    onPressed: () => _pasangSkill(i),
                  ),
                  IconButton(
                    icon: const Icon(Icons.edit_outlined),
                    tooltip: 'Edit',
                    onPressed: () => _dialogSkill(awal: m, indeks: i),
                  ),
                  IconButton(
                    icon: const Icon(Icons.delete_outline),
                    tooltip: 'Hapus',
                    color: Colors.red,
                    onPressed: () => _hapusSkill(i),
                  ),
                ]),
                onTap: () => _dialogSkill(awal: m, indeks: i),
              );
            }),
            const Divider(),
            Padding(
              padding: const EdgeInsets.fromLTRB(
                  AppSpacing.md, 4, AppSpacing.md, 4),
              child: Row(children: [
                Icon(Icons.inventory_2_outlined,
                    size: 18, color: t.colorScheme.primary),
                const SizedBox(width: 6),
                Text('Katalog Bawaan (${semua.length})',
                    style: t.textTheme.titleSmall),
              ]),
            ),
          ],
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
      final hasil = await klien.perintahAgent(cmd, panjang: true);
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
