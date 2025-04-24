import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import datetime

# === CONFIG ===
SHEET_ID = "1GSony_907R7rCpQFqrdpr2uXDEOmJBlEM-6nT-ETSQs"
TAB_UTENTI = "utenti"
TAB_DATI = "movimenti"

# === GOOGLE SHEETS CONNECTION ===
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds_dict = st.secrets["google"]
creds = ServiceAccountCredentials.from_json_keyfile_dict(dict(creds_dict), scope)
client = gspread.authorize(creds)
sheet_utenti = client.open_by_key(SHEET_ID).worksheet(TAB_UTENTI)
sheet_dati = client.open_by_key(SHEET_ID).worksheet(TAB_DATI)

# === LOGIN / REGISTRAZIONE ===
def login(nome, cognome, password):
    records = sheet_utenti.get_all_records()
    for r in records:
        if r["nome"] == nome and r["cognome"] == cognome and r["password"] == password:
            return True
    return False

def registra(nome, cognome, password):
    sheet_utenti.append_row([nome, cognome, password])

# === SESSIONE ===
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.nome_cognome = ""

# === INTERFACCIA ===
if not st.session_state.logged_in:
    st.title("🔐 Accedi o Registrati")
    scelta = st.radio("Seleziona", ["Login", "Registrazione"])

    nome = st.text_input("Nome")
    cognome = st.text_input("Cognome")
    password = st.text_input("Password", type="password")

    if scelta == "Login":
        if st.button("Accedi"):
            if login(nome, cognome, password):
                st.session_state.logged_in = True
                st.session_state.nome_cognome = f"{nome.strip().title()} {cognome.strip().title()}"
                st.success("Accesso riuscito!")
                st.experimental_rerun()
            else:
                st.error("Credenziali errate.")
    else:
        if st.button("Registrati"):
            registra(nome.strip().title(), cognome.strip().title(), password)
            st.success("Registrazione completata! Ora effettua il login.")

# === APP AUTENTICATA ===
else:
    tabs = st.tabs(["📊 Riepilogo", "📋 Dettaglio", "📄 Google Sheet"])
    nome_cognome = st.session_state.nome_cognome

    tutte_le_righe = sheet_dati.get_all_values()
    header = tutte_le_righe[0]
    righe = tutte_le_righe[1:]
    dati_utente = [r for r in righe if r[1] == nome_cognome]

    mesi = sorted(set(r[0][:7] for r in dati_utente))

    # === 📊 Riepilogo ===
    with tabs[0]:
        st.title("📊 Riepilogo")
        st.markdown(f"Benvenuto **{nome_cognome}**")

        with st.form("aggiungi_voce"):
            col1, col2 = st.columns(2)
            tipo = col1.selectbox("Tipo", ["Entrata", "Spesa"])
            descrizione = col2.text_input("Descrizione")
            importo = st.text_input("Importo (€)")
            invia = st.form_submit_button("Aggiungi")
            if invia and descrizione and importo:
                try:
                    imp = float(importo.replace(",", "."))
                    oggi = datetime.datetime.now().strftime("%Y-%m-%d")
                    sheet_dati.append_row([oggi, nome_cognome, tipo, descrizione, str(imp)])
                    st.success(f"{tipo} registrata: {descrizione} - {imp} €")
                    st.experimental_rerun()
                except:
                    st.error("Importo non valido")

        st.subheader("📈 Riepilogo")
        mese = st.selectbox("📅 Mese", mesi[::-1], key="riepilogo_mese") if mesi else None

        if mese:
            entrate = spese = 0.0
            for r in dati_utente:
                if r[0].startswith(mese):
                    try:
                        imp = float(r[4].replace(",", "."))
                        if r[2].lower() == "entrata":
                            entrate += imp
                        elif r[2].lower() == "spesa":
                            spese += imp
                    except:
                        continue
            saldo = entrate - spese
            c1, c2, c3 = st.columns(3)
            c1.metric("Entrate", f"{entrate:.2f} €")
            c2.metric("Spese", f"{spese:.2f} €")
            c3.metric("Risparmio", f"{saldo:.2f} €", delta=f"{saldo:.2f} €")

    # === 📋 Dettaglio voci ===
    with tabs[1]:
        st.title("📋 Dettaglio voci")
        mese = st.selectbox("📅 Mese", mesi[::-1], key="dettaglio_mese") if mesi else None

        if mese:
            for r in dati_utente:
                if r[0].startswith(mese):
                    try:
                        imp = float(r[4].replace(",", "."))
                        data = datetime.datetime.strptime(r[0], "%Y-%m-%d").strftime("%d:%m:%Y")
                        colore = "green" if r[2].lower() == "entrata" else "red"
                        st.markdown(
                            f"<span style='color:{colore}'>{data} | {r[3]} | {imp} €</span>",
                            unsafe_allow_html=True
                        )
                    except:
                        continue

    # === 📄 Google Sheet ===
    with tabs[2]:
        st.title("📄 Google Sheet")
        st.markdown("Puoi modificare il file manualmente qui:")
        st.markdown(
            "[🔗 Vai al foglio completo su Google Sheets](https://docs.google.com/spreadsheets/d/1GSony_907R7rCpQFqrdpr2uXDEOmJBlEM-6nT-ETSQs/edit)",
            unsafe_allow_html=True
        )

    # Logout
    if st.button("🔓 Logout"):
        st.session_state.logged_in = False
        st.session_state.nome_cognome = ""
        st.experimental_rerun()
