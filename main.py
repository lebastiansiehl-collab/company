import streamlit as st
import sqlite3
import pandas as pd
from github import Github
import base64

# Verbindung zu GitHub
g = Github(st.secrets["GIT_TOKEN"])
repo = g.get_repo("lebastiansiehl-collab/company")

def save_to_github(db_path):
    with open(db_path, "rb") as f:
        content = f.read()
    
    # Datei auf GitHub aktualisieren
    try:
        contents = repo.get_contents("data/arbeitsmedizin.db")
        repo.update_file(contents.path, "Update DB via App", content, contents.sha)
    except:
        repo.create_file("data/arbeitsmedizin.db", "Init DB", content)

# Wenn gespeichert wird:
if submit:
    # 1. Lokal in die DB (damit die App sofort aktualisiert)
    # 2. Synchronisation zu GitHub
    save_to_github('data/arbeitsmedizin.db')
    st.success("Daten sicher in GitHub gespeichert!")
