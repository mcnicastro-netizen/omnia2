import { formatEUR } from "../apps/immocloud/cloudTheme";

describe("formatEUR", () => {
  test("null → em dash", () => {
    expect(formatEUR(null)).toBe("—");
  });
  test("formatta in EUR senza decimali", () => {
    const s = formatEUR(250000);
    expect(s).toContain("250.000");
    expect(s).toContain("€");
  });
});
