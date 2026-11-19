# D-175 C2 · PR #232 — Security assessment (criterion map)

**Target:** https://github.com/mcnicastro-netizen/omnia2/pull/232  
**HEAD reviewed:** `7d3ebc4` (`cursor/d175-c2-backup-restore-e393`)  
**Date:** 19 novembre 2026 · Europe/Rome  
**Scope:** host/port allowlist bypass · URI parsing · mongodump/mongorestore injection · media path traversal · credential file handling · restore → production/shared DB  
**Related artifact:** `/opt/cursor/artifacts/D175-C2-CRITICAL-SAFETY-REVIEW.md` (merge-block framing)

**Verdict:** **Do not merge** until shared-port hard-deny + bootstrap/`stop_port` guard + drill pre-assert. Happy path on loopback:`27018` is materially safer after the post-review fix; fail-closed is **not** absolute under env misconfiguration.

---

## Criterion results

| # | Criterion | Severity | Result |
|---|---|---|---|
| 1 | Host/port allowlist bypass | **CRITICAL** | Partial — default happy path OK; `OMNIA_DF_MONGO_PORT=27017` or endpoints override **authorizes** shared mongod |
| 2 | URI parsing edge cases | **HIGH / MEDIUM** | Python vs mongoc diverge on double-`@`; permanent URI is exact-string; IPv6 env brackets mismatch |
| 3 | mongodump/mongorestore command injection | **LOW** (cleared) | `subprocess` argv list; shell metachar / fake flags stay inside single `--uri=` / `--db=` args |
| 4 | Media path traversal | **MEDIUM** | No root jail; `copytree` follows symlink **contents** into backup |
| 5 | Credential file handling (`dogfood_mongo_bootstrap`) | **HIGH** | Write-then-`chmod` leaves `0644` window; passwords in mongosh JS f-strings; argv URI leakage |
| 6 | Restore targeting production/shared DB | **CRITICAL** (config) / **GOOD** (names) | DB-name guards block `omnia` / `omnia_df_perm*`; endpoint misconfig + drill `drop_database` can still hit shared instance |

---

## 1. Host/port allowlist bypass

### What works

`assert_dogfood_mongo_endpoint()` (post-fix `7d3ebc4`) requires `(hostname.lower(), port)` ∈ allowlist **before** dump/restore. Under default env (`OMNIA_DF_MONGO_PORT=27018`, no endpoints override):

- `mongodb://127.0.0.1:27017/` → `mongo_endpoint_not_allowed` (even with empty/no DB path)
- remote hosts on `27018` → denied
- `0.0.0.0`, `127.0.0.2`, `127.1`, decimal/hex IP forms → denied (string match, not DNS/IP normalize)

Covered by unit tests + `D175-C2-ENDPOINT-NEGATIVES.json`.

### Bypass / fail-open

```text
OMNIA_DF_MONGO_PORT=27017
→ authorized_dogfood_mongo_endpoints() = {(127.0.0.1|localhost|::1, 27017)}
→ assert_dogfood_mongo_endpoint("mongodb://127.0.0.1:27017/") ALLOWS
```

Same with `OMNIA_DOGFOOD_MONGO_ENDPOINTS=127.0.0.1:27017`. There is **no** hard deny of the shared Cloud port. Docs saying “27017 fuori allowlist di default” are true only while the port knob stays `27018`.

**Worse companion:** `scripts/dogfood_mongo_bootstrap.py` accepts any `--port` / env port, can `stop_port` (SIGTERM/SIGKILL) the listener, then start dogfood mongod + create `omnia_df_admin` **root** on that port.

### Required fix

1. Hard-deny port `27017` (and non-loopback hosts) in allowlist, bootstrap, and drill — not overridable by `OMNIA_DF_MONGO_PORT` alone.
2. Optional dangerous override only via an explicit second flag (e.g. `OMNIA_DOGFOOD_ALLOW_SHARED_MONGO_PORT=1`) that is never set in certified drills.

