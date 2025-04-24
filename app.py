import streamlit as st

# Inizializzazione dello stato della sessione
if "income" not in st.session_state:
    st.session_state.income = 0.0

if "expenses" not in st.session_state:
    st.session_state.expenses = []

# Input del reddito mensile
st.title("📊 Gestione Budget Mensile")
st.header("1. Inserisci il tuo reddito")
income = st.number_input("Reddito (€)", min_value=0.0, step=100.0, value=st.session_state.income)
if st.button("Salva Reddito"):
    st.session_state.income = income
    st.success(f"Reddito aggiornato: {income} €")

# Aggiunta di una spesa
st.header("2. Aggiungi una spesa")
with st.form(key="expense_form"):
    expense_name = st.text_input("Nome della spesa")
    expense_amount = st.number_input("Importo (€)", min_value=0.0, step=10.0)
    submit_button = st.form_submit_button("Aggiungi Spesa")
    if submit_button:
        st.session_state.expenses.append({"name": expense_name, "amount": expense_amount})
        st.success(f"Aggiunta spesa: {expense_name} - {expense_amount} €")

# Riepilogo del budget
st.header("3. Riepilogo")
total_expenses = sum(e["amount"] for e in st.session_state.expenses)
balance = st.session_state.income - total_expenses

st.metric("Reddito Mensile", f"{st.session_state.income} €")
st.metric("Spese Totali", f"{total_expenses} €")
st.metric("Saldo Rimanente", f"{balance} €")

st.subheader("📋 Spese Dettagliate")
if st.session_state.expenses:
    for e in st.session_state.expenses:
        st.write(f"- {e['name']}: {e['amount']} €")
else:
    st.info("Nessuna spesa ancora registrata.")