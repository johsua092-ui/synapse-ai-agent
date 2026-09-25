import 'package:flutter/material.dart';

/// Warna resmi Synapse — HASIL UKUR `apps/desktop/src/styles.css`.
///
/// ATURAN: JANGAN bikin hex baru. Semua warna turunan dihitung dari [primary].
class AppColors {
  AppColors._();

  // ===== TEMA TERANG (dari desktop styles.css) =====
  /// Biru utama Synapse (brand).
  static const primary = Color(0xFF0053FD);
  /// Teks utama.
  static const foreground = Color(0xFF17171A);
  /// Latar layar.
  static const background = Color(0xFFF8FAFF);
  /// Latar sidebar.
  static const sidebar = Color(0xFFF3F7FF);
  /// Kartu.
  static const card = Color(0xFFFFFFFF);
  /// Panel mengambang.
  static const elevated = Color(0xFFFFFFFF);
  /// Aksen hangat.
  static const warm = Color(0xFFCF806D);
  /// Chrome netral.
  static const neutralChrome = Color(0xFFF3F3F3);

  // ===== TEKS (hierarki) =====
  static const textPrimary = Color(0xFF17171A);
  static const textSecondary = Color(0xFF5A5A63);
  static const textTertiary = Color(0xFF8E8E99);

  // ===== STATUS =====
  static const error = Color(0xFFD93025);
  static const warn = Color(0xFFE8A33D);
  static const success = Color(0xFF2E9E5B);

  // ===== TURUNAN (dihitung dari primary) =====
  /// Fill: primary dengan opasitas bertingkat (desktop: 16/11/8/5/3%).
  static Color fill1 = primary.withValues(alpha: 0.16);
  static Color fill2 = primary.withValues(alpha: 0.11);
  static Color fill3 = primary.withValues(alpha: 0.08);
  static Color fill4 = primary.withValues(alpha: 0.05);
  static Color fill5 = primary.withValues(alpha: 0.03);

  /// Stroke: primary dengan opasitas (desktop: 24/16/10/6%).
  static Color stroke1 = primary.withValues(alpha: 0.24);
  static Color stroke2 = primary.withValues(alpha: 0.16);
  static Color stroke3 = primary.withValues(alpha: 0.10);
  static Color stroke4 = primary.withValues(alpha: 0.06);

  /// Hover/active (desktop: 4-6% / 8%).
  static Color hover = primary.withValues(alpha: 0.05);
  static Color active = primary.withValues(alpha: 0.08);

  // ===== TEMA GELAP =====
  static const darkBackground = Color(0xFF0E0E12);
  static const darkSurface = Color(0xFF17171C);
  static const darkCard = Color(0xFF1E1E24);
  static const darkForeground = Color(0xFFEDEDF2);
  static const darkTextSecondary = Color(0xFFA0A0AC);
  static const darkTextTertiary = Color(0xFF6E6E7A);
  static const darkStroke = Color(0xFF2A2A32);
}
