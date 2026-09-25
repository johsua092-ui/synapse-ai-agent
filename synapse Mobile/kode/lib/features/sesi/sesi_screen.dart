import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import '../../core/sesi/sesi_model.dart';
import '../../core/sesi/sesi_provider.dart';
import '../../core/theme/spacing.dart';

/// Layar daftar sesi chat:
///  - banyak sesi tersimpan
///  - kolom pencarian
///  - titik tiga -> Pin / Rename / Hapus (dengan konfirmasi Ya/Tidak)
class SesiScreen extends ConsumerStatefulWidget {
  const SesiScreen({super.key});
  @override
  ConsumerState<SesiScreen> createState() => _SesiScreenState();
}

class _SesiScreenState extends ConsumerState<SesiScreen> {
  String _cari = '';

  @override
  Widget build(BuildContext context) {
    final t = Theme.of(context);
    final n = ref.watch(sesiProvider.notifier);
    final daftar = n.cari(_cari);

    return Scaffold(
      appBar: AppBar(
        title: const Text('Sesi Chat'),
        actions: [
          IconButton(
            tooltip: 'Sesi baru',
            icon: const Icon(Icons.add_comment_outlined),
            onPressed: () {
              n.buatBaru();
              context.go('/chat');
            },
          ),
        ],
      ),
      body: Column(
        children: [
          // pencarian
          Padding(
            padding: const EdgeInsets.all(AppSpacing.md),
            child: TextField(
              onChanged: (v) => setState(() => _cari = v),
              decoration: const InputDecoration(
                prefixIcon: Icon(Icons.search),
                hintText: 'Cari sesi / isi pesan...',
                border: OutlineInputBorder(),
                isDense: true,
              ),
            ),
          ),
          Expanded(
            child: daftar.isEmpty
                ? Center(
                    child: Padding(
                      padding: const EdgeInsets.all(AppSpacing.lg),
                      child: Column(
                        mainAxisAlignment: MainAxisAlignment.center,
                        children: [
                          Icon(Icons.forum_outlined,
                              size: 48, color: t.colorScheme.outline),
                          const SizedBox(height: AppSpacing.md),
                          Text(
                            _cari.isEmpty
                                ? 'Belum ada sesi.\nTekan + untuk mulai percakapan baru.'
                                : 'Tidak ada sesi yang cocok dengan "$_cari".',
                            textAlign: TextAlign.center,
                            style: t.textTheme.bodyMedium,
                          ),
                        ],
                      ),
                    ),
                  )
                : ListView.separated(
                    padding: const EdgeInsets.symmetric(horizontal: AppSpacing.sm),
                    itemCount: daftar.length,
                    separatorBuilder: (_, __) => const Divider(height: 1),
                    itemBuilder: (c, i) {
                      final s = daftar[i];
                      final aktif = s.id == n.aktifId;
                      return ListTile(
                        leading: CircleAvatar(
                          backgroundColor: aktif
                              ? t.colorScheme.primary
                              : t.colorScheme.surfaceContainerHighest,
                          child: Icon(
                            s.dipin ? Icons.push_pin : Icons.chat_bubble_outline,
                            size: 18,
                            color: aktif ? t.colorScheme.onPrimary : null,
                          ),
                        ),
                        title: Row(children: [
                          if (s.dipin) ...[
                            Icon(Icons.push_pin,
                                size: 14, color: t.colorScheme.primary),
                            const SizedBox(width: 4),
                          ],
                          Expanded(
                            child: Text(
                              s.judulTampil,
                              maxLines: 1,
                              overflow: TextOverflow.ellipsis,
                              style: t.textTheme.titleSmall?.copyWith(
                                fontWeight:
                                    aktif ? FontWeight.w700 : FontWeight.normal,
                              ),
                            ),
                          ),
                        ]),
                        subtitle: Text(
                          '${s.pesan.length} pesan · ${s.cuplikan}',
                          maxLines: 1,
                          overflow: TextOverflow.ellipsis,
                          style: t.textTheme.bodySmall,
                        ),
                        trailing: PopupMenuButton<String>(
                          icon: const Icon(Icons.more_vert),
                          tooltip: 'Opsi',
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
                                    : Icons.push_pin),
                                title: Text(s.dipin ? 'Lepas pin' : 'Pin'),
                              ),
                            ),
                            const PopupMenuItem(
                              value: 'rename',
                              child: ListTile(
                                dense: true,
                                leading: Icon(Icons.edit_outlined),
                                title: Text('Ganti nama'),
                              ),
                            ),
                            const PopupMenuItem(
                              value: 'hapus',
                              child: ListTile(
                                dense: true,
                                leading: Icon(Icons.delete_outline),
                                title: Text('Hapus'),
                              ),
                            ),
                          ],
                        ),
                        onTap: () {
                          n.pilih(s.id);
                          context.go('/chat');
                        },
                      );
                    },
                  ),
          ),
        ],
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
            onPressed: () => Navigator.pop(c),
            child: const Text('Batal'),
          ),
          FilledButton(
            onPressed: () => Navigator.pop(c, ctrl.text),
            child: const Text('Simpan'),
          ),
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
        content: Text(
          'Sesi "${s.judulTampil}" akan dihapus permanen.\n'
          'Tindakan ini tidak bisa dibatalkan.',
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(c, false),
            child: const Text('Tidak'),
          ),
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
      if (!context.mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Sesi dihapus')),
      );
    }
  }
}
