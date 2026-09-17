# Repo ufficiale Cursor/GitHub: `omnia2`

**Stato**: ✅ **POPOLATO** · push completato 2026-09-17

## URL
https://github.com/mcnicastro-netizen/omnia2

## Cosa contiene
- Mirror completo di questo workspace Cursor (`main`, 100+ commit)
- Superinsieme del vecchio Emergent `mcnicastro-netizen/OMNIA` (inventario: 0 file mancanti)
- Scout, gate preprod, security go-live, docs, ecc.

## Cosa NON toccare
- Emergent / GitHub **`OMNIA`** resta backup intatto (ultimo push 16-ago-2026)
- Non cancellare `OMNIA` finché non sei sicuro al 100%

## Come lavorare da ora
1. Apri Cloud Agent / progetto su **`omnia2`** (non sul vecchio `tmp-…`)
2. Branch di lavoro: `main` (o `cursor/…-15e8` se serve isolamento)
3. Secret `GITHUB_TOKEN` già in Environment (per agent futuri)

## Verifica post-push (agente)
- Tree GitHub: **628** path
- Spot-check 200: `backend/server.py`, `frontend/package.json`, `preprod_confidence_gate.py`, `omnia-stack.sh`, inventario
- Emergent `OMNIA` `pushed_at` invariato
