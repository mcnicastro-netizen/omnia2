# D-175 C3 · PR #233 — Critical safety review

**Target:** https://github.com/mcnicastro-netizen/omnia2/pull/233  
**Branch:** `cursor/d175-c3-permanent-base-e393` vs `main`  
**HEAD:** `9c66651`  
**Date:** 2026-11-19  

## Verdict: APPROVE (not merge-blocking)

The six critical criteria pass on `9c66651`. Residuals remain (admin root, loopback host-alias detection gap) but do **not** open an ordinary/runtime write path to the permanent base under the C3 threat model. Merge still requires Founder authorization.

| # | Criterion | Result |
|---|---|---|
| 1 | `dogfood_c3_verify` read-only | **PASS** |
| 2 | `permanent_init` refuse re-init | **PASS** |
| 3 | Emergency password not in general creds | **PASS** |
| 4 | Runtime/clone write-deny on permanent | **PASS** |
| 5 | Bypass via URI/host/port/admin | **PASS** for mutation paths; **residual** host-alias detection gap |
| 6 | Residual `omnia_df_admin` risk | **Documented residual** (accepted for C3) |

---

## 1. Verify read-only — PASS

`scripts/dogfood_c3_verify.py` on `9c66651`:

- Does **not** subprocess/import `dogfood_permanent_init.py` (fixed vs first commit `4d6cad2`).
- Does **not** call `write_identity`, role upsert, or permanent backup rewrite.
- Requires existing IDENTITY; missing → FAIL.
- Reads marker only; T16 compares fingerprint + raw IDENTITY text + marker count.
- Sidecar `C3_LAST_VERIFY.json` + append-only `EMERGENCY_AUDIT.jsonl` (via `--prove-gates`) are intentional non-IDENTITY side effects.

**Note:** `_try_write` against permanent expects DENY; if roles were broken it would insert+delete a probe (failure path mutates). Detected as T7/T8 FAIL — acceptable for a privilege probe.

---

## 2. Init one-shot — PASS

`refuse_reinitialization_if_present()` DENY if:

- `IDENTITY.json` exists → `permanent_already_initialized:IDENTITY_exists`
- sealed emergency creds exist → `…:emergency_creds_exist`

Init also DENY if Mongo `_omnia_permanent_identity` already has docs → `…:marker_exists`.  
No `delete_many` wipe of marker (removed in `9c66651`).

**Live:** re-run init → `FAIL permanent_already_initialized:IDENTITY_exists`, exit 2.

---

## 3. Emergency password separation — PASS

| File | Keys |
|---|---|
| `dogfood/secrets/mongo-df-credentials.json` | `admin`, `runtime`, `clone`, `backup` only |
| `dogfood/permanent/secrets/emergency-credentials.json` | `omnia_df_emergency` only (`0600`) |

Init writes emergency **only** to sealed path; strips legacy `emergency` from general; `assert_general_creds_have_no_emergency` in init + verify.  
`dogfood/permanent/` is gitignored. Live disk: `emergency in general = False`.

---

## 4. Runtime/clone write-deny — PASS

**Application gates:** `perimeter.check_dogfood_db_isolation` + `ordinary_ops` deny permanent targets (T1–T6).

**Mongo RBAC (live on :27018):**

- `omnia_df_runtime` → `OperationFailure` insert on `omnia_df_perm_main`
- `omnia_df_clone` → `OperationFailure` insert on `omnia_df_perm_main`
- Roles grant runtime RW only on work/`c2_src`; clone read-only on permanent.

Unit: 40 passed (`test_d175_c3_permanent` + C1 perimeter).

---

## 5. Bypass via URI / host / port / admin — PASS (with residual)

### Blocked (mutation-relevant)

- `DB_NAME=omnia_df_perm*` → perimeter DENY regardless of host alias (`db_name_is_permanent`).
- Alt URI with same endpoint + permanent DB on `127.0.0.1` → DENY.
- Ordinary clone/wipe/restore/migrate targeting permanent → DENY by name.
- Port `27017` refused for identity builder; permanent init hard-denies shared port.
- App DB selection uses `client[DB_NAME]` (`shared/db/connection.py`), not URI path default DB.

### Residual H4 — loopback host alias in `matches_permanent_endpoint`

Registered permanent endpoint is `127.0.0.1:27018`. Exact host string match → `localhost` / `::1` do **not** match.

Reproduced probes (`/opt/cursor/artifacts/D175-C3-HOST-ALIAS-PROBES.json`):

| Case | Perimeter |
|---|---|
| `localhost` + URI path=`omnia_df_perm_main` + `DB_NAME=work` | **ALLOW** (detection miss) |
| `omnia_df_emergency@localhost` + `DB_NAME=work` | **ALLOW** (user check skipped when endpoint mismatch) |
| same emergency user on `127.0.0.1` + work | **DENY** |
| `localhost` + `DB_NAME=omnia_df_perm_main` | **DENY** (name gate) |

**Why not BLOCK:** layered controls still prevent ordinary permanent writes:

1. Permanent as `DB_NAME` → name DENY.
2. Runtime/clone RBAC cannot write permanent even if connected.
3. Emergency role is RW **only** on permanent; with `DB_NAME=work` the app cannot write work and cannot set `DB_NAME=perm` through perimeter.
4. Main API never uses `get_default_database()` from URI path.

**Follow-up (non-blocking):** normalize loopback aliases in `matches_permanent_endpoint` / always inspect URI `path_db` for permanent prefixes even when host alias differs; treat `omnia_df_admin` like emergency for runtime URI user checks.

### Admin URI

`omnia_df_admin` as `MONGO_URL` with work `DB_NAME` is allowed by perimeter (expected). Admin **can** write permanent out-of-band — see §6.

---

## 6. Residual `omnia_df_admin` — documented, accepted for C3

- Root role; password lives in general `mongo-df-credentials.json`.
- Can insert/drop on permanent; can delete marker + IDENTITY to force a new init.
- Documented in `docs/dogfood/C3-PERMANENT-BASE.md` and verify report `residual_risk`.
- C3 threat model: accidental ordinary/runtime paths on isolated loopback Dogfood — **not** hostile holder of Dogfood admin secrets / filesystem.

Not merge-blocking. Later hardening: split admin, deny admin URI in ordinary wrappers, optional filesystem immutability claims out of scope.

---

## Cleared blockers from first commit (`4d6cad2` → `9c66651`)

1. Verify called `permanent_init` → removed.  
2. Init wiped marker via `delete_many` → removed; one-shot refuse.  
3. Emergency password written into general creds → sealed only.

---

## Evidence

| Artifact | Result |
|---|---|
| Unit C3+C1 | 40 passed |
| Reinit | exit 2 `IDENTITY_exists` |
| Live RBAC | runtime/clone DENIED write |
| Host-alias probes | see JSON artifact |
| General creds keys | no `emergency` |

---

## Bottom line

**APPROVE** for C3 safety criteria on `9c66651`.  
Do **not** merge without Founder.  
Optional follow-ups: loopback alias normalization; marker cross-check before any future emergency execute; admin secret split.
