import 'package:flutter/material.dart';

import '../../core/layout/breakpoints.dart';
import '../../core/theme/spacing.dart';
import '../../core/widgets/list_row.dart';

/// Status sistem + BUKTI 2 MODE (menampilkan orientasi & rasio layar).
class StatusScreen extends StatelessWidget {
  const StatusScreen({super.key});

  @override
  Widget build(BuildContext context) {
    final size = MediaQuery.of(context).size;
    final dpr = MediaQuery.of(context).devicePixelRatio;
    final land = Breakpoints.isLandscape(context);
    final two = Breakpoints.useTwoPane(context);

    return Scaffold(
      appBar: AppBar(title: const Text('Status')),
      body: ListView(
        children: [
          ListRow(title: 'Orientasi', subtitle: land ? 'Landscape (16:9)' : 'Potrait (9:16)'),
          ListRow(title: 'Rasio layar', subtitle: Breakpoints.ratioLabel(context)),
          ListRow(title: 'Ukuran logis', subtitle: '${size.width.toStringAsFixed(0)} x ${size.height.toStringAsFixed(0)} dp'),
          ListRow(title: 'Ukuran fisik', subtitle: '${(size.width * dpr).toStringAsFixed(0)} x ${(size.height * dpr).toStringAsFixed(0)} px'),
          ListRow(title: 'Tata letak', subtitle: two ? '2 kolom (navigasi samping)' : '1 kolom (navigasi bawah)'),
          const Divider(),
          const ListRow(title: 'Koneksi', subtitle: 'Lihat indikator di layar Chat (hijau = tersambung)'),
          const ListRow(title: 'Versi aplikasi', subtitle: '0.2.0 (M4 — chat + fitur lengkap)'),
          const SizedBox(height: AppSpacing.lg),
        ],
      ),
    );
  }
}
