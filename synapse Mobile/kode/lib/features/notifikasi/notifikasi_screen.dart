import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../core/notif/notif_provider.dart';
import '../../core/theme/spacing.dart';

/// Layar Notifikasi — memakai provider bersama (badge lonceng tersinkron).
class NotifikasiScreen extends ConsumerWidget {
  const NotifikasiScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final t = Theme.of(context);
    final daftar = ref.watch(notifProvider);
    final notif = ref.read(notifProvider.notifier);
    final belum = notif.belumDibaca;

    return Scaffold(
      appBar: AppBar(
        title: const Text('Notifikasi'),
        actions: [
          if (belum > 0)
            TextButton.icon(
              icon: const Icon(Icons.done_all, size: 18),
              label: const Text('Tandai semua'),
              onPressed: notif.tandaiSemuaDibaca,
            ),
          const SizedBox(width: 4),
        ],
      ),
      body: daftar.isEmpty
          ? Center(
              child: Column(
                mainAxisSize: MainAxisSize.min,
                children: [
                  Icon(Icons.notifications_off_outlined,
                      size: 48, color: t.colorScheme.outline),
                  const SizedBox(height: AppSpacing.md),
                  Text('Belum ada notifikasi',
                      style: t.textTheme.bodyMedium),
                ],
              ),
            )
          : ListView.separated(
              padding: const EdgeInsets.all(AppSpacing.md),
              itemCount: daftar.length,
              separatorBuilder: (_, __) => const SizedBox(height: 8),
              itemBuilder: (c, i) {
                final n = daftar[i];
                return Dismissible(
                  key: ValueKey('notif_$i${n.judul}'),
                  direction: DismissDirection.endToStart,
                  background: Container(
                    alignment: Alignment.centerRight,
                    padding: const EdgeInsets.only(right: 16),
                    decoration: BoxDecoration(
                      color: Colors.red,
                      borderRadius: BorderRadius.circular(10),
                    ),
                    child: const Icon(Icons.delete, color: Colors.white),
                  ),
                  onDismissed: (_) => notif.hapus(i),
                  child: Card(
                    margin: EdgeInsets.zero,
                    child: InkWell(
                      borderRadius: BorderRadius.circular(10),
                      onTap: () => notif.tandaiDibaca(i),
                      child: Padding(
                        padding: const EdgeInsets.all(AppSpacing.md),
                        child: Row(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Container(
                              padding: const EdgeInsets.all(8),
                              decoration: BoxDecoration(
                                color: n.warna.withValues(alpha: 0.15),
                                shape: BoxShape.circle,
                              ),
                              child: Icon(n.ikon, size: 18, color: n.warna),
                            ),
                            const SizedBox(width: 12),
                            Expanded(
                              child: Column(
                                crossAxisAlignment: CrossAxisAlignment.start,
                                children: [
                                  Row(children: [
                                    Expanded(
                                      child: Text(
                                        n.judul,
                                        style: t.textTheme.titleSmall?.copyWith(
                                          fontWeight: n.dibaca
                                              ? FontWeight.normal
                                              : FontWeight.bold,
                                        ),
                                      ),
                                    ),
                                    if (!n.dibaca)
                                      Container(
                                        width: 8,
                                        height: 8,
                                        decoration: const BoxDecoration(
                                          color: Colors.green,
                                          shape: BoxShape.circle,
                                        ),
                                      ),
                                  ]),
                                  const SizedBox(height: 4),
                                  Text(n.isi, style: t.textTheme.bodySmall),
                                  const SizedBox(height: 6),
                                  Text(n.waktu,
                                      style: t.textTheme.bodySmall?.copyWith(
                                        color: t.colorScheme.outline,
                                        fontSize: 11,
                                      )),
                                ],
                              ),
                            ),
                          ],
                        ),
                      ),
                    ),
                  ),
                );
              },
            ),
    );
  }
}
