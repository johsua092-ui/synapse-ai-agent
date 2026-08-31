import { describe, it, expect } from "vitest";
import {
  EFFORT_OPTIONS,
  VALID_EFFORTS,
  normalizeEffort,
} from "./reasoning-effort";

describe("normalizeEffort", () => {
  it("treats empty/unset as the Synapse default (medium)", () => {
    expect(normalizeEffort("")).toBe("medium");
    expect(normalizeEffort(null)).toBe("medium");
    expect(normalizeEffort(undefined)).toBe("medium");
    expect(normalizeEffort("   ")).toBe("medium");
  });

  it("passes through every dashboard effort level", () => {
    for (const level of ["medium", "high", "max"]) {
      expect(normalizeEffort(level)).toBe(level);
    }
  });

  it("migrates disabled and unsupported values to medium", () => {
    for (const value of ["none", "false", "off", "disabled", "minimal", "low", "xhigh", "ultra"]) {
      expect(normalizeEffort(value)).toBe("medium");
    }
  });

  it("is case- and whitespace-insensitive", () => {
    expect(normalizeEffort("HIGH")).toBe("high");
    expect(normalizeEffort("  Max  ")).toBe("max");
  });

  it("falls back to medium for unknown values", () => {
    expect(normalizeEffort("turbo")).toBe("medium");
    expect(normalizeEffort(42)).toBe("medium");
  });
});

describe("EFFORT_OPTIONS", () => {
  it("every option value is in VALID_EFFORTS (no orphan labels)", () => {
    for (const opt of EFFORT_OPTIONS) {
      expect(VALID_EFFORTS.has(opt.value)).toBe(true);
    }
  });

  it("offers only the approved always-on levels with trade-offs", () => {
    expect(EFFORT_OPTIONS).toEqual([
      { value: "medium", label: "Medium - balanced speed and cost" },
      { value: "high", label: "High - deeper, slower, and costlier" },
      { value: "max", label: "Max - strongest, slowest, and costliest" },
    ]);
  });
});
