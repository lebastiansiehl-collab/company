import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import pandas as pd

# Konfiguration (Credentials über Streamlit Secrets)
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds = ServiceAccountCredentials.from_json_keyfile_dict(st.secrets["gcp_service_account"], scope)
client = gspread.authorize(creds)
sheet = client.open("ArbeitsmedizinDB").sheet1

st.title("Arbeitsmedizin Portal (Cloud)")

# Formular
with st.form("einsatz_form"):
    betrieb_id = st.number_input("Betriebs-ID", min_value=1)
    stunden = st.number_input("Stunden", min_value=1)
    submit = st.form_submit_button("Speichern")
    
    if submit:
        # Neue Zeile anhängen
        sheet.append_row([len(sheet.get_all_values()), betrieb_id, "2026-06-04", stunden, "Offen"])
        st.success("Erfolgreich in Google Sheets gespeichert!")

# Daten anzeigen
if st.button("Daten anzeigen"):
    data = sheet.get_all_records()
    df = pd.DataFrame(data)
    st.write(df)

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
