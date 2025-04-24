import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import datetime
from collections import defaultdict

# Configura le credenziali dai secrets
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds_dict = st.secrets["google"]
creds = ServiceAccountCredentials.from_json_keyfile_dict(dict(creds_dict), scope)
client = gspread.authorize(creds)

# Connessione al foglio
SHEET_ID = "1GSony_907R7rCpQFqrdpr2uXDEOmJBlEM-6nT-ETSQs"
sheet = client.open_by_key(SHEET_ID).sheet1

# Funzione per aggiungere una voce
def aggiungi_voce(tipo, descrizione, importo):
    oggi = datetime.datetime.now().strftime("%Y-%m-%d")
    sheet.append_row([oggi, tipo, descrizione, importo])

# Lettura dei dati
righe = sheet.get_all_values()
header, dati = righe[0], righe[1:] if len(righe) > 1 else []

# Interfaccia
st.title("📊 Budget Mensile (Google Sheets)")
st.markdown("Registra e consulta le tue **entrate** e **spese** filtrate per mese.")

# ➕ Form per aggiungere voce
with st.form("aggiungi_voce"):
    col1, col2 = st.columns(2)
    tipo = col1.selectbox("Tipo di voce", ["Entrata", "Spesa"])
    descrizione = col2.text_input("Descrizione")
    importo = st.number_input("Importo (€)", step=1.0)
    invia = st.form_submit_button("Aggiungi")
    if invia and descrizione and importo:
        aggiungi_voce(tipo, descrizione, importo)
        st.success(f"{tipo} aggiunta: {descrizione} - {importo} €")

# 📅 Filtro per mese
st.subheader("📅 Seleziona mese")
mesi = sorted(set(r[0][:7] for r in dati))  # YYYY-MM
mese_selezionato = st.selectbox("Mese", mesi[::-1]) if mesi else None

# 📊 Calcolo riepilogo filtrato
entrate = spese = 0.0
voci_filtrate = []

if mese_selezionato:
    for r in dati:
        data, tipo, descr, imp = r
        if data.startswith(mese_selezionato):
            imp = float(imp)
            voci_filtrate.append((data, tipo, descr, imp))
            if tipo.lower() == "entrata":
                entrate += imp
            elif tipo.lower() == "spesa":
                spese += imp

    risparmio = entrate - spese

    st.subheader("📈 Riepilogo")
    col1, col2, col3 = st.columns(3)
    col1.metric("Entrate", f"{entrate:.2f} €")
    col2.metric("Spese", f"{spese:.2f} €")
    col3.metric("Risparmio", f"{risparmio:.2f} €", delta=f"{risparmio:.2f} €")

# 📋 Mostra elenco voci
st.subheader("📋 Dettaglio voci")
if voci_filtrate:
    for r in voci_filtrate:
        data_originale = datetime.datetime.strptime(r[0], "%Y-%m-%d")
        data_formattata = data_originale.strftime("%d:%m:%Y")
        colore = "green" if r[1].lower() == "entrata" else "red"
        st.markdown(
            f"<span style='color:{colore}'>{data_formattata} | {r[2]} | {r[3]} €</span>",
            unsafe_allow_html=True
        )
    else:
        st.info("Nessuna voce registrata per questo mese.")
else:
    st.info("Nessun dato disponibile.")
