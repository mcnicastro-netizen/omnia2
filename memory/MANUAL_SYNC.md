# Manuale sync — regola operativa (D-084)

**Obbligo Founder (16-Sep-2026)**: a **ogni** modifica di prodotto che cambia UX/API/comportamento documentato, il **manuale + YAML HAL** si aggiornano **nello stesso giro di lavoro** (stesso commit o commit docs immediatamente successivo), senza «lo facciamo dopo».

Questo non è un bot CI: è **obbligo dell’agente / sviluppatore** — “automatico” = non esiste più la fase “codice sì, manuale dopo”.

---

## Checklist (obbligatoria prima di dichiarare ship)

1. **Individua il capitolo** (`memory/manuale/NN-….md`) toccato dalla feature.
2. **Aggiorna il MD** (cosa esiste / cosa non esiste · D-051): path UI, API, limiti, errori comuni.
3. **Aggiorna le voci YAML** in `memory/manuale/hal/NN-….yaml` (stesse verità; `domanda_naturale` se cambiano le FAQ).
4. **ASPETTI / backlog**: marca ID ✅ o aggiorna testo se A-xxx era “proposta” e ora è shippata.
5. **CHANGELOG.md** + riga in `NEXT_SESSION.md` se cambia il “dove siamo”.
6. **Reindex HAL** se hai toccato YAML:  
   `POST /api/app/hal-knowledge/reindex` (super_admin) **oppure** restart backend che fa ingest all’avvio — verifica smoke 1–2 query.
7. **Commit** codice + docs insieme quando possibile.

---

## Cosa NON aggiornare “a caso”

- Screenshot kit: solo se UI visibile è cambiata e Founder chiede kit.
- Cap. Billing live: solo post Stripe live (D-051).
- Capitoli di moduli **non** toccati dal diff.

---

## Violazione

Ship senza sync manuale = **debito documentale**. Va chiuso prima del task successivo, non accantonato.
