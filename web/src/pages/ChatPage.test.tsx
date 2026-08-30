// @vitest-environment jsdom
import { act, type ReactNode } from "react";
import { createRoot, type Root } from "react-dom/client";
import { MemoryRouter } from "react-router";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { PTY_TICKET_TIMEOUT_MS } from "@/lib/pty-reconnect";

class FakeFitAddon {
  fit() {}
}

class FakeWebglAddon {
  static instances: FakeWebglAddon[] = [];
  onContextLossCb: (() => void) | null = null;
  disposed = false;

  constructor() {
    FakeWebglAddon.instances.push(this);
  }

  onContextLoss(cb: () => void) {
    this.onContextLossCb = cb;
    return { dispose: () => {} };
  }

  dispose() {
    this.disposed = true;
  }
}

class FakeTerminal {
  static instances: FakeTerminal[] = [];
  options: Record<string, unknown>;
  rows = 24;
  cols = 80;
  parser = {
    registerOscHandler: vi.fn(),
  };
  unicode = { activeVersion: "" };

  constructor(options: Record<string, unknown>) {
    this.options = options;
    FakeTerminal.instances.push(this);
  }

  attachCustomKeyEventHandler() {
    return true;
  }

  attachCustomWheelEventHandler() {
    return true;
  }

  clearSelection() {}

  dispose() {}

  focus() {}

  getSelection() {
    return "";
  }

  loadAddon() {}

  onData() {
    return { dispose() {} };
  }

  onResize() {
    return { dispose() {} };
  }

  onScroll() {
    return { dispose() {} };
  }

  get buffer() {
    // Minimal active-buffer surface for the resume follow-scroll pin
    // (isViewportPinnedToBottom reads viewportY/baseY).
    return { active: { baseY: 0, viewportY: 0 } };
  }

  scrollToBottom() {}

  open() {}

  paste() {}

  refresh = vi.fn();

  write() {}
}

const maybeReloadForLoopbackWsAuthFailure = vi.fn(() => false);
const apiMocks = vi.hoisted(() => ({
  buildWsUrl: vi.fn(async () => "ws://localhost/api/pty?channel=chat-1"),
  getSessionDetail: vi.fn(async () => ({
    title: "Fix session bug",
  })),
  getSessionLatestDescendant: vi.fn(async () => ({ session_id: "" })),
}));

vi.mock("@xterm/addon-fit", () => ({ FitAddon: FakeFitAddon }));
vi.mock("@xterm/addon-unicode11", () => ({ Unicode11Addon: class {} }));
vi.mock("@xterm/addon-web-links", () => ({ WebLinksAddon: class {} }));
vi.mock("@xterm/addon-webgl", () => ({ WebglAddon: FakeWebglAddon }));
vi.mock("@xterm/xterm", () => ({ Terminal: FakeTerminal }));
vi.mock("@/components/ChatSidebar", () => ({
  ChatSidebar: () => null,
}));
vi.mock("@/components/ChatSessionList", () => ({
  ChatSessionList: () => null,
}));
vi.mock("@/components/Backdrop", () => ({ Backdrop: () => null }));
vi.mock("@/plugins", () => ({
  PluginSlot: () => null,
}));
vi.mock("@/contexts/usePageHeader", () => ({
  usePageHeader: () => ({ setEnd: vi.fn(), setTitle: vi.fn() }),
}));
vi.mock("@/contexts/useProfileScope", () => ({
  useProfileScope: () => ({ profile: "" }),
}));
vi.mock("@/themes", () => ({
  useTheme: () => ({ theme: { terminalBackground: "#000000" } }),
}));
vi.mock("@/i18n", () => ({
  useI18n: () => ({
    t: {
      app: {
        closeModelTools: "Close model tools",
        modelToolsSheetSubtitle: "Tools",
        modelToolsSheetTitle: "Model",
      },
    },
  }),
}));
vi.mock("@/lib/dashboard-auth-reload", () => ({
  maybeReloadForLoopbackWsAuthFailure,
}));
vi.mock("@/lib/api", () => ({
  api: apiMocks,
  buildWsUrl: apiMocks.buildWsUrl,
}));

