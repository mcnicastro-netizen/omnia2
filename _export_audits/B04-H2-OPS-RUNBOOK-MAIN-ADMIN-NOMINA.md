# B04-H2 — Runbook Ops: nomina Main Admin

**Data:** 17 novembre 2026 · Europe/Rome  
**ID piano:** MC-043  
**Stato:** documento operativo (nessun codice nuovo)  
**Attore:** Super Admin Ops (`super_admin`)

---

## 1. Perché esiste

Dopo PR #216, il wallet centrale è **deny-by-default** se `commercial_customers.main_admin_user_id` è `null`.  
Nessuna auto-nomina. Nessuna euristica da `owner_id` / `agency_admin`.

## 2. Precondizioni

1. CC esiste e ha `id` noto.
2. Candidato User:
   - esiste in `users`;
   - `is_active is True`;
   - `email_verified is True`.
3. Attore: `super_admin` autenticato in Cabina Ops.

## 3. Nomina iniziale (campo vuoto)

```http
POST /ops/commercial-customers/main-admin
```

Body:

```json
{
  "commercial_customer_id": "<cc_id>",
  "user_id": "<user_id>",
  "reason": "ops_nominate_post_deploy"
}
```

Verifica successo:
- response `ok: true` e `main_admin_user_id` = candidato;
- evento `nominate` in `commercial_main_admin_events`;
- `GET /billing/commercial/main-admin` (come Main Admin) mostra binding.

## 4. Sostituzione Ops (già presente un Main Admin)

Richiede `force: true` + `reason` ≥ 8 caratteri (audit `ops_replace`).

```json
{
  "commercial_customer_id": "<cc_id>",
  "user_id": "<nuovo_user_id>",
  "reason": "emergency lockout replace",
  "force": true
}
```

Preferire il transfer a 2 fasi (propose/accept) quando il titolare è idoneo e disponibile.

## 5. Revoca

```http
POST /ops/commercial-customers/main-admin/revoke
```

Effetto: `main_admin_user_id = null` → wallet admin deny finché nuova nomina.

## 6. Checklist post-nomina (criterio di verifica MC-043)

| Check | OK se |
|---|---|
| Binding | campo Main Admin valorizzato sul CC |
| Evento | `nominate` o `ops_replace` presente |
| Wallet | Main Admin idoneo può `GET /billing/wallet` sul CC |
| Non-MA | altro `agency_admin` senza binding → 403 |
| Transfer pending | eventuali pending cancellati su force/nominate |

## 7. Fuori scope

- UI FE accept transfer (MC-040 → fase successiva)
- Cron expiry (MC-041 lazy accettabile)
- Whitelist read CC non operativo (MC-042 — decisione Founder)
