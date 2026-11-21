/**
 * A-007 FE — regression: diagnostic missing_* flags must not surface as chips.
 */
import {
  HIDDEN_LISTING_CHIP_FLAGS,
  visibleListingFlags,
} from "../apps/immoweb/listingFlagVisibility";

describe("visibleListingFlags (A-007 FE chip filter)", () => {
  test("missing_created_at alone → no visible chips", () => {
    expect(visibleListingFlags(["missing_created_at"])).toEqual([]);
  });

  test("missing_updated_at alone → no visible chips", () => {
    expect(visibleListingFlags(["missing_updated_at"])).toEqual([]);
  });

  test("both missing_* together → no technical chips", () => {
    expect(
      visibleListingFlags(["missing_created_at", "missing_updated_at"])
    ).toEqual([]);
  });

  test("known flags still visible with same labels path (order preserved)", () => {
    const input = ["no_photos", "incomplete", "weak_copy", "no_match", "price_drop"];
    expect(visibleListingFlags(input)).toEqual(input);
  });

  test("known flags kept when mixed with missing_*", () => {
    expect(
      visibleListingFlags([
        "no_photos",
        "missing_created_at",
        "price_drop",
        "missing_updated_at",
      ])
    ).toEqual(["no_photos", "price_drop"]);
  });

  test("unknown flags other than missing_* keep previous fallback behaviour (pass through)", () => {
    expect(visibleListingFlags(["custom_future_flag", "xyz"])).toEqual([
      "custom_future_flag",
      "xyz",
    ]);
  });

  test("null / undefined / empty → empty list", () => {
    expect(visibleListingFlags(null)).toEqual([]);
    expect(visibleListingFlags(undefined)).toEqual([]);
    expect(visibleListingFlags([])).toEqual([]);
  });

  test("hidden set is exactly the two diagnostic flags", () => {
    expect([...HIDDEN_LISTING_CHIP_FLAGS].sort()).toEqual([
      "missing_created_at",
      "missing_updated_at",
    ].sort());
  });
});
