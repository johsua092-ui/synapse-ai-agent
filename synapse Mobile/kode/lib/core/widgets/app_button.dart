import 'package:flutter/material.dart';

import '../theme/spacing.dart';

/// SATU tombol untuk seluruh aplikasi (prinsip: satu primitif per urusan).
enum AppButtonVariant { primary, secondary, outline, ghost, destructive }

class AppButton extends StatelessWidget {
  const AppButton({
    super.key,
    required this.label,
    this.onPressed,
    this.variant = AppButtonVariant.primary,
    this.icon,
    this.expand = false,
  });

  final String label;
  final VoidCallback? onPressed;
  final AppButtonVariant variant;
  final IconData? icon;
  final bool expand;

  @override
  Widget build(BuildContext context) {
    final scheme = Theme.of(context).colorScheme;

    late final Widget child;
    late final VoidCallback? tap;

    switch (variant) {
      case AppButtonVariant.primary:
        child = ElevatedButton.icon(
          onPressed: onPressed,
          icon: icon != null ? Icon(icon, size: 18) : const SizedBox.shrink(),
          label: Text(label),
        );
        tap = () {};
      case AppButtonVariant.secondary:
        child = FilledButton.tonal(
          onPressed: onPressed,
          child: Row(mainAxisSize: MainAxisSize.min, children: [
            if (icon != null) ...[Icon(icon, size: 18), const SizedBox(width: 8)],
            Text(label),
          ]),
        );
        tap = () {};
      case AppButtonVariant.outline:
        child = OutlinedButton(
          onPressed: onPressed,
          child: Row(mainAxisSize: MainAxisSize.min, children: [
            if (icon != null) ...[Icon(icon, size: 18), const SizedBox(width: 8)],
            Text(label),
          ]),
        );
        tap = () {};
      case AppButtonVariant.ghost:
        child = TextButton(
          onPressed: onPressed,
          child: Row(mainAxisSize: MainAxisSize.min, children: [
            if (icon != null) ...[Icon(icon, size: 18), const SizedBox(width: 8)],
            Text(label),
          ]),
        );
        tap = () {};
      case AppButtonVariant.destructive:
        child = ElevatedButton(
          onPressed: onPressed,
          style: ElevatedButton.styleFrom(backgroundColor: scheme.error, foregroundColor: Colors.white),
          child: Row(mainAxisSize: MainAxisSize.min, children: [
            if (icon != null) ...[Icon(icon, size: 18), const SizedBox(width: 8)],
            Text(label),
          ]),
        );
        tap = () {};
    }

    return expand ? SizedBox(width: double.infinity, child: child) : child;
  }
}

/// Tombol ikon (satu bentuk).
class AppIconButton extends StatelessWidget {
  const AppIconButton({super.key, required this.icon, this.onPressed, this.tooltip});
  final IconData icon;
  final VoidCallback? onPressed;
  final String? tooltip;

  @override
  Widget build(BuildContext context) {
    final b = IconButton(
      icon: Icon(icon),
      onPressed: onPressed,
      constraints: const BoxConstraints(minWidth: AppSpacing.touchTarget, minHeight: AppSpacing.touchTarget),
    );
    return tooltip == null ? b : Tooltip(message: tooltip!, child: b);
  }
}
