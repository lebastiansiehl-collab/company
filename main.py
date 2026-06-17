import streamlit as st
import sqlite3
import pandas as pd
from github import Github
import os
from datetime import date

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

with tab2:
    conn = sqlite3.connect(DB_PATH)
    df_betriebe = pd.read_sql_query("SELECT * FROM betriebe", conn)
    df_einsaetze = pd.read_sql_query("SELECT * FROM einsaetze", conn)
    conn.close()

    st.subheader("Stunden erfassen")
    if not df_betriebe.empty:
        b_select = st.selectbox("Betrieb auswählen", df_betriebe['betrieb_id'])
        h_input = st.number_input("Stunden", min_value=0.0, step=0.5)
        d_input = st.date_input("Datum", date.today())
        if st.button("Buchen"):
            conn = sqlite3.connect(DB_PATH)
            conn.execute("INSERT INTO einsaetze (betrieb_id, ist_stunden, datum) VALUES (?, ?, ?)", (b_select, h_input, str(d_input)))
            conn.commit()
            conn.close()
            save_db()
            st.rerun()

    st.divider()
    st.subheader("Aktuelle Auslastung")

    if not df_betriebe.empty:
        df_betriebe['betrieb_id'] = df_betriebe['betrieb_id'].astype(str)
        if not df_einsaetze.empty:
            ist_sum = df_einsaetze.groupby('betrieb_id')['ist_stunden'].sum().reset_index()
            df_overview = pd.merge(df_betriebe, ist_sum, on='betrieb_id', how='left').fillna(0)
        else:
            df_overview = df_betriebe.copy()
            df_overview['ist_stunden'] = 0.0

        df_overview['Auslastung'] = (df_overview['ist_stunden'] / df_overview['soll_stunden'].replace(0, 1)) * 100
        df_overview['diff_val'] = df_overview['soll_stunden'] - df_overview['ist_stunden']
        df_overview['Saldo'] = df_overview['diff_val'].apply(lambda x: f"{x:.1f} offen" if x > 0 else f"{abs(x):.1f} über Plan")
        df_overview['Status'] = df_overview['Auslastung'].apply(lambda x: "✅ OK" if x >= 100 else "⏳ offen")
        
        selection = st.dataframe(
            df_overview[['betrieb_id', 'soll_stunden', 'ist_stunden', 'Auslastung', 'Saldo', 'Status']], 
            hide_index=True, use_container_width=True, selection_mode="single-row", on_select="rerun",
            column_config={"Auslastung": st.column_config.ProgressColumn("Auslastung", format="%.1f%%", min_value=0, max_value=100)}
        )

        if selection.selection.rows:
            selected_idx = selection.selection.rows[0]
            b_del = df_overview.iloc[selected_idx]['betrieb_id']
            if st.button(f"Betrieb {b_del} löschen"):
                conn = sqlite3.connect(DB_PATH)
                conn.execute("DELETE FROM betriebe WHERE betrieb_id = ?", (b_del,))
                conn.execute("DELETE FROM einsaetze WHERE betrieb_id = ?", (b_del,))
                conn.commit()
                conn.close()
                save_db()
                st.rerun()

            st.divider()
            st.subheader(f"Buchungshistorie: {b_del}")
            df_filt = df_einsaetze[df_einsaetze['betrieb_id'] == b_del].copy()
            df_filt['Löschen'] = False
            edit = st.data_editor(df_filt[['datum', 'ist_stunden', 'Löschen', 'id']], 
                                  column_config={"ist_stunden": st.column_config.NumberColumn(format="%.1f"), "id": None},
                                  hide_index=True, key="hist_ed")
            
            if st.button("Speichern & Löschen"):
                conn = sqlite3.connect(DB_PATH)
                for _, row in edit.iterrows():
                    conn.execute("UPDATE einsaetze SET ist_stunden = ? WHERE id = ?", (row['ist_stunden'], row['id']))
                    if row['Löschen']: conn.execute("DELETE FROM einsaetze WHERE id = ?", (row['id'],))
                conn.commit()
                conn.close()
                save_db()
                st.rerun()
    else:
        st.info("Keine Betriebe angelegt.")