# D-175 C2 · PR #232 — Critical safety review

**Scope:** `cursor/d175-c2-backup-restore-e393` vs `main` (HEAD `7d3ebc4`)  
**Focus:** Mongo endpoint isolation, wrong-DB dump/restore, missing-media false positives, secrets leakage, Mongo role privilege escalation, shared `:27017` / permanent URI touch paths.  
**Verdict:** **BLOCK merge** until hard-deny of shared `:27017` in bootstrap + endpoint allowlist (and drill pre-flight). Default-happy-path is safer after the post-review fix, but fail-closed is **not** absolute.

---

## Executive verdict

| Area | Rating | Notes |
|---|---|---|
| Endpoint isolation fail-closed | **PARTIAL** | Host:port allowlist works *when* `OMNIA_DF_MONGO_PORT=27018`. Setting that env to `27017` **authorizes** shared port. No hard deny. |
| Dump/restore wrong DB | **GOOD** (with caveats) | Name guards deny `omnia` / `omnia_df_perm*` / non-probe restore targets. Ops still run on whatever host:port the allowlist accepts. |
| Missing-media false positive | **GOOD** | Fixed: `ok:false` unless explicit opt-out. |
| Secrets in scripts/artifacts | **ACCEPTABLE / residual risk** | Creds gitignored + `0600`; manifest redacts userinfo. Residual: URI+password on process argv; weak manifest word-scrub. |
| Mongo role privilege escalation | **ACCEPTABLE on isolated instance** | Least-priv roles OK; drill uses **root admin** for dump/restore; bootstrap can create root on **any** `--port`. |
| Touch shared `:27017` / permanent | **CRITICAL residual** | Bootstrap `stop_port` + mongod start has **no** 27017 ban. Drill seed/drop bypasses endpoint assert. |

---

## CRITICAL

### C1 — Allowlist is derived from the same knob that selects the target port

`authorized_dogfood_mongo_endpoints()` defaults to loopback + `OMNIA_DF_MONGO_PORT`. If that env is `27017`, shared Cloud mongod becomes “authorized”, and `assert_dogfood_mongo_endpoint("mongodb://127.0.0.1:27017/")` **accepts**.

Also: `OMNIA_DOGFOOD_MONGO_ENDPOINTS=127.0.0.1:27017` accepts with no hard deny.

**Reproduced** in-process against PR code: both paths accept `:27017`.

Docs claim “27017 fuori allowlist di default” — true only while port stays 27018. That is **configuration fail-open**, not fail-closed.

### C2 — `dogfood_mongo_bootstrap.py` can kill/replace shared `:27017`

- `--port` / `OMNIA_DF_MONGO_PORT` unconstrained.
- `stop_port(args.port)` SIGTERM/SIGKILL whatever listens.
- Then starts mongod with dogfood `dbpath` on that port + creates `omnia_df_admin` with **`root`**.

Mis-run with port 27017 on a Cloud agent that already uses shared Mongo → outage / data-dir swap / root user on the wrong instance.

### C3 — Drill destructive Mongo ops bypass endpoint assert

`scripts/dogfood_c2_drill.py`:

- Does **not** import/call `assert_dogfood_mongo_endpoint`.
- Builds `mongodb://127.0.0.1:{OMNIA_DF_MONGO_PORT}` and uses admin `MongoClient` for `drop_database(source)` / `drop_database(probe)` **before** dump/restore helpers.
- Dump/restore *do* call the assert — but if C1 holds, they also pass against `:27017`.

So seed/drop are not independently fail-closed on host:port.

---

## HIGH

### H1 — Permanent URI guard is exact string equality

`OMNIA_DOGFOOD_PERMANENT_URI` compared with `uri.strip() == perm` only. Variants rely on DB-name checks in the path. URIs without a forbidden DB path (auth-only `/admin`) depend entirely on endpoint allowlist (see C1).

### H2 — Dump/restore tool argv embeds credential URI

`mongodump` / `mongorestore` use `--uri=mongodb://user:pass@...` → visible in process listings. `mongosh --eval` interpolates passwords into JS during bootstrap.

### H3 — Drill prefers root admin for dump/restore

Role separation is verified best-effort, but the certified drill path uses `omnia_df_admin` (root). Least-privilege is not exercised for the dangerous ops.

### H4 — Role matrix overclaims `omnia_df_probe*`

JSON/docs say probe*; grants are only `omnia_df_probe` + `omnia_df_probe_c2`. Narrower is safer; docs are inaccurate. Negative checks against shared DB name `omnia` are not in `verify_roles`.

---

## MEDIUM / LOW

### M1 — Manifest “scrub” loop is mostly dead

`write_manifest` iterates `password|passwd|secret|token|://` but only enforces credential-URI regex. Literal `"password": "..."` in JSON is allowed. Credential URI pattern **is** blocked (verified).

### M2 — Media missing: fixed, but drill does not hard-stop early

`backup_media` returns `ok:false`; drill folds that into `report.ok` but still proceeds to restore. Correct for false-positive closure; not a full abort.

### M3 — `mongodump` dumps whole DB

Collection list is presence reporting only. Wrong-DB safety still relies on name + endpoint guards.

### M4 — Secrets path hygiene: OK for git

`dogfood/.gitignore` covers `secrets/`, `backups/`, `mongo-data/`, drill JSON, role matrix. Cred file mode `600`. Sample artifacts/manifest show redacted URI without userinfo. No `MONGO_URL` / prod URI read in C2 scripts.

---

## What the post-review fix *did* get right

1. Host+port check even when URI has no DB path (negatives on `:27017` / remote hosts under default 27018).
2. Missing media → `ok:false` unless `OMNIA_DOGFOOD_ALLOW_MISSING_MEDIA=1`.
3. Restore target must be `omnia_df_probe*`; source must be `omnia_df_*` and not probe/permanent/shared names.
4. `_uri_for_tool` clears path DB so `--db=` drives dump/restore target.
5. Bind `127.0.0.1` only in bootstrap mongod.
6. Unit coverage for endpoint deny + media blocking (with default port 27018).

---

## Merge gate (minimum)

Before Founder merge of PR #232:

1. **Hard-deny port 27017** (and non-loopback) in `authorized_dogfood_mongo_endpoints`, bootstrap `--port`, and drill pre-flight — not overridable by `OMNIA_DF_MONGO_PORT` alone.
2. Bootstrap: refuse start/`stop_port` if port ∈ forbidden shared ports; never SIGKILL listener on 27017.
3. Drill: call `assert_dogfood_mongo_endpoint(uri)` **before** any `MongoClient` / `drop_database`.
4. Prefer: dump with `omnia_df_backup`, restore with `omnia_df_clone`; keep root admin out of the happy path.
5. Tests: `OMNIA_DF_MONGO_PORT=27017` must still raise; bootstrap `--port 27017` must exit non-zero without touching the listener.

Until then: treat C2 as **unsafe under misconfiguration**, safe only on the intentional default loopback:27018 happy path.
