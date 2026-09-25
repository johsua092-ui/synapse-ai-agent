import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:shared_preferences/shared_preferences.dart';

/// Hanya 2 mode: Terang dan Gelap.
/// Default = TERANG (bukan ikut sistem).
enum AppThemeChoice { light, dark }

class ThemeModeNotifier extends StateNotifier<AppThemeChoice> {
  /// Default TERANG.
  ThemeModeNotifier() : super(AppThemeChoice.light) {
    _muat();
  }

  static const _kunci = 'theme_choice';

  Future<void> _muat() async {
    try {
      final prefs = await SharedPreferences.getInstance();
      final v = prefs.getString(_kunci);
      if (v != null) {
        state = v == 'dark' ? AppThemeChoice.dark : AppThemeChoice.light;
      }
    } catch (_) {
      // tetap pakai default terang
    }
  }

  Future<void> set(AppThemeChoice c) async {
    state = c;
    try {
      final prefs = await SharedPreferences.getInstance();
      await prefs.setString(_kunci, c.name);
    } catch (_) {}
  }

  ThemeMode get themeMode =>
      state == AppThemeChoice.dark ? ThemeMode.dark : ThemeMode.light;
}

final themeChoiceProvider =
    StateNotifierProvider<ThemeModeNotifier, AppThemeChoice>(
  (ref) => ThemeModeNotifier(),
);

String labelTema(AppThemeChoice c) =>
    c == AppThemeChoice.dark ? 'Gelap' : 'Terang';
