"""OMNIA — M5.S5 Comparatore Mutui: dati curati (benchmark + offerte banche + soglie usura).

Dati ORIENTATIVI aggiornati manualmente — ultimo aggiornamento: Giugno 2026.
Fonti: Eurirs/Euribor quotazioni pubbliche, TEGM Banca d'Italia (rilevazione trimestrale),
fogli informativi banche. Nessuno scraping (D-037): tabella curata, più affidabile.
"""

DATA_UPDATED_AT = "2026-06"

# Benchmark annuali (%) — Eurirs per tasso fisso (per durata), Euribor 3M per variabile
EURIRS = {10: 2.94, 15: 3.05, 20: 3.17, 25: 3.15, 30: 3.12}
EURIBOR_3M = 2.05

# TEGM Banca d'Italia (rilevazione Q2 2026) e soglie usura (TEGM*1.25 + 4)
TEGM = {
    "fisso": {"tegm": 4.05, "soglia": 9.0625},
    "variabile": {"tegm": 4.08, "soglia": 9.10},
}

DURATIONS = [10, 15, 20, 25, 30]
MAX_LTV_STANDARD = 80.0
MAX_LTV_UNDER36 = 95.0  # Fondo garanzia Consap prima casa under-36
MAX_RATA_REDDITO = 0.35  # sostenibilità: rata ≤ 35% del reddito mensile netto

# Offerte banche curate. spread in punti %, spese in €.
# istruttoria_pct applicata sull'importo (con minimo), altrimenti istruttoria_flat.
BANK_OFFERS = [
    {"bank": "Intesa Sanpaolo", "product": "Mutuo Domus Fisso", "type": "fisso",
     "spread": 0.65, "istruttoria_pct": 0.5, "istruttoria_min": 400, "perizia": 320,
     "incasso_rata": 3.75, "max_ltv": 80, "consap": True},
    {"bank": "Intesa Sanpaolo", "product": "Mutuo Domus Variabile", "type": "variabile",
     "spread": 1.10, "istruttoria_pct": 0.5, "istruttoria_min": 400, "perizia": 320,
     "incasso_rata": 3.75, "max_ltv": 80, "consap": True},
    {"bank": "UniCredit", "product": "Mutuo UniCredit Fisso", "type": "fisso",
     "spread": 0.55, "istruttoria_pct": 0.5, "istruttoria_min": 500, "perizia": 300,
     "incasso_rata": 3.50, "max_ltv": 80, "consap": True},
    {"bank": "UniCredit", "product": "Mutuo UniCredit Variabile", "type": "variabile",
     "spread": 1.00, "istruttoria_pct": 0.5, "istruttoria_min": 500, "perizia": 300,
     "incasso_rata": 3.50, "max_ltv": 80, "consap": True},
    {"bank": "BPER Banca", "product": "Mutuo BPER Fisso", "type": "fisso",
     "spread": 0.75, "istruttoria_flat": 750, "perizia": 250,
     "incasso_rata": 2.75, "max_ltv": 80, "consap": True},
    {"bank": "BPER Banca", "product": "Mutuo BPER Variabile", "type": "variabile",
     "spread": 1.25, "istruttoria_flat": 750, "perizia": 250,
     "incasso_rata": 2.75, "max_ltv": 80, "consap": True},
    {"bank": "Crédit Agricole", "product": "Mutuo CA Fisso", "type": "fisso",
     "spread": 0.50, "istruttoria_flat": 600, "perizia": 290,
     "incasso_rata": 2.00, "max_ltv": 80, "consap": True},
    {"bank": "Crédit Agricole", "product": "Mutuo CA Variabile", "type": "variabile",
     "spread": 0.95, "istruttoria_flat": 600, "perizia": 290,
     "incasso_rata": 2.00, "max_ltv": 80, "consap": True},
    {"bank": "BNL BNP Paribas", "product": "Mutuo BNL Fisso", "type": "fisso",
     "spread": 0.80, "istruttoria_pct": 0.6, "istruttoria_min": 500, "perizia": 310,
     "incasso_rata": 3.00, "max_ltv": 80, "consap": False},
    {"bank": "Banca MPS", "product": "Mutuo MPS Fisso", "type": "fisso",
     "spread": 0.70, "istruttoria_flat": 700, "perizia": 280,
     "incasso_rata": 2.50, "max_ltv": 80, "consap": True},
    {"bank": "ING", "product": "Mutuo Arancio Fisso", "type": "fisso",
     "spread": 0.45, "istruttoria_flat": 0, "perizia": 295,
     "incasso_rata": 0.0, "max_ltv": 80, "consap": False},
    {"bank": "ING", "product": "Mutuo Arancio Variabile", "type": "variabile",
     "spread": 0.85, "istruttoria_flat": 0, "perizia": 295,
     "incasso_rata": 0.0, "max_ltv": 80, "consap": False},
    {"bank": "Webank (BPM)", "product": "Mutuo Webank Fisso", "type": "fisso",
     "spread": 0.40, "istruttoria_flat": 0, "perizia": 300,
     "incasso_rata": 0.0, "max_ltv": 80, "consap": False},
    {"bank": "Webank (BPM)", "product": "Mutuo Webank Variabile", "type": "variabile",
     "spread": 0.80, "istruttoria_flat": 0, "perizia": 300,
     "incasso_rata": 0.0, "max_ltv": 80, "consap": False},
]
