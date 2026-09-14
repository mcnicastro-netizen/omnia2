"""Province-level €/m² fallback for the 107 Italian provinces.

Used when a user enters a comune NOT in the CITY_PRICES curated list.
The flow:
  1. CITY_PRICES (161 cities) — explicit prices
  2. Nominatim geocoder returns province code → look up here
  3. Regional fallback (REGIONAL_DEFAULTS)

Prices represent capoluogo + provincial average. For small comuni the
algorithm applies a downward regional adjustment via coefficients.

Source: Borsino Immobiliare + Tecnocasa + OMI Q4-2024/Q1-2025 cross-ref.
"""

# Province → (centro_min, centro_max, semicentro_min, semicentro_max,
#             periferia_min, periferia_max, region)
PROVINCE_PRICES = {
    # LOMBARDIA
    "MI": {"centro": (9000, 13000), "semicentro": (5500, 7500), "periferia": (3500, 4800), "region": "lombardia"},
    "BG": {"centro": (3500, 5000),  "semicentro": (2400, 3300), "periferia": (1700, 2300), "region": "lombardia"},
    "BS": {"centro": (2900, 4000),  "semicentro": (2000, 2800), "periferia": (1400, 2000), "region": "lombardia"},
    "MB": {"centro": (3200, 4500),  "semicentro": (2400, 3200), "periferia": (1800, 2400), "region": "lombardia"},
    "CO": {"centro": (3500, 5200),  "semicentro": (2400, 3400), "periferia": (1700, 2400), "region": "lombardia"},
    "VA": {"centro": (2400, 3300),  "semicentro": (1700, 2300), "periferia": (1200, 1700), "region": "lombardia"},
    "PV": {"centro": (2200, 3000),  "semicentro": (1600, 2100), "periferia": (1100, 1500), "region": "lombardia"},
    "CR": {"centro": (1800, 2400),  "semicentro": (1200, 1700), "periferia": (900, 1300),  "region": "lombardia"},
    "MN": {"centro": (2000, 2700),  "semicentro": (1400, 1900), "periferia": (1000, 1400), "region": "lombardia"},
    "LC": {"centro": (2600, 3500),  "semicentro": (1800, 2500), "periferia": (1300, 1800), "region": "lombardia"},
    "LO": {"centro": (1900, 2600),  "semicentro": (1300, 1800), "periferia": (1000, 1400), "region": "lombardia"},
    "SO": {"centro": (2200, 3000),  "semicentro": (1500, 2100), "periferia": (1100, 1500), "region": "lombardia"},
    # PIEMONTE
    "TO": {"centro": (2800, 4200),  "semicentro": (1700, 2400), "periferia": (1100, 1700), "region": "piemonte"},
    "NO": {"centro": (1900, 2700),  "semicentro": (1300, 1800), "periferia": (900, 1300),  "region": "piemonte"},
    "AT": {"centro": (1500, 2100),  "semicentro": (1000, 1400), "periferia": (700, 1000),  "region": "piemonte"},
    "AL": {"centro": (1400, 2000),  "semicentro": (900, 1300),  "periferia": (600, 900),   "region": "piemonte"},
    "CN": {"centro": (1700, 2400),  "semicentro": (1200, 1700), "periferia": (800, 1200),  "region": "piemonte"},
    "VB": {"centro": (1800, 2500),  "semicentro": (1200, 1700), "periferia": (900, 1300),  "region": "piemonte"},
    "VC": {"centro": (1400, 2000),  "semicentro": (900, 1300),  "periferia": (600, 900),   "region": "piemonte"},
    "BI": {"centro": (1300, 1900),  "semicentro": (900, 1200),  "periferia": (600, 900),   "region": "piemonte"},
    # LIGURIA
    "GE": {"centro": (3000, 4500),  "semicentro": (2000, 2800), "periferia": (1400, 2000), "region": "liguria"},
    "SV": {"centro": (3500, 5000),  "semicentro": (2400, 3300), "periferia": (1700, 2400), "region": "liguria"},
    "IM": {"centro": (3200, 4500),  "semicentro": (2200, 3000), "periferia": (1500, 2200), "region": "liguria"},
    "SP": {"centro": (2700, 3800),  "semicentro": (1800, 2500), "periferia": (1300, 1800), "region": "liguria"},
    # VALLE D'AOSTA
    "AO": {"centro": (2400, 3300),  "semicentro": (1700, 2300), "periferia": (1200, 1700), "region": "valle_d_aosta"},
    # VENETO
    "VE": {"centro": (5500, 8500),  "semicentro": (2500, 3500), "periferia": (1500, 2200), "region": "veneto"},
    "VR": {"centro": (3000, 4200),  "semicentro": (2000, 2800), "periferia": (1300, 1900), "region": "veneto"},
    "PD": {"centro": (2700, 3800),  "semicentro": (1900, 2600), "periferia": (1300, 1800), "region": "veneto"},
    "VI": {"centro": (2400, 3400),  "semicentro": (1700, 2300), "periferia": (1200, 1700), "region": "veneto"},
    "TV": {"centro": (2200, 3100),  "semicentro": (1500, 2100), "periferia": (1100, 1500), "region": "veneto"},
    "BL": {"centro": (2000, 2800),  "semicentro": (1400, 1900), "periferia": (900, 1400),  "region": "veneto"},
    "RO": {"centro": (1400, 2000),  "semicentro": (900, 1300),  "periferia": (600, 900),   "region": "veneto"},
    # TRENTINO ALTO ADIGE
    "TN": {"centro": (3200, 4500),  "semicentro": (2300, 3200), "periferia": (1600, 2300), "region": "trentino_alto_adige"},
    "BZ": {"centro": (4500, 6500),  "semicentro": (3200, 4500), "periferia": (2200, 3200), "region": "trentino_alto_adige"},
    # FRIULI VENEZIA GIULIA
    "TS": {"centro": (2500, 3500),  "semicentro": (1700, 2400), "periferia": (1200, 1700), "region": "friuli_venezia_giulia"},
    "UD": {"centro": (1900, 2600),  "semicentro": (1300, 1800), "periferia": (900, 1300),  "region": "friuli_venezia_giulia"},
    "PN": {"centro": (1800, 2500),  "semicentro": (1300, 1800), "periferia": (900, 1300),  "region": "friuli_venezia_giulia"},
    "GO": {"centro": (1600, 2200),  "semicentro": (1100, 1500), "periferia": (800, 1100),  "region": "friuli_venezia_giulia"},
    # EMILIA-ROMAGNA
    "BO": {"centro": (3500, 5200),  "semicentro": (2400, 3300), "periferia": (1600, 2300), "region": "emilia_romagna"},
    "PR": {"centro": (2700, 3800),  "semicentro": (1900, 2600), "periferia": (1300, 1800), "region": "emilia_romagna"},
    "MO": {"centro": (2400, 3300),  "semicentro": (1700, 2300), "periferia": (1200, 1700), "region": "emilia_romagna"},
    "RE": {"centro": (2300, 3200),  "semicentro": (1600, 2200), "periferia": (1100, 1600), "region": "emilia_romagna"},
    "FE": {"centro": (1800, 2500),  "semicentro": (1300, 1800), "periferia": (900, 1300),  "region": "emilia_romagna"},
    "RA": {"centro": (2300, 3200),  "semicentro": (1600, 2200), "periferia": (1100, 1600), "region": "emilia_romagna"},
    "FC": {"centro": (2200, 3000),  "semicentro": (1500, 2100), "periferia": (1000, 1500), "region": "emilia_romagna"},
    "RN": {"centro": (3200, 4500),  "semicentro": (2200, 3000), "periferia": (1500, 2200), "region": "emilia_romagna"},
    "PC": {"centro": (2100, 2900),  "semicentro": (1500, 2000), "periferia": (1000, 1400), "region": "emilia_romagna"},
    # TOSCANA
    "FI": {"centro": (4500, 6800),  "semicentro": (2800, 3900), "periferia": (1800, 2500), "region": "toscana"},
    "SI": {"centro": (3200, 4500),  "semicentro": (2200, 3000), "periferia": (1500, 2200), "region": "toscana"},
    "PI": {"centro": (2400, 3400),  "semicentro": (1700, 2400), "periferia": (1200, 1700), "region": "toscana"},
    "LI": {"centro": (2700, 3800),  "semicentro": (1900, 2600), "periferia": (1300, 1800), "region": "toscana"},
    "LU": {"centro": (2800, 4000),  "semicentro": (2000, 2700), "periferia": (1400, 2000), "region": "toscana"},
    "AR": {"centro": (2100, 2900),  "semicentro": (1500, 2000), "periferia": (1000, 1400), "region": "toscana"},
    "PT": {"centro": (2300, 3200),  "semicentro": (1600, 2200), "periferia": (1100, 1600), "region": "toscana"},
    "PO": {"centro": (2500, 3500),  "semicentro": (1800, 2400), "periferia": (1200, 1700), "region": "toscana"},
    "GR": {"centro": (2200, 3100),  "semicentro": (1500, 2100), "periferia": (1100, 1500), "region": "toscana"},
    "MS": {"centro": (2000, 2800),  "semicentro": (1400, 1900), "periferia": (1000, 1400), "region": "toscana"},
    # UMBRIA
    "PG": {"centro": (1900, 2700),  "semicentro": (1300, 1800), "periferia": (900, 1300),  "region": "umbria"},
    "TR": {"centro": (1500, 2100),  "semicentro": (1000, 1400), "periferia": (700, 1000),  "region": "umbria"},
    # MARCHE
    "AN": {"centro": (2100, 3000),  "semicentro": (1500, 2000), "periferia": (1000, 1400), "region": "marche"},
    "PU": {"centro": (1900, 2700),  "semicentro": (1300, 1800), "periferia": (900, 1300),  "region": "marche"},
    "MC": {"centro": (1500, 2100),  "semicentro": (1000, 1400), "periferia": (700, 1000),  "region": "marche"},
    "AP": {"centro": (1600, 2200),  "semicentro": (1100, 1500), "periferia": (700, 1100),  "region": "marche"},
    "FM": {"centro": (1500, 2100),  "semicentro": (1000, 1400), "periferia": (700, 1000),  "region": "marche"},
    # LAZIO
    "RM": {"centro": (6000, 9500),  "semicentro": (3500, 5000), "periferia": (2000, 3000), "region": "lazio"},
    "VT": {"centro": (1500, 2100),  "semicentro": (1000, 1400), "periferia": (700, 1000),  "region": "lazio"},
    "FR": {"centro": (1400, 2000),  "semicentro": (900, 1300),  "periferia": (600, 900),   "region": "lazio"},
    "LT": {"centro": (1800, 2500),  "semicentro": (1300, 1800), "periferia": (900, 1300),  "region": "lazio"},
    "RI": {"centro": (1300, 1800),  "semicentro": (900, 1200),  "periferia": (600, 900),   "region": "lazio"},
    # ABRUZZO
    "AQ": {"centro": (1500, 2100),  "semicentro": (1100, 1500), "periferia": (800, 1100),  "region": "abruzzo"},
    "PE": {"centro": (2100, 2900),  "semicentro": (1500, 2000), "periferia": (1000, 1500), "region": "abruzzo"},
    "CH": {"centro": (1500, 2100),  "semicentro": (1000, 1400), "periferia": (700, 1000),  "region": "abruzzo"},
    "TE": {"centro": (1600, 2200),  "semicentro": (1100, 1500), "periferia": (800, 1100),  "region": "abruzzo"},
    # MOLISE
    "CB": {"centro": (1200, 1700),  "semicentro": (800, 1100),  "periferia": (600, 800),   "region": "molise"},
    "IS": {"centro": (1100, 1500),  "semicentro": (750, 1000),  "periferia": (550, 750),   "region": "molise"},
    # CAMPANIA
    "NA": {"centro": (3500, 5500),  "semicentro": (2200, 3200), "periferia": (1300, 2000), "region": "campania"},
    "SA": {"centro": (2400, 3400),  "semicentro": (1700, 2300), "periferia": (1100, 1600), "region": "campania"},
    "CE": {"centro": (1800, 2500),  "semicentro": (1300, 1800), "periferia": (900, 1300),  "region": "campania"},
    "BN": {"centro": (1300, 1800),  "semicentro": (900, 1200),  "periferia": (600, 900),   "region": "campania"},
    "AV": {"centro": (1400, 2000),  "semicentro": (950, 1300),  "periferia": (650, 950),   "region": "campania"},
    # PUGLIA
    "BA": {"centro": (2300, 3300),  "semicentro": (1600, 2200), "periferia": (1100, 1600), "region": "puglia"},
    "LE": {"centro": (1900, 2600),  "semicentro": (1300, 1800), "periferia": (900, 1300),  "region": "puglia"},
    "BR": {"centro": (1600, 2200),  "semicentro": (1100, 1500), "periferia": (750, 1100),  "region": "puglia"},
    "BT": {"centro": (1500, 2100),  "semicentro": (1000, 1400), "periferia": (700, 1000),  "region": "puglia"},
    "FG": {"centro": (1300, 1800),  "semicentro": (900, 1200),  "periferia": (600, 900),   "region": "puglia"},
    "TA": {"centro": (1400, 2000),  "semicentro": (950, 1300),  "periferia": (650, 950),   "region": "puglia"},
    # BASILICATA
    "PZ": {"centro": (1300, 1800),  "semicentro": (900, 1200),  "periferia": (600, 900),   "region": "basilicata"},
    "MT": {"centro": (1500, 2100),  "semicentro": (1000, 1400), "periferia": (700, 1000),  "region": "basilicata"},
    # CALABRIA
    "CZ": {"centro": (1300, 1800),  "semicentro": (900, 1200),  "periferia": (600, 900),   "region": "calabria"},
    "RC": {"centro": (1200, 1700),  "semicentro": (800, 1100),  "periferia": (550, 800),   "region": "calabria"},
    "CS": {"centro": (1300, 1800),  "semicentro": (900, 1200),  "periferia": (600, 900),   "region": "calabria"},
    "KR": {"centro": (950, 1350),   "semicentro": (650, 950),   "periferia": (450, 750),   "region": "calabria"},
    "VV": {"centro": (1100, 1500),  "semicentro": (750, 1050),  "periferia": (500, 750),   "region": "calabria"},
    # SICILIA
    "PA": {"centro": (2100, 3000),  "semicentro": (1400, 2000), "periferia": (900, 1400),  "region": "sicilia"},
    "CT": {"centro": (2000, 2800),  "semicentro": (1400, 1900), "periferia": (900, 1400),  "region": "sicilia"},
    "ME": {"centro": (1700, 2400),  "semicentro": (1200, 1600), "periferia": (800, 1200),  "region": "sicilia"},
    "SR": {"centro": (1600, 2200),  "semicentro": (1100, 1500), "periferia": (750, 1100),  "region": "sicilia"},
    "RG": {"centro": (1500, 2100),  "semicentro": (1000, 1400), "periferia": (700, 1000),  "region": "sicilia"},
    "AG": {"centro": (1400, 2000),  "semicentro": (950, 1300),  "periferia": (650, 950),   "region": "sicilia"},
    "TP": {"centro": (1400, 2000),  "semicentro": (950, 1300),  "periferia": (650, 950),   "region": "sicilia"},
    "CL": {"centro": (1100, 1500),  "semicentro": (750, 1050),  "periferia": (500, 750),   "region": "sicilia"},
    "EN": {"centro": (1000, 1400),  "semicentro": (700, 950),   "periferia": (500, 700),   "region": "sicilia"},
    # SARDEGNA
    "CA": {"centro": (2400, 3400),  "semicentro": (1700, 2300), "periferia": (1100, 1600), "region": "sardegna"},
    "SS": {"centro": (1800, 2500),  "semicentro": (1200, 1700), "periferia": (850, 1200), "region": "sardegna"},
    "NU": {"centro": (1500, 2100),  "semicentro": (1000, 1400), "periferia": (700, 1000), "region": "sardegna"},
    "OR": {"centro": (1300, 1800),  "semicentro": (900, 1200),  "periferia": (600, 900),  "region": "sardegna"},
    "SU": {"centro": (1200, 1700),  "semicentro": (850, 1150),  "periferia": (550, 850),  "region": "sardegna"},
}

