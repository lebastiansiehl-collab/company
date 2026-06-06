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

tab1, tab2 = st.tabs(["Stammdaten (Betriebe)", "Tagesgeschäft (Buchen & Übersicht)"])

# Tab 1: Stammdaten
with tab1:
    st.subheader("Betriebe verwalten")
    b_id = st.text_input("Betriebsname/ID")
    soll = st.number_input("Soll-Stunden (jährlich)", min_value=0.0, step=0.5, format="%.1f")
    if st.button("Speichern/Aktualisieren"):
        conn = sqlite3.connect(DB_PATH)
        conn.execute("INSERT OR REPLACE INTO betriebe (betrieb_id, soll_stunden) VALUES (?, ?)", (b_id, soll))
        conn.commit()
        conn.close()
        save_db()
        st.success(f"Betrieb {b_id} gespeichert.")

# Tab 2: Tagesgeschäft
with tab2:
    # 1. Buchen
    st.subheader("Stunden erfassen")
    conn = sqlite3.connect(DB_PATH)
    betriebe = pd.read_sql_query("SELECT betrieb_id FROM betriebe", conn)
    conn.close()
    
    if not betriebe.empty:
        col1, col2 = st.columns([2, 1])
        with col1:
            sel_betrieb = st.selectbox("Betrieb auswählen", betriebe['betrieb_id'])
        with col2:
            ist = st.number_input("Stunden", min_value=0.0, step=0.5, format="%.1f")
        
        if st.button("Buchen"):
            conn = sqlite3.connect(DB_PATH)
            conn.execute("INSERT INTO einsaetze (betrieb_id, ist_stunden, datum) VALUES (?, ?, ?)", (sel_betrieb, ist, str(date.today())))
            conn.commit()
            conn.close()
            save_db()
            st.rerun()
    else:
        st.warning("Lege zuerst einen Betrieb in Tab 1 an.")

    st.divider()

    # 2. Übersicht (Aggregiert)
    st.subheader("Aktuelle Auslastung")
    conn = sqlite3.connect(DB_PATH)
    df_betriebe = pd.read_sql_query("SELECT * FROM betriebe", conn)
    df_einsaetze = pd.read_sql_query("SELECT * FROM einsaetze", conn)
    conn.close()

    if not df_betriebe.empty:
        if not df_einsaetze.empty:
            ist_sum = df_einsaetze.groupby('betrieb_id')['ist_stunden'].sum().reset_index()
            df_overview = df_betriebe.merge(ist_sum, on='betrieb_id', how='left').fillna(0)
        else:
            df_overview = df_betriebe.copy()
            df_overview['ist_stunden'] = 0.0

        df_overview['Auslastung'] = (df_overview['ist_stunden'] / df_overview['soll_stunden'].replace(0, 1)) * 100
        df_overview = df_overview.round(1)
        st.dataframe(df_overview, hide_index=True, use_container_width=True)

        # 3. Historie & Löschen
        st.subheader("Buchungshistorie")
        if not df_einsaetze.empty:
            # Spalte für Lösch-Checkbox hinzufügen
            df_einsaetze['Löschen'] = False
            
            # Editor für Historie
            edited_history = st.data_editor(
                df_einsaetze, 
                column_config={"ist_stunden": st.column_config.NumberColumn(format="%.1f")},
                hide_index=True,
                key="history_editor"
            )
            
            if st.button("Ausgewählte Buchungen löschen"):
                to_delete = edited_history[edited_history['Löschen'] == True]
                if not to_delete.empty:
                    conn = sqlite3.connect(DB_PATH)
                    for _, row in to_delete.iterrows():
                        conn.execute("DELETE FROM einsaetze WHERE id = ?", (row['id'],))
                    conn.commit()
                    conn.close()
                    save_db()
                    st.rerun()
        else:
            st.info("Keine Buchungen vorhanden.")
    else:
        st.info("Keine Betriebe angelegt.")