import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'api_client.dart';
import 'api_config.dart';

/// Klien API yang mengikuti konfigurasi terkini.
final apiClientProvider = Provider<ApiClient?>((ref) {
  final cfg = ref.watch(apiConfigProvider);
  if (!cfg.terisi) return null;
  return ApiClient(cfg);
});

/// Status koneksi (untuk indikator di UI).
///
/// TOLERAN: router kustom (mis. 9router) tidak punya `/health`. Dulu itu
/// membuat status tampak OFFLINE walau server jalan. Sekarang "tanpa /health"
/// dianggap TERHUBUNG (dengan platform generik).
final koneksiProvider =
    FutureProvider.autoDispose<Map<String, dynamic>>((ref) async {
  final c = ref.watch(apiClientProvider);
  if (c == null) throw Exception('Belum diatur');
  final h = await c.health();
  return h ?? <String, dynamic>{'platform': 'server', 'version': '?'};
});
