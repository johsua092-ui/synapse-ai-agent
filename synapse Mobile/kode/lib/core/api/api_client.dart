import 'dart:async';
import 'dart:convert';
import 'dart:io';
import 'package:http/http.dart' as http;
import 'api_config.dart';

/// Klien HTTP/streaming ke Synapse api_server (OpenAI-compatible).
class ApiClient {
  final ApiConfig cfg;
  ApiClient(this.cfg);

  Map<String, String> get _headers => {
        'Content-Type': 'application/json',
        if (cfg.apiKey.isNotEmpty) 'Authorization': 'Bearer ${cfg.apiKey}',
      };

  Uri _u(String path) =>
      Uri.parse('${cfg.baseUrl.replaceAll(RegExp(r"/+$"), "")}$path');

  Future<Map<String, dynamic>> health() async {
    final r = await http
        .get(_u('/health'), headers: _headers)
        .timeout(const Duration(seconds: 10));
    if (r.statusCode != 200) throw Exception('HTTP ${r.statusCode}');
    return jsonDecode(r.body) as Map<String, dynamic>;
  }

  Future<List<String>> daftarModel() async {
    final r = await http
        .get(_u('/v1/models'), headers: _headers)
        .timeout(const Duration(seconds: 15));
    if (r.statusCode != 200) throw Exception('HTTP ${r.statusCode}: ${r.body}');
    final d = jsonDecode(r.body) as Map<String, dynamic>;
    return ((d['data'] as List?) ?? const [])
        .map((e) => (e['id'] ?? '').toString())
        .where((s) => s.isNotEmpty)
        .toList();
  }

  Future<List<Map<String, dynamic>>> daftarSkill() async {
    final r = await http
        .get(_u('/v1/skills'), headers: _headers)
        .timeout(const Duration(seconds: 20));
    if (r.statusCode != 200) throw Exception('HTTP ${r.statusCode}');
    final d = jsonDecode(r.body) as Map<String, dynamic>;
    return ((d['data'] as List?) ?? const []).cast<Map<String, dynamic>>();
  }

  // ================= CHAT (teks) =================

  Future<String> chat(String pesan,
      {List<Map<String, dynamic>>? riwayat,
      Duration timeout = const Duration(seconds: 180)}) async {
    final r = await http
        .post(_u('/v1/chat/completions'),
            headers: _headers,
            body: jsonEncode({
              'model': cfg.model ?? 'synapse-agent',
              'messages': [
                ...?riwayat,
                {'role': 'user', 'content': pesan},
              ],
            }))
        .timeout(timeout);
    if (r.statusCode != 200) throw Exception('HTTP ${r.statusCode}: ${r.body}');
    final d = jsonDecode(r.body) as Map<String, dynamic>;
    return ((d['choices'] as List?)?.first?['message']?['content'] ?? '')
        .toString();
  }

  Stream<String> chatStream(String pesan,
          {List<Map<String, dynamic>>? riwayat}) =>
      _streamDari([
        ...?riwayat,
        {'role': 'user', 'content': pesan},
      ]);

  // ================= CHAT (gambar / multimodal) =================

  /// Kirim GAMBAR + teks (vision). File dibaca -> base64 data URL.
  Stream<String> chatGambar(File gambar, String teks,
      {List<Map<String, dynamic>>? riwayat}) async* {
    final bytes = await gambar.readAsBytes();
    final b64 = base64Encode(bytes);
    final nama = gambar.path.toLowerCase();
    final mime = nama.endsWith('.png')
        ? 'image/png'
        : nama.endsWith('.webp')
            ? 'image/webp'
            : 'image/jpeg';

    final isi = [
      if (teks.trim().isNotEmpty) {'type': 'text', 'text': teks.trim()},
      {
        'type': 'image_url',
        'image_url': {'url': 'data:$mime;base64,$b64'},
      },
    ];

    yield* _streamDari([
      ...?riwayat,
      {'role': 'user', 'content': isi},
    ]);
  }

  /// Kirim DOKUMEN sebagai teks (file dibaca -> disisipkan ke pesan).
  Stream<String> chatDokumen(File file, String teks) async* {
    String isi;
    try {
      isi = await file.readAsString();
    } catch (e) {
      throw Exception('File tidak bisa dibaca sebagai teks: $e');
    }
    const maks = 100000;
    if (isi.length > maks) {
      isi = '${isi.substring(0, maks)}\n\n[...dipotong]';
    }

    final namaFile = file.path.split(RegExp(r'[\\/]')).last;
    final perintah =
        teks.trim().isEmpty ? 'Baca dan rangkum dokumen ini.' : teks.trim();
    final pesan = '$perintah\n\n'
        '--- ISI FILE: $namaFile ---\n'
        '$isi\n'
        '--- AKHIR FILE ---';

    yield* _streamDari([
      {'role': 'user', 'content': pesan},
    ]);
  }

  // ================= STREAMING INTERNAL =================

  Stream<String> _streamDari(List<Map<String, dynamic>> messages) async* {
    final req = http.Request('POST', _u('/v1/chat/completions'));
    req.headers.addAll(_headers);
    req.body = jsonEncode({
      'model': cfg.model ?? 'synapse-agent',
      'stream': true,
      'messages': messages,
    });

    final resp = await req.send().timeout(const Duration(seconds: 120));
    if (resp.statusCode != 200) {
      final body = await resp.stream.bytesToString();
      throw Exception('HTTP ${resp.statusCode}: $body');
    }

    await for (final baris in resp.stream
        .transform(utf8.decoder)
        .transform(const LineSplitter())) {
      if (!baris.startsWith('data:')) continue;
      final data = baris.substring(5).trim();
      if (data == '[DONE]') break;
      try {
        final j = jsonDecode(data) as Map<String, dynamic>;
        final delta = (j['choices'] as List?)?.first?['delta'];
        final isi = (delta?['content'] ?? '').toString();
        if (isi.isNotEmpty) yield isi;
      } catch (_) {}
    }
  }

  /// Jalankan perintah lewat AGENT (install skill, akses perangkat, backup).
  ///
  /// [panjang] = true untuk operasi BERAT (backup/restore penuh) yang bisa
  /// makan beberapa menit. Tanpa ini, batas 180 detik membuat backup/restore
  /// selalu "TimeoutException" walau agent di laptop masih bekerja.
  Future<String> perintahAgent(String perintah, {bool panjang = false}) {
    final pesan =
        'Jalankan perintah ini di terminal host dan laporkan hasilnya:\n\n'
        '`$perintah`\n\n'
        'Balas singkat: berhasil/gagal + output penting.';
    // Operasi panjang: pakai jalur STREAMING (tanpa batas 180 detik) supaya
    // tidak kena timeout; hasil akhir = gabungan seluruh potongan teks.
    if (panjang) {
      return chatStream(pesan).join();
    }
    return chat(pesan);
  }
}
