import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../core/theme/spacing.dart';

/// Mode Synapse CLI — terminal mini di dalam HP.
/// "seolah sedang di laptop" kata tim.
class CliScreen extends ConsumerStatefulWidget {
  const CliScreen({super.key});
  @override
  ConsumerState<CliScreen> createState() => _CliScreenState();
}

class _CliScreenState extends ConsumerState<CliScreen> {
  final _in = TextEditingController();
  final _scroll = ScrollController();
  final List<Map<String, String>> _riwayat = [
    {'t': 'out', 'v': 'Synapse CLI v0.20.5  (mobile)'},
    {'t': 'out', 'v': 'Ketik perintah, mis. "synapse gateway status"'},
    {'t': 'out', 'v': ''},
  ];

  void _kirim() {
    final cmd = _in.text.trim();
    if (cmd.isEmpty) return;
    setState(() {
      _riwayat.add({'t': 'in', 'v': '\$ $cmd'});
      _riwayat.add({'t': 'out', 'v': _proses(cmd)});
      _riwayat.add({'t': 'out', 'v': ''});
      _in.clear();
    });
    Future.delayed(const Duration(milliseconds: 50), () {
      if (_scroll.hasClients) {
        _scroll.animateTo(_scroll.position.maxScrollExtent,
            duration: const Duration(milliseconds: 200), curve: Curves.easeOut);
      }
    });
  }

  String _proses(String cmd) {
    final c = cmd.toLowerCase();
    if (c.contains('help')) {
      return 'Perintah: status, model, skills, mcp, clear, version';
    }
    if (c.contains('version')) return 'synapse-agent 0.20.5';
    if (c.contains('status')) return 'Gateway: running\nAPI server: 8642\nModel: synapse-agent';
    if (c.contains('model')) return 'synapse-agent';
    if (c.contains('skills')) return '143 skill terpasang';
    if (c.contains('mcp')) return 'MCP: 20 tersedia';
    if (c.contains('clear')) { _riwayat.clear(); return ''; }
    return 'Perintah tidak dikenal: $cmd';
  }

  @override
  void dispose() { _in.dispose(); _scroll.dispose(); super.dispose(); }

  @override
  Widget build(BuildContext context) {
    final t = Theme.of(context);
    return Scaffold(
      appBar: AppBar(title: const Text('Synapse CLI')),
      body: Column(children: [
      Expanded(
        child: Container(
          width: double.infinity,
          color: const Color(0xFF0C0C10),
          child: ListView.builder(
            controller: _scroll,
            padding: const EdgeInsets.all(AppSpacing.md),
            itemCount: _riwayat.length,
            itemBuilder: (c, i) {
              final r = _riwayat[i];
              final masuk = r['t'] == 'in';
              return Text(
                r['v']!,
                style: TextStyle(
                  fontFamily: 'monospace',
                  fontSize: 13,
                  height: 1.4,
                  color: masuk ? const Color(0xFF7CE38B) : const Color(0xFFD8DEE9),
                ),
              );
            },
          ),
        ),
      ),
      SafeArea(
        top: false,
        child: Container(
          color: const Color(0xFF15151A),
          padding: const EdgeInsets.symmetric(horizontal: AppSpacing.sm, vertical: 6),
          child: Row(children: [
            const Padding(
              padding: EdgeInsets.symmetric(horizontal: 8),
              child: Text('\$', style: TextStyle(fontFamily: 'monospace',
                  color: Color(0xFF7CE38B), fontSize: 15)),
            ),
            Expanded(
              child: TextField(
                controller: _in,
                onSubmitted: (_) => _kirim(),
                style: const TextStyle(fontFamily: 'monospace',
                    color: Color(0xFFD8DEE9), fontSize: 14),
                decoration: const InputDecoration(
                  hintText: 'ketik perintah...',
                  hintStyle: TextStyle(color: Color(0xFF6B7280), fontFamily: 'monospace'),
                  border: InputBorder.none,
                  isDense: true,
                ),
              ),
            ),
            IconButton(
              onPressed: _kirim,
              icon: const Icon(Icons.send, color: Color(0xFF7CE38B)),
            ),
          ]),
        ),
      ),
    ]),
    );
  }
}
