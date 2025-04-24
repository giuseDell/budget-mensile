import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import datetime

# Configura le credenziali dai secrets
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds_dict = st.secrets["google"]
creds = ServiceAccountCredentials.from_json_keyfile_dict(dict(creds_dict), scope)
client = gspread.authorize(creds)

# ✅ Usa l'ID del foglio invece del nome
SHEET_ID = "1GSony_907R7rCpQFqrdpr2uXDEOmJBlEM-6nT-ETSQs"
sheet = client.open_by_key(SHEET_ID).sheet1

# Funzione per aggiungere una voce
def aggiungi_voce(tipo, descrizione, importo):
    oggi = datetime.datetime.now().strftime("%Y-%m-%d")
    sheet.append_row([oggi, tipo, descrizione, importo])

# Interfaccia utente
st.title("📊 Budget Mensile (Google Sheets)")
st.markdown("Registra spese e entrate direttamente su Google Sheets")

tipo = st.selectbox("Tipo di voce", ["Entrata", "Spesa"])
descrizione = st.text_input("Descrizione")
importo = st.number_input("Importo (€)", step=1.0)

if st.button("Aggiungi"):
    if descrizione and importo:
        aggiungi_voce(tipo, descrizione, importo)
        st.success(f"{tipo} aggiunta: {descrizione} - {importo} €")
    else:
        st.error("Compila tutti i campi")

# Visualizza le ultime 10 righe
st.subheader("📋 Ultime voci registrate")
righe = sheet.get_all_values()
header, dati = righe[0], righe[1:]
if dati:
    for r in dati[-10:]:
        st.write(f"{r[0]} - {r[1]}: {r[2]} ({r[3]} €)")
else:
    st.info("Nessuna voce presente nel foglio.")
