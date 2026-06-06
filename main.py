import streamlit as st
import sqlite3
import pandas as pd
from github import Github
import os
from datetime import date
import sqlite3
import pandas as pd

conn = sqlite3.connect("data/arbeitsmedizin.db")
# Wir löschen die alte Tabelle und erstellen sie neu mit den richtigen Spalten
conn.execute("DROP TABLE IF EXISTS einsaetze")
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
print("Datenbankstruktur wurde aktualisiert.")

# Konfiguration
g = Github(st.secrets["GIT_TOKEN"])
repo = g.get_repo("lebastiansiehl-collab/company")
DB_PATH = "data/arbeitsmedizin.db"

def load_db():
    if not os.path.exists("data"): os.makedirs("data")
    contents = repo.get_contents(DB_PATH)
    with open(DB_PATH, "wb") as f:
        f.write(contents.decoded_content)

def save_db():
    with open(DB_PATH, "rb") as f:
        content = f.read()
    contents = repo.get_contents(DB_PATH)
    repo.update_file(contents.path, "Update DB via App", content, contents.sha)

def load_db():
    if not os.path.exists("data"): os.makedirs("data")
    try:
        # Versuche, die Datei von GitHub zu holen
        contents = repo.get_contents(DB_PATH)
        with open(DB_PATH, "wb") as f:
            f.write(contents.decoded_content)
    except:
        # Falls Datei nicht gefunden wurde: Neue leere DB erstellen
        st.warning("Keine Datenbank gefunden, erstelle neue Struktur...")
        conn = sqlite3.connect(DB_PATH)
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
        save_db() # Einmalig hochladen
        st.success("Datenbank-Struktur wurde neu erstellt.")

st.title("Arbeitsmedizin Portal Pro")

# Formular
with st.form("einsatz_form"):
    col1, col2 = st.columns(2)
    betrieb_id = col1.number_input("Betriebs-ID", min_value=1)
    soll_stunden = col1.number_input("Soll-Stunden (jährlich)", min_value=0)
    ist_stunden = col2.number_input("Ist-Stunden (jetzt)", min_value=0)
    submit = st.form_submit_button("Speichern")
    
    if submit:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("INSERT INTO einsaetze (betrieb_id, soll_stunden, ist_stunden, datum) VALUES (?, ?, ?, ?)", 
                  (betrieb_id, soll_stunden, ist_stunden, str(date.today())))
        conn.commit()
        conn.close()
        save_db()
        st.success("Gespeichert!")

# Aggregierte Übersicht mit Farblogik
st.subheader("Betriebs-Übersicht")
conn = sqlite3.connect(DB_PATH)
df = pd.read_sql_query("SELECT * FROM einsaetze", conn)
conn.close()

if not df.empty:
    summary = df.groupby('betrieb_id').agg({'soll_stunden': 'max', 'ist_stunden': 'sum'})
    summary['Differenz'] = summary['soll_stunden'] - summary['ist_stunden']
    summary['Auslastung'] = (summary['ist_stunden'] / summary['soll_stunden'].replace(0, 1)) * 100

    def color_status(row):
        # Farblogik: Rot <= 50%, Gelb <= 75% (was 25% unterschritten entspricht)
        if row['Auslastung'] <= 50:
            return ['background-color: #ffcccc'] * len(row)
        elif row['Auslastung'] <= 75:
            return ['background-color: #ffffcc'] * len(row)
        return ['background-color: #ccffcc'] * len(row)

    styled_summary = summary.style.apply(color_status, axis=1)
    st.dataframe(styled_summary)

# Löschen
del_id = st.number_input("ID zum Löschen", min_value=1)
if st.button("Einsatz entfernen"):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("DELETE FROM einsaetze WHERE id = ?", (del_id,))
    conn.commit()
    conn.close()
    save_db()
    st.rerun()
