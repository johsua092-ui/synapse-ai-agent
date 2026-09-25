import 'dart:async';
import 'dart:convert';
import 'package:flutter/services.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:http/http.dart' as http;
import '../api/api_config.dart';

/// Jembatan ke TaskService (Android foreground service) untuk notifikasi
/// latar belakang: user menutup app, tugas tetap dipantau, notif muncul saat selesai.
class TugasLatar {
  static const _kanal = MethodChannel('synapse/task');

  /// Kirim tugas ke api_server, lalu minta service memantau di latar belakang.
  /// Mengembalikan runId kalau berhasil.
  static Future<String?> mulai({
    required String input,
    required ApiConfig cfg,
    String? judul,
  }) async {
    final base = cfg.baseUrl.replaceAll(RegExp(r'/+$'), '');
    final headers = {
      'Content-Type': 'application/json',
      if (cfg.apiKey.isNotEmpty) 'Authorization': 'Bearer ${cfg.apiKey}',
    };

    // 1. jalankan tugas (POST /v1/runs)
    final r = await http
        .post(Uri.parse('$base/v1/runs'),
            headers: headers,
            body: jsonEncode({
              'input': input,
              if (cfg.model != null) 'model': cfg.model,
            }))
        .timeout(const Duration(seconds: 60));

    // api_server mengembalikan 200 ATAU 202 (Accepted) untuk tugas async
    if (r.statusCode != 200 && r.statusCode != 202) {
      throw Exception('HTTP ${r.statusCode}: ${r.body}');
    }
    final d = jsonDecode(r.body) as Map<String, dynamic>;
    final runId = (d['run_id'] ?? '').toString();
    if (runId.isEmpty) throw Exception('run_id tidak diterima dari server');

    // 2. minta service pantau di latar belakang
    await _kanal.invokeMethod('mulaiPantau', {
      'runId': runId,
      'baseUrl': base,
      'apiKey': cfg.apiKey,
      'judul': (judul == null || judul.trim().isEmpty)
          ? _ringkas(input)
          : judul.trim(),
    });

    return runId;
  }

  /// Hentikan pemantauan.
  static Future<void> hentikan() async {
    try {
      await _kanal.invokeMethod('hentikan');
    } catch (_) {}
  }

  /// Apakah izin notifikasi sudah diberikan?
  static Future<bool> izinNotifikasi() async {
    try {
      final v = await _kanal.invokeMethod<bool>('izinNotifikasi');
      return v ?? false;
    } catch (_) {
      return false;
    }
  }

  static String _ringkas(String s) {
    final t = s.trim().replaceAll(RegExp(r'\s+'), ' ');
    return t.length > 60 ? '${t.substring(0, 60)}...' : t;
  }
}

/// Provider sederhana untuk status izin notifikasi.
final izinNotifProvider = FutureProvider<bool>((ref) => TugasLatar.izinNotifikasi());
