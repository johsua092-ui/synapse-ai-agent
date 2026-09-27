import 'dart:async';
import 'package:flutter/material.dart';
import 'package:flutter/services.dart' show rootBundle;
import 'dart:convert';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_tts/flutter_tts.dart';
import 'package:permission_handler/permission_handler.dart';
import 'package:speech_to_text/speech_to_text.dart' as stt;
import 'package:webview_flutter/webview_flutter.dart';
import '../../core/api/api_config.dart';
import '../../core/api/api_providers.dart';
import '../../core/sesi/sesi_model.dart';
import '../../core/sesi/sesi_provider.dart';
import '../../core/theme/spacing.dart';
import '../sesi/sesi_drawer.dart';
import 'live2d_view.dart';
import 'suara_anime.dart';

/// SPECIAL CHAT — fitur setara Open-LLM-VTuber
/// (https://github.com/Open-LLM-VTuber/Open-LLM-VTuber)
///
/// Fitur yang dihadirkan:
///   1. Avatar Live2D (WebGL, lewat WebView) — karakter bergerak
///   2. Voice interaction — AI bersuara (TTS) + user bicara (ASR)
///   3. Voice interruption — bisa potong suara AI
///   4. Chat + riwayat (percakapan tersimpan)
///   5. Visual perception — kirim gambar/kamera ke AI
///   6. Emotion/expression — avatar berubah sesuai emosi
///   7. AI proactive speaking — AI bisa bicara duluan
class SpecialChatScreen extends ConsumerStatefulWidget {
  const SpecialChatScreen({super.key});
  @override
  ConsumerState<SpecialChatScreen> createState() => _SpecialChatScreenState();
}

