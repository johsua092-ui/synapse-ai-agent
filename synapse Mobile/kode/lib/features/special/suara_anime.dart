import 'dart:convert';
import 'dart:io';
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

  /// Buat file suara anime lewat AGENT (edge-tts), lalu kembalikan path-nya.
  ///
  /// [klien] dipakai untuk mengirim perintah ke agent.
  static Future<String?> buatLewatAgent({
    required dynamic klien,
    required String teks,
    required String suara,
  }) async {
    try {
      final dir = await getTemporaryDirectory();
      final keluar = '${dir.path}/suara_vtuber.mp3';
      // hapus file lama supaya tidak memutar suara sebelumnya
      final f = File(keluar);
      if (await f.exists()) await f.delete();

      final aman = teks.replaceAll('"', "'").replaceAll('\n', ' ');
      final perintah =
          'Buat file suara dari teks berikut memakai edge-tts, lalu simpan ke '
          'path ini persis:\n'
          'FILE: $keluar\n'
          'VOICE: $suara\n'
          'TEKS: "$aman"\n\n'
          'Perintah: `python -m edge_tts --voice $suara --text "$aman" '
          '--write-media "$keluar"`\n'
          'Setelah selesai, pastikan file ada dan laporkan ukurannya saja '
          '(jangan tulis isi teksnya).';

      await klien.perintahAgent(perintah);

      // tunggu file muncul (maks 20 detik)
      for (var i = 0; i < 20; i++) {
        await Future.delayed(const Duration(milliseconds: 1000));
        if (await f.exists() && await f.length() > 1000) {
          return keluar;
        }
      }
      return null;
    } catch (_) {
      return null;
    }
  }

  /// Putar file mp3.
  static Future<void> putar(String path) async {
    try {
      await _pemutar.stop();
      await _pemutar.play(DeviceFileSource(path));
    } catch (_) {}
  }

  static Future<void> berhenti() async {
    try {
      await _pemutar.stop();
    } catch (_) {}
  }
}
