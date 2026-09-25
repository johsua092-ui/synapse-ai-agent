import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:shared_preferences/shared_preferences.dart';

/// Konfigurasi koneksi ke Synapse api_server.
class ApiConfig {
  final String baseUrl;
  final String apiKey;
  final String? model;
  final String? displayName;
  final int? contextWindow;

  /// Model VISION (untuk membaca gambar).
  final String? visionModel;

  /// Provider vision: 'auto' | 'gemini' | 'openai'
  final String visionProvider;

  const ApiConfig({
    this.baseUrl = '',
    this.apiKey = '',
    this.model,
    this.displayName,
    this.contextWindow,
    this.visionModel,
    this.visionProvider = 'auto',
  });

  bool get terisi => baseUrl.trim().isNotEmpty && apiKey.trim().isNotEmpty;

  ApiConfig copyWith({
    String? baseUrl,
    String? apiKey,
    String? model,
    String? displayName,
    int? contextWindow,
    String? visionModel,
    String? visionProvider,
  }) =>
      ApiConfig(
        baseUrl: baseUrl ?? this.baseUrl,
        apiKey: apiKey ?? this.apiKey,
        model: model ?? this.model,
        displayName: displayName ?? this.displayName,
        contextWindow: contextWindow ?? this.contextWindow,
        visionModel: visionModel ?? this.visionModel,
        visionProvider: visionProvider ?? this.visionProvider,
      );
}

/// Satu pilihan model vision.
class VisionOption {
  final String id;
  final String nama;
  final String deskripsi;
  const VisionOption(this.id, this.nama, this.deskripsi);
}

/// Daftar model vision yang bisa dipilih user (sesuai model di .env Synapse).
const daftarVision = <VisionOption>[
  VisionOption('auto', 'Otomatis (ikut server)',
      'Pakai pengaturan vision dari config Synapse'),
  VisionOption('gemini-3-flash-preview', 'Gemini 3 Flash',
      'Cepat, cocok untuk teks & gambar umum'),
  VisionOption('gemini-2.5-flash', 'Gemini 2.5 Flash', 'Seimbang, akurasi baik'),
  VisionOption('gemini-flash-latest', 'Gemini Flash Latest',
      'Selalu versi terbaru'),
  VisionOption('gemini-2.0-flash', 'Gemini 2.0 Flash', 'Stabil & hemat'),
  VisionOption('gemini-2.5-flash-lite', 'Gemini 2.5 Flash Lite',
      'Paling ringan & cepat'),
];

class ApiConfigNotifier extends StateNotifier<ApiConfig> {
  ApiConfigNotifier() : super(const ApiConfig()) {
    _muat();
  }

  static const _kBase = 'api_base_url';
  static const _kKey = 'api_key';
  static const _kModel = 'api_model';
  static const _kName = 'api_display_name';
  static const _kCtx = 'api_context_window';
  static const _kVision = 'api_vision_model';
  static const _kVisionProv = 'api_vision_provider';

  Future<void> _muat() async {
    final p = await SharedPreferences.getInstance();
    state = ApiConfig(
      baseUrl: p.getString(_kBase) ?? '',
      apiKey: p.getString(_kKey) ?? '',
      model: p.getString(_kModel),
      displayName: p.getString(_kName),
      contextWindow: p.getInt(_kCtx),
      visionModel: p.getString(_kVision),
      visionProvider: p.getString(_kVisionProv) ?? 'auto',
    );
  }

  Future<void> simpan(ApiConfig c) async {
    state = c;
    final p = await SharedPreferences.getInstance();
    await p.setString(_kBase, c.baseUrl);
    await p.setString(_kKey, c.apiKey);
    if (c.model != null) await p.setString(_kModel, c.model!);
    if (c.displayName != null) await p.setString(_kName, c.displayName!);
    if (c.contextWindow != null) await p.setInt(_kCtx, c.contextWindow!);
    if (c.visionModel != null) await p.setString(_kVision, c.visionModel!);
    await p.setString(_kVisionProv, c.visionProvider);
  }

  Future<void> kosongkan() async {
    state = const ApiConfig();
    final p = await SharedPreferences.getInstance();
    await p.clear();
  }
}

final apiConfigProvider =
    StateNotifierProvider<ApiConfigNotifier, ApiConfig>((ref) => ApiConfigNotifier());
