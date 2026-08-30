/**
 * ChatSessionList — a ChatGPT-style conversation switcher that sits beside
 * the embedded TUI on the dashboard Chat tab.
 *
 * It lists the most recent sessions for the active management profile and
 * lets the user swap between them without leaving the Chat page. Selecting
 * a row sets `/chat?resume=<id>`; ChatPage treats the resume target as part
 * of the PTY identity, so the change tears down the current terminal child
 * and respawns it resuming that conversation (see ChatPage.tsx). The
 * "New session" action clears the resume param, which spawns a fresh PTY.
 *
 * Best-effort, like ChatSidebar: a failed fetch surfaces a small inline
 * error with a retry affordance and the terminal pane keeps working.
 *
 * This stays a light navigation surface: delete, export, and bulk actions
 * live on the Sessions page. Pin/unpin and rename are offered here too
 * (they re-resolve on the Sessions page and cost no refetch) so the chat
 * context supports them without leaving the page. Everything stays
 * best-effort: failed mutations surface a small inline message; the
 * terminal pane is never affected.
 */

import { Button } from "@nous-research/ui/ui/components/button";
import { ListItem } from "@nous-research/ui/ui/components/list-item";
import { Spinner } from "@nous-research/ui/ui/components/spinner";
import {
  AlertCircle,
  Check,
  MessageSquarePlus,
  MoreHorizontal,
  Pencil,
  Pin,
  PinOff,
  RefreshCw,
  Trash2,
  X,
} from "lucide-react";
import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { useSearchParams } from "react-router";

import { DeleteConfirmDialog } from "@/components/DeleteConfirmDialog";
import { useI18n } from "@/i18n";
import { api, type SessionInfo } from "@/lib/api";
import { cn, timeAgo } from "@/lib/utils";

const SESSION_LIMIT = 30;
interface ChatSessionListProps {
  /** Active resume target (the session currently shown in the terminal). */
  activeSessionId: string | null;
  /** Management profile from the dashboard switcher — scopes the listing. */
  profile?: string;
  className?: string;
  /** Optional callback fired after a row is picked (e.g. close mobile sheet). */
  onPicked?: () => void;
  /**
   * Starts a fresh chat. ChatPage supplies its `startFreshDashboardChat`,
   * which clears `?resume` AND bumps the reconnect nonce so a brand-new PTY
   * spawns even when the user is already on an unsaved fresh session. When
   * omitted, we fall back to clearing the resume param ourselves.
   */
  onNewChat?: () => void;
}

function rowLabel(session: SessionInfo, untitled: string): string {
  const title = session.title?.trim();
  if (title && title !== "Untitled") return title;
  const preview = session.preview?.trim();
  if (preview) return preview;
  return untitled;
}

/** Stable partition: pinned sessions first, otherwise keep API order. */
function pinnedFirstCompare(a: SessionInfo, b: SessionInfo): number {
  const ap = !!a.pinned;
  const bp = !!b.pinned;
  if (ap !== bp) return ap ? -1 : 1;
  return 0;
}