class FakeWebSocket {
  static instances: FakeWebSocket[] = [];
  static OPEN = 1;

  binaryType = "blob";
  onclose: ((event: CloseEventLike) => void) | null = null;
  onmessage: ((event: { data: ArrayBuffer | string }) => void) | null = null;
  onopen: (() => void) | null = null;
  readyState = FakeWebSocket.OPEN;
  url: string;

  constructor(url: string) {
    this.url = url;
    FakeWebSocket.instances.push(this);
  }

  close() {
    this.readyState = 3;
  }

  sent: string[] = [];

  send(data: unknown) {
    if (typeof data === "string") {
      this.sent.push(data);
    }
  }
}

type CloseEventLike = {
  code: number;
  reason: string;
  wasClean: boolean;
};

let container: HTMLDivElement;
let root: Root;

// jsdom runs without an origin here (per-file @vitest-environment jsdom on a
// node-default config), so localStorage is undefined. Stub it so components
// that persist UI state (side panel collapse) can be exercised.
const localStorageMock = (() => {
  let store: Record<string, string> = {};
  return {
    getItem: (key: string) => store[key] ?? null,
    setItem: (key: string, value: string) => {
      store[key] = String(value);
    },
    removeItem: (key: string) => {
      delete store[key];
    },
    clear: () => {
      store = {};
    },
  };
})();

// React only routes updates through act() when this flag is set; without it
// the isActive re-renders in the keyboard-inset gate test warn.
(globalThis as { IS_REACT_ACT_ENVIRONMENT?: boolean }).IS_REACT_ACT_ENVIRONMENT =
  true;

// This box (Termux/proot) is slow under load; 5s default timeouts trip and
// cascade into unrelated failures. Keep the suite immune.
vi.setConfig({ testTimeout: 20_000 });

async function render(ui: ReactNode) {
  container = document.createElement("div");
  document.body.append(container);
  root = createRoot(container);
  await act(async () => root.render(ui));
}

beforeEach(() => {
  FakeWebSocket.instances = [];
  FakeWebglAddon.instances = [];
  FakeTerminal.instances = [];
  maybeReloadForLoopbackWsAuthFailure.mockClear();
  apiMocks.buildWsUrl.mockReset();
  apiMocks.buildWsUrl.mockResolvedValue("ws://localhost/api/pty?channel=chat-1");
  vi.stubGlobal("WebSocket", FakeWebSocket);
  vi.stubGlobal(
    "ResizeObserver",
    class {
      disconnect() {}
      observe() {}
      unobserve() {}
    },
  );
  vi.stubGlobal("requestAnimationFrame", (cb: FrameRequestCallback) => {
    cb(0);
    return 1;
  });
  vi.stubGlobal("cancelAnimationFrame", () => {});
  vi.stubGlobal("matchMedia", () => ({
    addEventListener() {},
    matches: false,
    media: "",
    removeEventListener() {},
  }));
  vi.stubGlobal("crypto", {
    getRandomValues: (values: Uint8Array) => {
      values.fill(7);
      return values;
    },
    randomUUID: () => "chat-test-id",
  });

  Object.defineProperty(window, "visualViewport", {
    configurable: true,
    value: { addEventListener() {}, removeEventListener() {}, width: 1280 },
  });
  Object.defineProperty(window, "__SYNAPSE_SESSION_TOKEN__", {
    configurable: true,
    value: "stale-token",
    writable: true,
  });
  Object.defineProperty(window, "__SYNAPSE_AUTH_REQUIRED__", {
    configurable: true,
    value: false,
    writable: true,
  });
  Object.defineProperty(window.navigator, "clipboard", {
    configurable: true,
    value: {
      readText: vi.fn(async () => ""),
      writeText: vi.fn(async () => {}),
    },
  });
  sessionStorage.clear();
  vi.stubGlobal("localStorage", localStorageMock);
  localStorageMock.clear();
});

