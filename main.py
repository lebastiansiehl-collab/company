import streamlit as st
import gspread
import pandas as pd

# Dein Google Sheet Link
SHEET_URL = "HIER_DEINEN_LINK_ZUM_GOOGLE_SHEET_EINTRAGEN"

st.title("Arbeitsmedizin Portal")

# Verbindung
conn = st.connection("gsheets", type="gsheets")
# Wenn du das erste Mal "st.connection" nutzt, fragt er nach der Installation:
# pip install streamlit-gsheets

# Daten laden
df = conn.read(spreadsheet=SHEET_URL)
st.write(df)

# Daten speichern
with st.form("einsatz_form"):
    betrieb_id = st.number_input("Betriebs-ID", min_value=1)
    stunden = st.number_input("Stunden", min_value=1)
    submit = st.form_submit_button("Speichern")
    
    if submit:
        # Neue Zeile
        neue_zeile = pd.DataFrame([{"betrieb_id": betrieb_id, "stunden": stunden, "status": "Offen"}])
        updated_df = pd.concat([df, neue_zeile], ignore_index=True)
        conn.update(spreadsheet=SHEET_URL, data=updated_df)
        st.success("Gespeichert!")
