import 'dart:async';
import 'dart:convert';
import 'package:flutter/services.dart';
import 'package:http/http.dart' as http;
import 'package:package_info_plus/package_info_plus.dart';
import 'package:shared_preferences/shared_preferences.dart';

/// FIX v1.2.7 — PENGINGAT UPDATE OTOMATIS (2 LAPIS) untuk tim/user.
///
/// PERMINTAAN USER (29 Sep 2026):
///   *"di hp mereka masing masing yang sudah menginstall 1.2.7 jika ada update
///    lagi di versi 1.2.8 mendatang di hp mereka ada notifikasi PERMANEN dari
///    Synapse Mobile ... meskipun user belum masuk ke apk"*
///   *"kalau udah di update ya udah gitu notifnya HILANG, tapi kalau ada update
///    langsung notifikasi MAJU di layar user"*
///   *"notifnya ada 2: selain di dalam lonceng dalam apk, juga di LUAR apk"*
///
/// DUA LAPIS NOTIFIKASI:
///   LAPIS 1 (LUAR APK / sistem Android): AlarmManager -> cek GitHub tiap 6 jam
///           -> notifikasi OS muncul walau app DITUTUP. Hilang otomatis setelah
///           user update ke versi terbaru.
///   LAPIS 2 (DALAM APK / lonceng): cek GitHub saat app dibuka -> tambah entri
///           di layar Notifikasi (badge lonceng). Hilang setelah update.
class PengingatUpdate {
  static const _kanal = MethodChannel('synapse/task');
  static const _kanalIntent = MethodChannel('synapse/intent');
  static const repo = 'johsua092-ui/synapse-ai-agent';

  /// FIX v1.2.7 — apakah app dibuka DARI notifikasi update?
  /// Kalau ya -> app langsung diarahkan ke menu Update (update cepat 1 ketuk).
  static Future<bool> dibukaDariNotifUpdate() async {
    try {
      final v = await _kanalIntent.invokeMethod<bool>('ambilBukaUpdate');
      return v ?? false;
    } catch (_) {
      return false;
    }
  }

  /// Versi terbaru dari GitHub (null kalau gagal / tidak ada rilis).
  static Future<String?> versiTerbaru() async {
    try {
      final r = await http.get(
        Uri.parse('https://api.github.com/repos/$repo/releases/latest'),
        headers: {'Accept': 'application/vnd.github+json'},
      ).timeout(const Duration(seconds: 20));
      if (r.statusCode != 200) return null;
      final d = jsonDecode(r.body) as Map<String, dynamic>;
      var tag = (d['tag_name'] ?? '').toString().trim();
      if (tag.isEmpty) return null;
      return tag.replaceFirst(RegExp(r'^[vV]'), '');
    } catch (_) {
      return null;
    }
  }

  /// Bandingkan versi semantik. >0 = a lebih baru dari b.
  static int banding(String a, String b) {
    List<int> p(String s) => s
        .split('.')
        .map((x) => int.tryParse(x.replaceAll(RegExp(r'[^0-9]'), '')) ?? 0)
        .toList();
    final pa = p(a), pb = p(b);
    final n = pa.length > pb.length ? pa.length : pb.length;
    for (var i = 0; i < n; i++) {
      final x = i < pa.length ? pa[i] : 0;
      final y = i < pb.length ? pb[i] : 0;
      if (x != y) return x - y;
    }
    return 0;
  }

  /// Versi yang terpasang sekarang (mis. "1.2.7").
  static Future<String> versiSekarang() async {
    try {
      final info = await PackageInfo.fromPlatform();
      return info.version;
    } catch (_) {
      return '0.0.0';
    }
  }

  /// Mulai pengingat LAPIS 1 (notifikasi sistem, jalan walau app ditutup).
  /// Aman dipanggil setiap app dibuka (idempoten).
  static Future<bool> mulaiSistem() async {
    try {
      final v = await versiSekarang();
      final ok = await _kanal.invokeMethod<bool>('mulaiPengingatUpdate', {
        'repo': repo,
        'versi': v,
      });
      final p = await SharedPreferences.getInstance();
      await p.setString('synapse_versi_terpasang', v);
      return ok ?? false;
    } catch (_) {
      return false;
    }
  }

  /// Hentikan pengingat LAPIS 1 + hapus notifikasi update.
  static Future<void> hentikanSistem() async {
    try {
      await _kanal.invokeMethod('hentikanPengingatUpdate');
    } catch (_) {}
  }
}
