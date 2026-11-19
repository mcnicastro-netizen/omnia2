# D-175 C3 · PR #233 — Critical safety review

**Scope:** `cursor/d175-c3-permanent-base-e393` vs `main` (HEAD `9c66651`)  
**Focus:** permanent base integrity under ordinary/runtime paths, one-shot init, sealed emergency, admin residual.  
**Verdict:** **Do not block merge** on C3 integrity criteria after `9c66651`. Residuals are explicit; Founder still owns the merge button.

---

## Executive verdict

| Area | Rating | Notes |
|---|---|---|
| Verify read-only | **GOOD** | No init; fingerprint + text + marker count |
| Init one-shot | **GOOD** | IDENTITY / sealed emergency / DB marker refuse |
| Emergency secret separation | **GOOD** | Not in general creds; sealed `0600` |
| Perimeter / ordinary deny | **GOOD** | T1–T6 + unit; work copies still allowed |
| Emergency gates | **GOOD** | Multi-gate; destructive execute refused in C3 |
| Admin/root escalation | **ACCEPTABLE residual** | Root can mutate permanent; documented |
| Identity ↔ marker | **GOOD** on verify | Emergency prove path skips marker (execute blocked) |

---

## CRITICAL (pre-fix — cleared on `9c66651`)

### Was C1 — Verify re-initialized the permanent base

Previously verify shelled out to `dogfood_permanent_init.py`. **Cleared:** verify is read-only; live 16/16; `instance_id` stable.

### Was C2 — Init could wipe / rewrite marker

Previously `delete_many` on marker collection. **Cleared:** refuse if IDENTITY/emergency/marker present; no wipe path.

### Was C3 — Emergency password in general credentials

Previously written into `mongo-df-credentials.json`. **Cleared:** sealed file only; assert + live keys check.

---

## HIGH residuals (not merge-blocking for C3)

### H1 — `omnia_df_admin` remains root with password in ordinary creds file

Any holder of `mongo-df-credentials.json` can write/drop permanent via admin, bypassing runtime/clone Mongo roles and ordinary_ops gates (gates only bind scripts that call them).

C3 documents this: base is **not** filesystem-immutable. Hardening (split admin, deny admin URI in ordinary tool wrappers) = later cycle.

### H2 — Emergency `--prove-gates` does not cross-check Mongo marker

Only `require_identity_or_raise()` (file). Mismatch would still “prove” gates. Mitigated because destructive restore is policy-blocked in C3. Fix before enabling execute.

### H3 — Unlock token may be literal `1`

By design Founder one-shot; compensated by phrase + dual confirm. Not sufficient alone against env injection on a shared shell history — treat unlock env as sensitive.

---

## MEDIUM / LOW

### M1 — Partial init can stick the environment

Crash after marker/emergency write but before IDENTITY → reinit DENY, verify FAIL until Founder cleans files/DB. Fail-closed preferred over silent rewrite.

### M2 — T15 overlaps T14

“Ordinary cannot see emergency” is proven by file separation + code paths, not an OS ACL test.

### M3 — `is_permanent_db_name` prefix greed

`startswith("omnia_df_perm")` would treat odd names like `omnia_df_permutation` as permanent. Unlikely; deny-side false positive only.

### L1 — Passwords in mongosh `--eval` / tool argv

Same class as C2 H2 (process listing). Residual on isolated Dogfood host.

---

## Proof commands (re-runnable)

```bash
# units
cd backend && .venv/bin/python -m pytest tests/test_d175_c3_permanent.py tests/test_d175_c1_dogfood_perimeter.py -q

# reinit refuse
python3 scripts/dogfood_permanent_init.py   # expect FAIL …IDENTITY_exists, exit 2

# read-only verify
python3 scripts/dogfood_c3_verify.py        # expect 16/16, stable instance_id
```

---

## Bottom line for ChatGPT / Founder

The three review-blocking defects called out against the first C3 commit are **fixed on `9c66651`**. Remaining issues are **documented residuals** aligned with C3 scope (isolated loopback Dogfood, no claim of absolute immutability).  

**Merge-blocking: no.**  
**Merge without Founder: no.**
