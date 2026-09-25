import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../core/theme/spacing.dart';

/// MCP (Model Context Protocol) — "jantung" kata tim.
/// Daftar server MCP + status + tombol tambah/hapus.
class McpScreen extends ConsumerStatefulWidget {
  const McpScreen({super.key});
  @override
  ConsumerState<McpScreen> createState() => _McpScreenState();
}

class _McpScreenState extends ConsumerState<McpScreen> {
  /// Katalog MCP bawaan (dari repo Synapse: optional-mcps/)
  static const _katalog = <Map<String, String>>[
    {'nama': 'airtable', 'desk': 'Database Airtable: baca/tulis record, tabel, view.'},
    {'nama': 'asana', 'desk': 'Manajemen tugas Asana: proyek, task, assignment.'},
    {'nama': 'atlassian', 'desk': 'Jira & Confluence: issue, sprint, dokumen.'},
    {'nama': 'comfy-cloud', 'desk': 'ComfyUI Cloud: workflow gambar generatif.'},
    {'nama': 'datadog', 'desk': 'Monitoring & log Datadog: metrik, alert, trace.'},
    {'nama': 'figma', 'desk': 'Figma: baca file, komponen, komentar desain.'},
    {'nama': 'hugging_face', 'desk': 'Hugging Face: model, dataset, Space.'},
    {'nama': 'intercom', 'desk': 'Intercom: percakapan pelanggan, tiket.'},
    {'nama': 'linear', 'desk': 'Linear: issue, siklus, proyek tim.'},
    {'nama': 'n8n', 'desk': 'n8n: jalankan workflow otomasi.'},
    {'nama': 'netlify', 'desk': 'Netlify: deploy situs, kelola build.'},
    {'nama': 'notion', 'desk': 'Notion: halaman, database, pencarian.'},
    {'nama': 'paypal', 'desk': 'PayPal: transaksi, invoice.'},
    {'nama': 'sentry', 'desk': 'Sentry: error tracking, issue, release.'},
    {'nama': 'square', 'desk': 'Square: pembayaran, katalog, pelanggan.'},
  ];

  final Set<String> _aktif = {};

  @override
  Widget build(BuildContext context) {
    final t = Theme.of(context);
    return Scaffold(
      appBar: AppBar(
        title: const Text('MCP Server'),
        actions: [
          Padding(
            padding: const EdgeInsets.only(right: 12),
            child: Center(
              child: Chip(
                label: Text('${_aktif.length} aktif'),
                backgroundColor: t.colorScheme.surfaceContainerHighest,
              ),
            ),
          ),
        ],
      ),
      body: ListView(
      padding: const EdgeInsets.all(AppSpacing.md),
      children: [
        Text(
          'Model Context Protocol — menghubungkan Synapse ke layanan luar.',
          style: t.textTheme.bodySmall,
        ),
        const SizedBox(height: AppSpacing.lg),
        ..._katalog.map((m) {
          final nama = m['nama']!;
          final on = _aktif.contains(nama);
          return Card(
            margin: const EdgeInsets.only(bottom: AppSpacing.sm),
            child: SwitchListTile(
              value: on,
              onChanged: (v) => setState(() {
                if (v) { _aktif.add(nama); } else { _aktif.remove(nama); }
              }),
              secondary: Icon(on ? Icons.hub : Icons.hub_outlined,
                  color: on ? t.colorScheme.primary : null),
              title: Text(nama, style: t.textTheme.titleSmall),
              subtitle: Text(m['desk']!, style: t.textTheme.bodySmall),
            ),
          );
        }),
      ],
      ),
    );
  }
}
