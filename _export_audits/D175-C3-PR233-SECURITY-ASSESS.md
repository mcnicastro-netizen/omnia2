# D-175 C3 · PR #233 — Security assessment (criterion map)

**Target:** https://github.com/mcnicastro-netizen/omnia2/pull/233  
**HEAD reviewed:** `9c66651` (`cursor/d175-c3-permanent-base-e393`)  
**Date:** 19 novembre 2026 · Europe/Rome  
**Scope:** verify read-only integrity · reinit refuse · emergency credential separation · perimeter permanent deny · ordinary ops gates · emergency unlock gates · privilege escalation via admin/root · identity/marker mismatch  
**Related:** `/opt/cursor/artifacts/D175-C3-CRITICAL-SAFETY-REVIEW.md`

**Verdict:** **Not merge-blocking** on the eight C3 criteria after fix `9c66651`. Residual admin/root power on the isolated Dogfood instance remains **documented and accepted** for C3 (base is not filesystem-immutable). Merge still requires Founder authorization (out of agent scope).

---

## Criterion results

| # | Criterion | Severity if broken | Result |
|---|---|---|---|
| 1 | Verify read-only integrity | CRITICAL | **PASS** — no `permanent_init`; no IDENTITY/marker rewrite; T16 + live `instance_id` stable |
| 2 | Reinit refuse | CRITICAL | **PASS** — IDENTITY / emergency sealed file / DB marker → DENY (`exit 2`) |
| 3 | Emergency credential separation | HIGH | **PASS** — sealed path only; absent from `mongo-df-credentials.json` |
| 4 | Perimeter permanent deny | CRITICAL | **PASS** — runtime + alt-URI + emergency-as-runtime denied |
| 5 | Ordinary ops gates | CRITICAL | **PASS** — clone/wipe/restore/migrate → DENY on permanent; work copies OK |
| 6 | Emergency unlock gates | HIGH | **PASS** — missing/wrong/incomplete DENY; full gates + `--prove-gates` PASS; execute blocked in C3 |
| 7 | Privilege escalation via admin/root | HIGH (residual) | **ACCEPTABLE residual** — `omnia_df_admin` **can** write permanent; documented; ordinary runtime/clone cannot |
| 8 | Identity/marker mismatch | HIGH | **PASS** — verify fails closed on missing/mismatched marker |

---

## 1. Verify read-only integrity

### What was broken (pre-`9c66651`)

`dogfood_c3_verify.py` invoked `dogfood_permanent_init.py`, so a “verify” could rewrite IDENTITY / roles / backup.

### What works now

- AST/subprocess scan: verify does **not** call `dogfood_permanent_init.py` and does not call `write_identity`.
- Requires existing IDENTITY; missing → FAIL.
- Pre/post `identity_fingerprint` + raw `IDENTITY.json` text + marker count (T16).
- Sidecar write `permanent/C3_LAST_VERIFY.json` is a report only (not IDENTITY).

### Live evidence (`9c66651`)

- Verify: **16/16 PASS**, `mode=read_only_verify`, `instance_id=aba62b63-…` unchanged before/after.
- Unit: `tests/test_d175_c3_permanent.py` + C1 perimeter → **40 passed**.

---

## 2. Reinit refuse

`refuse_reinitialization_if_present()` DENY if:

- `IDENTITY.json` exists → `permanent_already_initialized:IDENTITY_exists`
- sealed `emergency-credentials.json` exists → `…:emergency_creds_exist`

Init also DENY if Mongo marker collection already has docs → `…:marker_exists` (no `delete_many` wipe).

**Live:** re-run init → `FAIL permanent_already_initialized:IDENTITY_exists`, **exit 2**.

**Residual (not blocking):** operator who deletes IDENTITY + sealed emergency + marker can force a new init. That is intentional Founder break-glass via filesystem, not silent wipe.

---

## 3. Emergency credential separation

| Store | Contents |
|---|---|
| `dogfood/secrets/mongo-df-credentials.json` | `admin`, `runtime`, `clone`, `backup` only (`0600`) |
| `dogfood/permanent/secrets/emergency-credentials.json` | `omnia_df_emergency` password only (`0600`) |

- Init generates emergency pwd into sealed file only; strips legacy `emergency` key from general file.
- `assert_general_creds_have_no_emergency` used by init + verify.
- Live disk: `has_emergency=False` on general; sealed `user=omnia_df_emergency`.

