import 'dart:convert';
import 'dart:io';
import 'dart:typed_data';
import 'package:audioplayers/audioplayers.dart';
import 'package:flutter/services.dart' show rootBundle;
import 'package:path_provider/path_provider.dart';

/// Layanan suara anime per karakter.
///
/// DUA CARA (otomatis pilih yang terbaik):
///   1. UTAMA — suara anime ASLI via agent (edge-tts di laptop):
///      app minta agent membuat file .mp3 dengan suara karakter, lalu diputar.
///      Hasil: suara anime asli, BEDA tiap karakter.
///   2. CADANGAN — TTS bawaan HP (flutter_tts) kalau agent tidak siap.
///
/// Suara per karakter (8 berbeda, sudah diuji):
///   Hiyori -> ja-JP-NanamiNeural      (Jepang, cewek ceria)
///   Haru   -> zh-CN-XiaoyiNeural      (Cina, cewek manis)
///   Mao    -> zh-CN-XiaoxiaoNeural    (Cina, cewek lembut)
///   Natori -> zh-TW-HsiaoChenNeural   (Taiwan, cewek kalem)
///   Rice   -> zh-CN-shaanxi-XiaoniNeural (Cina, anak kecil)
///   Mark   -> ja-JP-KeitaNeural       (Jepang, cowok santai)
///   Ren    -> zh-CN-YunjianNeural     (Cina, cowok tegas)
///   Wanko  -> ko-KR-HyunsuMultilingualNeural (Korea, maskot)
class SuaraAnime {
  static final _pemutar = AudioPlayer();

  /// Ambil daftar opsi suara untuk satu karakter.
  static Future<List<Map<String, dynamic>>> untuk(String karakter) async {
    try {
      final raw = await rootBundle.loadString('assets/suara_karakter.json');
      final d = jsonDecode(raw) as Map<String, dynamic>;
      final s = (d['suara'] as Map?) ?? const {};
      final info = s[karakter] as Map?;
      if (info == null) return [];
      final opsi = (info['opsi'] as List?) ?? const [];
      return opsi.map((e) => Map<String, dynamic>.from(e as Map)).toList();
    } catch (_) {
      return [];
    }
  }

  /// Suara default untuk karakter.
  static Future<String?> defaultUntuk(String karakter) async {
    try {
      final raw = await rootBundle.loadString('assets/suara_karakter.json');
      final d = jsonDecode(raw) as Map<String, dynamic>;
      final s = (d['suara'] as Map?) ?? const {};
      final info = s[karakter] as Map?;
      return info?['suara'] as String?;
    } catch (_) {
      return null;
    }
  }

  /// Buat & putar suara anime lewat ENDPOINT SERVER (`/v1/tts`).
  ///
  /// JEBAKAN #119 (v1.2.6) — CARA YANG BENAR:
  /// Server menjalankan edge-tts LANGSUNG (tanpa LLM) -> cepat (~2 detik) &
  /// andal. Dulu lewat agent (LLM) -> 10-40 detik & sering gagal.
  ///
  /// Mengembalikan path file mp3 di HP, atau null kalau gagal.
  static Future<String?> buatLewatServer({
    required dynamic klien,
    required String teks,
    required String suara,
  }) async {
    try {
      final bytes = await klien.tts(teks, suara);
      if (bytes == null || bytes.isEmpty) return null;
      final dir = await getTemporaryDirectory();
      final keluar = '${dir.path}/suara_vtuber.mp3';
      await File(keluar).writeAsBytes(bytes);
      return keluar;
    } catch (_) {
      return null;
    }
  }

  /// Putar file mp3.
  ///
  /// JEBAKAN #118 (v1.2.6): file berada di storage HP
  /// (`/sdcard/Android/data/<pkg>/files/...`). Di Android modern jalur ini
  /// TIDAK bisa dibaca langsung dengan path mentah -> gunakan
  /// `UrlSource('file://...')`.
  static Future<void> putar(String path) async {
    try {
      await _pemutar.stop();
      final url = path.startsWith('file://') ? path : 'file://$path';
      await _pemutar.play(UrlSource(url));
    } catch (_) {
      // cadangan: coba sebagai file biasa
      try {
        await _pemutar.play(DeviceFileSource(path));
      } catch (_) {}
    }
  }

  static Future<void> berhenti() async {
    try {
      await _pemutar.stop();
    } catch (_) {}
  }
}
