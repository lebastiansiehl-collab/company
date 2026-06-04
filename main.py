import streamlit as st
import sqlite3
import pandas as pd
from github import Github
import os

# 1. GitHub Token aus Secrets laden
g = Github(st.secrets["GIT_TOKEN"])
repo = g.get_repo("lebastiansiehl-collab/company")
DB_PATH = "data/arbeitsmedizin.db"

# 2. Datenbank aus GitHub laden (beim Start)
def load_db():
    if not os.path.exists("data"): os.makedirs("data")
    contents = repo.get_contents(DB_PATH)
    with open(DB_PATH, "wb") as f:
        f.write(contents.decoded_content)

# 3. Datenbank nach GitHub speichern
def save_db():
    with open(DB_PATH, "rb") as f:
        content = f.read()
    contents = repo.get_contents(DB_PATH)
    repo.update_file(contents.path, "Update DB via App", content, contents.sha)

# Initialisierung
if "db_loaded" not in st.session_state:
    load_db()
    st.session_state.db_loaded = True

st.title("Arbeitsmedizin Portal (GitHub API)")

# Formular
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
        save_db() # Direkt zu GitHub
        st.success("Erfolgreich gespeichert und zu GitHub gepusht!")
