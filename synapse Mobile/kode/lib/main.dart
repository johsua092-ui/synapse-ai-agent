import 'dart:async';

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:package_info_plus/package_info_plus.dart';
import 'package:permission_handler/permission_handler.dart';

import 'app.dart';
import 'core/notif/notif_provider.dart';
import 'core/update/pengingat_update.dart';

/// Titik masuk aplikasi Synapse Mobile.
///
/// [SynapseApp] ada di `app.dart` (ConsumerWidget) supaya bisa
/// membaca pilihan tema (terang/gelap/sistem) dari Riverpod.
void main() {
  WidgetsFlutterBinding.ensureInitialized();

  // FIX v1.2.7 — PENGINGAT UPDATE OTOMATIS (2 LAPIS), lihat pengingat_update.dart
  unawaited(_aktifkanPengingatUpdate());

  runApp(const ProviderScope(child: SynapseApp()));
}

/// Aktifkan pengingat update:
///   LAPIS 1 — notifikasi SISTEM (AlarmManager, jalan walau app ditutup).
///   LAPIS 2 — cek versi sekarang juga, lalu isi LONCENG di dalam app.
Future<void> _aktifkanPengingatUpdate() async {
  try {
    // ---- IZIN NOTIFIKASI (WAJIB Android 13+) ----
    // Tanpa izin ini, notifikasi pengingat update TIDAK akan muncul.
    try {
      if (!await Permission.notification.isGranted) {
        await Permission.notification.request();
      }
    } catch (e) {
      debugPrint('Minta izin notifikasi gagal: $e');
    }

    // ---- LAPIS 1: daftarkan alarm + simpan versi terpasang ----
    final ok = await PengingatUpdate.mulaiSistem();

    // ---- LAPIS 2: cek versi -> isi lonceng di dalam app ----
    final sekarang = await PengingatUpdate.versiSekarang();
    final terbaru = await PengingatUpdate.versiTerbaru();
    if (terbaru != null && PengingatUpdate.banding(terbaru, sekarang) > 0) {
      _notifUpdateTersedia = terbaru;
      _versiSekarang = sekarang;
      debugPrint('Ada update: v$terbaru (sekarang v$sekarang)');
    } else {
      debugPrint('Sudah versi terbaru (v$sekarang)');
    }
    debugPrint('Pengingat sistem: ${ok ? "aktif" : "gagal"}');
  } catch (e) {
    debugPrint('Pengingat update gagal: $e');
  }
}

/// Dipakai [SynapseApp] untuk mengisi lonceng saat pertama dibuka.
/// (Sederhana: disimpan di variabel global supaya tidak perlu menunggu async.)
String? _notifUpdateTersedia;
String? _versiSekarang;

/// Dipanggil app.dart setelah provider siap.
void isiLoncengUpdate(WidgetRef ref) {
  final v = _notifUpdateTersedia;
  if (v != null) {
    ref.read(notifProvider.notifier).setUpdateTersedia(v, _versiSekarang ?? '?');
  } else {
    ref.read(notifProvider.notifier).hapusUpdate();
  }
}

/// Info versi untuk dipakai UI (opsional).
String? get versiUpdateTersedia => _notifUpdateTersedia;
