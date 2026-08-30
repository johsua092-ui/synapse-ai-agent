// @vitest-environment jsdom
import { act, type ReactNode } from "react";
import { createRoot, type Root } from "react-dom/client";
import { MemoryRouter } from "react-router";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import type { SessionInfo } from "@/lib/api";

Object.assign(globalThis, { IS_REACT_ACT_ENVIRONMENT: true });

// This box (Termux/proot) is slow under load; keep the suite immune to it.
vi.setConfig({ testTimeout: 20_000 });

function keydown(el: HTMLElement, key: string) {
  el.dispatchEvent(
    new KeyboardEvent("keydown", { key, bubbles: true, cancelable: true }),
  );
}

const apiMocks = vi.hoisted(() => ({
  getSessions: vi.fn(
    async (): Promise<{ sessions: SessionInfo[] }> => ({ sessions: [] }),
  ),
  renameSession: vi.fn(async (_id: string, title: string) => ({
    ok: true,
    title,
  })),
setSessionPinned: vi.fn(async (_id: string, pinned: boolean) => ({
    ok: true,
    pinned,
  })),
  deleteSession: vi.fn(async () => ({ ok: true })),
}));

vi.mock("@/lib/api", () => ({ api: apiMocks }));

vi.mock("@nous-research/ui/ui/components/button", () => ({
  Button: ({
    children,
    onClick,
    title,
  }: {
    children?: ReactNode;
    onClick?: () => void;
    title?: string;
  }) => (
    <button type="button" onClick={onClick} title={title}>
      {children}
    </button>
  ),
}));

vi.mock("@nous-research/ui/ui/components/list-item", () => ({
  ListItem: ({
    children,
    onClick,
  }: {
    children?: ReactNode;
    onClick?: () => void;
  }) => (
    <div role="button" tabIndex={0} onClick={onClick}>
      {children}
    </div>
  ),
}));

vi.mock("@nous-research/ui/ui/components/spinner", () => ({
  Spinner: () => <span>spinner</span>,
}));

vi.mock("@/components/DeleteConfirmDialog", () => ({
  DeleteConfirmDialog: ({
    open,
    onConfirm,
    onCancel,
  }: {
    open?: boolean;
    onConfirm?: () => void;
    onCancel?: () => void;
  }) =>
    open ? (
      <div data-testid="delete-dialog">
        <button type="button" onClick={onConfirm}>
          confirm-delete
        </button>
        <button type="button" onClick={onCancel}>
          cancel-delete
        </button>
      </div>
    ) : null,
}));

const SESSIONS: SessionInfo[] = [
  {
    id: "s1",
    title: "Alpha",
    preview: "first preview",
    last_active: 100,
    message_count: 3,
    source: "cli",
    model: null,
    started_at: 90,
    ended_at: null,
    is_active: false,
    tool_call_count: 2,
    input_tokens: 10,
    output_tokens: 20,
  },
  {
    id: "s2",
    title: "Untitled",
    preview: "second preview",
    last_active: 200,
    message_count: 0,
    source: "cli",
    model: null,
    started_at: 180,
    ended_at: null,
    is_active: false,
    tool_call_count: 0,
    input_tokens: 0,
    output_tokens: 0,
    pinned: true,
  },
];

let container: HTMLDivElement;
let root: Root;

async function render(ui: ReactNode) {
  container = document.createElement("div");
  document.body.append(container);
  root = createRoot(container);
  await act(async () =>
    root.render(<MemoryRouter initialEntries={["/chat"]}>{ui}</MemoryRouter>),
  );
}

function manageButtons() {
  return Array.from(
    container.querySelectorAll<HTMLButtonElement>(
      'button[title="Conversation actions"]',
    ),
  );
}

function menuButtons() {
  return Array.from(container.querySelectorAll<HTMLButtonElement>("button"));
}

function input() {
  return container.querySelector<HTMLInputElement>('input[aria-label="Rename chat"]');
}

function setInputValue(el: HTMLInputElement, value: string) {
  const setter = Object.getOwnPropertyDescriptor(
    window.HTMLInputElement.prototype,
    "value",
  )!.set!;
  setter.call(el, value);
  el.dispatchEvent(new Event("input", { bubbles: true }));
}

beforeEach(() => {
  vi.clearAllMocks();
  apiMocks.getSessions.mockResolvedValue({ sessions: [...SESSIONS] });
  apiMocks.renameSession.mockResolvedValue({ ok: true, title: "Beta" });
  apiMocks.deleteSession.mockResolvedValue({ ok: true });
});

afterEach(async () => {
  await act(async () => root?.unmount());
  container?.remove();
});

