import streamlit as st
import gspread
import pandas as pd
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
    records = sheet_utenti.get_all_records()
    for r in records:
        if r["nome"].strip().lower() == nome.strip().lower() and r["cognome"].strip().lower() == cognome.strip().lower():
            return False
    sheet_utenti.append_row([nome, cognome, password])
    return True

# === SESSIONE ===
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.nome_cognome = ""

# === LOGIN UI ===
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
                st.rerun()
            else:
                st.error("Credenziali errate.")
    else:
        if st.button("Registrati"):
            successo = registra(nome.strip().title(), cognome.strip().title(), password)
            if successo:
                st.success("Registrazione completata! Ora effettua il login.")
            else:
                st.warning("Utente già registrato.")

# === APP AUTENTICATA ===
else:
    nome_cognome = st.session_state.nome_cognome
    tab_titles = ["📊 Riepilogo", "📋 Dettaglio"]
    if nome_cognome == "Giuseppe Dell'Ali":
        tab_titles.append("📄 Google Sheet")
    tabs = st.tabs(tab_titles)

    # === CARICA DATI PERSONALI ===
    righe = sheet_dati.get_all_values()[1:]
    dati_utente = [r for r in righe if r[1] == nome_cognome]
    mesi = sorted(set(r[0][:7] for r in dati_utente))

    # === 📊 RIEPILOGO ===
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
                    imp = float(importo.replace(",", ".").replace("€", "").strip())
                    oggi = datetime.datetime.now().strftime("%Y-%m-%d")
                    sheet_dati.append_row([oggi, nome_cognome, tipo, descrizione, str(imp)])
                    st.success(f"{tipo} registrata: {descrizione} - {imp} €")
                    st.rerun()
                except:
                    st.error("Importo non valido")

        st.subheader("📈 Riepilogo tabellare")
        mese = st.selectbox("📅 Mese", mesi[::-1], key="riepilogo_mese") if mesi else None

        if mese:
            dati_filtrati = [
                r for r in dati_utente if r[0].startswith(mese)
            ]
            df = pd.DataFrame(dati_filtrati, columns=["Data", "Utente", "Tipo", "Descrizione", "Importo"])
            df["Importo"] = df["Importo"].astype(str).str.replace(",", ".").astype(float)
            df_stile = df.style.applymap(
                lambda v: "color: green" if v == "Entrata" else "color: red", subset=["Tipo"]
            )

            st.dataframe(df_stile, use_container_width=True)

            # Esporta CSV
            csv = df.to_csv(index=False).encode("utf-8")
            st.download_button("⬇️ Esporta CSV", data=csv, file_name=f"riepilogo_{mese}.csv", mime="text/csv")

    # === 📋 DETTAGLIO VOCI ===
    with tabs[1]:
        st.title("📋 Dettaglio voci")
        mese = st.selectbox("📅 Mese", mesi[::-1], key="dettaglio_mese") if mesi else None

        if mese:
            for idx, r in enumerate(dati_utente):
                if r[0].startswith(mese):
                    imp = r[4].replace(",", ".").replace("€", "").strip()
                    try:
                        imp_float = float(imp)
                        data_fmt = datetime.datetime.strptime(r[0], "%Y-%m-%d").strftime("%d:%m:%Y")
                        colore = "green" if r[2].lower() == "entrata" else "red"
                        col1, col2 = st.columns([4, 1])
                        with col1:
                            st.markdown(
                                f"<span style='color:{colore}'>{data_fmt} | {r[3]} | {imp_float:.2f} €</span>",
                                unsafe_allow_html=True
                            )
                        with col2:
                            if st.button("❌", key=f"del_{idx}"):
                                tutte = sheet_dati.get_all_values()
                                header, righe = tutte[0], tutte[1:]
                                for i, row in enumerate(righe):
                                    if row == r:
                                        sheet_dati.delete_rows(i + 2)
                                        st.rerun()
                    except:
                        continue

    # === 📄 GOOGLE SHEET (solo Giuseppe) ===
    if "📄 Google Sheet" in tab_titles:
        with tabs[2]:
            st.title("📄 Google Sheet")
            st.markdown("Modifica diretta sul file:")
            st.markdown(
                "[🔗 Vai al foglio Google Sheets](https://docs.google.com/spreadsheets/d/1GSony_907R7rCpQFqrdpr2uXDEOmJBlEM-6nT-ETSQs/edit)",
                unsafe_allow_html=True
            )

    if st.button("🔓 Logout"):
        st.session_state.logged_in = False
        st.session_state.nome_cognome = ""
        st.rerun()
