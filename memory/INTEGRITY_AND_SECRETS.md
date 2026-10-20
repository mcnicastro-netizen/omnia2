# Integrità codice + Secrets — regola Founder (SoT)

**Aggiornato**: 5 Ott 2026  
**Obiettivo**: il Founder non deve mai dipendere da Cursor (né da un agent) come *unica* copia di codice o di API key.

---

## 1. Codice — Source of Truth

| Cosa | Dove | Chi può “far sparire” |
|------|------|------------------------|
| Codice OMNIA | **`github.com/mcnicastro-netizen/omnia2` branch `main`** | Solo chi ha write su quel repo (tu + chi autorizzi). Un Cloud Agent **non cancella** github/main aprendo un New Project. |
| Pod / Origin-tmp | Usa e butta | Usa — non è SoT. Se un agent “sembra vuoto”, è il *clone locale*, non github. |

**Verifica in 10 secondi** (da qualsiasi macchina con accesso):

```bash
git ls-remote https://github.com/mcnicastro-netizen/omnia2.git refs/heads/main
```

Confronta lo SHA con l’ultimo commit che conosci. Se coincide → codice integro sul SoT.

**Protezioni GitHub consigliate** (Settings → Branches → Protect `main`):

- Require PR before merge (o almeno: no force-push, no delete branch)
- Restrict who can push
- Optional: signed commits

Cursor **non** può bypassare la branch protection di GitHub.

---

## 2. API key — Source of Truth (non Cursor)

| Cosa | SoT reale | Copia operativa | Mai |
|------|-----------|-----------------|-----|
| `RESEND_API_KEY`, `GEMINI_API_KEY`, `FAL_KEY`, Stripe, … | **Console provider** + **password manager** (1Password/Bitwarden entry «OMNIA») | Vault Secrets dell’environment Cloud *omnia2* (solo iniezione nel VM) | Git, chat, screenshot, `backend/.env` committato |

**Fatto tecnico importante**  
I Secrets Cursor sono **per environment**. Un New Project / repo `tmp-…` apre un **vault nuovo e vuoto**.  
Non è una cancellazione delle chiavi su Resend/Google/fal — è un *collegamento perso* a quel vault.  
Se Cursor è l’unica copia che hai, **sì: è pericoloso**. Quindi Cursor **non deve mai essere l’unica copia**.

### Regola dura (D-Secrets)

1. Ogni API key esiste **prima** nel password manager + nella console del provider.  
2. Cursor Environment Secrets = **copia** per far bootare gli agent.  
3. Se un agent mostra solo `GITHUB_TOKEN` → non è “sparito tutto”: sei sull’environment sbagliato o nuovo.  
4. Nessun agent, nessuno script, nessun commit deve contenere valori secret.

Inventario **solo nomi** + dove recuperarli: `memory/CLOUD_SECRETS_INVENTORY.md`.

---

## 3. Cosa Cursor può e non può fare

| | |
|--|--|
| **Può** | Creare un environment tmp senza i tuoi secret; avere un `.env` locale nel pod; pushare su remote se ha token |
| **Non può** (da solo) | Cancellare le API key dalle console Resend/Gemini/fal; cancellare `github/main` se branch protected; leggere il password manager |
| **Rischio reale** | Tu (o un flusso Desktop) parti su env sbagliato → *sembra* che le key siano perse → stress e lavoro ripetuto |

---

## 4. Checklist Founder (una volta, poi basta)

1. [ ] Password manager: entry **OMNIA Cloud Secrets** con tutte le key (valori).  
2. [ ] GitHub: branch protection su `main` (no force-push).  
3. [ ] Cursor: Secrets salvati **solo** sull’environment agganciato a **omnia2** (non ai `tmp-…`).  
4. [ ] Avvia Cloud Agent **sempre** sul repo GitHub omnia2 — mai New Project per continuare OMNIA.  
5. [ ] Se un agent riparte “vuoto”: ignora il vault tmp; recupera da password manager / console; non ricreare key a caso finché non hai controllato la console (rotazione solo se sospetti leak).

---

## 5. Stato verificato (pod **omnia2**, 5-Ott-2026)

- Repo SoT: `github.com/mcnicastro-netizen/omnia2` (non Origin-tmp / New Project).  
- Locale `HEAD` allineato a `origin/main` al momento della verifica.  
- `backend/.env` è **gitignored** (non nel repo); i placeholder `# GEMINI_API_KEY=` restano commentati — corretto.  
- Valori API **non** sono nel codice SoT (corretto).  
- Vault Secrets di **questo** environment omnia2 (presence only, `scripts/check-secrets-presence.sh`):  
  **PRESENT** `RESEND_API_KEY`, `GEMINI_API_KEY`, `FAL_KEY`.  
- Alias Gemini (`GOOGLE_API_KEY`, `EMERGENT_LLM_KEY`) non necessari se `GEMINI_API_KEY` è già iniettata.  
- Se un agent futuro mostra solo `GITHUB_TOKEN` → sei sull’environment sbagliato o nuovo, **non** le chiavi sono state cancellate dalle console.