---

## 2. URI parsing edge cases

| Case | Python allowlist | Tool behavior | Risk |
|---|---|---|---|
| No port in URI | Defaults to **27017** → denied under default allowlist | n/a | OK on default; dangerous if allowlist widened to 27017 |
| `mongodb+srv://…` | Host not allowlisted; port defaults 27017 → deny | n/a | OK |
| Double `@` (`user:pass@evil@127.0.0.1`) | urlparse → host `127.0.0.1` → **ALLOW** | mongodump: `unescaped @ sign in user info`; mongosh: `MongoParseError` | No successful redirect; defense is tool failure, not allowlist reject |
| Permanent URI equality | Exact `uri.strip() == OMNIA_DOGFOOD_PERMANENT_URI` only | n/a | Bypass equality with userinfo/slash; path `deny_check` still catches `omnia_df_perm*` / shared names in path |
| Auth-only path `/admin` on allowed host | Path DB ignored (system DBs) | `--db=` separate | Relies entirely on endpoint allowlist + `--db` name role |
| `OMNIA_DOGFOOD_MONGO_ENDPOINTS=[::1]:27018` | Stores host `'[::1]'` | urlparse hostname is `'::1'` | Usability deny (false negative), not bypass |

**Recommendation:** Reject URIs containing more than one unescaped `@` in authority before allowlist; normalize IPv6 allowlist entries; treat permanent URI with parsed-host+db equality, not raw string.

---

## 3. mongodump / mongorestore command injection

**Cleared for shell injection.**

Commands are built as argv lists:

```python
cmd = ["mongodump", f"--uri={tool_uri}", f"--db={db_name}", f"--out=..."]
subprocess.run(cmd, ...)
```

Probes:

- `$(id)`, backticks, `;rm` inside userinfo → remain inside one `--uri=` argument (no shell).
- `--db=omnia_df_probe_c2 --nsInclude=admin.*` → single argv; mongoc treats whole string as DB name → `InvalidNamespace` (`.` illegal), **not** extra flags.
- `_uri_for_tool` clears path so `--db=` owns the DB selection (good separation).

Residual (not classic injection):

- Credentials appear on process argv (`ps` leakage) — **H2** in critical review.
- `assert_safe_db_name` does not charset-restrict; relies on Mongo rejecting illegal names. Prefer `^[a-z0-9_]+$` after prefix checks.

---

## 4. Media path traversal

`backup_media(src, dest)`:

- No requirement that `src` / `dest` lie under `DOGFOOD_ROOT`.
- `shutil.copytree` with default `symlinks=False` **copies symlink target contents** into the backup tree.

**Reproduced:** symlink `media_src/escape → secret.txt` → backup contains file with secret payload (`leaked_secret=True`).

Trust model today: drill owns `dogfood/media/c2_src` (safe). Risk rises if `backup_media` is reused on untrusted trees or operator-supplied paths.

**Recommendation:** Resolve `src` under `default_dogfood_root()/media`; refuse symlinks (`symlinks=True` copy-as-link is also wrong for integrity — prefer skip/fail on symlink); refuse `src` that is not a real directory after `resolve()`.

Missing-media false-positive issue from earlier review: **fixed** (`ok:false` unless `OMNIA_DOGFOOD_ALLOW_MISSING_MEDIA=1`).

---

## 5. Credential file handling (`dogfood_mongo_bootstrap`)

### File lifecycle

```python
cred_path.write_text(... placeholder ...)   # often 0644 (umask 022)
cred_path.write_text(json.dumps(creds)...) # secrets still 0644
cred_path.chmod(0o600)                     # only now private
```

**Reproduced** under umask `0022`: secrets exist as `0644` until chmod. Live dogfood file is currently `0600` and gitignored (`dogfood/.gitignore` → `secrets/`) — good end state, bad create path.

