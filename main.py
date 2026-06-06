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

    # 2. Übersicht (Aggregiert & Interaktiv)
    st.subheader("Aktuelle Auslastung")
    conn = sqlite3.connect(DB_PATH)
    df_betriebe = pd.read_sql_query("SELECT * FROM betriebe", conn)
    df_einsaetze = pd.read_sql_query("SELECT * FROM einsaetze", conn)
    conn.close()

    if not df_betriebe.empty:
        df_betriebe['betrieb_id'] = df_betriebe['betrieb_id'].astype(str)
        df_betriebe = df_betriebe.drop_duplicates(subset=['betrieb_id'])
        
        if not df_einsaetze.empty:
            df_einsaetze['betrieb_id'] = df_einsaetze['betrieb_id'].astype(str)
            ist_sum = df_einsaetze.groupby('betrieb_id')['ist_stunden'].sum().reset_index()
            df_overview = pd.merge(df_betriebe, ist_sum, on='betrieb_id', how='left').fillna(0)
        else:
            df_overview = df_betriebe.copy()
            df_overview['ist_stunden'] = 0.0

        df_overview['Auslastung'] = (df_overview['ist_stunden'] / df_overview['soll_stunden'].replace(0, 1)) * 100
        df_overview = df_overview.round(1)

        # Tabelle mit Auswahlfunktion
        selection = st.dataframe(
            df_overview, 
            hide_index=True, 
            use_container_width=True,
            selection_mode="single-row", 
            on_select="rerun"
        )

        # 3. Historie (erscheint nur bei Auswahl)
        if selection.selection.rows:
            selected_index = selection.selection.rows[0]
            selected_betrieb = df_overview.iloc[selected_index]['betrieb_id']
            
            st.divider()
            st.subheader(f"Buchungshistorie: {selected_betrieb}")
            
            # Filtere Historie und ordne Spalten neu
            df_filtered = df_einsaetze[df_einsaetze['betrieb_id'] == selected_betrieb].copy()
            df_filtered['Löschen'] = False
            
# Editor für Historie: Datum, Stunden, Löschen anzeigen; ID verstecken
            edited_history = st.data_editor(
                df_filtered[['datum', 'ist_stunden', 'Löschen', 'id']], 
                column_config={
                    "ist_stunden": st.column_config.NumberColumn(format="%.1f"),
                    "id": st.column_config.Column(hidden=True)  # <-- Hier: NumberColumn zu Column geändert
                },
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
            st.info("Klicke auf eine Zeile in der Tabelle oben, um die Buchungshistorie zu sehen.")
            
    else:
        st.info("Keine Betriebe angelegt.")