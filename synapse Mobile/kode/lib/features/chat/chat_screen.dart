import 'dart:io';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:image_picker/image_picker.dart';
import 'package:file_picker/file_picker.dart';
import '../../core/api/api_config.dart';
import '../../core/api/api_providers.dart';
import '../../core/sesi/sesi_model.dart';
import '../../core/sesi/sesi_provider.dart';
import '../../core/theme/spacing.dart';
import '../../core/tugas/tugas_latar.dart';
import '../sesi/sesi_drawer.dart';

/// Layar Chat — permukaan utama.
/// Bisa kirim TEKS, GAMBAR, DOKUMEN. Percakapan disimpan sebagai SESI.
class ChatScreen extends ConsumerStatefulWidget {
  const ChatScreen({super.key});
  @override
  ConsumerState<ChatScreen> createState() => _ChatScreenState();
}

class _ChatScreenState extends ConsumerState<ChatScreen> with WidgetsBindingObserver {
  final _drawerKey = GlobalKey<ScaffoldState>();
  final _masukan = TextEditingController();
  final _scroll = ScrollController();
  bool _sibuk = false;
  File? _lampiran;
  String? _sesiId;

  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addObserver(this);
    WidgetsBinding.instance.addPostFrameCallback((_) async {
      final n = ref.read(sesiProvider.notifier);
      await n.siap(); // tunggu data dari penyimpanan selesai dimuat
      if (!mounted) return;
      if (ref.read(sesiProvider).isEmpty) {
        n.buatBaru();
      }
      if (mounted) {
        setState(() => _sesiId = n.aktifId ?? ref.read(sesiProvider).first.id);
      }
    });
  }

  @override
  void dispose() {
    WidgetsBinding.instance.removeObserver(this);
    _masukan.dispose();
    _scroll.dispose();
    super.dispose();
  }

  void _keBawah() {
    Future.delayed(const Duration(milliseconds: 60), () {
      if (_scroll.hasClients) {
        _scroll.animateTo(_scroll.position.maxScrollExtent,
            duration: const Duration(milliseconds: 200), curve: Curves.easeOut);
      }
    });
  }

  List<Map<String, dynamic>> _riwayat(List<Pesan> pesan) => pesan
      .where((p) => p.namaFile == null)
      .map((p) => {'role': p.dariSaya ? 'user' : 'assistant', 'content': p.teks})
      .toList();

  Future<void> _pilihGambar(bool kamera) async {
    try {
      final x = await ImagePicker().pickImage(
        source: kamera ? ImageSource.camera : ImageSource.gallery,
        maxWidth: 1600,
        imageQuality: 85,
      );
      if (x == null) return;
      setState(() => _lampiran = File(x.path));
    } catch (e) {
      if (!mounted) return;
      ScaffoldMessenger.of(context)
          .showSnackBar(SnackBar(content: Text('Gagal ambil gambar: $e')));
    }
  }

  Future<void> _pilihDokumen() async {
    try {
      final r = await FilePicker.platform.pickFiles(
        type: FileType.custom,
        allowedExtensions: [
          'txt', 'md', 'json', 'csv', 'xml', 'yaml', 'yml', 'log',
          'dart', 'py', 'js', 'html', 'css', 'java', 'kt', 'c', 'cpp', 'sql',
        ],
      );
      final path = r?.files.single.path;
      if (path == null) return;
      setState(() => _lampiran = File(path));
    } catch (e) {
      if (!mounted) return;
      ScaffoldMessenger.of(context)
          .showSnackBar(SnackBar(content: Text('Gagal ambil dokumen: $e')));
    }
  }

  /// Kirim tugas untuk dikerjakan di LATAR BELAKANG (notif saat selesai).
  Future<void> _kerjakanLatar() async {
    FocusScope.of(context).unfocus();   // tutup keyboard dulu
    final teks = _masukan.text.trim();
    if (teks.isEmpty) {
      ScaffoldMessenger.of(context).showSnackBar(const SnackBar(
          content: Text('Tulis dulu tugasnya, lalu pilih ini.')));
      return;
    }
    final klien = ref.read(apiClientProvider);
    final cfg = ref.read(apiConfigProvider);
    if (klien == null || !cfg.terisi) {
      ScaffoldMessenger.of(context).showSnackBar(const SnackBar(
          content: Text('Belum tersambung. Isi Base URL + API Key dulu.')));
      return;
    }

    final n = ref.read(sesiProvider.notifier);
    var id = _sesiId ?? '';
    if (id.isEmpty) {
      id = n.buatBaru();
      _sesiId = id;
    }

    try {
      final runId = await TugasLatar.mulai(input: teks, cfg: cfg);
      n.tambahPesan(id, Pesan(teks: teks, dariSaya: true));
      n.tambahPesan(id, Pesan(
          teks: '(dikerjakan di latar belakang — notifikasi akan muncul '
              'saat selesai. Tutup app pun tetap jalan.)'));
      setState(() => _masukan.clear());
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(SnackBar(
        content: Text('Berjalan di latar belakang (id: ${runId?.substring(0, 12)}...)'),
        duration: const Duration(seconds: 4),
      ));
    } catch (e) {
      if (!mounted) return;
      ScaffoldMessenger.of(context)
          .showSnackBar(SnackBar(content: Text('Gagal: $e')));
    }
  }

  Future<void> _kirim() async {
    final teks = _masukan.text.trim();
    final lamp = _lampiran;
    if ((teks.isEmpty && lamp == null) || _sibuk) return;

    final klien = ref.read(apiClientProvider);
    if (klien == null) {
      ScaffoldMessenger.of(context).showSnackBar(const SnackBar(
          content: Text('Belum tersambung. Isi Base URL + API Key di Setelan.')));
      return;
    }

    final n = ref.read(sesiProvider.notifier);
    String id = _sesiId ?? '';
    if (id.isEmpty) {
      id = n.buatBaru();
      _sesiId = id;
    }

    final namaLamp = lamp?.path.split(RegExp(r'[\\/]')).last;
    final isGambar = lamp != null &&
        RegExp(r'\.(png|jpe?g|webp|gif|bmp)$', caseSensitive: false)
            .hasMatch(lamp.path);

    // riwayat SEBELUM menambah pesan baru
    final pesanLama = [...(n.state.firstWhere((s) => s.id == id,
            orElse: () => Sesi(id: id, judul: '')).pesan)];

    setState(() {
      _sibuk = true;
      _masukan.clear();
      _lampiran = null;
    });

    n.tambahPesan(
        id,
        Pesan(
          teks: teks.isEmpty ? '(lampiran)' : teks,
          dariSaya: true,
          namaFile: namaLamp,
          gambar: isGambar,
        ));
    n.tambahPesan(id, Pesan(teks: '', dariSaya: false));
    _keBawah();

    final buffer = StringBuffer();
    try {
      final Stream<String> aliran = lamp == null
          ? klien.chatStream(teks, riwayat: _riwayat(pesanLama))
          : isGambar
              ? klien.chatGambar(lamp, teks, riwayat: _riwayat(pesanLama))
              : klien.chatDokumen(lamp, teks);

      await for (final potongan in aliran) {
        buffer.write(potongan);
        if (!mounted) return;
        setState(() {
          n.gantiTerakhir(id, Pesan(teks: buffer.toString()));
        });
        _keBawah();
      }
      if (!mounted) return;
      setState(() {
        n.gantiTerakhir(
            id!, Pesan(teks: buffer.isEmpty ? '(balasan kosong)' : buffer.toString()));
        n.simpanKeDisk(id);
        _sibuk = false;
      });
    } catch (e) {
      if (!mounted) return;
      setState(() {
        n.gantiTerakhir(id, Pesan(teks: 'Gagal: $e'));
        n.simpanKeDisk(id);
        _sibuk = false;
      });
    }
    _keBawah();
  }

  @override
  void didChangeMetrics() {
    if (mounted) setState(() {});
  }

  @override
  Widget build(BuildContext context) {
    final t = Theme.of(context);
    final cfg = ref.watch(apiConfigProvider);
    final tersambung = cfg.terisi;
    final semua = ref.watch(sesiProvider);
    final n = ref.read(sesiProvider.notifier);

    // sinkronkan sesi aktif
    if (n.aktifId != null && n.aktifId != _sesiId) {
      WidgetsBinding.instance.addPostFrameCallback((_) {
        if (mounted) setState(() => _sesiId = n.aktifId);
      });
    }
    final sesi = semua.where((s) => s.id == _sesiId).toList();
    final pesan = sesi.isEmpty ? <Pesan>[] : sesi.first.pesan;

    return Scaffold(
      key: _drawerKey,
      drawer: const SesiDrawer(),
      appBar: AppBar(
        title: const Text('Synapse'),
        leading: IconButton(
          tooltip: 'Daftar sesi',
          icon: const Icon(Icons.menu),
          onPressed: () => _drawerKey.currentState?.openDrawer(),
        ),
        actions: [
          IconButton(
            tooltip: 'Kerjakan di latar belakang',
            icon: const Icon(Icons.schedule_send_outlined),
            onPressed: _kerjakanLatar,
          ),
          IconButton(
            tooltip: 'Sesi baru',
            icon: const Icon(Icons.add_comment_outlined),
            onPressed: () => setState(() => _sesiId = n.buatBaru()),
          ),
          Padding(
            padding: const EdgeInsets.only(right: 8),
            child: Center(
              child: Row(children: [
                Icon(tersambung ? Icons.cloud_done : Icons.cloud_off,
                    size: 16,
                    color: tersambung ? Colors.green : t.colorScheme.outline),
                const SizedBox(width: 4),
                Text(cfg.model ?? (tersambung ? 'siap' : 'offline'),
                    style: t.textTheme.bodySmall),
              ]),
            ),
          ),
        ],
      ),
      body: Column(
        children: [
          Expanded(
            child: pesan.isEmpty
                ? _kosong(t, tersambung)
                : ListView.builder(
                    controller: _scroll,
                    padding: const EdgeInsets.all(AppSpacing.md),
                    itemCount: pesan.length,
                    itemBuilder: (c, i) => _gelembung(t, pesan[i]),
                  ),
          ),
          if (_lampiran != null)
            Container(
              padding: const EdgeInsets.symmetric(
                  horizontal: AppSpacing.md, vertical: 8),
              color: t.colorScheme.surfaceContainerHighest,
              child: Row(children: [
                Icon(Icons.attach_file, size: 16, color: t.colorScheme.primary),
                const SizedBox(width: 8),
                Expanded(
                  child: Text(
                    _lampiran!.path.split(RegExp(r'[\\/]')).last,
                    style: t.textTheme.bodySmall,
                    overflow: TextOverflow.ellipsis,
                  ),
                ),
                IconButton(
                  icon: const Icon(Icons.close, size: 18),
                  onPressed: () => setState(() => _lampiran = null),
                ),
              ]),
            ),
          SafeArea(
            top: false,
            child: Container(
              // JEBAKAN #67: naikkan input mengikuti keyboard.
              // resizeToAvoidBottomInset=false -> viewInsets dibaca dari View.
              padding: const EdgeInsets.symmetric(
                  horizontal: AppSpacing.sm, vertical: AppSpacing.sm),
              decoration: BoxDecoration(
                  border: Border(top: BorderSide(color: t.dividerColor))),
              child: Row(children: [
                PopupMenuButton<String>(
                  icon: const Icon(Icons.add_circle_outline),
                  tooltip: 'Lampiran',
                  onSelected: (v) {
                    if (v == 'galeri') _pilihGambar(false);
                    if (v == 'kamera') _pilihGambar(true);
                    if (v == 'dokumen') _pilihDokumen();
                    if (v == 'latar') _kerjakanLatar();
                  },
                  itemBuilder: (c) => const [
                    PopupMenuItem(
                      value: 'galeri',
                      child: ListTile(
                        dense: true,
                        leading: Icon(Icons.photo_library),
                        title: Text('Gambar (galeri)'),
                      ),
                    ),
                    PopupMenuItem(
                      value: 'kamera',
                      child: ListTile(
                        dense: true,
                        leading: Icon(Icons.camera_alt),
                        title: Text('Kamera'),
                      ),
                    ),
                    PopupMenuItem(
                      value: 'dokumen',
                      child: ListTile(
                        dense: true,
                        leading: Icon(Icons.description),
                        title: Text('Dokumen'),
                      ),
                    ),
                    PopupMenuItem(
                      value: 'latar',
                      child: ListTile(
                        dense: true,
                        leading: Icon(Icons.schedule_send),
                        title: Text('Kerjakan di latar belakang'),
                        subtitle: Text('Notif muncul saat selesai',
                            style: TextStyle(fontSize: 11)),
                      ),
                    ),
                  ],
                ),
                Expanded(
                  child: TextField(
                    controller: _masukan,
                    maxLines: 1,
                    textInputAction: TextInputAction.send,
                    onSubmitted: (_) => _kirim(),
                    decoration: const InputDecoration(
                      hintText: 'Tulis pesan...',
                      border: InputBorder.none,
                    ),
                  ),
                ),
                IconButton(
                  onPressed: _sibuk ? null : _kirim,
                  icon: _sibuk
                      ? const SizedBox(
                          width: 20,
                          height: 20,
                          child: CircularProgressIndicator(strokeWidth: 2))
                      : const Icon(Icons.send),
                ),
              ]),
            ),
          ),
        ],
      ),
    );
  }

  Widget _kosong(ThemeData t, bool tersambung) => Center(
        child: Padding(
          padding: const EdgeInsets.all(AppSpacing.lg),
          child: Column(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              Icon(Icons.chat_bubble_outline,
                  size: 48, color: t.colorScheme.outline),
              const SizedBox(height: AppSpacing.md),
              Text(
                tersambung
                    ? 'Mulai percakapan dengan Synapse.\nKetik pesan, atau lampirkan gambar/dokumen\nlewat tombol + di kiri.'
                    : 'Belum tersambung.\nIsi Base URL + API Key di Setelan.',
                textAlign: TextAlign.center,
                style: t.textTheme.bodyMedium,
              ),
            ],
          ),
        ),
      );

  Widget _gelembung(ThemeData t, Pesan p) {
    final saya = p.dariSaya;
    final kosong = p.teks.isEmpty;
    return Align(
      alignment: saya ? Alignment.centerRight : Alignment.centerLeft,
      child: Container(
        margin: const EdgeInsets.only(bottom: AppSpacing.sm),
        padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 10),
        constraints:
            BoxConstraints(maxWidth: MediaQuery.sizeOf(context).width * 0.80),
        decoration: BoxDecoration(
          color: saya
              ? t.colorScheme.primary
              : t.colorScheme.surfaceContainerHighest,
          borderRadius: BorderRadius.circular(14),
        ),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          mainAxisSize: MainAxisSize.min,
          children: [
            if (p.namaFile != null)
              Row(mainAxisSize: MainAxisSize.min, children: [
                Icon(p.gambar ? Icons.image : Icons.description,
                    size: 14,
                    color:
                        saya ? t.colorScheme.onPrimary : t.colorScheme.primary),
                const SizedBox(width: 4),
                Text(
                  p.namaFile!,
                  style: t.textTheme.bodySmall?.copyWith(
                    color: saya ? t.colorScheme.onPrimary : null,
                    fontWeight: FontWeight.w600,
                  ),
                ),
              ]),
            if (p.namaFile != null && p.teks.isNotEmpty)
              const SizedBox(height: 4),
            kosong
                ? SizedBox(
                    width: 40,
                    child: Row(mainAxisSize: MainAxisSize.min, children: [
                      _titik(t), const SizedBox(width: 4),
                      _titik(t), const SizedBox(width: 4),
                      _titik(t),
                    ]),
                  )
                : SelectableText(
                    p.teks,
                    style: t.textTheme.bodyMedium?.copyWith(
                      color: saya ? t.colorScheme.onPrimary : null,
                    ),
                  ),
          ],
        ),
      ),
    );
  }

  Widget _titik(ThemeData t) => Container(
        width: 6,
        height: 6,
        decoration:
            BoxDecoration(color: t.colorScheme.outline, shape: BoxShape.circle),
      );
}
