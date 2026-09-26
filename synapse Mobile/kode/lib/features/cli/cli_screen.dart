import 'dart:convert';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../core/api/api_config.dart';
import '../../core/api/api_providers.dart';
import '../../core/theme/spacing.dart';

/// Mode Synapse CLI — terminal mini di dalam HP.
///
/// PENTING (perbaikan v1.2.1):
///   Versi lama PALSU — hanya mengembalikan teks hardcode
///   (`if contains 'version' return 'synapse-agent 0.20.5'`), tidak pernah
///   menjalankan perintah sungguhan.
///   Sekarang: perintah DIKIRIM KE AGENT dan dijalankan di laptop,
///   lalu hasilnya ditampilkan.
class CliScreen extends ConsumerStatefulWidget {
  const CliScreen({super.key});
  @override
  ConsumerState<CliScreen> createState() => _CliScreenState();
}

class _CliScreenState extends ConsumerState<CliScreen> {
  final _in = TextEditingController();
  final _scroll = ScrollController();
  final List<Map<String, String>> _riwayat = [];
  bool _sibuk = false;

  @override
  void initState() {
    super.initState();
    _riwayat.addAll([
      {'t': 'out', 'v': 'Synapse CLI (mobile) — terhubung ke agent laptop'},
      {'t': 'out', 'v': 'Ketik perintah terminal, mis. "synapse gateway status"'},
      {'t': 'out', 'v': 'Perintah dijalankan di LAPTOP, hasilnya tampil di sini.'},
      {'t': 'out', 'v': ''},
    ]);
  }

  Future<void> _kirim() async {
    final cmd = _in.text.trim();
    if (cmd.isEmpty || _sibuk) return;

    // perintah lokal (tidak perlu agent)
    if (cmd.toLowerCase() == 'clear' || cmd.toLowerCase() == 'cls') {
      setState(() {
        _riwayat.clear();
        _riwayat.add({'t': 'out', 'v': ''});
      });
      _in.clear();
      return;
    }

    setState(() {
      _riwayat.add({'t': 'in', 'v': '\$ $cmd'});
      _riwayat.add({'t': 'out', 'v': 'menjalankan di laptop...'});
      _sibuk = true;
      _in.clear();
    });
    _gulir();

    String hasil;
    try {
      final klien = ref.read(apiClientProvider);
      if (klien == null) {
        hasil = 'Gagal: belum tersambung. Isi Base URL + API Key di Setelan.';
      } else {
        // kirim ke agent: dijalankan di laptop, hasilnya dikembalikan
        final r = await klien.perintahAgent(cmd);
        hasil = r.trim().isEmpty ? '(tidak ada output)' : r.trim();
      }
    } catch (e) {
      hasil = 'Gagal: $e';
    }

    if (!mounted) return;
    setState(() {
      _riwayat.removeLast();            // buang "menjalankan..."
      _riwayat.add({'t': 'out', 'v': hasil});
      _riwayat.add({'t': 'out', 'v': ''});
      _sibuk = false;
    });
    _gulir();
  }

  void _gulir() {
    Future.delayed(const Duration(milliseconds: 60), () {
      if (_scroll.hasClients) {
        _scroll.animateTo(_scroll.position.maxScrollExtent,
            duration: const Duration(milliseconds: 200), curve: Curves.easeOut);
      }
    });
  }

  @override
  void dispose() {
    _in.dispose();
    _scroll.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final cfg = ref.watch(apiConfigProvider);
    return Scaffold(
      appBar: AppBar(
        title: const Text('Synapse CLI'),
        actions: [
          IconButton(
            tooltip: 'Bersihkan layar',
            icon: const Icon(Icons.delete_sweep_outlined),
            onPressed: () => setState(() {
              _riwayat.clear();
              _riwayat.add({'t': 'out', 'v': ''});
            }),
          ),
        ],
      ),
      body: Column(children: [
        // status koneksi
        Container(
          width: double.infinity,
          padding: const EdgeInsets.symmetric(
              horizontal: AppSpacing.md, vertical: 6),
          color: cfg.terisi
              ? Colors.green.withValues(alpha: 0.15)
              : Colors.orange.withValues(alpha: 0.15),
          child: Text(
            cfg.terisi
                ? 'Terhubung ke agent (${cfg.baseUrl})'
                : 'Belum tersambung — isi Base URL + API Key di Setelan',
            style: const TextStyle(fontSize: 11),
          ),
        ),
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
                return SelectableText(
                  r['v']!,
                  style: TextStyle(
                    fontFamily: 'monospace',
                    fontSize: 13,
                    height: 1.4,
                    color: masuk
                        ? const Color(0xFF7CE38B)
                        : const Color(0xFFD8DEE9),
                  ),
                );
              },
            ),
          ),
        ),
        if (_sibuk)
          const LinearProgressIndicator(minHeight: 2),
        SafeArea(
          top: false,
          child: Container(
            color: const Color(0xFF15151A),
            padding: const EdgeInsets.symmetric(
                horizontal: AppSpacing.sm, vertical: 6),
            child: Row(children: [
              const Padding(
                padding: EdgeInsets.symmetric(horizontal: 8),
                child: Text('\$',
                    style: TextStyle(
                        fontFamily: 'monospace',
                        color: Color(0xFF7CE38B),
                        fontSize: 15)),
              ),
              Expanded(
                child: TextField(
                  controller: _in,
                  onSubmitted: (_) => _kirim(),
                  enabled: !_sibuk,
                  style: const TextStyle(
                      fontFamily: 'monospace',
                      color: Color(0xFFD8DEE9),
                      fontSize: 14),
                  decoration: const InputDecoration(
                    hintText: 'ketik perintah...',
                    hintStyle: TextStyle(
                        color: Color(0xFF6B7280), fontFamily: 'monospace'),
                    border: InputBorder.none,
                    isDense: true,
                  ),
                ),
              ),
              IconButton(
                onPressed: _sibuk ? null : _kirim,
                icon: Icon(_sibuk ? Icons.hourglass_top : Icons.send,
                    color: const Color(0xFF7CE38B)),
              ),
            ]),
          ),
        ),
      ]),
    );
  }
}
