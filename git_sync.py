import streamlit as st
import os
from git import Repo

def sync_db():
    token = st.secrets["GIT_TOKEN"]
    repo = Repo('.')
    
    # WICHTIG: Identität für Git setzen
    repo.config_writer().set_value("user", "name", "StreamlitApp").release()
    repo.config_writer().set_value("user", "email", "app@streamlit.com").release()
    
    repo.git.add('data/arbeitsmedizin.db')
    repo.git.commit('-m', 'Auto-Sync via App')
    
    origin = repo.remote(name='origin')
    origin.set_url(f"https://{token}@github.com/lebastiansiehl-collab/company.git")
    origin.push()
