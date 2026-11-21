# artifacts/d7 — run immutabili harness T3/T4

Ogni esecuzione autorizzata (pacchetto C) crea una sottocartella `<run_id>/` e **non** sovrascrive run precedenti.

I secret di run vivono in `<run_id>/secrets/` (gitignored, mode 0600).

Artefatti storici D7-1 (`/opt/cursor/artifacts/d7_*.json`, `/tmp/d7_*`) non sono gestiti da questa cartella e non vanno riscritti.