# Province sigla → nome esteso (per display)
PROVINCE_NAMES = {
    "MI": "Milano", "BG": "Bergamo", "BS": "Brescia", "MB": "Monza-Brianza", "CO": "Como",
    "VA": "Varese", "PV": "Pavia", "CR": "Cremona", "MN": "Mantova", "LC": "Lecco",
    "LO": "Lodi", "SO": "Sondrio", "TO": "Torino", "NO": "Novara", "AT": "Asti",
    "AL": "Alessandria", "CN": "Cuneo", "VB": "Verbano-Cusio-Ossola", "VC": "Vercelli",
    "BI": "Biella", "GE": "Genova", "SV": "Savona", "IM": "Imperia", "SP": "La Spezia",
    "AO": "Aosta", "VE": "Venezia", "VR": "Verona", "PD": "Padova", "VI": "Vicenza",
    "TV": "Treviso", "BL": "Belluno", "RO": "Rovigo", "TN": "Trento", "BZ": "Bolzano",
    "TS": "Trieste", "UD": "Udine", "PN": "Pordenone", "GO": "Gorizia", "BO": "Bologna",
    "PR": "Parma", "MO": "Modena", "RE": "Reggio Emilia", "FE": "Ferrara", "RA": "Ravenna",
    "FC": "Forlì-Cesena", "RN": "Rimini", "PC": "Piacenza", "FI": "Firenze", "SI": "Siena",
    "PI": "Pisa", "LI": "Livorno", "LU": "Lucca", "AR": "Arezzo", "PT": "Pistoia",
    "PO": "Prato", "GR": "Grosseto", "MS": "Massa-Carrara", "PG": "Perugia", "TR": "Terni",
    "AN": "Ancona", "PU": "Pesaro-Urbino", "MC": "Macerata", "AP": "Ascoli Piceno", "FM": "Fermo",
    "RM": "Roma", "VT": "Viterbo", "FR": "Frosinone", "LT": "Latina", "RI": "Rieti",
    "AQ": "L'Aquila", "PE": "Pescara", "CH": "Chieti", "TE": "Teramo", "CB": "Campobasso",
    "IS": "Isernia", "NA": "Napoli", "SA": "Salerno", "CE": "Caserta", "BN": "Benevento",
    "AV": "Avellino", "BA": "Bari", "LE": "Lecce", "BR": "Brindisi", "BT": "Barletta-Andria-Trani",
    "FG": "Foggia", "TA": "Taranto", "PZ": "Potenza", "MT": "Matera", "CZ": "Catanzaro",
    "RC": "Reggio Calabria", "CS": "Cosenza", "KR": "Crotone", "VV": "Vibo Valentia",
    "PA": "Palermo", "CT": "Catania", "ME": "Messina", "SR": "Siracusa", "RG": "Ragusa",
    "AG": "Agrigento", "TP": "Trapani", "CL": "Caltanissetta", "EN": "Enna",
    "CA": "Cagliari", "SS": "Sassari", "NU": "Nuoro", "OR": "Oristano", "SU": "Sud Sardegna",
}
