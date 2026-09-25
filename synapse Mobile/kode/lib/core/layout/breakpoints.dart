import 'package:flutter/widgets.dart';

/// Ambang & klasifikasi orientasi layar.
///
/// ATURAN (dari aturan PAM Bagian 2 & 3):
///   - 9:16  (potrait)  -> tata letak 1 kolom + navigasi BAWAH
///   - 16:9  (landscape)-> tata letak 2 kolom + navigasi SAMPING
class Breakpoints {
  Breakpoints._();

  /// Lebar minimum untuk dianggap "layar lebar" (tablet/landscape besar).
  static const double wide = 720;

  /// Apakah perangkat sedang landscape?
  static bool isLandscape(BuildContext c) =>
      MediaQuery.of(c).size.width > MediaQuery.of(c).size.height;

  /// Apakah layar cukup lebar untuk 2 kolom?
  static bool useTwoPane(BuildContext c) {
    final size = MediaQuery.of(c).size;
    return size.width >= wide && size.width > size.height;
  }

  /// Rasio layar (untuk info/debug).
  static String ratioLabel(BuildContext c) {
    final s = MediaQuery.of(c).size;
    final r = s.width / s.height;
    if ((r - 9 / 16).abs() < 0.05) return '9:16 (potrait)';
    if ((r - 16 / 9).abs() < 0.05) return '16:9 (landscape)';
    return '${r.toStringAsFixed(2)}:1';
  }
}