describe("ChatSessionList manage menu", () => {
  it("opens a menu with Pin, Rename and Delete per row", async () => {
    const { ChatSessionList } = await import("./ChatSessionList");
    await render(<ChatSessionList activeSessionId={null} />);

    await vi.waitFor(() => expect(apiMocks.getSessions).toHaveBeenCalled());
    expect(container.textContent).toContain("Alpha");
    expect(manageButtons()).toHaveLength(2);

    await act(async () => {
      manageButtons()[1].click();
    });
    expect(container.textContent).toContain("Pin chat");
    expect(container.textContent).toContain("Rename");
    expect(container.textContent).toContain("Delete session");
  });

  it("renders pinned sessions first", async () => {
    const { ChatSessionList } = await import("./ChatSessionList");
    await render(<ChatSessionList activeSessionId={null} />);
    await vi.waitFor(() => expect(apiMocks.getSessions).toHaveBeenCalled());

    // s2 is pinned in the fixture, so it must be listed above s1.
    expect(
      container.textContent!.indexOf("second preview"),
    ).toBeLessThan(container.textContent!.indexOf("Alpha"));
  });

  it("pins via api.setSessionPinned and moves the row to the top", async () => {
    const { ChatSessionList } = await import("./ChatSessionList");
    await render(<ChatSessionList activeSessionId={null} />);
    await vi.waitFor(() => expect(apiMocks.getSessions).toHaveBeenCalled());

    await act(async () => {
      manageButtons()[1].click();
    });
    await act(async () => {
      menuButtons().find((b) =>
        b.textContent?.includes("Pin chat"),
      )!.click();
    });

    expect(apiMocks.setSessionPinned).toHaveBeenCalledWith("s1", true);
    // s1 is now pinned too; both pinned keep API order (s1 before s2).
    await vi.waitFor(() => {
      expect(container.textContent!.indexOf("Alpha")).toBeLessThan(
        container.textContent!.indexOf("second preview"),
      );
    });
  });

  it("unpins a pinned row and drops it back below unpinned ones", async () => {
    const { ChatSessionList } = await import("./ChatSessionList");
    await render(<ChatSessionList activeSessionId={null} />);
    await vi.waitFor(() => expect(apiMocks.getSessions).toHaveBeenCalled());

    await act(async () => {
      manageButtons()[0].click();
    });
    expect(container.textContent).toContain("Unpin chat");

    await act(async () => {
      menuButtons().find((b) =>
        b.textContent?.includes("Unpin chat"),
      )!.click();
    });
    expect(apiMocks.setSessionPinned).toHaveBeenCalledWith("s2", false);
    // Nothing pinned anymore → API (recency) order: s1 first.
    await vi.waitFor(() => {
      expect(container.textContent!.indexOf("Alpha")).toBeLessThan(
        container.textContent!.indexOf("second preview"),
      );
    });
  });

  it("renames inline through api.renameSession", async () => {
    const { ChatSessionList } = await import("./ChatSessionList");
    await render(<ChatSessionList activeSessionId={null} />);
    await vi.waitFor(() => expect(apiMocks.getSessions).toHaveBeenCalled());

    await act(async () => {
      manageButtons()[1].click();
    });
    await act(async () => {
      menuButtons().find((b) =>
        b.textContent?.includes("Rename"),
      )!.click();
    });

    const el = input();
    expect(el).toBeTruthy();
    expect(el!.value).toBe("Alpha");

    await act(async () => {
      setInputValue(el!, "Beta");
    });
    await act(async () => {
      keydown(el!, "Enter");
    });

    expect(apiMocks.renameSession).toHaveBeenCalledWith("s1", "Beta");
    expect(container.textContent).toContain("Beta");
  });

  it("Escape cancels rename without calling the API", async () => {
    const { ChatSessionList } = await import("./ChatSessionList");
    await render(<ChatSessionList activeSessionId={null} />);
    await vi.waitFor(() => expect(apiMocks.getSessions).toHaveBeenCalled());

    await act(async () => {
      manageButtons()[1].click();
    });
    await act(async () => {
      menuButtons().find((b) =>
        b.textContent?.includes("Rename"),
      )!.click();
    });
    const el = input();
    await act(async () => {
      keydown(el!, "Escape");
    });

    expect(apiMocks.renameSession).not.toHaveBeenCalled();
    expect(input()).toBeNull();
  });

  it("deletes a session after confirmation", async () => {
    const { ChatSessionList } = await import("./ChatSessionList");
    await render(<ChatSessionList activeSessionId={null} />);
    await vi.waitFor(() => expect(apiMocks.getSessions).toHaveBeenCalled());

    await act(async () => {
      manageButtons()[1].click();
    });
    await act(async () => {
      menuButtons().find((b) =>
        b.textContent?.includes("Delete session"),
      )!.click();
    });

    expect(
      container.querySelector('[data-testid="delete-dialog"]'),
    ).toBeTruthy();

    await act(async () => {
      container
        .querySelector<HTMLButtonElement>(
          '[data-testid="delete-dialog"] button',
        )!
        .click();
    });

    expect(apiMocks.deleteSession).toHaveBeenCalledWith("s1");
    await vi.waitFor(() => {
      expect(container.textContent).not.toContain("Alpha");
    });
  });

  it("leaves the session when delete is cancelled", async () => {
    const { ChatSessionList } = await import("./ChatSessionList");
    await render(<ChatSessionList activeSessionId={null} />);
    await vi.waitFor(() => expect(apiMocks.getSessions).toHaveBeenCalled());

    await act(async () => {
      manageButtons()[1].click();
    });
    await act(async () => {
      menuButtons().find((b) =>
        b.textContent?.includes("Delete session"),
      )!.click();
    });

    await act(async () => {
      const dialog = container.querySelector(
        '[data-testid="delete-dialog"]',
      );
      Array.from(dialog!.querySelectorAll("button"))
        .find((b) => b.textContent?.includes("cancel-delete"))!
        .click();
    });

    expect(apiMocks.deleteSession).not.toHaveBeenCalled();
    expect(container.textContent).toContain("Alpha");
  });
});