/**
 * D04 — mapping rif. card ImmobilCloud (API → helper FE).
 */
import { cardReferenceCode, cardReferenceLabel } from "../apps/immocloud/lib/cardReference";

describe("cardReferenceCode / cardReferenceLabel (D04)", () => {
  test("mostra reference_code valorizzato", () => {
    expect(cardReferenceCode({ id: "uuid-1", reference_code: "OM-L-ABC123" })).toBe("OM-L-ABC123");
    expect(cardReferenceLabel({ reference_code: "OM-L-ABC123" }, "Rif.")).toBe("Rif. OM-L-ABC123");
  });

  test("assenza reference_code → null (niente codice artificiale / UUID)", () => {
    expect(cardReferenceCode({ id: "3b81db11-2988-47a7-ae26-f4396913c3a7" })).toBeNull();
    expect(cardReferenceCode({ id: "x", reference_code: "" })).toBeNull();
    expect(cardReferenceCode({ id: "x", reference_code: "   " })).toBeNull();
    expect(cardReferenceCode({ id: "x", reference_code: null })).toBeNull();
    expect(cardReferenceLabel({ id: "uuid-only" }, "Rif.")).toBeNull();
  });

  test("più risultati con riferimenti differenti restano distinti", () => {
    const items = [
      { id: "a", reference_code: "OM-L-AAAA01" },
      { id: "b", reference_code: "OM-L-BBBB02" },
      { id: "c", reference_code: null },
    ];
    const labels = items.map((p) => cardReferenceLabel(p, "Rif."));
    expect(labels).toEqual(["Rif. OM-L-AAAA01", "Rif. OM-L-BBBB02", null]);
    expect(new Set(labels.filter(Boolean)).size).toBe(2);
  });

  test("non usa agency_id / ObjectId come fallback rif.", () => {
    const p = {
      id: "prop-uuid",
      agency_id: "ag-secret",
      agency: { id: "ag-secret", name: "Casa" },
      reference_code: undefined,
    };
    expect(cardReferenceCode(p)).toBeNull();
    expect(cardReferenceLabel(p)).toBeNull();
  });

  test("trim spazi su reference_code", () => {
    expect(cardReferenceCode({ reference_code: "  OM-L-TRIM  " })).toBe("OM-L-TRIM");
  });
});
