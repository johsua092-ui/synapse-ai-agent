"""Peer Link — per-peer message mailbox.

Each approved peer gets a small FIFO queue of inbound messages.  The mailbox
is intentionally minimal: it is *not* a database, a message broker, or a
persistence layer.  It is an in-memory store backed by a single JSON file so
that messages survive a process restart but do not accumulate forever.

Design constraints
------------------
* **Zero new dependencies** — stdlib only (json, threading, time, pathlib).
* **Additive** — nothing in this module imports or mutates
  ``gateway/pairing.py`` or any existing core file.
* **Bounded** — each peer queue is capped at ``MAX_MESSAGES`` entries.
  Oldest messages are dropped when the cap is hit.
* **Thread-safe** — a single ``threading.Lock`` guards all mutations.  The
  mailbox is shared across HTTP handler threads.
"""

from __future__ import annotations

import json
import threading
import time
from pathlib import Path
from typing import Dict, List, Optional

#: Maximum messages per peer queue.  Old messages are dropped when the cap is
#: hit so the mailbox cannot grow without bound.
MAX_MESSAGES = 200

#: Schema version written to the on-disk file.  Bump when the shape changes.
_SCHEMA_VERSION = 1


class Message:
    """One inbound message from a peer."""

    __slots__ = ("from_peer_id", "text", "ts", "msg_id")

    def __init__(self, from_peer_id: str, text: str, ts: float, msg_id: str) -> None:
        self.from_peer_id = from_peer_id
        self.text = text
        self.ts = ts
        self.msg_id = msg_id

    def to_dict(self) -> dict:
        return {
            "from_peer_id": self.from_peer_id,
            "text": self.text,
            "ts": self.ts,
            "msg_id": self.msg_id,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "Message":
        return cls(
            from_peer_id=str(d["from_peer_id"]),
            text=str(d["text"]),
            ts=float(d["ts"]),
            msg_id=str(d["msg_id"]),
        )

    def __repr__(self) -> str:
        return (
            f"Message(from={self.from_peer_id!r}, msg_id={self.msg_id!r},"
            f" ts={self.ts:.0f})"
        )


class PeerMailbox:
    """Thread-safe in-memory mailbox backed by a JSON file.

    Parameters
    ----------
    path:
        Where to persist messages.  The parent directory must already exist
        (the mailbox does not create it — that is the caller's job, because
        the caller already owns the data directory).
    """

    def __init__(self, path: Path) -> None:
        self._path = path
        self._lock = threading.Lock()
        # peer_id -> list of Message, newest last
        self._queues: Dict[str, List[Message]] = {}
        self._load()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def put(self, msg: Message) -> None:
        """Enqueue *msg*.  Drops the oldest entry when the queue is full."""
        with self._lock:
            queue = self._queues.setdefault(msg.from_peer_id, [])
            if len(queue) >= MAX_MESSAGES:
                queue.pop(0)
            queue.append(msg)
            self._save()

    def peek(self, peer_id: Optional[str] = None) -> List[Message]:
        """Return messages without removing them.

        If *peer_id* is given, return only messages from that peer.
        Otherwise return all messages, newest last.
        """
        with self._lock:
            if peer_id is not None:
                return list(self._queues.get(peer_id, []))
            all_msgs: List[Message] = []
            for msgs in self._queues.values():
                all_msgs.extend(msgs)
            all_msgs.sort(key=lambda m: m.ts)
            return all_msgs

    def drain(self, peer_id: Optional[str] = None) -> List[Message]:
        """Return messages and remove them from the mailbox.

        If *peer_id* is given, drain only that peer's queue.
        Otherwise drain every queue.
        """
        with self._lock:
            if peer_id is not None:
                msgs = list(self._queues.pop(peer_id, []))
            else:
                msgs = []
                for peer_msgs in self._queues.values():
                    msgs.extend(peer_msgs)
                msgs.sort(key=lambda m: m.ts)
                self._queues.clear()
            self._save()
            return msgs

    def count(self, peer_id: Optional[str] = None) -> int:
        """Number of queued messages."""
        with self._lock:
            if peer_id is not None:
                return len(self._queues.get(peer_id, []))
            return sum(len(q) for q in self._queues.values())

    def peers_with_mail(self) -> List[str]:
        """Peer ids that have at least one queued message."""
        with self._lock:
            return [pid for pid, q in self._queues.items() if q]

    # ------------------------------------------------------------------
    # Persistence
    # ------------------------------------------------------------------

    def _save(self) -> None:
        """Write current state to disk (caller holds the lock)."""
        data = {
            "schema": _SCHEMA_VERSION,
            "queues": {
                peer_id: [m.to_dict() for m in msgs]
                for peer_id, msgs in self._queues.items()
                if msgs  # skip empty queues
            },
        }
        tmp = self._path.with_suffix(".tmp")
        tmp.write_text(json.dumps(data, separators=(",", ":")), encoding="utf-8")
        tmp.replace(self._path)

    def _load(self) -> None:
        """Read state from disk on startup.  Silently recovers from corruption."""
        if not self._path.exists():
            return
        try:
            raw = json.loads(self._path.read_text(encoding="utf-8"))
            if raw.get("schema") != _SCHEMA_VERSION:
                return
            for peer_id, msgs in raw.get("queues", {}).items():
                self._queues[peer_id] = [Message.from_dict(m) for m in msgs]
        except Exception:  # noqa: BLE001 — corrupted file is not a crash
            self._queues = {}


def new_msg_id() -> str:
    """Mint a unique, sortable message id."""
    import secrets

    return f"{int(time.time() * 1000):016x}-{secrets.token_hex(4)}"
