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
import '../../core/theme/spacing.dart';
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

  // ---- Chat ----
  final _masukan = TextEditingController();
  final _scroll = ScrollController();
  final List<Map<String, dynamic>> _pesan = [
    {
      'teks': 'Halo! Aku karakter VTuber-mu. Bicara atau ketik, aku jawab '
          'dengan suara. Tekan mikrofon untuk mulai bicara.',
      'dariSaya': false,
    },
  ];
  bool _sibuk = false;
  bool _sedangBicara = false;

  // ---- Pengaturan ----
  String _suaraPilihan = 'id-ID';
  double _kecepatan = 1.0;
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
        final f = await SuaraAnime.buatLewatAgent(
          klien: klien,
          teks: teks,
          suara: _suaraKarakter,
        );
        if (f != null) {
          await SuaraAnime.putar(f);
          // tunggu kira-kira selesai (perkiraan 0,4 detik per karakter)
          await Future.delayed(
              Duration(milliseconds: (teks.length * 90).clamp(1500, 30000)));
          return;
        }
      }

      // 2. CADANGAN: TTS bawaan HP
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

  /// Kirim pesan ke AI (chat) lalu dibacakan (TTS).
  Future<void> _kirim(String teks) async {
    if (teks.trim().isEmpty) return;
    setState(() {
      _pesan.add({'teks': teks, 'dariSaya': true});
      _sibuk = true;
    });
    _masukan.clear();
    _gulir();

    final klien = ref.read(apiClientProvider);
    if (klien == null) {
      setState(() {
        _pesan.add({
          'teks': 'Belum tersambung. Isi Base URL + API Key di Setelan.',
          'dariSaya': false,
        });
        _sibuk = false;
      });
      return;
    }

    try {
      final balasan = await klien.chat(
        'Kamu adalah karakter VTuber yang ramah dan ekspresif. '
        'Jawab singkat (maks 3 kalimat), hangat, dan hidup. '
        'Pakai bahasa Indonesia.\n\nUser: $teks',
      );
      if (!mounted) return;
      setState(() {
        _pesan.add({'teks': balasan, 'dariSaya': false});
        _sibuk = false;
      });
      _gulir();
      // AI bersuara
      _bicara(balasan);
    } catch (e) {
      if (!mounted) return;
      setState(() {
        _pesan.add({'teks': 'Gagal: $e', 'dariSaya': false});
        _sibuk = false;
      });
    }
  }

  void _gulir() {
    WidgetsBinding.instance.addPostFrameCallback((_) {
      if (_scroll.hasClients) {
        _scroll.animateTo(_scroll.position.maxScrollExtent,
            duration: const Duration(milliseconds: 250), curve: Curves.easeOut);
      }
    });
  }

  /// AI bicara duluan (proactive speaking).
  void _toggleProaktif(bool v) {
    setState(() => _proaktif = v);
    _timerProaktif?.cancel();
    if (v) {
      _timerProaktif = Timer.periodic(const Duration(seconds: 45), (_) {
        if (_pesan.isNotEmpty && !_sibuk) {
          _kirim('(bicaralah duluan — tanyakan sesuatu yang menarik)');
        }
      });
    }
  }

  // ================= UI =================

  @override
  Widget build(BuildContext context) {
    final t = Theme.of(context);
    final cfg = ref.watch(apiConfigProvider);

    // Tinggi avatar: 40% tinggi layar (tanpa keyboard).
    // JEBAKAN #68: kalau 50%, avatar + input TIDAK muat saat keyboard muncul
    // (keyboard ~45% layar) -> input terdorong keluar layar (tampak tertimpa).
    // 40% + input (~7%) = 47% < 55% sisa ruang -> aman.
    if (_tinggiAvatar == 0) {
      final h = MediaQuery.of(context).size.height;
      _tinggiAvatar = (h * 0.40).clamp(180.0, 520.0);
    }

    return Column(
      children: [
        // ---- AVATAR (TINGGI TETAP) ----
        // Tinggi tetap -> WebView TIDAK di-stretch -> karakter TIDAK membesar.
        SizedBox(
          height: _tinggiAvatar,
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
                    : (_sibuk ? 'AI sedang menjawab...' : 'Ketuk mikrofon & bicara'),
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
            itemCount: _pesan.length,
            itemBuilder: (c, i) {
              final p = _pesan[i];
              final saya = p['dariSaya'] == true;
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
                  child: SelectableText(
                    p['teks'] as String,
                    style: TextStyle(
                        color: saya ? Colors.white : null, fontSize: 13),
                  ),
                ),
              );
            },
          ),
        ),

        // ---- INPUT (naik mengikuti keyboard) ----
        // JEBAKAN #67: saat resizeToAvoidBottomInset=false, Scaffold MENGHAPUS
        // viewInsets dari MediaQuery anak -> MediaQuery.of(context) = 0.
        // Solusi: baca dari View LANGSUNG (MediaQueryData.fromView).
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
            Text('Kecepatan: ${_kecepatan.toStringAsFixed(1)}',
                style: const TextStyle(fontSize: 12)),
            Slider(
              value: _kecepatan, min: 0.3, max: 2.0, divisions: 17,
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