afterEach(async () => {
  await act(async () => root?.unmount());
  container?.remove();
  vi.unstubAllGlobals();
});

describe("ChatPage", () => {
  it("treats loopback 4401 closes as stale-token reload candidates", async () => {
    const { default: ChatPage } = await import("./ChatPage");

    await render(
      <MemoryRouter initialEntries={["/chat"]}>
        <ChatPage isActive />
      </MemoryRouter>,
    );

    await vi.waitFor(
      () => expect(FakeWebSocket.instances).toHaveLength(1),
      { timeout: 15_000 },
    );

    FakeWebSocket.instances[0].onclose?.({
      code: 4401,
      reason: "auth: token_mismatch",
      wasClean: true,
    });

    expect(maybeReloadForLoopbackWsAuthFailure).toHaveBeenCalledWith(4401);
  });

  it("attaches visualViewport keyboard-inset listeners only while the chat tab is active", async () => {
    // NS-434 follow-up: ChatPage stays mounted (hidden) on every dashboard
    // route. The keyboard-inset/scroll-pin listeners must only be live while
    // /chat is the active tab, or the scroll pin fires when a soft keyboard
    // opens on Settings etc.
    const addEventListener = vi.fn();
    const removeEventListener = vi.fn();
    Object.defineProperty(window, "visualViewport", {
      configurable: true,
      value: { addEventListener, removeEventListener, width: 1280 },
    });

    const { default: ChatPage } = await import("./ChatPage");

    await render(
      <MemoryRouter initialEntries={["/chat"]}>
        <ChatPage isActive={false} />
      </MemoryRouter>,
    );
    expect(addEventListener).not.toHaveBeenCalled();

    await act(async () =>
      root.render(
        <MemoryRouter initialEntries={["/chat"]}>
          <ChatPage isActive />
        </MemoryRouter>,
      ),
    );
    expect(addEventListener.mock.calls.map((c) => c[0]).sort()).toEqual([
      "resize",
      "scroll",
    ]);
    expect(removeEventListener).not.toHaveBeenCalled();

    await act(async () =>
      root.render(
        <MemoryRouter initialEntries={["/chat"]}>
          <ChatPage isActive={false} />
        </MemoryRouter>,
      ),
    );
    expect(removeEventListener.mock.calls.map((c) => c[0]).sort()).toEqual([
      "resize",
      "scroll",
    ]);
  });

  it("self-heals the renderer when the WebGL context is lost", async () => {
    // Windows/Chrome release the GL context when the dashboard window is
    // occluded, minimized, or captured. The addon must dispose itself and
    // force a repaint so the fallback canvas renderer redraws cleanly —
    // otherwise the old GL layer lingers as ghosted (stacked) glyphs.
    const warn = vi.spyOn(console, "warn").mockImplementation(() => {});

    const { default: ChatPage } = await import("./ChatPage");

    await render(
      <MemoryRouter initialEntries={["/chat"]}>
        <ChatPage isActive />
      </MemoryRouter>,
    );

    await vi.waitFor(
      () => expect(FakeWebglAddon.instances).toHaveLength(1),
      { timeout: 15_000 },
    );

    const webgl = FakeWebglAddon.instances[0];
    expect(webgl.onContextLossCb).not.toBeNull();
    const term = FakeTerminal.instances[0];

    await act(async () => {
      webgl.onContextLossCb!();
    });

    expect(webgl.disposed).toBe(true);
    expect(warn).toHaveBeenCalledWith(
      expect.stringContaining("context lost"),
    );
    expect(term.refresh).toHaveBeenCalledWith(0, term.rows - 1);

    warn.mockRestore();
  });
});

