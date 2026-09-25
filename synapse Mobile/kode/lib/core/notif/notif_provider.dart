import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

/// Satu notifikasi.
class NotifItem {
  final String judul;
  final String isi;
  final String waktu;
  final IconData ikon;
  final Color warna;
  bool dibaca;

  NotifItem({
    required this.judul,
    required this.isi,
    required this.waktu,
    required this.ikon,
    required this.warna,
    this.dibaca = false,
  });
}

/// Provider notifikasi bersama.
///
/// Dipakai oleh:
///   - Badge lonceng di pojok kanan atas (jumlah belum dibaca)
///   - Layar Notifikasi (daftar lengkap)
///
/// Jadi saat user menandai "sudah dibaca", badge langsung ikut berubah.
class NotifNotifier extends StateNotifier<List<NotifItem>> {
  NotifNotifier()
      : super([
          NotifItem(
            judul: 'Synapse Mobile siap',
            isi: 'Semua fitur aktif. Isi Base URL + API Key untuk mulai.',
            waktu: 'baru saja',
            ikon: Icons.check_circle,
            warna: Colors.green,
          ),
          NotifItem(
            judul: 'Katalog skill tersedia',
            isi: '143 skill siap dipasang. Buka tab Skills untuk melihat.',
            waktu: '1 menit lalu',
            ikon: Icons.extension,
            warna: Colors.blue,
          ),
          NotifItem(
            judul: 'Mode Otonom',
            isi: 'Agent bisa melihat layar HP dan mengetuk sendiri. Coba di '
                'Setelan > Akses Perangkat > ikon Otonom.',
            waktu: '2 menit lalu',
            ikon: Icons.auto_awesome,
            warna: Colors.purple,
          ),
          NotifItem(
            judul: 'Koneksi Perangkat',
            isi: 'Sambungkan lewat Kabel atau WiFi di Setelan > Koneksi AI.',
            waktu: '5 menit lalu',
            ikon: Icons.usb,
            warna: Colors.orange,
          ),
        ]);

  /// Jumlah yang belum dibaca.
  int get belumDibaca => state.where((n) => !n.dibaca).length;

  void tandaiDibaca(int i) {
    if (i < 0 || i >= state.length) return;
    state = [
      for (var j = 0; j < state.length; j++)
        state[j]..dibaca = (j == i ? true : state[j].dibaca),
    ];
  }

  void tandaiSemuaDibaca() {
    state = [for (final n in state) n..dibaca = true];
  }

  void hapus(int i) {
    if (i < 0 || i >= state.length) return;
    state = [...state]..removeAt(i);
  }

  /// Tambah notifikasi baru (mis. saat tugas selesai).
  void tambah({
    required String judul,
    required String isi,
    IconData ikon = Icons.notifications,
    Color warna = Colors.blue,
  }) {
    state = [
      NotifItem(
        judul: judul,
        isi: isi,
        waktu: 'baru saja',
        ikon: ikon,
        warna: warna,
      ),
      ...state,
    ];
  }
}

final notifProvider =
    StateNotifierProvider<NotifNotifier, List<NotifItem>>((ref) => NotifNotifier());
