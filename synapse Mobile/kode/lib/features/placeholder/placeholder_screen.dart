import 'package:flutter/material.dart';

import '../../core/widgets/app_states.dart';

/// Layar sementara untuk fitur yang belum dikerjakan (milestone berikutnya).
class PlaceholderScreen extends StatelessWidget {
  const PlaceholderScreen({super.key, required this.title});
  final String title;

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: Text(title)),
      body: AppEmpty(
        icon: Icons.construction_outlined,
        message: 'Fitur "$title"\nbelum dikerjakan (milestone berikutnya).',
      ),
    );
  }
}
