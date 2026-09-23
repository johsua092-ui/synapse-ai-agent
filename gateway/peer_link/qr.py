"""Peer Link — QR rendering for share links.

Why this module exists instead of importing the QR helper that already lives in
``synapse_cli.telegram_managed_bot``: that module imports ``httpx`` at module
scope, so reaching into it from the gateway layer would drag a full HTTP client
into a package that otherwise speaks only stdlib ``urllib``. The rendering
parameters are deliberately the same shape (one-cell boxes, minimal border,
ASCII, inverted for dark terminals) so a Peer Link QR looks and scans like the
Telegram one people have already met.

``qrcode`` is optional and lazy-installed through the ``peer_link.qr`` entry in
:mod:`tools.lazy_deps`. When it is unavailable — lazy installs disabled, no
network, read-only package store — :func:`render_qr` returns an empty string and
the caller prints the plain link instead. A missing QR must never be the reason
someone cannot connect.

The QR payload is a share artifact: it carries the peer URL *and* the invite
code, exactly as sending both over WhatsApp would. It is rendered to stdout
only. Nothing here writes it to disk or to a log.
"""

from __future__ import annotations

#: Error-correction level. Telegram's helper uses ``L``; a peer URL plus an
#: 8-character code is roughly twice as long and is meant to be photographed off
#: a screen, so the extra redundancy is worth a few more modules.
_ERROR_CORRECTION = "M"

#: One cell per module, one-cell quiet zone — same as the existing helper.
_BOX_SIZE = 1
_BORDER = 1


def _ensure_qrcode() -> bool:
    """Return True once ``qrcode`` is importable, lazy-installing if allowed."""
    try:
        import qrcode  # noqa: F401

        return True
    except ImportError:
        pass
    try:
        from tools.lazy_deps import ensure

        ensure("peer_link.qr")
    except Exception:  # noqa: BLE001 - installs disabled, offline, read-only store
        return False
    try:
        import qrcode  # noqa: F401,F811

        return True
    except ImportError:
        return False


def qr_available() -> bool:
    """True when ``qrcode`` is already importable (no install attempted)."""
    try:
        import qrcode  # noqa: F401

        return True
    except ImportError:
        return False


def render_qr(text: str) -> str:
    """Render *text* as an ASCII QR block, or ``""`` when unavailable.

    Never raises: a rendering failure must not break the command that wanted to
    show a code. Callers treat ``""`` as "show the link instead".
    """
    if not text:
        return ""
    if not _ensure_qrcode():
        return ""
    try:
        import io

        import qrcode  # type: ignore[import-untyped]

        level = getattr(qrcode.constants, f"ERROR_CORRECT_{_ERROR_CORRECTION}")
        qr = qrcode.QRCode(
            version=None,
            error_correction=level,
            box_size=_BOX_SIZE,
            border=_BORDER,
        )
        qr.add_data(text)
        qr.make(fit=True)
        buf = io.StringIO()
        qr.print_ascii(out=buf, invert=True)
        return buf.getvalue()
    except Exception:  # noqa: BLE001 - see docstring
        return ""