T14/T15 PASS. T15 is slightly redundant with T14 (path separation is by convention/code review, not a runtime ACL).

---

## 4. Perimeter permanent deny

`perimeter.check_dogfood_db_isolation` (C3 hooks):

- `db_name_is_permanent` for `omnia_df_perm*`
- `mongo_url_is_permanent` via `is_permanent_runtime_target` (alt creds on same endpoint+db; emergency user on permanent endpoint)

Live T1/T2 PASS. Unit coverage in C3 + C1 suites.

---

## 5. Ordinary ops gates

`ordinary_ops.*_allowed` → `assert_not_permanent_op` for clone/wipe/restore/migrate_destructive.

- Permanent target → `ok: false`
- Work copies (`omnia_df_clean_*`, etc.) → `ok: true`
- CLI `scripts/dogfood_ordinary_ops.py` is gate-probe only (no destructive execution)

C2 `backup.assert_safe_db_name` still forbids `omnia_df_perm*` independently.

---

## 6. Emergency unlock gates

`check_emergency_unlock_gates`: unlock token + exact auth phrase + double confirm.

| Case | Result |
|---|---|
| No unlock env | DENY (T9, script rc≠0) |
| Wrong phrase | DENY (T10) |
| Confirm incomplete | DENY (T11) |
| All gates + `--prove-gates` | PASS + audit append (T12) |
| `--execute-restore` even with `OMNIA_PERMANENT_EXECUTE=1` | DENY `destructive_restore_not_authorized_in_c3` |

**Residual:** unlock token literal `"1"` is a Founder one-shot by design; strength is phrase + dual confirm + separate execute flag (still refused in C3).

---

## 7. Privilege escalation via admin/root

**Reproduced:** `omnia_df_admin` (root, password in general creds) **can** `insert` on `omnia_df_perm_main` (probe inserted then deleted).

| Actor | Write permanent? |
|---|---|
| `omnia_df_runtime` | DENY (T7) |
| `omnia_df_clone` | DENY (T8) |
| `omnia_df_emergency` | RW role exists; password sealed; restore path gated |
| `omnia_df_admin` | **YES** — residual |

Docs + verify report state residual explicitly. C3 threat model = accidental ordinary/runtime paths, not hostile holder of Dogfood admin secrets on loopback `:27018`.

**Not merge-blocking** for stated C3 scope. Absolute immutability / admin split would be a later hardening cycle.

---

## 8. Identity / marker mismatch

Verify (read-only):

1. IDENTITY missing/invalid → FAIL `permanent_identity_*`
2. Marker missing → FAIL `permanent_marker_missing`
3. `instance_id` mismatch → FAIL `identity_marker_mismatch`

**Live tamper:** IDENTITY `instance_id` rewritten → verify rc 2 with mismatch payload; restore → 16/16 PASS again.

**Note (non-blocking):** `dogfood_permanent_emergency_restore.py` checks IDENTITY file only (no marker cross-check). Acceptable while C3 blocks destructive execute; recommend marker check before any future execute path (C4+).

---

## Evidence index

| Artifact | Meaning |
|---|---|
| `/opt/cursor/artifacts/D175-C3-UNIT-ASSESS.txt` | 40 passed |
| `/opt/cursor/artifacts/D175-C3-REINIT-REFUSE.txt` | reinit DENY |
| `/opt/cursor/artifacts/D175-C3-VERIFY-REASSESS.txt` | 16/16 read-only |
| `/opt/cursor/artifacts/D175-C3-ADMIN-RESIDUAL-PROBE.txt` | admin can write |
| `/opt/cursor/artifacts/D175-C3-MISMATCH-PROBE.txt` | mismatch FAIL + restore |
| `dogfood/permanent/C3_LAST_VERIFY.json` | last live verify report |

CI on HEAD: Backend billing / B04 unit **success**.

---

## Merge recommendation

| Question | Answer |
|---|---|
| Merge-blocking findings on the 8 criteria? | **No** |
| Founder merge authorization still required? | **Yes** (D-175 / PR policy) |
| Follow-ups (non-blocking) | Marker cross-check on emergency execute; optional admin/emergency further sealing; T15 stronger than “key absent” |