describe("ChatPage side panel collapse", () => {
  async function renderChat() {
    const { default: ChatPage } = await import("./ChatPage");
    await render(
      <MemoryRouter initialEntries={["/chat"]}>
        <ChatPage isActive />
      </MemoryRouter>,
    );
  }

  it("collapses the desktop side panel and persists the choice", async () => {
    localStorage.clear();
    await renderChat();
    await vi.waitFor(
      () => expect(FakeWebSocket.instances).toHaveLength(1),
      { timeout: 15_000 },
    );

    const collapseButton = container.querySelector(
      '[aria-label="Collapse chat side panel"]',
    );
    expect(collapseButton).not.toBeNull();

    await act(async () => {
      collapseButton!.dispatchEvent(
        new MouseEvent("click", { bubbles: true }),
      );
    });

    expect(localStorage.getItem("synapse-chat-panel-collapsed")).toBe("1");
    expect(
      container.querySelector('[aria-label="Collapse chat side panel"]'),
    ).toBeNull();
    expect(
      container.querySelector('[aria-label="Show chat side panel"]'),
    ).not.toBeNull();

    // Reopening restores the panel and clears the persisted flag.
    await act(async () => {
      container
        .querySelector('[aria-label="Show chat side panel"]')!
        .dispatchEvent(new MouseEvent("click", { bubbles: true }));
    });

    expect(localStorage.getItem("synapse-chat-panel-collapsed")).toBe("0");
    expect(
      container.querySelector('[aria-label="Collapse chat side panel"]'),
    ).not.toBeNull();
  });
});