export function ChatSessionList({
  activeSessionId,
  profile,
  className,
  onPicked,
  onNewChat,
}: ChatSessionListProps) {
  const { t } = useI18n();
  const [, setSearchParams] = useSearchParams();
  const [sessions, setSessions] = useState<SessionInfo[] | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  // Bumped to force a refetch (after switching, on Refresh, on mount).
  const [reloadNonce, setReloadNonce] = useState(0);
  // Id of the row whose manage menu is open (single menu at a time).
  const [openMenuId, setOpenMenuId] = useState<string | null>(null);
  // Id of the row currently being renamed inline.
  const [renamingId, setRenamingId] = useState<string | null>(null);
  const [renameValue, setRenameValue] = useState("");
  // Id + message of the last failed pin/rename/delete action, surfaced under the row.
  const [actionError, setActionError] = useState<{
    id: string;
    message: string;
  } | null>(null);
  // Id whose Delete confirm dialog is open.
  const [deleteTarget, setDeleteTarget] = useState<string | null>(null);
  // True while a delete request is in flight (keeps the dialog busy).
  const [deleteBusy, setDeleteBusy] = useState(false);

  // `profile` is read inside the fetch; it's part of the scope key so a
  // profile switch refetches. The empty-string fallback keeps the dep
  // stable when no profile is selected (default profile).
  const scopeKey = profile ?? "";

  // Monotonic request token: only the most recent fetch is allowed to
  // commit state, so a fast profile switch (or Refresh spam) can't land a
  // stale list out of order.
  const reqRef = useRef(0);

  const load = useCallback(() => {
    const myReq = ++reqRef.current;
    setLoading(true);
    setError(null);
    api
      .getSessions(SESSION_LIMIT, 0, scopeKey, "recent")
      .then((res) => {
        if (reqRef.current !== myReq) return;
        setSessions(res.sessions);
      })
      .catch((e: Error) => {
        if (reqRef.current !== myReq) return;
        setError(e.message || "failed to load sessions");
      })
      .finally(() => {
        if (reqRef.current === myReq) setLoading(false);
      });
  }, [scopeKey]);

  useEffect(() => {
    // Dashboard data surfaces fetch from an effect on mount + scope change;
    // keep this local and explicit until the shared lint profile is updated
    // for async loaders (matches FilesPage).
    // eslint-disable-next-line react-hooks/set-state-in-effect
    load();
    // `reloadNonce` is a manual refetch trigger (Refresh button / row pick).
  }, [load, reloadNonce]);

  const reload = useCallback(() => setReloadNonce((n) => n + 1), []);

  // Picking a row sets `/chat?resume=<id>`. Re-picking the row already in
  // the terminal is a no-op (avoids a needless PTY teardown).
  const pick = useCallback(
    (id: string) => {
      onPicked?.();
      if (id === activeSessionId) return;
      setSearchParams(
        (prev) => {
          const next = new URLSearchParams(prev);
          next.set("resume", id);
          return next;
        },
        { replace: false },
      );
    },
    [activeSessionId, onPicked, setSearchParams],
  );

  // "New chat" prefers ChatPage's robust handler (clears resume + forces a
  // PTY respawn even from an already-fresh session). Fallback: clear the
  // resume param ourselves, which spawns a fresh PTY whenever one was being
  // resumed. Session management (delete/rename/export) lives on the Sessions
  // page; this panel only switches and starts conversations.
  const startNew = useCallback(() => {
    onPicked?.();
    if (onNewChat) {
      onNewChat();
      return;
    }
    setSearchParams(
      (prev) => {
        const next = new URLSearchParams(prev);
        next.delete("resume");
        return next;
      },
      { replace: false },
    );
  }, [onNewChat, onPicked, setSearchParams]);

  const togglePin = useCallback(
    async (session: SessionInfo, pinned: boolean) => {
      setOpenMenuId(null);
      setActionError(null);
      try {
        const res = await api.setSessionPinned(session.id, pinned);
        setSessions((prev) =>
          prev?.map((s) =>
            s.id === session.id
              ? { ...s, pinned: res.pinned ?? pinned }
              : s,
          ) ?? prev,
        );
      } catch (e: unknown) {
        const message =
          e instanceof Error
            ? e.message
            : (pinned ? "Pin failed" : "Unpin failed");
        setActionError({ id: session.id, message });
      }
    },
    [],
  );

  const startRename = useCallback(
    (session: SessionInfo) => {
      setOpenMenuId(null);
      setActionError(null);
      setRenameValue(session.title?.trim() || session.preview?.trim() || "");
      setRenamingId(session.id);
    },
    [],
  );

  const commitRename = useCallback(
    async (session: SessionInfo) => {
      setActionError(null);
      const value = renameValue.trim();
      const existing = session.title?.trim() || "";
      if (!value || value === existing) {
        setRenamingId(null);
        return;
      }
      try {
        const res = await api.renameSession(session.id, value);
        setSessions((prev) =>
          prev?.map((s) =>
            s.id === session.id
              ? { ...s, title: res.title ?? value }
              : s,
          ) ?? prev,
        );
      } catch (e: unknown) {
        const message =
          e instanceof Error ? e.message : "Rename failed";
        setActionError({ id: session.id, message });
      } finally {
        setRenamingId(null);
      }
    },
    [renameValue],
  );

  const handleDelete = useCallback(async (session: SessionInfo) => {
    setActionError(null);
    setDeleteBusy(true);
    try {
      await api.deleteSession(session.id);
      setSessions((prev) =>
        prev?.filter((s) => s.id !== session.id) ?? prev,
      );
    } catch (e: unknown) {
      const message =
        e instanceof Error ? e.message : "Failed to delete session";
      setActionError({ id: session.id, message });
    } finally {
      setDeleteTarget(null);
      setDeleteBusy(false);
    }
  }, []);

  const content = useMemo(() => {
    if (loading && sessions === null) {
      return (
        <div className="flex items-center justify-center gap-2 px-2 py-6 text-xs text-text-secondary">
          <Spinner /> {t.common.loading}
        </div>
      );
    }
    if (error) {
      return (
        <div className="flex flex-col items-start gap-2 px-2 py-4 text-xs">
          <div className="flex items-start gap-2 text-destructive">
            <AlertCircle className="mt-0.5 h-3.5 w-3.5 shrink-0" />
            <span className="wrap-break-word">{error}</span>
          </div>
          <Button size="sm" outlined onClick={reload} prefix={<RefreshCw />}>
            {t.common.retry}
          </Button>
        </div>
      );
    }
    const rows = sessions ? [...sessions].sort(pinnedFirstCompare) : sessions;
    if (!rows || rows.length === 0) {
      return (
        <div className="px-2 py-6 text-center text-xs text-text-secondary">
          {t.sessions.noSessions}
        </div>
      );
    }
    return (
      <div className="flex flex-col gap-0.5">
        {rows.map((s) => {
          const isActive = s.id === activeSessionId;
          const menuOpen = openMenuId === s.id;
          if (renamingId === s.id) {
            return (
              <div
                key={s.id}
                className="flex items-center gap-1 rounded px-2 py-1.5"
              >
                <input
                  autoFocus
                  value={renameValue}
                  onChange={(e) => setRenameValue(e.target.value)}
                  onKeyDown={(e) => {
                    if (e.key === "Enter") {
                      e.preventDefault();
                      void commitRename(s);
                    } else if (e.key === "Escape") {
                      setRenamingId(null);
                    }
                  }}
                  aria-label="Rename chat"
                  placeholder={t.sessions.untitledSession}
                  className="min-w-0 flex-1 rounded border border-midground/15 bg-transparent px-1.5 py-0.5 text-sm text-foreground outline-none focus:border-primary"
                />
                <Button
                  ghost
                  size="icon"
                  aria-label="Save rename"
                  title="Save"
                  onClick={() => void commitRename(s)}
                  className="shrink-0 text-text-secondary hover:text-foreground"
                >
                  <Check className="size-4" />
                </Button>
                <Button
                  ghost
                  size="icon"
                  aria-label="Cancel rename"
                  title="Cancel"
                  onClick={() => setRenamingId(null)}
                  className="shrink-0 text-text-secondary hover:text-foreground"
                >
                  <X className="size-4" />
                </Button>
              </div>
            );
          }
          return (
            <div key={s.id} className="relative">
              <div className="flex items-stretch gap-0.5">
                <ListItem
                  onClick={() => pick(s.id)}
                  aria-current={isActive ? "true" : undefined}
                  className={cn(
                    "min-w-0 flex-1 flex-col items-start gap-0.5 rounded px-2 py-1.5",
                    "normal-case tracking-normal",
                    isActive
                      ? "bg-primary/10 text-foreground border-l-2 border-primary"
                      : "text-text-secondary hover:bg-midground/5 hover:text-foreground",
                  )}
                >
                  <span className="w-full truncate text-sm font-medium">
                    {rowLabel(s, t.sessions.untitledSession)}
                  </span>
                  <span className="flex w-full items-center gap-1.5 text-[0.6875rem] text-text-tertiary">
                    {s.pinned && (
                      <>
                        <Pin
                          aria-label="Pinned"
                          className="size-3 shrink-0"
                        />
                      </>
                    )}
                    <span>{timeAgo(s.last_active)}</span>
                    {s.message_count > 0 && (
                      <>
                        <span aria-hidden>·</span>
                        <span>{s.message_count} msgs</span>
                      </>
                    )}
                    {s.source && s.source !== "cli" && (
                      <>
                        <span aria-hidden>·</span>
                        <span className="truncate">{s.source}</span>
                      </>
                    )}
                  </span>
                </ListItem>
                <Button
                  ghost
                  size="icon"
                  aria-label="Conversation actions"
                  title="Conversation actions"
                  onClick={() => setOpenMenuId(menuOpen ? null : s.id)}
                  className="shrink-0 self-start rounded p-1 text-text-secondary hover:text-foreground"
                >
                  <MoreHorizontal className="size-4" />
                </Button>
                {menuOpen && (
                  <>
                    <button
                      type="button"
                      aria-hidden
                      tabIndex={-1}
                      className="fixed inset-0 z-0 cursor-default"
                      onClick={() => setOpenMenuId(null)}
                    />
                    <div
                      role="menu"
                      className="absolute right-0 top-full z-10 mt-0.5 flex min-w-40 flex-col gap-0.5 rounded-md border border-midground/10 bg-background p-1 shadow-lg"
                    >
                      <button
                        type="button"
                        role="menuitem"
                        onClick={() => void togglePin(s, !s.pinned)}
                        className="flex items-center gap-2 rounded px-2 py-1.5 text-left text-xs text-foreground hover:bg-midground/10"
                      >
                        {s.pinned ? (
                          <PinOff className="size-3.5" />
                        ) : (
                          <Pin className="size-3.5" />
                        )}
                        {s.pinned ? "Unpin chat" : "Pin chat"}
                      </button>
                      <button
                        type="button"
                        role="menuitem"
                        onClick={() => startRename(s)}
                        className="flex items-center gap-2 rounded px-2 py-1.5 text-left text-xs text-foreground hover:bg-midground/10"
                      >
                        <Pencil className="size-3.5" />
                        Rename
                      </button>
                      <button
                        type="button"
                        role="menuitem"
                        onClick={() => {
                          setOpenMenuId(null);
                          setDeleteTarget(s.id);
                        }}
                        className="flex items-center gap-2 rounded px-2 py-1.5 text-left text-xs text-destructive hover:bg-destructive/10"
                      >
                        <Trash2 className="size-3.5" />
                        {t.sessions.deleteSession}
                      </button>
                    </div>
                  </>
                )}
              </div>
              {actionError?.id === s.id && (
                <span className="mt-0.5 block px-2 text-[0.6875rem] text-destructive">
                  {actionError.message}
                </span>
              )}
            </div>
          );
        })}
      </div>
    );
  }, [
    actionError,
    activeSessionId,
    commitRename,
    error,
    loading,
    openMenuId,
    pick,
    reload,
    renamingId,
    renameValue,
    sessions,
    startRename,
    t,
    togglePin,
  ]);

  return (
    <aside
      className={cn(
        "flex h-full w-full min-w-0 shrink-0 flex-col overflow-hidden",
        className,
      )}
    >
      <div className="flex items-center justify-between gap-2 px-2 pb-2">
        <span className="text-display text-xs tracking-wider text-text-tertiary">
          {t.sessions.title}
        </span>
        <Button
          ghost
          size="icon"
          onClick={reload}
          aria-label={t.common.refresh}
          title={t.common.refresh}
          className="text-text-secondary hover:text-foreground"
        >
          <RefreshCw className={cn(loading && "animate-spin")} />
        </Button>
      </div>

      <Button
        outlined
        size="sm"
        onClick={startNew}
        prefix={<MessageSquarePlus />}
        className="mx-2 mb-2 justify-center"
      >
        {t.sessions.newChat}
      </Button>

      <div className="min-h-0 flex-1 overflow-y-auto overflow-x-hidden px-1 pb-1">
        {content}
      </div>

      <DeleteConfirmDialog
        open={deleteTarget !== null}
        loading={deleteBusy}
        title={t.sessions.confirmDeleteTitle}
        description={t.sessions.confirmDeleteMessage}
        onCancel={() => setDeleteTarget(null)}
        onConfirm={() => {
          const target = sessions?.find((s) => s.id === deleteTarget);
          if (target) void handleDelete(target);
        }}
      />
    </aside>
  );
}
