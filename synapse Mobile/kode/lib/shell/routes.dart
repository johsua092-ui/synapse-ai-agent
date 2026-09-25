import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';
import '../features/chat/chat_screen.dart';
import '../features/backup/backup_screen.dart';
import '../features/cli/cli_screen.dart';
import '../features/koneksi/koneksi_screen.dart';
import '../features/koneksi/koneksi_perangkat_screen.dart';
import '../features/mcp/mcp_screen.dart';
import '../features/notifikasi/notifikasi_screen.dart';
import '../features/perangkat/perangkat_screen.dart';
import '../features/otonom/otonom_screen.dart';
import '../features/sesi/sesi_screen.dart';
import '../features/settings/settings_screen.dart';
import '../features/skills/skills_screen.dart';
import '../features/status/status_screen.dart';
import '../features/update/update_screen.dart';
import 'app_shell.dart';

/// Semua rute aplikasi (go_router).
final router = GoRouter(
  initialLocation: '/chat',
  routes: [
    ShellRoute(
      builder: (context, state, child) => AppShell(child: child),
      routes: [
        GoRoute(path: '/chat', builder: (c, s) => const ChatScreen()),
        GoRoute(path: '/skills', builder: (c, s) => const SkillsScreen()),
        GoRoute(path: '/mcp', builder: (c, s) => const McpScreen()),
        GoRoute(path: '/cli', builder: (c, s) => const CliScreen()),
        GoRoute(path: '/koneksi', builder: (c, s) => const KoneksiScreen()),
        GoRoute(
            path: '/koneksi-perangkat',
            builder: (c, s) => const KoneksiPerangkatScreen()),
        GoRoute(path: '/update', builder: (c, s) => const UpdateScreen()),
        GoRoute(path: '/status', builder: (c, s) => const StatusScreen()),
        GoRoute(path: '/settings', builder: (c, s) => const SettingsScreen()),
        GoRoute(path: '/sesi', builder: (c, s) => const SesiScreen()),
        GoRoute(path: '/backup', builder: (c, s) => const BackupScreen()),
        GoRoute(path: '/perangkat', builder: (c, s) => const PerangkatScreen()),
        GoRoute(path: '/otonom', builder: (c, s) => const OtonomScreen()),
        GoRoute(path: '/notifikasi', builder: (c, s) => const NotifikasiScreen()),
      ],
    ),
  ],
);
