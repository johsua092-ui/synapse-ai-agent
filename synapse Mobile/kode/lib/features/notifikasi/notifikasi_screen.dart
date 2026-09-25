import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../core/theme/spacing.dart';

/// Notifikasi — design kartu berwarna per jenis, dengan ikon & waktu.
class NotifikasiScreen extends ConsumerStatefulWidget {
  const NotifikasiScreen({super.key});
  @override
  ConsumerState<NotifikasiScreen> createState() => _NotifikasiScreenState();
}

class _Notif {
  final String judul, isi, waktu;
  final IconData ikon;
  final Color warna;
  bool dibaca;
  _Notif({
    required this.judul,
    required this.isi,
    required this.waktu,
    required this.ikon,
    required this.warna,
    this.dibaca = false,
  });
}

class _NotifikasiScreenState extends ConsumerState<NotifikasiScreen> {
  final List<_Notif> _daftar = [
    _Notif(
      judul: 'Synapse siap',
      isi: 'Agent berjalan normal. Klik untuk mulai percakapan.',
      waktu: 'baru saja',
      ikon: Icons.check_circle,
      warna: Colors.green,
    ),
    _Notif(
      judul: 'API server aktif',
      isi: 'Terhubung di port 8642. Semua fitur siap dipakai.',
      waktu: '2 menit lalu',
      ikon: Icons.cloud_done,
      warna: Colors.blue,
    ),
    _Notif(
      judul: '143 skill tersedia',
      isi: 'Buka tab Skills untuk melihat & memasang skill baru.',
      waktu: '5 menit lalu',
      ikon: Icons.extension,
      warna: Colors.purple,
    ),
  ];

  int get _belumDibaca => _daftar.where((n) => !n.dibaca).length;

  @override
  Widget build(BuildContext context) {
    final t = Theme.of(context);
    return Scaffold(
      appBar: AppBar(
        title: const Text('Notifikasi'),
        actions: [
          if (_belumDibaca > 0)
            Padding(
              padding: const EdgeInsets.only(right: 8),
              child: Center(
                child: Chip(
                  label: Text('$_belumDibaca baru'),
                  backgroundColor: t.colorScheme.primaryContainer,
                  labelStyle: TextStyle(color: t.colorScheme.onPrimaryContainer),
                ),
              ),
            ),
          IconButton(
            tooltip: 'Tandai semua dibaca',
            icon: const Icon(Icons.done_all),
            onPressed: () => setState(() {
              for (final n in _daftar) { n.dibaca = true; }
            }),
          ),
        ],
      ),
      body: _daftar.isEmpty
          ? Center(
              child: Column(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  Icon(Icons.notifications_none, size: 48, color: t.colorScheme.outline),
                  const SizedBox(height: AppSpacing.md),
                  Text('Belum ada notifikasi', style: t.textTheme.bodyMedium),
                ],
              ),
            )
          : ListView.separated(
              padding: const EdgeInsets.all(AppSpacing.md),
              itemCount: _daftar.length,
              separatorBuilder: (_, __) => const SizedBox(height: AppSpacing.sm),
              itemBuilder: (c, i) {
                final n = _daftar[i];
                return Dismissible(
                  key: ValueKey('notif_$i'),
                  direction: DismissDirection.endToStart,
                  onDismissed: (_) => setState(() => _daftar.removeAt(i)),
                  background: Container(
                    alignment: Alignment.centerRight,
                    padding: const EdgeInsets.only(right: 20),
                    decoration: BoxDecoration(
                      color: Colors.red.withValues(alpha: 0.85),
                      borderRadius: BorderRadius.circular(12),
                    ),
                    child: const Icon(Icons.delete, color: Colors.white),
                  ),
                  child: Material(
                    color: n.dibaca
                        ? t.colorScheme.surfaceContainerHighest
                        : n.warna.withValues(alpha: 0.10),
                    borderRadius: BorderRadius.circular(12),
                    child: InkWell(
                      borderRadius: BorderRadius.circular(12),
                      onTap: () => setState(() => n.dibaca = true),
                      child: Padding(
                        padding: const EdgeInsets.all(AppSpacing.md),
                        child: Row(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            // ikon berwarna bulat
                            Container(
                              width: 40, height: 40,
                              decoration: BoxDecoration(
                                color: n.warna.withValues(alpha: 0.18),
                                shape: BoxShape.circle,
                              ),
                              child: Icon(n.ikon, color: n.warna, size: 22),
                            ),
                            const SizedBox(width: AppSpacing.md),
                            Expanded(
                              child: Column(
                                crossAxisAlignment: CrossAxisAlignment.start,
                                children: [
                                  Row(children: [
                                    Expanded(
                                      child: Text(n.judul,
                                          style: t.textTheme.titleSmall?.copyWith(
                                            fontWeight: n.dibaca
                                                ? FontWeight.normal
                                                : FontWeight.w700,
                                          )),
                                    ),
                                    Text(n.waktu, style: t.textTheme.bodySmall),
                                  ]),
                                  const SizedBox(height: 4),
                                  Text(n.isi, style: t.textTheme.bodySmall),
                                ],
                              ),
                            ),
                            if (!n.dibaca)
                              Container(
                                width: 8, height: 8,
                                margin: const EdgeInsets.only(left: 8, top: 6),
                                decoration: BoxDecoration(
                                  color: n.warna, shape: BoxShape.circle),
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
