/**
 * A4 — MlsPage inventory scopes call /app/mls/inventory (not CRM /app/properties).
 */
import fs from "fs";
import path from "path";

const pagePath = path.join(
  __dirname,
  "../apps/immoweb/pages/MlsPage.jsx"
);
const src = fs.readFileSync(pagePath, "utf8");

describe("MlsPage MLS inventory (A4)", () => {
  test("loads inventory via /app/mls/inventory with scope param", () => {
    expect(src).toMatch(/\/app\/mls\/inventory\?scope=\$\{scope\}/);
    expect(src).not.toMatch(/\/app\/properties\?q=/);
  });

  test("exposes mine/local/national scope controls", () => {
    expect(src).toMatch(/id:\s*"mine"/);
    expect(src).toMatch(/id:\s*"local"/);
    expect(src).toMatch(/id:\s*"national"/);
    expect(src).toMatch(/data-testid=\{`mls-inventory-scope-\$\{t\.id\}`\}/);
  });

  test("renders inventory cards from API items", () => {
    expect(src).toMatch(/inventory\.items/);
    expect(src).toMatch(/mls-inventory-card-/);
  });

  test("handles empty inventory without CRM fallback", () => {
    expect(src).toMatch(/\(inventory\.items \|\| \[\]\)\.map/);
    expect(src).not.toMatch(/EntitySearch/);
  });
});
