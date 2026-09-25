import 'dart:convert';

/// Satu pesan dalam sesi.
class Pesan {
  final String teks;
  final bool dariSaya;
  final String? namaFile;
  final bool gambar;
  final DateTime waktu;

  Pesan({
    required this.teks,
    this.dariSaya = false,
    this.namaFile,
    this.gambar = false,
    DateTime? waktu,
  }) : waktu = waktu ?? DateTime.now();

  Map<String, dynamic> toJson() => {
        'teks': teks,
        'dariSaya': dariSaya,
        'namaFile': namaFile,
        'gambar': gambar,
        'waktu': waktu.toIso8601String(),
      };

  factory Pesan.fromJson(Map<String, dynamic> j) => Pesan(
        teks: (j['teks'] ?? '').toString(),
        dariSaya: j['dariSaya'] == true,
        namaFile: j['namaFile']?.toString(),
        gambar: j['gambar'] == true,
        waktu: DateTime.tryParse((j['waktu'] ?? '').toString()) ?? DateTime.now(),
      );
}

/// Satu sesi percakapan.
class Sesi {
  final String id;
  String judul;
  bool dipin;
  final List<Pesan> pesan;
  DateTime diperbarui;

  Sesi({
    required this.id,
    required this.judul,
    this.dipin = false,
    List<Pesan>? pesan,
    DateTime? diperbarui,
  })  : pesan = pesan ?? [],
        diperbarui = diperbarui ?? DateTime.now();

  /// Judul otomatis dari pesan pertama.
  String get judulTampil {
    if (judul.trim().isNotEmpty) return judul;
    final p = pesan.firstWhere((x) => x.dariSaya, orElse: () => Pesan(teks: ''));
    final t = p.teks.trim();
    if (t.isEmpty) return 'Percakapan baru';
    return t.length > 40 ? '${t.substring(0, 40)}...' : t;
  }

  /// Cuplikan pesan terakhir (untuk daftar).
  String get cuplikan {
    if (pesan.isEmpty) return 'Belum ada pesan';
    final t = pesan.last.teks.trim();
    if (t.isEmpty) return 'Belum ada pesan';
    return t.length > 50 ? '${t.substring(0, 50)}...' : t;
  }

  Map<String, dynamic> toJson() => {
        'id': id,
        'judul': judul,
        'dipin': dipin,
        'pesan': pesan.map((e) => e.toJson()).toList(),
        'diperbarui': diperbarui.toIso8601String(),
      };

  factory Sesi.fromJson(Map<String, dynamic> j) => Sesi(
        id: (j['id'] ?? '').toString(),
        judul: (j['judul'] ?? '').toString(),
        dipin: j['dipin'] == true,
        pesan: ((j['pesan'] as List?) ?? const [])
            .map((e) => Pesan.fromJson(e as Map<String, dynamic>))
            .toList(),
        diperbarui:
            DateTime.tryParse((j['diperbarui'] ?? '').toString()) ?? DateTime.now(),
      );

  String keJson() => jsonEncode(toJson());
  static Sesi dariJson(String s) =>
      Sesi.fromJson(jsonDecode(s) as Map<String, dynamic>);
}
