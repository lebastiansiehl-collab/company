import sqlite3
import os

# Pfad sicherstellen
if not os.path.exists("data"):
    os.makedirs("data")

# Datenbank erstellen
conn = sqlite3.connect("data/arbeitsmedizin.db")
conn.execute("""
    CREATE TABLE einsaetze (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        betrieb_id INTEGER,
        soll_stunden REAL,
        ist_stunden REAL,
        datum TEXT
    )
""")
conn.commit()
conn.close()
print("Datenbank in 'data/arbeitsmedizin.db' erfolgreich erstellt.")