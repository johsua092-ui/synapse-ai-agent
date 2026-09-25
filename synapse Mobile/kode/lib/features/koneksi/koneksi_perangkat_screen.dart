import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../core/api/api_providers.dart';
import '../../core/koneksi/koneksi_perangkat.dart';
import '../../core/theme/spacing.dart';

/// M14 — Halaman terpisah: Koneksi AI Agent Synapse PC ke Mobile.
///
/// Dibuka dari tombol di bawah Base URL & API Key (halaman Koneksi AI).
/// User pilih mode -> pengaturannya BEDA per mode -> langsung diterapkan.
class KoneksiPerangkatScreen extends ConsumerStatefulWidget {
  const KoneksiPerangkatScreen({super.key});
  @override
  ConsumerState<KoneksiPerangkatScreen> createState() =>
      _KoneksiPerangkatScreenState();
}

class _KoneksiPerangkatScreenState
    extends ConsumerState<KoneksiPerangkatScreen> {
  final _ip = TextEditingController();
  bool _sibuk = false;
  String? _hasil;

  @override
  void initState() {
    super.initState();
    final st = ref.read(koneksiPerangkatProvider);
    if ((st.ipHp ?? '').isNotEmpty) _ip.text = st.ipHp!;
  }

  @override
  void dispose() {
    _ip.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final t = Theme.of(context);
    final st = ref.watch(koneksiPerangkatProvider);
    final notif = ref.read(koneksiPerangkatProvider.notifier);

    return Scaffold(
      appBar: AppBar(title: const Text('Koneksi Perangkat')),
      body: ListView(
        padding: const EdgeInsets.all(AppSpacing.md),
        children: [
          Text(
            'Sambungkan Synapse Mobile ke agent Synapse di laptop.',
            style: t.textTheme.bodySmall,
          ),
          const SizedBox(height: AppSpacing.md),

          // ===== PILIH MODE =====
          Text('Pilih cara menyambung', style: t.textTheme.titleSmall),
          const SizedBox(height: AppSpacing.sm),

          Row(children: [
            Expanded(
              child: _kartuMode(
                ikon: Icons.usb,
                label: 'Kabel (USB)',
                ket: 'Paling stabil',
                aktif: st.mode == ModeKoneksi.kabel,
                onTap: _sibuk ? null : () => notif.setMode(ModeKoneksi.kabel),
              ),
            ),
            const SizedBox(width: AppSpacing.sm),
            Expanded(
              child: _kartuMode(
                ikon: Icons.wifi,
                label: 'WiFi (nirkabel)',
                ket: 'Tanpa kabel',
                aktif: st.mode == ModeKoneksi.wifi,
                onTap: _sibuk ? null : () => notif.setMode(ModeKoneksi.wifi),
              ),
            ),
          ]),

          const SizedBox(height: AppSpacing.lg),

          // ===== PENGATURAN (BEDA per mode) =====
          Container(
            padding: const EdgeInsets.all(AppSpacing.md),
            decoration: BoxDecoration(
              color: t.colorScheme.surfaceContainerHighest,
              borderRadius: BorderRadius.circular(10),
            ),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Row(children: [
                  Icon(
                    st.mode == ModeKoneksi.kabel ? Icons.usb : Icons.wifi,
                    size: 18,
                    color: t.colorScheme.primary,
                  ),
                  const SizedBox(width: 8),
                  Text(
                    st.mode == ModeKoneksi.kabel
                        ? 'Pengaturan: Kabel (USB)'
                        : 'Pengaturan: WiFi (nirkabel)',
                    style: t.textTheme.titleSmall,
                  ),
                ]),
                const SizedBox(height: AppSpacing.sm),

                // --- isi pengaturan sesuai mode ---
                if (st.mode == ModeKoneksi.kabel) ...[
                  _langkah('1', 'Sambungkan kabel USB HP ke laptop'),
                  _langkah('2', 'Di HP, pilih mode "Transfer file (MTP)"'),
                  _langkah('3', 'Ketuk "Sambungkan" di bawah'),
                  const SizedBox(height: 6),
                  Text(
                    'Port 8642 (api_server) diteruskan otomatis lewat kabel. '
                    'Tidak perlu isi IP.',
                    style: t.textTheme.bodySmall,
                  ),
                ] else ...[
                  TextField(
                    controller: _ip,
                    keyboardType: TextInputType.number,
                    onChanged: (v) => notif.setIp(v.trim()),
                    decoration: const InputDecoration(
                      labelText: 'IP HP di WiFi',
                      hintText: '192.168.1.7',
                      helperText:
                          'Lihat di HP: Setelan > WiFi > jaringan > Detail',
                      border: OutlineInputBorder(),
                      isDense: true,
                    ),
                  ),
                  const SizedBox(height: AppSpacing.sm),
                  _langkah('1', 'HP & laptop di WiFi yang SAMA'),
                  _langkah('2', 'HP tersambung USB dulu (untuk aktifkan)'),
                  _langkah('3', 'Isi IP HP, lalu ketuk "Sambungkan"'),
                  const SizedBox(height: 6),
                  Text('Port otomatis: 5555',
                      style: t.textTheme.bodySmall),
                ],
              ],
            ),
          ),

          const SizedBox(height: AppSpacing.lg),

          // ===== TOMBOL AKSI =====
          Row(children: [
            Expanded(
              child: FilledButton.icon(
                onPressed: _sibuk ? null : _sambung,
                icon: _sibuk
                    ? const SizedBox(
                        width: 16, height: 16,
                        child: CircularProgressIndicator(strokeWidth: 2))
                    : const Icon(Icons.link),
                label: Text(_sibuk ? 'Menyambung...' : 'Sambungkan'),
              ),
            ),
            const SizedBox(width: AppSpacing.sm),
            OutlinedButton.icon(
              onPressed: _sibuk ? null : _putus,
              icon: const Icon(Icons.link_off),
              label: const Text('Putus'),
            ),
          ]),

          // ===== STATUS =====
          if (st.pesan != null) ...[
            const SizedBox(height: AppSpacing.md),
            Container(
              padding: const EdgeInsets.all(AppSpacing.md),
              decoration: BoxDecoration(
                color: (st.terhubung ? Colors.green : Colors.orange)
                    .withValues(alpha: 0.12),
                borderRadius: BorderRadius.circular(8),
              ),
              child: Row(children: [
                Icon(
                  st.terhubung ? Icons.check_circle : Icons.info_outline,
                  size: 18,
                  color: st.terhubung ? Colors.green : Colors.orange,
                ),
                const SizedBox(width: 8),
                Expanded(
                    child:
                        Text(st.pesan!, style: t.textTheme.bodySmall)),
              ]),
            ),
          ],

          // ===== HASIL =====
          if (_hasil != null) ...[
            const SizedBox(height: AppSpacing.md),
            Text('Hasil dari agent', style: t.textTheme.titleSmall),
            const SizedBox(height: AppSpacing.sm),
            Container(
              width: double.infinity,
              padding: const EdgeInsets.all(AppSpacing.md),
              decoration: BoxDecoration(
                color: t.colorScheme.surfaceContainerHighest,
                borderRadius: BorderRadius.circular(10),
              ),
              child: SelectableText(_hasil!, style: t.textTheme.bodySmall),
            ),
          ],
        ],
      ),
    );
  }

  Widget _kartuMode({
    required IconData ikon,
    required String label,
    required String ket,
    required bool aktif,
    required VoidCallback? onTap,
  }) {
    final t = Theme.of(context);
    return InkWell(
      borderRadius: BorderRadius.circular(12),
      onTap: onTap,
      child: Container(
        padding: const EdgeInsets.symmetric(vertical: 16, horizontal: 10),
        decoration: BoxDecoration(
          color: aktif
              ? t.colorScheme.primary.withValues(alpha: 0.12)
              : t.colorScheme.surfaceContainerHighest,
          borderRadius: BorderRadius.circular(12),
          border: Border.all(
            color: aktif ? t.colorScheme.primary : Colors.transparent,
            width: 2,
          ),
        ),
        child: Column(children: [
          Icon(ikon,
              size: 28,
              color: aktif ? t.colorScheme.primary : t.colorScheme.outline),
          const SizedBox(height: 6),
          Text(label,
              textAlign: TextAlign.center,
              style: t.textTheme.labelLarge?.copyWith(
                color: aktif ? t.colorScheme.primary : null,
                fontWeight: aktif ? FontWeight.w600 : null,
              )),
          Text(ket, style: t.textTheme.bodySmall),
          if (aktif) ...[
            const SizedBox(height: 4),
            Icon(Icons.check_circle,
                size: 16, color: t.colorScheme.primary),
          ],
        ]),
      ),
    );
  }

  Widget _langkah(String no, String teks) {
    final t = Theme.of(context);
    return Padding(
      padding: const EdgeInsets.only(bottom: 4),
      child: Row(crossAxisAlignment: CrossAxisAlignment.start, children: [
        Container(
          width: 18,
          height: 18,
          alignment: Alignment.center,
          decoration: BoxDecoration(
            color: t.colorScheme.primary.withValues(alpha: 0.15),
            shape: BoxShape.circle,
          ),
          child: Text(no,
              style: TextStyle(
                  fontSize: 11,
                  fontWeight: FontWeight.bold,
                  color: t.colorScheme.primary)),
        ),
        const SizedBox(width: 8),
        Expanded(child: Text(teks, style: t.textTheme.bodySmall)),
      ]),
    );
  }

  Future<void> _sambung() async {
    final klien = ref.read(apiClientProvider);
    if (klien == null) {
      setState(() => _hasil = 'Belum tersambung ke server. Isi Base URL + API Key dulu.');
      return;
    }
    setState(() {
      _sibuk = true;
      _hasil = null;
    });
    final notif = ref.read(koneksiPerangkatProvider.notifier);
    final h = await notif.sambung(klien, ip: _ip.text.trim());
    if (!mounted) return;
    setState(() {
      _hasil = h;
      _sibuk = false;
    });
  }

  Future<void> _putus() async {
    final klien = ref.read(apiClientProvider);
    if (klien == null) return;
    setState(() => _sibuk = true);
    final notif = ref.read(koneksiPerangkatProvider.notifier);
    final h = await notif.putus(klien);
    if (!mounted) return;
    setState(() {
      _hasil = h;
      _sibuk = false;
    });
  }
}
