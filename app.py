import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import datetime

# Configura le credenziali dai secrets
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds_dict = st.secrets["google"]
creds = ServiceAccountCredentials.from_json_keyfile_dict(dict(creds_dict), scope)
client = gspread.authorize(creds)

# Connessione al foglio
SHEET_ID = "1GSony_907R7rCpQFqrdpr2uXDEOmJBlEM-6nT-ETSQs"
sheet = client.open_by_key(SHEET_ID).sheet1

# Lettura dei dati
righe = sheet.get_all_values()
header, dati = righe[0], righe[1:] if len(righe) > 1 else []

# Mesi disponibili
mesi = sorted(set(r[0][:7] for r in dati))  # YYYY-MM

# Navigazione a tab
tab1, tab2 = st.tabs(["📊 Riepilogo", "📋 Dettaglio voci"])

# ↩️ Tab 1 – Riepilogo e inserimento
with tab1:
    st.title("📊 Budget Mensile")
    st.markdown(
        "[🔗 Apri il file su Google Sheets](https://docs.google.com/spreadsheets/d/1GSony_907R7rCpQFqrdpr2uXDEOmJBlEM-6nT-ETSQs/edit)",
        unsafe_allow_html=True
    )
    st.markdown("Registra nuove entrate/spese e consulta il riepilogo mensile.")

    # ➕ Form per aggiungere voce
    with st.form("aggiungi_voce"):
        col1, col2 = st.columns(2)
        tipo = col1.selectbox("Tipo di voce", ["Entrata", "Spesa"])
        descrizione = col2.text_input("Descrizione")
        importo = st.text_input("Importo (€)")  # accetta virgola o punto
        invia = st.form_submit_button("Aggiungi")
        if invia and descrizione and importo:
            try:
                importo_float = float(importo.replace(",", "."))
                oggi = datetime.datetime.now().strftime("%Y-%m-%d")
                sheet.append_row([oggi, tipo, descrizione, str(importo_float)])
                st.success(f"{tipo} aggiunta: {descrizione} - {importo_float} €")
            except ValueError:
                st.error("Importo non valido. Usa numeri con virgola o punto.")

    # 📈 Riepilogo
    entrate = spese = 0.0
    st.subheader("📈 Riepilogo")
    mese_selezionato = st.selectbox("📅 Mese", mesi[::-1], key="riepilogo_mese") if mesi else None

    if mese_selezionato:
        for r in dati:
            data, tipo, descr, imp = r
            if data.startswith(mese_selezionato):
                try:
                    imp = float(imp.replace(",", "."))
                    if tipo.lower() == "entrata":
                        entrate += imp
                    elif tipo.lower() == "spesa":
                        spese += imp
                except ValueError:
                    continue
        risparmio = entrate - spese

        col1, col2, col3 = st.columns(3)
        col1.metric("Entrate", f"{entrate:.2f} €")
        col2.metric("Spese", f"{spese:.2f} €")
        col3.metric("Risparmio", f"{risparmio:.2f} €", delta=f"{risparmio:.2f} €")

# ↪️ Tab 2 – Dettaglio voci
with tab2:
    st.title("📋 Dettaglio voci")
    st.markdown("Consulta tutte le voci registrate per il mese selezionato.")

    mese_selezionato = st.selectbox("📅 Mese", mesi[::-1], key="dettaglio_mese") if mesi else None

    voci_filtrate = []
    if mese_selezionato:
        for r in dati:
            data, tipo, descr, imp = r
            if data.startswith(mese_selezionato):
                try:
                    imp = float(imp.replace(",", "."))
                    voci_filtrate.append((data, tipo, descr, imp))
                except ValueError:
                    continue

    if voci_filtrate:
        for r in voci_filtrate:
            data_formattata = datetime.datetime.strptime(r[0], "%Y-%m-%d").strftime("%d:%m:%Y")
            colore = "green" if r[1].lower() == "entrata" else "red"
            st.markdown(
                f"<span style='color:{colore}'>{data_formattata} | {r[2]} | {r[3]} €</span>",
                unsafe_allow_html=True
            )
    else:
        st.info("Nessuna voce registrata per questo mese.")