// A blur/occlusion-triggered socket drop (window minimize, screenshot) makes
// the client RECONNECT. The PTY keeps living server-side, so that reconnect is
// a REATTACH: the terminal already has content and live output, and must not
// re-enter the resume-boot "Please wait while the conversation loads…" state
// (nor re-arm erase suppression). Regression for Blc's "minimize window → chat
// says please wait" report.
// Hydration + wait notice are now keyed per-MOUNT and per-`created` (server-
// sent control frame): a fresh tab reattaching a living PTY STILL shows the
// wait notice and repaint pulse; a same-mount reconnect never does. Regressions
// for Blc's "minimize → please wait" AND "new tab reloaded the session"
// reports.
describe("ChatPage resume vs reattach", () => {
  async function renderChat(entry: string) {
    const { default: ChatPage } = await import("./ChatPage");
    await render(
      <MemoryRouter initialEntries={[entry]}>
        <ChatPage isActive />
      </MemoryRouter>,
    );
  }

  const WAIT = "Please wait while the conversation loads";
  const resumeFrame = (created = false) =>
    JSON.stringify({ type: "resume", id: "session-1", created });

  function send(ws: FakeWebSocket, data: ArrayBuffer | string) {
    return act(async () => {
      ws.onmessage?.({ data });
    });
  }

  it("waits on a fresh resume, but not on a reattach after a drop", async () => {
    await renderChat("/chat?resume=session-1");
    await vi.waitFor(
      () => expect(FakeWebSocket.instances).toHaveLength(1),
      { timeout: 7000 },
    );
    const ws = FakeWebSocket.instances[0];

    // Fresh page load with ?resume=: the wait notice is up from mount.
    await act(async () => {
      ws.onopen?.();
    });
    expect(container.textContent).toContain(WAIT);

    // The server names the session (explicit resumes ship a control frame
    // too, so `created` is known before the replay bytes land).
    await send(ws, resumeFrame(false));
    expect(container.textContent).toContain(WAIT);

    // First real chunk lands → notice finishes.
    await send(ws, new TextEncoder().encode("ready\n").buffer);
    expect(container.textContent).not.toContain(WAIT);

    // The window gets occluded/minimized → the socket drops (1006) → the
    // connect backoff mints a fresh socket that reattaches the same PTY.
    await act(async () => {
      ws.onclose?.({ code: 1006, reason: "", wasClean: false });
    });
    await vi.waitFor(
      () => expect(FakeWebSocket.instances).toHaveLength(2),
      { timeout: 7000 },
    );
    const reattached = FakeWebSocket.instances[1];
    await act(async () => {
      reattached.onopen?.();
    });

    // Reattach within the same mount: the terminal already holds the
    // conversation — no wait wall even though the control frame re-fires.
    await send(reattached, resumeFrame(false));
    expect(container.textContent).not.toContain(WAIT);
  });

  it("shows the wait notice on a fresh tab's implicit resume, but not on its reconnect", async () => {
    await renderChat("/chat");
    await vi.waitFor(
      () => expect(FakeWebSocket.instances).toHaveLength(1),
      { timeout: 7000 },
    );
    const ws = FakeWebSocket.instances[0];

    await act(async () => {
      ws.onopen?.();
    });
    expect(container.textContent).not.toContain(WAIT);

    // Implicit active-session fallback: no ?resume= on the URL, so the server
    // names the session AFTER the socket opened. This mount's terminal is
    // empty and a replay is coming — the wait notice must appear even though
    // the socket is already open (regression: it was suppressed because the
    // "reattach" gate looked at the socket being open instead of this mount).
    await send(ws, resumeFrame(false));
    expect(container.textContent).toContain(WAIT);

    await send(ws, new TextEncoder().encode("hello\n").buffer);
    expect(container.textContent).not.toContain(WAIT);

    // Drop + reconnect in this same tab: content is on screen again — the
    // control frame must NOT re-pop the notice.
    await act(async () => {
      ws.onclose?.({ code: 1006, reason: "", wasClean: false });
    });
    await vi.waitFor(
      () => expect(FakeWebSocket.instances).toHaveLength(2),
      { timeout: 7000 },
    );
    const reattached = FakeWebSocket.instances[1];
    await act(async () => {
      reattached.onopen?.();
    });
    await send(reattached, resumeFrame(false));
    expect(container.textContent).not.toContain(WAIT);
  });

  it("pulses the living TUI to repaint on a reattach, but not on a fresh spawn", async () => {
    await renderChat("/chat");
    await vi.waitFor(
      () => expect(FakeWebSocket.instances).toHaveLength(1),
      { timeout: 7000 },
    );
    const ws = FakeWebSocket.instances[0];
    const term = FakeTerminal.instances[0];
    const [cols, rows] = [term.cols, term.rows];

    // First connect (no resume yet, mount fresh): plain RESIZE only.
    await act(async () => {
      ws.onopen?.();
    });
    expect(ws.sent).toEqual([`\x1b[RESIZE:${cols};${rows}]`]);

    // Reattach to the living PTY: the server's \x0c clears the terminal and
    // the TUI ignores it, so the client nudges a full repaint (off-by-one
    // pulse — a same-size TIOCSWINSZ raises no SIGWINCH).
    await send(ws, resumeFrame(false));
    expect(ws.sent).toEqual([
      `\x1b[RESIZE:${cols};${rows}]`,
      `\x1b[RESIZE:${cols + 1};${rows}]`,
      `\x1b[RESIZE:${cols};${rows}]`,
    ]);

    // Drop + reconnect: the onopen pulse covers the repaint (still one pulse,
    // no duplicate from the control frame).
    await act(async () => {
      ws.onclose?.({ code: 1006, reason: "", wasClean: false });
    });
    await vi.waitFor(
      () => expect(FakeWebSocket.instances).toHaveLength(2),
      { timeout: 7000 },
    );
    const reattached = FakeWebSocket.instances[1];
    await act(async () => {
      reattached.onopen?.();
    });
    await send(reattached, resumeFrame(false));
    expect(reattached.sent).toEqual([
      `\x1b[RESIZE:${cols};${rows}]`,
      `\x1b[RESIZE:${cols + 1};${rows}]`,
      `\x1b[RESIZE:${cols};${rows}]`,
    ]);
  });

  it("does NOT repaint-pulse a fresh spawn (booting TUI paints itself)", async () => {
    await renderChat("/chat?resume=session-1");
    await vi.waitFor(
      () => expect(FakeWebSocket.instances).toHaveLength(1),
      { timeout: 7000 },
    );
    const ws = FakeWebSocket.instances[0];
    const [cols, rows] = [
      FakeTerminal.instances[0].cols,
      FakeTerminal.instances[0].rows,
    ];

    await act(async () => {
      ws.onopen?.();
    });
    await send(ws, resumeFrame(true));
    expect(container.textContent).toContain(WAIT);
    // Fresh spawn: Ink is booting and will paint its own frame — no nudge.
    expect(ws.sent).toEqual([`\x1b[RESIZE:${cols};${rows}]`]);
  });
});
// The gated-mode ticket request runs before any socket exists, so a rejection
// or a hang emits no `close` event and never arms PTY_CONNECTING_TIMEOUT_MS
// (that timer is set after `new WebSocket`). Without its own deadline the tab
// strands on "connecting" with no retry. Mirrors the ChatSidebar events-feed
// coverage in src/components/ChatSidebar.test.tsx.
describe("ChatPage PTY ticket connect deadline", () => {
  beforeEach(() => {
    vi.useFakeTimers();
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  async function renderChat() {
    const { default: ChatPage } = await import("./ChatPage");
    await render(
      <MemoryRouter initialEntries={["/chat"]}>
        <ChatPage isActive />
      </MemoryRouter>,
    );
  }

  /** Advance timers and flush the async connect that fires on the tick. */
  async function advance(ms: number) {
    await act(async () => {
      await vi.advanceTimersByTimeAsync(ms);
    });
  }

  it("retries when the ticket request rejects", async () => {
    apiMocks.buildWsUrl.mockRejectedValueOnce(
      new Error("ticket endpoint unavailable"),
    );

    await renderChat();
    await advance(0);
    expect(FakeWebSocket.instances).toHaveLength(0);

    // First backoff step is 250ms; the retry must mint a fresh ticket.
    await advance(250);
    expect(apiMocks.buildWsUrl).toHaveBeenCalledTimes(2);
    expect(FakeWebSocket.instances).toHaveLength(1);
  });

  it("times out a stalled ticket request and retries", async () => {
    let resolveStalledRequest!: (url: string) => void;
    apiMocks.buildWsUrl.mockImplementationOnce(
      () =>
        new Promise<string>((resolve) => {
          resolveStalledRequest = resolve;
        }),
    );

    await renderChat();
    await advance(0);
    expect(FakeWebSocket.instances).toHaveLength(0);

    await advance(PTY_TICKET_TIMEOUT_MS);
    expect(FakeWebSocket.instances).toHaveLength(0);

    // A late ticket from the timed-out attempt must not open a socket behind
    // the replacement the deadline scheduled.
    await act(async () => {
      resolveStalledRequest("ws://localhost/api/pty?channel=stale");
      await Promise.resolve();
    });
    expect(FakeWebSocket.instances).toHaveLength(0);

    await advance(250);
    expect(FakeWebSocket.instances).toHaveLength(1);
    expect(FakeWebSocket.instances[0].url).not.toContain("channel=stale");
  });

  it("leaves a settled ticket's socket to the CONNECTING timer", async () => {
    await renderChat();
    await advance(0);
    await vi.waitFor(
      () => expect(FakeWebSocket.instances).toHaveLength(1),
      { timeout: 15_000 },
    );

    // NS-591 regression: once the socket exists the ticket deadline is
    // disarmed, so PTY_CONNECTING_TIMEOUT_MS stays the only thing that may
    // force-close a wedged handshake — the two must not both fire.
    await advance(PTY_TICKET_TIMEOUT_MS);
    expect(apiMocks.buildWsUrl).toHaveBeenCalledTimes(1);
  });
});
