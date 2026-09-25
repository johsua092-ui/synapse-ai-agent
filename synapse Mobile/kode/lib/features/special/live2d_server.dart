import 'dart:async';
import 'dart:io';
import 'dart:typed_data';
import 'package:flutter/services.dart' show rootBundle;

/// Server HTTP lokal untuk melayani file Live2D + background dari dalam APK.
///
/// KENAPA INI DIPERLUKAN (JEBAKAN PENTING):
///   WebView Android memblokir akses `file://` (CORS) sejak API 30, jadi
///   model Live2D lokal tidak bisa dibaca -> "Network error".
///   Solusi: server HTTP kecil di 127.0.0.1, WebView buka via http://.
///
/// Root server = folder `assets/` -> jadi:
///   /viewer.html            -> assets/viewer.html (tidak ada, pakai /live2d/viewer.html)
///   /live2d/Hiyori/...      -> assets/live2d/Hiyori/...
///   /backgrounds/sekolah.jpg -> assets/backgrounds/sekolah.jpg
class Live2DServer {
  static HttpServer? _server;
  static int _port = 0;

  static int get port => _port;
  static String get url => 'http://127.0.0.1:$_port/live2d/viewer.html';

  static Future<int> mulai() async {
    if (_server != null) return _port;

    late HttpServer s;
    try {
      s = await HttpServer.bind(InternetAddress.loopbackIPv4, 8765);
    } catch (_) {
      s = await HttpServer.bind(InternetAddress.loopbackIPv4, 0);
    }
    _server = s;
    _port = s.port;

    s.listen((req) async {
      try {
        var jalur = req.uri.path;
        if (jalur == '/' || jalur.isEmpty) jalur = '/live2d/viewer.html';
        if (jalur == '/viewer.html') jalur = '/live2d/viewer.html';

        final bersih = jalur.replaceAll('..', '').replaceAll('//', '/');
        final asset = 'assets$bersih';

        try {
          final data = await rootBundle.load(asset);
          req.response.headers.contentType = _tipe(bersih);
          req.response.headers.set('Cache-Control', 'max-age=86400');
          req.response.headers.set('Access-Control-Allow-Origin', '*');
          req.response.add(Uint8List.view(data.buffer));
          print('[Live2DServer] OK  $asset');
        } catch (_) {
          req.response.statusCode = HttpStatus.notFound;
          req.response.write('tidak ada: $asset');
          print('[Live2DServer] 404 $asset');
        }
      } catch (_) {
      } finally {
        try {
          await req.response.close();
        } catch (_) {}
      }
    });
    return _port;
  }

  static ContentType _tipe(String p) {
    final l = p.toLowerCase();
    if (l.endsWith('.html')) return ContentType.html;
    if (l.endsWith('.js')) return ContentType('application', 'javascript');
    if (l.endsWith('.json')) return ContentType('application', 'json');
    if (l.endsWith('.png')) return ContentType('image', 'png');
    if (l.endsWith('.jpg') || l.endsWith('.jpeg')) return ContentType('image', 'jpeg');
    if (l.endsWith('.webp')) return ContentType('image', 'webp');
    return ContentType.binary;
  }

  static Future<void> hentikan() async {
    await _server?.close(force: true);
    _server = null;
    _port = 0;
  }
}
