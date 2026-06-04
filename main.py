import streamlit as st
import sqlite3
import pandas as pd
import os
import streamlit as st

st.write("Aktueller Arbeitsordner:", os.getcwd())
st.write("Existiert die Datenbankdatei?", os.path.exists('data/arbeitsmedizin.db'))

st.title("Arbeitsmedizin Portal")

# Verbindung zur SQLite-Datenbank herstellen
# Streamlit Cloud findet die Datei im Ordner 'data/'
DB_PATH = 'data/arbeitsmedizin.db'

def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS einsaetze 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                  betrieb_id INTEGER, 
                  datum DATE, 
                  stunden INTEGER, 
                  status TEXT)''')
    conn.commit()
    conn.close()

# Initialisiere die DB beim Start
init_db()

# Einfaches Formular zum Testen
with st.form("einsatz_form"):
    betrieb_id = st.number_input("Betriebs-ID", min_value=1)
    stunden = st.number_input("Stunden", min_value=1)
    submit = st.form_submit_button("Speichern")
    
if submit:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("INSERT INTO einsaetze (betrieb_id, stunden, status) VALUES (?, ?, ?)", 
                  (betrieb_id, stunden, 'Offen'))
        conn.commit()
        conn.close()
        st.success("Einsatz gespeichert!")

# Daten anzeigen
if st.button("Daten anzeigen"):
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql_query("SELECT * FROM einsaetze", conn)
    st.write(df)
    conn.close()
# Ganz oben in main.py
from git_sync import sync_db 

    submit = st.form_submit_button("Speichern")
    
if submit:
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("INSERT INTO einsaetze (betrieb_id, stunden, status) VALUES (?, ?, ?)", 
              (betrieb_id, stunden, 'Offen'))
    conn.commit()
    conn.close()
    
    sync_db() 
    st.success("Einsatz gespeichert und synchronisiert!")
import streamlit as st

if "GIT_TOKEN" in st.secrets:
    st.write("✅ Token gefunden, wir können speichern!")
else:
    st.error("❌ Token nicht gefunden! Bitte in Streamlit 'Secrets' eintragen.")
