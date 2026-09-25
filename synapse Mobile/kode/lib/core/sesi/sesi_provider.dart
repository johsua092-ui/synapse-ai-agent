import 'dart:convert';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'sesi_model.dart';

/// Penyimpanan & pengelolaan sesi chat (banyak sesi, pin, rename, hapus).
class SesiNotifier extends StateNotifier<List<Sesi>> {
  SesiNotifier() : super([]) {
    _muatSelesai = _muat();
  }

  /// Future pemuatan awal (ditunggu sebelum membuat sesi baru).
  late Future<void> _muatSelesai;

  /// Tunggu sampai data dari penyimpanan selesai dimuat.
  Future<void> siap() => _muatSelesai;

  static const _kunci = 'daftar_sesi';
  static const _kAktif = 'sesi_aktif';
  String? _aktifId;

  String? get aktifId => _aktifId;

  bool _sudahMuat = false;

  Future<void> _muat() async {
    final p = await SharedPreferences.getInstance();
    final raw = p.getStringList(_kunci) ?? [];
    final daftar = raw.map((e) {
      try {
        return Sesi.dariJson(e);
      } catch (_) {
        return Sesi(id: '', judul: '');
      }
    }).where((s) => s.id.isNotEmpty).toList();
    _sudahMuat = true;
    // JANGAN timpa sesi yang sudah dibuat user sebelum data selesai dimuat
    if (state.isNotEmpty) return;
    _aktifId = p.getString(_kAktif);
    state = daftar;
  }

  Future<void> _simpan() async {
    final p = await SharedPreferences.getInstance();
    await p.setStringList(_kunci, state.map((e) => e.keJson()).toList());
    if (_aktifId != null) await p.setString(_kAktif, _aktifId!);
  }

  /// Daftar untuk tampilan: dipin dulu, lalu terbaru.
  List<Sesi> get terurut {
    final l = [...state];
    l.sort((a, b) {
      if (a.dipin != b.dipin) return a.dipin ? -1 : 1;
      return b.diperbarui.compareTo(a.diperbarui);
    });
    return l;
  }

  /// Cari sesi berdasarkan judul / isi pesan.
  List<Sesi> cari(String q) {
    final k = q.trim().toLowerCase();
    if (k.isEmpty) return terurut;
    return terurut.where((s) {
      if (s.judulTampil.toLowerCase().contains(k)) return true;
      return s.pesan.any((p) => p.teks.toLowerCase().contains(k));
    }).toList();
  }

  Sesi? get aktif {
    if (_aktifId == null) return null;
    for (final s in state) {
      if (s.id == _aktifId) return s;
    }
    return null;
  }

  String buatBaru() {
    final id = DateTime.now().microsecondsSinceEpoch.toString();
    final s = Sesi(id: id, judul: '');
    state = [s, ...state];
    _aktifId = id;
    _simpan();
    return id;
  }

  void pilih(String id) {
    _aktifId = id;
    _simpan();
    state = [...state];
  }

  void tambahPesan(String id, Pesan p) {
    final i = state.indexWhere((s) => s.id == id);
    if (i < 0) return;
    state[i].pesan.add(p);
    state[i].diperbarui = DateTime.now();
    state = [...state];
    _simpan();
  }

  /// Ganti pesan terakhir (untuk streaming).
  void gantiTerakhir(String id, Pesan p) {
    final i = state.indexWhere((s) => s.id == id);
    if (i < 0 || state[i].pesan.isEmpty) return;
    state[i].pesan[state[i].pesan.length - 1] = p;
    state[i].diperbarui = DateTime.now();
    state = [...state];
  }

  void simpanKeDisk(String id) {
    _simpan();
  }

  void pin(String id) {
    final i = state.indexWhere((s) => s.id == id);
    if (i < 0) return;
    state[i].dipin = !state[i].dipin;
    state = [...state];
    _simpan();
  }

  void gantiJudul(String id, String judul) {
    final i = state.indexWhere((s) => s.id == id);
    if (i < 0) return;
    state[i].judul = judul.trim();
    state = [...state];
    _simpan();
  }

  void hapus(String id) {
    state = state.where((s) => s.id != id).toList();
    if (_aktifId == id) _aktifId = state.isEmpty ? null : state.first.id;
    _simpan();
  }

  void hapusSemua() {
    state = [];
    _aktifId = null;
    _simpan();
  }
}

final sesiProvider = StateNotifierProvider<SesiNotifier, List<Sesi>>(
  (ref) => SesiNotifier(),
);
