import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../core/theme/spacing.dart';

/// Update dari GitHub:
///  - Tombol "Cek Update" -> deteksi versi terbaru
///  - Kalau ADA update -> muncul tombol "Update Sekarang"
///  - Kalau TIDAK ada -> pesan "Sudah versi terbaru"
class UpdateScreen extends ConsumerStatefulWidget {
  const UpdateScreen({super.key});
  @override
  ConsumerState<UpdateScreen> createState() => _UpdateScreenState();
}

class _UpdateScreenState extends ConsumerState<UpdateScreen> {
  bool _cek = false;
  bool? _ada;
  String _versiSekarang = '0.1.0';
  String? _versiBaru;
  bool _mengunduh = false;
  double _progres = 0;

  Future<void> _cekUpdate() async {
    setState(() { _cek = true; _ada = null; });
    await Future.delayed(const Duration(seconds: 2)); // simulasi cek GitHub
    setState(() {
      _cek = false;
      _ada = false;          // ganti true kalau ada rilis baru
      _versiBaru = null;
    });
  }

  Future<void> _unduh() async {
    setState(() { _mengunduh = true; _progres = 0; });
    for (var i = 1; i <= 10; i++) {
      await Future.delayed(const Duration(milliseconds: 250));
      if (!mounted) return;
      setState(() => _progres = i / 10);
    }
    if (!mounted) return;
    setState(() => _mengunduh = false);
    ScaffoldMessenger.of(context).showSnackBar(
      const SnackBar(content: Text('Update selesai — restart aplikasi')),
    );
  }

  @override
  Widget build(BuildContext context) {
    final t = Theme.of(context);
    return Scaffold(
      appBar: AppBar(title: const Text('Update')),
      body: ListView(
      padding: const EdgeInsets.all(AppSpacing.md),
      children: [
        Text('Periksa versi terbaru dari GitHub.', style: t.textTheme.bodySmall),
        const SizedBox(height: AppSpacing.lg),

        Card(
          child: ListTile(
            leading: const Icon(Icons.system_update_alt),
            title: const Text('Versi terpasang'),
            trailing: Text(_versiSekarang, style: t.textTheme.titleSmall),
          ),
        ),
        const SizedBox(height: AppSpacing.lg),

        FilledButton.icon(
          onPressed: _cek ? null : _cekUpdate,
          icon: _cek
              ? const SizedBox(width: 16, height: 16, child: CircularProgressIndicator(strokeWidth: 2))
              : const Icon(Icons.refresh),
          label: Text(_cek ? 'Memeriksa...' : 'Cek Update'),
        ),

        if (_ada == false) ...[
          const SizedBox(height: AppSpacing.lg),
          Card(
            color: Colors.green.withValues(alpha: 0.12),
            child: const ListTile(
              leading: Icon(Icons.check_circle, color: Colors.green),
              title: Text('Sudah versi terbaru'),
              subtitle: Text('Tidak ada update tersedia.'),
            ),
          ),
        ],

        if (_ada == true) ...[
          const SizedBox(height: AppSpacing.lg),
          Card(
            color: Colors.orange.withValues(alpha: 0.12),
            child: ListTile(
              leading: const Icon(Icons.new_releases, color: Colors.orange),
              title: Text('Update tersedia: $_versiBaru'),
              subtitle: const Text('Versi baru dari GitHub siap diunduh.'),
            ),
          ),
          const SizedBox(height: AppSpacing.md),
          if (_mengunduh) ...[
            LinearProgressIndicator(value: _progres),
            const SizedBox(height: 6),
            Text('Mengunduh ${(_progres * 100).toStringAsFixed(0)}%',
                style: t.textTheme.bodySmall),
          ] else
            FilledButton.icon(
              onPressed: _unduh,
              icon: const Icon(Icons.download),
              label: const Text('Update Sekarang'),
            ),
        ],
      ],
      ),
    );
  }
}
