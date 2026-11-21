# Railway staging topology — W4 remediation (A2)

**Data (Europe/Rome):** 2026-11-21 22:00 CET  
**Progetto:** `omnia-api-staging` (`<RAILWAY_STAGING_PROJECT_ID>`)  
**Environment Railway nome:** `production` (naming storico; **non** è produzione commerciale)

## Servizi

| Servizio | Ruolo | Volume | Domain | Note |
|----------|-------|--------|--------|------|
| `omnia-api` | API primaria staging | `omnia-api-volume` → mount tipico media (vars `RAILWAY_VOLUME_*`) | `https://<STAGING_API_A_HOST>` | Deploy codice `3f34c5f` (deploy id `804e63dd…`) |
| `omnia-api-w4b` | Seconda istanza API **senza volume** | nessuno | `https://<STAGING_API_B_HOST>` | Deploy `Dockerfile.railway` (pin GraphQL); `LOCAL_STORAGE_ROOT=/tmp` |
| `MongoDB-Fk03` | Mongo condiviso | `mongodb-volume` | TCP proxy `sakura.proxy.rlwy.net:46223` | DB app: `omnia_staging_e2e` |

## Perché `numReplicas>1` sul servizio primario fallisce

Railway rifiuta lo scale orizzontale quando è collegato un volume persistente al servizio. Il volume primario espone `RAILWAY_VOLUME_MOUNT_PATH` (media locale sotto `.media`). Non è stato scollegato/migrato in questo ciclo.

## Strategia adottata (prova W4-02/06)

1. Secondo servizio `omnia-api-w4b` senza volume.
2. Stesso `MONGO_URL` / `DB_NAME` / `JWT_SECRET` del primario.
3. Storage locale effimero (`LOCAL_STORAGE_ROOT=/tmp`) — media non condivisi; accettabile per prova sessioni.
4. Pin `dockerfilePath=Dockerfile.railway` via GraphQL (`serviceInstanceUpdate`) — senza pin, `railway up` usava il `Dockerfile` Cloud Agent e il container usciva subito (`Status: STOPPED`).

## Prova distribuita eseguita

Artefatto: `/opt/cursor/artifacts/w4r/cross_instance_revoke.json`

- Istanza A `8147372f9cd8:2` · Istanza B `2f494410745c:2` (distinte)
- Login A → `/api/auth/me` 200 su A e B con stesso access JWT
- Logout A → riuso immediato JWT → **401 su A e 401 su B**

## Raccomandazione architetturale (non applicata)

Per multi-replica “nativa” sul solo servizio primario:

1. Inventario file sotto volume (media/backup).
2. Migrare media a object storage condiviso (R2/S3) già previsto dal codice `STORAGE_BACKEND`.
3. Scollegare volume solo dopo restore verificato.
4. Solo allora `numReplicas≥2` sul primario dietro lo stesso dominio.

**Blocco residuo per topologia “singolo servizio multi-replica”:** migrazione storage + decisione Founder. La prova W4-02/06 è comunque soddisfatta con due servizi indipendenti e Mongo/sessioni condivise.
