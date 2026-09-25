import 'package:flutter/material.dart';
import 'package:webview_flutter/webview_flutter.dart';
import 'live2d_server.dart';

/// Viewer Live2D asli — model + background dibawa DI DALAM APK (offline).
///
/// 8 model resmi Live2D Inc + 14 background dari Open-LLM-VTuber.
///
/// JEBAKAN YANG SUDAH DILEWATI:
///   1. WebView blokir `file://` (CORS) -> "Network error".
///      SOLUSI: server HTTP lokal (Live2DServer) + buka via http://127.0.0.1.
///   2. Flutter TIDAK rekursif untuk asset -> subfolder harus didaftarkan.
///   3. WAJIB `registerTicker` untuk pixi-live2d-display versi UMD
///      (kalau tidak -> "Maximum call stack size exceeded").
///   4. JANGAN muat cubism2 + cubism4 + index bersamaan (registrasi ganda).
///   5. JANGAN pakai `resizeTo` di PIXI.Application (bisa bikin loop).
class Live2DView extends StatefulWidget {
  const Live2DView({
    super.key,
    required this.modelId,
    this.background,
    this.bicara = false,
    this.emosi,
    this.onSiap,
  });

  final String modelId;
  final String? background;
  final bool bicara;
  final String? emosi;
  final VoidCallback? onSiap;

  @override
  State<Live2DView> createState() => _Live2DViewState();
}

class _Live2DViewState extends State<Live2DView> {
  WebViewController? _c;
  bool _siap = false;
  String _pesan = 'Menyiapkan...';

  @override
  void initState() {
    super.initState();
    _siapkan();
  }

  @override
  void didUpdateWidget(Live2DView old) {
    super.didUpdateWidget(old);
    if (old.bicara != widget.bicara) {
      _panggil('setBicara', widget.bicara.toString());
    }
    if (old.emosi != widget.emosi && widget.emosi != null) {
      _panggil('setEmosi', widget.emosi!);
    }
    if (old.modelId != widget.modelId) {
      _panggil('gantiModel', widget.modelId);
    }
    if (old.background != widget.background) {
      _panggil('gantiBackground', widget.background ?? 'none');
    }
  }

  void _panggil(String f, String a) {
    if (!_siap) return;
    _c?.runJavaScript("window.$f && window.$f('$a');");
  }

  Future<void> _siapkan() async {
    try {
      final port = await Live2DServer.mulai();
      if (!mounted) return;
      setState(() => _pesan = 'Memuat karakter...');

      final c = WebViewController()
        ..setJavaScriptMode(JavaScriptMode.unrestricted)
        ..setBackgroundColor(const Color(0xFF0D0C11))
        ..setNavigationDelegate(NavigationDelegate(
          onPageFinished: (_) {
            if (!mounted) return;
            setState(() => _siap = true);
            widget.onSiap?.call();
            _panggil('gantiBackground', widget.background ?? 'none');
            _panggil('gantiModel', widget.modelId);
          },
          onWebResourceError: (_) {},
        ));
      await c.loadRequest(Uri.parse('http://127.0.0.1:$port/live2d/viewer.html'));
      if (mounted) setState(() => _c = c);
    } catch (e) {
      if (mounted) setState(() => _pesan = 'Gagal: $e');
    }
  }

  @override
  Widget build(BuildContext context) {
    if (_c == null) {
      return ColoredBox(
        color: const Color(0xFF0D0C11),
        child: Center(
          child: Column(mainAxisSize: MainAxisSize.min, children: [
            const CircularProgressIndicator(),
            const SizedBox(height: 12),
            Text(_pesan,
                style: const TextStyle(color: Color(0xFFDCB363), fontSize: 12)),
          ]),
        ),
      );
    }
    return WebViewWidget(controller: _c!);
  }
}
