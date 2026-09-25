import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../core/sesi/sesi_model.dart';
import '../../core/sesi/sesi_provider.dart';
import '../../core/theme/spacing.dart';

/// Panel SESI (setengah layar, seperti Gemini).
/// Chat tetap terlihat di sisi kanan — tidak menutup 1 layar penuh.
class SesiDrawer extends ConsumerStatefulWidget {
  const SesiDrawer({super.key});
  @override
  ConsumerState<SesiDrawer> createState() => _SesiDrawerState();
}

class _SesiDrawerState extends ConsumerState<SesiDrawer> {
  String _cari = '';

  @override
  Widget build(BuildContext context) {
    final t = Theme.of(context);
    final n = ref.watch(sesiProvider.notifier);
    final daftar = n.cari(_cari);
    // lebar ~60% layar: setengah untuk daftar, sisanya chat tetap terlihat
    final lebar = MediaQuery.sizeOf(context).width * 0.60;

    return Drawer(
      width: lebar,
      shape: const RoundedRectangleBorder(
        borderRadius: BorderRadius.only(
          topRight: Radius.circular(18),
          bottomRight: Radius.circular(18),
        ),
      ),
      child: SafeArea(
        child: Column(
          children: [
            // ==== KEPALA PANEL ====
            Padding(
              padding: const EdgeInsets.fromLTRB(
                  AppSpacing.md, AppSpacing.md, AppSpacing.sm, AppSpacing.sm),
              child: Row(children: [
                Icon(Icons.forum_outlined, size: 20, color: t.colorScheme.primary),
                const SizedBox(width: 8),
                Expanded(
                  child: Text('Sesi Chat',
                      style: t.textTheme.titleMedium
                          ?.copyWith(fontWeight: FontWeight.w700)),
                ),
                IconButton(
                  tooltip: 'Sesi baru',
                  icon: const Icon(Icons.add_comment_outlined),
                  onPressed: () {
                    final id = n.buatBaru();
                    n.pilih(id);
                    Navigator.pop(context); // tutup panel -> tampil chat
                  },
                ),
              ]),
            ),

            // ==== PENCARIAN ====
            Padding(
              padding: const EdgeInsets.symmetric(horizontal: AppSpacing.md),
              child: TextField(
                onChanged: (v) => setState(() => _cari = v),
                decoration: const InputDecoration(
                  prefixIcon: Icon(Icons.search, size: 20),
                  hintText: 'Cari sesi...',
                  border: OutlineInputBorder(),
                  isDense: true,
                ),
              ),
            ),
            const SizedBox(height: AppSpacing.sm),

            // ==== DAFTAR SESI ====
            Expanded(
              child: daftar.isEmpty
                  ? Center(
                      child: Padding(
                        padding: const EdgeInsets.all(AppSpacing.md),
                        child: Column(
                          mainAxisAlignment: MainAxisAlignment.center,
                          children: [
                            Icon(Icons.forum_outlined,
                                size: 40, color: t.colorScheme.outline),
                            const SizedBox(height: AppSpacing.sm),
                            Text(
                              _cari.isEmpty
                                  ? 'Belum ada sesi.\nTekan + untuk mulai.'
                                  : 'Tidak ada yang cocok.',
                              textAlign: TextAlign.center,
                              style: t.textTheme.bodySmall,
                            ),
                          ],
                        ),
                      ),
                    )
                  : ListView.builder(
                      padding: const EdgeInsets.symmetric(
                          horizontal: AppSpacing.sm),
                      itemCount: daftar.length,
                      itemBuilder: (c, i) {
                        final s = daftar[i];
                        final aktif = s.id == n.aktifId;
                        return Material(
                          color: aktif
                              ? t.colorScheme.primaryContainer
                                  .withValues(alpha: 0.45)
                              : Colors.transparent,
                          borderRadius: BorderRadius.circular(10),
                          child: InkWell(
                            borderRadius: BorderRadius.circular(10),
                            onTap: () {
                              n.pilih(s.id);
                              Navigator.pop(context); // tutup panel
                            },
                            child: Padding(
                              padding: const EdgeInsets.symmetric(
                                  horizontal: 10, vertical: 10),
                              child: Row(children: [
                                Icon(
                                  s.dipin
                                      ? Icons.push_pin
                                      : Icons.chat_bubble_outline,
                                  size: 18,
                                  color: aktif
                                      ? t.colorScheme.primary
                                      : t.colorScheme.outline,
                                ),
                                const SizedBox(width: 10),
                                Expanded(
                                  child: Column(
                                    crossAxisAlignment:
                                        CrossAxisAlignment.start,
                                    children: [
                                      Text(
                                        s.judulTampil,
                                        maxLines: 1,
                                        overflow: TextOverflow.ellipsis,
                                        style: t.textTheme.bodyMedium?.copyWith(
                                          fontWeight: aktif
                                              ? FontWeight.w700
                                              : FontWeight.w500,
                                        ),
                                      ),
                                      const SizedBox(height: 2),
                                      Text(
                                        '${s.pesan.length} pesan · ${s.cuplikan}',
                                        maxLines: 1,
                                        overflow: TextOverflow.ellipsis,
                                        style: t.textTheme.bodySmall?.copyWith(
                                          color: t.colorScheme.outline,
                                          fontSize: 11,
                                        ),
                                      ),
                                    ],
                                  ),
                                ),
                                // titik tiga: pin / ganti nama / hapus
                                PopupMenuButton<String>(
                                  icon: const Icon(Icons.more_vert, size: 18),
                                  tooltip: 'Opsi',
                                  padding: EdgeInsets.zero,
                                  onSelected: (v) {
                                    if (v == 'pin') n.pin(s.id);
                                    if (v == 'rename') _gantiNama(context, s);
                                    if (v == 'hapus') _konfirmasiHapus(context, s);
                                  },
                                  itemBuilder: (c) => [
                                    PopupMenuItem(
                                      value: 'pin',
                                      child: ListTile(
                                        dense: true,
                                        leading: Icon(s.dipin
                                            ? Icons.push_pin_outlined
                                            : Icons.push_pin,
                                            size: 20),
                                        title: Text(
                                            s.dipin ? 'Lepas pin' : 'Pin'),
                                      ),
                                    ),
                                    const PopupMenuItem(
                                      value: 'rename',
                                      child: ListTile(
                                        dense: true,
                                        leading:
                                            Icon(Icons.edit_outlined, size: 20),
                                        title: Text('Ganti nama'),
                                      ),
                                    ),
                                    const PopupMenuItem(
                                      value: 'hapus',
                                      child: ListTile(
                                        dense: true,
                                        leading:
                                            Icon(Icons.delete_outline, size: 20),
                                        title: Text('Hapus'),
                                      ),
                                    ),
                                  ],
                                ),
                              ]),
                            ),
                          ),
                        );
                      },
                    ),
            ),
          ],
        ),
      ),
    );
  }

