import 'dart:async';
import 'dart:convert';
import 'dart:io';
import 'dart:typed_data';
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

  /// Susun URL dengan BENAR — tahan terhadap Base URL yang sudah berakhiran
  /// `/v1`.
  ///
  /// JEBAKAN (v1.2.3): kalau user mengisi Base URL `https://host/v1` lalu kita
  /// tempel `/v1/models`, hasilnya `https://host/v1/v1/models` -> HTTP 404.
  Uri _u(String path) {
    final base = cfg.baseUrl.trim().replaceAll(RegExp(r"/+$"), "");
    var p = path;
    if (base.endsWith('/v1') && p.startsWith('/v1/')) {
      p = p.substring(3); // buang '/v1' supaya tidak dobel
    }
    return Uri.parse('$base$p');
  }

  /// Cek koneksi — TOLERAN.
  ///
  /// Router kustom (mis. 9router) TIDAK punya `/health` khas Synapse. Dulu ini
  /// melempar HTTP 404 sehingga DETEKSI MODEL GAGAL walau `/v1/models`
  /// sebenarnya jalan. Sekarang: kembalikan `null` (bukan error) kalau server
  /// tidak punya endpoint health.
  Future<Map<String, dynamic>?> health() async {
    for (final p in const ['/health', '/v1/health']) {
      try {
        final r = await http
            .get(_u(p), headers: _headers)
            .timeout(const Duration(seconds: 10));
        if (r.statusCode == 200) {
          try {
            return jsonDecode(r.body) as Map<String, dynamic>;
          } catch (_) {
            return <String, dynamic>{};
          }
        }
      } catch (_) {}
    }
    return null; // tidak ada /health -> BUKAN kegagalan
  }

  /// Ambil daftar model — TOLERAN terhadap berbagai bentuk respons:
  /// `{data:[{id}]}` (OpenAI) maupun `{models:[...]}`.
  ///
  /// JEBAKAN (v1.2.3): dulu hanya coba `/v1/models`. Kalau base sudah berakhir
  /// `/v1` -> jadi `/v1/v1/models` -> 404. Sekarang dicoba `/v1/models` dulu,
  /// lalu `/models`, dan pesan galat menampilkan URL yang benar-benar dicoba.
  Future<List<String>> daftarModel() async {
    final dicoba = <String>[];
    String? galat;
    for (final p in const ['/v1/models', '/models']) {
      final u = _u(p);
      dicoba.add(u.toString());
      try {
        final r = await http
            .get(u, headers: _headers)
            .timeout(const Duration(seconds: 20));
        if (r.statusCode != 200) {
          if (r.statusCode == 401 || r.statusCode == 403) {
            galat = 'HTTP ${r.statusCode} — API Key DITOLAK.\n'
                'Pastikan kunci SAMA dengan yang dipakai Synapse CLI, '
                'dan diizinkan untuk akses remote.';
          } else if (r.statusCode == 404) {
            galat = 'HTTP 404 — endpoint /v1/models tidak ada di server ini.';
          } else {
            galat = 'HTTP ${r.statusCode}';
          }
          continue;
        }
        final d = jsonDecode(r.body) as Map<String, dynamic>;
        final list = (d['data'] ?? d['models']) as List?;
        final hasil = (list ?? const [])
            .map((e) => e is Map
                ? (e['id'] ?? e['name'] ?? '').toString()
                : e.toString())
            .where((s) => s.isNotEmpty)
            .toList();
        if (hasil.isNotEmpty) return hasil;
        galat = 'respons tidak memuat daftar model';
      } catch (e) {
        galat = e.toString();
      }
    }
    throw Exception('${galat ?? "gagal"}\nURL dicoba:\n  ${dicoba.join("\n  ")}');
  }

  Future<List<Map<String, dynamic>>> daftarSkill() async {
    final r = await http
        .get(_u('/v1/skills'), headers: _headers)
        .timeout(const Duration(seconds: 20));
    if (r.statusCode != 200) throw Exception('HTTP ${r.statusCode}');
    final d = jsonDecode(r.body) as Map<String, dynamic>;
    return ((d['data'] as List?) ?? const []).cast<Map<String, dynamic>>();
  }

  // ================= TTS (suara) =================

  /// Buat suara (mp3) dari teks lewat endpoint server `/v1/tts`.
  ///
  /// JEBAKAN #119 (v1.2.6): dulu app menyuruh AGENT (LLM) menjalankan edge-tts
  /// -> lambat (10-40s) & sering gagal. Sekarang server yang menjalankan
  /// edge-tts LANGSUNG (tanpa LLM) -> cepat (~2 detik) & andal.
  /// Mengembalikan bytes mp3, atau null kalau gagal.
  Future<Uint8List?> tts(String teks, String suara) async {
    try {
      final r = await http
          .post(
            _u('/v1/tts'),
            headers: _headers,
            body: jsonEncode({'text': teks, 'voice': suara}),
          )
          .timeout(const Duration(seconds: 60));
      if (r.statusCode != 200) return null;
      return r.bodyBytes;
    } catch (_) {
      return null;
    }
  }

  // ================= VALIDASI KONFIGURASI =================

  /// Periksa konfigurasi 100%: apakah benar-benar bisa dipakai untuk CHAT.
  ///
  /// Mengembalikan daftar masalah (kosong = valid). Tiap masalah berisi
  /// [judul] singkat + [saran] perbaikan, supaya user tahu APA yang salah
  /// dan APA yang kurang — bukan sekadar "gagal".
  ///
  /// CEPAT (v1.2.6): hanya SATU permintaan HTTP (bukan dua berurutan), dan
  /// timeout dipendekkan supaya kegagalan tidak menggantung lama.
  /// (Server lokal biasanya hanya butuh ~0,01 detik.)
  Future<List<Map<String, String>>> validasi() async {
    final masalah = <Map<String, String>>[];

    // 1. Base URL
    final base = cfg.baseUrl.trim();
    if (base.isEmpty) {
      masalah.add({
        'judul': 'Base URL kosong',
        'saran': 'Isi alamat server, mis. http://127.0.0.1:8642/v1',
      });
    } else {
      final u = Uri.tryParse(base);
      if (u == null || !u.hasScheme || u.host.isEmpty) {
        masalah.add({
          'judul': 'Base URL tidak valid: $base',
          'saran': 'Harus lengkap dengan http:// atau https:// dan nama host',
        });
      }
    }

    // 2. API Key
    if (cfg.apiKey.trim().isEmpty) {
      masalah.add({
        'judul': 'API Key kosong',
        'saran': 'Isi API Key dari server (API_SERVER_KEY)',
      });
    }

    // 3. Model
    if ((cfg.model ?? '').trim().isEmpty) {
      masalah.add({
        'judul': 'Model belum dipilih',
        'saran': 'Tekan "Deteksi Model" lalu pilih model',
      });
    }

    // Masalah dasar sudah ada -> tidak perlu tanya server (langsung cepat).
    if (masalah.isNotEmpty) return masalah;

    // 4. Server benar-benar bisa dihubungi? -> SATU permintaan saja.
    //    (Dulu: /v1/models lalu /models = 2 permintaan berurutan -> lambat.)
    final u = _u('/v1/models');
    try {
      final r = await http
          .get(u, headers: _headers)
          .timeout(const Duration(seconds: 8)); // dipendekkan dari 15s
      if (r.statusCode == 200) return masalah; // VALID
      if (r.statusCode == 401 || r.statusCode == 403) {
        masalah.add({
          'judul': 'API Key DITOLAK (HTTP ${r.statusCode})',
          'saran': 'Kunci tidak diizinkan server ini. Pastikan kunci sama '
              'dengan yang dipakai Synapse CLI dan diizinkan akses remote.',
        });
      } else if (r.statusCode == 404) {
        masalah.add({
          'judul': 'Endpoint tidak ditemukan (HTTP 404)',
          'saran': 'Base URL salah. Contoh benar: http://127.0.0.1:8642/v1',
        });
      } else {
        masalah.add({
          'judul': 'Server balas HTTP ${r.statusCode}',
          'saran': 'Periksa Base URL dan status server',
        });
      }
    } catch (e) {
      masalah.add({
        'judul': 'Tidak bisa menghubungi server',
        'saran': 'Cek: (1) server hidup? (2) HP & server sejaringan? '
            '(3) sudah "adb reverse tcp:8642 tcp:8642" kalau lewat USB? '
            '(4) Base URL benar?\n\nURL dicoba: $u',
      });
    }
    return masalah;
  }

  /// Daftar TOOLSET (kemampuan agent) dari `/v1/toolsets`.
  /// Permintaan tim v1.2.4: "sediain tools nya dong minimal kaya yang di cli".
  /// Server Synapse punya ~28 toolset (web, browser, terminal, file, dll).
  Future<List<Map<String, dynamic>>> toolsets() async {
    final r = await http
        .get(_u('/v1/toolsets'), headers: _headers)
        .timeout(const Duration(seconds: 20));
    if (r.statusCode != 200) throw Exception('HTTP ${r.statusCode}');
    final d = jsonDecode(r.body) as Map<String, dynamic>;
    return ((d['data'] as List?) ?? const [])
        .map((e) => Map<String, dynamic>.from(e as Map))
        .toList();
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
          {List<Map<String, dynamic>>? riwayat, String? model}) =>
      _streamDari([
        ...?riwayat,
        {'role': 'user', 'content': pesan},
      ], model: model);

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

    // JEBAKAN #99 (v1.2.6): dulu kirim gambar memakai cfg.model (model chat),
    // sehingga pilihan "Model vision" di Setelan TIDAK dipakai — dan kalau
    // model chat tidak bisa baca gambar (mis. deepseek), hasilnya ngawur.
    // Sekarang: pakai cfg.visionModel kalau diisi, kalau tidak -> model chat.
    yield* _streamDari([
      ...?riwayat,
      {'role': 'user', 'content': isi},
    ], model: (cfg.visionModel != null && cfg.visionModel!.isNotEmpty)
        ? cfg.visionModel
        : null);
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

  /// [model] = override model (dipakai untuk VISION supaya gambar dikirim ke
  /// model yang memang bisa membaca gambar, mis. ag/gemini-3.8-flash-high).
  Stream<String> _streamDari(List<Map<String, dynamic>> messages,
      {String? model}) async* {
    final req = http.Request('POST', _u('/v1/chat/completions'));
    req.headers.addAll(_headers);
    req.body = jsonEncode({
      'model': (model != null && model.isNotEmpty)
          ? model
          : (cfg.model ?? 'synapse-agent'),
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
