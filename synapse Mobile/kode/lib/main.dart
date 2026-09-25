import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import 'app.dart';

/// Titik masuk aplikasi Synapse Mobile.
///
/// [SynapseApp] ada di `app.dart` (ConsumerWidget) supaya bisa
/// membaca pilihan tema (terang/gelap/sistem) dari Riverpod.
void main() {
  runApp(const ProviderScope(child: SynapseApp()));
}
