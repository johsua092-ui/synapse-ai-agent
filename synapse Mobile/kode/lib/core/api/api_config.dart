import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:shared_preferences/shared_preferences.dart';

/// Konfigurasi koneksi ke Synapse api_server.
class ApiConfig {
  final String baseUrl;
  final String apiKey;
  /// FIX v1.2.7 — BASE URL TERPISAH UNTUK AGENT (fitur "2 Base URL").
  final String? model;
  final String? displayName;
  final int? contextWindow;

  /// Model VISION (untuk membaca gambar).
  final String? visionModel;

  /// Provider vision: 'auto' | 'gemini' | 'openai'
  final String visionProvider;

  /// JEBAKAN #102 (v1.2.6) — PENANDA "SUDAH SELESAI & TERBUKTI VALID".
  ///
  /// `true` HANYA kalau konfigurasi ini pernah DIVALIDASI NYATA ke server dan
  /// BERHASIL. Inilah bukti 100% bahwa user benar-benar sudah selesai
  /// (bukan sekadar "terisi"), sehingga app tidak salah bilang
  /// "belum selesai" padahal sudah valid.
  final bool tervalidasi;

  /// FIX v1.2.7 — BASE URL AGENT (untuk Tools/Skills/Backup/MCP/Perangkat).
  /// Kalau KOSONG -> pakai `baseUrl` (perilaku lama, tetap kompatibel).
  /// Diisi kalau user mau: CHAT via router (9router) + AGENT via Synapse PC.
  final String agentBaseUrl;

  /// FIX v1.2.7 — API KEY AGENT (kalau beda dari API key chat).
  final String agentApiKey;

  const ApiConfig({
    this.baseUrl = '',
    this.apiKey = '',
    this.model,
    this.displayName,
    this.contextWindow,
    this.visionModel,
    this.visionProvider = 'auto',
    this.tervalidasi = false,
    this.agentBaseUrl = '',
    this.agentApiKey = '',
  });

  bool get terisi => baseUrl.trim().isNotEmpty && apiKey.trim().isNotEmpty;

  /// FIX v1.2.7 — Base URL yang dipakai untuk fitur AGENT.
  /// Kalau `agentBaseUrl` kosong -> jatuh ke `baseUrl` (kompatibel).
  String get baseUrlAgent =>
      agentBaseUrl.trim().isNotEmpty ? agentBaseUrl.trim() : baseUrl.trim();

  /// FIX v1.2.7 — API Key untuk fitur AGENT.
  String get apiKeyAgent =>
      agentApiKey.trim().isNotEmpty ? agentApiKey.trim() : apiKey.trim();

  /// Apakah agent dikonfigurasi terpisah (2 Base URL aktif).
  bool get pakaiAgentTerpisah => agentBaseUrl.trim().isNotEmpty;

  ApiConfig copyWith({
    String? baseUrl,
    String? apiKey,
    String? model,
    String? displayName,
    int? contextWindow,
    String? visionModel,
    String? visionProvider,
    bool? tervalidasi,
    String? agentBaseUrl,
    String? agentApiKey,
  }) =>
      ApiConfig(
        baseUrl: baseUrl ?? this.baseUrl,
        apiKey: apiKey ?? this.apiKey,
        model: model ?? this.model,
        displayName: displayName ?? this.displayName,
        contextWindow: contextWindow ?? this.contextWindow,
        visionModel: visionModel ?? this.visionModel,
        visionProvider: visionProvider ?? this.visionProvider,
        tervalidasi: tervalidasi ?? this.tervalidasi,
        agentBaseUrl: agentBaseUrl ?? this.agentBaseUrl,
        agentApiKey: agentApiKey ?? this.agentApiKey,
      );
}

/// Satu pilihan model vision.
class VisionOption {
  final String id;
  final String nama;
  final String deskripsi;
  const VisionOption(this.id, this.nama, this.deskripsi);
}

/// Daftar model vision yang bisa dipilih user.
///
/// WAJIB: sediakan `ag/gemini-3.8-flash-high` (router 9router) sebagai pilihan
/// UTAMA — model ini terbukti bisa membaca gambar dengan baik, sedangkan
/// `cbai/deepseek-v4.1-flash` TIDAK bisa decode gambar (buta).
const daftarVision = <VisionOption>[
  VisionOption('ag/gemini-3.8-flash-high', 'Gemini 3.8 Flash High (disarankan)',
      'Paling akurat untuk gambar. Router 9router. Context 1 juta token'),
  VisionOption('auto', 'Otomatis (ikut server)',
      'Pakai pengaturan vision dari config Synapse'),
  VisionOption('gemini-3-flash-preview', 'Gemini 3 Flash',
      'Cepat, cocok untuk teks & gambar umum'),
  VisionOption('gemini-3.5-flash', 'Gemini 3.5 Flash', 'Versi lebih baru'),
  VisionOption('gemini-2.5-flash', 'Gemini 2.5 Flash', 'Seimbang, akurasi baik'),
  VisionOption('gemini-flash-latest', 'Gemini Flash Latest',
      'Selalu versi terbaru'),
  VisionOption('gemini-2.5-flash-lite', 'Gemini 2.5 Flash Lite',
      'Paling ringan & cepat'),
];

class ApiConfigNotifier extends StateNotifier<ApiConfig> {
  ApiConfigNotifier() : super(const ApiConfig()) {
    _muatSelesai = _muat();
  }

  /// Selesai memuat konfigurasi dari storage.
  ///
  /// JEBAKAN #101 (v1.2.6) — BUG "kadang bisa, kadang tidak":
  /// `_muat()` berjalan async. Kalau user cepat menekan Kirim / buka layar
  /// sebelum pemuatan selesai, `apiClientProvider` melihat config KOSONG ->
  /// muncul "Belum tersambung" padahal sudah diisi. Chat WAJIB menunggu
  /// `siap` ini dulu sebelum memutuskan "belum tersambung".
  late final Future<void> _muatSelesai;
  Future<void> get siap => _muatSelesai;

  static const _kBase = 'api_base_url';
  static const _kKey = 'api_key';
  static const _kModel = 'api_model';
  static const _kName = 'api_display_name';
  static const _kCtx = 'api_context_window';
  static const _kVision = 'api_vision_model';
  static const _kVisionProv = 'api_vision_provider';
  static const _kValid = 'api_tervalidasi';
  static const _kAgentBase = 'api_agent_base_url';   // FIX v1.2.7
  static const _kAgentKey = 'api_agent_key';         // FIX v1.2.7

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
      tervalidasi: p.getBool(_kValid) ?? false,
      agentBaseUrl: p.getString(_kAgentBase) ?? '',
      agentApiKey: p.getString(_kAgentKey) ?? '',
    );
  }

  /// Simpan DRAFT (belum tentu valid) — progress user tetap tersimpan.
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
    await p.setBool(_kValid, c.tervalidasi);
    await p.setString(_kAgentBase, c.agentBaseUrl);
    await p.setString(_kAgentKey, c.agentApiKey);
  }

  /// Simpan DRAFT cepat (mis. saat user keluar) — progress tidak hilang.
  /// TIDAK menandai `tervalidasi` (biar status "sudah selesai" tetap akurat).
  Future<void> simpanDraft(ApiConfig c) => simpan(c.copyWith(tervalidasi: false));

  Future<void> kosongkan() async {
    state = const ApiConfig();
    final p = await SharedPreferences.getInstance();
    await p.clear();
  }
}

final apiConfigProvider =
    StateNotifierProvider<ApiConfigNotifier, ApiConfig>((ref) => ApiConfigNotifier());
