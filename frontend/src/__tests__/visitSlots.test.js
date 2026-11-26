import {
  MIN_VISIT_PROPOSED_SLOTS,
  defaultProposedSlots,
  normalizeProposedSlots,
} from "../apps/immoweb/components/visitSlots";

describe("CMJ visitSlots", () => {
  test("requires at least three slots", () => {
    expect(MIN_VISIT_PROPOSED_SLOTS).toBe(3);
    expect(normalizeProposedSlots([]).ok).toBe(false);
    expect(normalizeProposedSlots(["2026-12-01T10:00"]).ok).toBe(false);
    expect(normalizeProposedSlots(["2026-12-01T10:00", "2026-12-01T11:00"]).ok).toBe(false);
  });

  test("accepts three valid distinct slots", () => {
    const r = normalizeProposedSlots([
      "2026-12-01T10:00",
      "2026-12-01T14:00",
      "2026-12-01T16:00",
    ]);
    expect(r.ok).toBe(true);
    expect(r.slots).toHaveLength(3);
  });

  test("rejects duplicates", () => {
    const r = normalizeProposedSlots([
      "2026-12-01T10:00",
      "2026-12-01T14:00",
      "2026-12-01T10:00",
    ]);
    expect(r.ok).toBe(false);
    expect(r.error).toMatch(/duplicat/i);
  });

  test("rejects invalid datetime", () => {
    const r = normalizeProposedSlots(["not-a-date", "2026-12-01T14:00", "2026-12-01T16:00"]);
    expect(r.ok).toBe(false);
  });

  test("defaultProposedSlots returns three values", () => {
    const slots = defaultProposedSlots(new Date("2026-11-25T12:00:00"));
    expect(slots).toHaveLength(3);
    expect(normalizeProposedSlots(slots).ok).toBe(true);
  });
});
