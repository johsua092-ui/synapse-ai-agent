import 'dart:convert';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:shared_preferences/shared_preferences.dart';
import '../api/api_client.dart';
import '../api/api_config.dart';

/// M14 — Mode koneksi HP <-> Agent Synapse (PC).
enum ModeKoneksi {
  kabel,   // USB (adb reverse) — paling stabil
  wifi,    // WiFi sama (adb connect) — tanpa kabel
}

extension ModeKoneksiLabel on ModeKoneksi {
  String get label => this == ModeKoneksi.kabel ? 'Kabel (USB)' : 'WiFi (nirkabel)';
  String get id => this == ModeKoneksi.kabel ? 'kabel' : 'wifi';
}

/// Status koneksi perangkat.
class StatusKoneksi {
  final ModeKoneksi mode;
  final String? ipHp;        // untuk WiFi
  final bool terhubung;
  final String? pesan;
  const StatusKoneksi({
    this.mode = ModeKoneksi.kabel,
    this.ipHp,
    this.terhubung = false,
    this.pesan,
  });

  StatusKoneksi copyWith({
    ModeKoneksi? mode,
    String? ipHp,
    bool? terhubung,
    String? pesan,
  }) =>
      StatusKoneksi(
        mode: mode ?? this.mode,
        ipHp: ipHp ?? this.ipHp,
        terhubung: terhubung ?? this.terhubung,
        pesan: pesan ?? this.pesan,
      );
}

/// Pengelola koneksi perangkat (kabel / WiFi).
///
/// CARA KERJA:
///   - Kabel : agent jalankan `adb reverse tcp:8642 tcp:8642`
///             (HP akses laptop lewat 127.0.0.1:8642)
///   - WiFi  : agent jalankan `adb tcpip 5555` + `adb connect <ip>:5555`
///             + `adb -s <ip>:5555 reverse tcp:8642 tcp:8642`
class KoneksiPerangkatNotifier extends StateNotifier<StatusKoneksi> {
  KoneksiPerangkatNotifier() : super(const StatusKoneksi()) {
    _muat();
  }

  static const _kMode = 'koneksi_mode';
  static const _kIp = 'koneksi_ip_hp';

  Future<void> _muat() async {
    final p = await SharedPreferences.getInstance();
    final m = p.getString(_kMode);
    state = state.copyWith(
      mode: m == 'wifi' ? ModeKoneksi.wifi : ModeKoneksi.kabel,
      ipHp: p.getString(_kIp),
    );
  }

  Future<void> setMode(ModeKoneksi m) async {
    final p = await SharedPreferences.getInstance();
    await p.setString(_kMode, m.id);
    state = state.copyWith(mode: m, pesan: null);
  }

  Future<void> setIp(String ip) async {
    final p = await SharedPreferences.getInstance();
    await p.setString(_kIp, ip);
    state = state.copyWith(ipHp: ip);
  }

  /// Aktifkan koneksi sesuai mode.
  /// [klien] dipakai untuk mengirim perintah ke agent.
  /// Mengembalikan pesan hasil.
  Future<String> sambung(ApiClient klien, {String? ip}) async {
    state = state.copyWith(pesan: 'Menghubungkan...');
    try {
      final String perintah;
      if (state.mode == ModeKoneksi.kabel) {
        perintah =
            'Siapkan koneksi HP <-> laptop lewat KABEL USB untuk Synapse Mobile:\n'
            '1. `adb devices -l` — pastikan HP terdeteksi\n'
            '2. `adb reverse tcp:8642 tcp:8642` — teruskan port api_server\n'
            '3. `adb reverse --list` — verifikasi\n'
            'Laporkan hasilnya singkat.';
      } else {
        final alamat = (ip ?? state.ipHp ?? '').trim();
        if (alamat.isEmpty) {
          state = state.copyWith(
              pesan: 'Isi IP HP dulu (lihat Setelan > WiFi > Detail).');
          return state.pesan!;
        }
        perintah =
            'Siapkan koneksi HP <-> laptop lewat WIFI untuk Synapse Mobile.\n'
            'IP HP: $alamat, port 5555.\n'
            'Langkah:\n'
            '1. `adb devices -l` — pastikan HP terdeteksi (USB dulu)\n'
            '2. `adb tcpip 5555` — aktifkan mode WiFi\n'
            '3. tunggu 3 detik\n'
            '4. `adb connect $alamat:5555`\n'
            '5. `adb -s $alamat:5555 reverse tcp:8642 tcp:8642`\n'
            '6. `adb devices -l` — verifikasi muncul IP:5555\n'
            'PENTING: kalau ada lebih dari satu device, WAJIB pakai -s <serial>.\n'
            'Laporkan hasilnya singkat.';
      }

      final hasil = await klien.perintahAgent(perintah);
      final sukses = !hasil.toLowerCase().contains('gagal') &&
          !hasil.toLowerCase().contains('error') &&
          !hasil.toLowerCase().contains('tidak ditemukan');
      state = state.copyWith(
        terhubung: sukses,
        pesan: sukses ? 'Terhubung (${state.mode.label}).' : hasil,
      );
      return hasil;
    } catch (e) {
      state = state.copyWith(terhubung: false, pesan: 'Gagal: $e');
      return 'Gagal: $e';
    }
  }

  /// Putuskan koneksi.
  Future<String> putus(ApiClient klien) async {
    try {
      final perintah = state.mode == ModeKoneksi.wifi
          ? 'Putuskan koneksi WiFi ADB ke HP saya: `adb disconnect` lalu '
              '`adb usb`, dan laporkan hasilnya.'
          : 'Putuskan penerusan port ADB: `adb reverse --remove-all`, '
              'dan laporkan hasilnya.';
      final hasil = await klien.perintahAgent(perintah);
      state = state.copyWith(terhubung: false, pesan: 'Terputus.');
      return hasil;
    } catch (e) {
      return 'Gagal: $e';
    }
  }
}

final koneksiPerangkatProvider =
    StateNotifierProvider<KoneksiPerangkatNotifier, StatusKoneksi>(
        (ref) => KoneksiPerangkatNotifier());

/// Provider bantu: apakah konfigurasi AI sudah terisi.
final siapKoneksiProvider = Provider<bool>((ref) {
  final cfg = ref.watch(apiConfigProvider);
  return cfg.terisi;
});
