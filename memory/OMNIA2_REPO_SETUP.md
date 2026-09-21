# Repo ufficiale Cursor/GitHub: `omnia2`

**Stato**: ✅ **SOURCE OF TRUTH** · allineato 21-Set-2026 (D-086 + ripristino flusso)

## URL
https://github.com/mcnicastro-netizen/omnia2

## Cosa contiene
- Monorepo completo (`main`)
- Superinsieme del vecchio Emergent `mcnicastro-netizen/OMNIA` (inventario: 0 file mancanti)
- Scout, gate preprod, security go-live, docs, HAL, Cloud Agent

## Cosa NON toccare
- Emergent / GitHub **`OMNIA`** resta backup intatto (ultimo push 16-ago-2026)
- Non cancellare `OMNIA` finché non sei sicuro al 100%
- **Origin-tmp / New Project Cursor non è mai source of truth**

---

## Come lavorare (come sabato — D-087)

1. **Apri il Cloud Agent sempre sul repo GitHub `omnia2`**
   - Composer / New Agent → repository **`mcnicastro-netizen/omnia2`** (GitHub).
   - Non avviare l’agent su un clone Origin-tmp, né su un “New Project” che crea un repo Origin usa-e-getta.
2. **`origin` = GitHub**
   - `git remote -v` deve mostrare `github.com/mcnicastro-netizen/omnia2`.
   - `git push origin main` usa l’**auth Cursor/GitHub nativa** (niente username, niente PAT in chat).
   - **Non dipende da `GITHUB_TOKEN`** se l’agent è su omnia2.
3. **Fallback `GITHUB_TOKEN`** (solo se per errore l’agent gira su Origin-tmp)
   - Secret Environment `GITHUB_TOKEN` + `bash scripts/github-omnia2-push.sh`
   - Lo script **non** riscrive `origin`. Non rende Origin il master.
4. Branch: **`main`** se il Founder lo chiede; altrimenti `cursor/…` e PR solo se richiesto. **Niente PR** se il Founder dice no.

## Environment Cloud (D-086)

- `.cursor/environment.json` → `name: omnia2-cloud`
- Install/start: `scripts/cloud-agent-install.sh` / `scripts/cloud-agent-start.sh`
- HAL: `OMNIA_MEMORY_ROOT` o `/workspace/memory`
- Regola: `.cursor/rules/omnia-cloud.mdc`

## Verifica post-push (agente)

```bash
git remote -v          # github.com/mcnicastro-netizen/omnia2
git log -5 --oneline origin/main
GIT_TERMINAL_PROMPT=0 git push origin main   # Everything up-to-date, no username
```
