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
final koneksiProvider = FutureProvider.autoDispose<Map<String, dynamic>>((ref) async {
  final c = ref.watch(apiClientProvider);
  if (c == null) throw Exception('Belum diatur');
  return c.health();
});
