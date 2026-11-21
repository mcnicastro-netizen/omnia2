/**
 * A-007 FE — listing_flags shown as chips on the property list.
 * Backend may attach diagnostic flags; these must stay in the API payload
 * but must not appear as user-facing chips.
 */
export const HIDDEN_LISTING_CHIP_FLAGS = Object.freeze([
  "missing_created_at",
  "missing_updated_at",
]);

const HIDDEN = new Set(HIDDEN_LISTING_CHIP_FLAGS);

/**
 * @param {string[]|null|undefined} flags
 * @returns {string[]}
 */
export function visibleListingFlags(flags) {
  if (!flags?.length) return [];
  return flags.filter((f) => !HIDDEN.has(f));
}