  /// Ganti nama sesi.
  Future<void> _gantiNama(BuildContext context, Sesi s) async {
    final ctrl = TextEditingController(text: s.judulTampil);
    final baru = await showDialog<String>(
      context: context,
      builder: (c) => AlertDialog(
        title: const Text('Ganti nama sesi'),
        content: TextField(
          controller: ctrl,
          autofocus: true,
          decoration: const InputDecoration(
            labelText: 'Nama sesi',
            border: OutlineInputBorder(),
          ),
        ),
        actions: [
          TextButton(
              onPressed: () => Navigator.pop(c), child: const Text('Batal')),
          FilledButton(
              onPressed: () => Navigator.pop(c, ctrl.text),
              child: const Text('Simpan')),
        ],
      ),
    );
    if (baru != null && baru.trim().isNotEmpty) {
      ref.read(sesiProvider.notifier).gantiJudul(s.id, baru);
    }
  }

  /// Konfirmasi hapus (Ya/Tidak).
  Future<void> _konfirmasiHapus(BuildContext context, Sesi s) async {
    final ya = await showDialog<bool>(
      context: context,
      builder: (c) => AlertDialog(
        title: const Text('Hapus sesi?'),
        content: Text('Sesi "${s.judulTampil}" akan dihapus permanen.\n'
            'Tindakan ini tidak bisa dibatalkan.'),
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
    if (ya == true) {
      ref.read(sesiProvider.notifier).hapus(s.id);
    }
  }
}
