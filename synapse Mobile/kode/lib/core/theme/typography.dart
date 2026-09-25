import 'package:flutter/material.dart';

import 'colors.dart';

/// Skala teks (dari aturan PAM: minimal 12sp, hormati perbesar teks sistem).
class AppTypography {
  AppTypography._();

  static const String? fontFamily = null; // pakai font sistem (bisa diganti nanti)

  static const title = TextStyle(fontSize: 22, fontWeight: FontWeight.w700, color: AppColors.textPrimary);
  static const subtitle = TextStyle(fontSize: 16, fontWeight: FontWeight.w600, color: AppColors.textPrimary);
  static const body = TextStyle(fontSize: 15, fontWeight: FontWeight.w400, color: AppColors.textPrimary);
  static const caption = TextStyle(fontSize: 12, fontWeight: FontWeight.w400, color: AppColors.textTertiary);
  static const mono = TextStyle(fontSize: 13, fontFamily: 'monospace', color: AppColors.textPrimary);
}