**Fix:** `os.open(path, O_WRONLY|O_CREAT|O_EXCL, 0o600)` or write temp + `os.chmod` + `os.replace`; never write secrets before mode is private.

### Other credential issues

| Issue | Detail |
|---|---|
| mongosh JS interpolation | `pwd:'{creds['admin']}'` and `--runtime-db` embedded in JS. `token_urlsafe` is quote-safe; hand-edited JSON with `'` → JS injection / broken bootstrap |
| Process argv | Admin URI with password passed to `mongosh` / later dump tools |
| Artifacts | Role matrix / manifests reviewed: no passwords; URI redaction strips userinfo |
| Re-read existing file | No mode re-check; no rotation |

---

## 6. Restore targeting production / shared DB

### Name-level (GOOD)

`assert_safe_db_name(..., role="target_probe")`:

- Requires prefix `omnia_df_probe`
- Denies shared set (`omnia`, `omnia_prod`, `prod`, `admin`, …) and `omnia_df_perm*` / `omnia_df_permanent*`

Source role requires `omnia_df_*` and forbids probe-as-source. Drill negative cases confirm deny for `omnia` / `omnia_df_perm_x`.

### Endpoint-level (CRITICAL under misconfig)

If allowlist accepts `:27017` (criterion 1), restore remaps dump into `omnia_df_probe_*` **on the shared mongod** — does not overwrite DB `omnia` by name, but:

- Creates/writes probe DBs on the shared instance
- Drill `MongoClient.drop_database` / seed run **without** `assert_dogfood_mongo_endpoint` before client ops
- Bootstrap may have already disrupted the shared listener

So “cannot restore into DB named `omnia`” ≠ “cannot touch production Mongo process.”

### Drill gap

`scripts/dogfood_c2_drill.py` builds URI from port + admin creds and drops/seeds **before** dump helpers. Endpoint assert is only inside `run_mongodump` / `run_mongorestore`.

---

## What the post-review fix got right

1. Host+port check even when URI has no DB path.
2. Missing media → blocking failure with documented opt-out.
3. Probe-only restore targets; dogfood-prefix sources.
4. `_uri_for_tool` clears path DB.
5. Bootstrap mongod `--bind_ip 127.0.0.1`.
6. Unit coverage for endpoint deny + media missing (under default 27018).

---

## Merge gate (minimum)

1. Hard-deny port `27017` + non-loopback in allowlist, bootstrap `--port`, and drill preflight.
2. Bootstrap: never `stop_port` / start on forbidden ports; refuse before kill.
3. Drill: `assert_dogfood_mongo_endpoint(uri)` before any `MongoClient` / `drop_database`.
4. Cred file: atomic create with mode `0600`; avoid password-in-JS (use `--file` / env / stdin).
5. Tests: `OMNIA_DF_MONGO_PORT=27017` must still raise; bootstrap `--port 27017` exits non-zero without touching the listener.
6. (Should) Media: jail under dogfood root + fail on symlinks; prefer dump/restore with least-priv users not root admin.

Until then: C2 is **safe on intentional default loopback:27018**, **unsafe under port/endpoint misconfiguration**.

---

## Evidence log (this assessment)

| Probe | Result |
|---|---|
| Allow default `127.0.0.1:27018` | ALLOW |
| Deny `127.0.0.1:27017` (default env) | DENY |
| Deny remote `:27018` | DENY |
| `OMNIA_DF_MONGO_PORT=27017` then assert `:27017` | **ALLOW** (fail-open) |
| Double-`@` URI | Python ALLOW; mongodump/mongosh parse fail |
| `--db=… --nsInclude=…` as one argv | No flag split; Mongo `InvalidNamespace` |
| Symlink in media src | Content copied into backup |
| Cred write-before-chmod | `0644` → then `0600` |
| Live `dogfood/secrets/…` | mode `0600`, gitignored, keys only inspected |
