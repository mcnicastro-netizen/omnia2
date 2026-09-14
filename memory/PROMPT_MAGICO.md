# 🔑 PROMPT MAGICO — DA COPIARE/INCOLLARE

Quando riapri una conversazione (sia tu stesso domani, sia dopo un fork, sia con un nuovo agente),
**incolla esattamente questo prompt come PRIMO messaggio**:

---

```
Riprendiamo il progetto OMNIA.

PROTOCOLLO BOOTSTRAP OBBLIGATORIO:
1. Leggi /app/memory/AGENT_BOOTSTRAP.md
2. Leggi /app/memory/PROGRAMMA_OMNIA.md
3. Leggi /app/memory/ROADMAP.md
4. Leggi /app/memory/DECISIONS.md
5. Leggi /app/memory/PRD.md

Poi rispondi con:
- Milestone e sessione attuale
- Decisioni vincolanti (D-XXX)
- Prossima sessione da fare
- Conferma che seguirai PROGRAMMA_OMNIA.md senza deviazioni

Non rispondere prima di aver letto tutti i file.
```

---

## 🎯 Quando usarlo

| Situazione | Devi usare il prompt? |
|---|---|
| Riprendi dopo qualche ora stesso giorno | ❌ No, basta `"Riprendiamo OMNIA, partiamo con M.S"` |
| Riprendi il giorno dopo | 🟡 Consigliato |
| Riprendi dopo 1 settimana+ | ✅ SÌ, sempre |
| Conversazione "forkata" da Emergent | ✅ SÌ, sempre |
| Cambio agente / nuovo agente | ✅ SÌ, sempre |
| L'agente sembra confuso | ✅ SÌ, sempre |

## 💡 Versione SHORT (per quando l'agente è già nel contesto)

```
Riprendiamo OMNIA. Leggi /app/memory/*, dimmi dove siamo, partiamo con M1.S2.
```

## 🆘 Versione EMERGENZA (se l'agente fa stupidaggini)

```
STOP. Leggi /app/memory/AGENT_BOOTSTRAP.md ORA.
Tutte le decisioni in DECISIONS.md sono vincolanti.
Non proporre cose già decise. Riprendi da dove eravamo.
```

---

## 🧪 Come testare se funziona

Prima di chiudere una sessione importante, fai questo test:

1. Salva su GitHub
2. Apri una nuova conversazione (Tab nuovo o Fork)
3. Incolla il "PROMPT MAGICO" sopra
4. Verifica che il nuovo agente:
   - ✅ Legga tutti i file
   - ✅ Sappia dirti dove siamo
   - ✅ Citi le decisioni D-XXX
   - ✅ Proponga la prossima sessione corretta
   - ❌ NON proponga di rifare decisioni già prese

Se il test passa → sei al sicuro.
Se fallisce → il bootstrap va rinforzato.