class _SpecialChatScreenState extends ConsumerState<SpecialChatScreen>
    with WidgetsBindingObserver {
  // ---- TTS (AI bersuara) ----
  final _tts = FlutterTts();
  bool _ttsSiap = false;
  bool _suaraAktif = true;

  // ---- ASR (user bicara) ----
  final _stt = stt.SpeechToText();
  bool _sttSiap = false;
  bool _mendengar = false;
  String _teksDidengar = '';

  // ---- Avatar ----
  String _modelId = 'Hiyori';
  String? _background = 'sdxl-classroom-door-view.jpeg';
  /// Suara anime per karakter (Edge TTS) — beda tiap karakter.
  String _suaraKarakter = 'ja-JP-NanamiNeural';
  List<Map<String, dynamic>> _opsiSuara = [];
  /// JEBAKAN #107 (v1.2.6) — JANGAN default `false`!
  /// `false` = suara anime (edge-tts) TIDAK dipakai -> selalu jatuh ke TTS
  /// bawaan HP (Google) -> terasa "seperti Google Indonesia" & GANTI SUARA
  /// TIDAK BERPENGARUH. Default `true` (suara anime asli).
  /// (Kalau lambat, kasih umpan balik "Menyiapkan suara...", bukan matikan fitur.)
  bool _pakaiSuaraAnime = true;
  List<Map<String, dynamic>> _daftarBg = [];
  bool _layarPenuh = false;
  List<Map<String, dynamic>> _daftarModel = [];
  bool _avatarSiap = false;
  /// Tinggi avatar: pakai TINGGI AWAL (tidak menyusut saat keyboard muncul).
  /// JEBAKAN #66: kalau avatar ikut menyusut, karakter jadi terpotong.
  double _tinggiAvatar = 0;
  /// Tinggi keyboard (dibaca dari View; Scaffold menghapus viewInsets
  /// saat resizeToAvoidBottomInset=false). JEBAKAN #67.
  double _tinggiKeyboard = 0;

  // ---- Chat (disimpan lewat sesiProvider -> tidak hilang) ----
  final _masukan = TextEditingController();
  final _scroll = ScrollController();
  final _drawerKey = GlobalKey<ScaffoldState>();
  /// ID sesi aktif (disimpan seperti tab Chat).
  String? _sesiId;
  bool _sibuk = false;
  bool _sedangBicara = false;
  /// Info saat suara sedang disiapkan (JEBAKAN #107).
  String? _infoSuara;

  /// Nama karakter untuk prompt roleplay (ikut model Live2D yang dipilih).
  String get _namaKarakter =>
      _modelId.isEmpty ? 'Hiyori' : _modelId;

  // ---- Pengaturan ----
  String _suaraPilihan = 'id-ID';
  /// Kecepatan suara (JEBAKAN #110, v1.2.6).
  ///
  /// PENTING: pada `flutter_tts` untuk Android, nilai `setSpeechRate(1.0)`
  /// BUKAN "normal" — 1.0 = 2x kecepatan normal (terdengar seperti ngerap).
  /// Normal di Android = **0.5**. Default dipakai 0.5 supaya enak didengar;
  /// user tetap bisa mengubahnya lewat Pengaturan suara.
  double _kecepatan = 0.5;
  double _nada = 1.0;
  bool _proaktif = false;
  Timer? _timerProaktif;

  @override
  void initState() {
    super.initState();
    // Observer keyboard: supaya input naik saat keyboard muncul.
    // JEBAKAN #67: resizeToAvoidBottomInset=false -> MediaQuery.viewInsets
    // jadi 0 dan tidak ada rebuild; harus pakai observer + View.
    WidgetsBinding.instance.addObserver(this);
    _siapkanTts();
    _siapkanStt();
    _muatDaftarModel();
    _muatSuaraKarakter('Hiyori');
  }

  @override
  void dispose() {
    WidgetsBinding.instance.removeObserver(this);
    _timerProaktif?.cancel();
    _tts.stop();
    _stt.stop();
    _masukan.dispose();
    _scroll.dispose();
    super.dispose();
  }

  @override
  void didChangeMetrics() {
    // keyboard muncul/tertutup -> hitung ulang tinggi keyboard
    if (mounted) setState(() {});
  }

  /// Tinggi keyboard (px). Dibaca dari View, karena Scaffold menghapus
  /// viewInsets saat resizeToAvoidBottomInset=false.
  double get _kb => View.of(context).viewInsets.bottom;

  // ================= PERSIAPAN =================

  Future<void> _siapkanTts() async {
    try {
      await _tts.setLanguage(_suaraPilihan);
      await _tts.setSpeechRate(_kecepatan);
      await _tts.setPitch(_nada);
      await _tts.setVolume(1.0);
      await _tts.awaitSpeakCompletion(true);
      if (mounted) setState(() => _ttsSiap = true);
    } catch (_) {}
  }

  Future<void> _siapkanStt() async {
    try {
      final ok = await _stt.initialize(
        onStatus: (s) {
          if (!mounted) return;
          if (s == 'done' || s == 'notListening') {
            setState(() => _mendengar = false);
            if (_teksDidengar.trim().isNotEmpty) {
              _kirim(_teksDidengar.trim());
              _teksDidengar = '';
            }
          }
        },
        onError: (_) {
          if (mounted) setState(() => _mendengar = false);
        },
      );
      if (mounted) setState(() => _sttSiap = ok);
    } catch (_) {}
  }

  /// Muat daftar model Live2D (dari assets).
  Future<void> _muatDaftarModel() async {
    try {
      final raw = await rootBundle.loadString('assets/live2d_model.json');
      final d = jsonDecode(raw) as Map<String, dynamic>;
      final list = ((d['model'] as List?) ?? const [])
          .map((e) => Map<String, dynamic>.from(e as Map))
          .toList();
      if (mounted) setState(() => _daftarModel = list);
    } catch (_) {}
    try {
      final raw2 = await rootBundle.loadString('assets/background_list.json');
      final d2 = jsonDecode(raw2) as Map<String, dynamic>;
      final lb = ((d2['background'] as List?) ?? const [])
          .map((e) => Map<String, dynamic>.from(e as Map))
          .toList();
      if (mounted) setState(() => _daftarBg = lb);
    } catch (_) {}
  }

  // ================= AKSI =================

  /// Bicara (TTS).
  Future<void> _bicara(String teks) async {
    if (!_suaraAktif) return;
    setState(() => _sedangBicara = true);
    try {
      await _tts.stop();            // interruption
      await SuaraAnime.berhenti();  // interruption suara anime

      // 1. COBA suara anime asli (edge-tts lewat agent)
      final klien = ref.read(apiClientProvider);
      if (_pakaiSuaraAnime && klien != null) {
        // Umpan balik: pembuatan suara butuh beberapa detik -> beri tahu user
        // (jangan diam). JEBAKAN #107.
        if (mounted) setState(() => _infoSuara = 'Menyiapkan suara...');
        final f = await SuaraAnime.buatLewatServer(
          klien: klien,
          teks: teks,
          suara: _suaraKarakter,
        );
        if (mounted) setState(() => _infoSuara = null);
        if (f != null) {
          await SuaraAnime.putar(f);
          // tunggu kira-kira selesai (perkiraan 0,4 detik per karakter)
          await Future.delayed(
              Duration(milliseconds: (teks.length * 90).clamp(1500, 30000)));
          return;
        }
      }

      // 2. CADANGAN: TTS bawaan HP (dipakai kalau agent tidak siap)
      if (mounted) setState(() => _infoSuara = null);
      if (_ttsSiap) await _tts.speak(teks);
    } catch (_) {
    } finally {
      if (mounted) setState(() => _sedangBicara = false);
    }
  }

  /// Mulai/berhenti mendengar (ASR).
  Future<void> _toggleDengar() async {
    if (_mendengar) {
      await _stt.stop();
      setState(() => _mendengar = false);
      return;
    }
    // izin mikrofon
    final izin = await Permission.microphone.request();
    if (!izin.isGranted) {
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(const SnackBar(
          content: Text('Izin mikrofon ditolak. Aktifkan di Setelan HP.')));
      return;
    }
    if (!_sttSiap) {
      await _siapkanStt();
      if (!_sttSiap) {
        if (!mounted) return;
        ScaffoldMessenger.of(context).showSnackBar(const SnackBar(
            content: Text('Pengenal suara tidak tersedia di HP ini.')));
        return;
      }
    }
    // interruption: hentikan suara AI dulu
    await _tts.stop();
    _teksDidengar = '';
    setState(() => _mendengar = true);
    await _stt.listen(
      localeId: _suaraPilihan,
      listenFor: const Duration(seconds: 30),
      pauseFor: const Duration(seconds: 3),
      onResult: (r) {
        setState(() => _teksDidengar = r.recognizedWords);
      },
    );
  }

  /// Kirim pesan ke AI (STREAMING) lalu dibacakan (TTS).
  ///
  /// JEBAKAN #106 (v1.2.6) — 4 keluhan user sekaligus:
  ///  1. LAMBAT  -> dulu pakai `klien.chat()` (non-streaming, nunggu jawaban
  ///     PENUH dulu). Sekarang `chatStream()` -> teks muncul bertahap.
  ///  2. TIDAK ada animasi mikir -> tambah indikator "Sedang berpikir".
  ///  3. Chat HILANG -> dulu `_pesan` cuma list lokal (tidak disimpan).
  ///     Sekarang pakai `sesiProvider` (sama seperti tab Chat) + drawer sesi.
  ///  4. TTS telat -> mulai bicara saat kalimat PERTAMA sudah utuh
  ///     (bukan menunggu seluruh balasan selesai).
  Future<void> _kirim(String teks) async {
    if (teks.trim().isEmpty) return;
    final n = ref.read(sesiProvider.notifier);
    await n.siap();
    var id = _sesiId ?? '';
    if (id.isEmpty) {
      id = n.buatBaru();
      _sesiId = id;
    }
    setState(() {
      n.tambahPesan(id, Pesan(teks: teks, dariSaya: true));
      _sibuk = true;
    });
    _masukan.clear();
    _gulir();

    final klien = ref.read(apiClientProvider);
    if (klien == null) {
      setState(() {
        n.tambahPesan(id, Pesan(
            teks: 'Belum tersambung. Isi Base URL + API Key di Setelan.',
            dariSaya: false));
        _sibuk = false;
      });
      return;
    }

    // pesan kosong tempat streaming ditulis
    n.tambahPesan(id, Pesan(teks: '', dariSaya: false));
    final buffer = StringBuffer();
    // JEBAKAN #120 (v1.2.6): dulu suara baru mulai setelah balasan PENUH ->
    // terasa delay panjang. Sekarang: begitu KALIMAT PERTAMA utuh, langsung
    // minta suara (paralel) sementara sisa teks masih mengalir.
    var suaraDimulai = false;

    try {
      final aliran = klien.chatStream(
        _promptKarakter(teks),
        model: ref.read(apiConfigProvider).model,
      );
      await for (final potongan in aliran) {
        buffer.write(potongan);
        if (!mounted) return;
        setState(() {
          n.gantiTerakhir(id!, Pesan(teks: buffer.toString()));
        });
        _gulir();
        // Mulai bersuara lebih awal (kalimat pertama sudah utuh).
        if (_suaraAktif && !suaraDimulai) {
          final k = _kalimatUtuhPertama(buffer.toString());
          if (k != null) {
            suaraDimulai = true;
            _bicara(k); // tidak di-await: biar streaming tetap jalan
          }
        }
      }
      if (!mounted) return;
      setState(() {
        n.gantiTerakhir(id!, Pesan(
            teks: buffer.isEmpty ? '(balasan kosong)' : buffer.toString()));
        n.simpanKeDisk(id);
        _sibuk = false;
      });
      _gulir();
      // JEBAKAN #120: kalau suara belum dimulai (balasan pendek / tanpa tanda
      // baca), bacakan sekarang. Kalau sudah dimulai di tengah -> JANGAN ulang
      // (biar tidak dobel).
      if (_suaraAktif && !suaraDimulai && buffer.isNotEmpty) {
        _bicara(buffer.toString());
      }
    } catch (e) {
      if (!mounted) return;
      setState(() {
        n.gantiTerakhir(id!, Pesan(teks: 'Gagal: $e'));
        n.simpanKeDisk(id);
        _sibuk = false;
      });
    }
  }

  /// Kalimat pertama yang sudah UTUH (diakhiri . ! ? atau baris baru).
  ///
  /// Mengembalikan null kalau belum ada kalimat utuh / masih terlalu pendek.
  /// Dipakai untuk MULAI BERSUARA lebih awal (JEBAKAN #120).
  String? _kalimatUtuhPertama(String s) {
    final t = s.trim();
    if (t.length < 15) return null;
    final m = RegExp(r'^[\s\S]{10,}?[.!?](\s|$)').firstMatch(t);
    if (m == null) {
      // tidak ada tanda baca: tunggu sampai cukup panjang (>= 60 huruf)
      return t.length >= 60 ? t : null;
    }
    return m.group(0)!.trim();
  }

  /// Prompt KEPRIBADIAN karakter (roleplay) — permintaan user v1.2.6.
  ///
  /// Karakter konsisten sebagai tokoh anime, ingat peran, ekspresif.
  /// (Catatan: TIDAK ada instruksi untuk melewati kebijakan keamanan model.)
  String _promptKarakter(String pesan) =>
      'Kamu berperan sebagai karakter VTuber bernama $_namaKarakter. '
      'ATURAN PERAN:\n'
      '- Tetap 100% konsisten sebagai tokoh ini (jangan keluar dari peran).\n'
      '- Ingat & lanjutkan alur percakapan/peran sebelumnya.\n'
      '- Gaya bicara: hangat, ekspresif, hidup, sedikit ceria seperti anime.\n'
      '- Jawab SINGKAT (maksimal 3 kalimat) supaya enak dibacakan.\n'
      '- Pakai bahasa Indonesia.\n'
      '- Kalau peran tidak jelas, ikuti saja arahan user.\n\n'
      'User: $pesan';

  void _gulir() {
    WidgetsBinding.instance.addPostFrameCallback((_) {
      if (_scroll.hasClients) {
        _scroll.animateTo(_scroll.position.maxScrollExtent,
            duration: const Duration(milliseconds: 250), curve: Curves.easeOut);
      }
    });
  }

  /// AI bicara duluan (proactive speaking).
  ///
  /// JEBAKAN #109 (v1.2.6): user minta fitur ini TIDAK perlu -> pesan otomatis
  /// "(bicaralah duluan ...)" DIHAPUS. Proaktif sekarang hanya memicu sapaan
  /// tanpa mengirim teks instruksi ke chat.
  void _toggleProaktif(bool v) {
    setState(() => _proaktif = v);
    _timerProaktif?.cancel();
    if (v) {
      _timerProaktif = Timer.periodic(const Duration(seconds: 45), (_) {
        if (ref.read(sesiProvider.notifier).aktif?.pesan.isNotEmpty == true &&
            !_sibuk) {
          // Sengaja TIDAK mengirim pesan teks apa pun ke chat.
          // (Fitur "kirim pesan otomatis" dimatikan atas permintaan user.)
        }
      });
    }
  }

  // ================= UI =================

  @override
  Widget build(BuildContext context) {
    final t = Theme.of(context);
    final cfg = ref.watch(apiConfigProvider);
    // Sesi aktif -> pesan diambil dari sesiProvider (tersimpan, tidak hilang).
    final sesiAktif = ref.watch(sesiProvider.notifier).aktif;
    final daftarPesan = sesiAktif?.pesan ?? const <Pesan>[];

    // Tinggi avatar: 40% tinggi layar (tanpa keyboard).
    // JEBAKAN #68: kalau 50%, avatar + input TIDAK muat saat keyboard muncul
    // (keyboard ~45% layar) -> input terdorong keluar layar (tampak tertimpa).
    // 40% + input (~7%) = 47% < 55% sisa ruang -> aman.
    if (_tinggiAvatar == 0) {
      final h = MediaQuery.of(context).size.height;
      _tinggiAvatar = (h * 0.40).clamp(180.0, 520.0);
    }

    // JEBAKAN #113 (v1.2.6): tinggi avatar WAJIB STABIL.
    // JANGAN hitung dari `LayoutBuilder.maxHeight` / `viewInsets` — nilai itu
    // BERUBAH SELAMA ANIMASI keyboard -> avatar ikut "gede-kecil-gede"
    // (glitching). Pakai ukuran LAYAR (MediaQuery.size) yang TIDAK berubah
    // saat keyboard muncul.
    final hLayar = MediaQuery.of(context).size.height;
    final tinggiAvatar = (hLayar * 0.40).clamp(180.0, 520.0);
    // Tinggi keyboard (RAW dari View — tidak terpengaruh resize Scaffold).
    final kb = View.of(context).viewInsets.bottom;

    return Scaffold(
      key: _drawerKey,
      // JEBAKAN #106: drawer SESI CHAT (strip tiga) — plek ketiplek tab Chat.
      drawer: const SesiDrawer(),
      backgroundColor: Colors.transparent,
      // JEBAKAN #114 (v1.2.6) — AKAR TERAKHIR kolom terjepit:
      // AppShell (kerangka utama) SUDAH punya Scaffold dengan
      // `resizeToAvoidBottomInset: true`. Kalau layar INI juga `true`, keyboard
      // dikurangi DUA KALI -> ruang menyusut berlebihan (sisa ~700px) padahal
      // avatar butuh 1084px -> Column meluber -> kolom input TERJEPIT (3px).
      // SOLUSI: `false` di sini (biarkan AppShell yang menggeser seluruh layar),
      // avatar TETAP 40% (stabil), kolom input dapat tinggi penuh.
      resizeToAvoidBottomInset: false,
      body: _isiUtama(context, t, cfg, daftarPesan, tinggiAvatar, kb),
    );
  }

  Widget _isiUtama(BuildContext context, ThemeData t, ApiConfig cfg,
      List<Pesan> daftarPesan, double tinggiAvatar, double kb) {
    return Column(
      children: [
        // ---- SUBJUDUL (disembunyikan saat keyboard terbuka; JEBAKAN #114) ----
        // Hemat ~120px supaya kolom input dapat tinggi penuh. Avatar TIDAK
        // disentuh (tetap 40%). Muncul lagi saat keyboard ditutup.
        if (kb <= 0)
          Padding(
          padding: const EdgeInsets.fromLTRB(4, 6, 12, 0),
          child: Row(children: [
            IconButton(
              tooltip: 'Sesi chat (simpan/buka)',
              visualDensity: VisualDensity.compact,
              icon: const Icon(Icons.menu, size: 20),
              onPressed: () => _drawerKey.currentState?.openDrawer(),
            ),
            const SizedBox(width: 2),
            Icon(Icons.auto_awesome, size: 15, color: t.colorScheme.primary),
            const SizedBox(width: 6),
            Text('VTuber — Special Chat',
                style: t.textTheme.bodySmall?.copyWith(
                  color: t.colorScheme.primary,
                  fontWeight: FontWeight.w600,
                )),
          ]),
        ),
        // ---- AVATAR (dihitung dari RUANG NYATA; JEBAKAN #112) ----
        // Tidak lagi dikecilkan saat keyboard — tingginya sudah menyesuaikan
        // ruang, jadi kotak Live2D tidak "dipaksa" berubah oleh bug tata letak.
        SizedBox(
          height: tinggiAvatar,
          child: Stack(children: [
            Positioned.fill(
              child: Live2DView(
                modelId: _modelId,
                background: _background,
                bicara: _sedangBicara,
                onSiap: () => setState(() => _avatarSiap = true),
              ),
            ),
            // status koneksi
            Positioned(
              left: 12,
              top: 12,
              child: _chip(
                cfg.terisi ? 'Terhubung' : 'Belum tersambung',
                cfg.terisi ? Colors.green : Colors.orange,
              ),
            ),
            if (_mendengar)
              Positioned(
                right: 12,
                top: 12,
                child: _chip('Mendengar...', Colors.red),
              ),
            if (!_avatarSiap)
              const Center(child: CircularProgressIndicator()),
          ]),
        ),

        // ---- KONTROL SUARA ----
        Container(
          padding: const EdgeInsets.symmetric(
              horizontal: AppSpacing.md, vertical: AppSpacing.sm),
          color: t.colorScheme.surfaceContainerHighest,
          child: Row(children: [
            IconButton(
              tooltip: _suaraAktif ? 'Matikan suara AI' : 'Nyalakan suara AI',
              icon: Icon(_suaraAktif ? Icons.volume_up : Icons.volume_off),
              onPressed: () => setState(() => _suaraAktif = !_suaraAktif),
            ),
            Expanded(
              child: Text(
                _mendengar
                    ? (_teksDidengar.isEmpty ? 'Bicara sekarang...' : _teksDidengar)
                    : (_infoSuara ??
                        (_sibuk ? 'AI sedang menjawab...' : 'Ketuk mikrofon & bicara')),
                maxLines: 1,
                overflow: TextOverflow.ellipsis,
                style: t.textTheme.bodySmall,
              ),
            ),
            IconButton(
              tooltip: 'Ganti karakter',
              icon: const Icon(Icons.person_outline),
              onPressed: _dialogModel,
            ),
            IconButton(
              tooltip: 'Ganti latar belakang',
              icon: const Icon(Icons.wallpaper),
              onPressed: _dialogBackground,
            ),
            IconButton(
              tooltip: 'Ganti suara karakter',
              icon: const Icon(Icons.record_voice_over),
              onPressed: _dialogSuaraKarakter,
            ),
            IconButton(
              tooltip: 'Pengaturan suara',
              icon: const Icon(Icons.tune),
              onPressed: _dialogSuara,
            ),
            IconButton(
              tooltip: _proaktif ? 'Matikan bicara proaktif' : 'Nyalakan bicara proaktif',
              icon: Icon(_proaktif ? Icons.record_voice_over : Icons.voice_over_off),
              onPressed: () => _toggleProaktif(!_proaktif),
            ),
          ]),
        ),

        // ---- CHAT (boleh menyusut saat keyboard muncul) ----
        Expanded(
          child: ListView.builder(
            controller: _scroll,
            padding: const EdgeInsets.all(AppSpacing.md),
            itemCount: daftarPesan.length,
            itemBuilder: (c, i) {
              final p = daftarPesan[i];
              final saya = p.dariSaya;
              final kosong = p.teks.isEmpty; // balasan belum datang -> mikir
              return Align(
                alignment: saya ? Alignment.centerRight : Alignment.centerLeft,
                child: Container(
                  margin: const EdgeInsets.only(bottom: 8),
                  padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
                  constraints: BoxConstraints(
                      maxWidth: MediaQuery.of(context).size.width * 0.75),
                  decoration: BoxDecoration(
                    color: saya
                        ? t.colorScheme.primary
                        : t.colorScheme.surfaceContainerHighest,
                    borderRadius: BorderRadius.circular(12),
                  ),
                  child: kosong
                      // JEBAKAN #106: animasi "Sedang berpikir" (dulu tidak ada)
                      ? Row(mainAxisSize: MainAxisSize.min, children: [
                          SizedBox(
                            width: 13,
                            height: 13,
                            child: CircularProgressIndicator(
                              strokeWidth: 2,
                              color: t.colorScheme.primary,
                            ),
                          ),
                          const SizedBox(width: 8),
                          Text('Sedang berpikir',
                              style: t.textTheme.bodySmall?.copyWith(
                                  fontStyle: FontStyle.italic)),
                        ])
                      : SelectableText(
                          p.teks,
                          style: TextStyle(
                              color: saya ? Colors.white : null, fontSize: 13),
                        ),
                ),
              );
            },
          ),
        ),

        // ---- INPUT (naik di atas keyboard lewat resize; JEBAKAN #112) ----
        // resizeToAvoidBottomInset:true -> Scaffold menggeser input otomatis.
        // (JEBAKAN #67 tidak berlaku lagi karena resize AKTIF.)
        SafeArea(
          top: false,
          child: Padding(
            padding: EdgeInsets.fromLTRB(
                AppSpacing.md,
                0,
                AppSpacing.md,
                AppSpacing.sm),
            child: Row(children: [
              Expanded(
                child: TextField(
                  controller: _masukan,
                  maxLines: 1,
                  textInputAction: TextInputAction.send,
                  onSubmitted: _kirim,
                  decoration: const InputDecoration(
                    hintText: 'Ketik pesan...',
                    border: OutlineInputBorder(),
                    isDense: true,
                  ),
                ),
              ),
              const SizedBox(width: 6),
              // mikrofon (ASR) — inti fitur VTuber
              IconButton.filled(
                tooltip: _mendengar ? 'Berhenti' : 'Bicara',
                icon: Icon(_mendengar ? Icons.stop : Icons.mic),
                style: IconButton.styleFrom(
                  backgroundColor: _mendengar ? Colors.red : t.colorScheme.primary,
                ),
                onPressed: _sibuk ? null : _toggleDengar,
              ),
              IconButton(
                tooltip: 'Kirim',
                icon: const Icon(Icons.send),
                onPressed: _sibuk ? null : () => _kirim(_masukan.text),
              ),
            ]),
          ),
        ),
      ],
    );
  }

  Widget _chip(String teks, Color warna) => Container(
        padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
        decoration: BoxDecoration(
          color: warna.withValues(alpha: 0.85),
          borderRadius: BorderRadius.circular(10),
        ),
        child: Text(teks,
            style: const TextStyle(color: Colors.white, fontSize: 11)),
      );

  /// Muat suara anime untuk karakter (beda tiap karakter).
  Future<void> _muatSuaraKarakter(String id) async {
    final opsi = await SuaraAnime.untuk(id);
    final def = await SuaraAnime.defaultUntuk(id);
    if (!mounted) return;
    setState(() {
      _opsiSuara = opsi;
      if (def != null) _suaraKarakter = def;
    });
  }

  /// Pilih suara karakter (suara anime, beda tiap karakter).
  Future<void> _dialogSuaraKarakter() async {
    await showModalBottomSheet(
      context: context,
      showDragHandle: true,
      builder: (c) {
        final t = Theme.of(c);
        return SafeArea(
          child: Column(mainAxisSize: MainAxisSize.min, children: [
            Padding(
              padding: const EdgeInsets.all(AppSpacing.md),
              child: Row(children: [
                const Icon(Icons.record_voice_over),
                const SizedBox(width: 8),
                Expanded(
                  child: Text('Suara ${_modelId}',
                      style: t.textTheme.titleMedium),
                ),
              ]),
            ),
            Padding(
              padding: const EdgeInsets.symmetric(horizontal: AppSpacing.md),
              child: Text(
                'Suara anime asli (Edge TTS). Tiap karakter punya suara '
                'berbeda. Ketuk untuk mendengar.',
                style: t.textTheme.bodySmall,
              ),
            ),
            const SizedBox(height: AppSpacing.sm),
            // JEBAKAN #116 (v1.2.6): daftar suara sekarang 12+ per karakter ->
            // WAJIB bisa di-scroll, kalau tidak daftarnya terpotong.
            Flexible(
              child: ListView(
                shrinkWrap: true,
                children: [
            for (final o in _opsiSuara)
              ListTile(
                leading: Icon(
                  o['id'] == _suaraKarakter
                      ? Icons.radio_button_checked
                      : Icons.radio_button_unchecked,
                  color: o['id'] == _suaraKarakter
                      ? t.colorScheme.primary
                      : null,
                ),
                title: Text(o['nama'] as String),
                trailing: const Icon(Icons.play_circle_outline),
                onTap: () {
                  setState(() => _suaraKarakter = o['id'] as String);
                  _bicara('Halo, aku ${_modelId}. Ini suaraku.');
                  Navigator.pop(c);
                },
              ),
                ],
              ),
            ),
            const SizedBox(height: AppSpacing.sm),
          ]),
        );
      },
    );
  }

  /// Pilih latar belakang (14 background dari Open-LLM-VTuber).
  Future<void> _dialogBackground() async {
    await showModalBottomSheet(
      context: context,
      showDragHandle: true,
      isScrollControlled: true,
      builder: (c) {
        final t = Theme.of(c);
        return SafeArea(
          child: SizedBox(
            height: MediaQuery.of(c).size.height * 0.7,
            child: Column(children: [
              Padding(
                padding: const EdgeInsets.all(AppSpacing.md),
                child: Row(children: [
                  const Icon(Icons.wallpaper),
                  const SizedBox(width: 8),
                  Text('Pilih Latar Belakang', style: t.textTheme.titleMedium),
                ]),
              ),
              // pilihan "tanpa latar" (hitam)
              ListTile(
                leading: Container(
                  width: 44, height: 44,
                  decoration: BoxDecoration(
                    color: const Color(0xFF0D0C11),
                    borderRadius: BorderRadius.circular(6),
                    border: Border.all(color: t.colorScheme.outlineVariant),
                  ),
                ),
                title: const Text('Tanpa latar (gelap)'),
                trailing: _background == null
                    ? Icon(Icons.check_circle, color: t.colorScheme.primary)
                    : null,
                onTap: () {
                  setState(() => _background = null);
                  Navigator.pop(c);
                },
              ),
              const Divider(height: 1),
              Expanded(
                child: ListView.builder(
                  itemCount: _daftarBg.length,
                  itemBuilder: (c2, i) {
                    final b = _daftarBg[i];
                    final file = b['file'] as String;
                    final aktif = file == _background;
                    return ListTile(
                      leading: ClipRRect(
                        borderRadius: BorderRadius.circular(6),
                        child: Image.asset(
                          'assets/backgrounds/$file',
                          width: 44, height: 44, fit: BoxFit.cover,
                          errorBuilder: (_, __, ___) => Container(
                            width: 44, height: 44,
                            color: t.colorScheme.surfaceContainerHighest,
                          ),
                        ),
                      ),
                      title: Text(b['nama'] as String),
                      trailing: aktif
                          ? Icon(Icons.check_circle, color: t.colorScheme.primary)
                          : null,
                      onTap: () {
                        setState(() => _background = file);
                        Navigator.pop(c);
                      },
                    );
                  },
                ),
              ),
            ]),
          ),
        );
      },
    );
  }

  /// Pilih model Live2D (8 model resmi, dibawa di APK).
  Future<void> _dialogModel() async {
    await showModalBottomSheet(
      context: context,
      showDragHandle: true,
      builder: (c) {
        final t = Theme.of(c);
        return SafeArea(
          child: Column(mainAxisSize: MainAxisSize.min, children: [
            Padding(
              padding: const EdgeInsets.all(AppSpacing.md),
              child: Row(children: [
                const Icon(Icons.auto_awesome),
                const SizedBox(width: 8),
                Text('Pilih Karakter VTuber', style: t.textTheme.titleMedium),
              ]),
            ),
            Flexible(
              child: ListView.builder(
                shrinkWrap: true,
                itemCount: _daftarModel.length,
                itemBuilder: (c2, i) {
                  final m = _daftarModel[i];
                  final id = m['id'] as String;
                  final aktif = id == _modelId;
                  return ListTile(
                    leading: CircleAvatar(
                      backgroundColor: aktif
                          ? t.colorScheme.primary
                          : t.colorScheme.surfaceContainerHighest,
                      child: Text('${i + 1}',
                          style: TextStyle(
                              color: aktif ? Colors.white : null,
                              fontWeight: FontWeight.bold)),
                    ),
                    title: Text(m['nama'] as String),
                    subtitle: Text(m['ket'] as String),
                    trailing: aktif
                        ? Icon(Icons.check_circle, color: t.colorScheme.primary)
                        : null,
                    onTap: () {
                      setState(() => _modelId = id);
                      _muatSuaraKarakter(id);
                      Navigator.pop(c);
                    },
                  );
                },
              ),
            ),
            const SizedBox(height: AppSpacing.sm),
          ]),
        );
      },
    );
  }

  Future<void> _dialogSuara() async {
    final suara = ['id-ID', 'en-US', 'ja-JP', 'zh-CN', 'ko-KR'];
    await showDialog(
      context: context,
      builder: (c) => AlertDialog(
        title: const Text('Pengaturan Suara'),
        content: StatefulBuilder(builder: (c, setD) => Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            const Text('Bahasa suara', style: TextStyle(fontSize: 12)),
            const SizedBox(height: 6),
            DropdownButton<String>(
              value: _suaraPilihan,
              isExpanded: true,
              items: [for (final s in suara) DropdownMenuItem(value: s, child: Text(s))],
              onChanged: (v) {
                if (v == null) return;
                setD(() => _suaraPilihan = v);
                setState(() => _suaraPilihan = v);
                _tts.setLanguage(v);
              },
            ),
            const SizedBox(height: 10),
            Text('Kecepatan: ${_kecepatan.toStringAsFixed(1)} '
                '(normal = 0.5)',
                style: const TextStyle(fontSize: 12)),
            Slider(
              value: _kecepatan, min: 0.3, max: 1.5, divisions: 24,
              onChanged: (v) {
                setD(() => _kecepatan = v);
                setState(() => _kecepatan = v);
                _tts.setSpeechRate(v);
              },
            ),
            Text('Nada: ${_nada.toStringAsFixed(1)}',
                style: const TextStyle(fontSize: 12)),
            Slider(
              value: _nada, min: 0.5, max: 2.0, divisions: 15,
              onChanged: (v) {
                setD(() => _nada = v);
                setState(() => _nada = v);
                _tts.setPitch(v);
              },
            ),
          ],
        )),
        actions: [
          TextButton(
              onPressed: () async {
                await _tts.speak('Halo, ini suara saya.');
              },
              child: const Text('Tes suara')),
          FilledButton(
              onPressed: () => Navigator.pop(c), child: const Text('Tutup')),
        ],
      ),
    );
  }
}
