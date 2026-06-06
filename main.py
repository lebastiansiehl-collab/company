import streamlit as st
import sqlite3
import pandas as pd
from github import Github
import os
from datetime import date

# Konfiguration
g = Github(st.secrets["GIT_TOKEN"])
repo = g.get_repo("lebastiansiehl-collab/company")
DB_PATH = "data/arbeitsmedizin.db"

def init_db():
    if not os.path.exists("data"): os.makedirs("data")
    conn = sqlite3.connect(DB_PATH)
    conn.execute("CREATE TABLE IF NOT EXISTS betriebe (betrieb_id TEXT PRIMARY KEY, soll_stunden REAL)")
    conn.execute("CREATE TABLE IF NOT EXISTS einsaetze (id INTEGER PRIMARY KEY AUTOINCREMENT, betrieb_id TEXT, ist_stunden REAL, datum TEXT)")
    conn.commit()
    conn.close()

def save_db():
    with open(DB_PATH, "rb") as f:
        content = f.read()
    contents = repo.get_contents(DB_PATH)
    repo.update_file(contents.path, "Update DB", content, contents.sha)

init_db()

st.title("Arbeitsmedizin Portal Pro")

tab1, tab2, tab3 = st.tabs(["Betriebe verwalten", "Stunden erfassen", "Übersicht"])

# Tab 1: Stammdaten
with tab1:
    st.subheader("Betrieb anlegen / bearbeiten")
    b_id = st.text_input("Betriebsname/ID")
    soll = st.number_input("Soll-Stunden (jährlich)", min_value=0.0, step=0.5, format="%.1f")
    if st.button("Speichern/Aktualisieren"):
        conn = sqlite3.connect(DB_PATH)
        conn.execute("INSERT OR REPLACE INTO betriebe (betrieb_id, soll_stunden) VALUES (?, ?)", (b_id, soll))
        conn.commit()
        conn.close()
        save_db()
        st.success(f"Betrieb {b_id} gespeichert.")

# Tab 2: Stunden erfassen
with tab2:
    st.subheader("Ist-Stunden buchen")
    conn = sqlite3.connect(DB_PATH)
    betriebe = pd.read_sql_query("SELECT betrieb_id FROM betriebe", conn)
    conn.close()
    
    if not betriebe.empty:
        sel_betrieb = st.selectbox("Betrieb auswählen", betriebe['betrieb_id'])
        ist = st.number_input("Geleistete Stunden", min_value=0.0, step=0.5, format="%.1f")
        if st.button("Stunden buchen"):
            conn = sqlite3.connect(DB_PATH)
            conn.execute("INSERT INTO einsaetze (betrieb_id, ist_stunden, datum) VALUES (?, ?, ?)", (sel_betrieb, ist, str(date.today())))
            conn.commit()
            conn.close()
            save_db()
            st.success("Erfasst.")
    else:
        st.warning("Lege zuerst einen Betrieb in Tab 1 an.")

# Tab 3: Übersicht & Bearbeitung
with tab3:
    st.subheader("Betriebs-Übersicht")
    conn = sqlite3.connect(DB_PATH)
    df_betriebe = pd.read_sql_query("SELECT * FROM betriebe", conn)
    df_einsaetze = pd.read_sql_query("SELECT betrieb_id, ist_stunden FROM einsaetze", conn)
    conn.close()

    if not df_betriebe.empty:
        # 1. Sicherstellen, dass die IDs Text sind, damit der Merge klappt
        df_betriebe['betrieb_id'] = df_betriebe['betrieb_id'].astype(str)
        
        # 2. Logik, wenn Einsätze vorhanden sind
        if not df_einsaetze.empty:
            df_einsaetze['betrieb_id'] = df_einsaetze['betrieb_id'].astype(str)
            ist_sum = df_einsaetze.groupby('betrieb_id')['ist_stunden'].sum().reset_index()
            df_final = df_betriebe.merge(ist_sum, on='betrieb_id', how='left').fillna(0)
        else:
            # 2b. Logik, wenn noch keine Einsätze gebucht wurden
            df_final = df_betriebe.copy()
            df_final['ist_stunden'] = 0.0

        # Auslastung berechnen
        df_final['Auslastung'] = (df_final['ist_stunden'] / df_final['soll_stunden'].replace(0, 1)) * 100

       # Ändere diese Zeile in deiner main.py (innerhalb von Tab 3):
        edited_df = st.data_editor(
        df_final, 
        column_config={"soll_stunden": st.column_config.NumberColumn(format="%.1f")},
        key="betriebe_editor"  # <--- Das ist die wichtige Ergänzung
        )
        # Speichern der Änderungen
        if st.button("Soll-Stunden aktualisieren"):
            conn = sqlite3.connect(DB_PATH)
            for _, row in edited_df.iterrows():
                conn.execute("UPDATE betriebe SET soll_stunden = ? WHERE betrieb_id = ?", (row['soll_stunden'], row['betrieb_id']))
            conn.commit()
            conn.close()
            save_db()
            st.rerun()

        # Farblogik
        def color_status(val):
            if val <= 50: return 'background-color: #ffcccc'
            if val <= 75: return 'background-color: #ffffcc'
            return 'background-color: #ccffcc'
        
        # Anzeige
        st.dataframe(df_final.style.map(color_status, subset=['Auslastung']))
    else:
        st.info("Bitte lege in Tab 1 erst Betriebe an.")

    if not df_betriebe.empty:
        # Aggregation
        if not df_einsaetze.empty:
            ist_sum = df_einsaetze.groupby('betrieb_id')['ist_stunden'].sum().reset_index()
            df_final = df_betriebe.merge(ist_sum, on='betrieb_id', how='left').fillna(0)
        else:
            df_final = df_betriebe
            df_final['ist_stunden'] = 0.0

        df_final['Auslastung'] = (df_final['ist_stunden'] / df_final['soll_stunden'].replace(0, 1)) * 100

        # Editierbare Tabelle für Stammdaten
        edited_df = st.data_editor(df_final, column_config={"soll_stunden": st.column_config.NumberColumn(format="%.1f")})
        
        # Speichern der Änderungen aus der Tabelle
        if st.button("Soll-Stunden in Tabelle aktualisieren"):
            conn = sqlite3.connect(DB_PATH)
            for _, row in edited_df.iterrows():
                conn.execute("UPDATE betriebe SET soll_stunden = ? WHERE betrieb_id = ?", (row['soll_stunden'], row['betrieb_id']))
            conn.commit()
            conn.close()
            save_db()
            st.rerun()

        # Farblogik
        def color_status(val):
            if val <= 50: return 'background-color: #ffcccc'
            if val <= 75: return 'background-color: #ffffcc'
            return 'background-color: #ccffcc'
        
        st.dataframe(df_final.style.map(color_status, subset=['Auslastung']))